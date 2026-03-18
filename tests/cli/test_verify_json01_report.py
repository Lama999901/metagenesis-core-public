#!/usr/bin/env python3
"""
VERIFY-JSON-01: Machine-readable verification report.

Tests that mg verify --pack <dir> --json <out_path> writes deterministic
JSON report for both PASS and FAIL cases.
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
    """Run MTR-1 (normal or canary) with dataset + UQ."""
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


def _build_pack(source_reports_dir: Path, pack_out: Path) -> int:
    """Build evidence-inclusive pack. Returns exit code."""
    return _mg([
        "pack", "build",
        "--output", str(pack_out),
        "--include-evidence",
        "--source-reports-dir", str(source_reports_dir),
    ])[0]


def _recompute_manifest(pack_dir: Path) -> None:
    """Recompute pack_manifest.json so integrity passes."""
    pack_dir = Path(pack_dir)
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
        "protocol_version": 1,
        "files": files_list,
        "root_hash": root_hash,
    }
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


class TestVerifyJson01Report:
    """VERIFY-JSON-01 machine-readable report."""

    def test_verify_json_valid_pack_passes(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Build valid pack, verify with --json; assert file exists, valid JSON, status PASS."""
        monkeypatch.delenv("MG_PROGRESS_ARTIFACT_DIR", raising=False)
        source_reports_dir = tmp_path / "source_reports"
        pack_out = tmp_path / "pack_out"
        report_path = tmp_path / "report.json"

        _run_mtr1_evidence(source_reports_dir, canary_mode=False)
        _run_mtr1_evidence(source_reports_dir, canary_mode=True)
        rc = _build_pack(source_reports_dir, pack_out)
        assert rc == 0

        exit_code, _ = _mg(["verify", "--pack", str(pack_out), "--json", str(report_path)])

        assert exit_code == 0
        assert report_path.exists()
        data = json.loads(report_path.read_text(encoding="utf-8"))

        assert data.get("version") == "v1"
        assert data.get("manifest_ok") is True
        assert data.get("semantic_ok") is True
        assert isinstance(data.get("pack_root_hash"), str)
        assert len(data["pack_root_hash"]) == 64
        assert data.get("errors") == []
        assert "checks" in data
        assert any(c.get("name") == "semantic_evidence" and c.get("status") == "pass" for c in data["checks"])

    def test_verify_json_tampered_pack_fails_with_errors(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Tamper run_artifact, recompute manifest; verify --json; assert FAIL and errors non-empty."""
        monkeypatch.delenv("MG_PROGRESS_ARTIFACT_DIR", raising=False)
        source_reports_dir = tmp_path / "source_reports"
        pack_out = tmp_path / "pack_out"
        report_path = tmp_path / "report.json"

        _run_mtr1_evidence(source_reports_dir, canary_mode=False)
        _run_mtr1_evidence(source_reports_dir, canary_mode=True)
        rc = _build_pack(source_reports_dir, pack_out)
        assert rc == 0

        run_path = pack_out / "evidence" / "MTR-1" / "normal" / "run_artifact.json"
        data = json.loads(run_path.read_text(encoding="utf-8"))
        del data["job_snapshot"]
        run_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        _recompute_manifest(pack_out)

        exit_code, _ = _mg(["verify", "--pack", str(pack_out), "--json", str(report_path)])

        assert exit_code != 0
        assert report_path.exists()
        report = json.loads(report_path.read_text(encoding="utf-8"))

        assert report.get("manifest_ok") is True
        assert report.get("semantic_ok") is False
        assert len(report.get("errors", [])) > 0
        assert "job_snapshot" in report["errors"][0] or "missing required key" in report["errors"][0]

    def test_verify_json_deterministic_same_pack_twice(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """Same pack verified twice produces identical JSON output."""
        monkeypatch.delenv("MG_PROGRESS_ARTIFACT_DIR", raising=False)
        source_reports_dir = tmp_path / "source_reports"
        pack_out = tmp_path / "pack_out"
        report1 = tmp_path / "report1.json"
        report2 = tmp_path / "report2.json"

        _run_mtr1_evidence(source_reports_dir, canary_mode=False)
        _run_mtr1_evidence(source_reports_dir, canary_mode=True)
        rc = _build_pack(source_reports_dir, pack_out)
        assert rc == 0

        _mg(["verify", "--pack", str(pack_out), "--json", str(report1)])
        _mg(["verify", "--pack", str(pack_out), "--json", str(report2)])

        j1 = report1.read_text(encoding="utf-8")
        j2 = report2.read_text(encoding="utf-8")
        assert j1 == j2, "JSON output must be deterministic"
