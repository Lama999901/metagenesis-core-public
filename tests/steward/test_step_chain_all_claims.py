#!/usr/bin/env python3
"""
STEP_CHAIN_ALL: Step Chain Verification for all 8 claims.

Tests that every claim produces:
  - execution_trace: list of 4 steps with valid hashes
  - trace_root_hash: SHA-256 of final step == last step hash

28 tests (4 per claim × 7 new claims).
ML_BENCH-01 already covered in test_mlbench01_accuracy_certificate.py
"""
import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_trace_valid(result: dict, claim_id: str) -> None:
    """Assert execution_trace and trace_root_hash are present and valid."""
    domain = result.get("result", {}) if "result" in result else result
    # For claims that wrap result in nested dict
    if "mtr_phase" in result:
        domain = result
    
    trace = domain.get("execution_trace")
    root = domain.get("trace_root_hash")
    
    assert trace is not None, f"{claim_id}: execution_trace missing"
    assert root is not None, f"{claim_id}: trace_root_hash missing"
    assert isinstance(trace, list), f"{claim_id}: execution_trace must be list"
    assert len(trace) == 4, f"{claim_id}: execution_trace must have 4 steps, got {len(trace)}"
    
    # Validate each step hash
    for step in trace:
        h = step.get("hash", "")
        assert isinstance(h, str) and len(h) == 64, \
            f"{claim_id}: step {step.get('step')} hash invalid: {h!r}"
        assert all(c in "0123456789abcdef" for c in h), \
            f"{claim_id}: step {step.get('step')} hash not lowercase hex"
    
    # trace_root_hash == last step hash
    last_hash = trace[-1]["hash"]
    assert root == last_hash, \
        f"{claim_id}: trace_root_hash {root!r} != last step hash {last_hash!r}"


def _get_trace_root(result: dict) -> str:
    """Extract trace_root_hash from result dict."""
    if "trace_root_hash" in result:
        return result["trace_root_hash"]
    raise KeyError("trace_root_hash not found in result")


# ---------------------------------------------------------------------------
# MTR-1: Young's Modulus
# ---------------------------------------------------------------------------

class TestStepChainMTR1:
    from backend.progress.mtr1_calibration import run_calibration as _run

    def _run_mtr1(self):
        from backend.progress.mtr1_calibration import run_calibration
        return run_calibration(seed=42, E_true=70e9, n_points=50, max_strain=0.002)

    def test_mtr1_trace_present(self):
        result = self._run_mtr1()
        _assert_trace_valid(result, "MTR-1")

    def test_mtr1_trace_four_steps(self):
        result = self._run_mtr1()
        names = [s["name"] for s in result["execution_trace"]]
        assert len(names) == 4
        assert names[0] == "init_params"
        assert names[3] == "threshold_check"

    def test_mtr1_trace_deterministic(self):
        r1 = self._run_mtr1()
        r2 = self._run_mtr1()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_mtr1_trace_changes_with_seed(self):
        from backend.progress.mtr1_calibration import run_calibration
        r1 = run_calibration(seed=42, E_true=70e9, n_points=50, max_strain=0.002)
        r2 = run_calibration(seed=99, E_true=70e9, n_points=50, max_strain=0.002)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]


# ---------------------------------------------------------------------------
# MTR-2: Thermal Conductivity
# ---------------------------------------------------------------------------

class TestStepChainMTR2:

    def _run_mtr2(self):
        from backend.progress.mtr2_thermal_conductivity import run_calibration
        return run_calibration(seed=42, k_true=5.0, n_points=50)

    def test_mtr2_trace_present(self):
        result = self._run_mtr2()
        _assert_trace_valid(result, "MTR-2")

    def test_mtr2_trace_four_steps(self):
        result = self._run_mtr2()
        assert len(result["execution_trace"]) == 4

    def test_mtr2_trace_deterministic(self):
        r1 = self._run_mtr2()
        r2 = self._run_mtr2()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_mtr2_trace_changes_with_seed(self):
        from backend.progress.mtr2_thermal_conductivity import run_calibration
        r1 = run_calibration(seed=42, k_true=5.0, n_points=50)
        r2 = run_calibration(seed=99, k_true=5.0, n_points=50)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]


# ---------------------------------------------------------------------------
# MTR-3: Multilayer Contact
# ---------------------------------------------------------------------------

class TestStepChainMTR3:

    def _run_mtr3(self):
        from backend.progress.mtr3_thermal_multilayer import run_calibration
        return run_calibration(seed=42, k_true=5.0, r_contact_true=0.1, n_points=50)

    def test_mtr3_trace_present(self):
        result = self._run_mtr3()
        _assert_trace_valid(result, "MTR-3")

    def test_mtr3_trace_four_steps(self):
        result = self._run_mtr3()
        assert len(result["execution_trace"]) == 4

    def test_mtr3_trace_deterministic(self):
        r1 = self._run_mtr3()
        r2 = self._run_mtr3()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_mtr3_trace_changes_with_seed(self):
        from backend.progress.mtr3_thermal_multilayer import run_calibration
        r1 = run_calibration(seed=42, k_true=5.0, r_contact_true=0.1, n_points=50)
        r2 = run_calibration(seed=99, k_true=5.0, r_contact_true=0.1, n_points=50)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]


# ---------------------------------------------------------------------------
# SYSID-01: ARX Calibration
# ---------------------------------------------------------------------------

class TestStepChainSYSID01:

    def _run_sysid(self):
        from backend.progress.sysid1_arx_calibration import run_calibration
        return run_calibration(seed=42, a_true=0.9, b_true=0.5, n_steps=50)

    def test_sysid_trace_present(self):
        result = self._run_sysid()
        _assert_trace_valid(result, "SYSID-01")

    def test_sysid_trace_four_steps(self):
        result = self._run_sysid()
        assert len(result["execution_trace"]) == 4

    def test_sysid_trace_deterministic(self):
        r1 = self._run_sysid()
        r2 = self._run_sysid()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_sysid_trace_changes_with_seed(self):
        from backend.progress.sysid1_arx_calibration import run_calibration
        r1 = run_calibration(seed=42, a_true=0.9, b_true=0.5, n_steps=50)
        r2 = run_calibration(seed=99, a_true=0.9, b_true=0.5, n_steps=50)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]


# ---------------------------------------------------------------------------
# DATA-PIPE-01: Quality Certificate
# ---------------------------------------------------------------------------

class TestStepChainDATAPIPE01:

    def _run_datapipe(self):
        from backend.progress.datapipe1_quality_certificate import run_certificate
        return run_certificate(
            seed=42,
            dataset_relpath="tests/fixtures/data01/al6061_stress_strain_sample.csv",
        )

    def test_datapipe_trace_present(self):
        result = self._run_datapipe()
        _assert_trace_valid(result, "DATA-PIPE-01")

    def test_datapipe_trace_four_steps(self):
        result = self._run_datapipe()
        assert len(result["execution_trace"]) == 4

    def test_datapipe_trace_deterministic(self):
        r1 = self._run_datapipe()
        r2 = self._run_datapipe()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_datapipe_trace_root_equals_last_step(self):
        result = self._run_datapipe()
        last_hash = result["execution_trace"][-1]["hash"]
        assert result["trace_root_hash"] == last_hash


# ---------------------------------------------------------------------------
# DRIFT-01: Drift Monitor
# ---------------------------------------------------------------------------

class TestStepChainDRIFT01:

    def _run_drift(self):
        from backend.progress.drift_monitor import run_drift_monitor
        return run_drift_monitor(
            anchor_value=70e9,
            current_value=70e9,
            drift_threshold_pct=5.0,
        )

    def test_drift_trace_present(self):
        result = self._run_drift()
        _assert_trace_valid(result, "DRIFT-01")

    def test_drift_trace_four_steps(self):
        result = self._run_drift()
        assert len(result["execution_trace"]) == 4

    def test_drift_trace_deterministic(self):
        r1 = self._run_drift()
        r2 = self._run_drift()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_drift_trace_changes_with_current_value(self):
        from backend.progress.drift_monitor import run_drift_monitor
        r1 = run_drift_monitor(anchor_value=70e9, current_value=70e9, drift_threshold_pct=5.0)
        r2 = run_drift_monitor(anchor_value=70e9, current_value=71e9, drift_threshold_pct=5.0)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]


# ---------------------------------------------------------------------------
# DT-FEM-01: FEM Verification
# ---------------------------------------------------------------------------

class TestStepChainDTFEM01:

    def _run_dtfem(self):
        from backend.progress.dtfem1_displacement_verification import run_certificate
        return run_certificate(seed=42, reference_value=1.0, rel_err_threshold=0.02)

    def test_dtfem_trace_present(self):
        result = self._run_dtfem()
        _assert_trace_valid(result, "DT-FEM-01")

    def test_dtfem_trace_four_steps(self):
        result = self._run_dtfem()
        assert len(result["execution_trace"]) == 4

    def test_dtfem_trace_deterministic(self):
        r1 = self._run_dtfem()
        r2 = self._run_dtfem()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_dtfem_trace_changes_with_seed(self):
        from backend.progress.dtfem1_displacement_verification import run_certificate
        r1 = run_certificate(seed=42, reference_value=1.0, rel_err_threshold=0.02)
        r2 = run_certificate(seed=99, reference_value=1.0, rel_err_threshold=0.02)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]
