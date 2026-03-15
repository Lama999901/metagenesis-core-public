#!/usr/bin/env python3
"""
MTR-3 Two-parameter thermal calibration (k + contact resistance) - Tests.

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
from backend.progress.mtr3_thermal_multilayer import JOB_KIND, run_calibration

MTR3_PAYLOAD = {
    "kind": JOB_KIND,
    "seed": 42,
    "k_true": 5.0,
    "r_contact_true": 0.1,
    "n_points": 50,
    "L1": 0.01,
    "A1": 1e-4,
    "L2": 0.02,
    "A2": 1e-4,
    "q_max": 10.0,
}


def _run_mtr3_job(artifact_dir: Path, canary_mode: bool = False):
    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(artifact_dir / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)
    job = runner.create_job(payload=MTR3_PAYLOAD)
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


class TestMTR3ThermalMultilayer:
    """MTR-3 two-parameter calibration: E2E, V&V, reproducibility."""

    def test_a_e2e_create_run_normal_canary_artifacts_evidence(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))

        trace1, job1 = _run_mtr3_job(tmp_path, canary_mode=False)
        trace2, job2 = _run_mtr3_job(tmp_path, canary_mode=True)

        progress_runs = tmp_path / "progress_runs"
        ledger_snapshots = tmp_path / "ledger_snapshots"
        assert progress_runs.exists() and ledger_snapshots.exists()
        run_files = list(progress_runs.glob("*.json"))
        assert len(run_files) >= 2

        for job in (job1, job2):
            assert job.result is not None
            assert job.result.get("mtr_phase") == "MTR-3"
            assert "inputs" in job.result
            assert "result" in job.result
            r = job.result["result"]
            assert "estimated_k" in r
            assert "estimated_r_contact" in r
            assert "rmse" in r
            assert "rel_err_k" in r
            assert "rel_err_r" in r
            assert r.get("method") == "ols_2param"
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
        assert res.get("mtr_phase") == "MTR-3"
        assert "result" in res
        assert "estimated_k" in res["result"]
        assert "estimated_r_contact" in res["result"]

    def test_b_vv_rel_err_k_rel_err_r_rmse_thresholds(self):
        k_true = 5.0
        r_contact_true = 0.1
        L1, A1, L2, A2, q_max = 0.01, 1e-4, 0.02, 1e-4, 10.0
        max_delta_T1 = (L1 / (k_true * A1) + r_contact_true) * q_max
        max_delta_T2 = (L2 / (k_true * A2) + r_contact_true) * q_max
        max_delta_T_true = max(max_delta_T1, max_delta_T2)
        noise_scale = max_delta_T_true * 0.001

        out = run_calibration(
            seed=42,
            k_true=k_true,
            r_contact_true=r_contact_true,
            n_points=80,
            L1=L1, A1=A1, L2=L2, A2=A2,
            q_max=q_max,
            noise_scale=noise_scale,
        )
        r = out["result"]
        assert r["rel_err_k"] <= 0.03
        assert r["rel_err_r"] <= 0.05
        assert r["rmse"] <= max_delta_T_true * 0.05

    def test_c_reproducibility_same_payload_twice_shape_matches(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MG_PROGRESS_ARTIFACT_DIR", str(tmp_path))

        _run_mtr3_job(tmp_path, canary_mode=False)
        _run_mtr3_job(tmp_path, canary_mode=False)

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
        assert "estimated_r_contact" in res0["result"]
        assert "rmse" in res0["result"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
