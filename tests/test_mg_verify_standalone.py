#!/usr/bin/env python3
"""Tests for scripts/mg_verify_standalone.py -- standalone bundle verifier.

Proves the standalone verifier correctly validates bundles through all 5 layers,
rejects tampered bundles, handles edge cases, and produces valid receipts and
JSON reports. This is the most important file for client trust: a client
receiving their first bundle uses this script to verify it independently.
"""

import hashlib
import hmac as hmac_mod
import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_verify_standalone import (
    verify_bundle,
    verify_layer1_integrity,
    verify_layer2_semantic,
    verify_layer3_step_chain,
    verify_layer4_signature,
    verify_layer5_temporal,
    format_receipt,
)


# ---- Helpers ---------------------------------------------------------------

def _hash_step(step_name, step_data, prev_hash):
    """Reproduce the Step Chain hash function."""
    content = json.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _build_valid_bundle(tmp_path, claim_id="ML_BENCH-01"):
    """Build a complete valid bundle with all 5 layers."""
    bundle_dir = tmp_path / "bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # Build evidence with step chain
    prev = _hash_step("init_params", {"seed": 42}, "genesis")
    trace = [{"step": 1, "name": "init_params", "hash": prev}]
    prev = _hash_step("compute", {"accuracy": 0.909}, prev)
    trace.append({"step": 2, "name": "compute", "hash": prev})
    prev = _hash_step("metrics", {"delta": 0.009}, prev)
    trace.append({"step": 3, "name": "metrics", "hash": prev})
    prev = _hash_step("threshold_check", {"passed": True, "threshold": 0.02}, prev)
    trace.append({"step": 4, "name": "threshold_check", "hash": prev})

    evidence = {
        "mtr_phase": claim_id,
        "inputs": {"seed": 42, "claimed_accuracy": 0.90},
        "result": {"pass": True, "actual_accuracy": 0.909},
        "execution_trace": trace,
        "trace_root_hash": prev,
    }
    evidence_path = bundle_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    # Build manifest
    sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    entries = [{"relpath": "evidence.json", "sha256": sha}]
    lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in entries)
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    manifest = {
        "protocol_version": 1,
        "files": entries,
        "root_hash": root_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    (bundle_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Build signature (Layer 4)
    raw_key = secrets.token_bytes(32)
    fingerprint = hashlib.sha256(raw_key).hexdigest()
    signature = hmac_mod.new(raw_key, root_hash.encode("utf-8"), hashlib.sha256).hexdigest()
    sig = {
        "version": "hmac-sha256-v1",
        "signed_root_hash": root_hash,
        "signature": signature,
        "key_fingerprint": fingerprint,
    }
    (bundle_dir / "bundle_signature.json").write_text(
        json.dumps(sig, indent=2), encoding="utf-8"
    )
    (bundle_dir / "signing_key.json").write_text(
        json.dumps({
            "version": "hmac-sha256-v1",
            "key_hex": raw_key.hex(),
            "fingerprint": fingerprint,
        }, indent=2), encoding="utf-8"
    )

    # Build temporal commitment (Layer 5)
    pre_commitment = hashlib.sha256(root_hash.encode("utf-8")).hexdigest()
    tc = {
        "version": "temporal-nist-v1",
        "root_hash": root_hash,
        "pre_commitment_hash": pre_commitment,
        "beacon_status": "unavailable",
        "local_timestamp": datetime.now(timezone.utc).isoformat(),
        "beacon_output_value": None,
        "beacon_timestamp": None,
        "temporal_binding": None,
    }
    (bundle_dir / "temporal_commitment.json").write_text(
        json.dumps(tc, indent=2), encoding="utf-8"
    )

    return bundle_dir


# ---- Full Pipeline Tests ---------------------------------------------------

class TestFullVerification:
    """Test the complete 5-layer verification pipeline."""

    def test_valid_bundle_passes(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        passed, results = verify_bundle(bundle)
        assert passed
        assert len(results) == 5
        assert all(ok for _, ok, _ in results)

    def test_missing_manifest_fails(self, tmp_path):
        bundle = tmp_path / "empty"
        bundle.mkdir()
        passed, results = verify_bundle(bundle)
        assert not passed
        assert "pack_manifest.json not found" in results[0][2]

    def test_tampered_evidence_fails(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        # Tamper with evidence file
        ev = bundle / "evidence.json"
        data = json.loads(ev.read_text(encoding="utf-8"))
        data["result"]["actual_accuracy"] = 0.50  # change the accuracy
        ev.write_text(json.dumps(data), encoding="utf-8")
        passed, results = verify_bundle(bundle)
        assert not passed
        assert "SHA-256 mismatch" in results[0][2]

    def test_tampered_step_chain_fails(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        # Tamper with trace_root_hash in evidence
        ev_path = bundle / "evidence.json"
        data = json.loads(ev_path.read_text(encoding="utf-8"))
        data["trace_root_hash"] = "00" * 32
        ev_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        # Rebuild manifest to match new file hash
        sha = hashlib.sha256(ev_path.read_bytes()).hexdigest()
        entries = [{"relpath": "evidence.json", "sha256": sha}]
        lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in entries)
        root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        manifest = {"protocol_version": 1, "files": entries, "root_hash": root_hash}
        (bundle / "pack_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        passed, results = verify_bundle(bundle)
        assert not passed
        # Layer 1 passes (manifest rebuilt), but Layer 3 should fail
        assert any("Step Chain broken" in msg for _, _, msg in results)


# ---- Layer 1 Tests --------------------------------------------------------

class TestLayer1Integrity:
    """Test SHA-256 integrity verification."""

    def test_valid_passes(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        ok, msg, manifest = verify_layer1_integrity(bundle)
        assert ok
        assert manifest is not None

    def test_missing_manifest(self, tmp_path):
        d = tmp_path / "no_manifest"
        d.mkdir()
        ok, msg, _ = verify_layer1_integrity(d)
        assert not ok

    def test_corrupt_json(self, tmp_path):
        d = tmp_path / "bad_json"
        d.mkdir()
        (d / "pack_manifest.json").write_text("{bad!", encoding="utf-8")
        ok, msg, _ = verify_layer1_integrity(d)
        assert not ok
        assert "Failed to load" in msg

    def test_missing_files_key(self, tmp_path):
        d = tmp_path / "no_files"
        d.mkdir()
        (d / "pack_manifest.json").write_text(
            json.dumps({"protocol_version": 1, "root_hash": "a" * 64}),
            encoding="utf-8",
        )
        ok, msg, _ = verify_layer1_integrity(d)
        assert not ok
        assert "files" in msg

    def test_path_traversal_rejected(self, tmp_path):
        d = tmp_path / "trav"
        d.mkdir()
        (d / "pack_manifest.json").write_text(
            json.dumps({
                "protocol_version": 1,
                "root_hash": "a" * 64,
                "files": [{"relpath": "../etc/passwd", "sha256": "a" * 64}],
            }),
            encoding="utf-8",
        )
        ok, msg, _ = verify_layer1_integrity(d)
        assert not ok
        assert "Invalid path" in msg

    def test_protocol_version_rollback(self, tmp_path):
        d = tmp_path / "rollback"
        d.mkdir()
        (d / "pack_manifest.json").write_text(
            json.dumps({
                "protocol_version": 0,
                "root_hash": "a" * 64,
                "files": [],
            }),
            encoding="utf-8",
        )
        ok, msg, _ = verify_layer1_integrity(d)
        assert not ok
        assert "minimum" in msg

    def test_protocol_version_string_rejected(self, tmp_path):
        d = tmp_path / "pvstr"
        d.mkdir()
        (d / "pack_manifest.json").write_text(
            json.dumps({
                "protocol_version": "1",
                "root_hash": "a" * 64,
                "files": [],
            }),
            encoding="utf-8",
        )
        ok, msg, _ = verify_layer1_integrity(d)
        assert not ok
        assert "integer" in msg

    def test_file_hash_mismatch(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        (bundle / "evidence.json").write_text("tampered!", encoding="utf-8")
        ok, msg, _ = verify_layer1_integrity(bundle)
        assert not ok
        assert "SHA-256 mismatch" in msg

    def test_missing_file(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        (bundle / "evidence.json").unlink()
        ok, msg, _ = verify_layer1_integrity(bundle)
        assert not ok
        assert "File missing" in msg

    def test_root_hash_mismatch(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        manifest["root_hash"] = "ff" * 32
        (bundle / "pack_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        ok, msg, _ = verify_layer1_integrity(bundle)
        assert not ok
        assert "Root hash mismatch" in msg


# ---- Layer 2 Tests --------------------------------------------------------

class TestLayer2Semantic:
    """Test semantic verification."""

    def test_no_evidence_passes(self, tmp_path):
        d = tmp_path / "no_ev"
        d.mkdir()
        ok, msg, info = verify_layer2_semantic(d)
        assert ok

    def test_valid_evidence_json(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        ok, msg, info = verify_layer2_semantic(bundle)
        assert ok
        assert info is not None
        assert info["claim_id"] == "ML_BENCH-01"

    def test_missing_mtr_phase(self, tmp_path):
        d = tmp_path / "no_mtr"
        d.mkdir()
        (d / "evidence.json").write_text(
            json.dumps({"execution_trace": [], "trace_root_hash": "a" * 64}),
            encoding="utf-8",
        )
        ok, msg, _ = verify_layer2_semantic(d)
        assert not ok
        assert "mtr_phase" in msg

    def test_corrupt_evidence_json(self, tmp_path):
        d = tmp_path / "corrupt"
        d.mkdir()
        (d / "evidence.json").write_text("{bad json!", encoding="utf-8")
        ok, msg, _ = verify_layer2_semantic(d)
        assert not ok


# ---- Layer 3 Tests --------------------------------------------------------

class TestLayer3StepChain:
    """Test step chain verification."""

    def test_valid_chain(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        ok, msg = verify_layer3_step_chain(bundle)
        assert ok

    def test_broken_root_hash(self, tmp_path):
        d = tmp_path / "broken"
        d.mkdir()
        (d / "evidence.json").write_text(json.dumps({
            "mtr_phase": "TEST",
            "execution_trace": [
                {"step": 1, "name": "a", "hash": "aa" * 32},
                {"step": 2, "name": "b", "hash": "bb" * 32},
                {"step": 3, "name": "c", "hash": "cc" * 32},
                {"step": 4, "name": "d", "hash": "dd" * 32},
            ],
            "trace_root_hash": "00" * 32,
        }), encoding="utf-8")
        ok, msg = verify_layer3_step_chain(d)
        assert not ok
        assert "Step Chain broken" in msg

    def test_wrong_step_count(self, tmp_path):
        d = tmp_path / "steps"
        d.mkdir()
        (d / "evidence.json").write_text(json.dumps({
            "mtr_phase": "TEST",
            "execution_trace": [
                {"step": 1, "name": "a", "hash": "aa" * 32},
                {"step": 2, "name": "b", "hash": "bb" * 32},
            ],
            "trace_root_hash": "bb" * 32,
        }), encoding="utf-8")
        ok, msg = verify_layer3_step_chain(d)
        assert not ok
        assert "4 steps" in msg

    def test_invalid_step_hash(self, tmp_path):
        d = tmp_path / "badhash"
        d.mkdir()
        (d / "evidence.json").write_text(json.dumps({
            "mtr_phase": "TEST",
            "execution_trace": [
                {"step": 1, "name": "a", "hash": "not-a-hash"},
                {"step": 2, "name": "b", "hash": "bb" * 32},
                {"step": 3, "name": "c", "hash": "cc" * 32},
                {"step": 4, "name": "d", "hash": "dd" * 32},
            ],
            "trace_root_hash": "dd" * 32,
        }), encoding="utf-8")
        ok, msg = verify_layer3_step_chain(d)
        assert not ok
        assert "invalid hash" in msg

    def test_no_evidence_passes(self, tmp_path):
        d = tmp_path / "nothing"
        d.mkdir()
        ok, msg = verify_layer3_step_chain(d)
        assert ok


# ---- Layer 4 Tests --------------------------------------------------------

class TestLayer4Signature:
    """Test bundle signature verification."""

    def test_no_signature_passes(self, tmp_path):
        d = tmp_path / "nosig"
        d.mkdir()
        ok, msg = verify_layer4_signature(d, {"root_hash": "a" * 64})
        assert ok

    def test_valid_signature(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        ok, msg = verify_layer4_signature(bundle, manifest)
        assert ok
        assert "HMAC-SHA256 valid" in msg

    def test_wrong_root_hash_in_signature(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        sig = json.loads((bundle / "bundle_signature.json").read_text(encoding="utf-8"))
        sig["signed_root_hash"] = "ff" * 32
        (bundle / "bundle_signature.json").write_text(
            json.dumps(sig), encoding="utf-8"
        )
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        ok, msg = verify_layer4_signature(bundle, manifest)
        assert not ok

    def test_tampered_signature_fails(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        sig = json.loads((bundle / "bundle_signature.json").read_text(encoding="utf-8"))
        sig["signature"] = "00" * 32
        (bundle / "bundle_signature.json").write_text(
            json.dumps(sig), encoding="utf-8"
        )
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        ok, msg = verify_layer4_signature(bundle, manifest)
        assert not ok
        assert "failed" in msg.lower()


# ---- Layer 5 Tests --------------------------------------------------------

class TestLayer5Temporal:
    """Test temporal commitment verification."""

    def test_no_temporal_passes(self, tmp_path):
        d = tmp_path / "notc"
        d.mkdir()
        ok, msg = verify_layer5_temporal(d, {"root_hash": "a" * 64})
        assert ok

    def test_valid_local_timestamp(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        ok, msg = verify_layer5_temporal(bundle, manifest)
        assert ok
        assert "Local timestamp" in msg

    def test_tampered_pre_commitment(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        tc = json.loads((bundle / "temporal_commitment.json").read_text(encoding="utf-8"))
        tc["pre_commitment_hash"] = "00" * 32
        (bundle / "temporal_commitment.json").write_text(
            json.dumps(tc), encoding="utf-8"
        )
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        ok, msg = verify_layer5_temporal(bundle, manifest)
        assert not ok
        assert "Pre-commitment hash mismatch" in msg


# ---- Receipt Tests ---------------------------------------------------------

class TestReceipt:
    """Test receipt generation."""

    def test_receipt_contains_claim(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        _, results = verify_bundle(bundle)
        claim_info = {
            "claim_id": "ML_BENCH-01",
            "evidence": {"result": {"actual_accuracy": 0.909, "pass": True}},
        }
        receipt = format_receipt(bundle, results, claim_info)
        assert "ML_BENCH-01" in receipt
        assert "PASS" in receipt
        assert "VERIFICATION RECEIPT" in receipt

    def test_receipt_shows_anchor_for_mtr1(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path, claim_id="MTR-1")
        _, results = verify_bundle(bundle)
        claim_info = {
            "claim_id": "MTR-1",
            "evidence": {"result": {"relative_error": 0.005}},
        }
        receipt = format_receipt(bundle, results, claim_info)
        assert "70 GPa" in receipt

    def test_receipt_shows_provenance_for_non_anchored(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        _, results = verify_bundle(bundle)
        claim_info = {
            "claim_id": "ML_BENCH-01",
            "evidence": {"result": {"pass": True}},
        }
        receipt = format_receipt(bundle, results, claim_info)
        assert "provenance only" in receipt.lower()

    def test_receipt_with_no_claim_info(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        _, results = verify_bundle(bundle)
        receipt = format_receipt(bundle, results, None)
        assert "VERIFICATION RECEIPT" in receipt
        assert "PASS" in receipt


# ---- CLI Tests -------------------------------------------------------------

class TestCLI:
    """Test CLI invocation."""

    def test_cli_valid_bundle(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_verify_standalone.py"),
             str(bundle)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "PASS" in result.stdout

    def test_cli_nonexistent_bundle(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_verify_standalone.py"),
             "/nonexistent/path"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1

    def test_cli_json_report(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        report_path = tmp_path / "report.json"
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_verify_standalone.py"),
             str(bundle), "--json", str(report_path)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert report_path.exists()
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["result"] == "PASS"
        assert len(report["layers"]) == 5

    def test_cli_receipt(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_verify_standalone.py"),
             str(bundle), "--receipt"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert "VERIFICATION RECEIPT" in result.stdout

    def test_cli_tampered_bundle_fails(self, tmp_path):
        bundle = _build_valid_bundle(tmp_path)
        (bundle / "evidence.json").write_text("TAMPERED", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_verify_standalone.py"),
             str(bundle)],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 1
        assert "FAIL" in result.stdout

    def test_cli_version(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_verify_standalone.py"),
             "--version"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "1.0.0" in result.stdout


# ---- Symlink Attack Test ---------------------------------------------------

class TestSymlinkAttack:
    """Test that symlinks in bundles are rejected (attacker lens finding)."""

    @pytest.mark.skipif(sys.platform == "win32" and not hasattr(os, "symlink"),
                        reason="Symlinks may require admin on Windows")
    def test_symlink_in_bundle_rejected(self, tmp_path):
        """A bundle containing a symlink should be rejected by Layer 1."""
        bundle = _build_valid_bundle(tmp_path)

        # Create a symlink inside the bundle
        target = tmp_path / "secret.txt"
        target.write_text("secret data", encoding="utf-8")
        link = bundle / "link.txt"
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("Cannot create symlinks (requires elevated privileges)")

        # Add the symlink to manifest
        sha = hashlib.sha256(link.read_bytes()).hexdigest()
        manifest = json.loads((bundle / "pack_manifest.json").read_text(encoding="utf-8"))
        manifest["files"].append({"relpath": "link.txt", "sha256": sha})
        # Recompute root hash
        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(manifest["files"], key=lambda x: x["relpath"])
        )
        manifest["root_hash"] = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        (bundle / "pack_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )

        ok, msg, _ = verify_layer1_integrity(bundle)
        assert not ok
        assert "Symlink" in msg


