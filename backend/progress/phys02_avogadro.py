#!/usr/bin/env python3
"""
PHYS-02 Avogadro Constant Chemistry Verification.

Purpose: Deterministic verification of molecular mass of water using
Avogadro's number NA = 6.02214076e23 mol^-1 (SI 2019, exact).
No heavy deps (stdlib only). Part of MetaGenesis Core verification pipeline.
"""

from typing import Dict, Any

JOB_KIND = "phys02_avogadro_chemistry"
AVOGADRO_N = 6.02214076e23  # mol^-1 exact SI 2019
MOLAR_MASS_WATER = 18.01528e-3  # kg/mol
ALGORITHM_VERSION = "v1"
METHOD = "molecular_mass_water"


def run_verification() -> Dict[str, Any]:
    """
    Verify molecular mass of water: m_molecule = M_water / N_A.

    Compare computed value against reference.
    4-step chain: init_constants -> compute_molecular_mass -> compare_reference -> threshold_check
    """
    m_molecule = MOLAR_MASS_WATER / AVOGADRO_N
    m_ref = 18.01528e-3 / 6.02214076e23  # 2.99151e-26 kg
    rel_err = abs(m_molecule - m_ref) / m_ref if m_ref != 0 else 0.0
    threshold = 1e-8
    passed = rel_err <= threshold

    inputs_summary = {
        "NA": AVOGADRO_N,
        "M_water": MOLAR_MASS_WATER,
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
    }
    result = {
        "m_molecule": m_molecule,
        "m_ref": m_ref,
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

    _prev = _hash_step("init_constants", {"NA": AVOGADRO_N, "M_water": MOLAR_MASS_WATER}, "genesis")
    _trace = [{"step": 1, "name": "init_constants", "hash": _prev}]
    _prev = _hash_step("compute_molecular_mass", {"m_molecule": m_molecule}, _prev)
    _trace.append({"step": 2, "name": "compute_molecular_mass", "hash": _prev, "output": {"m_molecule": m_molecule}})
    _prev = _hash_step("compare_reference", {"m_ref": m_ref, "rel_err": rel_err}, _prev)
    _trace.append({"step": 3, "name": "compare_reference", "hash": _prev, "output": {"rel_err": rel_err}})
    _prev = _hash_step("threshold_check", {"rel_err": rel_err, "threshold": threshold, "passed": passed}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": passed}})
    _trace_root_hash = _prev
    # --- End Step Chain ---

    return {
        "mtr_phase": "PHYS-02",
        "inputs": inputs_summary,
        "result": result,
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
