"""PHARMA-01 Tests — ADMET Prediction Certificate."""
import pytest
from backend.progress.pharma1_admet_certificate import run_certificate, JOB_KIND, ADMET_BOUNDS


class TestJobKind:
    def test_job_kind(self):
        assert JOB_KIND == "pharma1_admet_certificate"


class TestAdmetBounds:
    def test_all_properties_present(self):
        for p in ["solubility", "permeability", "toxicity_score", "binding_affinity", "bioavailability_score"]:
            assert p in ADMET_BOUNDS


class TestRunCertificate:
    def test_solubility_pass(self):
        r = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5, tolerance=1.0)
        assert r["result"]["pass"] is True
        assert r["mtr_phase"] == "PHARMA-01"

    def test_all_five_properties(self):
        for prop, vals in ADMET_BOUNDS.items():
            mid = (vals["min"] + vals["max"]) / 2
            r = run_certificate(seed=42, property_name=prop, claimed_value=mid, tolerance=2.0)
            assert r["mtr_phase"] == "PHARMA-01"

    def test_fail_tight_tolerance(self):
        r = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5,
                            tolerance=0.001, noise_scale=1.0)
        assert r["result"]["pass"] is False

    def test_invalid_property_raises(self):
        with pytest.raises(ValueError):
            run_certificate(property_name="unknown_prop")

    def test_deterministic(self):
        r1 = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5)
        r2 = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5)
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_step_chain_4_steps(self):
        r = run_certificate(seed=42, property_name="binding_affinity", claimed_value=7.0, tolerance=1.0)
        assert len(r["execution_trace"]) == 4
        assert r["trace_root_hash"] == r["execution_trace"][-1]["hash"]

    def test_anchor_changes_trace(self):
        r1 = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5)
        r2 = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5, anchor_hash="a" * 64)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_regulatory_note_present(self):
        r = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5)
        assert "FDA" in r["inputs"].get("regulatory_note", "")

    def test_unit_in_result(self):
        r = run_certificate(seed=42, property_name="solubility", claimed_value=-3.5)
        assert r["result"]["unit"] == "logS"
