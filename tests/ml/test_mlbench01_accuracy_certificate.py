"""
ML_BENCH-01 Tests — ML Accuracy Certificate
Verifies: accuracy threshold pass/fail, determinism, adversarial noise,
semantic keys, invalid inputs, and boundary conditions.
"""
import pytest
from backend.progress.mlbench1_accuracy_certificate import (
    run_certificate,
    _compute_metrics,
    _generate_binary_dataset,
    JOB_KIND,
    ALGORITHM_VERSION,
)


class TestJobKindConstant:

    def test_job_kind(self):
        assert JOB_KIND == "mlbench1_accuracy_certificate"

    def test_algorithm_version(self):
        assert ALGORITHM_VERSION == "v1"


class TestComputeMetrics:

    def test_perfect_accuracy(self):
        y_true = [0, 1, 0, 1, 1, 0]
        y_pred = [0, 1, 0, 1, 1, 0]
        m = _compute_metrics(y_true, y_pred)
        assert m["accuracy"] == 1.0
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["f1"] == 1.0

    def test_zero_accuracy(self):
        y_true = [0, 0, 1, 1]
        y_pred = [1, 1, 0, 0]
        m = _compute_metrics(y_true, y_pred)
        assert m["accuracy"] == 0.0

    def test_partial_accuracy(self):
        # 3 out of 4 correct → accuracy = 0.75
        y_true = [0, 1, 0, 1]
        y_pred = [0, 1, 0, 0]
        m = _compute_metrics(y_true, y_pred)
        assert abs(m["accuracy"] - 0.75) < 1e-9

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            _compute_metrics([], [])

    def test_required_keys(self):
        y_true = [0, 1]
        y_pred = [0, 1]
        m = _compute_metrics(y_true, y_pred)
        for k in ("accuracy", "precision", "recall", "f1", "n_samples"):
            assert k in m


class TestGenerateBinaryDataset:

    def test_deterministic(self):
        _, y1, p1 = _generate_binary_dataset(42, 100, 5, 0.9)
        _, y2, p2 = _generate_binary_dataset(42, 100, 5, 0.9)
        assert y1 == y2
        assert p1 == p2

    def test_different_seeds_different_data(self):
        _, _, p1 = _generate_binary_dataset(42, 100, 5, 0.9)
        _, _, p2 = _generate_binary_dataset(99, 100, 5, 0.9)
        assert p1 != p2

    def test_approximate_accuracy(self):
        _, y_true, y_pred = _generate_binary_dataset(42, 5000, 10, 0.90)
        m = _compute_metrics(y_true, y_pred)
        # Should be within 3% of target
        assert abs(m["accuracy"] - 0.90) < 0.03


class TestRunCertificate:

    def test_pass_within_tolerance(self):
        """Claimed 90%, generated ~90% → PASS."""
        result = run_certificate(
            seed=42,
            claimed_accuracy=0.90,
            accuracy_tolerance=0.02,
            n_samples=2000,
        )
        assert result["result"]["pass"] is True
        assert result["mtr_phase"] == "ML_BENCH-01"
        assert result["status"] == "SUCCEEDED"

    def test_fail_outside_tolerance(self):
        """
        Adversarial: claim 99% accuracy but inject heavy noise
        so actual accuracy ~70% → FAIL.
        """
        result = run_certificate(
            seed=42,
            claimed_accuracy=0.99,
            accuracy_tolerance=0.02,
            n_samples=2000,
            noise_scale=1.0,   # maximum noise — degrades performance
        )
        assert result["result"]["pass"] is False

    def test_deterministic_same_seed(self):
        r1 = run_certificate(seed=42, claimed_accuracy=0.85, n_samples=500)
        r2 = run_certificate(seed=42, claimed_accuracy=0.85, n_samples=500)
        assert r1["result"]["actual_accuracy"] == r2["result"]["actual_accuracy"]

    def test_different_seeds_different_results(self):
        r1 = run_certificate(seed=42, claimed_accuracy=0.85, n_samples=500)
        r2 = run_certificate(seed=99, claimed_accuracy=0.85, n_samples=500)
        assert r1["result"]["actual_accuracy"] != r2["result"]["actual_accuracy"]

    def test_mtr_phase_key_present(self):
        """Semantic verifier requires mtr_phase key at top level."""
        result = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=200)
        assert "mtr_phase" in result

    def test_inputs_recorded(self):
        result = run_certificate(
            seed=7,
            claimed_accuracy=0.88,
            accuracy_tolerance=0.03,
            n_samples=300,
        )
        assert result["inputs"]["claimed_accuracy"] == 0.88
        assert result["inputs"]["accuracy_tolerance"] == 0.03
        assert result["inputs"]["seed"] == 7

    def test_result_keys_complete(self):
        result = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=200)
        for k in ("actual_accuracy", "claimed_accuracy", "absolute_error",
                  "tolerance", "pass", "precision", "recall", "f1", "n_samples"):
            assert k in result["result"]

    def test_invalid_claimed_accuracy_raises(self):
        with pytest.raises(ValueError):
            run_certificate(seed=42, claimed_accuracy=1.5)

    def test_invalid_tolerance_raises(self):
        with pytest.raises(ValueError):
            run_certificate(seed=42, claimed_accuracy=0.9, accuracy_tolerance=-0.01)

    def test_too_few_samples_raises(self):
        with pytest.raises(ValueError):
            run_certificate(seed=42, claimed_accuracy=0.9, n_samples=5)

    def test_adversarial_noise_zero(self):
        """noise_scale=0.0 should not degrade accuracy."""
        result_no_noise = run_certificate(seed=42, claimed_accuracy=0.90,
                                          n_samples=2000, noise_scale=None)
        result_zero_noise = run_certificate(seed=42, claimed_accuracy=0.90,
                                            n_samples=2000, noise_scale=0.0)
        # noise_scale=0 → no degradation → same result as no noise
        assert result_no_noise["result"]["actual_accuracy"] == \
               result_zero_noise["result"]["actual_accuracy"]

    def test_boundary_tolerance_exact(self):
        """
        If absolute_error == tolerance exactly (floating point),
        the certificate should PASS (<=, not <).
        """
        result = run_certificate(seed=42, claimed_accuracy=0.90,
                                 accuracy_tolerance=0.02, n_samples=2000)
        err = result["result"]["absolute_error"]
        tol = result["result"]["tolerance"]
        # The pass flag must be consistent with the reported error
        assert result["result"]["pass"] == (err <= tol)


class TestExecutionTraceChain:
    """Step Chain Verification tests — PPA #63/996,819."""

    def test_trace_present_in_result(self):
        """execution_trace and trace_root_hash must be in synthetic mode result."""
        result = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        assert "execution_trace" in result
        assert "trace_root_hash" in result

    def test_trace_has_four_steps(self):
        """Trace must have exactly 4 steps in order."""
        result = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        trace = result["execution_trace"]
        assert len(trace) == 4
        names = [s["name"] for s in trace]
        assert names == [
            "init_params", "generate_dataset",
            "compute_metrics", "threshold_check"
        ]

    def test_trace_hashes_are_valid_hex64(self):
        """Every step hash must be a 64-char lowercase hex string."""
        result = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        for step in result["execution_trace"]:
            h = step["hash"]
            assert isinstance(h, str)
            assert len(h) == 64
            assert all(c in "0123456789abcdef" for c in h)

    def test_trace_is_deterministic(self):
        """Same seed → identical trace every time."""
        r1 = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        r2 = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        assert r1["execution_trace"] == r2["execution_trace"]
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_trace_changes_with_different_seed(self):
        """Different seed → different trace root hash."""
        r1 = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        r2 = run_certificate(seed=99, claimed_accuracy=0.90, n_samples=500)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_trace_root_hash_equals_last_step_hash(self):
        """trace_root_hash must equal the hash of the final step."""
        result = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=500)
        last_hash = result["execution_trace"][-1]["hash"]
        assert result["trace_root_hash"] == last_hash
