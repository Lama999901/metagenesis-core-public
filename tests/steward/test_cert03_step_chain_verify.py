#!/usr/bin/env python3
"""
CERT-03: Step Chain Verification in mg.py _verify_semantic.

Tests that _verify_semantic correctly validates execution_trace +
trace_root_hash when present in run artifacts.

Three layers of verification:
  1. integrity:     SHA-256 over bundle files (existing)
  2. semantic:      required evidence fields present (existing)
  3. step chain:    trace_root_hash == final step hash (NEW — this file)
"""

import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg import _verify_semantic  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

JOB_KIND = "mlbench1_accuracy_certificate"

_VALID_HASH_A = "a" * 64
_VALID_HASH_B = "b" * 64
_VALID_HASH_C = "c" * 64
_VALID_HASH_D = "d" * 64

_VALID_TRACE = [
    {"step": 1, "name": "init_params",      "hash": _VALID_HASH_A},
    {"step": 2, "name": "generate_dataset", "hash": _VALID_HASH_B},
    {"step": 3, "name": "compute_metrics",  "hash": _VALID_HASH_C},
    {"step": 4, "name": "threshold_check",  "hash": _VALID_HASH_D},
]
_VALID_ROOT = _VALID_HASH_D  # trace_root_hash == last step hash


def _make_pack(tmp_path: Path, execution_trace=None, trace_root_hash=None,
               omit_trace=False, omit_root=False) -> tuple:
    """Build a minimal fake pack directory with one claim (ML_BENCH-01)."""
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    ev_dir = pack_dir / "evidence" / "ML_BENCH-01" / "normal"
    ev_dir.mkdir(parents=True)

    domain_result = {
        "mtr_phase": "ML_BENCH-01",
        "inputs": {
            "seed": 42, "claimed_accuracy": 0.9, "accuracy_tolerance": 0.02,
            "n_samples": 1000, "n_features": 10, "noise_scale": None,
            "mode": "synthetic",
        },
        "result": {
            "actual_accuracy": 0.901, "claimed_accuracy": 0.9,
            "absolute_error": 0.001, "tolerance": 0.02, "pass": True,
            "precision": 0.9, "recall": 0.9, "f1": 0.9, "n_samples": 1000,
        },
    }
    if not omit_trace and execution_trace is not None:
        domain_result["execution_trace"] = execution_trace
    if not omit_root and trace_root_hash is not None:
        domain_result["trace_root_hash"] = trace_root_hash

    run_artifact = {
        "w6_phase": "W6-A5",
        "kind": "success",
        "job_id": "job-test-001",
        "trace_id": "trace-test-001",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": "job-test-001",
            "status": "SUCCEEDED",
            "payload": {"kind": JOB_KIND},
            "result": domain_result,
        },
        "ledger_action": "job_completed",
        "persisted_at": "2026-03-14T00:00:00Z",
    }

    run_path = ev_dir / "run_artifact.json"
    run_path.write_text(json.dumps(run_artifact), encoding="utf-8")

    ledger_path = ev_dir / "ledger_snapshot.jsonl"
    ledger_path.write_text(
        json.dumps({
            "trace_id": "trace-test-001", "action": "job_completed",
            "actor": "scheduler_v1", "meta": {"canary_mode": False},
        }) + "\n",
        encoding="utf-8",
    )

    evidence_index = {
        "ML_BENCH-01": {
            "job_kind": JOB_KIND,
            "normal": {
                "run_relpath":    "evidence/ML_BENCH-01/normal/run_artifact.json",
                "ledger_relpath": "evidence/ML_BENCH-01/normal/ledger_snapshot.jsonl",
            },
        }
    }
    index_path = pack_dir / "evidence_index.json"
    index_path.write_text(json.dumps(evidence_index), encoding="utf-8")

    return pack_dir, index_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStepChainVerification:

    def test_valid_trace_root_hash_passes(self, tmp_path):
        """Valid execution_trace + matching trace_root_hash → PASS."""
        pack_dir, index_path = _make_pack(
            tmp_path,
            execution_trace=_VALID_TRACE,
            trace_root_hash=_VALID_ROOT,
        )
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS, got: {msg}"
        assert errors == []

    def test_tampered_trace_root_hash_fails(self, tmp_path):
        """
        trace_root_hash does not match final step hash → FAIL.
        Catches: step was modified but trace_root_hash not updated.
        """
        wrong_root = "e" * 64
        pack_dir, index_path = _make_pack(
            tmp_path,
            execution_trace=_VALID_TRACE,
            trace_root_hash=wrong_root,
        )
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False
        assert "Step Chain broken" in msg

    def test_missing_trace_root_hash_when_trace_present_fails(self, tmp_path):
        """execution_trace present but trace_root_hash absent → FAIL."""
        pack_dir, index_path = _make_pack(
            tmp_path,
            execution_trace=_VALID_TRACE,
            trace_root_hash=None,
            omit_root=True,
        )
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False
        assert "missing trace_root_hash" in msg

    def test_missing_trace_when_root_hash_present_fails(self, tmp_path):
        """trace_root_hash present but execution_trace absent → FAIL."""
        pack_dir, index_path = _make_pack(
            tmp_path,
            execution_trace=None,
            trace_root_hash=_VALID_ROOT,
            omit_trace=True,
        )
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False
        assert "missing execution_trace" in msg

    def test_invalid_step_hash_format_fails(self, tmp_path):
        """Step hash not valid 64-char lowercase hex → FAIL."""
        bad_trace = [
            {"step": 1, "name": "init_params",      "hash": "NOT_A_VALID_HASH"},
            {"step": 2, "name": "generate_dataset", "hash": _VALID_HASH_B},
            {"step": 3, "name": "compute_metrics",  "hash": _VALID_HASH_C},
            {"step": 4, "name": "threshold_check",  "hash": _VALID_HASH_D},
        ]
        pack_dir, index_path = _make_pack(
            tmp_path,
            execution_trace=bad_trace,
            trace_root_hash=_VALID_HASH_D,
        )
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False
        assert "invalid hash" in msg

    def test_no_trace_fields_passes(self, tmp_path):
        """
        Artifact without execution_trace and trace_root_hash → PASS.
        Backward-compatible: claims without Step Chain are not rejected.
        """
        pack_dir, index_path = _make_pack(
            tmp_path,
            execution_trace=None,
            trace_root_hash=None,
            omit_trace=True,
            omit_root=True,
        )
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS for artifact without trace, got: {msg}"
