"""Tests for scripts/agent_learn.py — pure-function coverage."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_learn  # noqa: E402


# ── load_kb ──────────────────────────────────────────────────────────────────

class TestLoadKb:
    def test_default_when_no_file(self, tmp_path):
        fake = tmp_path / "kb.json"
        with patch("agent_learn.KB_FILE", fake):
            result = agent_learn.load_kb()
        assert result == {"sessions": [], "known_issues": {}, "auto_fixes": {}, "etalon": {}}

    def test_loads_saved_data(self, tmp_path):
        fake = tmp_path / "kb.json"
        data = {"sessions": [{"id": 1}], "known_issues": {}, "auto_fixes": {}, "etalon": {"v": 1}}
        fake.write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_learn.KB_FILE", fake):
            result = agent_learn.load_kb()
        assert result == data

    def test_invalid_json_raises(self, tmp_path):
        fake = tmp_path / "kb.json"
        fake.write_text("NOT JSON", encoding="utf-8")
        with patch("agent_learn.KB_FILE", fake):
            with pytest.raises(json.JSONDecodeError):
                agent_learn.load_kb()


# ── save_kb ──────────────────────────────────────────────────────────────────

class TestSaveKb:
    def test_writes_file(self, tmp_path):
        fake = tmp_path / "kb.json"
        data = {"sessions": [], "known_issues": {}, "auto_fixes": {}, "etalon": {}}
        with patch("agent_learn.KB_FILE", fake):
            agent_learn.save_kb(data)
        assert fake.exists()
        assert json.loads(fake.read_text(encoding="utf-8")) == data

    def test_roundtrip(self, tmp_path):
        fake = tmp_path / "kb.json"
        data = {"sessions": [{"x": 42}], "known_issues": {"a": "b"}, "auto_fixes": {}, "etalon": {"v": "0.8"}}
        with patch("agent_learn.KB_FILE", fake):
            agent_learn.save_kb(data)
            loaded = agent_learn.load_kb()
        assert loaded == data

    def test_overwrite(self, tmp_path):
        fake = tmp_path / "kb.json"
        with patch("agent_learn.KB_FILE", fake):
            agent_learn.save_kb({"sessions": [1]})
            agent_learn.save_kb({"sessions": [2]})
            loaded = agent_learn.load_kb()
        assert loaded == {"sessions": [2]}


# ── load_patterns / save_patterns ────────────────────────────────────────────

class TestPatterns:
    def test_load_default(self, tmp_path):
        fake = tmp_path / "patterns.json"
        with patch("agent_learn.PATTERNS_FILE", fake):
            result = agent_learn.load_patterns()
        assert result == {}

    def test_save_and_load(self, tmp_path):
        fake = tmp_path / "patterns.json"
        data = {"issue_x": {"count": 3, "first_seen": "2026-01-01"}}
        with patch("agent_learn.PATTERNS_FILE", fake):
            agent_learn.save_patterns(data)
            result = agent_learn.load_patterns()
        assert result == data


# ── scan_file_for_stale ──────────────────────────────────────────────────────

class TestScanFileForStale:
    def test_missing_file(self, tmp_path):
        issues = agent_learn.scan_file_for_stale(tmp_path / "nope.md", 608, "v0.8.0")
        assert len(issues) == 1
        assert "FILE MISSING" in issues[0]

    def test_clean_file(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("All good, 608 tests, v0.8.0", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        assert issues == []

    def test_old_count(self, tmp_path):
        f = tmp_path / "stale.md"
        f.write_text("We have 295 tests now", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        assert any("STALE COUNT" in i for i in issues)

    def test_old_version(self, tmp_path):
        f = tmp_path / "old.md"
        f.write_text("Current: v0.2.0 and 608 tests", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        assert any("STALE VERSION" in i for i in issues)

    def test_merge_conflict(self, tmp_path):
        f = tmp_path / "conflict.md"
        f.write_text("<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n608 tests", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        assert any("MERGE CONFLICT" in i for i in issues)

    def test_wrong_innovations(self, tmp_path):
        f = tmp_path / "innov.md"
        f.write_text("We have 7 innovations and 608 tests", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        assert any("WRONG INNOVATION COUNT" in i for i in issues)

    def test_readme_ppa_skips_282(self, tmp_path):
        f = tmp_path / "README_PPA.md"
        f.write_text("Patent ref 282 and 608 tests", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        stale_count_issues = [i for i in issues if "STALE COUNT" in i]
        assert stale_count_issues == []

    def test_multiple_issues(self, tmp_path):
        f = tmp_path / "multi.md"
        f.write_text("v0.1.0 with 271 tests and 7 innovations and <<<<<<< conflict", encoding="utf-8")
        issues = agent_learn.scan_file_for_stale(f, 608, "v0.8.0")
        assert len(issues) >= 3
