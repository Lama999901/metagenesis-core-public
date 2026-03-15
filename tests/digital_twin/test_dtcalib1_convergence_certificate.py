"""DT-CALIB-LOOP-01 Tests — Calibration Convergence Certificate."""
import pytest
from backend.progress.dtcalib1_convergence_certificate import run_certificate, JOB_KIND


class TestJobKind:
    def test_job_kind(self):
        assert JOB_KIND == "dtcalib1_convergence_certificate"


class TestRunCertificate:
    def test_converging_passes(self):
        r = run_certificate(seed=42, n_iterations=15, initial_drift_pct=20.0,
                            convergence_rate=0.5, convergence_threshold=5.0, noise_scale=0.0)
        assert r["result"]["pass"] is True
        assert r["mtr_phase"] == "DT-CALIB-LOOP-01"

    def test_non_converging_fails(self):
        r = run_certificate(seed=42, n_iterations=5, initial_drift_pct=20.0,
                            convergence_rate=0.01, convergence_threshold=0.001)
        assert r["result"]["pass"] is False

    def test_history_length(self):
        r = run_certificate(seed=42, n_iterations=10, initial_drift_pct=20.0,
                            convergence_rate=0.4, convergence_threshold=5.0)
        assert len(r["result"]["calibration_history"]) == 10

    def test_deterministic(self):
        r1 = run_certificate(seed=42, n_iterations=10, initial_drift_pct=20.0)
        r2 = run_certificate(seed=42, n_iterations=10, initial_drift_pct=20.0)
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_step_chain(self):
        r = run_certificate(seed=42, n_iterations=10, initial_drift_pct=20.0,
                            convergence_rate=0.4, convergence_threshold=5.0)
        assert len(r["execution_trace"]) == 4
        assert r["trace_root_hash"] == r["execution_trace"][-1]["hash"]

    def test_anchor_changes_trace(self):
        r1 = run_certificate(seed=42, n_iterations=10, initial_drift_pct=20.0)
        r2 = run_certificate(seed=42, n_iterations=10, initial_drift_pct=20.0, anchor_hash="a" * 64)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_invalid_iterations_raises(self):
        with pytest.raises(ValueError):
            run_certificate(n_iterations=2)

    def test_invalid_convergence_rate_raises(self):
        with pytest.raises(ValueError):
            run_certificate(convergence_rate=1.5)
