#!/usr/bin/env python3
"""
CERT-ADV-TEMPORAL-PURE: Layer 5 Pure Temporal Isolation Attacks.

Four pure temporal attacks that do NOT involve other layers:
  1. Truncated beacon value
  2. Empty timestamp string
  3. Swapped pre_commitment fields between two bundles
  4. All-zero hashes in temporal_commitment.json
"""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg_temporal import (  # noqa: E402
    create_temporal_commitment,
    verify_temporal_commitment,
    write_temporal_commitment,
    TEMPORAL_FILE,
)


_MOCK_BEACON = {
    "outputValue": "deadbeef" * 16,
    "timeStamp": "2026-03-19T12:00:00Z",
    "uri": "https://beacon.nist.gov/beacon/2.0/chain/test/pulse/1",
}


def _make_bundle_with_temporal(tmp_path, evidence_content=None, mock_beacon=None):
    """Create a minimal bundle with temporal commitment."""
    if mock_beacon is None:
        mock_beacon = _MOCK_BEACON
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)

    if evidence_content is None:
        evidence_content = {"claim": "ML_BENCH-01", "result": "PASS"}
    evidence_file = bundle / "evidence.json"
    evidence_file.write_text(json.dumps(evidence_content), encoding="utf-8")

    sha = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
    files = [{"relpath": "evidence.json", "sha256": sha, "bytes": evidence_file.stat().st_size}]
    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    manifest = {"version": "v1", "files": files, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    with patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=mock_beacon):
        tc = create_temporal_commitment(root_hash)
    write_temporal_commitment(bundle, tc)

    return bundle, tc, root_hash


class TestCertAdvTemporalPure:
    """Pure Layer 5 temporal isolation attacks."""

    def test_temporal_truncated_beacon_value(self, tmp_path):
        """
        Create commitment with truncated beacon_output_value.
        Temporal binding recomputation should fail.
        """
        bundle, tc, _ = _make_bundle_with_temporal(tmp_path)

        tc_path = bundle / TEMPORAL_FILE
        tc_data = json.loads(tc_path.read_text(encoding="utf-8"))
        tc_data["beacon_output_value"] = tc_data["beacon_output_value"][:16]  # truncate
        tc_path.write_text(json.dumps(tc_data, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, f"Should catch truncated beacon value: {msg}"
        assert "temporal_binding hash mismatch" in msg

    def test_temporal_empty_timestamp(self, tmp_path):
        """
        Create commitment with beacon_timestamp="".
        Temporal binding recomputation should fail.
        """
        bundle, tc, _ = _make_bundle_with_temporal(tmp_path)

        tc_path = bundle / TEMPORAL_FILE
        tc_data = json.loads(tc_path.read_text(encoding="utf-8"))
        tc_data["beacon_timestamp"] = ""
        tc_path.write_text(json.dumps(tc_data, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, f"Should catch empty timestamp: {msg}"
        assert "temporal_binding hash mismatch" in msg

    def test_temporal_swapped_precommitment(self, tmp_path):
        """
        Create two commitments for different root_hashes, swap
        pre_commitment_hash between them. Both should fail verification.
        """
        bundle_a, tc_a, _ = _make_bundle_with_temporal(
            tmp_path / "a",
            evidence_content={"claim": "ML_BENCH-01", "id": "a"})
        bundle_b, tc_b, _ = _make_bundle_with_temporal(
            tmp_path / "b",
            evidence_content={"claim": "ML_BENCH-01", "id": "b"})

        # Swap pre_commitment_hash
        tc_a_path = bundle_a / TEMPORAL_FILE
        tc_b_path = bundle_b / TEMPORAL_FILE
        data_a = json.loads(tc_a_path.read_text(encoding="utf-8"))
        data_b = json.loads(tc_b_path.read_text(encoding="utf-8"))
        data_a["pre_commitment_hash"], data_b["pre_commitment_hash"] = \
            data_b["pre_commitment_hash"], data_a["pre_commitment_hash"]
        tc_a_path.write_text(json.dumps(data_a, indent=2), encoding="utf-8")
        tc_b_path.write_text(json.dumps(data_b, indent=2), encoding="utf-8")

        ok_a, msg_a = verify_temporal_commitment(bundle_a)
        assert ok_a is False, f"Bundle A should fail with swapped pre_commitment: {msg_a}"

        ok_b, msg_b = verify_temporal_commitment(bundle_b)
        assert ok_b is False, f"Bundle B should fail with swapped pre_commitment: {msg_b}"

    def test_temporal_allzero_hashes(self, tmp_path):
        """
        Create temporal_commitment.json with all fields set to "0"*64.
        Verification should fail.
        """
        bundle, tc, _ = _make_bundle_with_temporal(tmp_path)

        tc_path = bundle / TEMPORAL_FILE
        tc_data = json.loads(tc_path.read_text(encoding="utf-8"))
        tc_data["pre_commitment_hash"] = "0" * 64
        tc_data["beacon_output_value"] = "0" * 64
        tc_data["temporal_binding"] = "0" * 64
        tc_path.write_text(json.dumps(tc_data, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, f"Should catch all-zero hashes: {msg}"
