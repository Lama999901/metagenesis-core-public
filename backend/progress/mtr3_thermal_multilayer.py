#!/usr/bin/env python3
"""
MTR-3 Two-parameter thermal calibration: k + contact resistance.

Model: ΔT = (L/(k*A) + r_contact)*Q. Two setups (L1,A1) and (L2,A2) give
y = a*x1 + b*x2 with x1=(L/A)*Q, x2=Q; a=1/k, b=r_contact.
OLS 2-param via normal equations (no numpy). Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import random
from typing import Dict, Any, List, Tuple

JOB_KIND = "mtr3_thermal_multilayer_contact_calibration"
ALGORITHM_VERSION = "v1"
METHOD = "ols_2param"


def _seeded_noise(seed: int, n: int, scale: float) -> List[float]:
    rng = random.Random(seed)
    return [rng.gauss(0, scale) for _ in range(n)]


def generate_synthetic_data(
    seed: int,
    k_true: float,
    r_contact_true: float,
    n_points: int,
    L1: float,
    A1: float,
    L2: float,
    A2: float,
    q_max: float,
    noise_scale: float,
) -> Tuple[List[float], List[float], List[float]]:
    """Two setups: same Q grid 0..q_max. x1=(L/A)*Q, x2=Q, y = (L/(k*A)+r_contact)*Q + noise.
    Returns (x1_list, x2_list, y_list) with 2*n_points rows (setup1 then setup2).
    """
    if k_true <= 0 or A1 <= 0 or A2 <= 0:
        raise ValueError("k_true, A1, A2 must be positive")
    s1 = (L1 / (k_true * A1)) + r_contact_true
    s2 = (L2 / (k_true * A2)) + r_contact_true
    Q = [q_max * i / (n_points - 1) if n_points > 1 else 0.0 for i in range(n_points)]
    noise1 = _seeded_noise(seed, n_points, noise_scale)
    noise2 = _seeded_noise(seed + 1, n_points, noise_scale)
    x1_list, x2_list, y_list = [], [], []
    for i in range(n_points):
        q = Q[i]
        x1_list.append((L1 / A1) * q)
        x2_list.append(q)
        y_list.append(s1 * q + noise1[i])
    for i in range(n_points):
        q = Q[i]
        x1_list.append((L2 / A2) * q)
        x2_list.append(q)
        y_list.append(s2 * q + noise2[i])
    return x1_list, x2_list, y_list


def solve_2x2_ols(
    x1: List[float], x2: List[float], y: List[float]
) -> Tuple[float, float]:
    """Solve normal equations (X'X) beta = X'Y for beta = (a, b). No numpy."""
    n = len(y)
    if n < 2:
        return 0.0, 0.0
    sum_x1 = sum(x1)
    sum_x2 = sum(x2)
    sum_y = sum(y)
    sum_x1x1 = sum(a * a for a in x1)
    sum_x1x2 = sum(a * b for a, b in zip(x1, x2))
    sum_x2x2 = sum(b * b for b in x2)
    sum_x1y = sum(a * yi for a, yi in zip(x1, y))
    sum_x2y = sum(b * yi for b, yi in zip(x2, y))
    # X'X = [[sum_x1x1, sum_x1x2], [sum_x1x2, sum_x2x2]]
    # det = sum_x1x1*sum_x2x2 - sum_x1x2*sum_x1x2
    det = sum_x1x1 * sum_x2x2 - sum_x1x2 * sum_x1x2
    if det == 0:
        raise ValueError("det(X'X) == 0; two setups are degenerate")
    a_hat = (sum_x2x2 * sum_x1y - sum_x1x2 * sum_x2y) / det
    b_hat = (sum_x1x1 * sum_x2y - sum_x1x2 * sum_x1y) / det
    return a_hat, b_hat


def compute_rmse(actual: List[float], pred: List[float]) -> float:
    n = len(actual)
    if n == 0:
        return 0.0
    sse = sum((a - p) ** 2 for a, p in zip(actual, pred))
    return (sse / n) ** 0.5


def run_calibration(
    seed: int,
    k_true: float,
    r_contact_true: float,
    n_points: int = 50,
    L1: float = 0.01,
    A1: float = 1e-4,
    L2: float = 0.02,
    A2: float = 1e-4,
    q_max: float = 10.0,
    noise_scale: float = None,
) -> Dict[str, Any]:
    """Run MTR-3 two-parameter calibration. noise_scale defaults to (max ΔT) * 0.01."""
    if k_true <= 0:
        raise ValueError("k_true must be positive")
    if L1 <= 0 or A1 <= 0 or L2 <= 0 or A2 <= 0:
        raise ValueError("L1, A1, L2, A2 must be positive")
    if q_max <= 0:
        raise ValueError("q_max must be positive")
    if n_points < 2:
        raise ValueError("n_points must be >= 2")
    ratio1 = L1 / A1
    ratio2 = L2 / A2
    if ratio1 == ratio2:
        raise ValueError("(L1/A1) must not equal (L2/A2)")

    max_delta_T1 = (L1 / (k_true * A1) + r_contact_true) * q_max
    max_delta_T2 = (L2 / (k_true * A2) + r_contact_true) * q_max
    max_delta_T_true = max(max_delta_T1, max_delta_T2)
    if noise_scale is None:
        noise_scale = max_delta_T_true * 0.01

    x1, x2, y = generate_synthetic_data(
        seed, k_true, r_contact_true, n_points, L1, A1, L2, A2, q_max, noise_scale
    )
    a_hat, b_hat = solve_2x2_ols(x1, x2, y)
    if a_hat <= 0:
        raise ValueError("a_hat <= 0; cannot recover k_hat")

    k_hat = 1.0 / a_hat
    r_hat = b_hat
    y_pred = [a_hat * a + b_hat * b for a, b in zip(x1, x2)]
    rmse = compute_rmse(y, y_pred)
    rel_err_k = abs(k_hat - k_true) / k_true if k_true != 0 else 0.0
    if r_contact_true != 0:
        rel_err_r = abs(r_hat - r_contact_true) / abs(r_contact_true)
    else:
        denom = max_delta_T_true * 0.01 or 1e-12
        rel_err_r = abs(r_hat) / denom

    inputs_summary = {
        "k_true": k_true,
        "r_contact_true": r_contact_true,
        "n_points": n_points,
        "L1": L1,
        "A1": A1,
        "L2": L2,
        "A2": A2,
        "q_max": q_max,
        "noise_scale": noise_scale,
        "seed": seed,
    }
    result = {
        "estimated_k": k_hat,
        "estimated_r_contact": r_hat,
        "rmse": rmse,
        "rel_err_k": rel_err_k,
        "rel_err_r": rel_err_r,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
    }
    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _prev = _hash_step("init_params", {"seed": seed, "k_true": k_true, "r_contact_true": r_contact_true, "n_points": n_points, "noise_scale": round(noise_scale, 8)}, "genesis")
    _trace = [{"step": 1, "name": "init_params", "hash": _prev}]
    _prev = _hash_step("generate_data", {"n_points": n_points, "noise_scale": round(noise_scale, 8)}, _prev)
    _trace.append({"step": 2, "name": "generate_data", "hash": _prev, "output": {"n_points": n_points}})
    _prev = _hash_step("estimate_params", {"k_hat": round(k_hat, 6), "r_hat": round(r_hat, 8), "rel_err_k": round(rel_err_k, 8), "rel_err_r": round(rel_err_r, 8)}, _prev)
    _trace.append({"step": 3, "name": "estimate_params", "hash": _prev, "output": {"rel_err_k": round(rel_err_k, 8), "rel_err_r": round(rel_err_r, 8)}})
    _passed_sc = rel_err_k <= 0.03 and rel_err_r <= 0.05
    _prev = _hash_step("threshold_check", {"rel_err_k": round(rel_err_k, 8), "rel_err_r": round(rel_err_r, 8), "threshold_k": 0.03, "threshold_r": 0.05, "passed": _passed_sc}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": _passed_sc}})
    _trace_root_hash = _prev
    # --- End Step Chain ---
    return {
        "mtr_phase": "MTR-3",
        "inputs": inputs_summary,
        "result": result,
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
