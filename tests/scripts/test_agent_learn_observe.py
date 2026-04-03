#!/usr/bin/env python3
"""Coverage tests for agent_learn.py observe/brief/stats -- 10 tests.

Targets observe() at 1.5%, brief() at 14.3%, stats() at 7.4%.
All heavy I/O (steward_audit, deep_verify, pytest) is mocked.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_learn as al


def _setup_agent_memory(tmp_path):
    """Create minimal repo structure needed by agent_learn."""
    mem_dir = tmp_path / ".agent_memory"
    mem_dir.mkdir(exist_ok=True)

    kb = {"sessions": [], "known_issues": {}, "auto_fixes": {}, "etalon": {}}
    (mem_dir / "knowledge_base.json").write_text(
        json.dumps(kb), encoding="utf-8"
    )
    (mem_dir / "patterns.json").write_text("{}", encoding="utf-8")

    # system_manifest.json
    (tmp_path / "system_manifest.json").write_text(
        json.dumps({"version": "0.8.0", "test_count": 1273}), encoding="utf-8"
    )

    # Critical files that check_critical_files scans
    for name in ["README.md", "AGENTS.md", "llms.txt", "CONTEXT_SNAPSHOT.md",
                 "CLAUDE.md", "paper.md"]:
        (tmp_path / name).write_text(f"# {name}\n1273 tests v0.8.0\n", encoding="utf-8")

    (tmp_path / "ppa").mkdir(exist_ok=True)
    (tmp_path / "ppa" / "README_PPA.md").write_text("# PPA\n", encoding="utf-8")

    (tmp_path / "reports").mkdir(exist_ok=True)
    (tmp_path / "reports" / "known_faults.yaml").write_text(
        "faults: []\n", encoding="utf-8"
    )

    # Lessons file (optional, created on first run)
    return tmp_path


def _mock_run_ok(cmd, *args, **kwargs):
    """Mock run() returning success for steward/deep_verify/pytest."""
    if "steward_audit" in str(cmd):
        return ("STEWARD AUDIT: PASS", 0)
    elif "deep_verify" in str(cmd):
        return ("ALL 13 TESTS PASSED", 0)
    elif "pytest" in str(cmd):
        return ("1273 passed", 0)
    return ("", 0)


# -- observe() tests --------------------------------------------------------

class TestObserve:
    def test_observe_runs_clean(self, tmp_path):
        """observe() completes without exception and returns bool."""
        repo = _setup_agent_memory(tmp_path)
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", repo / ".agent_memory" / "knowledge_base.json"), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"), \
             patch.object(al, "LESSONS_FILE", repo / ".agent_memory" / "lessons.md"), \
             patch.object(al, "run", _mock_run_ok):
            result = al.observe()
        assert isinstance(result, bool)

    def test_observe_saves_kb(self, tmp_path):
        """observe() writes updated knowledge_base.json with a session."""
        repo = _setup_agent_memory(tmp_path)
        kb_file = repo / ".agent_memory" / "knowledge_base.json"
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"), \
             patch.object(al, "LESSONS_FILE", repo / ".agent_memory" / "lessons.md"), \
             patch.object(al, "run", _mock_run_ok):
            al.observe()
        kb = json.loads(kb_file.read_text(encoding="utf-8"))
        assert len(kb["sessions"]) == 1
        assert kb["sessions"][0]["steward_pass"] is True

    def test_observe_detects_steward_failure(self, tmp_path):
        """observe() records steward failure when audit fails."""
        repo = _setup_agent_memory(tmp_path)
        kb_file = repo / ".agent_memory" / "knowledge_base.json"

        def mock_run_fail(cmd, *a, **kw):
            if "steward_audit" in str(cmd):
                return ("FAIL", 1)
            return _mock_run_ok(cmd, *a, **kw)

        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"), \
             patch.object(al, "LESSONS_FILE", repo / ".agent_memory" / "lessons.md"), \
             patch.object(al, "run", mock_run_fail):
            al.observe()
        kb = json.loads(kb_file.read_text(encoding="utf-8"))
        assert kb["sessions"][0]["steward_pass"] is False

    def test_observe_returns_true_when_clean(self, tmp_path):
        """observe() returns True when no issues found."""
        repo = _setup_agent_memory(tmp_path)
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", repo / ".agent_memory" / "knowledge_base.json"), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"), \
             patch.object(al, "LESSONS_FILE", repo / ".agent_memory" / "lessons.md"), \
             patch.object(al, "run", _mock_run_ok):
            result = al.observe()
        assert result is True


# -- brief() tests ----------------------------------------------------------

class TestBrief:
    def test_brief_no_sessions(self, tmp_path, capsys):
        """brief() prints summary even with empty kb."""
        repo = _setup_agent_memory(tmp_path)
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", repo / ".agent_memory" / "knowledge_base.json"), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"):
            al.brief()
        captured = capsys.readouterr()
        assert "Agent memory" in captured.out

    def test_brief_with_sessions(self, tmp_path, capsys):
        """brief() includes session count in output."""
        repo = _setup_agent_memory(tmp_path)
        kb_file = repo / ".agent_memory" / "knowledge_base.json"
        kb = json.loads(kb_file.read_text(encoding="utf-8"))
        kb["sessions"] = [{"timestamp": "2026-01-01"}] * 5
        kb["etalon"] = {"version": "0.8.0", "test_count": 1273}
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"):
            al.brief()
        captured = capsys.readouterr()
        assert "5 sessions" in captured.out

    def test_brief_shows_hints(self, tmp_path, capsys):
        """brief() counts auto-fix hints."""
        repo = _setup_agent_memory(tmp_path)
        pf = repo / ".agent_memory" / "patterns.json"
        pf.write_text(json.dumps({
            "issue_a": {"count": 3, "fix_hint": "do X"},
            "issue_b": {"count": 1},
        }), encoding="utf-8")
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", repo / ".agent_memory" / "knowledge_base.json"), \
             patch.object(al, "PATTERNS_FILE", pf):
            al.brief()
        captured = capsys.readouterr()
        assert "1 auto-fix" in captured.out


# -- stats() tests ----------------------------------------------------------

class TestStats:
    def test_stats_no_sessions(self, tmp_path, capsys):
        """stats() handles empty kb gracefully."""
        repo = _setup_agent_memory(tmp_path)
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", repo / ".agent_memory" / "knowledge_base.json"), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"):
            al.stats()
        captured = capsys.readouterr()
        assert "No sessions" in captured.out

    def test_stats_with_sessions(self, tmp_path, capsys):
        """stats() prints evolution stats with session data."""
        repo = _setup_agent_memory(tmp_path)
        kb_file = repo / ".agent_memory" / "knowledge_base.json"
        kb = {
            "sessions": [
                {"timestamp": "2026-01-01T00:00:00", "issue_count": 2},
                {"timestamp": "2026-01-02T00:00:00", "issue_count": 0},
            ],
            "known_issues": {}, "auto_fixes": {}, "etalon": {},
        }
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"):
            al.stats()
        captured = capsys.readouterr()
        assert "Total sessions" in captured.out
        assert "2" in captured.out

    def test_stats_trend_improving(self, tmp_path, capsys):
        """stats() detects improving trend."""
        repo = _setup_agent_memory(tmp_path)
        kb_file = repo / ".agent_memory" / "knowledge_base.json"
        kb = {
            "sessions": [
                {"timestamp": "2026-01-01T00:00:00", "issue_count": 5},
                {"timestamp": "2026-01-02T00:00:00", "issue_count": 0},
            ],
            "known_issues": {}, "auto_fixes": {}, "etalon": {},
        }
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        with patch.object(al, "REPO_ROOT", repo), \
             patch.object(al, "MEMORY_DIR", repo / ".agent_memory"), \
             patch.object(al, "KB_FILE", kb_file), \
             patch.object(al, "PATTERNS_FILE", repo / ".agent_memory" / "patterns.json"):
            al.stats()
        captured = capsys.readouterr()
        assert "improving" in captured.out
