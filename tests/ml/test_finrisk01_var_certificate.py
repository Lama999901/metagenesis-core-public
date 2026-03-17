"""FINRISK-01 Tests — VaR Certificate."""
import pytest
from backend.progress.finrisk1_var_certificate import run_certificate, JOB_KIND


class TestJobKind:
    def test_job_kind(self):
        assert JOB_KIND == "finrisk1_var_certificate"


class TestRunCertificate:
    def test_pass_wide_tolerance(self):
        r = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02, n_obs=1000)
        assert r["mtr_phase"] == "FINRISK-01"
        assert r["status"] == "SUCCEEDED"

    def test_fail_tight_tolerance(self):
        r = run_certificate(seed=42, claimed_var=0.001, var_tolerance=0.0001, n_obs=1000)
        assert r["result"]["pass"] is False

    def test_deterministic(self):
        r1 = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02)
        r2 = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02)
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_step_chain(self):
        r = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02)
        assert len(r["execution_trace"]) == 4
        assert r["trace_root_hash"] == r["execution_trace"][-1]["hash"]

    def test_anchor_changes_trace(self):
        r1 = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02)
        r2 = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02, anchor_hash="a" * 64)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_invalid_confidence_raises(self):
        with pytest.raises(ValueError):
            run_certificate(confidence_level=0.5)

    def test_too_few_obs_raises(self):
        with pytest.raises(ValueError):
            run_certificate(n_obs=50)

    def test_regulatory_note(self):
        r = run_certificate(seed=42, claimed_var=0.02, var_tolerance=0.02)
        assert "Basel" in r["inputs"].get("regulatory_note", "")
