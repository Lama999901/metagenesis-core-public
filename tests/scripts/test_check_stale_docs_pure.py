"""Tests for scripts/check_stale_docs.py — pure-function coverage."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_stale_docs  # noqa: E402


# ── check_content ────────────────────────────────────────────────────────────

class TestCheckContent:
    def test_clean_file(self, tmp_path):
        (tmp_path / "good.md").write_text("We have 734 tests and v0.8 release", encoding="utf-8")
        checks = {"banned": ["601 tests"], "required": ["734", "v0.8"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("good.md", checks)
        assert issues == []

    def test_banned_string_found(self, tmp_path):
        (tmp_path / "bad.md").write_text("We still have 601 tests", encoding="utf-8")
        checks = {"banned": ["601 tests"], "required": []}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("bad.md", checks)
        assert len(issues) == 1
        assert issues[0].startswith("BANNED:")

    def test_missing_required(self, tmp_path):
        (tmp_path / "miss.md").write_text("Some content without the count", encoding="utf-8")
        checks = {"banned": [], "required": ["734"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("miss.md", checks)
        assert len(issues) == 1
        assert issues[0].startswith("MISSING:")

    def test_both_banned_and_missing(self, tmp_path):
        (tmp_path / "both.md").write_text("old 601 tests here", encoding="utf-8")
        checks = {"banned": ["601 tests"], "required": ["734"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("both.md", checks)
        assert len(issues) == 2
        types = {i.split(":")[0] for i in issues}
        assert types == {"BANNED", "MISSING"}

    def test_case_insensitive(self, tmp_path):
        (tmp_path / "case.md").write_text("ALL 13 tests PASSED", encoding="utf-8")
        checks = {"banned": [], "required": ["all 13 tests passed"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("case.md", checks)
        assert issues == []

    def test_case_insensitive_banned(self, tmp_path):
        (tmp_path / "case2.md").write_text("We have 601 TESTS here", encoding="utf-8")
        checks = {"banned": ["601 tests"], "required": []}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("case2.md", checks)
        assert len(issues) == 1
        assert "BANNED" in issues[0]

    def test_missing_file_returns_empty(self, tmp_path):
        checks = {"banned": ["x"], "required": ["y"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("nonexistent.md", checks)
        assert issues == []

    def test_empty_file(self, tmp_path):
        (tmp_path / "empty.md").write_text("", encoding="utf-8")
        checks = {"banned": [], "required": ["something"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("empty.md", checks)
        assert len(issues) == 1
        assert "MISSING" in issues[0]

    def test_multiple_banned(self, tmp_path):
        (tmp_path / "multi.md").write_text("601 tests and 595 passing", encoding="utf-8")
        checks = {"banned": ["601 tests", "595 passing"], "required": []}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("multi.md", checks)
        assert len(issues) == 2

    def test_multiple_missing(self, tmp_path):
        (tmp_path / "multi2.md").write_text("nothing here", encoding="utf-8")
        checks = {"banned": [], "required": ["734", "v0.8", "20 claims"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("multi2.md", checks)
        assert len(issues) == 3

    def test_empty_checks(self, tmp_path):
        (tmp_path / "ok.md").write_text("anything", encoding="utf-8")
        checks = {"banned": [], "required": []}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("ok.md", checks)
        assert issues == []

    def test_subdirectory_path(self, tmp_path):
        sub = tmp_path / "reports"
        sub.mkdir()
        (sub / "file.md").write_text("has 734 in it", encoding="utf-8")
        checks = {"banned": [], "required": ["734"]}
        with patch("check_stale_docs.REPO_ROOT", tmp_path):
            issues = check_stale_docs.check_content("reports/file.md", checks)
        assert issues == []


# ── files_in_tracked_paths ───────────────────────────────────────────────────

class TestFilesInTrackedPaths:
    def test_exact_match(self):
        result = check_stale_docs.files_in_tracked_paths(
            ["scripts/mg.py"], ["scripts/mg.py"]
        )
        assert result is True

    def test_prefix_match(self):
        result = check_stale_docs.files_in_tracked_paths(
            ["scripts/mg.py"], ["scripts/"]
        )
        assert result is True

    def test_no_match(self):
        result = check_stale_docs.files_in_tracked_paths(
            ["backend/runner.py"], ["scripts/"]
        )
        assert result is False

    def test_empty_changed(self):
        result = check_stale_docs.files_in_tracked_paths([], ["scripts/"])
        assert result is False

    def test_empty_tracked(self):
        result = check_stale_docs.files_in_tracked_paths(["scripts/mg.py"], [])
        assert result is False

    def test_multiple_changed_one_matches(self):
        result = check_stale_docs.files_in_tracked_paths(
            ["README.md", "tests/test_foo.py", "scripts/mg.py"],
            ["scripts/"]
        )
        assert result is True

    def test_multiple_tracked_one_matches(self):
        result = check_stale_docs.files_in_tracked_paths(
            ["backend/progress/runner.py"],
            ["scripts/", "backend/progress/", "docs/"]
        )
        assert result is True

    def test_no_partial_dir_match(self):
        """'scripts_extra/foo.py' should NOT match tracked 'scripts/'
        because startswith would match. This tests actual behavior."""
        result = check_stale_docs.files_in_tracked_paths(
            ["scripts_extra/foo.py"], ["scripts/"]
        )
        # startswith("scripts/") is False for "scripts_extra/foo.py"
        assert result is False
