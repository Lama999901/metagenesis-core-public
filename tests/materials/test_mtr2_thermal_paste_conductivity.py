#!/usr/bin/env python3
"""
MTR-2 Thermal Paste Conductivity Calibration - Tests.

Purpose: E2E proof-loop, V&V thresholds, reproducibility shape.
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
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
from backend.progress.mtr2_thermal_conductivity import JOB_KIND, run_calibration

MTR2_PAYLOAD = {
    "kind": JOB_KIND,
    "seed": 42,
    "k_true": 5.0,
    "n_points": 50,
    "L": 0.01,
    "A": 1e-4,
    "q_max": 10.0,
}


def _run_mtr2_job(artifact_dir: Path, canary_mode: bool = False):
    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(artifact_dir / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)
    job = runner.create_job(payload=MTR2_PAYLOAD)
    runner.run_job(job.job_id, canary_mode=canary_mode)
    return job.trace_id, job


def _normalize_evidence(obj):
    skip = {
        "trace_id", "job_id", "created_at", "started_at", "completed_at",
        "persisted_at", "execution_time_ms", "path"
    }
    if isinstance(obj, dict):
        return {k: _normalize_evidence(v) for k, v in obj.items() if k not in skip}
    if isinstance(obj, list):
        return [_normalize_evidence(i) for i in obj]
    return obj


def _key_paths(obj, prefix=""):
    keys = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(f"{prefix}{k}")
            keys.update(_key_paths(v, f"{prefix}{k}."))
    elif isinstance(obj, list) and obj:
        keys.update(_key_paths(obj[0], f"{prefix}[]."))
    return keys


class TestMTR2ThermalPasteConductivity:
    """MTR-2 calibration: E2E, V&V, reproducibility."""

    def test_a_e2e_create_run_normal_canary_artifacts_evidence(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))

        trace1, job1 = _run_mtr2_job(tmp_path, canary_mode=False)
        trace2, job2 = _run_mtr2_job(tmp_path, canary_mode=True)

        progress_runs = tmp_path / "progress_runs"
        ledger_snapshots = tmp_path / "ledger_snapshots"
        assert progress_runs.exists() and ledger_snapshots.exists()
        run_files = list(progress_runs.glob("*.json"))
        assert len(run_files) >= 2

        for job in (job1, job2):
            assert job.result is not None
            assert job.result.get("mtr_phase") == "MTR-2"
            assert "inputs" in job.result
            assert "result" in job.result
            r = job.result["result"]
            assert "estimated_k" in r
            assert "rmse" in r
            assert "relative_error" in r
            assert r.get("method") == "ols_origin"
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

        artifact = None
        for f in run_files:
            data = json.loads(f.read_text())
            if data.get("trace_id") == trace1:
                artifact = data
                break
        assert artifact is not None
        assert artifact.get("trace_id") == trace1
        snap = artifact.get("job_snapshot", {})
        res = snap.get("result", {})
        assert res.get("mtr_phase") == "MTR-2"
        assert "result" in res
        assert "estimated_k" in res["result"]

    def test_b_vv_relative_error_and_rmse_thresholds(self):
        k_true = 5.0
        L, A, q_max = 0.01, 1e-4, 10.0
        max_delta_T = (L / (k_true * A)) * q_max
        out = run_calibration(seed=42, k_true=k_true, n_points=50, L=L, A=A, q_max=q_max)
        r = out["result"]
        assert r["relative_error"] <= 0.02
        assert r["rmse"] <= max_delta_T * 0.03

    def test_c_reproducibility_same_payload_twice_shape_matches(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))

        _run_mtr2_job(tmp_path, canary_mode=False)
        _run_mtr2_job(tmp_path, canary_mode=False)

        run_files = sorted((tmp_path / "progress_runs").glob("*.json"))
        assert len(run_files) >= 2

        shapes = []
        for f in run_files[:2]:
            data = json.loads(f.read_text())
            norm = _normalize_evidence(data)
            shapes.append((norm, _key_paths(data)))

        assert shapes[0][1] == shapes[1][1]
        snap0 = shapes[0][0].get("job_snapshot", {})
        res0 = snap0.get("result", {})
        assert "mtr_phase" in res0
        assert "result" in res0
        assert "estimated_k" in res0["result"]
        assert "rmse" in res0["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
