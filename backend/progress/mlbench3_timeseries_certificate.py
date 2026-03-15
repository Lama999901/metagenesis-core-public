#!/usr/bin/env python3
"""
ML_BENCH-03 — Time-Series Forecast Certificate.
Verifies MAPE of a forecast model against claimed value.
Supports synthetic (seed-based) and real data (CSV: t, y_true, y_pred) modes.
"""
import csv
import math
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JOB_KIND = "mlbench3_timeseries_certificate"
ALGORITHM_VERSION = "v1"
METHOD = "mape_horizon_verification"


def _generate_ts(seed, n_steps, trend, noise_scale):
    rng = random.Random(seed)
    y_true = [trend * t + rng.gauss(0, noise_scale) for t in range(n_steps)]
    y_pred = [v + rng.gauss(0, noise_scale * 0.5) for v in y_true]
    return y_true, y_pred


def _compute_mape(y_true, y_pred):
    if len(y_true) == 0:
        raise ValueError("Empty series")
    errs = []
    for t, p in zip(y_true, y_pred):
        if t == 0.0:
            continue
        errs.append(abs((t - p) / t))
    if not errs:
        raise ValueError("All y_true values are zero — MAPE undefined")
    return sum(errs) / len(errs)


def _load_ts_csv(path):
    y_true, y_pred = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                y_true.append(float(row["y_true"]))
                y_pred.append(float(row["y_pred"]))
            except (KeyError, ValueError):
                continue
    return y_true, y_pred


def _hash_step(step_name, step_data, prev_hash):
    import hashlib
    import json as _j
    content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def run_certificate(
    seed: int = 42,
    claimed_mape: float = 0.05,
    mape_tolerance: float = 0.02,
    n_steps: int = 200,
    trend: float = 1.0,
    noise_scale: float = 5.0,
    dataset_relpath: Optional[str] = None,
    anchor_hash: Optional[str] = None,
    anchor_claim_id: str = "ML_BENCH-01",
) -> Dict[str, Any]:
    if dataset_relpath is not None:
        from backend.progress.data_integrity import fingerprint_file
        path = REPO_ROOT / dataset_relpath
        if not path.exists():
            raise ValueError(f"Dataset not found: {dataset_relpath}")
        fp = fingerprint_file(path)
        y_true, y_pred = _load_ts_csv(path)
        if len(y_true) < 10:
            raise ValueError("Dataset has fewer than 10 timesteps")
        actual_mape = _compute_mape(y_true, y_pred)
        abs_err = abs(actual_mape - claimed_mape)
        passed = abs_err <= mape_tolerance
        return {
            "mtr_phase": "ML_BENCH-03",
            "algorithm_version": ALGORITHM_VERSION,
            "method": METHOD,
            "inputs": {
                "dataset_relpath": dataset_relpath,
                "dataset": {"source": dataset_relpath, "sha256": fp["sha256"], "bytes": fp["bytes"]},
                "claimed_mape": claimed_mape,
                "mape_tolerance": mape_tolerance,
                "anchor_hash": anchor_hash,
                "anchor_claim_id": anchor_claim_id if anchor_hash else None,
            },
            "result": {
                "actual_mape": round(actual_mape, 8),
                "claimed_mape": claimed_mape,
                "absolute_error": round(abs_err, 8),
                "tolerance": mape_tolerance,
                "pass": passed,
                "n_steps": len(y_true),
            },
        }

    if claimed_mape <= 0:
        raise ValueError("claimed_mape must be positive")
    if mape_tolerance <= 0:
        raise ValueError("mape_tolerance must be positive")
    if n_steps < 10:
        raise ValueError("n_steps must be >= 10")

    y_true, y_pred = _generate_ts(seed, n_steps, trend, noise_scale)
    actual_mape = _compute_mape(y_true, y_pred)
    abs_err = abs(actual_mape - claimed_mape)
    passed = abs_err <= mape_tolerance

    p = _hash_step("init_params", {
        "seed": seed,
        "claimed_mape": claimed_mape,
        "mape_tolerance": mape_tolerance,
        "n_steps": n_steps,
        "trend": trend,
        "noise_scale": noise_scale,
        "anchor_hash": anchor_hash or "none",
    }, "genesis")
    trace = [{"step": 1, "name": "init_params", "hash": p}]
    p = _hash_step("generate_series", {"n_steps": n_steps, "seed": seed}, p)
    trace.append({"step": 2, "name": "generate_series", "hash": p, "output": {"n_steps": n_steps}})
    p = _hash_step("compute_mape", {"actual_mape": round(actual_mape, 8)}, p)
    trace.append({"step": 3, "name": "compute_mape", "hash": p, "output": {"actual_mape": round(actual_mape, 8)}})
    p = _hash_step("threshold_check", {"abs_err": round(abs_err, 8), "tol": mape_tolerance, "passed": passed}, p)
    trace.append({"step": 4, "name": "threshold_check", "hash": p, "output": {"pass": passed}})

    return {
        "mtr_phase": "ML_BENCH-03",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "seed": seed,
            "claimed_mape": claimed_mape,
            "mape_tolerance": mape_tolerance,
            "n_steps": n_steps,
            "trend": trend,
            "noise_scale": noise_scale,
            "mode": "synthetic",
            "anchor_hash": anchor_hash,
            "anchor_claim_id": anchor_claim_id if anchor_hash else None,
        },
        "result": {
            "actual_mape": round(actual_mape, 8),
            "claimed_mape": claimed_mape,
            "absolute_error": round(abs_err, 8),
            "tolerance": mape_tolerance,
            "pass": passed,
            "n_steps": n_steps,
        },
        "execution_trace": trace,
        "trace_root_hash": p,
        "status": "SUCCEEDED",
    }
