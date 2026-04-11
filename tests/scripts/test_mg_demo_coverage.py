"""Tests for scripts/mg_demo.py -- coverage for helper functions."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_demo import (
    _extract_and_verify,
    _find_bundle_root,
    _print_layer_results,
    _safe_zip_member,
    _short_claim_id,
)


# ---- _safe_zip_member tests -------------------------------------------------


def test_safe_zip_member_normal():
    assert _safe_zip_member("evidence.json") is True


def test_safe_zip_member_nested():
    assert _safe_zip_member("sub/dir/file.txt") is True


def test_safe_zip_member_path_traversal_dotdot():
    assert _safe_zip_member("../etc/passwd") is False


def test_safe_zip_member_dotdot_in_middle():
    assert _safe_zip_member("foo/../bar") is False


def test_safe_zip_member_absolute_unix():
    assert _safe_zip_member("/etc/passwd") is False


def test_safe_zip_member_backslash_start():
    assert _safe_zip_member("\\Windows\\system32") is False


# ---- _short_claim_id tests --------------------------------------------------


def test_short_claim_id_mtr1():
    assert _short_claim_id("MTR-1_materials-20260407T052827Z") == "MTR-1"


def test_short_claim_id_dt_fem():
    assert _short_claim_id("DT-FEM-01_digital_twin-2026") == "DT-FEM-01"


def test_short_claim_id_agent_drift():
    assert _short_claim_id("AGENT-DRIFT-01_agent-2026") == "AGENT-DRIFT-01"


def test_short_claim_id_ml_bench():
    assert _short_claim_id("ML_BENCH-01_ml-2026") == "ML_BENCH-01"


def test_short_claim_id_fallback():
    """Unknown claim ID returns as-is."""
    assert _short_claim_id("UNKNOWN-99_foo") == "UNKNOWN-99_foo"


# ---- _find_bundle_root tests ------------------------------------------------


def test_find_bundle_root_at_root(tmp_path):
    (tmp_path / "pack_manifest.json").write_text("{}", encoding="utf-8")
    assert _find_bundle_root(tmp_path) == tmp_path


def test_find_bundle_root_one_level_deep(tmp_path):
    sub = tmp_path / "bundle_dir"
    sub.mkdir()
    (sub / "pack_manifest.json").write_text("{}", encoding="utf-8")
    assert _find_bundle_root(tmp_path) == sub


def test_find_bundle_root_not_found(tmp_path):
    """Falls back to extract_dir when no manifest found."""
    assert _find_bundle_root(tmp_path) == tmp_path


# ---- _print_layer_results tests ---------------------------------------------


def test_print_layer_results_output(capsys):
    results = [
        ("Layer 1 -- SHA-256 Integrity", True, "All file hashes verified"),
        ("Layer 2 -- Semantic Verification", False, "Missing key"),
    ]
    _print_layer_results(results)
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "FAIL" in captured.out
    assert "Layer 1" in captured.out
    assert "Layer 2" in captured.out


# ---- _extract_and_verify tests ----------------------------------------------


def test_extract_and_verify_bad_zip(tmp_path):
    """Non-ZIP file returns failure."""
    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_text("not a zip", encoding="utf-8")
    passed, results, evidence, tmp_dir = _extract_and_verify(bad_zip)
    assert passed is False
    assert results[0][1] is False  # first result is failure
    assert evidence is None
    assert tmp_dir is None


def test_extract_and_verify_unsafe_member(tmp_path):
    """ZIP with path traversal member is rejected."""
    import zipfile
    zip_path = tmp_path / "malicious.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("../etc/passwd", "root:x:0:0")
    passed, results, evidence, tmp_dir = _extract_and_verify(zip_path)
    assert passed is False
    assert "Unsafe path" in results[0][2] or "Security" in results[0][0]
    assert tmp_dir is None
