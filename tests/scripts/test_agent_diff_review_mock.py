#!/usr/bin/env python3
"""Mock-based coverage tests for scripts/agent_diff_review.py -- 10 tests."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agent_diff_review import (
    get_changed_py_files, extract_structure, review_file
)
import agent_diff_review


# -- get_changed_py_files --------------------------------------------------

def test_get_changed_py_files_returns_py_only():
    with patch.object(agent_diff_review, "run", return_value=("scripts/mg.py\ndocs/README.md\n", 0)):
        result = get_changed_py_files()
    assert result == ["scripts/mg.py"]


def test_get_changed_py_files_empty_output():
    with patch.object(agent_diff_review, "run", return_value=("", 0)):
        result = get_changed_py_files()
    assert result == []


def test_get_changed_py_files_multiple_py():
    with patch.object(agent_diff_review, "run", return_value=("a.py\nb.py\nc.md\n", 0)):
        result = get_changed_py_files()
    assert len(result) == 2


def test_get_changed_py_files_fallback_to_unstaged():
    with patch.object(agent_diff_review, "run", side_effect=[("", 0), ("staged.py", 0)]):
        result = get_changed_py_files()
    assert "staged.py" in result


# -- review_file -----------------------------------------------------------

def test_review_file_nonexistent_returns_empty():
    result = review_file("definitely_nonexistent_file.py")
    assert result == []


def test_review_file_new_file_no_compare(tmp_path):
    """New file (no old source) should return no issues."""
    fname = "new_test_file.py"
    new_file = tmp_path / fname
    new_file.write_text("def new_func():\n    return 1\n", encoding="utf-8")
    with patch.object(agent_diff_review, "REPO_ROOT", tmp_path):
        with patch.object(agent_diff_review, "get_old_source", return_value=None):
            result = review_file(fname)
    assert result == []


def test_review_file_removed_public_function(tmp_path):
    """Removing a public function should produce an issue."""
    fname = "changed.py"
    new_file = tmp_path / fname
    new_file.write_text("def new_func():\n    return 1\n", encoding="utf-8")
    old_source = "def old_func():\n    return 2\n"
    with patch.object(agent_diff_review, "REPO_ROOT", tmp_path):
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            result = review_file(fname)
    assert any("old_func" in i for i in result)


def test_review_file_signature_changed(tmp_path):
    """Changing function signature should produce an issue."""
    fname = "sig.py"
    new_file = tmp_path / fname
    new_file.write_text("def foo(a, b, c):\n    return 1\n", encoding="utf-8")
    old_source = "def foo(a, b):\n    return 1\n"
    with patch.object(agent_diff_review, "REPO_ROOT", tmp_path):
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            result = review_file(fname)
    assert any("foo" in i and "signature" in i for i in result)


def test_review_file_lost_return(tmp_path):
    """Removing a return statement should produce an issue."""
    fname = "ret.py"
    new_file = tmp_path / fname
    new_file.write_text("def foo():\n    pass\n", encoding="utf-8")
    old_source = "def foo():\n    return 42\n"
    with patch.object(agent_diff_review, "REPO_ROOT", tmp_path):
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            result = review_file(fname)
    assert any("return" in i for i in result)


def test_review_file_syntax_error_in_current(tmp_path):
    """Syntax error in current file should produce a syntax issue."""
    fname = "broken.py"
    new_file = tmp_path / fname
    new_file.write_text("def broken(:\n    pass\n", encoding="utf-8")
    with patch.object(agent_diff_review, "REPO_ROOT", tmp_path):
        with patch.object(agent_diff_review, "get_old_source", return_value="def broken():\n    pass\n"):
            result = review_file(fname)
    assert any("syntax" in i.lower() for i in result)
