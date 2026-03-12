"""
Tests for DT-FEM-01 Digital Twin FEM Verification Certificate.

Coverage:
  - Normal PASS case (low noise)
  - Normal FAIL case (high noise)
  - Adversarial: noise_scale=0.5 → FAIL
  - mtr_phase key present (semantic verification requirement)
  - Determinism: same seed → same result
  - Edge: reference_value=0 → ValueError
  - Edge: rel_err_threshold=0 → ValueError
  - Edge: noise_scale=0 → perfect result, rel_err=0.0
  - Edge: rel_err exactly at threshold → PASS
  - runner dispatch: payload kind routes correctly
"""

import pytest
from backend.progress.dtfem1_displacement_verification import (
    run_certificate,
    compute_rel_err,
    JOB_KIND,
    DEFAULT_REL_ERR_THRESHOLD,
)


# ── Helpers ────────────────────────────────────────────────────────────

def _run(seed=42, reference_value=10.0, rel_err_threshold=0.02,
         noise_scale=0.005, quantity="displacement_mm", units="mm"):
    return run_certificate(
        seed=seed,
        reference_value=reference_value,
        rel_err_threshold=rel_err_threshold,
        noise_scale=noise_scale,
        quantity=quantity,
        units=units,
    )


# ── Structure ──────────────────────────────────────────────────────────

def test_mtr_phase_key_present():
    """Semantic invariant: mtr_phase must be present at top level."""
    result = _run()
    assert result["mtr_phase"] == "DT-FEM-01"


def test_result_keys_present():
    """Required result fields must all be present."""
    r = _run()["result"]
    for key in ["fem_value", "reference_value", "rel_err",
                "rel_err_threshold", "pass", "quantity", "units",
                "method", "algorithm_version"]:
        assert key in r, f"Missing key: {key}"


def test_inputs_keys_present():
    """Required inputs fields must all be present."""
    inp = _run()["inputs"]
    for key in ["seed", "reference_value", "rel_err_threshold",
                "noise_scale", "quantity", "units"]:
        assert key in inp, f"Missing key in inputs: {key}"


# ── Pass / Fail ────────────────────────────────────────────────────────

def test_normal_pass_low_noise():
    """Low noise (0.5%) → rel_err well within 2% threshold → PASS."""
    r = _run(noise_scale=0.005)
    assert r["result"]["pass"] is True
    assert r["result"]["rel_err"] <= 0.02


def test_normal_fail_high_noise():
    """High noise (50%) → rel_err >> 2% threshold → FAIL."""
    r = _run(noise_scale=0.5)
    assert r["result"]["pass"] is False
    assert r["result"]["rel_err"] > 0.02


def test_adversarial_noise_scale_50pct_fails():
    """Adversarial: noise_scale=0.5 proves claim detects bad FEM output."""
    r = run_certificate(seed=99, reference_value=100.0,
                        rel_err_threshold=0.02, noise_scale=0.5)
    assert r["result"]["pass"] is False


def test_zero_noise_perfect_result():
    """noise_scale=0 → fem_value == reference_value → rel_err == 0.0 → PASS."""
    r = _run(noise_scale=0.0)
    assert r["result"]["rel_err"] == 0.0
    assert r["result"]["pass"] is True


# ── Determinism ────────────────────────────────────────────────────────

def test_determinism_same_seed():
    """Same seed must always produce identical result."""
    r1 = _run(seed=7)
    r2 = _run(seed=7)
    assert r1["result"]["fem_value"] == r2["result"]["fem_value"]
    assert r1["result"]["rel_err"] == r2["result"]["rel_err"]


def test_different_seeds_differ():
    """Different seeds should produce different fem_value."""
    r1 = _run(seed=1)
    r2 = _run(seed=2)
    assert r1["result"]["fem_value"] != r2["result"]["fem_value"]


# ── Threshold boundary ─────────────────────────────────────────────────

def test_boundary_exactly_at_threshold_passes():
    """
    Construct fem_value exactly at rel_err_threshold boundary → PASS.
    rel_err = threshold exactly → pass (<=).
    """
    ref = 100.0
    threshold = 0.02
    # fem_value that produces exactly 2% error
    fem_at_boundary = ref * (1 + threshold)
    rel_err = compute_rel_err(fem_at_boundary, ref)
    assert abs(rel_err - threshold) < 1e-10
    # Now verify the compute_rel_err function is correct
    assert rel_err <= threshold


# ── Edge cases ─────────────────────────────────────────────────────────

def test_reference_value_zero_raises():
    """reference_value=0 must raise ValueError."""
    with pytest.raises(ValueError, match="non-zero"):
        run_certificate(seed=42, reference_value=0.0)


def test_rel_err_threshold_zero_raises():
    """rel_err_threshold=0 must raise ValueError."""
    with pytest.raises(ValueError, match="positive"):
        run_certificate(seed=42, reference_value=10.0, rel_err_threshold=0.0)


def test_noise_scale_negative_raises():
    """noise_scale < 0 must raise ValueError."""
    with pytest.raises(ValueError, match="noise_scale"):
        run_certificate(seed=42, reference_value=10.0, noise_scale=-0.1)


def test_custom_quantity_and_units():
    """Custom quantity and units propagate to result."""
    r = run_certificate(seed=42, reference_value=200000.0,
                        quantity="youngs_modulus_MPa", units="MPa")
    assert r["result"]["quantity"] == "youngs_modulus_MPa"
    assert r["result"]["units"] == "MPa"


# ── Runner dispatch ────────────────────────────────────────────────────

def test_job_kind_constant():
    """JOB_KIND must match the runner dispatch key."""
    assert JOB_KIND == "dtfem1_displacement_verification"


def test_runner_dispatches_dtfem1():
    """Runner correctly dispatches DT-FEM-01 job via payload kind."""
    from backend.progress.models import Job, JobStatus, now_iso8601, generate_job_id, generate_trace_id
    from backend.progress.store import JobStore
    from backend.ledger.ledger_store import LedgerStore
    from backend.progress.runner import ProgressRunner

    job_store = JobStore()
    ledger_store = LedgerStore()
    runner = ProgressRunner(job_store, ledger_store)

    job = runner.create_job(payload={
        "kind": "dtfem1_displacement_verification",
        "seed": 42,
        "reference_value": 10.0,
        "rel_err_threshold": 0.02,
        "noise_scale": 0.005,
        "quantity": "displacement_mm",
        "units": "mm",
    })
    completed = runner.run_job(job.job_id)
    assert completed.status == JobStatus.SUCCEEDED
    assert completed.result["mtr_phase"] == "DT-FEM-01"
    assert completed.result["result"]["pass"] is True
