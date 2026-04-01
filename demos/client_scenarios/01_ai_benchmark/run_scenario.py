#!/usr/bin/env python3
"""
SCENARIO 01: NeuralBench AI — ML Benchmark Verification (ML_BENCH-01).

150-row prediction CSV, 94% accuracy claim. Runs runner (normal + canary),
builds pack with evidence, verifies pack, prints PASS or FAIL.
"""

import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parent.parent.parent
DATASET_RELPATH = "demos/client_scenarios/01_ai_benchmark/data/benchmark_predictions.csv"


def _generate_csv() -> None:
    """Generate deterministic 150-row prediction CSV (94% accuracy)."""
    csv_path = REPO_ROOT / DATASET_RELPATH
    if csv_path.exists():
        return
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["y_true", "y_pred"])
        for i in range(150):
            y_true = i % 2
            y_pred = y_true if i < 141 else (1 - y_true)
            w.writerow([y_true, y_pred])


def _run_job(canary_mode: bool) -> None:
    """Run ML_BENCH-01 via ProgressRunner."""
    os.environ["MG_PROGRESS_ARTIFACT_DIR"] = str(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "progress_runs").mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "ledger_snapshots").mkdir(parents=True, exist_ok=True)

    from backend.ledger.ledger_store import LedgerStore
    from backend.progress.mlbench1_accuracy_certificate import JOB_KIND as MLBENCH1_KIND
    from backend.progress.runner import ProgressRunner
    from backend.progress.store import JobStore

    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(DEMO_DIR / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)

    payload = {
        "kind": MLBENCH1_KIND,
        "dataset_relpath": DATASET_RELPATH,
        "claimed_accuracy": 0.94,
        "accuracy_tolerance": 0.02,
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
        print("SCENARIO 1 PASS: NeuralBench AI — 94% accuracy claim verified")
        return 0
    reason = "; ".join(errors) if errors else ("manifest_ok=" + str(manifest_ok) + ", semantic_ok=" + str(semantic_ok))
    print("FAIL: " + reason)
    return 1


if __name__ == "__main__":
    sys.exit(main())
