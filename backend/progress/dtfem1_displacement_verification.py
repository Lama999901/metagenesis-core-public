#!/usr/bin/env python3
"""
DT-FEM-01 Digital Twin FEM Verification Certificate.

Purpose: Verify that a FEM/simulation solver output matches a physical
reference measurement within a proven relative error threshold.

This claim does NOT implement a FEM solver. It verifies the OUTPUT
of any external FEM solver (ANSYS, FEniCS, OpenFOAM, COMSOL, custom)
against a physical reference value (lab measurement, known constant).

Supports:
  - Synthetic mode: deterministic single-value pairs from seed
  - Real data mode: CSV with columns fem_value, measured_value, quantity

No heavy deps. Stdlib only.
# Part of MetaGenesis Core verification pipeline (MVP v0.1)
"""

import csv
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

JOB_KIND = "dtfem1_displacement_verification"
ALGORITHM_VERSION = "v1"
METHOD = "fem_vs_reference_rel_err"

DEFAULT_REL_ERR_THRESHOLD = 0.02  # 2% — standard FEM calibration tolerance


def compute_rel_err(fem_value: float, reference_value: float) -> float:
    """rel_err = |fem - reference| / |reference|. Raises if reference == 0."""
    if reference_value == 0.0:
        raise ValueError("reference_value must be non-zero")
    return abs(fem_value - reference_value) / abs(reference_value)


def _seeded_fem_pair(
    seed: int,
    reference_value: float,
    noise_scale: float,
) -> Tuple[float, float]:
    """
    Generate a deterministic (fem_value, reference_value) pair.
    fem_value = reference_value + gaussian noise at noise_scale fraction.
    Same seed always produces the same result.
    """
    rng = random.Random(seed)
    noise = rng.gauss(0, reference_value * noise_scale)
    fem_value = reference_value + noise
    return fem_value, reference_value


def _load_fem_csv(path: Path) -> List[Dict[str, Any]]:
    """
    Load CSV with columns: fem_value, measured_value, quantity (optional).
    Returns list of dicts. Skips rows with parse errors.
    """
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                entry = {
                    "fem_value": float(row["fem_value"]),
                    "measured_value": float(row["measured_value"]),
                    "quantity": str(row.get("quantity", "")).strip(),
                }
                rows.append(entry)
            except (KeyError, ValueError):
                continue
    return rows


def run_certificate(
    seed: int,
    reference_value: float = 1.0,
    rel_err_threshold: float = DEFAULT_REL_ERR_THRESHOLD,
    noise_scale: float = 0.005,
    quantity: str = "displacement_mm",
    units: str = "mm",
    dataset_relpath: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run DT-FEM-01 verification certificate.

    Synthetic mode (dataset_relpath=None):
      Generates a deterministic FEM/reference pair from seed.
      rel_err = |fem - reference| / |reference|
      PASS if rel_err <= rel_err_threshold.

    Real data mode (dataset_relpath set):
      Loads CSV (fem_value, measured_value, quantity columns).
      Computes per-row rel_err. Reports max_rel_err and per-row results.
      PASS if max_rel_err <= rel_err_threshold.

    Args:
        seed: RNG seed for synthetic mode determinism
        reference_value: Physical reference measurement (synthetic mode)
        rel_err_threshold: Maximum allowed relative error (default 0.02 = 2%)
        noise_scale: FEM noise as fraction of reference (synthetic mode, default 0.005)
        quantity: Physical quantity being verified (e.g. 'displacement_mm')
        units: Physical units string (e.g. 'mm', 'MPa', 'K')
        dataset_relpath: Relative path to CSV from repo root (real data mode)

    Returns:
        Dict with mtr_phase='DT-FEM-01', inputs, result keys.
        result.pass is True if verification succeeds.
    """
    if rel_err_threshold <= 0:
        raise ValueError("rel_err_threshold must be positive")
    if noise_scale < 0:
        raise ValueError("noise_scale must be >= 0")

    # ── Real data mode ──────────────────────────────────────────────────
    if dataset_relpath is not None:
        from backend.progress.data_integrity import fingerprint_file
        path = REPO_ROOT / dataset_relpath
        if not path.exists():
            raise ValueError(f"Dataset not found: {dataset_relpath}")
        fp = fingerprint_file(path)
        rows = _load_fem_csv(path)
        if len(rows) < 1:
            raise ValueError("Dataset has no valid rows (need fem_value, measured_value columns)")

        per_row = []
        for i, row in enumerate(rows):
            rel_err = compute_rel_err(row["fem_value"], row["measured_value"])
            per_row.append({
                "row": i,
                "quantity": row["quantity"] or quantity,
                "fem_value": row["fem_value"],
                "measured_value": row["measured_value"],
                "rel_err": round(rel_err, 8),
                "pass": rel_err <= rel_err_threshold,
            })

        max_rel_err = max(r["rel_err"] for r in per_row)
        passed = max_rel_err <= rel_err_threshold

        return {
            "mtr_phase": "DT-FEM-01",
            "algorithm_version": ALGORITHM_VERSION,
            "method": METHOD,
            "inputs": {
                "dataset_relpath": dataset_relpath,
                "rel_err_threshold": rel_err_threshold,
                "units": units,
                "dataset": {
                    "source": dataset_relpath,
                    "sha256": fp["sha256"],
                    "bytes": fp["bytes"],
                    "rows": len(rows),
                },
            },
            "result": {
                "max_rel_err": round(max_rel_err, 8),
                "rel_err_threshold": rel_err_threshold,
                "n_points": len(per_row),
                "pass": passed,
                "per_row": per_row,
                "method": METHOD,
                "algorithm_version": ALGORITHM_VERSION,
            },
        }

    # ── Synthetic mode ───────────────────────────────────────────────────
    if reference_value == 0.0:
        raise ValueError("reference_value must be non-zero in synthetic mode")

    fem_value, ref_value = _seeded_fem_pair(seed, reference_value, noise_scale)
    rel_err = compute_rel_err(fem_value, ref_value)
    passed = rel_err <= rel_err_threshold

    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _prev = _hash_step("init_params", {"seed": seed, "reference_value": reference_value, "rel_err_threshold": rel_err_threshold, "noise_scale": noise_scale, "quantity": quantity, "units": units}, "genesis")
    _trace = [{"step": 1, "name": "init_params", "hash": _prev}]
    _prev = _hash_step("generate_fem_pair", {"fem_value": round(fem_value, 8), "ref_value": round(ref_value, 8)}, _prev)
    _trace.append({"step": 2, "name": "generate_fem_pair", "hash": _prev, "output": {"fem_value": round(fem_value, 8)}})
    _prev = _hash_step("compute_rel_err", {"rel_err": round(rel_err, 8)}, _prev)
    _trace.append({"step": 3, "name": "compute_rel_err", "hash": _prev, "output": {"rel_err": round(rel_err, 8)}})
    _prev = _hash_step("threshold_check", {"rel_err": round(rel_err, 8), "threshold": rel_err_threshold, "passed": passed}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": passed}})
    _trace_root_hash = _prev
    # --- End Step Chain ---
    return {
        "mtr_phase": "DT-FEM-01",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "seed": seed,
            "reference_value": reference_value,
            "rel_err_threshold": rel_err_threshold,
            "noise_scale": noise_scale,
            "quantity": quantity,
            "units": units,
        },
        "result": {
            "fem_value": fem_value,
            "reference_value": ref_value,
            "rel_err": round(rel_err, 8),
            "rel_err_threshold": rel_err_threshold,
            "pass": passed,
            "quantity": quantity,
            "units": units,
            "method": METHOD,
            "algorithm_version": ALGORITHM_VERSION,
        },
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
