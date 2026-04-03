#!/usr/bin/env python3
"""Coverage tests for agent_diff_review.py review_file() and main() branches."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_diff_review  # noqa: E402


# ---------------------------------------------------------------------------
# review_file() tests
# ---------------------------------------------------------------------------

class TestReviewFile:
    """Tests for review_file() regression detection."""

    def test_detects_removed_public_function(self, tmp_path, monkeypatch):
        """review_file() detects when a public function is removed."""
        monkeypatch.setattr(agent_diff_review, "REPO_ROOT", tmp_path)
        # Create current file without the function
        target = tmp_path / "scripts" / "example.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def remaining():\n    return 1\n", encoding="utf-8")

        old_source = "def removed_func():\n    return 1\n\ndef remaining():\n    return 1\n"
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            issues = agent_diff_review.review_file("scripts/example.py")
        assert any("removed_func" in i and "removed" in i for i in issues)

    def test_detects_signature_change(self, tmp_path, monkeypatch):
        """review_file() detects signature changes in existing functions."""
        monkeypatch.setattr(agent_diff_review, "REPO_ROOT", tmp_path)
        target = tmp_path / "scripts" / "example.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def my_func(a, b, c):\n    return a\n", encoding="utf-8")

        old_source = "def my_func(a, b):\n    return a\n"
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            issues = agent_diff_review.review_file("scripts/example.py")
        assert any("signature changed" in i for i in issues)

    def test_detects_lost_return(self, tmp_path, monkeypatch):
        """review_file() detects when a function loses its return statement."""
        monkeypatch.setattr(agent_diff_review, "REPO_ROOT", tmp_path)
        target = tmp_path / "scripts" / "example.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def compute(x):\n    x + 1\n", encoding="utf-8")

        old_source = "def compute(x):\n    return x + 1\n"
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            issues = agent_diff_review.review_file("scripts/example.py")
        assert any("lost its return" in i for i in issues)

    def test_detects_missing_trace_root_hash(self, tmp_path):
        """review_file() detects _hash_step without trace_root_hash in claim files."""
        target = tmp_path / "backend" / "progress" / "claim.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        current_source = (
            "def _hash_step(name, data, prev):\n"
            "    pass\n"
        )
        target.write_text(current_source, encoding="utf-8")

        # Provide old_source so review_file doesn't return early at line 107
        old_source = "def _hash_step(name, data, prev):\n    pass\n"
        with patch.object(agent_diff_review, "REPO_ROOT", tmp_path), \
             patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            issues = agent_diff_review.review_file("backend/progress/claim.py")
        assert any("trace_root_hash" in i for i in issues)
        assert any("execution_trace" in i for i in issues)

    def test_no_issues_for_private_removal(self, tmp_path, monkeypatch):
        """review_file() does not flag removal of private functions (starting with _)."""
        monkeypatch.setattr(agent_diff_review, "REPO_ROOT", tmp_path)
        target = tmp_path / "scripts" / "example.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def public_fn():\n    return 1\n", encoding="utf-8")

        old_source = "def _private():\n    return 1\n\ndef public_fn():\n    return 1\n"
        with patch.object(agent_diff_review, "get_old_source", return_value=old_source):
            issues = agent_diff_review.review_file("scripts/example.py")
        assert not any("_private" in i for i in issues)

    def test_no_issues_for_new_file(self, tmp_path, monkeypatch):
        """review_file() returns no issues for new files (no old source)."""
        monkeypatch.setattr(agent_diff_review, "REPO_ROOT", tmp_path)
        target = tmp_path / "scripts" / "new_file.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def new_func():\n    pass\n", encoding="utf-8")

        with patch.object(agent_diff_review, "get_old_source", return_value=None):
            issues = agent_diff_review.review_file("scripts/new_file.py")
        assert issues == []


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for main() flow."""

    @patch.object(agent_diff_review, "get_changed_py_files", return_value=[])
    def test_main_returns_0_no_changed_files(self, mock_files, monkeypatch):
        """main() returns 0 when no Python files changed."""
        monkeypatch.setattr("sys.argv", ["agent_diff_review.py"])
        result = agent_diff_review.main()
        assert result == 0

    @patch.object(agent_diff_review, "get_changed_py_files", return_value=[])
    def test_main_summary_diff_pass(self, mock_files, capsys, monkeypatch):
        """main() prints DIFF_PASS in summary mode when clean."""
        monkeypatch.setattr("sys.argv", ["agent_diff_review.py", "--summary"])
        result = agent_diff_review.main()
        assert result == 0
        captured = capsys.readouterr()
        assert "DIFF_PASS" in captured.out

    @patch.object(agent_diff_review, "get_changed_py_files", return_value=["scripts/test.py"])
    @patch.object(agent_diff_review, "review_file", return_value=["scripts/test.py: public function 'foo' was removed"])
    def test_main_returns_1_with_issues(self, mock_review, mock_files, monkeypatch):
        """main() returns 1 when issues are found."""
        monkeypatch.setattr("sys.argv", ["agent_diff_review.py"])
        result = agent_diff_review.main()
        assert result == 1

    @patch.object(agent_diff_review, "get_changed_py_files", return_value=["scripts/test.py"])
    @patch.object(agent_diff_review, "review_file", return_value=["issue"])
    def test_main_summary_diff_fail(self, mock_review, mock_files, capsys, monkeypatch):
        """main() prints DIFF_FAIL in summary mode when issues exist."""
        monkeypatch.setattr("sys.argv", ["agent_diff_review.py", "--summary"])
        result = agent_diff_review.main()
        assert result == 1
        captured = capsys.readouterr()
        assert "DIFF_FAIL" in captured.out
