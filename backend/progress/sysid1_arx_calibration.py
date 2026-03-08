#!/usr/bin/env python3
"""
SYSID-01 ARX Calibration - Deterministic system identification.

Purpose: Estimate (a, b) in y[t+1] = a*y[t] + b*u[t] from synthetic time-series.
Cross-domain claim for portability. Stdlib only, no numpy.
# Part of MetaGenesis Core verification pipeline (MVP v0.1)
"""

import random
from typing import Dict, Any, List, Tuple, Optional

JOB_KIND = "sysid1_arx_calibration"
ALGORITHM_VERSION = "v1"
METHOD = "ols_arx_2param"


def _seeded_noise(seed: int, n: int, scale: float) -> List[float]:
    """Deterministic Gaussian noise."""
    rng = random.Random(seed)
    return [rng.gauss(0, scale) for _ in range(n)]


def _seeded_uniform(seed: int, n: int, low: float, high: float) -> List[float]:
    """Deterministic uniform samples."""
    rng = random.Random(seed)
    return [rng.uniform(low, high) for _ in range(n)]


def generate_synthetic_arx(
    seed: int,
    a_true: float,
    b_true: float,
    n_steps: int,
    u_max: float,
    noise_scale: float = 0.0,
) -> Tuple[List[float], List[float]]:
    """Generate u (deterministic) and y (ARX with optional noise)."""
    u = _seeded_uniform(seed, n_steps, -u_max, u_max)
    noise = _seeded_noise(seed + 1, n_steps, noise_scale) if noise_scale else [0.0] * n_steps
    y = [0.0]
    for t in range(n_steps - 1):
        y_next = a_true * y[t] + b_true * u[t] + noise[t]
        y.append(y_next)
    return u, y


def estimate_arx_2param_ols(
    u: List[float], y: List[float]
) -> Tuple[float, float]:
    """
    Estimate (a, b) via 2x2 normal equations: y[t+1] = a*y[t] + b*u[t].
    Returns (a_hat, b_hat). Raises ValueError if det == 0.
    """
    n = len(y) - 1
    if n < 2:
        raise ValueError("Need at least 3 y values (n_steps >= 3)")
    sum_yy = sum(y[t] ** 2 for t in range(n))
    sum_uu = sum(u[t] ** 2 for t in range(n))
    sum_yu = sum(y[t] * u[t] for t in range(n))
    sum_y_yn = sum(y[t] * y[t + 1] for t in range(n))
    sum_u_yn = sum(u[t] * y[t + 1] for t in range(n))
    det = sum_yy * sum_uu - sum_yu * sum_yu
    if abs(det) < 1e-20:
        raise ValueError("Singular design matrix (det == 0)")
    a_hat = (sum_uu * sum_y_yn - sum_yu * sum_u_yn) / det
    b_hat = (sum_yy * sum_u_yn - sum_yu * sum_y_yn) / det
    return a_hat, b_hat


def compute_rmse(y_actual: List[float], y_pred: List[float]) -> float:
    """Root mean squared error."""
    n = min(len(y_actual), len(y_pred))
    if n == 0:
        return 0.0
    sse = sum((a - p) ** 2 for a, p in zip(y_actual[1:n+1], y_pred[1:n+1]))
    return (sse / n) ** 0.5


def run_calibration(
    seed: int,
    a_true: float,
    b_true: float,
    n_steps: int = 50,
    u_max: float = 1.0,
    noise_scale: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run SYSID-01 ARX calibration. Deterministic synthetic data.
    Model: y[t+1] = a*y[t] + b*u[t]
    """
    if n_steps < 3:
        raise ValueError("n_steps must be >= 3")
    if u_max <= 0:
        raise ValueError("u_max must be > 0")
    if noise_scale is not None and noise_scale < 0:
        raise ValueError("noise_scale must be >= 0")
    if noise_scale is None:
        noise_scale = 0.01 * (abs(a_true) + abs(b_true)) * u_max

    u, y = generate_synthetic_arx(seed, a_true, b_true, n_steps, u_max, noise_scale)
    a_hat, b_hat = estimate_arx_2param_ols(u, y)
    y_pred = [y[0]]
    for t in range(len(y) - 1):
        y_pred.append(a_hat * y[t] + b_hat * u[t])
    rmse = compute_rmse(y, y_pred)
    rel_err_a = abs(a_hat - a_true) / abs(a_true) if a_true != 0 else 0.0
    rel_err_b = abs(b_hat - b_true) / abs(b_true) if b_true != 0 else 0.0

    inputs_summary = {
        "seed": seed,
        "a_true": a_true,
        "b_true": b_true,
        "n_steps": n_steps,
        "u_max": u_max,
        "noise_scale": noise_scale,
    }
    result = {
        "estimated_a": a_hat,
        "estimated_b": b_hat,
        "rmse": rmse,
        "rel_err_a": rel_err_a,
        "rel_err_b": rel_err_b,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
    }
    return {
        "domain": "SYSID",
        "claim_id": "SYSID-01",
        "mtr_phase": "SYSID-01",
        "inputs": inputs_summary,
        "result": result,
    }
