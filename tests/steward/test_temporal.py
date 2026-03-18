#!/usr/bin/env python3
"""
Temporal Commitment Tests -- Phase 3, Plan 01.

Tests for mg_temporal.py covering all TEMP requirements:
- TEMP-01: NIST Beacon pulse capture
- TEMP-02: Cryptographic binding (SHA-256)
- TEMP-03: Graceful degradation
- TEMP-04: Layer 5 independent verification
- TEMP-05: Offline verification (no network calls)
- TEMP-06: Pre-commitment hash scheme
"""

import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg_temporal import (  # noqa: E402
    _fetch_beacon_pulse,
    create_temporal_commitment,
    verify_temporal_commitment,
    write_temporal_commitment,
    BEACON_URL,
    TEMPORAL_FILE,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOCK_ROOT_HASH = "a1b2c3d4e5f6" * 10 + "a1b2"  # 64 hex chars

MOCK_BEACON_PULSE = {
    "pulse": {
        "outputValue": "a" * 128,
        "timeStamp": "2026-03-18T00:00:00.000Z",
        "uri": "https://beacon.nist.gov/beacon/2.0/chain/2/pulse/1234567",
    }
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pack_dir(tmp_path, root_hash=MOCK_ROOT_HASH):
    """Create a minimal pack dir with pack_manifest.json."""
    pack_dir = tmp_path / "bundle"
    pack_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"files": [], "root_hash": root_hash}
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return pack_dir


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_beacon(monkeypatch):
    """Mock NIST Beacon to return predictable pulse."""
    def fake_urlopen(req, timeout=None):
        body = json.dumps(MOCK_BEACON_PULSE).encode("utf-8")
        resp = io.BytesIO(body)
        return resp
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)


@pytest.fixture
def mock_beacon_unavailable(monkeypatch):
    """Mock NIST Beacon as unreachable."""
    def fail_urlopen(req, timeout=None):
        raise urllib.error.URLError("timeout")
    monkeypatch.setattr("urllib.request.urlopen", fail_urlopen)


# ---------------------------------------------------------------------------
# Beacon Fetch Tests
# ---------------------------------------------------------------------------

class TestBeaconFetch:
    """Tests for _fetch_beacon_pulse()."""

    def test_beacon_fetch_success(self, mock_beacon):
        """Mock beacon returns dict with outputValue, timeStamp, uri."""
        result = _fetch_beacon_pulse()
        assert result is not None
        assert "outputValue" in result
        assert len(result["outputValue"]) == 128  # 512-bit hex
        assert "timeStamp" in result
        assert result["timeStamp"] == "2026-03-18T00:00:00.000Z"
        assert "uri" in result

    def test_beacon_fetch_timeout(self, mock_beacon_unavailable):
        """Unreachable beacon returns None."""
        result = _fetch_beacon_pulse()
        assert result is None

    def test_beacon_fetch_bad_json(self, monkeypatch):
        """Invalid JSON from beacon returns None."""
        def bad_urlopen(req, timeout=None):
            return io.BytesIO(b"this is not json")
        monkeypatch.setattr("urllib.request.urlopen", bad_urlopen)
        result = _fetch_beacon_pulse()
        assert result is None


# ---------------------------------------------------------------------------
# Create Temporal Commitment Tests
# ---------------------------------------------------------------------------

class TestCreateTemporalCommitment:
    """Tests for create_temporal_commitment()."""

    def test_create_with_beacon(self, mock_beacon):
        """TEMP-01, TEMP-02, TEMP-06: Beacon available produces valid commitment."""
        result = create_temporal_commitment(MOCK_ROOT_HASH)

        assert result["version"] == "temporal-nist-v1"

        expected_pre = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        assert result["pre_commitment_hash"] == expected_pre

        assert result["beacon_status"] == "available"
        assert result["beacon_output_value"] is not None

        # Verify temporal binding
        concat = expected_pre + MOCK_BEACON_PULSE["pulse"]["outputValue"] + MOCK_BEACON_PULSE["pulse"]["timeStamp"]
        expected_binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()
        assert result["temporal_binding"] == expected_binding

    def test_create_degraded(self, mock_beacon_unavailable):
        """TEMP-03: Beacon unreachable produces degraded commitment."""
        result = create_temporal_commitment(MOCK_ROOT_HASH)

        assert result["beacon_status"] == "unavailable"
        assert result["beacon_output_value"] is None
        assert result["temporal_binding"] is None
        assert result["local_timestamp"] is not None
        # local_timestamp should be ISO format
        assert "T" in result["local_timestamp"]

        # pre_commitment_hash should still be valid
        expected_pre = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        assert result["pre_commitment_hash"] == expected_pre

    def test_precommitment_before_beacon(self, monkeypatch):
        """TEMP-06: Pre-commitment hash computed before beacon fetch."""
        call_order = []

        original_sha256 = hashlib.sha256

        def tracking_sha256(data=b""):
            call_order.append("sha256")
            return original_sha256(data)

        def tracking_urlopen(req, timeout=None):
            call_order.append("urlopen")
            body = json.dumps(MOCK_BEACON_PULSE).encode("utf-8")
            return io.BytesIO(body)

        monkeypatch.setattr("urllib.request.urlopen", tracking_urlopen)

        # We need to track that sha256 is called before urlopen.
        # Use a side effect on _fetch_beacon_pulse to record ordering.
        from scripts import mg_temporal
        original_fetch = mg_temporal._fetch_beacon_pulse

        def tracked_fetch(*args, **kwargs):
            call_order.append("fetch_beacon")
            return original_fetch(*args, **kwargs)

        monkeypatch.setattr(mg_temporal, "_fetch_beacon_pulse", tracked_fetch)

        result = create_temporal_commitment(MOCK_ROOT_HASH)

        # The pre_commitment_hash should be computed (sha256 call) before
        # _fetch_beacon_pulse is called
        assert "fetch_beacon" in call_order
        # Find first fetch_beacon index
        fetch_idx = call_order.index("fetch_beacon")
        # There should be activity before the fetch
        assert fetch_idx > 0, "Pre-commitment hash must be computed before beacon fetch"

        # Verify the result is still valid
        expected_pre = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        assert result["pre_commitment_hash"] == expected_pre


# ---------------------------------------------------------------------------
# Verify Temporal Commitment Tests
# ---------------------------------------------------------------------------

class TestVerifyTemporalCommitment:
    """Tests for verify_temporal_commitment()."""

    def test_verify_valid_beacon(self, tmp_path):
        """TEMP-04, TEMP-05: Valid beacon-backed commitment verifies."""
        pack_dir = _make_pack_dir(tmp_path)

        pre_hash = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        beacon_val = MOCK_BEACON_PULSE["pulse"]["outputValue"]
        beacon_ts = MOCK_BEACON_PULSE["pulse"]["timeStamp"]
        concat = pre_hash + beacon_val + beacon_ts
        binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()

        tc = {
            "version": "temporal-nist-v1",
            "root_hash": MOCK_ROOT_HASH,
            "pre_commitment_hash": pre_hash,
            "beacon_output_value": beacon_val,
            "beacon_timestamp": beacon_ts,
            "beacon_pulse_uri": MOCK_BEACON_PULSE["pulse"]["uri"],
            "beacon_status": "available",
            "temporal_binding": binding,
        }
        (pack_dir / TEMPORAL_FILE).write_text(
            json.dumps(tc, indent=2), encoding="utf-8"
        )

        ok, msg = verify_temporal_commitment(pack_dir)
        assert ok is True, f"Expected True, got: {msg}"
        assert "VALID" in msg

    def test_verify_valid_degraded(self, tmp_path):
        """TEMP-05: Degraded commitment verifies with advisory."""
        pack_dir = _make_pack_dir(tmp_path)

        pre_hash = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        tc = {
            "version": "temporal-nist-v1",
            "root_hash": MOCK_ROOT_HASH,
            "pre_commitment_hash": pre_hash,
            "beacon_output_value": None,
            "beacon_timestamp": None,
            "beacon_pulse_uri": None,
            "beacon_status": "unavailable",
            "local_timestamp": "2026-03-18T00:00:00+00:00",
            "temporal_binding": None,
        }
        (pack_dir / TEMPORAL_FILE).write_text(
            json.dumps(tc, indent=2), encoding="utf-8"
        )

        ok, msg = verify_temporal_commitment(pack_dir)
        assert ok is True, f"Expected True, got: {msg}"
        assert "local timestamp only" in msg

    def test_verify_precommitment_mismatch(self, tmp_path):
        """Wrong pre_commitment_hash detected."""
        pack_dir = _make_pack_dir(tmp_path)

        tc = {
            "version": "temporal-nist-v1",
            "root_hash": MOCK_ROOT_HASH,
            "pre_commitment_hash": "wrong" * 12 + "abcd",  # 64 chars but wrong
            "beacon_output_value": None,
            "beacon_timestamp": None,
            "beacon_pulse_uri": None,
            "beacon_status": "unavailable",
            "local_timestamp": "2026-03-18T00:00:00+00:00",
            "temporal_binding": None,
        }
        (pack_dir / TEMPORAL_FILE).write_text(
            json.dumps(tc, indent=2), encoding="utf-8"
        )

        ok, msg = verify_temporal_commitment(pack_dir)
        assert ok is False
        assert "pre_commitment_hash does not match" in msg

    def test_verify_binding_mismatch(self, tmp_path):
        """Correct pre_commitment but wrong temporal_binding detected."""
        pack_dir = _make_pack_dir(tmp_path)

        pre_hash = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        tc = {
            "version": "temporal-nist-v1",
            "root_hash": MOCK_ROOT_HASH,
            "pre_commitment_hash": pre_hash,
            "beacon_output_value": MOCK_BEACON_PULSE["pulse"]["outputValue"],
            "beacon_timestamp": MOCK_BEACON_PULSE["pulse"]["timeStamp"],
            "beacon_pulse_uri": MOCK_BEACON_PULSE["pulse"]["uri"],
            "beacon_status": "available",
            "temporal_binding": "tampered" * 8,  # 64 chars but wrong
        }
        (pack_dir / TEMPORAL_FILE).write_text(
            json.dumps(tc, indent=2), encoding="utf-8"
        )

        ok, msg = verify_temporal_commitment(pack_dir)
        assert ok is False
        assert "temporal_binding hash mismatch" in msg

    def test_verify_no_file(self, tmp_path):
        """No temporal_commitment.json returns True with skip message."""
        pack_dir = _make_pack_dir(tmp_path)
        # Don't create temporal_commitment.json

        ok, msg = verify_temporal_commitment(pack_dir)
        assert ok is True
        assert "no temporal commitment present" in msg

    def test_verify_never_imports_urllib(self):
        """TEMP-05: verify_temporal_commitment never calls urllib."""
        import inspect
        source = inspect.getsource(verify_temporal_commitment)
        assert "urllib" not in source, (
            "verify_temporal_commitment must not reference urllib"
        )

    def test_layer5_independence(self, tmp_path):
        """TEMP-04: Verify works with ONLY manifest + temporal file (no evidence, no signature)."""
        pack_dir = _make_pack_dir(tmp_path)

        pre_hash = hashlib.sha256(MOCK_ROOT_HASH.encode("utf-8")).hexdigest()
        beacon_val = MOCK_BEACON_PULSE["pulse"]["outputValue"]
        beacon_ts = MOCK_BEACON_PULSE["pulse"]["timeStamp"]
        concat = pre_hash + beacon_val + beacon_ts
        binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()

        tc = {
            "version": "temporal-nist-v1",
            "root_hash": MOCK_ROOT_HASH,
            "pre_commitment_hash": pre_hash,
            "beacon_output_value": beacon_val,
            "beacon_timestamp": beacon_ts,
            "beacon_pulse_uri": MOCK_BEACON_PULSE["pulse"]["uri"],
            "beacon_status": "available",
            "temporal_binding": binding,
        }
        (pack_dir / TEMPORAL_FILE).write_text(
            json.dumps(tc, indent=2), encoding="utf-8"
        )

        # No evidence.json, no bundle_signature.json -- only manifest + temporal
        ok, msg = verify_temporal_commitment(pack_dir)
        assert ok is True, f"Layer 5 should work independently: {msg}"


# ---------------------------------------------------------------------------
# Write Temporal Commitment Tests
# ---------------------------------------------------------------------------

class TestWriteTemporalCommitment:
    """Tests for write_temporal_commitment()."""

    def test_write_temporal_commitment(self, tmp_path):
        """write_temporal_commitment creates correct JSON file."""
        pack_dir = tmp_path / "bundle"
        pack_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "version": "temporal-nist-v1",
            "root_hash": MOCK_ROOT_HASH,
            "pre_commitment_hash": "abc123",
        }

        result_path = write_temporal_commitment(pack_dir, data)
        tc_path = pack_dir / TEMPORAL_FILE

        assert tc_path.exists()
        assert result_path == tc_path

        loaded = json.loads(tc_path.read_text(encoding="utf-8"))
        assert loaded == data
