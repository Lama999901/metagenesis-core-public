"""Tests for CSV loader functions across backend/progress modules."""
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.progress.mlbench2_regression_certificate import _load_regression_csv
from backend.progress.mlbench3_timeseries_certificate import _load_ts_csv
from backend.progress.mtr4_titanium_calibration import _load_stress_strain_csv as load_mtr4
from backend.progress.mtr5_steel_calibration import _load_stress_strain_csv as load_mtr5


class TestLoadRegressionCsv:
    def test_valid_csv(self, tmp_path):
        f = tmp_path / "reg.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["y_true", "y_pred"])
            w.writerow([1.0, 1.1])
            w.writerow([2.0, 2.2])
            w.writerow([3.0, 2.9])
        y_true, y_pred = _load_regression_csv(f)
        assert len(y_true) == 3
        assert len(y_pred) == 3
        assert y_true[0] == 1.0
        assert y_pred[0] == 1.1

    def test_missing_file(self, tmp_path):
        f = tmp_path / "missing.csv"
        try:
            _load_regression_csv(f)
            assert False, "Should have raised"
        except (FileNotFoundError, OSError):
            pass

    def test_malformed_rows_skipped(self, tmp_path):
        f = tmp_path / "bad.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["y_true", "y_pred"])
            w.writerow([1.0, 1.1])
            w.writerow(["bad", "data"])
            w.writerow([3.0, 2.9])
        y_true, y_pred = _load_regression_csv(f)
        assert len(y_true) == 2


class TestLoadTsCsv:
    def test_valid_csv(self, tmp_path):
        f = tmp_path / "ts.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["y_true", "y_pred"])
            w.writerow([100.0, 101.0])
            w.writerow([200.0, 198.0])
        y_true, y_pred = _load_ts_csv(f)
        assert len(y_true) == 2
        assert len(y_pred) == 2

    def test_empty_csv(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("y_true,y_pred\n")
        y_true, y_pred = _load_ts_csv(f)
        assert len(y_true) == 0


class TestLoadMtr4Csv:
    def test_valid_csv(self, tmp_path):
        f = tmp_path / "mtr4.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["strain", "stress"])
            w.writerow([0.0001, 11400000])
            w.writerow([0.0005, 57000000])
            w.writerow([0.001, 114000000])
        strain, stress = load_mtr4(f, elastic_strain_max=0.002)
        assert len(strain) == 3
        assert len(stress) == 3

    def test_filters_by_strain_max(self, tmp_path):
        f = tmp_path / "mtr4_filter.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["strain", "stress"])
            w.writerow([0.001, 114000000])
            w.writerow([0.01, 1140000000])  # above max
        strain, stress = load_mtr4(f, elastic_strain_max=0.002)
        assert len(strain) == 1

    def test_missing_file(self, tmp_path):
        try:
            load_mtr4(tmp_path / "missing.csv", elastic_strain_max=0.002)
            assert False, "Should have raised"
        except (FileNotFoundError, OSError):
            pass


class TestLoadMtr5Csv:
    def test_valid_csv(self, tmp_path):
        f = tmp_path / "mtr5.csv"
        with open(f, "w", newline="", encoding="utf-8") as fp:
            w = csv.writer(fp)
            w.writerow(["strain", "stress"])
            w.writerow([0.0001, 19300000])
            w.writerow([0.0005, 96500000])
        strain, stress = load_mtr5(f, elastic_strain_max=0.002)
        assert len(strain) == 2
