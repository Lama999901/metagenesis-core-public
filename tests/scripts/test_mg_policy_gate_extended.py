#!/usr/bin/env python3
"""Extended coverage tests for scripts/mg_policy_gate.py -- 10 tests."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import mg_policy_gate as mpg


POLICY_PATH = str(REPO_ROOT / "scripts" / "mg_policy_gate_policy.json")


def _gate():
    return mpg.PolicyGate(POLICY_PATH)


# -- get_changed_files_git -----------------------------------------------------

class TestGetChangedFilesGit:
    def test_returns_list_of_files(self):
        mock_result = MagicMock()
        mock_result.stdout = "README.md\nscripts/mg.py\n"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            files = _gate().get_changed_files_git("origin/main", "HEAD")
        assert "README.md" in files
        assert "scripts/mg.py" in files

    def test_empty_diff_returns_empty(self):
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            files = _gate().get_changed_files_git("origin/main", "HEAD")
        assert files == []

    def test_single_file(self):
        mock_result = MagicMock()
        mock_result.stdout = "index.html\n"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            files = _gate().get_changed_files_git("a", "b")
        assert files == ["index.html"]

    def test_strips_whitespace(self):
        mock_result = MagicMock()
        mock_result.stdout = "  a.py  \n  b.md  \n"
        mock_result.returncode = 0
        with patch("subprocess.run", return_value=mock_result):
            files = _gate().get_changed_files_git("a", "b")
        assert "a.py" in files
        assert "b.md" in files


# -- get_changed_files_list ----------------------------------------------------

class TestGetChangedFilesList:
    def test_parses_comma_separated(self):
        files = _gate().get_changed_files_list("a.py,b.md,c.txt")
        assert files == ["a.py", "b.md", "c.txt"]

    def test_empty_string(self):
        files = _gate().get_changed_files_list("")
        assert files == []


# -- enforce -------------------------------------------------------------------

class TestEnforce:
    def test_empty_files_passes(self, capsys):
        result = _gate().enforce([])
        assert result is True

    def test_allowed_files_pass(self, capsys):
        result = _gate().enforce(["README.md", "scripts/mg.py"])
        assert result is True

    def test_locked_file_fails(self, capsys):
        result = _gate().enforce(["scripts/steward_audit.py"])
        assert result is False

    def test_prints_policy_version(self, capsys):
        _gate().enforce(["README.md"])
        out = capsys.readouterr().out
        assert "Policy" in out or "PASSED" in out
