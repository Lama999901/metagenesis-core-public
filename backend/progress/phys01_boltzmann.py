#!/usr/bin/env python3
"""
PHYS-01 Boltzmann Constant Thermodynamics Verification.

Purpose: Deterministic verification of ideal gas kinetic energy using
the Boltzmann constant kB = 1.380649e-23 J/K (SI 2019, exact).
No heavy deps (stdlib only). Part of MetaGenesis Core verification pipeline.
"""

from typing import Dict, Any

JOB_KIND = "phys01_boltzmann_thermodynamics"
BOLTZMANN_K = 1.380649e-23  # J/K exact SI 2019
ALGORITHM_VERSION = "v1"
METHOD = "ideal_gas_kinetic_energy"


def run_verification(T: float = 300.0) -> Dict[str, Any]:
    """
    Verify ideal gas kinetic energy: E_kin = (3/2) * kB * T.

    Compare computed value against reference at T=300 K.
    4-step chain: init_constants -> compute_energy -> compare_reference -> threshold_check
    """
    E_kin = 1.5 * BOLTZMANN_K * T
    E_ref = 1.5 * 1.380649e-23 * 300.0  # 6.2129205e-21 J
    rel_err = abs(E_kin - E_ref) / E_ref if E_ref != 0 else 0.0
    threshold = 1e-9
    passed = rel_err <= threshold

    inputs_summary = {
        "T": T,
        "kB": BOLTZMANN_K,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
    }
    result = {
        "E_kin": E_kin,
        "E_ref": E_ref,
        "rel_err": rel_err,
        "threshold": threshold,
        "pass": passed,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
    }

    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _prev = _hash_step("init_constants", {"T": T, "kB": BOLTZMANN_K}, "genesis")
    _trace = [{"step": 1, "name": "init_constants", "hash": _prev}]
    _prev = _hash_step("compute_energy", {"E_kin": E_kin}, _prev)
    _trace.append({"step": 2, "name": "compute_energy", "hash": _prev, "output": {"E_kin": E_kin}})
    _prev = _hash_step("compare_reference", {"E_ref": E_ref, "rel_err": rel_err}, _prev)
    _trace.append({"step": 3, "name": "compare_reference", "hash": _prev, "output": {"rel_err": rel_err}})
    _prev = _hash_step("threshold_check", {"rel_err": rel_err, "threshold": threshold, "passed": passed}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": passed}})
    _trace_root_hash = _prev
    # --- End Step Chain ---

    return {
        "mtr_phase": "PHYS-01",
        "inputs": inputs_summary,
        "result": result,
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
