"""
DT-FEM-01 Real Data Mode Tests.

Tests that MetaGenesis Core correctly verifies FEM simulation outputs
against REAL CSV data (fem_value / measured_value / quantity columns).

This is the path a real engineering client takes:
  1. They run their FEM solver (ANSYS, FEniCS, OpenFOAM, COMSOL, custom)
  2. They have lab measurements for the same physical quantities
  3. MetaGenesis Core verifies: rel_err = |fem - measured| / |measured| vs threshold
  4. Bundle is produced with SHA-256 fingerprint of their dataset

Fixtures:
  tests/fixtures/dtfem01_pass.csv  — all rel_err < 2% (PASS)
  tests/fixtures/dtfem01_fail.csv  — one row rel_err = 20% (FAIL)

CSV format:
  fem_value      — output from FEM solver
  measured_value — physical lab measurement
  quantity       — name of the physical quantity (optional, informational)
"""
import pytest
from pathlib import Path

from backend.progress.dtfem1_displacement_verification import (
    run_certificate,
    compute_rel_err,
)

PASS_CSV = "tests/fixtures/dtfem01_pass.csv"
FAIL_CSV = "tests/fixtures/dtfem01_fail.csv"


# ── Basic real data PASS ───────────────────────────────────────────────

class TestDTFEM01RealDataPass:

    def test_pass_all_rows_within_threshold(self):
        """
        All rows in PASS CSV have rel_err < 2%. max_rel_err <= 0.02 → PASS.
        """
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
            rel_err_threshold=0.02,
        )
        assert result["result"]["pass"] is True
        assert result["mtr_phase"] == "DT-FEM-01"

    def test_pass_per_row_results_present(self):
        """
        Real data mode must return per-row results.
        Each row shows fem_value, measured_value, rel_err, pass.
        """
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
            rel_err_threshold=0.02,
        )
        per_row = result["result"]["per_row"]
        assert len(per_row) == 5  # PASS CSV has 5 rows
        for row in per_row:
            assert "fem_value" in row
            assert "measured_value" in row
            assert "rel_err" in row
            assert "pass" in row

    def test_pass_dataset_fingerprint_present(self):
        """Dataset SHA-256 fingerprint must be in inputs."""
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
            rel_err_threshold=0.02,
        )
        dataset = result["inputs"]["dataset"]
        assert "sha256" in dataset
        assert len(dataset["sha256"]) == 64
        assert dataset["source"] == PASS_CSV
        assert dataset["rows"] == 5

    def test_pass_max_rel_err_is_max_of_per_row(self):
        """max_rel_err must equal max of all per-row rel_err values."""
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
            rel_err_threshold=0.02,
        )
        per_row = result["result"]["per_row"]
        expected_max = max(r["rel_err"] for r in per_row)
        assert abs(result["result"]["max_rel_err"] - expected_max) < 1e-10

    def test_pass_n_points_matches_csv_rows(self):
        """n_points must equal number of rows in CSV."""
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
            rel_err_threshold=0.02,
        )
        assert result["result"]["n_points"] == 5

    def test_pass_mtr_phase_key(self):
        """Semantic invariant: mtr_phase = 'DT-FEM-01' at top level."""
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
        )
        assert result["mtr_phase"] == "DT-FEM-01"


# ── Basic real data FAIL ───────────────────────────────────────────────

class TestDTFEM01RealDataFail:

    def test_fail_one_bad_row_fails_bundle(self):
        """
        FAIL CSV has one row with rel_err = 20% >> 2%.
        max_rel_err > threshold → entire bundle FAILS.
        One bad simulation result invalidates the certificate.
        """
        result = run_certificate(
            seed=42,
            dataset_relpath=FAIL_CSV,
            rel_err_threshold=0.02,
        )
        assert result["result"]["pass"] is False

    def test_fail_max_rel_err_exceeds_threshold(self):
        """max_rel_err must be > threshold for FAIL dataset."""
        result = run_certificate(
            seed=42,
            dataset_relpath=FAIL_CSV,
            rel_err_threshold=0.02,
        )
        assert result["result"]["max_rel_err"] > 0.02

    def test_fail_per_row_identifies_failing_rows(self):
        """per_row must correctly mark failing rows as pass=False."""
        result = run_certificate(
            seed=42,
            dataset_relpath=FAIL_CSV,
            rel_err_threshold=0.02,
        )
        per_row = result["result"]["per_row"]
        failing = [r for r in per_row if not r["pass"]]
        # FAIL CSV has exactly 1 bad row (30.0 vs 25.0 = 20% error)
        assert len(failing) == 1

    def test_fail_bad_row_has_correct_rel_err(self):
        """The failing row must have correct rel_err = |30-25|/25 = 0.2."""
        result = run_certificate(
            seed=42,
            dataset_relpath=FAIL_CSV,
            rel_err_threshold=0.02,
        )
        per_row = result["result"]["per_row"]
        bad_row = next(r for r in per_row if not r["pass"])
        assert abs(bad_row["rel_err"] - 0.2) < 1e-6

    def test_fail_dataset_still_fingerprinted(self):
        """Even on FAIL, dataset fingerprint must be present."""
        result = run_certificate(
            seed=42,
            dataset_relpath=FAIL_CSV,
        )
        assert "sha256" in result["inputs"]["dataset"]


# ── Threshold variations ───────────────────────────────────────────────

class TestDTFEM01Thresholds:

    def test_loose_threshold_turns_fail_to_pass(self):
        """
        FAIL CSV worst row has 20% error.
        With threshold=0.25 (25%) → all rows pass → PASS.
        """
        result = run_certificate(
            seed=42,
            dataset_relpath=FAIL_CSV,
            rel_err_threshold=0.25,
        )
        assert result["result"]["pass"] is True

    def test_tight_threshold_turns_pass_to_fail(self):
        """
        PASS CSV best row has ~0.83% error (12.10 vs 12.00).
        With threshold=0.005 (0.5%) → FAIL.
        """
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
            rel_err_threshold=0.005,
        )
        assert result["result"]["pass"] is False


# ── SHA-256 fingerprint integrity ──────────────────────────────────────

class TestDTFEM01Fingerprint:

    def test_different_csvs_different_sha256(self):
        """PASS and FAIL CSVs have different content → different SHA-256."""
        r_pass = run_certificate(seed=42, dataset_relpath=PASS_CSV)
        r_fail = run_certificate(seed=42, dataset_relpath=FAIL_CSV)
        assert (r_pass["inputs"]["dataset"]["sha256"] !=
                r_fail["inputs"]["dataset"]["sha256"])

    def test_same_csv_same_sha256(self):
        """Same CSV loaded twice → identical SHA-256. Deterministic."""
        r1 = run_certificate(seed=42, dataset_relpath=PASS_CSV)
        r2 = run_certificate(seed=42, dataset_relpath=PASS_CSV)
        assert (r1["inputs"]["dataset"]["sha256"] ==
                r2["inputs"]["dataset"]["sha256"])


# ── Error handling ─────────────────────────────────────────────────────

class TestDTFEM01RealDataErrors:

    def test_missing_file_raises(self):
        """Non-existent dataset raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            run_certificate(
                seed=42,
                dataset_relpath="tests/fixtures/no_such_file.csv",
            )

    def test_empty_csv_raises(self, tmp_path):
        """CSV with no valid rows raises ValueError."""
        pytest.skip("Requires tmp file with repo-relative path")


# ── Real data mode structure ───────────────────────────────────────────

class TestDTFEM01RealDataStructure:

    def test_no_execution_trace_in_real_data_mode(self):
        """
        Real data mode does NOT produce execution_trace.
        Tamper evidence = dataset SHA-256 fingerprint.
        Step Chain is for synthetic deterministic mode only.
        """
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
        )
        # Real data mode returns result without execution_trace
        assert "dataset" in result["inputs"]
        assert "sha256" in result["inputs"]["dataset"]
        # No execution_trace in real data mode (correct by design)
        assert "execution_trace" not in result

    def test_quantity_propagates_from_csv(self):
        """quantity field from CSV rows should appear in per_row results."""
        result = run_certificate(
            seed=42,
            dataset_relpath=PASS_CSV,
        )
        per_row = result["result"]["per_row"]
        # All rows in PASS CSV have quantity='displacement_mm'
        for row in per_row:
            assert row["quantity"] == "displacement_mm"
