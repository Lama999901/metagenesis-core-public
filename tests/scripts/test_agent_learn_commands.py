#!/usr/bin/env python3
"""Coverage tests for agent_learn.py recall(), brief(), and stats() commands."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_learn  # noqa: E402


def _make_kb(sessions=None, etalon=None):
    """Build a knowledge base dict for testing."""
    return {
        "sessions": sessions or [],
        "known_issues": {},
        "auto_fixes": {},
        "etalon": etalon or {},
    }


def _make_session(ts="2026-04-01T12:00:00", count=1634, issues=0):
    """Build a session entry for testing."""
    return {
        "timestamp": ts,
        "etalon_version": "0.9.0",
        "actual_test_count": count,
        "manifest_test_count": count,
        "steward_pass": True,
        "deep_verify_pass": True,
        "manifest_consistent": True,
        "file_issues": {},
        "issue_count": issues,
    }


# ---------------------------------------------------------------------------
# recall() tests
# ---------------------------------------------------------------------------

class TestRecall:
    """Tests for recall() command."""

    def test_recall_prints_etalon_and_sessions(self, tmp_path, capsys):
        """recall() prints etalon version and recent sessions."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb(
            sessions=[_make_session(), _make_session(ts="2026-04-02T10:00:00")],
            etalon={"version": "0.9.0", "test_count": 1634, "updated": "2026-04-02T10:00:00"},
        )
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns_file.write_text("{}", encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.recall()

        out = capsys.readouterr().out
        assert "0.9.0" in out
        assert "1634" in out
        assert "RECENT SESSIONS" in out

    def test_recall_empty_kb(self, tmp_path, capsys):
        """recall() prints 'No sessions recorded' when KB is empty."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb()
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns_file.write_text("{}", encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.recall()

        out = capsys.readouterr().out
        assert "No sessions recorded" in out

    def test_recall_shows_fix_hints(self, tmp_path, capsys):
        """recall() shows auto-fix hints when patterns have them."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb(
            sessions=[_make_session()],
            etalon={"version": "0.9.0", "test_count": 1634, "updated": "2026-04-01"},
        )
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns = {
            "STALE COUNT in README.md": {
                "count": 3,
                "first_seen": "2026-03-01",
                "fix_hint": "Sync counters",
                "last_seen": "2026-04-01",
            }
        }
        patterns_file.write_text(json.dumps(patterns), encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.recall()

        out = capsys.readouterr().out
        assert "AUTO-FIX HINTS" in out
        assert "Sync counters" in out


# ---------------------------------------------------------------------------
# brief() tests
# ---------------------------------------------------------------------------

class TestBrief:
    """Tests for brief() command."""

    def test_brief_prints_summary(self, tmp_path, capsys):
        """brief() prints one-line summary with session count and pattern count."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb(
            sessions=[_make_session(), _make_session()],
            etalon={"version": "0.9.0", "test_count": 1634},
        )
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns = {"pattern1": {"count": 2, "fix_hint": "fix it"}}
        patterns_file.write_text(json.dumps(patterns), encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.brief()

        out = capsys.readouterr().out
        assert "2 sessions" in out
        assert "1 patterns" in out
        assert "1 auto-fix hints" in out


# ---------------------------------------------------------------------------
# stats() tests
# ---------------------------------------------------------------------------

class TestStats:
    """Tests for stats() command."""

    def test_stats_prints_totals(self, tmp_path, capsys):
        """stats() prints total sessions, clean count, total issues, trend."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb(
            sessions=[
                _make_session(issues=2),
                _make_session(ts="2026-04-02T10:00:00", issues=0),
            ],
        )
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns = {"p1": {"count": 1}}
        patterns_file.write_text(json.dumps(patterns), encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.stats()

        out = capsys.readouterr().out
        assert "Total sessions:" in out
        assert "2" in out
        assert "Clean sessions:" in out
        assert "1/2" in out
        assert "Total issues seen:" in out
        assert "improving" in out

    def test_stats_no_sessions(self, tmp_path, capsys):
        """stats() prints 'No sessions yet' when KB has no sessions."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb()
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns_file.write_text("{}", encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.stats()

        out = capsys.readouterr().out
        assert "No sessions yet" in out

    def test_stats_stable_trend(self, tmp_path, capsys):
        """stats() shows 'stable' trend when issues are not decreasing."""
        kb_file = tmp_path / "knowledge_base.json"
        patterns_file = tmp_path / "patterns.json"

        kb = _make_kb(
            sessions=[
                _make_session(issues=0),
                _make_session(ts="2026-04-02T10:00:00", issues=1),
            ],
        )
        kb_file.write_text(json.dumps(kb), encoding="utf-8")
        patterns_file.write_text("{}", encoding="utf-8")

        with patch.object(agent_learn, "KB_FILE", kb_file), \
             patch.object(agent_learn, "PATTERNS_FILE", patterns_file):
            agent_learn.stats()

        out = capsys.readouterr().out
        assert "stable" in out
