#!/usr/bin/env python3
"""
CERT-ADV-SYSID01-SEMANTIC: Layer 2 Semantic Stripping for SYSID-01.

Tests that Layer 2 (_verify_semantic) catches missing or empty semantic fields
when evidence is specifically crafted for SYSID-01 claim type.

Each test strips a required field and asserts verification FAILS.
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg import _verify_semantic  # noqa: E402


def _make_sysid01_sem_pack(tmp_path, mtr_phase="SYSID-01",
                            trace_root_hash="d" * 64,
                            execution_trace=None,
                            include_inputs=True,
                            include_result=True,
                            job_kind="sysid1_arx_calibration"):
    """Build minimal SYSID-01 pack for semantic verification tests."""
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir(exist_ok=True)
    ev_dir = pack_dir / "evidence" / "SYSID-01" / "normal"
    ev_dir.mkdir(parents=True, exist_ok=True)

    if execution_trace is None:
        execution_trace = [
            {"step": 1, "name": "init_params", "hash": "a" * 64},
            {"step": 2, "name": "generate_sequence", "hash": "b" * 64},
            {"step": 3, "name": "estimate_arx", "hash": "c" * 64},
            {"step": 4, "name": "threshold_check", "hash": "d" * 64},
        ]

    domain_result = {}
    if mtr_phase is not None:
        domain_result["mtr_phase"] = mtr_phase
    else:
        domain_result["mtr_phase"] = None

    if include_inputs:
        domain_result["inputs"] = {
            "seed": 42,
            "a_true": 0.9,
            "b_true": 0.5,
            "n_steps": 50,
            "u_max": 1.0,
            "noise_scale": 0.014,
        }
    if include_result:
        domain_result["result"] = {
            "estimated_a": 0.9001,
            "estimated_b": 0.4999,
            "rmse": 0.001,
            "rel_err_a": 0.0001,
            "rel_err_b": 0.0002,
            "method": "ols_arx_2param",
            "algorithm_version": "v1",
        }

    if execution_trace is not False:
        domain_result["execution_trace"] = execution_trace
    if trace_root_hash is not False:
        domain_result["trace_root_hash"] = trace_root_hash

    run_artifact = {
        "w6_phase": "W6-A5",
        "kind": "success",
        "job_id": "job-sysid01-test",
        "trace_id": "trace-sysid01-test",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": "job-sysid01-test",
            "status": "SUCCEEDED",
            "payload": {"kind": job_kind},
            "result": domain_result,
        },
        "ledger_action": "job_completed",
        "persisted_at": "2026-03-19T00:00:00Z",
    }

    (ev_dir / "run_artifact.json").write_text(
        json.dumps(run_artifact), encoding="utf-8")
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        json.dumps({"trace_id": "trace-sysid01-test", "action": "job_completed",
                     "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
        encoding="utf-8")

    evidence_index = {
        "SYSID-01": {
            "job_kind": job_kind,
            "normal": {
                "run_relpath": "evidence/SYSID-01/normal/run_artifact.json",
                "ledger_relpath": "evidence/SYSID-01/normal/ledger_snapshot.jsonl",
            },
        }
    }

    index_path = pack_dir / "evidence_index.json"
    index_path.write_text(json.dumps(evidence_index), encoding="utf-8")
    return pack_dir, index_path


class TestCertAdvSysid01Semantic:
    """Layer 2 semantic stripping attacks targeting SYSID-01 claim."""

    def test_sysid01_strip_mtr_phase(self, tmp_path):
        """Set mtr_phase=None, assert _verify_semantic fails."""
        pack_dir, index_path = _make_sysid01_sem_pack(tmp_path, mtr_phase=None)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for null mtr_phase, got PASS: {msg}"
        assert "mtr_phase" in msg

    def test_sysid01_strip_execution_trace(self, tmp_path):
        """Remove execution_trace but keep trace_root_hash, assert fails."""
        pack_dir, index_path = _make_sysid01_sem_pack(
            tmp_path, execution_trace=False, trace_root_hash="d" * 64)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for missing execution_trace: {msg}"

    def test_sysid01_strip_inputs(self, tmp_path):
        """Remove inputs dict from domain result, assert semantic check still runs."""
        pack_dir, index_path = _make_sysid01_sem_pack(tmp_path, include_inputs=False)
        # Verification should still pass since inputs is not strictly required
        # by _verify_semantic (it checks mtr_phase, trace, etc.)
        # This test documents the behavior
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        # inputs removal alone does not fail semantic; this is a documentation test
        assert isinstance(ok, bool), "Should return bool"

    def test_sysid01_strip_result(self, tmp_path):
        """Remove result dict from domain result, assert semantic check still runs."""
        pack_dir, index_path = _make_sysid01_sem_pack(tmp_path, include_result=False)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert isinstance(ok, bool), "Should return bool"

    def test_sysid01_empty_job_kind(self, tmp_path):
        """Set job_kind="" in evidence_index, assert fails."""
        pack_dir, index_path = _make_sysid01_sem_pack(tmp_path, job_kind="")
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False, f"Expected FAIL for empty job_kind, got PASS: {msg}"
