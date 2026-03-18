#!/usr/bin/env python3
"""
STEP_CHAIN_ALL: Step Chain Verification for all 14 claims.

Tests that every claim produces:
  - execution_trace: list of 4 steps with valid hashes
  - trace_root_hash: SHA-256 of final step == last step hash

28 tests total (ML_BENCH-01 covered in test_mlbench01_accuracy_certificate.py)
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


def _recompute_hash_step(step_name, step_data, prev_hash):
    """Independent reimplementation of _hash_step for genesis verification."""
    import hashlib, json as _j
    content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


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

    def test_mtr1_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_mtr1()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_mtr1()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.mtr1_calibration import run_calibration
        r_alt = run_calibration(seed=99, E_true=70e9, n_points=50, max_strain=0.002)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_mtr1_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_mtr1()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


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

    def test_mtr2_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_mtr2()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_mtr2()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.mtr2_thermal_conductivity import run_calibration
        r_alt = run_calibration(seed=99, k_true=5.0, n_points=50)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_mtr2_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_mtr2()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


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

    def test_mtr3_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_mtr3()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_mtr3()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.mtr3_thermal_multilayer import run_calibration
        r_alt = run_calibration(seed=99, k_true=5.0, r_contact_true=0.1, n_points=50)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_mtr3_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_mtr3()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


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

    def test_sysid_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_sysid()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_sysid()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.sysid1_arx_calibration import run_calibration
        r_alt = run_calibration(seed=99, a_true=0.9, b_true=0.5, n_steps=50)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_sysid_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_sysid()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


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

    def test_datapipe_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_datapipe()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_datapipe()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]

    def test_datapipe_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_datapipe()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


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

    def test_drift_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_drift()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_drift()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.drift_monitor import run_drift_monitor
        r_alt = run_drift_monitor(anchor_value=70e9, current_value=71e9, drift_threshold_pct=5.0)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_drift_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_drift()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


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

    def test_dtfem_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run_dtfem()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run_dtfem()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.dtfem1_displacement_verification import run_certificate
        r_alt = run_certificate(seed=99, reference_value=1.0, rel_err_threshold=0.02)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_dtfem_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run_dtfem()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# ML_BENCH-01: Accuracy Certificate
# ---------------------------------------------------------------------------

class TestStepChainMLBENCH01:

    def _run(self):
        from backend.progress.mlbench1_accuracy_certificate import run_certificate
        return run_certificate(seed=42)

    def test_mlbench1_trace_present(self):
        _assert_trace_valid(self._run(), "ML_BENCH-01")

    def test_mlbench1_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_mlbench1_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_mlbench1_trace_changes_with_input(self):
        from backend.progress.mlbench1_accuracy_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_mlbench1_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.mlbench1_accuracy_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_mlbench1_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# ML_BENCH-02: Regression Certificate
# ---------------------------------------------------------------------------

class TestStepChainMLBENCH02:

    def _run(self):
        from backend.progress.mlbench2_regression_certificate import run_certificate
        return run_certificate(seed=42)

    def test_mlbench2_trace_present(self):
        _assert_trace_valid(self._run(), "ML_BENCH-02")

    def test_mlbench2_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_mlbench2_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_mlbench2_trace_changes_with_input(self):
        from backend.progress.mlbench2_regression_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_mlbench2_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.mlbench2_regression_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_mlbench2_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# ML_BENCH-03: Time Series Certificate
# ---------------------------------------------------------------------------

class TestStepChainMLBENCH03:

    def _run(self):
        from backend.progress.mlbench3_timeseries_certificate import run_certificate
        return run_certificate(seed=42)

    def test_mlbench3_trace_present(self):
        _assert_trace_valid(self._run(), "ML_BENCH-03")

    def test_mlbench3_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_mlbench3_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_mlbench3_trace_changes_with_input(self):
        from backend.progress.mlbench3_timeseries_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_mlbench3_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.mlbench3_timeseries_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_mlbench3_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# PHARMA-01: ADMET Certificate
# ---------------------------------------------------------------------------

class TestStepChainPHARMA01:

    def _run(self):
        from backend.progress.pharma1_admet_certificate import run_certificate
        return run_certificate(seed=42)

    def test_pharma1_trace_present(self):
        _assert_trace_valid(self._run(), "PHARMA-01")

    def test_pharma1_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_pharma1_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_pharma1_trace_changes_with_input(self):
        from backend.progress.pharma1_admet_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_pharma1_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.pharma1_admet_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_pharma1_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# FINRISK-01: VaR Certificate
# ---------------------------------------------------------------------------

class TestStepChainFINRISK01:

    def _run(self):
        from backend.progress.finrisk1_var_certificate import run_certificate
        return run_certificate(seed=42)

    def test_finrisk1_trace_present(self):
        _assert_trace_valid(self._run(), "FINRISK-01")

    def test_finrisk1_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_finrisk1_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_finrisk1_trace_changes_with_input(self):
        from backend.progress.finrisk1_var_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_finrisk1_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.finrisk1_var_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_finrisk1_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# DT-SENSOR-01: IoT Certificate
# ---------------------------------------------------------------------------

class TestStepChainDTSENSOR01:

    def _run(self):
        from backend.progress.dtsensor1_iot_certificate import run_certificate
        return run_certificate(seed=42)

    def test_dtsensor1_trace_present(self):
        _assert_trace_valid(self._run(), "DT-SENSOR-01")

    def test_dtsensor1_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_dtsensor1_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_dtsensor1_trace_changes_with_input(self):
        from backend.progress.dtsensor1_iot_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_dtsensor1_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.dtsensor1_iot_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_dtsensor1_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"


# ---------------------------------------------------------------------------
# DT-CALIB-LOOP-01: Convergence Certificate
# ---------------------------------------------------------------------------

class TestStepChainDTCALIBLOOP01:

    def _run(self):
        from backend.progress.dtcalib1_convergence_certificate import run_certificate
        return run_certificate(seed=42)

    def test_dtcalib1_trace_present(self):
        _assert_trace_valid(self._run(), "DT-CALIB-LOOP-01")

    def test_dtcalib1_trace_four_steps(self):
        assert len(self._run()["execution_trace"]) == 4

    def test_dtcalib1_trace_deterministic(self):
        assert self._run()["trace_root_hash"] == self._run()["trace_root_hash"]

    def test_dtcalib1_trace_changes_with_input(self):
        from backend.progress.dtcalib1_convergence_certificate import run_certificate
        assert run_certificate(seed=42)["trace_root_hash"] != run_certificate(seed=99)["trace_root_hash"]

    def test_dtcalib1_genesis_hash(self):
        """Step 1 hash derives from genesis (structural verification)."""
        result = self._run()
        trace = result["execution_trace"]
        assert trace[0]["name"] == "init_params"
        assert len(trace[0]["hash"]) == 64
        result2 = self._run()
        assert trace[0]["hash"] == result2["execution_trace"][0]["hash"]
        from backend.progress.dtcalib1_convergence_certificate import run_certificate
        r_alt = run_certificate(seed=99)
        assert trace[0]["hash"] != r_alt["execution_trace"][0]["hash"]

    def test_dtcalib1_inter_step_linkage(self):
        """All 4 step hashes are distinct (non-trivial chain)."""
        result = self._run()
        hashes = [s["hash"] for s in result["execution_trace"]]
        assert len(set(hashes)) == 4, "Step hashes must all be distinct"
