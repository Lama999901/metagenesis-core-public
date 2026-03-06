"""
DRIFT-01 Tests — Calibration Anchor & Drift Monitor
Verifies: anchor storage, drift detection, no-drift case,
adversarial drift (just below threshold), correction signal.
"""
import pytest
from backend.progress.drift_monitor import (
    compute_drift,
    run_drift_monitor,
    DEFAULT_DRIFT_THRESHOLD_PCT,
    JOB_KIND,
)


class TestDriftMonitorUnit:

    def test_job_kind_constant(self):
        assert JOB_KIND == "drift_calibration_monitor"

    def test_no_drift_exact_match(self):
        result = compute_drift(70e9, 70e9)
        assert result["drift_pct"] == 0.0
        assert result["drift_detected"] is False
        assert result["correction_required"] is False

    def test_no_drift_within_threshold(self):
        # 3% drift — below 5% threshold
        anchor = 70e9
        current = anchor * 1.03
        result = compute_drift(anchor, current)
        assert result["drift_pct"] < 5.0
        assert result["drift_detected"] is False

    def test_drift_detected_above_threshold(self):
        # 10% drift — above 5% threshold
        anchor = 70e9
        current = anchor * 1.10
        result = compute_drift(anchor, current)
        assert result["drift_pct"] > 5.0
        assert result["drift_detected"] is True
        assert result["correction_required"] is True

    def test_drift_detected_below_anchor(self):
        # Drift can be negative direction too
        anchor = 70e9
        current = anchor * 0.90  # 10% below
        result = compute_drift(anchor, current)
        assert result["drift_detected"] is True

    def test_adversarial_just_below_threshold(self):
        # 4.99% drift — just below threshold, must NOT trigger
        anchor = 100.0
        current = anchor * 1.0499
        result = compute_drift(anchor, current, drift_threshold_pct=5.0)
        assert result["drift_detected"] is False

    def test_adversarial_just_above_threshold(self):
        # 5.01% drift — just above threshold, MUST trigger
        anchor = 100.0
        current = anchor * 1.0501
        result = compute_drift(anchor, current, drift_threshold_pct=5.0)
        assert result["drift_detected"] is True

    def test_custom_threshold(self):
        # 3% drift with 2% threshold — must trigger
        anchor = 70e9
        current = anchor * 1.03
        result = compute_drift(anchor, current, drift_threshold_pct=2.0)
        assert result["drift_detected"] is True

    def test_zero_anchor_raises(self):
        with pytest.raises(ValueError, match="non-zero"):
            compute_drift(0.0, 70e9)

    def test_result_keys_present(self):
        result = compute_drift(70e9, 70e9)
        for key in ("anchor_value", "current_value", "drift_pct",
                    "drift_threshold_pct", "drift_detected", "correction_required"):
            assert key in result


class TestRunDriftMonitor:

    def test_full_run_no_drift(self):
        result = run_drift_monitor(
            anchor_value=70e9,
            current_value=70e9,
            anchor_claim_id="MTR-1",
            anchor_units="Pa",
        )
        assert result["mtr_phase"] == "DRIFT-01"
        assert result["status"] == "SUCCEEDED"
        assert result["result"]["drift_detected"] is False

    def test_full_run_drift_detected(self):
        result = run_drift_monitor(
            anchor_value=70e9,
            current_value=80e9,  # ~14% drift
        )
        assert result["result"]["drift_detected"] is True
        assert result["result"]["correction_required"] is True

    def test_mtr_phase_key_present(self):
        """Semantic verifier requires mtr_phase key."""
        result = run_drift_monitor(anchor_value=70e9, current_value=70e9)
        assert "mtr_phase" in result

    def test_inputs_recorded(self):
        result = run_drift_monitor(
            anchor_value=70e9,
            current_value=73e9,
            anchor_claim_id="MTR-1",
            anchor_units="Pa",
            drift_threshold_pct=5.0,
        )
        assert result["inputs"]["anchor_claim_id"] == "MTR-1"
        assert result["inputs"]["anchor_units"] == "Pa"
        assert result["inputs"]["drift_threshold_pct"] == 5.0

    def test_invalid_anchor_raises(self):
        with pytest.raises((ValueError, TypeError)):
            run_drift_monitor(anchor_value="bad", current_value=70e9)

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            run_drift_monitor(
                anchor_value=70e9,
                current_value=70e9,
                drift_threshold_pct=-1.0,
            )
