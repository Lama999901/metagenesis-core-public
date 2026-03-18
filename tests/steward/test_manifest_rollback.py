#!/usr/bin/env python3
"""
ADV-07: Manifest protocol_version rollback attack.

Tests that the verifier rejects bundles with rolled-back, missing, or
invalid protocol_version in pack_manifest.json. Prevents attackers from
downgrading to older protocol versions that lack newer validation rules.

5 tests.
"""
import hashlib
import json
import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg import _verify_pack  # noqa: E402

_VALID_HASH = "a" * 64
JOB_KIND = "dtfem1_displacement_verification"


def _make_rollback_pack(tmp_path, protocol_version=1):
    """Build minimal pack with configurable protocol_version.

    If protocol_version is the string "OMIT", the key is omitted entirely.
    """
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir(exist_ok=True)
    ev_dir = pack_dir / "evidence" / "DT-FEM-01" / "normal"
    ev_dir.mkdir(parents=True, exist_ok=True)

    domain_result = {
        "mtr_phase": "DT-FEM-01",
        "inputs": {
            "seed": 42,
            "reference_value": 1.0,
            "rel_err_threshold": 0.02,
            "noise_scale": 0.005,
            "quantity": "displacement_mm",
            "units": "mm",
        },
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
        "ledger_action": "job_completed",
        "persisted_at": "2026-03-18T00:00:00Z",
    }

    (ev_dir / "run_artifact.json").write_text(
        json.dumps(run_artifact), encoding="utf-8")
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        json.dumps({"trace_id": "trace-test-001", "action": "job_completed",
                    "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
        encoding="utf-8")

    evidence_index = {
        "DT-FEM-01": {
            "job_kind": JOB_KIND,
            "normal": {
                "run_relpath": "evidence/DT-FEM-01/normal/run_artifact.json",
                "ledger_relpath": "evidence/DT-FEM-01/normal/ledger_snapshot.jsonl",
            },
        }
    }
    (pack_dir / "evidence_index.json").write_text(
        json.dumps(evidence_index), encoding="utf-8")

    # Build manifest with correct SHA-256 hashes
    files_list = []
    for p in sorted(pack_dir.rglob("*")):
        if not p.is_file() or p.name == "pack_manifest.json":
            continue
        relpath = str(p.relative_to(pack_dir)).replace("\\", "/")
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        files_list.append({"relpath": relpath, "sha256": sha, "bytes": len(raw)})

    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files_list, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "pack_version": "1",
        "files": files_list,
        "root_hash": root_hash,
    }
    if protocol_version != "OMIT":
        manifest["protocol_version"] = protocol_version

    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    return pack_dir


class TestManifestRollback:
    """ADV-07: Protocol version rollback attack detection."""

    def test_a_current_version_passes(self, tmp_path):
        """Pack with protocol_version=1 (integer) passes verification."""
        pack_dir = _make_rollback_pack(tmp_path, protocol_version=1)
        ok, msg, report = _verify_pack(pack_dir)
        assert ok is True, f"Expected PASS for protocol_version=1, got: {msg}"

    def test_b_version_zero_rejected(self, tmp_path):
        """Pack with protocol_version=0 is rejected."""
        pack_dir = _make_rollback_pack(tmp_path, protocol_version=0)
        ok, msg, report = _verify_pack(pack_dir)
        assert ok is False, "protocol_version=0 must be rejected"
        assert "protocol_version" in msg.lower(), \
            f"Error message should mention protocol_version, got: {msg}"

    def test_c_version_negative_rejected(self, tmp_path):
        """Pack with protocol_version=-1 is rejected."""
        pack_dir = _make_rollback_pack(tmp_path, protocol_version=-1)
        ok, msg, report = _verify_pack(pack_dir)
        assert ok is False, "protocol_version=-1 must be rejected"
        assert "protocol_version" in msg.lower(), \
            f"Error message should mention protocol_version, got: {msg}"

    def test_d_version_missing_rejected(self, tmp_path):
        """Pack with no protocol_version key is rejected."""
        pack_dir = _make_rollback_pack(tmp_path, protocol_version="OMIT")
        ok, msg, report = _verify_pack(pack_dir)
        assert ok is False, "Missing protocol_version must be rejected"
        assert "protocol_version" in msg.lower(), \
            f"Error message should mention protocol_version, got: {msg}"

    def test_e_version_string_rejected(self, tmp_path):
        """Pack with protocol_version='old' (string) is rejected."""
        pack_dir = _make_rollback_pack(tmp_path, protocol_version="old")
        ok, msg, report = _verify_pack(pack_dir)
        assert ok is False, "String protocol_version must be rejected"
        assert "protocol_version" in msg.lower(), \
            f"Error message should mention protocol_version, got: {msg}"
