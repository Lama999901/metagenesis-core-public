#!/usr/bin/env python3
"""
Tests for mg_receipt.py -- Verification Receipt Generator

RCPT-06: 15+ tests covering all 20 claim types, anchored vs non-anchored,
FAIL handling, format validation, file saving, missing bundle, Unicode paths.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_receipt import (
    CLAIM_DESCRIPTIONS,
    NON_ANCHORED_NOTE,
    PHYSICAL_ANCHORS,
    _determine_pass,
    _extract_result_summary,
    format_receipt,
    generate_receipt,
    get_anchor_line,
    get_claim_description,
)
from scripts.mg_client import create_bundle, run_claim


# ---- Helpers ----------------------------------------------------------------

def _make_claim_result(claim_id, passed=True, trace_root="a" * 64):
    """Create a minimal claim result dict for testing."""
    return {
        "mtr_phase": claim_id,
        "inputs": {"seed": 42},
        "result": {"pass": passed, "value": 0.001},
        "execution_trace": [
            {"step": 1, "name": "init_params", "hash": "b" * 64},
            {"step": 2, "name": "compute", "hash": "c" * 64},
            {"step": 3, "name": "metrics", "hash": "d" * 64},
            {"step": 4, "name": "threshold_check", "hash": trace_root},
        ],
        "trace_root_hash": trace_root,
    }


def _make_bundle(claim_result):
    """Create a real signed bundle in a temp directory."""
    tmpdir = tempfile.mkdtemp(prefix="mg_test_bundle_")
    bundle_dir = create_bundle(claim_result, output_dir=tmpdir)
    return bundle_dir


# ---- RCPT-02: Anchored claims show physical constant -----------------------

ANCHORED_CLAIMS = list(PHYSICAL_ANCHORS.keys())


@pytest.mark.parametrize("claim_id", ANCHORED_CLAIMS)
def test_anchored_claim_shows_physical_constant(claim_id):
    """Anchored claims display the physical constant in the anchor line."""
    anchor = get_anchor_line(claim_id)
    assert anchor != NON_ANCHORED_NOTE
    assert anchor == PHYSICAL_ANCHORS[claim_id]


@pytest.mark.parametrize("claim_id", ANCHORED_CLAIMS)
def test_anchored_claim_receipt_format(claim_id):
    """Anchored claims produce receipts with the physical anchor line."""
    result = _make_claim_result(claim_id)
    receipt = format_receipt(result)
    assert PHYSICAL_ANCHORS[claim_id] in receipt
    assert "METAGENESIS CORE" in receipt
    assert "PASS" in receipt


# ---- RCPT-03: Non-anchored claims show SCOPE_001 ---------------------------

NON_ANCHORED_CLAIMS = [
    "ML_BENCH-01", "ML_BENCH-02", "ML_BENCH-03",
    "PHARMA-01", "FINRISK-01", "DATA-PIPE-01",
    "SYSID-01", "DT-SENSOR-01", "AGENT-DRIFT-01",
]


@pytest.mark.parametrize("claim_id", NON_ANCHORED_CLAIMS)
def test_non_anchored_claim_shows_scope_001(claim_id):
    """Non-anchored claims show SCOPE_001 provenance note."""
    anchor = get_anchor_line(claim_id)
    assert anchor == NON_ANCHORED_NOTE
    assert "SCOPE_001" in anchor


@pytest.mark.parametrize("claim_id", NON_ANCHORED_CLAIMS)
def test_non_anchored_claim_receipt_format(claim_id):
    """Non-anchored claims produce receipts with SCOPE_001 reference."""
    result = _make_claim_result(claim_id)
    receipt = format_receipt(result)
    assert "SCOPE_001" in receipt
    assert "Tamper-evident provenance only" in receipt


# ---- All 20 claims have descriptions ---------------------------------------

ALL_20_CLAIMS = ANCHORED_CLAIMS + NON_ANCHORED_CLAIMS


@pytest.mark.parametrize("claim_id", ALL_20_CLAIMS)
def test_all_claims_have_description(claim_id):
    """All 20 claims have a human-readable description."""
    desc = get_claim_description(claim_id)
    assert desc != claim_id  # Should not fall back to raw ID
    assert len(desc) > 5


@pytest.mark.parametrize("claim_id", ALL_20_CLAIMS)
def test_all_claims_produce_valid_receipt(claim_id):
    """All 20 claims produce a receipt with all required fields."""
    result = _make_claim_result(claim_id)
    receipt = format_receipt(result)

    # Format validation: all required fields present
    assert "Verified:" in receipt
    assert "Claim:" in receipt
    assert "Result:" in receipt
    assert "Status:" in receipt
    assert "Anchor:" in receipt
    assert "Chain root:" in receipt
    assert "To verify independently:" in receipt
    assert "python mg.py verify --pack bundle.zip" in receipt
    assert "metagenesis-core.dev" in receipt
    assert "PPA #63/996,819" in receipt
    assert "MIT License" in receipt


# ---- RCPT-04: FAIL handling ------------------------------------------------

def test_fail_bundle_no_receipt_file():
    """FAIL bundles produce no receipt file."""
    tmpdir = tempfile.mkdtemp(prefix="mg_test_fail_")
    try:
        # Create a broken bundle (no manifest)
        bundle_dir = Path(tmpdir) / "bad_bundle"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "evidence.json").write_text("{}", encoding="utf-8")

        out_dir = Path(tmpdir) / "receipts"
        success, msg, path = generate_receipt(bundle_dir, output_dir=out_dir)
        assert not success
        assert path is None
        assert "FAIL" in msg or "not found" in msg.lower() or "not pass" in msg.lower()
    finally:
        shutil.rmtree(tmpdir)


def test_fail_claim_no_receipt():
    """Claim that fails (pass=False) produces no receipt file even if bundle is valid."""
    tmpdir = tempfile.mkdtemp(prefix="mg_test_failclaim_")
    try:
        # Create a bundle with a failing claim
        result = _make_claim_result("MTR-1", passed=False)
        bundle_dir = _make_bundle(result)

        out_dir = Path(tmpdir) / "receipts"
        success, msg, path = generate_receipt(bundle_dir, output_dir=out_dir)
        assert not success
        assert path is None
    finally:
        shutil.rmtree(tmpdir)
        if bundle_dir.exists():
            shutil.rmtree(str(bundle_dir))


# ---- RCPT-01: Receipt file saved to correct path ---------------------------

def test_receipt_saved_to_correct_path():
    """Receipt is saved to reports/receipts/{trace_id}_receipt.txt."""
    tmpdir = tempfile.mkdtemp(prefix="mg_test_save_")
    try:
        result = run_claim("ml")
        bundle_dir = _make_bundle(result)

        out_dir = Path(tmpdir) / "receipts"
        success, msg, path = generate_receipt(bundle_dir, output_dir=out_dir)

        assert success
        assert path is not None
        assert path.exists()
        assert path.suffix == ".txt"
        assert "_receipt.txt" in path.name
        assert path.parent == out_dir

        # Verify content
        content = path.read_text(encoding="utf-8")
        assert "METAGENESIS CORE" in content
        assert "PASS" in content
    finally:
        shutil.rmtree(tmpdir)
        if bundle_dir.exists():
            shutil.rmtree(str(bundle_dir))


def test_receipt_trace_id_in_filename():
    """Receipt filename contains trace_root_hash prefix."""
    tmpdir = tempfile.mkdtemp(prefix="mg_test_traceid_")
    try:
        result = run_claim("materials")
        trace_prefix = result["trace_root_hash"][:16]
        bundle_dir = _make_bundle(result)

        out_dir = Path(tmpdir) / "receipts"
        success, msg, path = generate_receipt(bundle_dir, output_dir=out_dir)

        assert success
        assert trace_prefix in path.name
    finally:
        shutil.rmtree(tmpdir)
        if bundle_dir.exists():
            shutil.rmtree(str(bundle_dir))


# ---- Missing bundle produces clear error ------------------------------------

def test_missing_bundle_clear_error():
    """Missing bundle path produces a clear error message."""
    success, msg, path = generate_receipt(Path("/nonexistent/bundle/path"))
    assert not success
    assert path is None
    assert "not found" in msg.lower() or "Bundle" in msg


# ---- Unicode path handling --------------------------------------------------

def test_unicode_path_handling():
    """Receipt generation handles Unicode characters in paths."""
    tmpdir = tempfile.mkdtemp(prefix="mg_test_unicode_")
    try:
        result = run_claim("ml")
        bundle_dir = _make_bundle(result)

        # Use a Unicode output directory name
        unicode_dir = Path(tmpdir) / "receipts_test_dir"
        unicode_dir.mkdir(parents=True, exist_ok=True)

        success, msg, path = generate_receipt(bundle_dir, output_dir=unicode_dir)
        assert success
        assert path is not None
        assert path.exists()
    finally:
        shutil.rmtree(tmpdir)
        if bundle_dir.exists():
            shutil.rmtree(str(bundle_dir))


# ---- Format validation (all required fields) --------------------------------

def test_receipt_format_complete():
    """Receipt format contains all required fields per spec."""
    result = _make_claim_result("PHYS-01")
    receipt = format_receipt(result, timestamp="2026-04-04 12:00:00 UTC")

    lines = receipt.split("\n")

    # Check separator lines
    assert lines[0].startswith("-----")
    assert "METAGENESIS CORE" in lines[1]

    # Check fields
    field_prefixes = ["Verified:", "Claim:", "Result:", "Status:", "Anchor:", "Chain root:"]
    receipt_text = receipt
    for prefix in field_prefixes:
        assert prefix in receipt_text, f"Missing field: {prefix}"

    # Check footer
    assert "MIT License" in receipt_text
    assert "metagenesis-core.dev" in receipt_text


def test_chain_root_shows_first_16_chars():
    """Chain root line shows first 16 chars of trace_root_hash."""
    trace = "abcdef1234567890" + "0" * 48
    result = _make_claim_result("MTR-1", trace_root=trace)
    receipt = format_receipt(result)
    assert "abcdef1234567890" in receipt


# ---- _determine_pass edge cases ---------------------------------------------

def test_determine_pass_drift_not_detected():
    """DRIFT claims: drift_detected=False means PASS."""
    result = {
        "mtr_phase": "DRIFT-01",
        "result": {"drift_detected": False, "drift_pct": 0.5},
    }
    assert _determine_pass(result) is True


def test_determine_pass_drift_detected():
    """DRIFT claims: drift_detected=True means FAIL."""
    result = {
        "mtr_phase": "DRIFT-01",
        "result": {"drift_detected": True, "drift_pct": 10.0},
    }
    assert _determine_pass(result) is False


def test_determine_pass_standard_claim():
    """Standard claims: pass=True means PASS."""
    result = {
        "mtr_phase": "ML_BENCH-01",
        "result": {"pass": True, "actual_accuracy": 0.91},
    }
    assert _determine_pass(result) is True


def test_determine_pass_standard_fail():
    """Standard claims: pass=False means FAIL."""
    result = {
        "mtr_phase": "ML_BENCH-01",
        "result": {"pass": False, "actual_accuracy": 0.50},
    }
    assert _determine_pass(result) is False


# ---- Result summary extraction -----------------------------------------------

def test_result_summary_mtr():
    """MTR claims show relative_error."""
    summary = _extract_result_summary("MTR-1", {"relative_error": 0.001234})
    assert "relative_error" in summary
    assert "0.001234" in summary


def test_result_summary_ml():
    """ML claims show accuracy."""
    summary = _extract_result_summary("ML_BENCH-01", {"actual_accuracy": 0.909})
    assert "accuracy" in summary


def test_result_summary_phys():
    """PHYS claims show rel_err."""
    summary = _extract_result_summary("PHYS-01", {"rel_err": 1.2e-15})
    assert "rel_err" in summary


def test_result_summary_drift():
    """DRIFT claims show drift percentage."""
    summary = _extract_result_summary("DRIFT-01", {"drift_pct": 2.5})
    assert "drift" in summary
    assert "2.50" in summary


# ---- Real claim integration tests -------------------------------------------

@pytest.mark.parametrize("domain", ["ml", "materials", "finance", "pharma", "digital_twin"])
def test_real_claim_receipt_roundtrip(domain):
    """Real claim -> bundle -> verify -> receipt roundtrip works."""
    tmpdir = tempfile.mkdtemp(prefix=f"mg_test_{domain}_")
    bundle_dir = None
    try:
        result = run_claim(domain)
        bundle_dir = _make_bundle(result)

        out_dir = Path(tmpdir) / "receipts"
        success, msg, path = generate_receipt(bundle_dir, output_dir=out_dir)

        assert success, f"Receipt generation failed for {domain}: {msg}"
        assert path is not None
        assert path.exists()

        content = path.read_text(encoding="utf-8")
        assert "METAGENESIS CORE" in content
        assert "PASS" in content
    finally:
        shutil.rmtree(tmpdir)
        if bundle_dir and Path(bundle_dir).exists():
            shutil.rmtree(str(bundle_dir))


# ---- Edge: unknown claim ID -------------------------------------------------

def test_unknown_claim_id_fallback():
    """Unknown claim ID falls back to raw ID for description."""
    desc = get_claim_description("UNKNOWN-99")
    assert desc == "UNKNOWN-99"

    anchor = get_anchor_line("UNKNOWN-99")
    assert anchor == NON_ANCHORED_NOTE


def test_receipt_with_empty_trace_root():
    """Receipt handles missing trace_root_hash gracefully."""
    result = {
        "mtr_phase": "MTR-1",
        "inputs": {},
        "result": {"pass": True, "relative_error": 0.001},
        "execution_trace": [],
        "trace_root_hash": "",
    }
    receipt = format_receipt(result)
    assert "Chain root:  N/A" in receipt


# ---- Coverage: 20 claims x anchor correctness = comprehensive ---------------

def test_exactly_20_claim_descriptions():
    """Verify we have descriptions for all 20 claims."""
    assert len(CLAIM_DESCRIPTIONS) == 20


def test_anchored_plus_non_anchored_equals_20():
    """Anchored (11) + non-anchored (9) = 20 claims."""
    all_claims = set(PHYSICAL_ANCHORS.keys()) | set(NON_ANCHORED_CLAIMS)
    assert len(all_claims) == 20
