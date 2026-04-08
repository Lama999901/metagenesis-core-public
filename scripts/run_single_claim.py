#!/usr/bin/env python3
"""
run_single_claim.py -- Single-claim dispatcher for real verification.

Usage:
    python scripts/run_single_claim.py CLAIM_ID INPUT_PATH OUTPUT_PATH

Reads input from INPUT_PATH (JSON or CSV depending on claim), dispatches to the
correct claim run function, and writes the result JSON to OUTPUT_PATH.

Exit codes:
    0 = success
    1 = failure (invalid claim, import error, runtime error)
"""

import json
import os
import sys
import traceback
from pathlib import Path

# Ensure project root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _to_relpath(input_path: str) -> str:
    """Convert input path to relative path from REPO_ROOT for dataset_relpath."""
    p = Path(input_path).resolve()
    try:
        return str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        # Already relative or outside repo
        return input_path.replace("\\", "/")


def _load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_output(result: dict, output_path: str) -> None:
    """Write result dict to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2, default=str))
        f.write("\n")


def dispatch(claim_id: str, input_path: str) -> dict:
    """Dispatch claim_id to the correct run function with input data."""
    relpath = _to_relpath(input_path)

    # ---- Materials domain ----

    if claim_id == "MTR-1":
        from backend.progress.mtr1_calibration import run_calibration
        return run_calibration(seed=42, E_true=70e9, dataset_relpath=relpath)

    if claim_id == "MTR-2":
        from backend.progress.mtr2_thermal_conductivity import run_calibration
        params = _load_json(input_path)
        return run_calibration(**params)

    if claim_id == "MTR-3":
        from backend.progress.mtr3_thermal_multilayer import run_calibration
        params = _load_json(input_path)
        return run_calibration(**params)

    if claim_id == "MTR-4":
        from backend.progress.mtr4_titanium_calibration import run_calibration
        return run_calibration(seed=42, E_true=114e9, dataset_relpath=relpath)

    if claim_id == "MTR-5":
        from backend.progress.mtr5_steel_calibration import run_calibration
        return run_calibration(seed=42, E_true=193e9, dataset_relpath=relpath)

    if claim_id == "MTR-6":
        from backend.progress.mtr6_copper_conductivity import run_calibration
        params = _load_json(input_path)
        return run_calibration(**params)

    # ---- Physics domain ----

    if claim_id == "PHYS-01":
        from backend.progress.phys01_boltzmann import run_verification
        params = _load_json(input_path)
        return run_verification(T=params["T"])

    if claim_id == "PHYS-02":
        from backend.progress.phys02_avogadro import run_verification
        return run_verification()

    # ---- ML domain ----

    if claim_id == "ML_BENCH-01":
        from backend.progress.mlbench1_accuracy_certificate import run_certificate
        return run_certificate(seed=42, claimed_accuracy=0.94, dataset_relpath=relpath)

    if claim_id == "ML_BENCH-02":
        from backend.progress.mlbench2_regression_certificate import run_certificate
        return run_certificate(seed=42, claimed_rmse=0.15, dataset_relpath=relpath)

    if claim_id == "ML_BENCH-03":
        from backend.progress.mlbench3_timeseries_certificate import run_certificate
        return run_certificate(seed=42, claimed_mape=0.005, dataset_relpath=relpath)

    # ---- Systems domain ----

    if claim_id == "SYSID-01":
        from backend.progress.sysid1_arx_calibration import run_calibration
        params = _load_json(input_path)
        return run_calibration(**params)

    if claim_id == "DATA-PIPE-01":
        from backend.progress.datapipe1_quality_certificate import run_certificate
        return run_certificate(
            seed=42,
            dataset_relpath=relpath,
            required_columns=["id", "value", "category"],
            numeric_columns=["value"],
            ranges_json='{"value":{"min":0.0,"max":1000.0}}',
        )

    if claim_id == "DRIFT-01":
        from backend.progress.drift_monitor import run_drift_monitor
        params = _load_json(input_path)
        return run_drift_monitor(**params)

    # ---- Digital twin domain ----

    if claim_id == "DT-FEM-01":
        from backend.progress.dtfem1_displacement_verification import run_certificate
        return run_certificate(seed=42, dataset_relpath=relpath)

    if claim_id == "DT-SENSOR-01":
        from backend.progress.dtsensor1_iot_certificate import run_certificate
        params = _load_json(input_path)
        return run_certificate(**params)

    if claim_id == "DT-CALIB-LOOP-01":
        from backend.progress.dtcalib1_convergence_certificate import run_certificate
        params = _load_json(input_path)
        return run_certificate(**params)

    # ---- Pharma domain ----

    if claim_id == "PHARMA-01":
        from backend.progress.pharma1_admet_certificate import run_certificate
        params = _load_json(input_path)
        return run_certificate(**params)

    # ---- Finance domain ----

    if claim_id == "FINRISK-01":
        from backend.progress.finrisk1_var_certificate import run_certificate
        params = _load_json(input_path)
        return run_certificate(**params)

    # ---- Agent domain ----

    if claim_id == "AGENT-DRIFT-01":
        from backend.progress.agent_drift_monitor import run_agent_drift_monitor
        params = _load_json(input_path)
        return run_agent_drift_monitor(**params)

    raise ValueError(
        f"Unknown CLAIM_ID: '{claim_id}'. "
        f"Valid IDs: MTR-1, MTR-2, MTR-3, MTR-4, MTR-5, MTR-6, "
        f"PHYS-01, PHYS-02, ML_BENCH-01, ML_BENCH-02, ML_BENCH-03, "
        f"SYSID-01, DATA-PIPE-01, DRIFT-01, "
        f"DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01, "
        f"PHARMA-01, FINRISK-01, AGENT-DRIFT-01"
    )


def main():
    if len(sys.argv) != 4:
        print(
            "Usage: python scripts/run_single_claim.py CLAIM_ID INPUT_PATH OUTPUT_PATH",
            file=sys.stderr,
        )
        sys.exit(1)

    claim_id = sys.argv[1]
    input_path = sys.argv[2]
    output_path = sys.argv[3]

    # Change to repo root so relative paths work
    os.chdir(str(REPO_ROOT))

    try:
        result = dispatch(claim_id, input_path)
        _write_output(result, output_path)
        print(f"[run_single_claim] {claim_id} -> {output_path} OK")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
