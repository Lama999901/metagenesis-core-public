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


# -- parse_report_date extended -----------------------------------------------

class TestParseReportDateExtended:
    def test_extracts_from_middle_of_filename(self):
        dt = agent_evolve_self.parse_report_date("WEEKLY_REPORT_20260319_v2.md")
        assert dt == datetime(2026, 3, 19)

    def test_multiple_date_groups_takes_first(self):
        dt = agent_evolve_self.parse_report_date("REPORT_20260101_20260202.md")
        assert dt == datetime(2026, 1, 1)

    def test_returns_none_for_no_digits(self):
        assert agent_evolve_self.parse_report_date("README.md") is None

    def test_returns_none_for_short_digits(self):
        assert agent_evolve_self.parse_report_date("report_123.md") is None


# -- analyze_reports extended -------------------------------------------------

class TestAnalyzeReportsExtended:
    def test_empty_reports_dir(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_reports()
        assert result == []

    def test_extracts_headers(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "AGENT_REPORT_20260401.md").write_text(
            "## Section A\n### Sub B\nSome text\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_reports()
        assert len(result) >= 1
        assert len(result[0]["headers"]) >= 2

    def test_extracts_task_ids(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "AGENT_REPORT_20260401.md").write_text(
            "Working on TASK-001 and TASK-002\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_reports()
        assert len(result) >= 1
        assert "TASK-001" in result[0]["task_ids"]
        assert "TASK-002" in result[0]["task_ids"]

    def test_extracts_file_paths(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "AGENT_REPORT_20260401.md").write_text(
            "Check `scripts/foo.py` for issues\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_reports()
        assert len(result) >= 1
        assert "scripts/foo.py" in result[0]["files_mentioned"]


# -- analyze_patterns extended ------------------------------------------------

class TestAnalyzePatternsExtended:
    def test_no_memory_dir(self, tmp_path):
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert all_p == [] and unadd == []

    def test_invalid_json(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        (mem / "patterns.json").write_text("not json!", encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert all_p == [] and unadd == []

    def test_all_with_hints(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        data = {"p1": {"count": 5, "fix_hint": "do x", "first_seen": "2026-01-01", "last_seen": "2026-03-01"}}
        (mem / "patterns.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert len(all_p) == 1
        assert unadd == []

    def test_count_one_with_no_hint(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        data = {"rare": {"count": 1, "fix_hint": "", "first_seen": "2026-01-01", "last_seen": "2026-01-01"}}
        (mem / "patterns.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert len(all_p) == 1
        assert unadd == []  # count < 2 threshold

    def test_first_seen_last_seen_preserved(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        data = {"bug": {"count": 3, "fix_hint": "fix it",
                        "first_seen": "2026-01-01", "last_seen": "2026-03-15"}}
        (mem / "patterns.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unadd = agent_evolve_self.analyze_patterns()
        assert all_p[0]["first_seen"] == "2026-01-01"
        assert all_p[0]["last_seen"] == "2026-03-15"


# -- analyze_handlers extended ------------------------------------------------

class TestAnalyzeHandlersExtended:
    def test_no_research_file(self, tmp_path):
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert result == []

    def test_complex_handler(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        lines = ["def execute_task_001():"] + ["    x = 1"] * 249
        (scripts / "agent_research.py").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert len(result) == 1
        assert result[0]["verdict"] == "COMPLEX"

    def test_multiple_handlers(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        # handler 1: 10 lines (SHALLOW)
        lines = ["def execute_task_001():"] + ["    x = 1"] * 9
        # handler 2: 100 lines (OK)
        lines += ["def execute_task_002():"] + ["    y = 2"] * 99
        (scripts / "agent_research.py").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert len(result) == 2

    def test_handler_start_line(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        content = "# header\n\ndef execute_task_001():\n    pass\n"
        (scripts / "agent_research.py").write_text(content, encoding="utf-8")
        with patch("agent_evolve_self.REPO_ROOT", tmp_path):
            result = agent_evolve_self.analyze_handlers()
        assert len(result) == 1
        assert result[0]["start"] == 3  # 1-indexed, line 3


# -- check_report_frequency extended ------------------------------------------

class TestCheckReportFrequencyExtended:
    def test_single_report(self):
        reports = [{"date": datetime(2026, 3, 1)}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert status == "insufficient data"

    def test_all_none_dates(self):
        reports = [{"date": None}, {"date": None}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert status == "insufficient data"

    def test_exactly_7_day_gap(self):
        d1 = datetime(2026, 3, 1)
        d2 = datetime(2026, 3, 8)
        reports = [{"date": d1}, {"date": d2}]
        status, gap = agent_evolve_self.check_report_frequency(reports)
        assert "healthy" in status
