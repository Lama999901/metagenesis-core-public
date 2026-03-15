#!/usr/bin/env python3
"""
CERT-04: anchor_hash format validation in mg.py _verify_semantic.

Tests that _verify_semantic validates anchor_hash format when present
in inputs dict of a run artifact.

anchor_hash must be:
- None (absent) → skip validation (backward compatible)
- Valid 64-char lowercase hex → PASS
- Invalid format (wrong length, non-hex) → FAIL

4 tests.
"""
import json
import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg import _verify_semantic  # noqa: E402

JOB_KIND = "dtfem1_displacement_verification"
_VALID_HASH = "a" * 64


def _make_pack(tmp_path: Path, anchor_hash=None, include_anchor=False) -> tuple:
    """Build minimal pack with DT-FEM-01 claim, optionally with anchor_hash in inputs."""
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    ev_dir = pack_dir / "evidence" / "DT-FEM-01" / "normal"
    ev_dir.mkdir(parents=True)

    inputs = {
        "seed": 42,
        "reference_value": 1.0,
        "rel_err_threshold": 0.02,
        "noise_scale": 0.005,
        "quantity": "displacement_mm",
        "units": "mm",
    }
    if include_anchor:
        inputs["anchor_hash"] = anchor_hash
        inputs["anchor_claim_id"] = "MTR-1"

    domain_result = {
        "mtr_phase": "DT-FEM-01",
        "inputs": inputs,
        "result": {
            "fem_value": 1.001, "reference_value": 1.0,
            "rel_err": 0.001, "rel_err_threshold": 0.02,
            "pass": True, "quantity": "displacement_mm",
            "units": "mm", "method": "fem_vs_reference_rel_err",
            "algorithm_version": "v1",
        },
        "execution_trace": [
            {"step": 1, "name": "init_params", "hash": _VALID_HASH},
            {"step": 2, "name": "generate_fem_pair", "hash": "b" * 64},
            {"step": 3, "name": "compute_rel_err", "hash": "c" * 64},
            {"step": 4, "name": "threshold_check", "hash": "d" * 64},
        ],
        "trace_root_hash": "d" * 64,
    }

    run_artifact = {
        "w6_phase": "W6-A5", "kind": "success",
        "job_id": "job-test-001", "trace_id": "trace-test-001",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": "job-test-001", "status": "SUCCEEDED",
            "payload": {"kind": JOB_KIND},
            "result": domain_result,
        },
        "ledger_action": "job_completed", "persisted_at": "2026-03-14T00:00:00Z",
    }

    (ev_dir / "run_artifact.json").write_text(json.dumps(run_artifact), encoding="utf-8")
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        json.dumps({"trace_id": "trace-test-001", "action": "job_completed",
                    "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
        encoding="utf-8",
    )

    evidence_index = {
        "DT-FEM-01": {
            "job_kind": JOB_KIND,
            "normal": {
                "run_relpath": "evidence/DT-FEM-01/normal/run_artifact.json",
                "ledger_relpath": "evidence/DT-FEM-01/normal/ledger_snapshot.jsonl",
            },
        }
    }
    index_path = pack_dir / "evidence_index.json"
    index_path.write_text(json.dumps(evidence_index), encoding="utf-8")
    return pack_dir, index_path


class TestAnchorHashValidation:

    def test_no_anchor_hash_passes(self, tmp_path):
        """No anchor_hash in inputs → PASS (backward compatible)."""
        pack_dir, index_path = _make_pack(tmp_path, include_anchor=False)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS, got: {msg}"

    def test_valid_anchor_hash_passes(self, tmp_path):
        """Valid 64-char hex anchor_hash → PASS."""
        pack_dir, index_path = _make_pack(
            tmp_path, anchor_hash="a" * 64, include_anchor=True)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is True, f"Expected PASS for valid anchor_hash, got: {msg}"

    def test_invalid_anchor_hash_length_fails(self, tmp_path):
        """anchor_hash with wrong length → FAIL."""
        pack_dir, index_path = _make_pack(
            tmp_path, anchor_hash="abc123", include_anchor=True)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False
        assert "anchor_hash" in msg.lower() or "anchor" in msg.lower()

    def test_invalid_anchor_hash_non_hex_fails(self, tmp_path):
        """anchor_hash with non-hex characters → FAIL."""
        pack_dir, index_path = _make_pack(
            tmp_path, anchor_hash="Z" * 64, include_anchor=True)
        ok, msg, errors = _verify_semantic(pack_dir, index_path)
        assert ok is False
        assert "anchor_hash" in msg.lower() or "anchor" in msg.lower()
