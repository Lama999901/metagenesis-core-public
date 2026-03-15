#!/usr/bin/env python3
"""
DATA-PIPE-01 Dataset Quality Certificate - Tests.

Purpose: E2E, quality checks detect bad CSV, reproducibility shape.
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

DATASET_RELPATH = "tests/fixtures/data01/al6061_stress_strain_sample.csv"

from backend.progress.runner import ProgressRunner
from backend.progress.store import JobStore
from backend.ledger.ledger_store import LedgerStore
from backend.progress.datapipe1_quality_certificate import JOB_KIND, run_certificate

DATAPIPE1_PAYLOAD = {
    "kind": JOB_KIND,
    "seed": 42,
    "dataset_relpath": DATASET_RELPATH,
    "required_columns": ["strain", "stress"],
    "numeric_columns": ["strain", "stress"],
    "ranges_json": json.dumps({"strain": {"min": 0, "max": 0.01}, "stress": {"min": 0}}),
}


def _run_datapipe1_job(artifact_dir: Path, payload: dict, canary_mode: bool = False):
    """Create DATA-PIPE-01 job, run, return (trace_id, job)."""
    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(artifact_dir / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)
    job = runner.create_job(payload=payload)
    runner.run_job(job.job_id, canary_mode=canary_mode)
    return job.trace_id, job


def _normalize_evidence(obj):
    """Strip trace_id, timestamps, durations, paths for comparison."""
    if isinstance(obj, dict):
        skip = {
            "trace_id", "job_id", "created_at", "started_at", "completed_at",
            "persisted_at", "execution_time_ms", "path"
        }
        return {k: _normalize_evidence(v) for k, v in obj.items() if k not in skip}
    if isinstance(obj, list):
        return [_normalize_evidence(i) for i in obj]
    return obj


def _key_paths(obj, prefix=""):
    """Set of nested key paths."""
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(f"{prefix}{k}")
            keys.update(_key_paths(v, f"{prefix}{k}."))
    elif isinstance(obj, list) and obj:
        keys.update(_key_paths(obj[0], f"{prefix}[]."))
    return keys


class TestDatapipe01QualityCertificate:
    """DATA-PIPE-01: E2E, quality checks, reproducibility."""

    def test_a_e2e_normal_canary_artifacts_evidence(self, tmp_path, monkeypatch):
        """E2E: normal+canary job runs; artifacts exist; evidence index/API; job_snapshot.result has dataset.sha256."""
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))

        trace1, job1 = _run_datapipe1_job(tmp_path, DATAPIPE1_PAYLOAD, canary_mode=False)
        trace2, job2 = _run_datapipe1_job(tmp_path, DATAPIPE1_PAYLOAD, canary_mode=True)

        progress_runs = tmp_path / "progress_runs"
        ledger_snapshots = tmp_path / "ledger_snapshots"
        assert progress_runs.exists() and ledger_snapshots.exists()
        run_files = list(progress_runs.glob("*.json"))
        assert len(run_files) >= 2

        for job in (job1, job2):
            assert job.result is not None
            assert job.result.get("domain") == "DATA"
            assert job.result.get("claim_id") == "DATA-PIPE-01"
            assert "inputs" in job.result
            assert "result" in job.result
            ds = job.result["inputs"].get("dataset", {})
            assert "sha256" in ds
            assert len(ds["sha256"]) == 64
            r = job.result["result"]
            assert "pass" in r
            assert "issues" in r
            assert "metrics" in r

        try:
            from fastapi.testclient import TestClient
            from fastapi import FastAPI
            from api.evidence_api import evidence_router
            use_client = True
        except ImportError:
            use_client = False
            from backend.progress.evidence_index import build_evidence_index

        if use_client:
            app = FastAPI()
            app.include_router(evidence_router)
            client = TestClient(app)
            for tid in (trace1, trace2):
                resp = client.get(f"/api/evidence/{tid}")
                assert resp.status_code == 200
                data = resp.json()
                assert data["trace_id"] == tid
                assert "artifacts" in data
        else:
            index = build_evidence_index(tmp_path)
            for tid in (trace1, trace2):
                assert tid in index
                assert index[tid]["trace_id"] == tid

    def test_b_quality_checks_detect_bad_csv(self, tmp_path):
        """Quality checks detect intentionally bad CSV (missing col, bad numeric)."""
        import tempfile
        with tempfile.TemporaryDirectory(dir=str(_ROOT)) as tmp:
            tmp_dir = Path(tmp)
            bad_numeric = tmp_dir / "bad_numeric.csv"
            bad_numeric.write_text("strain,stress\n0.001,not_a_number\n", encoding="utf-8")
            relpath = str(bad_numeric.relative_to(_ROOT)).replace("\\", "/")
            out = run_certificate(
                seed=42,
                dataset_relpath=relpath,
                required_columns=["strain", "stress"],
                numeric_columns=["strain", "stress"],
            )
            assert out["result"]["pass"] is False
            assert len(out["result"]["issues"]) > 0 or out["result"]["metrics"]["parse_error_count"] > 0

            missing_col = tmp_dir / "missing_col.csv"
            missing_col.write_text("strain\n0.001\n", encoding="utf-8")
            relpath2 = str(missing_col.relative_to(_ROOT)).replace("\\", "/")
            out2 = run_certificate(
                seed=42,
                dataset_relpath=relpath2,
                required_columns=["strain", "stress"],
                numeric_columns=["strain"],
            )
            assert out2["result"]["pass"] is False
            assert any("stress" in i for i in out2["result"]["issues"]) or "Missing" in str(out2["result"]["issues"])

    def test_c_reproducibility_shape(self, tmp_path, monkeypatch):
        """Reproducibility: normalize trace_id/timestamps; compare key paths."""
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))
        _, job1 = _run_datapipe1_job(tmp_path, DATAPIPE1_PAYLOAD, canary_mode=False)
        _, job2 = _run_datapipe1_job(tmp_path, DATAPIPE1_PAYLOAD, canary_mode=False)
        norm1 = _normalize_evidence({"result": job1.result})
        norm2 = _normalize_evidence({"result": job2.result})
        k1 = _key_paths(norm1)
        k2 = _key_paths(norm2)
        assert k1 == k2
        assert "result.domain" in k1
        assert "result.inputs.dataset.sha256" in k1
        assert "result.result.metrics" in k1
