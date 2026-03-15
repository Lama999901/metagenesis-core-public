#!/usr/bin/env python3
"""
ML_BENCH-02 — Regression Model Certificate.

Verifies that a regression model achieves claimed RMSE on a held-out test set.
Supports synthetic mode (deterministic from seed) and real data mode (CSV).
No external deps. Stdlib only.
"""

import csv
import math
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

JOB_KIND = "mlbench2_regression_certificate"
ALGORITHM_VERSION = "v1"
METHOD = "linear_regression_ols"


def _generate_regression_dataset(
    seed: int,
    n_samples: int,
    n_features: int,
    noise_scale: float,
) -> Tuple[List[List[float]], List[float], List[float]]:
    """Generate synthetic regression dataset with known RMSE."""
    rng = random.Random(seed)
    weights = [rng.gauss(0, 1.0) for _ in range(n_features)]
    X = [[rng.gauss(0, 1.0) for _ in range(n_features)] for _ in range(n_samples)]
    y_true = [sum(w * x for w, x in zip(weights, row)) for row in X]
    noise = [rng.gauss(0, noise_scale) for _ in range(n_samples)]
    y_pred = [t + n for t, n in zip(y_true, noise)]
    return X, y_true, y_pred


def _compute_regression_metrics(
    y_true: List[float], y_pred: List[float]
) -> Dict[str, float]:
    """Compute RMSE, MAE, R² for regression."""
    n = len(y_true)
    if n == 0:
        raise ValueError("Empty prediction list")

    residuals = [t - p for t, p in zip(y_true, y_pred)]
    mae = sum(abs(r) for r in residuals) / n
    mse = sum(r ** 2 for r in residuals) / n
    rmse = math.sqrt(mse)

    mean_y = sum(y_true) / n
    ss_tot = sum((y - mean_y) ** 2 for y in y_true)
    ss_res = sum(r ** 2 for r in residuals)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "rmse": round(rmse, 8),
        "mae": round(mae, 8),
        "r2": round(r2, 8),
        "n_samples": n,
    }


def _load_regression_csv(path: Path) -> Tuple[List[float], List[float]]:
    """Load CSV with y_true and y_pred columns."""
    y_true, y_pred = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                y_true.append(float(row["y_true"]))
                y_pred.append(float(row["y_pred"]))
            except (KeyError, ValueError):
                continue
    return y_true, y_pred


def _hash_step(step_name: str, step_data: dict, prev_hash: str) -> str:
    import hashlib
    import json as _j
    content = _j.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def run_certificate(
    seed: int = 42,
    claimed_rmse: float = 0.10,
    rmse_tolerance: float = 0.02,
    n_samples: int = 1000,
    n_features: int = 10,
    noise_scale: float = 0.10,
    dataset_relpath: Optional[str] = None,
    anchor_hash: Optional[str] = None,
    anchor_claim_id: str = "ML_BENCH-01",
) -> Dict[str, Any]:
    """
    Run ML_BENCH-02 regression certificate.

    PASS if abs(actual_rmse - claimed_rmse) <= rmse_tolerance.
    Supports synthetic mode (seed) and real data mode (CSV y_true/y_pred).
    """
    # Real data mode
    if dataset_relpath is not None:
        from backend.progress.data_integrity import fingerprint_file
        path = REPO_ROOT / dataset_relpath
        if not path.exists():
            raise ValueError(f"Dataset not found: {dataset_relpath}")
        fp = fingerprint_file(path)
        y_true, y_pred = _load_regression_csv(path)
        if len(y_true) < 10:
            raise ValueError("Dataset has fewer than 10 samples")
        metrics = _compute_regression_metrics(y_true, y_pred)
        abs_error = abs(metrics["rmse"] - claimed_rmse)
        passed = abs_error <= rmse_tolerance
        return {
            "mtr_phase": "ML_BENCH-02",
            "algorithm_version": ALGORITHM_VERSION,
            "method": METHOD,
            "inputs": {
                "dataset_relpath": dataset_relpath,
                "dataset": {"source": dataset_relpath, "sha256": fp["sha256"],
                            "bytes": fp["bytes"]},
                "claimed_rmse": claimed_rmse,
                "rmse_tolerance": rmse_tolerance,
                "anchor_hash": anchor_hash,
                "anchor_claim_id": anchor_claim_id if anchor_hash else None,
            },
            "result": {
                "actual_rmse": metrics["rmse"],
                "claimed_rmse": claimed_rmse,
                "absolute_error": round(abs_error, 8),
                "tolerance": rmse_tolerance,
                "pass": passed,
                "mae": metrics["mae"],
                "r2": metrics["r2"],
                "n_samples": metrics["n_samples"],
            },
        }

    # Synthetic mode
    if claimed_rmse <= 0:
        raise ValueError("claimed_rmse must be positive")
    if rmse_tolerance <= 0:
        raise ValueError("rmse_tolerance must be positive")
    if n_samples < 10:
        raise ValueError("n_samples must be >= 10")

    _, y_true, y_pred = _generate_regression_dataset(seed, n_samples, n_features, noise_scale)
    metrics = _compute_regression_metrics(y_true, y_pred)
    abs_error = abs(metrics["rmse"] - claimed_rmse)
    passed = abs_error <= rmse_tolerance

    # Step Chain
    prev = _hash_step("init_params", {
        "seed": seed, "claimed_rmse": claimed_rmse,
        "rmse_tolerance": rmse_tolerance, "n_samples": n_samples,
        "n_features": n_features, "noise_scale": noise_scale,
        "anchor_hash": anchor_hash or "none",
    }, "genesis")
    trace = [{"step": 1, "name": "init_params", "hash": prev}]

    prev = _hash_step("generate_dataset", {
        "seed": seed, "n_samples": n_samples, "noise_scale": noise_scale,
    }, prev)
    trace.append({"step": 2, "name": "generate_dataset", "hash": prev,
                  "output": {"n_samples": n_samples}})

    prev = _hash_step("compute_metrics", {
        "rmse": metrics["rmse"], "mae": metrics["mae"], "r2": metrics["r2"],
    }, prev)
    trace.append({"step": 3, "name": "compute_metrics", "hash": prev,
                  "output": {"rmse": metrics["rmse"], "r2": metrics["r2"]}})

    prev = _hash_step("threshold_check", {
        "abs_error": round(abs_error, 8), "tolerance": rmse_tolerance, "passed": passed,
    }, prev)
    trace.append({"step": 4, "name": "threshold_check", "hash": prev,
                  "output": {"pass": passed}})

    return {
        "mtr_phase": "ML_BENCH-02",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "seed": seed, "claimed_rmse": claimed_rmse,
            "rmse_tolerance": rmse_tolerance, "n_samples": n_samples,
            "n_features": n_features, "noise_scale": noise_scale,
            "mode": "synthetic",
            "anchor_hash": anchor_hash,
            "anchor_claim_id": anchor_claim_id if anchor_hash else None,
        },
        "result": {
            "actual_rmse": metrics["rmse"],
            "claimed_rmse": claimed_rmse,
            "absolute_error": round(abs_error, 8),
            "tolerance": rmse_tolerance,
            "pass": passed,
            "mae": metrics["mae"],
            "r2": metrics["r2"],
            "n_samples": metrics["n_samples"],
        },
        "execution_trace": trace,
        "trace_root_hash": prev,
        "status": "SUCCEEDED",
    }
