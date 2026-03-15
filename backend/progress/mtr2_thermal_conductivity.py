#!/usr/bin/env python3
"""
MTR-2 Thermal Paste Conductivity Calibration - OLS through origin.

Model: ΔT = (L/(k*A)) * Q. Estimate slope s_hat; k_hat = L / (A * s_hat).
No heavy deps (stdlib only). Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import random
from typing import Dict, Any, List, Tuple

JOB_KIND = "mtr2_thermal_paste_conductivity_calibration"
ALGORITHM_VERSION = "v1"
METHOD = "ols_origin"


def _seeded_noise(seed: int, n: int, scale: float) -> List[float]:
    rng = random.Random(seed)
    return [rng.gauss(0, scale) for _ in range(n)]


def generate_synthetic_data(
    seed: int,
    k_true: float,
    n_points: int,
    L: float,
    A: float,
    q_max: float,
    noise_scale: float,
) -> Tuple[List[float], List[float]]:
    """Q = linear grid [0..q_max], ΔT = (L/(k_true*A))*Q + noise."""
    s_true = L / (k_true * A) if (k_true and A) else 0.0
    Q = [q_max * i / (n_points - 1) if n_points > 1 else 0.0 for i in range(n_points)]
    noise = _seeded_noise(seed, n_points, noise_scale)
    delta_T = [s_true * Q[i] + noise[i] for i in range(n_points)]
    return Q, delta_T


def estimate_slope_ols_origin(Q: List[float], delta_T: List[float]) -> float:
    """s_hat = sum(Q_i * ΔT_i) / sum(Q_i^2)."""
    n = len(Q)
    if n == 0:
        return 0.0
    sum_qt = sum(q * t for q, t in zip(Q, delta_T))
    sum_qq = sum(q * q for q in Q)
    if sum_qq == 0:
        return 0.0
    return sum_qt / sum_qq


def compute_rmse(actual: List[float], pred: List[float]) -> float:
    n = len(actual)
    if n == 0:
        return 0.0
    sse = sum((a - p) ** 2 for a, p in zip(actual, pred))
    return (sse / n) ** 0.5


def run_calibration(
    seed: int,
    k_true: float,
    n_points: int = 50,
    L: float = 0.01,
    A: float = 1e-4,
    q_max: float = 10.0,
    noise_scale: float = None,
) -> Dict[str, Any]:
    """Run MTR-2 calibration. noise_scale defaults to (max ΔT) * 0.01."""
    if n_points < 2:
        raise ValueError("n_points must be >= 2")
    if q_max <= 0 or L <= 0 or A <= 0 or k_true <= 0:
        raise ValueError("q_max, L, A, k_true must be positive")
    max_delta_T_true = (L / (k_true * A)) * q_max
    if noise_scale is None:
        noise_scale = max_delta_T_true * 0.01
    Q, delta_T = generate_synthetic_data(seed, k_true, n_points, L, A, q_max, noise_scale)
    s_hat = estimate_slope_ols_origin(Q, delta_T)
    if s_hat == 0:
        raise ValueError("OLS slope is zero; cannot recover k_hat")
    k_hat = L / (A * s_hat)
    delta_T_pred = [s_hat * q for q in Q]
    rmse = compute_rmse(delta_T, delta_T_pred)
    relative_error = abs(k_hat - k_true) / k_true if k_true != 0 else 0.0

    inputs_summary = {
        "k_true": k_true,
        "n_points": n_points,
        "L": L,
        "A": A,
        "q_max": q_max,
        "noise_scale": noise_scale,
        "seed": seed,
    }
    result = {
        "estimated_k": k_hat,
        "rmse": rmse,
        "relative_error": relative_error,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
    }
    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _prev = _hash_step("init_params", {"seed": seed, "k_true": k_true, "n_points": n_points, "L": L, "A": A, "q_max": q_max, "noise_scale": round(noise_scale, 8)}, "genesis")
    _trace = [{"step": 1, "name": "init_params", "hash": _prev}]
    _prev = _hash_step("generate_data", {"n_points": n_points, "noise_scale": round(noise_scale, 8)}, _prev)
    _trace.append({"step": 2, "name": "generate_data", "hash": _prev, "output": {"n_points": n_points}})
    _prev = _hash_step("estimate_k", {"k_hat": round(k_hat, 6), "relative_error": round(relative_error, 8)}, _prev)
    _trace.append({"step": 3, "name": "estimate_k", "hash": _prev, "output": {"relative_error": round(relative_error, 8)}})
    _passed_sc = relative_error <= 0.02
    _prev = _hash_step("threshold_check", {"relative_error": round(relative_error, 8), "threshold": 0.02, "passed": _passed_sc}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": _passed_sc}})
    _trace_root_hash = _prev
    # --- End Step Chain ---
    return {
        "mtr_phase": "MTR-2",
        "inputs": inputs_summary,
        "result": result,
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
