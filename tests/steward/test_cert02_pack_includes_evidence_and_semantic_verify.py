#!/usr/bin/env python3
"""
CERT-02 / PACK-02: Evidence-Inclusive Submission Pack + Semantic Verify.

Tests that:
1) Pack builder includes evidence bundles when --include-evidence is set
2) Pack contains pack_manifest.json, evidence_index.json, evidence/<CLAIM_ID>/{normal,canary}/*
3) mg verify passes for a valid evidence-inclusive pack
4) mg verify fails with clear message when semantic invariants are violated
   (e.g. run_artifact missing job_snapshot) even if integrity (sha/root_hash) passes
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

DATASET_RELPATH = "tests/fixtures/data01/al6061_stress_strain_sample.csv"


def _run_mtr1_evidence(source_reports_dir: Path, canary_mode: bool) -> None:
    """Run MTR-1 (normal or canary) with dataset + UQ; write progress_runs and ledger_snapshots."""
    import os

    from backend.ledger.ledger_store import LedgerStore
    from backend.progress.mtr1_calibration import JOB_KIND
    from backend.progress.runner import ProgressRunner
    from backend.progress.store import JobStore

    os.environ["MG_PROGRESS_ARTIFACT_DIR"] = str(source_reports_dir)
    source_reports_dir.mkdir(parents=True, exist_ok=True)
    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(source_reports_dir / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)
    payload = {
        "kind": JOB_KIND,
        "dataset_relpath": DATASET_RELPATH,
        "elastic_strain_max": 0.002,
        "uq_samples": 200,
        "uq_seed": 42,
    }
    job = runner.create_job(payload=payload)
    runner.run_job(job.job_id, canary_mode=canary_mode)


def _mg(args: list[str]) -> tuple[int, str]:
    """Run mg CLI; return (exit_code, combined stdout+stderr)."""
    result = subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "mg.py")] + args,
        cwd=str(_ROOT),
        capture_output=True,
        text=True,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def _build_pack_with_evidence(tmp_path: Path, source_reports_dir: Path, pack_out: Path) -> int:
    """Build pack with --include-evidence. Returns exit code."""
    return _mg([
        "pack", "build",
        "--output", str(pack_out),
        "--include-evidence",
        "--source-reports-dir", str(source_reports_dir),
    ])[0]


def _verify_pack(pack_dir: Path) -> tuple[int, str]:
    """Run mg verify --pack. Returns (exit_code, output)."""
    return _mg(["verify", "--pack", str(pack_dir)])


class TestCert02PackIncludesEvidenceAndSemanticVerify:
    """CERT-02 evidence-inclusive pack and semantic verification."""

    def test_pack_includes_evidence_and_verify_passes(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Generate MTR-1 evidence, build pack with evidence, assert structure, verify passes."""
        monkeypatch.delenv("MG_PROGRESS_ARTIFACT_DIR", raising=False)

        source_reports_dir = tmp_path / "source_reports"
        pack_out = tmp_path / "pack_out"

        _run_mtr1_evidence(source_reports_dir, canary_mode=False)
        _run_mtr1_evidence(source_reports_dir, canary_mode=True)

        rc = _build_pack_with_evidence(tmp_path, source_reports_dir, pack_out)
        assert rc == 0, "Pack build should succeed"

        assert (pack_out / "pack_manifest.json").exists()
        assert (pack_out / "evidence_index.json").exists()
        assert (pack_out / "evidence" / "MTR-1" / "normal" / "run_artifact.json").exists()
        assert (pack_out / "evidence" / "MTR-1" / "normal" / "ledger_snapshot.jsonl").exists()
        assert (pack_out / "evidence" / "MTR-1" / "canary" / "run_artifact.json").exists()
        assert (pack_out / "evidence" / "MTR-1" / "canary" / "ledger_snapshot.jsonl").exists()

        vrc, vout = _verify_pack(pack_out)
        assert vrc == 0, f"mg verify should PASS: {vout}"
        assert "PASS" in vout

    def test_semantic_negative_missing_job_snapshot_fails_verify(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Corrupt run_artifact (remove job_snapshot), update manifest so integrity passes; verify must FAIL."""
        monkeypatch.delenv("MG_PROGRESS_ARTIFACT_DIR", raising=False)

        source_reports_dir = tmp_path / "source_reports"
        pack_out = tmp_path / "pack_out"

        _run_mtr1_evidence(source_reports_dir, canary_mode=False)
        _run_mtr1_evidence(source_reports_dir, canary_mode=True)

        rc = _build_pack_with_evidence(tmp_path, source_reports_dir, pack_out)
        assert rc == 0

        run_artifact_path = pack_out / "evidence" / "MTR-1" / "normal" / "run_artifact.json"
        data = json.loads(run_artifact_path.read_text(encoding="utf-8"))
        assert "job_snapshot" in data
        del data["job_snapshot"]
        run_artifact_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        manifest_path = pack_out / "pack_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        run_rel = "evidence/MTR-1/normal/run_artifact.json"
        new_sha = hashlib.sha256(run_artifact_path.read_bytes()).hexdigest()
        for e in manifest["files"]:
            if e["relpath"] == run_rel:
                e["sha256"] = new_sha
                e["bytes"] = run_artifact_path.stat().st_size
                break

        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(manifest["files"], key=lambda x: x["relpath"])
        )
        manifest["root_hash"] = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        vrc, vout = _verify_pack(pack_out)
        assert vrc != 0, f"mg verify must FAIL on semantic violation: {vout}"
        assert "job_snapshot" in vout or "missing required key" in vout


# ---------------------------------------------------------------------------
# Semantic Edge Case Tests (SEM-01, SEM-02, SEM-03)
# ---------------------------------------------------------------------------

from scripts.mg import _verify_semantic  # noqa: E402

_VALID_HASH = "a" * 64
_SEM_JOB_KIND = "dtfem1_displacement_verification"


def _make_sem_pack(tmp_path, claim_id="DT-FEM-01",
                   job_kind="dtfem1_displacement_verification",
                   mtr_phase="DT-FEM-01", trace_root_hash="d" * 64,
                   execution_trace=None, extra_result_fields=None,
                   extra_input_fields=None, result_overrides=None,
                   evidence_index_overrides=None):
    """Build minimal pack with customizable domain result fields for semantic tests."""
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir(exist_ok=True)
    ev_dir = pack_dir / "evidence" / claim_id / "normal"
    ev_dir.mkdir(parents=True, exist_ok=True)

    if execution_trace is None:
        execution_trace = [
            {"step": 1, "name": "init_params", "hash": "a" * 64},
            {"step": 2, "name": "generate_fem_pair", "hash": "b" * 64},
            {"step": 3, "name": "compute_rel_err", "hash": "c" * 64},
            {"step": 4, "name": "threshold_check", "hash": "d" * 64},
        ]

    inputs = {
        "seed": 42,
        "reference_value": 1.0,
        "rel_err_threshold": 0.02,
        "noise_scale": 0.005,
        "quantity": "displacement_mm",
        "units": "mm",
    }
    if extra_input_fields:
        inputs.update(extra_input_fields)

    result_block = {
        "fem_value": 1.001, "reference_value": 1.0,
        "rel_err": 0.001, "rel_err_threshold": 0.02,
        "pass": True, "quantity": "displacement_mm",
        "units": "mm", "method": "fem_vs_reference_rel_err",
        "algorithm_version": "v1",
    }
    if result_overrides:
        result_block.update(result_overrides)

    domain_result = {
        "mtr_phase": mtr_phase,
        "inputs": inputs,
        "result": result_block,
        "execution_trace": execution_trace,
        "trace_root_hash": trace_root_hash,
    }
    if extra_result_fields:
        domain_result.update(extra_result_fields)

    run_artifact = {
        "w6_phase": "W6-A5", "kind": "success",
        "job_id": "job-test-sem", "trace_id": "trace-test-sem",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": "job-test-sem", "status": "SUCCEEDED",
            "payload": {"kind": job_kind},
            "result": domain_result,
        },
        "ledger_action": "job_completed", "persisted_at": "2026-03-18T00:00:00Z",
    }

    (ev_dir / "run_artifact.json").write_text(
        json.dumps(run_artifact), encoding="utf-8")
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        json.dumps({"trace_id": "trace-test-sem", "action": "job_completed",
                     "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
        encoding="utf-8")

    evidence_index = {
        claim_id: {
            "job_kind": job_kind,
            "normal": {
                "run_relpath": f"evidence/{claim_id}/normal/run_artifact.json",
                "ledger_relpath": f"evidence/{claim_id}/normal/ledger_snapshot.jsonl",
            },
        }
    }
    if evidence_index_overrides:
        evidence_index[claim_id].update(evidence_index_overrides)

    index_path = pack_dir / "evidence_index.json"
    index_path.write_text(json.dumps(evidence_index), encoding="utf-8")
    return pack_dir, index_path


class TestSemanticPartialFields:
    """SEM-01: Partial fields -- null values in required fields."""

    def test_a_null_mtr_phase_rejected(self, tmp_path):
        """domain result has mtr_phase=None -> FAIL."""
        pack_dir, index_path = _make_sem_pack(tmp_path, mtr_phase=None)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for null mtr_phase, got PASS: {msg}"
        assert "mtr_phase" in msg

    def test_b_null_trace_root_hash_rejected(self, tmp_path):
        """domain has trace_root_hash=None but execution_trace present -> FAIL."""
        pack_dir, index_path = _make_sem_pack(tmp_path, trace_root_hash=None)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for null trace_root_hash with trace: {msg}"

    def test_c_missing_execution_trace_with_null_root(self, tmp_path):
        """both execution_trace=None and trace_root_hash=None -> PASS (backward compatible)."""
        # Build a normal pack, then patch both fields to None
        pack_dir, index_path = _make_sem_pack(tmp_path)
        run_path = pack_dir / "evidence" / "DT-FEM-01" / "normal" / "run_artifact.json"
        art = json.loads(run_path.read_text(encoding="utf-8"))
        del art["job_snapshot"]["result"]["execution_trace"]
        del art["job_snapshot"]["result"]["trace_root_hash"]
        run_path.write_text(json.dumps(art), encoding="utf-8")
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS for both absent (backward compat), got: {msg}"

    def test_d_partial_step_hash_null(self, tmp_path):
        """execution_trace step has hash=None -> FAIL with 'invalid hash'."""
        trace = [
            {"step": 1, "name": "init_params", "hash": "a" * 64},
            {"step": 2, "name": "generate_fem_pair", "hash": None},
            {"step": 3, "name": "compute_rel_err", "hash": "c" * 64},
            {"step": 4, "name": "threshold_check", "hash": "d" * 64},
        ]
        pack_dir, index_path = _make_sem_pack(tmp_path, execution_trace=trace)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for null step hash, got: {msg}"
        assert "invalid hash" in msg.lower()


class TestSemanticExtraFields:
    """SEM-02: Extra unexpected fields -- forward compatible but logged."""

    def test_a_extra_fields_in_result_passes(self, tmp_path):
        """domain result has extra key 'bonus_field' -> PASS (forward compatible)."""
        pack_dir, index_path = _make_sem_pack(
            tmp_path, extra_result_fields={"bonus_field": "surprise"})
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS for extra fields, got: {msg}"

    def test_b_extra_fields_in_inputs_passes(self, tmp_path):
        """inputs has extra key 'debug_mode' -> PASS."""
        pack_dir, index_path = _make_sem_pack(
            tmp_path, extra_input_fields={"debug_mode": True})
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS for extra input fields, got: {msg}"

    def test_c_extra_fields_logged_in_report(self, tmp_path):
        """extra fields in domain result -> ok=True AND warnings list mentions the field."""
        pack_dir, index_path = _make_sem_pack(
            tmp_path, extra_result_fields={"bonus_field": "surprise"})
        ok, msg, warnings = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS, got: {msg}"
        assert "PASS" in msg
        assert any("bonus_field" in w for w in warnings), \
            f"Extra fields must be logged in warnings, got: {warnings}"


class TestSemanticMeaninglessValues:
    """SEM-03: Semantically meaningless values -- empty strings, zero/negative thresholds."""

    def test_a_empty_mtr_phase_rejected(self, tmp_path):
        """mtr_phase='' -> FAIL."""
        pack_dir, index_path = _make_sem_pack(tmp_path, mtr_phase="")
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for empty mtr_phase, got: {msg}"
        assert "mtr_phase" in msg

    def test_b_zero_threshold_rejected(self, tmp_path):
        """result has rel_err_threshold=0 -> FAIL."""
        pack_dir, index_path = _make_sem_pack(
            tmp_path, result_overrides={"rel_err_threshold": 0})
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for zero threshold, got: {msg}"
        assert "zero" in msg.lower() or "threshold" in msg.lower()

    def test_c_negative_threshold_rejected(self, tmp_path):
        """result has rel_err_threshold=-0.01 -> FAIL."""
        pack_dir, index_path = _make_sem_pack(
            tmp_path, result_overrides={"rel_err_threshold": -0.01})
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for negative threshold, got: {msg}"
        assert "negative" in msg.lower() or "threshold" in msg.lower()

    def test_d_empty_job_kind_in_evidence_index_rejected(self, tmp_path):
        """evidence_index has job_kind='' -> FAIL."""
        pack_dir, index_path = _make_sem_pack(
            tmp_path, job_kind="")
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for empty job_kind, got: {msg}"
