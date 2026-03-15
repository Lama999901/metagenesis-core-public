"""ML_BENCH-02 Tests — Regression Certificate."""
import pytest
from backend.progress.mlbench2_regression_certificate import (
    run_certificate, _compute_regression_metrics, JOB_KIND, ALGORITHM_VERSION,
)


class TestJobKind:
    def test_job_kind(self):
        assert JOB_KIND == "mlbench2_regression_certificate"
    def test_algorithm_version(self):
        assert ALGORITHM_VERSION == "v1"


class TestComputeMetrics:
    def test_perfect_prediction(self):
        y = [1.0, 2.0, 3.0, 4.0]
        m = _compute_regression_metrics(y, y)
        assert m["rmse"] == 0.0
        assert m["mae"] == 0.0
        assert abs(m["r2"] - 1.0) < 1e-9

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            _compute_regression_metrics([], [])

    def test_required_keys(self):
        m = _compute_regression_metrics([1.0, 2.0], [1.1, 2.1])
        for k in ("rmse", "mae", "r2", "n_samples"):
            assert k in m


class TestRunCertificate:
    def test_pass_within_tolerance(self):
        result = run_certificate(seed=42, claimed_rmse=0.10, rmse_tolerance=0.05,
                                  n_samples=1000, noise_scale=0.10)
        assert result["result"]["pass"] is True
        assert result["mtr_phase"] == "ML_BENCH-02"
        assert result["status"] == "SUCCEEDED"

    def test_fail_outside_tolerance(self):
        result = run_certificate(seed=42, claimed_rmse=0.001, rmse_tolerance=0.001,
                                  n_samples=1000, noise_scale=0.50)
        assert result["result"]["pass"] is False

    def test_deterministic(self):
        r1 = run_certificate(seed=42, claimed_rmse=0.10, n_samples=500)
        r2 = run_certificate(seed=42, claimed_rmse=0.10, n_samples=500)
        assert r1["result"]["actual_rmse"] == r2["result"]["actual_rmse"]

    def test_mtr_phase_present(self):
        result = run_certificate(seed=42, claimed_rmse=0.10, n_samples=200)
        assert "mtr_phase" in result

    def test_trace_present(self):
        result = run_certificate(seed=42, claimed_rmse=0.10, n_samples=500)
        assert "execution_trace" in result
        assert "trace_root_hash" in result
        assert len(result["execution_trace"]) == 4

    def test_trace_root_equals_last_step(self):
        result = run_certificate(seed=42, claimed_rmse=0.10, n_samples=500)
        last = result["execution_trace"][-1]["hash"]
        assert result["trace_root_hash"] == last

    def test_anchor_hash_changes_trace(self):
        r1 = run_certificate(seed=42, claimed_rmse=0.10, n_samples=500)
        r2 = run_certificate(seed=42, claimed_rmse=0.10, n_samples=500,
                              anchor_hash="a" * 64, anchor_claim_id="ML_BENCH-01")
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_result_keys_complete(self):
        result = run_certificate(seed=42, claimed_rmse=0.10, n_samples=200)
        for k in ("actual_rmse", "claimed_rmse", "absolute_error", "tolerance",
                  "pass", "mae", "r2", "n_samples"):
            assert k in result["result"]

    def test_invalid_claimed_rmse_raises(self):
        with pytest.raises(ValueError):
            run_certificate(seed=42, claimed_rmse=-0.1)

    def test_too_few_samples_raises(self):
        with pytest.raises(ValueError):
            run_certificate(seed=42, claimed_rmse=0.1, n_samples=5)
