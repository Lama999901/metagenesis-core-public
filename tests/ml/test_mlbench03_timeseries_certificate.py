"""ML_BENCH-03 Tests — Time-Series Forecast Certificate."""
import pytest
from backend.progress.mlbench3_timeseries_certificate import run_certificate, JOB_KIND, _compute_mape


class TestJobKind:
    def test_job_kind(self):
        assert JOB_KIND == "mlbench3_timeseries_certificate"


class TestComputeMape:
    def test_zero_error(self):
        assert _compute_mape([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 0.0

    def test_all_zero_raises(self):
        with pytest.raises(ValueError, match="zero"):
            _compute_mape([0.0, 0.0], [1.0, 2.0])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _compute_mape([], [])


class TestRunCertificate:
    def test_pass(self):
        r = run_certificate(seed=42, claimed_mape=0.05, mape_tolerance=0.10, n_steps=200)
        assert r["result"]["pass"] is True
        assert r["mtr_phase"] == "ML_BENCH-03"

    def test_fail(self):
        r = run_certificate(seed=42, claimed_mape=0.001, mape_tolerance=0.001, n_steps=200, noise_scale=50.0)
        assert r["result"]["pass"] is False

    def test_deterministic(self):
        r1 = run_certificate(seed=42, claimed_mape=0.05, n_steps=100)
        r2 = run_certificate(seed=42, claimed_mape=0.05, n_steps=100)
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_step_chain_4_steps(self):
        r = run_certificate(seed=42, claimed_mape=0.05, n_steps=200)
        assert len(r["execution_trace"]) == 4
        assert r["trace_root_hash"] == r["execution_trace"][-1]["hash"]

    def test_anchor_changes_trace(self):
        r1 = run_certificate(seed=42, claimed_mape=0.05, n_steps=100)
        r2 = run_certificate(seed=42, claimed_mape=0.05, n_steps=100, anchor_hash="a" * 64)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_invalid_n_steps_raises(self):
        with pytest.raises(ValueError):
            run_certificate(claimed_mape=0.05, n_steps=5)

    def test_invalid_mape_raises(self):
        with pytest.raises(ValueError):
            run_certificate(claimed_mape=-0.1)
