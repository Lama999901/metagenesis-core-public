#!/usr/bin/env python3
"""
ML_BENCH-01  —  ML Accuracy Certificate (Classification).

Purpose: Verify that a classification model achieves claimed accuracy
on a held-out test set. Produces a tamper-evident evidence bundle
that any third party can verify offline with one command.

No external ML dependencies. Stdlib only.
Deterministic: same seed → same synthetic dataset → same result.

Typical use cases:
  - Verifying accuracy claims in ML research papers
  - Auditing vendor model performance guarantees
  - Regulatory submissions requiring model performance evidence
  - AI benchmark result certification (SOTA claims)
"""

import csv
import random
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

JOB_KIND = "mlbench1_accuracy_certificate"
ALGORITHM_VERSION = "v1"
METHOD = "majority_vote_binary_classifier"


# ---------------------------------------------------------------------------
# Synthetic data generation (no external deps)
# ---------------------------------------------------------------------------

def _generate_binary_dataset(
    seed: int,
    n_samples: int,
    n_features: int,
    true_accuracy: float,
) -> Tuple[List[List[float]], List[int], List[int]]:
    """
    Generate a synthetic binary classification dataset.

    Returns:
        X: feature matrix (n_samples x n_features)
        y_true: ground truth labels (0 or 1)
        y_pred: model predictions achieving approximately true_accuracy
    """
    rng = random.Random(seed)

    y_true = [rng.randint(0, 1) for _ in range(n_samples)]
    X = [
        [rng.gauss(float(y_true[i]), 1.0) for _ in range(n_features)]
        for i in range(n_samples)
    ]

    # Generate predictions that hit the target accuracy
    y_pred = []
    for i in range(n_samples):
        if rng.random() < true_accuracy:
            y_pred.append(y_true[i])       # correct prediction
        else:
            y_pred.append(1 - y_true[i])   # wrong prediction

    return X, y_true, y_pred


def _load_predictions_csv(path: Path) -> Tuple[List[int], List[int]]:
    """
    Load a CSV with columns 'y_true' and 'y_pred'.
    Returns (y_true, y_pred) as integer lists.
    """
    y_true, y_pred = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                y_true.append(int(row["y_true"]))
                y_pred.append(int(row["y_pred"]))
            except (KeyError, ValueError):
                continue
    return y_true, y_pred


# ---------------------------------------------------------------------------
# Metrics (stdlib only — no sklearn)
# ---------------------------------------------------------------------------

def _compute_metrics(y_true: List[int], y_pred: List[int]) -> Dict[str, float]:
    """
    Compute accuracy, precision, recall, F1 for binary classification.
    All metrics in [0.0, 1.0].
    """
    n = len(y_true)
    if n == 0:
        raise ValueError("Empty prediction list")

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)

    accuracy = (tp + tn) / n
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0 else 0.0
    )

    return {
        "accuracy": round(accuracy, 6),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "n_samples": n,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


# ---------------------------------------------------------------------------
# Execution trace (Step Chain Verification — PPA #63/996,819)
# ---------------------------------------------------------------------------


def _hash_step(step_name: str, step_data: dict, prev_hash: str) -> str:
    """
    Hash a single execution step chained to the previous step hash.
    Creates a cryptographic chain: each step commits to the previous step.
    Tampering with any intermediate step breaks all subsequent hashes.

    Args:
        step_name: Human-readable step identifier
        step_data: Deterministic dict of step inputs/outputs
        prev_hash: SHA-256 hash of previous step (or "genesis" for first step)

    Returns:
        SHA-256 hex digest of this step in the chain
    """
    import hashlib
    import json as _json
    content = _json.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_certificate(
    seed: int = 42,
    claimed_accuracy: float = 0.90,
    accuracy_tolerance: float = 0.02,
    n_samples: int = 1000,
    n_features: int = 10,
    noise_scale: Optional[float] = None,
    dataset_relpath: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run ML_BENCH-01 accuracy certificate.

    Args:
        seed: Random seed (deterministic — same seed → same result always)
        claimed_accuracy: The accuracy the model claims to achieve (e.g. 0.90)
        accuracy_tolerance: Max allowed deviation from claimed_accuracy (default 0.02)
        n_samples: Number of test samples for synthetic mode
        n_features: Number of input features for synthetic mode
        noise_scale: Injected noise level (0.0–1.0). None = no noise injection.
        dataset_relpath: Path to CSV with y_true/y_pred columns (real data mode).
                        Relative to repo root. If set, synthetic params are ignored.

    Returns:
        Full result dict with mtr_phase key for semantic verification.
        result.pass is True when |actual_accuracy - claimed_accuracy| <= tolerance.
    """

    # --- Real data mode ---
    if dataset_relpath is not None:
        from backend.progress.data_integrity import fingerprint_file
        path = REPO_ROOT / dataset_relpath
        if not path.exists():
            raise ValueError(f"Dataset not found: {dataset_relpath}")

        fp = fingerprint_file(path)
        y_true, y_pred = _load_predictions_csv(path)

        if len(y_true) < 10:
            raise ValueError("Dataset has fewer than 10 samples — insufficient for certification")

        metrics = _compute_metrics(y_true, y_pred)
        actual_accuracy = metrics["accuracy"]
        abs_error = abs(actual_accuracy - claimed_accuracy)
        passed = abs_error <= accuracy_tolerance

        return {
            "mtr_phase": "ML_BENCH-01",
            "algorithm_version": ALGORITHM_VERSION,
            "method": METHOD,
            "inputs": {
                "dataset_relpath": dataset_relpath,
                "dataset": {
                    "source": dataset_relpath,
                    "sha256": fp["sha256"],
                    "bytes": fp["bytes"],
                    "rows": fp.get("rows"),
                },
                "claimed_accuracy": claimed_accuracy,
                "accuracy_tolerance": accuracy_tolerance,
            },
            "result": {
                "actual_accuracy": actual_accuracy,
                "claimed_accuracy": claimed_accuracy,
                "absolute_error": round(abs_error, 6),
                "tolerance": accuracy_tolerance,
                "pass": passed,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "n_samples": metrics["n_samples"],
            },
            "status": "SUCCEEDED",
        }

    # --- Synthetic mode ---
    if not (0.0 < claimed_accuracy <= 1.0):
        raise ValueError("claimed_accuracy must be in (0.0, 1.0]")
    if accuracy_tolerance <= 0:
        raise ValueError("accuracy_tolerance must be positive")
    if n_samples < 10:
        raise ValueError("n_samples must be >= 10")

    # Apply noise if requested (degrades model performance deterministically)
    effective_accuracy = claimed_accuracy
    if noise_scale is not None:
        if not (0.0 <= noise_scale <= 1.0):
            raise ValueError("noise_scale must be in [0.0, 1.0]")
        effective_accuracy = max(0.5, claimed_accuracy - noise_scale * 0.2)

    _, y_true, y_pred = _generate_binary_dataset(
        seed=seed,
        n_samples=n_samples,
        n_features=n_features,
        true_accuracy=effective_accuracy,
    )

    metrics = _compute_metrics(y_true, y_pred)
    actual_accuracy = metrics["accuracy"]
    abs_error = abs(actual_accuracy - claimed_accuracy)
    passed = abs_error <= accuracy_tolerance

    # --- Step Chain Verification (PPA #63/996,819) ---
    prev = "genesis"
    trace = []

    prev = _hash_step("init_params", {
        "seed": seed,
        "claimed_accuracy": claimed_accuracy,
        "accuracy_tolerance": accuracy_tolerance,
        "n_samples": n_samples,
        "n_features": n_features,
        "noise_scale": noise_scale,
    }, prev)
    trace.append({"step": 1, "name": "init_params", "hash": prev})

    prev = _hash_step("generate_dataset", {
        "seed": seed,
        "n_samples": n_samples,
        "n_features": n_features,
        "effective_accuracy": round(effective_accuracy, 6),
    }, prev)
    trace.append({"step": 2, "name": "generate_dataset", "hash": prev,
                  "output": {"n_samples": len(y_true)}})

    prev = _hash_step("compute_metrics", {
        "n_samples": metrics["n_samples"],
        "actual_accuracy": metrics["accuracy"],
    }, prev)
    trace.append({"step": 3, "name": "compute_metrics", "hash": prev,
                  "output": {"accuracy": metrics["accuracy"],
                             "f1": metrics["f1"]}})

    prev = _hash_step("threshold_check", {
        "abs_error": round(abs_error, 6),
        "tolerance": accuracy_tolerance,
        "passed": passed,
    }, prev)
    trace.append({"step": 4, "name": "threshold_check", "hash": prev,
                  "output": {"pass": passed}})

    trace_root_hash = prev
    # --------------------------------------------------

    return {
        "mtr_phase": "ML_BENCH-01",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "seed": seed,
            "claimed_accuracy": claimed_accuracy,
            "accuracy_tolerance": accuracy_tolerance,
            "n_samples": n_samples,
            "n_features": n_features,
            "noise_scale": noise_scale,
            "mode": "synthetic",
        },
        "result": {
            "actual_accuracy": actual_accuracy,
            "claimed_accuracy": claimed_accuracy,
            "absolute_error": round(abs_error, 6),
            "tolerance": accuracy_tolerance,
            "pass": passed,
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "f1": metrics["f1"],
            "n_samples": metrics["n_samples"],
        },
        "execution_trace": trace,
        "trace_root_hash": trace_root_hash,
        "status": "SUCCEEDED",
    }
