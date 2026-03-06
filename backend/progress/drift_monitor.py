#!/usr/bin/env python3
"""
DRIFT-01 Calibration Anchor & Drift Monitor.

Purpose: Stores a verified calibration result as a trusted anchor point.
Compares new calibration results against the anchor.
Drift beyond threshold is a signal for simulation correction.

A verified calibration result (e.g. E=70 GPa from MTR-1) becomes the
anchor. Any future run is compared: drift_pct = |new - anchor| / anchor.
If drift_pct > threshold → drift_detected = True → simulation needs correction.

No numpy. No external deps. Stdlib only.
Legal Authority: Infinity Protocol v2.0
"""

from typing import Dict, Any, Optional

JOB_KIND = "drift_calibration_monitor"
ALGORITHM_VERSION = "v1"
METHOD = "anchor_drift_pct"

# Default threshold: 5% drift triggers detection
DEFAULT_DRIFT_THRESHOLD_PCT = 5.0


def compute_drift(
    anchor_value: float,
    current_value: float,
    drift_threshold_pct: float = DEFAULT_DRIFT_THRESHOLD_PCT,
) -> Dict[str, Any]:
    """
    Compare current_value against anchor_value.
    Returns drift_pct and whether drift exceeds threshold.

    Args:
        anchor_value: Verified trusted calibration result (e.g. E=70e9 Pa)
        current_value: New calibration result to check
        drift_threshold_pct: Drift % that triggers detection (default 5.0)

    Returns:
        dict with keys:
            anchor_value, current_value, drift_pct,
            drift_threshold_pct, drift_detected, correction_required
    """
    if anchor_value == 0.0:
        raise ValueError("anchor_value must be non-zero")
    drift_pct = abs(current_value - anchor_value) / abs(anchor_value) * 100.0
    drift_detected = drift_pct > drift_threshold_pct
    return {
        "anchor_value": anchor_value,
        "current_value": current_value,
        "drift_pct": round(drift_pct, 6),
        "drift_threshold_pct": drift_threshold_pct,
        "drift_detected": drift_detected,
        "correction_required": drift_detected,
    }


def run_drift_monitor(
    anchor_value: float,
    current_value: float,
    anchor_claim_id: str = "MTR-1",
    anchor_units: str = "Pa",
    drift_threshold_pct: float = DEFAULT_DRIFT_THRESHOLD_PCT,
) -> Dict[str, Any]:
    """
    Run DRIFT-01 drift monitoring job.
    This is the main entry point called by runner._execute_job_logic().

    Args:
        anchor_value: Trusted verified calibration result
        current_value: New result to compare against anchor
        anchor_claim_id: Which claim produced the anchor (default MTR-1)
        anchor_units: Physical units of the value (default Pa)
        drift_threshold_pct: Detection threshold in percent (default 5.0)

    Returns:
        Full result dict with mtr_phase key for semantic verification
    """
    if not isinstance(anchor_value, (int, float)):
        raise ValueError("anchor_value must be numeric")
    if not isinstance(current_value, (int, float)):
        raise ValueError("current_value must be numeric")
    if drift_threshold_pct <= 0:
        raise ValueError("drift_threshold_pct must be positive")

    drift_result = compute_drift(
        anchor_value=float(anchor_value),
        current_value=float(current_value),
        drift_threshold_pct=float(drift_threshold_pct),
    )

    return {
        "mtr_phase": "DRIFT-01",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "anchor_claim_id": anchor_claim_id,
            "anchor_value": anchor_value,
            "anchor_units": anchor_units,
            "current_value": current_value,
            "drift_threshold_pct": drift_threshold_pct,
        },
        "result": drift_result,
        "status": "SUCCEEDED",
    }
