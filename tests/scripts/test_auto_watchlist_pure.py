"""Tests for scripts/auto_watchlist_scan.py — pure-function coverage."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import auto_watchlist_scan  # noqa: E402


# ── _should_exclude ──────────────────────────────────────────────────────────

class TestShouldExclude:
    def test_pycache(self):
        assert auto_watchlist_scan._should_exclude(Path("__pycache__/foo.py")) is True

    def test_git(self):
        assert auto_watchlist_scan._should_exclude(Path(".git/config")) is True

    def test_venv(self):
        assert auto_watchlist_scan._should_exclude(Path(".venv/lib/thing.txt")) is True

    def test_node_modules(self):
        assert auto_watchlist_scan._should_exclude(Path("node_modules/pkg/x.md")) is True

    def test_ppa_excluded(self):
        assert auto_watchlist_scan._should_exclude(Path("ppa/README_PPA.md")) is True

    def test_docs_not_excluded(self):
        assert auto_watchlist_scan._should_exclude(Path("docs/PROTOCOL.md")) is False

    def test_scripts_not_excluded(self):
        assert auto_watchlist_scan._should_exclude(Path("scripts/mg.py")) is False

    def test_root_file_not_excluded(self):
        assert auto_watchlist_scan._should_exclude(Path("README.md")) is False


# ── collect_doc_files ────────────────────────────────────────────────────────

class TestCollectDocFiles:
    def test_root_md_file(self, tmp_path):
        (tmp_path / "README.md").write_text("hello", encoding="utf-8")
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert "README.md" in result

    def test_root_txt_file(self, tmp_path):
        (tmp_path / "llms.txt").write_text("data", encoding="utf-8")
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert "llms.txt" in result

    def test_docs_subdir(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "PROTOCOL.md").write_text("proto", encoding="utf-8")
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert "docs/PROTOCOL.md" in result

    def test_reports_yaml(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "faults.yaml").write_text("x: 1", encoding="utf-8")
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert "reports/faults.yaml" in result

    def test_excludes_pycache(self, tmp_path):
        docs = tmp_path / "docs" / "__pycache__"
        docs.mkdir(parents=True)
        (docs / "cached.md").write_text("x", encoding="utf-8")
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert not any("__pycache__" in r for r in result)

    def test_empty_dir(self, tmp_path):
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert result == set()

    def test_returns_set(self, tmp_path):
        (tmp_path / "A.md").write_text("a", encoding="utf-8")
        with patch("auto_watchlist_scan.REPO_ROOT", tmp_path):
            result = auto_watchlist_scan.collect_doc_files()
        assert isinstance(result, set)
