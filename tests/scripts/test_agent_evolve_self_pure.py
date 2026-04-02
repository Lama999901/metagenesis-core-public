"""Tests for scripts/agent_evolve_self.py — 20 pure/patched tests."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_evolve_self


# ── parse_report_date ───────────────────────────────────────────────────────

class TestParseReportDate:
    def test_agent_report(self):
        dt = agent_evolve_self.parse_report_date("AGENT_REPORT_20260319.md")
        assert dt == datetime(2026, 3, 19)

    def test_weekly_report(self):
        dt = agent_evolve_self.parse_report_date("WEEKLY_REPORT_20260101.md")
        assert dt == datetime(2026, 1, 1)

    def test_no_date(self):
        assert agent_evolve_self.parse_report_date("README.md") is None

    def test_empty(self):
        assert agent_evolve_self.parse_report_date("") is None

    def test_invalid_date(self):
        # 13th month — ValueError in strptime
        assert agent_evolve_self.parse_report_date("REPORT_20261301.md") is None

    def test_returns_datetime_type(self):
        result = agent_evolve_self.parse_report_date("X_20260315.md")
        assert isinstance(result, datetime)


# ── check_report_frequency ──────────────────────────────────────────────────

class TestCheckReportFrequency:
    def test_empty_list(self):
        status, gap = agent_evolve_self.check_report_frequency([])
        assert status == "insufficient data"
        assert gap == 0

    def test_single_report(self):
        reports = [{"date": datetime(2026, 3, 1)}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert status == "insufficient data"

    def test_healthy_frequency(self):
        d1 = datetime(2026, 3, 1)
        d2 = datetime(2026, 3, 3)
        d3 = datetime(2026, 3, 5)
        reports = [{"date": d1}, {"date": d2}, {"date": d3}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert "healthy" in status
        assert gap == 2

    def test_large_gap_warning(self):
        d1 = datetime(2026, 1, 1)
        d2 = datetime(2026, 1, 20)
        reports = [{"date": d1}, {"date": d2}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert "WARNING" in status
        assert gap == 19

    def test_tuple_of_dates(self):
        """Reports with a mix of None and real dates."""
        reports = [{"date": None}, {"date": datetime(2026, 3, 1)},
                   {"date": datetime(2026, 3, 4)}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert "healthy" in status

    def test_none_dates_filtered(self):
        reports = [{"date": None}, {"date": None}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert status == "insufficient data"


# ── analyze_patterns ────────────────────────────────────────────────────────

class TestAnalyzePatterns:
    def test_no_file(self, tmp_path):
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert all_p == []
        assert unadd == []

    def test_empty_json(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        (mem / "patterns.json").write_text("{}", encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert all_p == []
        assert unadd == []

    def test_with_hint_not_unaddressed(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        data = {"stale_docs": {"count": 5, "fix_hint": "run stale check",
                                "first_seen": "2026-01-01", "last_seen": "2026-03-01"}}
        (mem / "patterns.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert len(all_p) == 1
        assert all_p[0]["has_hint"] is True
        assert unadd == []

    def test_without_hint_unaddressed(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        data = {"windows_crash": {"count": 3, "fix_hint": "",
                                   "first_seen": "2026-01-01", "last_seen": "2026-03-01"}}
        (mem / "patterns.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert len(unadd) == 1
        assert unadd[0]["pattern"] == "windows_crash"

    def test_count_one_not_unaddressed(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        data = {"rare_bug": {"count": 1, "fix_hint": "",
                              "first_seen": "2026-01-01", "last_seen": "2026-03-01"}}
        (mem / "patterns.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert len(all_p) == 1
        assert unadd == []


# ── analyze_handlers ────────────────────────────────────────────────────────

class TestAnalyzeHandlers:
    def test_no_file(self, tmp_path):
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert result == []

    def test_shallow_handler(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        # 10 lines < 50 → SHALLOW
        lines = ["def execute_task_001():"] + ["    pass"] * 9
        (scripts / "agent_research.py").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert len(result) == 1
        assert result[0]["verdict"] == "SHALLOW"
        assert result[0]["name"] == "execute_task_001"

    def test_ok_handler(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        # 100 lines: 50 <= 100 <= 200 → OK
        lines = ["def execute_task_002():"] + ["    x = 1"] * 99
        (scripts / "agent_research.py").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert len(result) == 1
        assert result[0]["verdict"] == "OK"
