#!/usr/bin/env python3
"""
SCENARIO 04: AeroSim Engineering — FEM Displacement Verification (DT-FEM-01).

20-row FEM validation CSV. Runs runner (normal + canary),
builds pack with evidence, verifies pack, prints PASS or FAIL.
"""

import csv
import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parent.parent.parent
DATASET_RELPATH = "demos/client_scenarios/04_digital_twin/data/fem_validation.csv"


def _generate_csv() -> None:
    """Generate deterministic 20-row FEM validation CSV (~1% rel_err)."""
    csv_path = REPO_ROOT / DATASET_RELPATH
    if csv_path.exists():
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    base = 12.0
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["fem_value", "measured_value", "quantity"])
        for _ in range(20):
            measured = round(base + rng.uniform(-0.05, 0.05), 4)
            fem = round(measured * (1 + rng.uniform(-0.01, 0.01)), 4)
            w.writerow([fem, measured, "displacement_mm"])


def _run_job(canary_mode: bool) -> None:
    """Run DT-FEM-01 via ProgressRunner."""
    os.environ["MG_PROGRESS_ARTIFACT_DIR"] = str(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "progress_runs").mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "ledger_snapshots").mkdir(parents=True, exist_ok=True)

    from backend.ledger.ledger_store import LedgerStore
    from backend.progress.dtfem1_displacement_verification import JOB_KIND as DTFEM1_KIND
    from backend.progress.runner import ProgressRunner
    from backend.progress.store import JobStore

    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(DEMO_DIR / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)

    payload = {
        "kind": DTFEM1_KIND,
        "dataset_relpath": DATASET_RELPATH,
        "rel_err_threshold": 0.02,
    }
    job = runner.create_job(payload=payload)
    runner.run_job(job.job_id, canary_mode=canary_mode)


def _mg(args: list) -> int:
    """Run mg CLI from repo root. Returns exit code."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "mg.py")] + args
    return subprocess.run(cmd, cwd=str(REPO_ROOT), executable=sys.executable).returncode


def main() -> int:
    os.chdir(REPO_ROOT)
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    _generate_csv()

    data_path = REPO_ROOT / DATASET_RELPATH
    if not data_path.exists():
        print("FAIL: Dataset not found at " + DATASET_RELPATH)
        return 1

    _run_job(canary_mode=False)
    _run_job(canary_mode=True)

    bundle_dir = DEMO_DIR / "bundle"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    rc_build = _mg([
        "pack", "build",
        "--output", str(bundle_dir),
        "--include-evidence",
        "--source-reports-dir", str(DEMO_DIR),
    ])
    if rc_build != 0:
        print("FAIL: Pack build failed (exit code " + str(rc_build) + ")")
        return 1

    report_path = DEMO_DIR / "VERIFY_REPORT.json"
    rc_verify = _mg(["verify", "--pack", str(bundle_dir), "--json", str(report_path)])
    if rc_verify != 0:
        print("FAIL: Pack verify failed (exit code " + str(rc_verify) + ")")
        return 1

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print("FAIL: Could not read VERIFY_REPORT.json: " + str(e))
        return 1

    manifest_ok = report.get("manifest_ok") is True
    semantic_ok = report.get("semantic_ok") is True
    errors = report.get("errors") or []

    if manifest_ok and semantic_ok and len(errors) == 0:
        print("SCENARIO 4 PASS: AeroSim Engineering — FEM simulation verified (DT-FEM-01, rel_err <= 2%)")
        return 0
    reason = "; ".join(errors) if errors else ("manifest_ok=" + str(manifest_ok) + ", semantic_ok=" + str(semantic_ok))
    print("FAIL: " + reason)
    return 1


if __name__ == "__main__":
    sys.exit(main())
