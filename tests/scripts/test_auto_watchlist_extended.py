#!/usr/bin/env python3
"""Extended coverage tests for scripts/auto_watchlist_scan.py -- 15 tests."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import auto_watchlist_scan as aws


# -- _should_exclude extended --------------------------------------------------

class TestShouldExcludeExtended:
    def test_planning_excluded(self):
        assert aws._should_exclude(Path(".planning/STATE.md")) is True

    def test_claude_excluded(self):
        assert aws._should_exclude(Path(".claude/config.json")) is True

    def test_mypy_cache_excluded(self):
        assert aws._should_exclude(Path(".mypy_cache/some/file.txt")) is True

    def test_pytest_cache_excluded(self):
        assert aws._should_exclude(Path(".pytest_cache/v/cache/file.txt")) is True

    def test_pack_excluded(self):
        assert aws._should_exclude(Path("pack/something.md")) is True

    def test_reports_not_excluded(self):
        assert aws._should_exclude(Path("reports/COVERAGE.md")) is False

    def test_demos_not_excluded(self):
        assert aws._should_exclude(Path("demos/readme.md")) is False


# -- collect_doc_files extended ------------------------------------------------

class TestCollectDocFilesExtended:
    def test_yaml_extension(self, tmp_path):
        (tmp_path / "reports").mkdir()
        (tmp_path / "reports" / "data.yaml").write_text("x: 1", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path):
            result = aws.collect_doc_files()
        assert "reports/data.yaml" in result

    def test_yml_extension(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "config.yml").write_text("a: b", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path):
            result = aws.collect_doc_files()
        assert "docs/config.yml" in result

    def test_cff_extension(self, tmp_path):
        (tmp_path / "CITATION.cff").write_text("cff-version: 1.2.0", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path):
            result = aws.collect_doc_files()
        assert "CITATION.cff" in result

    def test_ignores_py_files(self, tmp_path):
        (tmp_path / "script.py").write_text("print('hi')", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path):
            result = aws.collect_doc_files()
        assert "script.py" not in result

    def test_nested_subdir(self, tmp_path):
        nested = tmp_path / "docs" / "sub"
        nested.mkdir(parents=True)
        (nested / "deep.md").write_text("deep", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path):
            result = aws.collect_doc_files()
        assert "docs/sub/deep.md" in result


# -- scan() --------------------------------------------------------------------

class TestScanExtended:
    def test_scan_returns_zero_all_watched(self, tmp_path, capsys):
        """When all files are watched, returns 0."""
        (tmp_path / "README.md").write_text("hi", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path), \
             patch.object(aws, "WATCHED", {"README.md"}):
            code = aws.scan(strict=False)
        assert code == 0

    def test_scan_returns_one_strict_unwatched(self, tmp_path, capsys):
        """Strict mode returns 1 when unwatched files exist."""
        (tmp_path / "UNKNOWN.md").write_text("hi", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path), \
             patch.object(aws, "WATCHED", set()):
            code = aws.scan(strict=True)
        assert code == 1

    def test_scan_returns_zero_non_strict_unwatched(self, tmp_path, capsys):
        """Non-strict returns 0 even with unwatched."""
        (tmp_path / "UNKNOWN.md").write_text("hi", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path), \
             patch.object(aws, "WATCHED", set()):
            code = aws.scan(strict=False)
        assert code == 0

    def test_scan_empty_dir(self, tmp_path, capsys):
        with patch.object(aws, "REPO_ROOT", tmp_path), \
             patch.object(aws, "WATCHED", set()):
            code = aws.scan(strict=False)
        assert code == 0

    def test_scan_prints_warning_for_unwatched(self, tmp_path, capsys):
        (tmp_path / "ORPHAN.txt").write_text("lost", encoding="utf-8")
        with patch.object(aws, "REPO_ROOT", tmp_path), \
             patch.object(aws, "WATCHED", set()):
            aws.scan(strict=False)
        out = capsys.readouterr().out
        assert "WARNING" in out or "unwatched" in out
