#!/usr/bin/env python3
"""
MTR-4 Titanium Ti-6Al-4V Young's Modulus Calibration - OLS through origin.

Purpose: Deterministic calibration workload for Progress Engine evidence.
Synthetic mode or dataset-backed (DATA-01 fingerprint). No heavy deps (stdlib only).
"""

import csv
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

JOB_KIND = "mtr4_titanium_modulus_calibration"
ALGORITHM_VERSION = "v1"
METHOD = "ols_origin"


def _seeded_noise(seed: int, n: int, scale: float) -> List[float]:
    """Deterministic noise for n points. Scale is absolute (e.g. stress units)."""
    rng = random.Random(seed)
    return [rng.gauss(0, scale) for _ in range(n)]


def generate_synthetic_data(
    seed: int,
    E_true: float,
    n_points: int,
    max_strain: float,
    noise_scale: float,
) -> Tuple[List[float], List[float]]:
    """Strain = linear grid [0..max_strain], stress = E_true * strain + deterministic noise."""
    strain = [max_strain * i / (n_points - 1) if n_points > 1 else 0.0 for i in range(n_points)]
    noise = _seeded_noise(seed, n_points, noise_scale)
    stress = [E_true * strain[i] + noise[i] for i in range(n_points)]
    return strain, stress


def estimate_E_ols_origin(strain: List[float], stress: List[float]) -> float:
    """E_hat = sum(strain_i * stress_i) / sum(strain_i^2)."""
    n = len(strain)
    if n == 0:
        return 0.0
    sum_se = sum(s * e for s, e in zip(strain, stress))
    sum_ee = sum(e * e for e in strain)
    if sum_ee == 0:
        return 0.0
    return sum_se / sum_ee


def compute_rmse(stress_actual: List[float], stress_pred: List[float]) -> float:
    """Root mean squared error."""
    n = len(stress_actual)
    if n == 0:
        return 0.0
    sse = sum((a - p) ** 2 for a, p in zip(stress_actual, stress_pred))
    return (sse / n) ** 0.5


def _load_stress_strain_csv(path: Path, elastic_strain_max: float) -> Tuple[List[float], List[float]]:
    """Load CSV with headers strain, stress; return points with strain <= elastic_strain_max."""
    strain, stress = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                s = float(row["strain"])
                t = float(row["stress"])
                if s <= elastic_strain_max:
                    strain.append(s)
                    stress.append(t)
            except (KeyError, ValueError):
                continue
    return strain, stress


def run_calibration(
    seed: int = 42,
    E_true: float = 114.0e9,
    n_points: int = 50,
    max_strain: float = 0.002,
    noise_scale: float = None,
    dataset_relpath: Optional[str] = None,
    elastic_strain_max: float = 0.002,
    uq_samples: Optional[int] = None,
    uq_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run MTR-4 calibration. If dataset_relpath is set, load CSV (strain, stress) and fingerprint;
    otherwise use synthetic data. No absolute paths in result.
    """
    if dataset_relpath is not None:
        from backend.progress.data_integrity import fingerprint_file
        path = REPO_ROOT / dataset_relpath
        if not path.exists():
            raise ValueError(f"Dataset not found: {dataset_relpath}")
        fp = fingerprint_file(path)
        strain, stress = _load_stress_strain_csv(path, elastic_strain_max)
        if len(strain) < 2:
            raise ValueError("Dataset has fewer than 2 points in elastic region (strain <= elastic_strain_max)")
        E_hat = estimate_E_ols_origin(strain, stress)
        stress_pred = [E_hat * e for e in strain]
        rmse = compute_rmse(stress, stress_pred)
        dataset_info = {
            "source": dataset_relpath,
            "sha256": fp["sha256"],
            "bytes": fp["bytes"],
            "rows": fp.get("rows"),
            "cols": fp.get("cols"),
        }
        inputs_summary = {
            "dataset_relpath": dataset_relpath,
            "elastic_strain_max": elastic_strain_max,
            "dataset": dataset_info,
        }
        result = {
            "estimated_E": E_hat,
            "rmse": rmse,
            "method": METHOD,
            "algorithm_version": ALGORITHM_VERSION,
            "n_points": len(strain),
        }
        if uq_samples and uq_samples > 0:
            from backend.progress.uncertainty import bootstrap_ols_origin
            uq_seed_val = uq_seed if uq_seed is not None else seed
            result["uncertainty"] = bootstrap_ols_origin(strain, stress, uq_samples, uq_seed_val)
        return {
            "mtr_phase": "MTR-4",
            "inputs": inputs_summary,
            "result": result,
        }

    if max_strain <= 0:
        raise ValueError("max_strain must be positive (avoid division by zero in OLS)")
    if n_points < 2:
        raise ValueError("n_points must be >= 2 for strain grid with non-zero values")
    if noise_scale is None:
        noise_scale = (E_true * max_strain) * 0.005
    strain, stress = generate_synthetic_data(seed, E_true, n_points, max_strain, noise_scale)
    E_hat = estimate_E_ols_origin(strain, stress)
    stress_pred = [E_hat * e for e in strain]
    rmse = compute_rmse(stress, stress_pred)
    relative_error = abs(E_hat - E_true) / E_true if E_true != 0 else 0.0

    inputs_summary = {
        "E_true": E_true,
        "n_points": n_points,
        "max_strain": max_strain,
        "noise_spec": "gaussian",
        "noise_scale": noise_scale,
        "seed": seed,
    }
    result = {
        "estimated_E": E_hat,
        "rmse": rmse,
        "relative_error": relative_error,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
        "n_points": n_points,
    }
    if uq_samples and uq_samples > 0:
        from backend.progress.uncertainty import bootstrap_ols_origin
        uq_seed_val = uq_seed if uq_seed is not None else seed
        result["uncertainty"] = bootstrap_ols_origin(strain, stress, uq_samples, uq_seed_val)
    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _prev = _hash_step("init_params", {"seed": seed, "E_true": E_true, "n_points": n_points, "max_strain": max_strain, "noise_scale": round(noise_scale, 8)}, "genesis")
    _trace = [{"step": 1, "name": "init_params", "hash": _prev}]
    _prev = _hash_step("generate_data", {"n_points": n_points, "noise_scale": round(noise_scale, 8)}, _prev)
    _trace.append({"step": 2, "name": "generate_data", "hash": _prev, "output": {"n_points": n_points}})
    _prev = _hash_step("estimate_E", {"E_hat": round(E_hat, 6), "relative_error": round(relative_error, 8)}, _prev)
    _trace.append({"step": 3, "name": "estimate_E", "hash": _prev, "output": {"relative_error": round(relative_error, 8)}})
    _passed_sc = relative_error <= 0.01
    _prev = _hash_step("threshold_check", {"relative_error": round(relative_error, 8), "threshold": 0.01, "passed": _passed_sc}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": _passed_sc}})
    _trace_root_hash = _prev
    # --- End Step Chain ---
    return {
        "mtr_phase": "MTR-4",
        "inputs": inputs_summary,
        "result": result,
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
