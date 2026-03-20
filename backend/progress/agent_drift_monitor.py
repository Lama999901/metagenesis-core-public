#!/usr/bin/env python3
"""
AGENT-DRIFT-01 Agent Quality Drift Monitor.

Purpose: Monitors AI agent quality drift by comparing current agent metrics
(tests_per_phase, pass_rate, regressions, verifier_iterations) against a
verified baseline. Composite drift beyond threshold signals correction is
required.

This is the first claim where AI agents monitor their own quality through
the same verification protocol they extend.

No numpy. No external deps. Stdlib only.
"""

from typing import Dict, Any, Optional

JOB_KIND = "agent_drift_monitor"
ALGORITHM_VERSION = "v1"
METHOD = "weighted_composite_drift"

# Default threshold: 20% composite drift triggers detection
DEFAULT_DRIFT_THRESHOLD_PCT = 20.0

# Default baseline from verified agent performance
DEFAULT_BASELINE = {
    "tests_per_phase": 47,
    "pass_rate": 1.0,
    "regressions": 0,
    "verifier_iterations": 1.2,
}

# Default weights for composite drift calculation
DEFAULT_WEIGHTS = {
    "tests_per_phase": 0.3,
    "pass_rate": 0.3,
    "regressions": 0.2,
    "verifier_iterations": 0.2,
}

REQUIRED_KEYS = {"tests_per_phase", "pass_rate", "regressions", "verifier_iterations"}


def compute_agent_drift(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    drift_threshold_pct: float = DEFAULT_DRIFT_THRESHOLD_PCT,
) -> Dict[str, Any]:
    """
    Compute composite agent quality drift across 4 metrics.

    Args:
        baseline: Verified baseline metrics dict.
        current: Current agent metrics dict.
        weights: Per-metric weights (must sum to ~1.0). Defaults to DEFAULT_WEIGHTS.
        drift_threshold_pct: Threshold in percent for drift detection.

    Returns:
        dict with baseline, current, weights, per_metric_drift,
        composite_drift_pct, drift_threshold_pct, drift_detected,
        correction_required.
    """
    weights_used = dict(weights) if weights is not None else dict(DEFAULT_WEIGHTS)

    per_metric_drift = {}
    for key in REQUIRED_KEYS:
        b_val = float(baseline[key])
        c_val = float(current[key])
        # For regressions with baseline=0: denominator becomes 1
        # (each regression = 100% drift unit)
        denominator = max(abs(b_val), 1e-9)
        drift_pct = abs(c_val - b_val) / denominator * 100.0
        per_metric_drift[key] = round(drift_pct, 6)

    composite_drift_pct = sum(
        weights_used[key] * per_metric_drift[key] for key in REQUIRED_KEYS
    )
    composite_drift_pct = round(composite_drift_pct, 6)

    drift_detected = composite_drift_pct > drift_threshold_pct

    return {
        "baseline": baseline,
        "current": current,
        "weights": weights_used,
        "per_metric_drift": per_metric_drift,
        "composite_drift_pct": composite_drift_pct,
        "drift_threshold_pct": drift_threshold_pct,
        "drift_detected": drift_detected,
        "correction_required": drift_detected,
    }


def run_agent_drift_monitor(
    baseline: Dict[str, Any],
    current: Dict[str, Any],
    weights: Optional[Dict[str, float]] = None,
    drift_threshold_pct: float = DEFAULT_DRIFT_THRESHOLD_PCT,
) -> Dict[str, Any]:
    """
    Run AGENT-DRIFT-01 agent quality drift monitoring job.

    Args:
        baseline: Verified baseline metrics (tests_per_phase, pass_rate,
                  regressions, verifier_iterations).
        current: Current agent metrics (same keys).
        weights: Per-metric weights for composite drift. Defaults to
                 DEFAULT_WEIGHTS.
        drift_threshold_pct: Detection threshold in percent (default 20.0).

    Returns:
        Full result dict with mtr_phase='AGENT-DRIFT-01', 4-step execution
        trace, and trace_root_hash.
    """
    # Validate inputs
    if not isinstance(baseline, dict):
        raise ValueError("baseline must be a dict")
    if not isinstance(current, dict):
        raise ValueError("current must be a dict")
    missing_b = REQUIRED_KEYS - set(baseline.keys())
    if missing_b:
        raise ValueError(f"baseline missing keys: {missing_b}")
    missing_c = REQUIRED_KEYS - set(current.keys())
    if missing_c:
        raise ValueError(f"current missing keys: {missing_c}")
    if drift_threshold_pct <= 0:
        raise ValueError("drift_threshold_pct must be positive")

    weights_used = dict(weights) if weights is not None else dict(DEFAULT_WEIGHTS)

    drift_result = compute_agent_drift(
        baseline=baseline,
        current=current,
        weights=weights_used,
        drift_threshold_pct=float(drift_threshold_pct),
    )

    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data,
                           "prev_hash": prev_hash},
                          sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _prev = _hash_step("init_params", {
        "baseline": baseline,
        "current": current,
        "drift_threshold_pct": float(drift_threshold_pct),
    }, "genesis")
    _trace = [{"step": 1, "name": "init_params", "hash": _prev}]

    _prev = _hash_step("compute", {
        "composite_drift_pct": drift_result["composite_drift_pct"],
        "per_metric_drift": drift_result["per_metric_drift"],
    }, _prev)
    _trace.append({"step": 2, "name": "compute", "hash": _prev})

    _prev = _hash_step("metrics", {
        "composite_drift_pct": drift_result["composite_drift_pct"],
        "drift_detected": drift_result["drift_detected"],
    }, _prev)
    _trace.append({"step": 3, "name": "metrics", "hash": _prev})

    _passed = not drift_result["drift_detected"]
    _prev = _hash_step("threshold_check", {
        "passed": _passed,
        "threshold": float(drift_threshold_pct),
    }, _prev)
    _trace.append({"step": 4, "name": "threshold_check",
                   "hash": _prev, "output": {"pass": _passed}})
    trace_root_hash = _prev
    # --- End Step Chain ---

    return {
        "mtr_phase": "AGENT-DRIFT-01",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "baseline": baseline,
            "current": current,
            "weights": weights_used,
            "drift_threshold_pct": float(drift_threshold_pct),
        },
        "result": drift_result,
        "status": "SUCCEEDED",
        "execution_trace": _trace,
        "trace_root_hash": trace_root_hash,
    }
