#!/usr/bin/env python3
"""Extended coverage tests for scripts/agent_learn.py -- 20 tests."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_learn as al


# -- load_kb / save_kb extended ------------------------------------------------

class TestLoadKbExtended:
    def test_load_kb_no_file_returns_default(self, tmp_path):
        fake = tmp_path / "nonexistent" / "kb.json"
        with patch.object(al, "KB_FILE", fake):
            result = al.load_kb()
        assert "sessions" in result
        assert isinstance(result["sessions"], list)

    def test_load_kb_valid_file(self, tmp_path):
        fake = tmp_path / "kb.json"
        data = {"sessions": [{"ts": "2026-01-01"}], "known_issues": {},
                "auto_fixes": {}, "etalon": {"version": "0.8.0"}}
        fake.write_text(json.dumps(data), encoding="utf-8")
        with patch.object(al, "KB_FILE", fake):
            result = al.load_kb()
        assert result["etalon"]["version"] == "0.8.0"
        assert len(result["sessions"]) == 1


class TestSaveKbExtended:
    def test_save_kb_writes_valid_json(self, tmp_path):
        fake = tmp_path / "kb.json"
        data = {"sessions": [{"id": 99}], "known_issues": {},
                "auto_fixes": {}, "etalon": {}}
        with patch.object(al, "KB_FILE", fake):
            al.save_kb(data)
        loaded = json.loads(fake.read_text(encoding="utf-8"))
        assert loaded["sessions"][0]["id"] == 99


# -- load_patterns / save_patterns extended ------------------------------------

class TestPatternsExtended:
    def test_load_patterns_no_file(self, tmp_path):
        fake = tmp_path / "no_such_patterns.json"
        with patch.object(al, "PATTERNS_FILE", fake):
            result = al.load_patterns()
        assert result == {}

    def test_load_patterns_valid(self, tmp_path):
        fake = tmp_path / "patterns.json"
        data = {"stale_count": {"count": 5, "first_seen": "2026-01-01"}}
        fake.write_text(json.dumps(data), encoding="utf-8")
        with patch.object(al, "PATTERNS_FILE", fake):
            result = al.load_patterns()
        assert result["stale_count"]["count"] == 5

    def test_save_patterns_writes_json(self, tmp_path):
        fake = tmp_path / "patterns.json"
        data = {"issue_a": {"count": 2}}
        with patch.object(al, "PATTERNS_FILE", fake):
            al.save_patterns(data)
        loaded = json.loads(fake.read_text(encoding="utf-8"))
        assert loaded == data


# -- get_test_count ------------------------------------------------------------

class TestGetTestCount:
    def test_parses_count_from_output(self):
        with patch.object(al, "run", return_value=("1125 passed in 10.23s", 0)):
            count = al.get_test_count()
        assert count == 1125

    def test_returns_zero_on_no_match(self):
        with patch.object(al, "run", return_value=("error: no tests", 1)):
            count = al.get_test_count()
        assert count == 0


# -- get_manifest_version ------------------------------------------------------

class TestGetManifestVersion:
    def test_valid_manifest(self, tmp_path):
        manifest = tmp_path / "system_manifest.json"
        manifest.write_text(json.dumps({"version": "0.8.0", "test_count": 1125}),
                            encoding="utf-8")
        with patch.object(al, "REPO_ROOT", tmp_path):
            ver, count = al.get_manifest_version()
        assert ver == "0.8.0"
        assert count == 1125

    def test_no_manifest_file(self, tmp_path):
        with patch.object(al, "REPO_ROOT", tmp_path):
            ver, count = al.get_manifest_version()
        assert ver == "?"
        assert count == 0


# -- scan_file_for_stale extended ----------------------------------------------

class TestScanFileExtended:
    def test_clean_file_no_issues(self, tmp_path):
        f = tmp_path / "clean.md"
        f.write_text("We have 1125 tests v0.8.0", encoding="utf-8")
        issues = al.scan_file_for_stale(f, 1125, "v0.8.0")
        assert issues == []

    def test_missing_file_returns_issue(self, tmp_path):
        issues = al.scan_file_for_stale(tmp_path / "gone.md", 1125, "v0.8.0")
        assert len(issues) == 1
        assert "FILE MISSING" in issues[0]

    def test_merge_conflict_detected(self, tmp_path):
        f = tmp_path / "conflict.md"
        f.write_text("<<<<<<< HEAD\nstuff\n=======\nother\n>>>>>>> branch\n1125 tests",
                      encoding="utf-8")
        issues = al.scan_file_for_stale(f, 1125, "v0.8.0")
        assert any("MERGE CONFLICT" in i for i in issues)

    def test_old_count_flagged(self, tmp_path):
        f = tmp_path / "stale.md"
        f.write_text("We have 295 tests now", encoding="utf-8")
        issues = al.scan_file_for_stale(f, 1125, "v0.8.0")
        assert any("STALE COUNT" in i for i in issues)

    def test_old_version_flagged(self, tmp_path):
        f = tmp_path / "old_ver.md"
        f.write_text("Current v0.2.0 release with 1125 tests", encoding="utf-8")
        issues = al.scan_file_for_stale(f, 1125, "v0.8.0")
        assert any("STALE VERSION" in i for i in issues)


# -- check_critical_files -----------------------------------------------------

class TestCheckCriticalFiles:
    def _create_critical_files(self, root, count, version):
        """Create all 9 critical files with valid content."""
        files = {
            "README.md": f"{count} tests {version}",
            "AGENTS.md": f"{count} tests {version}",
            "llms.txt": f"{count} tests {version}",
            "CONTEXT_SNAPSHOT.md": f"{count} tests {version}",
            "CLAUDE.md": f"{count} tests {version}",
            "system_manifest.json": json.dumps({"version": version, "test_count": count}),
            "paper.md": f"{count} tests {version}",
        }
        (root / "ppa").mkdir(exist_ok=True)
        files["ppa/README_PPA.md"] = f"{count} tests {version}"
        (root / "reports").mkdir(exist_ok=True)
        files["reports/known_faults.yaml"] = f"{count} tests {version}"

        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

    def test_all_clean(self, tmp_path):
        self._create_critical_files(tmp_path, 1125, "v0.8.0")
        with patch.object(al, "REPO_ROOT", tmp_path):
            results = al.check_critical_files(1125, "v0.8.0")
        for fname, issues in results.items():
            assert issues == [], f"{fname} has issues: {issues}"

    def test_one_stale(self, tmp_path):
        self._create_critical_files(tmp_path, 1125, "v0.8.0")
        # Make README.md stale
        (tmp_path / "README.md").write_text("Old 295 tests", encoding="utf-8")
        with patch.object(al, "REPO_ROOT", tmp_path):
            results = al.check_critical_files(1125, "v0.8.0")
        assert len(results["README.md"]) > 0


# -- _write_lessons_log --------------------------------------------------------

class TestWriteLessonsLog:
    def test_creates_file(self, tmp_path):
        lessons = tmp_path / "lessons.md"
        with patch.object(al, "LESSONS_FILE", lessons), \
             patch.object(al, "REPO_ROOT", tmp_path):
            session = {"actual_test_count": 1125, "etalon_version": "0.8.0",
                       "steward_pass": True, "deep_verify_pass": True}
            al._write_lessons_log(session, [], {})
        assert lessons.exists()
        content = lessons.read_text(encoding="utf-8")
        assert "Session" in content
        assert "1125" in content


# -- recall / stats ------------------------------------------------------------

class TestRecall:
    def test_recall_no_error(self, tmp_path, capsys):
        kb_file = tmp_path / "kb.json"
        patterns_file = tmp_path / "patterns.json"
        kb = {"sessions": [{"timestamp": "2026-01-01T00:00:00",
                            "issue_count": 0, "actual_test_count": 1125}],
              "known_issues": {}, "auto_fixes": {},
              "etalon": {"version": "0.8.0", "test_count": 1125,
                         "updated": "2026-01-01T00:00:00"}}
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns_file.write_text("{}", encoding="utf-8")
        with patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", patterns_file):
            al.recall()
        out = capsys.readouterr().out
        assert "ETALON" in out or "0.8.0" in out


class TestStats:
    def test_stats_no_error(self, tmp_path, capsys):
        kb_file = tmp_path / "kb.json"
        patterns_file = tmp_path / "patterns.json"
        kb = {"sessions": [{"timestamp": "2026-01-01T00:00:00",
                            "issue_count": 0, "actual_test_count": 1125}],
              "known_issues": {}, "auto_fixes": {}, "etalon": {}}
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns_file.write_text("{}", encoding="utf-8")
        with patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", patterns_file):
            al.stats()
        out = capsys.readouterr().out
        assert "sessions" in out.lower() or "Stats" in out
