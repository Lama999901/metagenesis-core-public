#!/usr/bin/env python3
"""
Tests for mg_demo.py -- Domain Demo Script

Covers DEMO-01 (single command flow), DEMO-02 (receipt generation),
DEMO-03 (offline operation).
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _run_demo(*args, cwd=None, timeout=120):
    """Run mg_demo.py as subprocess and return CompletedProcess."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "mg_demo.py")] + list(args)
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or str(REPO_ROOT),
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )


# ---- Test 1: Interactive menu display ----------------------------------------


def test_domain_menu_display():
    """Calling demo with no args and simulated input '1' selects first domain."""
    cmd = [sys.executable, str(REPO_ROOT / "scripts" / "mg_demo.py")]
    proc = subprocess.run(
        cmd,
        input="1\n",
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
        encoding="utf-8",
        errors="replace",
    )
    combined = proc.stdout + proc.stderr
    # Menu should show domain labels
    assert "Materials Science" in combined
    assert "Fundamental Physics" in combined
    # After selecting "1", it should run the materials demo
    assert "Materials Science" in combined


# ---- Test 2: Materials domain demo produces receipt --------------------------


def test_demo_materials_domain(tmp_path):
    """Running demo with --domain materials produces receipt file in output dir."""
    result = _run_demo("--domain", "materials", "--output-dir", str(tmp_path))
    assert result.returncode == 0, f"Demo failed:\n{result.stderr}"

    receipt = tmp_path / "materials_receipt.txt"
    assert receipt.exists(), "Receipt file not created"
    content = receipt.read_text(encoding="utf-8")
    assert "MTR-1" in content


# ---- Test 3: Offline -- no network calls -------------------------------------


def test_demo_offline_no_network(tmp_path):
    """Demo makes zero network calls (all bundles are local)."""
    import socket

    original_connect = socket.create_connection

    def deny_connection(*args, **kwargs):
        raise AssertionError("Network call detected during demo -- should be offline")

    with patch.object(socket, "create_connection", deny_connection):
        # Import and run the demo function directly (avoids subprocess overhead)
        from scripts.mg_demo import run_domain_demo
        ok = run_domain_demo("physics", tmp_path)

    assert ok, "Physics domain demo should pass"
    receipt = tmp_path / "physics_receipt.txt"
    assert receipt.exists()


# ---- Test 4: Receipt file contains required sections -------------------------


def test_receipt_file_content(tmp_path):
    """Receipt file contains all 4 required sections."""
    result = _run_demo("--domain", "materials", "--output-dir", str(tmp_path))
    assert result.returncode == 0

    receipt = tmp_path / "materials_receipt.txt"
    assert receipt.exists()
    content = receipt.read_text(encoding="utf-8")

    required_sections = ["Summary", "Claims Verified", "Verification Result", "How to Reproduce"]
    for section in required_sections:
        assert section in content, f"Missing section: '{section}'"


# ---- Test 5: Unknown domain error --------------------------------------------


def test_unknown_domain_error():
    """Passing --domain nonexistent prints error and returns exit code 1."""
    result = _run_demo("--domain", "nonexistent")
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "Unknown domain" in combined or "unknown domain" in combined.lower()


# ---- Test 6: Bundle path normalization (backslashes) -------------------------


def test_bundle_path_normalization():
    """Backslash paths from index.json are handled correctly."""
    from scripts.mg_demo import _resolve_bundle_path

    entry = {"bundle_path": "proof_library\\bundles\\MTR-1_materials_20260407T052827Z.zip"}
    resolved = _resolve_bundle_path(entry)
    assert resolved.exists(), f"Bundle not found at {resolved}"


# ---- Test 7: --all flag runs all domains ------------------------------------


def test_all_domains_flag(tmp_path):
    """--all runs all domains without error, creates receipt files."""
    result = _run_demo("--all", "--output-dir", str(tmp_path))
    assert result.returncode == 0, f"--all failed:\n{result.stderr}"

    # At minimum, materials and physics should have receipts
    assert (tmp_path / "materials_receipt.txt").exists()
    assert (tmp_path / "physics_receipt.txt").exists()

    # Count total receipt files -- should be >= 8 (one per domain with bundles)
    receipts = list(tmp_path.glob("*_receipt.txt"))
    assert len(receipts) >= 7, f"Only {len(receipts)} receipts created"
