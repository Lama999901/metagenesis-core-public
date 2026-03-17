#!/usr/bin/env python3
"""
UQ-01 Deterministic Bootstrap Uncertainty Engine v1.

Seeded bootstrap OLS-through-origin. No heavy deps (stdlib only).
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import random
from typing import List, Dict, Any


def _ols_slope_origin(x_values: List[float], y_values: List[float]) -> float:
    """Slope = sum(x*y) / sum(x^2)."""
    n = len(x_values)
    if n == 0:
        return 0.0
    sum_xy = sum(x * y for x, y in zip(x_values, y_values))
    sum_xx = sum(x * x for x in x_values)
    if sum_xx == 0:
        return 0.0
    return sum_xy / sum_xx


def bootstrap_ols_origin(
    x_values: List[float],
    y_values: List[float],
    samples: int,
    seed: int,
) -> Dict[str, Any]:
    """
    Deterministic bootstrap: resample with replacement, OLS-through-origin each time.
    Returns mean, std, ci_low (5th), ci_high (95th), stability_score.
    """
    n = len(x_values)
    if n < 2 or samples < 1:
        return {
            "n": samples,
            "seed": seed,
            "mean": 0.0,
            "std": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "stability_score": 0.0,
            "method": "bootstrap_origin_ols",
            "version": "v1",
        }
    rng = random.Random(seed)
    distribution: List[float] = []
    for _ in range(samples):
        indices = [rng.randrange(n) for _ in range(n)]
        x_boot = [x_values[i] for i in indices]
        y_boot = [y_values[i] for i in indices]
        slope = _ols_slope_origin(x_boot, y_boot)
        distribution.append(slope)

    dist_sorted = sorted(distribution)
    mean = sum(distribution) / len(distribution)
    variance = sum((v - mean) ** 2 for v in distribution) / len(distribution)
    std = variance ** 0.5 if variance >= 0 else 0.0

    k = len(dist_sorted)
    idx_low = int(0.05 * (k - 1)) if k > 1 else 0
    idx_high = int(0.95 * (k - 1)) if k > 1 else 0
    ci_low = dist_sorted[idx_low]
    ci_high = dist_sorted[idx_high]

    if mean != 0:
        raw_stability = 1.0 - (std / abs(mean))
        stability_score = max(0.0, min(1.0, raw_stability))
    else:
        stability_score = 0.0

    return {
        "n": samples,
        "seed": seed,
        "mean": mean,
        "std": std,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "stability_score": stability_score,
        "method": "bootstrap_origin_ols",
        "version": "v1",
    }
