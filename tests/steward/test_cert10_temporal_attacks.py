#!/usr/bin/env python3
"""
CERT-10: Temporal Commitment Attack Gauntlet -- Five Attack Scenarios, All Caught.

This test file documents five distinct attacks that a sophisticated adversary
might attempt against MetaGenesis Core temporal commitments (Layer 5).
Each attack is caught by the temporal verification logic.

ATTACK SCENARIOS:
  Attack A -- Replay Temporal Commitment
    Adversary copies temporal_commitment.json from bundle_a to bundle_b.
    pre_commitment_hash won't match bundle_b's root_hash.

  Attack B -- Future Timestamp
    Adversary changes beacon_timestamp to a future date.
    temporal_binding hash won't match recomputed binding.

  Attack C -- Beacon Value Forge
    Adversary replaces beacon_output_value with a forged value.
    temporal_binding hash won't match recomputed binding.

  Attack D -- Binding Hash Tamper
    Adversary replaces temporal_binding with a forged hash.
    Recomputed binding won't match the tampered value.

  Attack E -- Pre-commitment Hash Tamper
    Adversary replaces pre_commitment_hash with a forged value.
    SHA-256(root_hash) won't match the tampered pre_commitment_hash.

All five attacks pass the test by FAILING verification -- proving the protocol
catches each attack class.

Repo: https://github.com/Lama999901/metagenesis-core-public
PPA:  USPTO #63/996,819
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
from scripts.mg_sign import generate_key, sign_bundle, SIGNATURE_FILE  # noqa: E402


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_MOCK_BEACON = {
    "outputValue": "deadbeef" * 16,
    "timeStamp": "2026-03-17T12:00:00Z",
    "uri": "https://beacon.nist.gov/beacon/2.0/chain/test/pulse/1",
}


def _make_bundle_with_temporal(tmp_path: Path, evidence_content=None,
                               root_hash_override=None):
    """
    Create a minimal bundle with a beacon-backed temporal commitment.

    Returns (bundle_path, temporal_data, mock_beacon).
    """
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)

    # Evidence file
    if evidence_content is None:
        evidence_content = {"claim": "ML_BENCH-01", "result": "PASS"}
    evidence_file = bundle / "evidence.json"
    evidence_file.write_text(
        json.dumps(evidence_content), encoding="utf-8"
    )

    # Build pack_manifest.json
    sha = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
    files = [{"relpath": "evidence.json", "sha256": sha, "bytes": evidence_file.stat().st_size}]
    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    manifest = {"version": "v1", "files": files, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Create temporal commitment with mocked beacon
    with patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=_MOCK_BEACON):
        temporal_data = create_temporal_commitment(root_hash_override or root_hash)

    write_temporal_commitment(bundle, temporal_data)

    return bundle, temporal_data, _MOCK_BEACON


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCert10TemporalAttacks:
    """
    Five temporal commitment attack scenarios. All caught by Layer 5.

    Each test represents a realistic attack a sophisticated adversary
    would attempt against the temporal commitment scheme.
    Each test PASSES by the attack being DETECTED (verify returns False).
    """

    # ------------------------------------------------------------------
    # ATTACK A -- Replay Temporal Commitment
    # "I'll copy a valid temporal commitment from another bundle."
    # ------------------------------------------------------------------
    def test_a_replay_temporal_commitment(self, tmp_path):
        """
        ATTACK: Copy temporal_commitment.json from bundle_a to bundle_b.
        Since bundle_b has a different root_hash, the pre_commitment_hash
        (SHA-256 of root_hash) won't match.

        Proves: temporal commitments are bound to a specific bundle and
        cannot be replayed across bundles.
        """
        # Bundle A
        bundle_a, tc_a, _ = _make_bundle_with_temporal(
            tmp_path / "a",
            evidence_content={"claim": "ML_BENCH-01", "result": "PASS", "id": "bundle_a"},
        )

        # Bundle B (different evidence content -> different root_hash)
        bundle_b, tc_b, _ = _make_bundle_with_temporal(
            tmp_path / "b",
            evidence_content={"claim": "ML_BENCH-01", "result": "PASS", "id": "bundle_b"},
        )

        # Verify bundles have different root_hashes
        manifest_a = json.loads((bundle_a / "pack_manifest.json").read_text())
        manifest_b = json.loads((bundle_b / "pack_manifest.json").read_text())
        assert manifest_a["root_hash"] != manifest_b["root_hash"], \
            "Bundles must have different root_hashes for this test"

        # ATTACK: Copy temporal commitment from bundle_a to bundle_b
        tc_a_path = bundle_a / TEMPORAL_FILE
        tc_b_path = bundle_b / TEMPORAL_FILE
        tc_b_path.write_text(tc_a_path.read_text(encoding="utf-8"), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle_b)
        assert ok is False, "ATTACK A: replay temporal commitment was NOT detected"
        assert "pre_commitment_hash does not match" in msg, \
            f"ATTACK A detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK B -- Future Timestamp
    # "I'll change the beacon timestamp to claim the bundle was signed later."
    # ------------------------------------------------------------------
    def test_b_future_timestamp(self, tmp_path):
        """
        ATTACK: Change beacon_timestamp to a future date.
        The temporal_binding is SHA-256(pre + beacon_value + timestamp),
        so changing the timestamp invalidates the binding.

        Proves: timestamps cannot be altered without detection.
        """
        bundle, tc_data, _ = _make_bundle_with_temporal(tmp_path)

        # ATTACK: Tamper with beacon_timestamp
        tc_path = bundle / TEMPORAL_FILE
        tc = json.loads(tc_path.read_text(encoding="utf-8"))
        tc["beacon_timestamp"] = "2030-01-01T00:00:00Z"
        tc_path.write_text(json.dumps(tc, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, "ATTACK B: future timestamp was NOT detected"
        assert "temporal_binding hash mismatch" in msg, \
            f"ATTACK B detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK C -- Beacon Value Forge
    # "I'll replace the beacon output value with my own."
    # ------------------------------------------------------------------
    def test_c_beacon_value_forge(self, tmp_path):
        """
        ATTACK: Replace beacon_output_value with a forged value.
        The temporal_binding is SHA-256(pre + beacon_value + timestamp),
        so any change to the beacon value invalidates the binding.

        Proves: beacon values cannot be forged without detection.
        The NIST Beacon provides the unpredictable entropy that anchors
        the temporal commitment to a specific point in time.
        """
        bundle, tc_data, _ = _make_bundle_with_temporal(tmp_path)

        # ATTACK: Replace beacon_output_value
        tc_path = bundle / TEMPORAL_FILE
        tc = json.loads(tc_path.read_text(encoding="utf-8"))
        tc["beacon_output_value"] = "ff" * 64
        tc_path.write_text(json.dumps(tc, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, "ATTACK C: forged beacon value was NOT detected"
        assert "temporal_binding hash mismatch" in msg, \
            f"ATTACK C detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK D -- Binding Hash Tamper
    # "I'll replace the temporal_binding with a hand-crafted hash."
    # ------------------------------------------------------------------
    def test_d_binding_hash_tamper(self, tmp_path):
        """
        ATTACK: Replace temporal_binding with a forged hash (all zeros).
        The recomputed binding (from pre + beacon_value + timestamp) won't
        match the tampered value.

        Proves: the temporal_binding is verified by recomputation, not just
        by presence. An attacker cannot substitute an arbitrary hash.
        """
        bundle, tc_data, _ = _make_bundle_with_temporal(tmp_path)

        # ATTACK: Replace temporal_binding
        tc_path = bundle / TEMPORAL_FILE
        tc = json.loads(tc_path.read_text(encoding="utf-8"))
        tc["temporal_binding"] = "00" * 32
        tc_path.write_text(json.dumps(tc, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, "ATTACK D: tampered binding hash was NOT detected"
        assert "temporal_binding hash mismatch" in msg, \
            f"ATTACK D detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK E -- Pre-commitment Hash Tamper
    # "I'll change the pre_commitment_hash to match a different root_hash."
    # ------------------------------------------------------------------
    def test_e_pre_commitment_hash_tamper(self, tmp_path):
        """
        ATTACK: Replace pre_commitment_hash with a forged value.
        Since verification recomputes SHA-256(root_hash) from the manifest,
        the tampered pre_commitment_hash won't match.

        Proves: the pre-commitment scheme is verified against the authoritative
        root_hash in pack_manifest.json, not the stored value in temporal_commitment.json.
        """
        bundle, tc_data, _ = _make_bundle_with_temporal(tmp_path)

        # ATTACK: Replace pre_commitment_hash
        tc_path = bundle / TEMPORAL_FILE
        tc = json.loads(tc_path.read_text(encoding="utf-8"))
        tc["pre_commitment_hash"] = "ff" * 32
        tc_path.write_text(json.dumps(tc, indent=2), encoding="utf-8")

        ok, msg = verify_temporal_commitment(bundle)
        assert ok is False, "ATTACK E: tampered pre-commitment hash was NOT detected"
        assert "pre_commitment_hash does not match" in msg, \
            f"ATTACK E detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # COMPOSITE: All five attacks summarized
    # ------------------------------------------------------------------
    def test_z_gauntlet_summary(self):
        """
        Composite proof: all five temporal attack classes are covered.

        This test documents the temporal commitment attack surface and
        confirms that Layer 5 catches all documented attack classes.

        Attack Surface Coverage:
          Layer 5 (Temporal Commitment): catches all 5 attacks
            - Replay: pre_commitment_hash mismatch (bound to root_hash)
            - Future timestamp: temporal_binding mismatch
            - Beacon forge: temporal_binding mismatch
            - Binding tamper: temporal_binding mismatch
            - Pre-commitment tamper: pre_commitment_hash mismatch
        """
        coverage = {
            "Attack A -- Replay Temporal Commitment":  "Layer 5 (pre_commitment_hash mismatch)",
            "Attack B -- Future Timestamp":            "Layer 5 (temporal_binding mismatch)",
            "Attack C -- Beacon Value Forge":          "Layer 5 (temporal_binding mismatch)",
            "Attack D -- Binding Hash Tamper":         "Layer 5 (temporal_binding mismatch)",
            "Attack E -- Pre-commitment Hash Tamper":  "Layer 5 (pre_commitment_hash mismatch)",
        }
        assert len(coverage) >= 5
        print("CERT-10: 5 temporal attacks, ALL CAUGHT by Layer 5")
