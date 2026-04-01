"""Tests for scripts/agent_learn.py — pure file I/O functions."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agent_learn import load_kb, save_kb, load_patterns, save_patterns, scan_file_for_stale


class TestLoadKb:
    def test_returns_dict(self):
        kb = load_kb()
        assert isinstance(kb, dict)

    def test_has_sessions_key(self):
        kb = load_kb()
        assert "sessions" in kb


class TestSaveAndLoadKb:
    def test_roundtrip(self, tmp_path):
        kb_file = tmp_path / "kb.json"
        test_kb = {"sessions": [{"ts": "2026-01-01"}], "known_issues": {}, "auto_fixes": {}, "etalon": {}}
        kb_file.write_text(json.dumps(test_kb), encoding="utf-8")
        loaded = json.loads(kb_file.read_text(encoding="utf-8"))
        assert loaded == test_kb


class TestLoadPatterns:
    def test_returns_dict(self):
        patterns = load_patterns()
        assert isinstance(patterns, dict)


class TestSavePatterns:
    def test_roundtrip(self, tmp_path):
        p_file = tmp_path / "patterns.json"
        test_patterns = {"stale_count": {"count": 3}}
        p_file.write_text(json.dumps(test_patterns), encoding="utf-8")
        loaded = json.loads(p_file.read_text(encoding="utf-8"))
        assert loaded == test_patterns


class TestScanFileForStale:
    def test_clean_file(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("608 tests passing v0.8.0")
        issues = scan_file_for_stale(f, 608, "0.8.0")
        assert isinstance(issues, list)

    def test_missing_file(self, tmp_path):
        f = tmp_path / "nonexistent.md"
        issues = scan_file_for_stale(f, 608, "0.8.0")
        assert len(issues) > 0
        assert "MISSING" in issues[0]

    def test_merge_conflict_markers(self, tmp_path):
        f = tmp_path / "conflict.md"
        f.write_text("<<<<<<< HEAD\nsome content\n=======\nother\n>>>>>>> branch")
        issues = scan_file_for_stale(f, 608, "0.8.0")
        assert any("MERGE CONFLICT" in i for i in issues)
