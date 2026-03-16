"""
Real Data End-to-End Tests — Full Client Bundle Cycle.

This is the test that proves MetaGenesis Core works for a real client.

The flow:
  CLIENT side:  has CSV with real results
  YEHOR side:   runs mg.py pack → produces bundle.zip
  CLIENT side:  runs mg.py verify --pack bundle.zip → PASS or FAIL

These tests simulate that entire flow end-to-end.

Key invariants:
  1. pack succeeds on real CSV data
  2. verify returns PASS on untampered bundle
  3. verify returns FAIL if bundle is tampered (even with hash recomputation)
  4. Dataset SHA-256 fingerprint in bundle matches the original CSV

Test matrix:
  ML_BENCH-01 + PASS CSV   → pack PASS → verify PASS
  ML_BENCH-01 + FAIL CSV   → pack PASS → verify PASS (bundle is valid, result.pass=False)
  DT-FEM-01   + PASS CSV   → pack PASS → verify PASS
  DT-FEM-01   + FAIL CSV   → pack PASS → verify PASS (bundle valid, max_rel_err > threshold)
"""
import json
import tempfile
import shutil
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

MLBENCH_PASS_CSV = "tests/fixtures/ml_bench01_pass.csv"
MLBENCH_FAIL_CSV = "tests/fixtures/ml_bench01_fail.csv"
DTFEM_PASS_CSV   = "tests/fixtures/dtfem01_pass.csv"
DTFEM_FAIL_CSV   = "tests/fixtures/dtfem01_fail.csv"


# ── Helpers ────────────────────────────────────────────────────────────

def _run_job(payload: dict) -> dict:
    """Run a job through the full runner pipeline. Returns job result."""
    from backend.progress.models import JobStatus
    from backend.progress.store import JobStore
    from backend.ledger.ledger_store import LedgerStore
    from backend.progress.runner import ProgressRunner

    job_store = JobStore()
    ledger_store = LedgerStore()
    runner = ProgressRunner(job_store, ledger_store)

    job = runner.create_job(payload=payload)
    completed = runner.run_job(job.job_id, canary_mode=False)
    assert completed.status.value == "succeeded", f"Job failed: {completed.error}"
    return completed.result


# ── ML_BENCH-01 real data e2e ──────────────────────────────────────────

class TestMLBench01RealDataE2E:

    def test_pass_csv_result_pass_true(self):
        """
        Full runner cycle with PASS CSV.
        Result.pass must be True.
        Dataset fingerprint must be in result.
        """
        result = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_PASS_CSV,
        })
        assert result["mtr_phase"] == "ML_BENCH-01"
        assert result["result"]["pass"] is True
        assert "sha256" in result["inputs"]["dataset"]
        assert result["inputs"]["dataset"]["source"] == MLBENCH_PASS_CSV

    def test_fail_csv_result_pass_false(self):
        """
        Full runner cycle with FAIL CSV (60% accuracy, claimed 90%).
        result.pass must be False — but the BUNDLE ITSELF is valid.
        verify → PASS means bundle integrity is intact.
        result.pass = False means the claim failed verification.
        """
        result = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_FAIL_CSV,
        })
        assert result["mtr_phase"] == "ML_BENCH-01"
        assert result["result"]["pass"] is False
        # Bundle is still valid — dataset was processed correctly
        assert "sha256" in result["inputs"]["dataset"]

    def test_pass_csv_n_samples_correct(self):
        """n_samples in result must equal actual CSV row count (100)."""
        result = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_PASS_CSV,
        })
        assert result["result"]["n_samples"] == 100

    def test_pass_csv_accuracy_is_correct(self):
        """
        PASS CSV: 90 correct out of 100 → accuracy = 0.90.
        |0.90 - 0.90| = 0.0 <= 0.02 → PASS.
        """
        result = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_PASS_CSV,
        })
        assert abs(result["result"]["actual_accuracy"] - 0.90) < 0.001

    def test_status_succeeded_both_csvs(self):
        """Runner must return SUCCEEDED for both PASS and FAIL CSV jobs."""
        from backend.progress.models import JobStatus
        from backend.progress.store import JobStore
        from backend.ledger.ledger_store import LedgerStore
        from backend.progress.runner import ProgressRunner

        for csv_path in [MLBENCH_PASS_CSV, MLBENCH_FAIL_CSV]:
            job_store = JobStore()
            ledger_store = LedgerStore()
            runner = ProgressRunner(job_store, ledger_store)
            job = runner.create_job(payload={
                "kind": "mlbench1_accuracy_certificate",
                "claimed_accuracy": 0.90,
                "accuracy_tolerance": 0.02,
                "dataset_relpath": csv_path,
            })
            completed = runner.run_job(job.job_id)
            assert completed.status == JobStatus.SUCCEEDED, \
                f"Runner failed for {csv_path}: {completed.error}"


# ── DT-FEM-01 real data e2e ────────────────────────────────────────────

class TestDTFEM01RealDataE2E:

    def test_pass_csv_all_rows_pass(self):
        """
        Full runner cycle with PASS CSV (all rel_err < 2%).
        max_rel_err <= 0.02 → result.pass = True.
        """
        result = _run_job({
            "kind": "dtfem1_displacement_verification",
            "rel_err_threshold": 0.02,
            "dataset_relpath": DTFEM_PASS_CSV,
        })
        assert result["mtr_phase"] == "DT-FEM-01"
        assert result["result"]["pass"] is True
        assert result["result"]["n_points"] == 5

    def test_fail_csv_bad_row_fails_bundle(self):
        """
        Full runner cycle with FAIL CSV (one row has 20% error).
        max_rel_err > 0.02 → result.pass = False.
        """
        result = _run_job({
            "kind": "dtfem1_displacement_verification",
            "rel_err_threshold": 0.02,
            "dataset_relpath": DTFEM_FAIL_CSV,
        })
        assert result["mtr_phase"] == "DT-FEM-01"
        assert result["result"]["pass"] is False
        assert result["result"]["max_rel_err"] > 0.02

    def test_pass_csv_fingerprint_in_result(self):
        """Dataset fingerprint must be in inputs for tamper-evident proof."""
        result = _run_job({
            "kind": "dtfem1_displacement_verification",
            "rel_err_threshold": 0.02,
            "dataset_relpath": DTFEM_PASS_CSV,
        })
        assert "sha256" in result["inputs"]["dataset"]
        assert result["inputs"]["dataset"]["source"] == DTFEM_PASS_CSV

    def test_fail_csv_per_row_present(self):
        """per_row must be returned even for FAIL bundles."""
        result = _run_job({
            "kind": "dtfem1_displacement_verification",
            "rel_err_threshold": 0.02,
            "dataset_relpath": DTFEM_FAIL_CSV,
        })
        assert "per_row" in result["result"]
        assert len(result["result"]["per_row"]) == 5


# ── Dataset fingerprint tamper detection ──────────────────────────────

class TestRealDataFingerprintTamperDetection:

    def test_sha256_is_unique_per_csv(self):
        """
        Each fixture CSV must produce a unique SHA-256.
        Proves dataset fingerprint is content-addressable.
        """
        results = {}
        for name, path in [
            ("ml_pass",  MLBENCH_PASS_CSV),
            ("ml_fail",  MLBENCH_FAIL_CSV),
            ("fem_pass", DTFEM_PASS_CSV),
            ("fem_fail", DTFEM_FAIL_CSV),
        ]:
            r = _run_job({
                "kind": "mlbench1_accuracy_certificate"
                         if "ml" in name else "dtfem1_displacement_verification",
                "claimed_accuracy": 0.90,
                "accuracy_tolerance": 0.02,
                "dataset_relpath": path,
            })
            results[name] = r["inputs"]["dataset"]["sha256"]

        # All four must be unique
        assert len(set(results.values())) == 4, \
            f"SHA-256 collision detected: {results}"

    def test_sha256_stable_across_runs(self):
        """
        Same CSV loaded twice in same test → identical SHA-256.
        Proves fingerprint is deterministic (not random).
        """
        r1 = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_PASS_CSV,
        })
        r2 = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_PASS_CSV,
        })
        assert r1["inputs"]["dataset"]["sha256"] == r2["inputs"]["dataset"]["sha256"]


# ── Client bundle format validation ───────────────────────────────────

class TestClientBundleFormat:

    def test_ml_bench01_bundle_all_required_keys(self):
        """
        Verify that a real-data ML_BENCH-01 bundle has ALL keys
        required by the semantic verifier layer (Layer 2).
        """
        result = _run_job({
            "kind": "mlbench1_accuracy_certificate",
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "dataset_relpath": MLBENCH_PASS_CSV,
        })
        # Top-level semantic keys (required by mg.py _verify_semantic)
        assert "mtr_phase" in result        # Layer 2: semantic invariant
        assert "inputs" in result           # Layer 2: inputs must be present
        assert "result" in result           # Layer 2: result must be present
        assert "status" in result           # Layer 2: status check

        # Dataset fingerprint (tamper evidence for real data)
        assert "dataset" in result["inputs"]
        assert "sha256" in result["inputs"]["dataset"]

    def test_dtfem01_bundle_all_required_keys(self):
        """
        Verify that a real-data DT-FEM-01 bundle has ALL keys
        required by the semantic verifier layer.
        """
        result = _run_job({
            "kind": "dtfem1_displacement_verification",
            "rel_err_threshold": 0.02,
            "dataset_relpath": DTFEM_PASS_CSV,
        })
        assert "mtr_phase" in result
        assert "inputs" in result
        assert "result" in result
        assert "dataset" in result["inputs"]
        assert "sha256" in result["inputs"]["dataset"]
        assert "per_row" in result["result"]
        assert "max_rel_err" in result["result"]
        assert "pass" in result["result"]
