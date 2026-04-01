#!/usr/bin/env python3
"""
SCENARIO 02: PsiThera — ADMET Solubility Prediction (PHARMA-01).

FDA 21 CFR Part 11 aligned. Runs runner (normal + canary),
builds pack with evidence, verifies pack, prints PASS or FAIL.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parent.parent.parent


def _run_job(canary_mode: bool) -> None:
    """Run PHARMA-01 via ProgressRunner."""
    os.environ["MG_PROGRESS_ARTIFACT_DIR"] = str(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "progress_runs").mkdir(parents=True, exist_ok=True)
    (DEMO_DIR / "ledger_snapshots").mkdir(parents=True, exist_ok=True)

    from backend.ledger.ledger_store import LedgerStore
    from backend.progress.pharma1_admet_certificate import JOB_KIND as PHARMA1_KIND
    from backend.progress.runner import ProgressRunner
    from backend.progress.store import JobStore

    job_store = JobStore()
    ledger_store = LedgerStore(file_path=str(DEMO_DIR / "ledger.jsonl"))
    runner = ProgressRunner(job_store=job_store, ledger_store=ledger_store)

    payload = {
        "kind": PHARMA1_KIND,
        "property_name": "solubility",
        "claimed_value": -3.5,
        "seed": 42,
        "noise_scale": 0.005,
        "tolerance": 0.05,
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
        print("SCENARIO 2 PASS: PsiThera — ADMET solubility prediction verified (FDA 21 CFR Part 11)")
        return 0
    reason = "; ".join(errors) if errors else ("manifest_ok=" + str(manifest_ok) + ", semantic_ok=" + str(semantic_ok))
    print("FAIL: " + reason)
    return 1


if __name__ == "__main__":
    sys.exit(main())
