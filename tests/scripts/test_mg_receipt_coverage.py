"""Tests for scripts/mg_receipt.py -- coverage boost."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import scripts.mg_receipt as mod


# ---- get_anchor_line tests ---------------------------------------------------


def test_get_anchor_line_anchored():
    line = mod.get_anchor_line("MTR-1")
    assert "70 GPa" in line
    assert "NIST" in line


def test_get_anchor_line_non_anchored():
    line = mod.get_anchor_line("ML_BENCH-01")
    assert "SCOPE_001" in line


def test_get_anchor_line_phys():
    line = mod.get_anchor_line("PHYS-01")
    assert "SI 2019" in line


# ---- get_claim_description tests ---------------------------------------------


def test_get_claim_description_known():
    desc = mod.get_claim_description("MTR-1")
    assert "aluminum" in desc.lower() or "Young" in desc


def test_get_claim_description_unknown():
    desc = mod.get_claim_description("FAKE-99")
    assert desc == "FAKE-99"


# ---- _extract_result_summary tests -------------------------------------------


def test_extract_relative_error():
    r = mod._extract_result_summary("MTR-1", {"relative_error": 0.001})
    assert "0.001" in r


def test_extract_rel_err():
    r = mod._extract_result_summary("PHYS-01", {"rel_err": 1e-12})
    assert "1" in r and "e" in r.lower()


def test_extract_actual_accuracy():
    r = mod._extract_result_summary("ML_BENCH-01", {"actual_accuracy": 0.94})
    assert "0.94" in r


def test_extract_actual_rmse():
    r = mod._extract_result_summary("ML_BENCH-02", {"actual_rmse": 0.123})
    assert "0.123" in r


def test_extract_actual_mape():
    r = mod._extract_result_summary("ML_BENCH-03", {"actual_mape": 0.005})
    assert "0.005" in r


def test_extract_drift_pct():
    r = mod._extract_result_summary("DRIFT-01", {"drift_pct": 2.5})
    assert "2.50" in r


def test_extract_predicted_value():
    r = mod._extract_result_summary("PHARMA-01", {"predicted_value": 0.85})
    assert "0.85" in r


def test_extract_computed_var():
    r = mod._extract_result_summary("FINRISK-01", {"computed_var": 0.05123})
    assert "0.05" in r


def test_extract_n_readings():
    r = mod._extract_result_summary("DT-SENSOR-01", {"n_readings": 100, "anomaly_count": 3})
    assert "100" in r
    assert "3" in r


def test_extract_composite_drift():
    r = mod._extract_result_summary("AGENT-DRIFT-01", {"composite_drift_pct": 5.0})
    assert "5.00" in r


def test_extract_columns_checked():
    r = mod._extract_result_summary("DATA-PIPE-01", {"columns_checked": 5})
    assert "5" in r


def test_extract_pass_key():
    r = mod._extract_result_summary("UNKNOWN", {"pass": True})
    assert r == "PASS"


def test_extract_pass_key_false():
    r = mod._extract_result_summary("UNKNOWN", {"pass": False})
    assert r == "FAIL"


def test_extract_empty_result():
    r = mod._extract_result_summary("X", {})
    assert "See bundle" in r


def test_extract_non_dict():
    r = mod._extract_result_summary("X", "not a dict")
    assert r == "N/A"


# ---- _determine_pass tests ---------------------------------------------------


def test_determine_pass_with_pass_key():
    assert mod._determine_pass({"result": {"pass": True}}) is True
    assert mod._determine_pass({"result": {"pass": False}}) is False


def test_determine_pass_mtr_with_trace():
    trace = [
        {"step": 1, "name": "init_params", "hash": "a" * 64},
        {"step": 2, "name": "compute", "hash": "b" * 64},
        {"step": 3, "name": "metrics", "hash": "c" * 64},
        {"step": 4, "name": "threshold_check", "hash": "d" * 64,
         "output": {"pass": True}},
    ]
    claim = {"result": {"relative_error": 0.001}, "execution_trace": trace}
    assert mod._determine_pass(claim) is True


def test_determine_pass_mtr_trace_fail():
    trace = [
        {"step": 1, "name": "init_params", "hash": "a" * 64},
        {"step": 2, "name": "compute", "hash": "b" * 64},
        {"step": 3, "name": "metrics", "hash": "c" * 64},
        {"step": 4, "name": "threshold_check", "hash": "d" * 64,
         "output": {"pass": False}},
    ]
    claim = {"result": {"relative_error": 0.5}, "execution_trace": trace}
    assert mod._determine_pass(claim) is False


def test_determine_pass_mtr_no_trace():
    claim = {"result": {"relative_error": 0.001}}
    assert mod._determine_pass(claim) is True


def test_determine_pass_drift_no_drift():
    claim = {"result": {"drift_detected": False}}
    assert mod._determine_pass(claim) is True


def test_determine_pass_drift_detected():
    claim = {"result": {"drift_detected": True}}
    assert mod._determine_pass(claim) is False


def test_determine_pass_data_pipe():
    claim = {"result": {"schema_valid": True, "range_valid": True}}
    assert mod._determine_pass(claim) is True
    claim2 = {"result": {"schema_valid": True, "range_valid": False}}
    assert mod._determine_pass(claim2) is False


def test_determine_pass_dt_sensor():
    claim = {"result": {"all_valid": True}}
    assert mod._determine_pass(claim) is True
    claim2 = {"result": {"all_valid": False}}
    assert mod._determine_pass(claim2) is False


def test_determine_pass_fallback():
    assert mod._determine_pass({"result": {"unknown_key": 42}}) is False


def test_determine_pass_non_dict_result():
    assert mod._determine_pass({"result": "not a dict"}) is False


# ---- format_receipt tests ----------------------------------------------------


def test_format_receipt_basic():
    claim = {
        "mtr_phase": "MTR-1",
        "result": {"relative_error": 0.001},
        "trace_root_hash": "a" * 64,
    }
    receipt = mod.format_receipt(claim, timestamp="2026-04-10 12:00:00 UTC")
    assert "VERIFICATION RECEIPT" in receipt
    assert "MTR-1" in receipt or "aluminum" in receipt
    assert "70 GPa" in receipt or "NIST" in receipt
    assert "aaaaaaaaaaaaaaaa" in receipt  # chain root display


def test_format_receipt_no_trace():
    claim = {
        "mtr_phase": "ML_BENCH-01",
        "result": {"actual_accuracy": 0.94},
        "trace_root_hash": "",
    }
    receipt = mod.format_receipt(claim)
    assert "N/A" in receipt


# ---- generate_receipt tests --------------------------------------------------


def test_generate_receipt_missing_bundle(tmp_path):
    ok, msg, path = mod.generate_receipt(tmp_path / "nonexistent")
    assert ok is False
    assert "not found" in msg


def test_generate_receipt_success(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    evidence = {
        "mtr_phase": "MTR-1",
        "result": {"relative_error": 0.001},
        "execution_trace": [
            {"step": 1, "name": "init_params", "hash": "a" * 64},
            {"step": 2, "name": "compute", "hash": "b" * 64},
            {"step": 3, "name": "metrics", "hash": "c" * 64},
            {"step": 4, "name": "threshold_check", "hash": "d" * 64,
             "output": {"pass": True}},
        ],
        "trace_root_hash": "d" * 64,
    }
    (bundle / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    output_dir = tmp_path / "receipts"

    with mock.patch("scripts.mg_client.verify_bundle", return_value=(True, [])):
        ok, msg, rpath = mod.generate_receipt(bundle, output_dir)
    assert ok is True
    assert rpath is not None
    assert rpath.exists()


def test_generate_receipt_verification_failed(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "evidence.json").write_text("{}", encoding="utf-8")

    with mock.patch(
        "scripts.mg_client.verify_bundle",
        return_value=(False, [("Layer 1", False, "hash mismatch")]),
    ):
        ok, msg, rpath = mod.generate_receipt(bundle)
    assert ok is False
    assert "FAIL" in msg
    assert rpath is None


def test_generate_receipt_claim_did_not_pass(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    evidence = {
        "mtr_phase": "MTR-1",
        "result": {"unknown_field": True},
    }
    (bundle / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    with mock.patch("scripts.mg_client.verify_bundle", return_value=(True, [])):
        ok, msg, rpath = mod.generate_receipt(bundle)
    assert ok is False
    assert "did not pass" in msg


def test_generate_receipt_no_evidence(tmp_path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    with mock.patch("scripts.mg_client.verify_bundle", return_value=(True, [])):
        ok, msg, rpath = mod.generate_receipt(bundle)
    assert ok is False
    assert "evidence.json not found" in msg


# ---- main tests --------------------------------------------------------------


def test_main_success(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    monkeypatch.setattr(
        sys, "argv", ["mg_receipt.py", "--pack", str(bundle)]
    )
    with mock.patch.object(
        mod, "generate_receipt",
        return_value=(True, "receipt text", tmp_path / "receipt.txt"),
    ):
        ret = mod.main()
    assert ret == 0


def test_main_failure(tmp_path, monkeypatch):
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    monkeypatch.setattr(
        sys, "argv", ["mg_receipt.py", "--pack", str(bundle)]
    )
    with mock.patch.object(
        mod, "generate_receipt",
        return_value=(False, "FAIL", None),
    ):
        ret = mod.main()
    assert ret == 1
