"""Tests for scripts/run_single_claim.py -- single-claim dispatcher."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import scripts.run_single_claim as mod


# ---- _to_relpath tests -------------------------------------------------------


def test_to_relpath_absolute_inside_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    abs_path = str(tmp_path / "data" / "input.json")
    result = mod._to_relpath(abs_path)
    assert result == "data/input.json"


def test_to_relpath_absolute_outside_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path / "repo")
    outside = str(tmp_path / "other" / "file.csv")
    result = mod._to_relpath(outside)
    # Should return the original path with forward slashes
    assert "\\" not in result


def test_to_relpath_relative(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    result = mod._to_relpath("data/input.json")
    assert "/" in result or result == "data/input.json"


# ---- _load_json tests --------------------------------------------------------


def test_load_json_valid(tmp_path):
    f = tmp_path / "test.json"
    f.write_text('{"key": "value", "num": 42}', encoding="utf-8")
    result = mod._load_json(str(f))
    assert result == {"key": "value", "num": 42}


def test_load_json_invalid(tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        mod._load_json(str(f))


# ---- _write_output tests -----------------------------------------------------


def test_write_output_creates_file(tmp_path):
    out = tmp_path / "sub" / "dir" / "output.json"
    data = {"mtr_phase": "MTR-1", "result": {"pass": True}}
    mod._write_output(data, str(out))
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["mtr_phase"] == "MTR-1"


def test_write_output_valid_json(tmp_path):
    out = tmp_path / "result.json"
    mod._write_output({"a": 1}, str(out))
    content = out.read_text(encoding="utf-8")
    assert content.endswith("\n")
    parsed = json.loads(content)
    assert parsed["a"] == 1


# ---- dispatch tests ----------------------------------------------------------


def test_dispatch_mtr1(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    fake_result = {"mtr_phase": "MTR-1", "result": {"relative_error": 0.001}}
    with mock.patch(
        "backend.progress.mtr1_calibration.run_calibration",
        return_value=fake_result,
    ) as m:
        result = mod.dispatch("MTR-1", str(input_file))
        assert result["mtr_phase"] == "MTR-1"
        m.assert_called_once()
        call_kw = m.call_args
        assert call_kw[1]["seed"] == 42
        assert call_kw[1]["E_true"] == 70e9


def test_dispatch_phys02(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    fake_result = {"mtr_phase": "PHYS-02", "result": {"rel_err": 0.0}}
    with mock.patch(
        "backend.progress.phys02_avogadro.run_verification",
        return_value=fake_result,
    ) as m:
        result = mod.dispatch("PHYS-02", str(input_file))
        assert result["mtr_phase"] == "PHYS-02"
        m.assert_called_once_with()


def test_dispatch_ml_bench01(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    fake_result = {"mtr_phase": "ML_BENCH-01", "result": {"actual_accuracy": 0.94}}
    with mock.patch(
        "backend.progress.mlbench1_accuracy_certificate.run_certificate",
        return_value=fake_result,
    ) as m:
        result = mod.dispatch("ML_BENCH-01", str(input_file))
        assert result["mtr_phase"] == "ML_BENCH-01"
        m.assert_called_once()


def test_dispatch_finrisk01(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    input_file = tmp_path / "input.json"
    input_file.write_text('{"seed": 42}', encoding="utf-8")
    fake_result = {"mtr_phase": "FINRISK-01", "result": {"computed_var": 0.05}}
    with mock.patch(
        "backend.progress.finrisk1_var_certificate.run_certificate",
        return_value=fake_result,
    ) as m:
        result = mod.dispatch("FINRISK-01", str(input_file))
        assert result["mtr_phase"] == "FINRISK-01"
        m.assert_called_once()


def test_dispatch_unknown_claim():
    with pytest.raises(ValueError, match="Unknown CLAIM_ID"):
        mod.dispatch("FAKE-99", "input.json")


# ---- main tests --------------------------------------------------------------


def test_main_success(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    output_file = tmp_path / "out.json"

    monkeypatch.setattr(
        sys, "argv",
        ["run_single_claim.py", "MTR-1", str(input_file), str(output_file)],
    )
    fake_result = {"mtr_phase": "MTR-1", "result": {"relative_error": 0.001}}
    with mock.patch.object(mod, "dispatch", return_value=fake_result):
        # main calls sys.exit only on failure
        ret = mod.main()
        assert ret is None  # success path does not return explicitly


def test_main_bad_argc(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["run_single_claim.py", "MTR-1"])
    with pytest.raises(SystemExit) as exc_info:
        mod.main()
    assert exc_info.value.code == 1


def test_main_dispatch_exception(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")
    output_file = tmp_path / "out.json"

    monkeypatch.setattr(
        sys, "argv",
        ["run_single_claim.py", "FAKE-99", str(input_file), str(output_file)],
    )
    with pytest.raises(SystemExit) as exc_info:
        mod.main()
    assert exc_info.value.code == 1
