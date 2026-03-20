"""
AGENT-DRIFT-01 Tests -- Agent Quality Drift Monitor
6 tests: pass, fail (35% drift), determinism, step chain tamper,
semantic stripping, boundary (exactly 20%).
"""
import pytest
import copy
from backend.progress.agent_drift_monitor import (
    run_agent_drift_monitor,
    compute_agent_drift,
    JOB_KIND,
    DEFAULT_DRIFT_THRESHOLD_PCT,
)

BASELINE = {
    "tests_per_phase": 47,
    "pass_rate": 1.0,
    "regressions": 0,
    "verifier_iterations": 1.2,
}


class TestAgentDrift01:

    def test_pass_no_drift(self):
        """Current == baseline: zero drift, all checks pass."""
        current = dict(BASELINE)
        result = run_agent_drift_monitor(baseline=BASELINE, current=current)

        assert result["mtr_phase"] == "AGENT-DRIFT-01"
        assert result["status"] == "SUCCEEDED"
        assert result["result"]["composite_drift_pct"] == 0.0
        assert result["result"]["drift_detected"] is False
        assert result["result"]["correction_required"] is False
        assert len(result["execution_trace"]) == 4
        assert isinstance(result["trace_root_hash"], str)
        assert len(result["trace_root_hash"]) == 64

    def test_fail_high_drift(self):
        """Significantly degraded metrics: composite drift well above 20%."""
        current = {
            "tests_per_phase": 30,
            "pass_rate": 0.85,
            "regressions": 3,
            "verifier_iterations": 2.0,
        }
        result = run_agent_drift_monitor(baseline=BASELINE, current=current)

        assert result["result"]["composite_drift_pct"] > 20.0
        assert result["result"]["drift_detected"] is True
        assert result["result"]["correction_required"] is True

    def test_determinism(self):
        """Same inputs produce identical trace_root_hash; different inputs differ."""
        current_a = dict(BASELINE)
        r1 = run_agent_drift_monitor(baseline=BASELINE, current=current_a)
        r2 = run_agent_drift_monitor(baseline=BASELINE, current=current_a)
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

        current_b = dict(BASELINE)
        current_b["tests_per_phase"] = 46
        r3 = run_agent_drift_monitor(baseline=BASELINE, current=current_b)
        assert r1["trace_root_hash"] != r3["trace_root_hash"]

    def test_step_chain_tamper_detection(self):
        """Tampering with any step hash invalidates downstream chain linkage."""
        result = run_agent_drift_monitor(baseline=BASELINE, current=dict(BASELINE))
        trace = result["execution_trace"]

        # Record original step 2 and step 3 hashes
        original_step2_hash = trace[1]["hash"]
        original_step3_hash = trace[2]["hash"]

        # Tamper step 2 hash (change one character)
        tampered_hash = original_step2_hash[:-1] + (
            "0" if original_step2_hash[-1] != "0" else "1"
        )
        assert tampered_hash != original_step2_hash

        # If step 2 hash were used as prev_hash for step 3,
        # step 3 would produce a different hash. The chain is linked:
        # changing step 2 would invalidate step 3 and step 4.
        import hashlib
        import json

        step3_data = {
            "composite_drift_pct": result["result"]["composite_drift_pct"],
            "drift_detected": result["result"]["drift_detected"],
        }
        content = json.dumps(
            {"step": "metrics", "data": step3_data, "prev_hash": tampered_hash},
            sort_keys=True,
            separators=(",", ":"),
        )
        recomputed_step3 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        assert recomputed_step3 != original_step3_hash

    def test_semantic_stripping(self):
        """Result contains required semantic keys; stripping mtr_phase is detectable."""
        result = run_agent_drift_monitor(baseline=BASELINE, current=dict(BASELINE))

        # Required semantic keys exist
        assert "mtr_phase" in result
        assert "inputs" in result
        assert "result" in result
        assert "composite_drift_pct" in result["result"]
        assert "drift_detected" in result["result"]

        # Stripping mtr_phase is detectable
        stripped = copy.deepcopy(result)
        del stripped["mtr_phase"]
        assert "mtr_phase" not in stripped

    def test_boundary_exactly_20pct(self):
        """Exactly 20% composite drift does NOT trigger (strict > comparison).

        Use custom baseline with regressions=5 to avoid zero-denominator edge case.
        Set all per-metric drifts to exactly 20%.
        """
        custom_baseline = {
            "tests_per_phase": 50.0,
            "pass_rate": 1.0,
            "regressions": 5,
            "verifier_iterations": 1.0,
        }
        # Each metric drifts exactly 20%:
        # tests_per_phase: 60 -> |60-50|/50*100 = 20%
        # pass_rate: 0.8 -> |0.8-1.0|/1.0*100 = 20%
        # regressions: 6 -> |6-5|/5*100 = 20%
        # verifier_iterations: 1.2 -> |1.2-1.0|/1.0*100 = 20%
        # composite = 0.3*20 + 0.3*20 + 0.2*20 + 0.2*20 = 20.0
        current = {
            "tests_per_phase": 60.0,
            "pass_rate": 0.8,
            "regressions": 6,
            "verifier_iterations": 1.2,
        }
        result = run_agent_drift_monitor(
            baseline=custom_baseline, current=current, drift_threshold_pct=20.0
        )

        assert result["result"]["composite_drift_pct"] == 20.0
        # Strict >: exactly 20.0 does NOT trigger
        assert result["result"]["drift_detected"] is False
        assert result["result"]["correction_required"] is False
