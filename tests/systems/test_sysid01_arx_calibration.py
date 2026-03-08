#!/usr/bin/env python3
"""
SYSID-01 ARX Calibration - Tests.

Purpose: E2E, V&V thresholds, reproducibility shape.
# Part of MetaGenesis Core verification pipeline (MVP v0.1)
"""

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.progress.runner import ProgressRunner
from backend.progress.store import JobStore
from backend.ledger.ledger_store import LedgerStore
from backend.progress.sysid1_arx_calibration import JOB_KIND, run_calibration

SYSID1_PAYLOAD = {
    "kind": JOB_KIND,
    "seed": 42,
    "a_true": 0.9,
    "b_true": 0.5,
    "n_steps": 50,
    "u_max": 1.0,
}


def _run_sysid1_job(artifact_dir: Path, canary_mode: bool = False):
    """Create SYSID-01 job, run, return (trace_id, job)."""
    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(artifact_dir / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)
    job = runner.create_job(payload=SYSID1_PAYLOAD)
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


class TestSYSID01ARXCalibration:
    """SYSID-01 ARX calibration: E2E, V&V, reproducibility."""

    def test_a_e2e_normal_canary_artifacts_evidence(self, tmp_path, monkeypatch):
        """E2E: normal+canary job runs; artifacts exist; evidence index/API fallback resolves; job_snapshot.result has domain fields."""
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))

        trace1, job1 = _run_sysid1_job(tmp_path, canary_mode=False)
        trace2, job2 = _run_sysid1_job(tmp_path, canary_mode=True)

        progress_runs = tmp_path / "progress_runs"
        ledger_snapshots = tmp_path / "ledger_snapshots"
        assert progress_runs.exists() and ledger_snapshots.exists()
        run_files = list(progress_runs.glob("*.json"))
        assert len(run_files) >= 2

        for job in (job1, job2):
            assert job.result is not None
            assert job.result.get("domain") == "SYSID"
            assert job.result.get("claim_id") == "SYSID-01"
            assert "inputs" in job.result
            assert "result" in job.result
            r = job.result["result"]
            assert "estimated_a" in r
            assert "estimated_b" in r
            assert "rmse" in r
            assert "rel_err_a" in r
            assert "rel_err_b" in r
            assert r.get("method") == "ols_arx_2param"
            assert r.get("algorithm_version") == "v1"

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

    def test_b_vv_thresholds(self):
        """V&V: rel_err_a <= 0.03, rel_err_b <= 0.03, rmse <= bound."""
        out = run_calibration(seed=42, a_true=0.9, b_true=0.5, n_steps=100, u_max=1.0, noise_scale=0.01)
        r = out["result"]
        assert r["rel_err_a"] <= 0.03
        assert r["rel_err_b"] <= 0.03
        rmse_bound = 0.05 * (abs(0.9) + abs(0.5)) * 1.0
        assert r["rmse"] <= rmse_bound

    def test_c_reproducibility_shape(self, tmp_path, monkeypatch):
        """Reproducibility: normalize timestamps/trace_id; compare key-path sets."""
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))
        _, job1 = _run_sysid1_job(tmp_path, canary_mode=False)
        _, job2 = _run_sysid1_job(tmp_path, canary_mode=False)
        norm1 = _normalize_evidence({"result": job1.result})
        norm2 = _normalize_evidence({"result": job2.result})
        k1 = _key_paths(norm1)
        k2 = _key_paths(norm2)
        assert k1 == k2
        assert "result.domain" in k1
        assert "result.result.estimated_a" in k1
