#!/usr/bin/env python3
"""Tests for scripts/mg_client.py -- client-facing bundle generator."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_client import (
    DOMAIN_CONFIG,
    _create_pack_manifest,
    _create_temporal_commitment,
    _hash_step,
    _rebuild_manifest,
    _sign_bundle,
    create_bundle,
    run_claim,
    verify_bundle,
)


# ---------------------------------------------------------------------------
# _hash_step
# ---------------------------------------------------------------------------

class TestHashStep:
    def test_deterministic(self):
        h1 = _hash_step("init", {"a": 1}, "genesis")
        h2 = _hash_step("init", {"a": 1}, "genesis")
        assert h1 == h2

    def test_different_data(self):
        h1 = _hash_step("init", {"a": 1}, "genesis")
        h2 = _hash_step("init", {"a": 2}, "genesis")
        assert h1 != h2

    def test_chain_dependency(self):
        h1 = _hash_step("s1", {}, "genesis")
        h2 = _hash_step("s1", {}, "other_genesis")
        assert h1 != h2

    def test_returns_hex_string(self):
        h = _hash_step("x", {}, "g")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# run_claim
# ---------------------------------------------------------------------------

class TestRunClaim:
    def test_ml_domain(self):
        result = run_claim("ml")
        assert result["mtr_phase"] == "ML_BENCH-01"
        assert result["result"]["pass"] is True
        assert "execution_trace" in result
        assert "trace_root_hash" in result

    def test_pharma_domain(self):
        result = run_claim("pharma")
        assert result["mtr_phase"] == "PHARMA-01"
        assert "result" in result

    def test_finance_domain(self):
        result = run_claim("finance")
        assert result["mtr_phase"] == "FINRISK-01"
        assert "result" in result

    def test_materials_domain(self):
        result = run_claim("materials")
        assert result["mtr_phase"] == "MTR-1"
        assert "result" in result

    def test_digital_twin_domain(self):
        result = run_claim("digital_twin")
        assert result["mtr_phase"] == "DT-FEM-01"
        assert "result" in result

    def test_unknown_domain(self):
        with pytest.raises(ValueError, match="Unknown domain"):
            run_claim("quantum")

    def test_all_domains_have_trace(self):
        for domain in DOMAIN_CONFIG:
            result = run_claim(domain)
            assert "execution_trace" in result, f"{domain} missing execution_trace"
            assert "trace_root_hash" in result, f"{domain} missing trace_root_hash"

    def test_user_data_file(self, tmp_path):
        data_file = tmp_path / "params.json"
        data_file.write_text(json.dumps({"seed": 99, "claimed_accuracy": 0.85}))
        result = run_claim("ml", user_data_path=str(data_file))
        assert result["mtr_phase"] == "ML_BENCH-01"

    def test_user_data_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            run_claim("ml", user_data_path="/nonexistent/file.json")


# ---------------------------------------------------------------------------
# create_bundle + verify_bundle
# ---------------------------------------------------------------------------

class TestCreateAndVerifyBundle:
    def test_full_pipeline_ml(self, tmp_path):
        result = run_claim("ml")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))
        assert (bundle_dir / "evidence.json").exists()
        assert (bundle_dir / "pack_manifest.json").exists()
        assert (bundle_dir / "bundle_signature.json").exists()
        assert (bundle_dir / "temporal_commitment.json").exists()
        assert (bundle_dir / "signing_key.json").exists()

        passed, layer_results = verify_bundle(bundle_dir)
        assert passed is True
        assert len(layer_results) == 5
        for name, ok, _ in layer_results:
            assert ok is True, f"{name} failed"

    def test_full_pipeline_pharma(self, tmp_path):
        result = run_claim("pharma")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))
        passed, _ = verify_bundle(bundle_dir)
        assert passed is True

    def test_full_pipeline_finance(self, tmp_path):
        result = run_claim("finance")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))
        passed, _ = verify_bundle(bundle_dir)
        assert passed is True

    def test_full_pipeline_materials(self, tmp_path):
        result = run_claim("materials")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))
        passed, _ = verify_bundle(bundle_dir)
        assert passed is True

    def test_full_pipeline_digital_twin(self, tmp_path):
        result = run_claim("digital_twin")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))
        passed, _ = verify_bundle(bundle_dir)
        assert passed is True

    def test_auto_tempdir_if_no_output(self):
        result = run_claim("ml")
        bundle_dir = create_bundle(result)
        try:
            assert bundle_dir.exists()
            passed, _ = verify_bundle(bundle_dir)
            assert passed is True
        finally:
            shutil.rmtree(bundle_dir)

    def test_overwrite_existing_bundle(self, tmp_path):
        out = tmp_path / "bundle"
        out.mkdir()
        (out / "old_file.txt").write_text("old")
        result = run_claim("ml")
        bundle_dir = create_bundle(result, output_dir=str(out))
        assert not (bundle_dir / "old_file.txt").exists()


# ---------------------------------------------------------------------------
# verify_bundle edge cases
# ---------------------------------------------------------------------------

class TestVerifyBundleEdgeCases:
    def test_missing_manifest(self, tmp_path):
        passed, results = verify_bundle(tmp_path)
        assert passed is False
        assert "pack_manifest.json not found" in results[0][2]

    def test_invalid_protocol_version(self, tmp_path):
        manifest = {"protocol_version": "bad", "files": [], "root_hash": "abc"}
        (tmp_path / "pack_manifest.json").write_text(json.dumps(manifest))
        passed, results = verify_bundle(tmp_path)
        assert passed is False

    def test_missing_file_in_manifest(self, tmp_path):
        manifest = {
            "protocol_version": 1,
            "files": [{"relpath": "missing.json", "sha256": "abc"}],
            "root_hash": "abc",
        }
        (tmp_path / "pack_manifest.json").write_text(json.dumps(manifest))
        passed, results = verify_bundle(tmp_path)
        assert passed is False
        assert "Missing file" in results[0][2]

    def test_tampered_evidence(self, tmp_path):
        result = run_claim("ml")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))

        # Tamper with evidence
        ev_path = bundle_dir / "evidence.json"
        ev = json.loads(ev_path.read_text())
        ev["result"]["pass"] = False
        ev_path.write_text(json.dumps(ev))

        passed, results = verify_bundle(bundle_dir)
        assert passed is False
        # Layer 1 should catch the hash mismatch
        assert results[0][1] is False

    def test_tampered_signature(self, tmp_path):
        result = run_claim("ml")
        bundle_dir = create_bundle(result, output_dir=str(tmp_path / "bundle"))

        sig_path = bundle_dir / "bundle_signature.json"
        sig = json.loads(sig_path.read_text())
        sig["signature"] = "0" * 64
        sig_path.write_text(json.dumps(sig))

        passed, results = verify_bundle(bundle_dir)
        # Signature is not in manifest, so Layer 1 passes but Layer 4 fails
        l4_results = [r for r in results if "Layer 4" in r[0]]
        assert len(l4_results) == 1
        assert l4_results[0][1] is False

    def test_no_evidence_file(self, tmp_path):
        """Bundle with just a manifest (no evidence) -- layers 2-3 skip gracefully."""
        import hashlib

        ev = tmp_path / "data.txt"
        ev.write_text("hello")
        sha = hashlib.sha256(ev.read_bytes()).hexdigest()
        entries = [{"relpath": "data.txt", "sha256": sha}]
        lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in entries)
        root = hashlib.sha256(lines.encode()).hexdigest()
        manifest = {"protocol_version": 1, "files": entries, "root_hash": root}
        (tmp_path / "pack_manifest.json").write_text(json.dumps(manifest))

        passed, results = verify_bundle(tmp_path)
        assert passed is True
        assert len(results) == 5


# ---------------------------------------------------------------------------
# _create_pack_manifest
# ---------------------------------------------------------------------------

class TestCreatePackManifest:
    def test_creates_manifest(self, tmp_path):
        f1 = tmp_path / "a.json"
        f1.write_text('{"x":1}')
        manifest = _create_pack_manifest(tmp_path, [f1])
        assert "root_hash" in manifest
        assert len(manifest["files"]) == 1
        assert (tmp_path / "pack_manifest.json").exists()

    def test_root_hash_deterministic(self, tmp_path):
        f1 = tmp_path / "a.json"
        f1.write_text('{"x":1}')
        m1 = _create_pack_manifest(tmp_path, [f1])
        m2 = _create_pack_manifest(tmp_path, [f1])
        assert m1["root_hash"] == m2["root_hash"]


# ---------------------------------------------------------------------------
# _sign_bundle / _create_temporal_commitment
# ---------------------------------------------------------------------------

class TestSignAndTemporal:
    def _make_bundle(self, tmp_path):
        ev = tmp_path / "evidence.json"
        h1 = _hash_step("init_params", {"seed": 42}, "genesis")
        h2 = _hash_step("compute", {"x": 1}, h1)
        h3 = _hash_step("metrics", {"acc": 0.9}, h2)
        h4 = _hash_step("threshold_check", {"passed": True}, h3)
        evidence = {
            "mtr_phase": "TEST-01",
            "inputs": {"seed": 42},
            "result": {"pass": True},
            "execution_trace": [
                {"step": 1, "name": "init_params", "hash": h1},
                {"step": 2, "name": "compute", "hash": h2},
                {"step": 3, "name": "metrics", "hash": h3},
                {"step": 4, "name": "threshold_check", "hash": h4},
            ],
            "trace_root_hash": h4,
        }
        ev.write_text(json.dumps(evidence))
        _rebuild_manifest(tmp_path)
        return tmp_path

    def test_sign_creates_files(self, tmp_path):
        self._make_bundle(tmp_path)
        sig = _sign_bundle(tmp_path)
        assert "signature" in sig
        assert (tmp_path / "bundle_signature.json").exists()
        assert (tmp_path / "signing_key.json").exists()

    def test_temporal_creates_file(self, tmp_path):
        self._make_bundle(tmp_path)
        tc = _create_temporal_commitment(tmp_path)
        assert tc["beacon_status"] == "unavailable"
        assert (tmp_path / "temporal_commitment.json").exists()

    def test_sign_then_verify(self, tmp_path):
        self._make_bundle(tmp_path)
        _sign_bundle(tmp_path)
        _create_temporal_commitment(tmp_path)
        passed, results = verify_bundle(tmp_path)
        assert passed is True


# ---------------------------------------------------------------------------
# CLI smoke tests
# ---------------------------------------------------------------------------

class TestCLI:
    def test_demo_exit_code(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_client.py"), "--demo"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        assert proc.returncode == 0
        assert "PASS" in proc.stdout

    def test_verify_nonexistent(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_client.py"), "--verify", "/tmp/nonexistent_bundle_xyz"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        assert proc.returncode == 1

    def test_no_args_shows_help(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_client.py")],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        assert proc.returncode == 0
        assert "mg_client" in proc.stdout or "usage" in proc.stdout.lower()

    def test_domain_ml_with_output(self, tmp_path):
        out = tmp_path / "out_bundle"
        proc = subprocess.run(
            [
                sys.executable, str(REPO_ROOT / "scripts" / "mg_client.py"),
                "--domain", "ml", "--output", str(out),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        assert proc.returncode == 0
        assert (out / "evidence.json").exists()

    def test_domain_unknown(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "mg_client.py"), "--domain", "quantum"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        assert proc.returncode != 0


# ---------------------------------------------------------------------------
# DOMAIN_CONFIG completeness
# ---------------------------------------------------------------------------

class TestDomainConfig:
    def test_all_required_domains(self):
        required = {"ml", "pharma", "finance", "materials", "digital_twin"}
        assert required.issubset(set(DOMAIN_CONFIG.keys()))

    def test_each_domain_has_keys(self):
        for domain, cfg in DOMAIN_CONFIG.items():
            assert "claim" in cfg, f"{domain} missing claim"
            assert "module" in cfg, f"{domain} missing module"
            assert "func" in cfg, f"{domain} missing func"
            assert "defaults" in cfg, f"{domain} missing defaults"
