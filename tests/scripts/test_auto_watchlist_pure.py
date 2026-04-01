"""Tests for scripts/auto_watchlist_scan.py — pure functions."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from auto_watchlist_scan import _should_exclude, collect_doc_files


class TestShouldExclude:
    def test_git_excluded(self):
        assert _should_exclude(Path(".git/config")) is True

    def test_pycache_excluded(self):
        assert _should_exclude(Path("scripts/__pycache__/foo.pyc")) is True

    def test_node_modules_excluded(self):
        assert _should_exclude(Path("node_modules/package.json")) is True

    def test_normal_path_not_excluded(self):
        assert _should_exclude(Path("docs/PROTOCOL.md")) is False

    def test_root_file_not_excluded(self):
        assert _should_exclude(Path("README.md")) is False


class TestCollectDocFiles:
    def test_returns_non_empty(self):
        result = collect_doc_files()
        assert len(result) > 0

    def test_returns_set(self):
        result = collect_doc_files()
        assert isinstance(result, set)

    def test_contains_readme(self):
        result = collect_doc_files()
        assert "README.md" in result
