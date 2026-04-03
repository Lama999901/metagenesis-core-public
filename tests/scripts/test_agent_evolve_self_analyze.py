#!/usr/bin/env python3
"""Tests for agent_evolve_self.py analyze() end-to-end flow.

Targets uncovered orchestration in analyze() (lines 209-375):
report generation, recommendation building, handler analysis,
recurring themes, summary mode, empty state, and frequency warnings.
7 tests per COV-02.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_evolve_self as aes


def _setup_repo(tmp_path, reports=None, patterns=None, handler_lines=60):
    """Create a minimal repo structure for analyze().

    Args:
        reports: list of (filename, content) tuples for reports/
        patterns: dict for .agent_memory/patterns.json
        handler_lines: number of lines per handler in agent_research.py
    """
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(exist_ok=True)

    if reports:
        for fname, content in reports:
            (reports_dir / fname).write_text(content, encoding="utf-8")

    if patterns is not None:
        mem = tmp_path / ".agent_memory"
        mem.mkdir(exist_ok=True)
        (mem / "patterns.json").write_text(json.dumps(patterns), encoding="utf-8")

    scripts = tmp_path / "scripts"
    scripts.mkdir(exist_ok=True)
    lines = ["def execute_task_001():"] + ["    x = 1"] * (handler_lines - 1)
    (scripts / "agent_research.py").write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestAnalyzeEndToEnd:
    def test_produces_report_with_history_section(self, tmp_path):
        """analyze() produces report with 'Agent Report History' section."""
        _setup_repo(
            tmp_path,
            reports=[
                ("AGENT_REPORT_20260318.md", "## Check A\n- Finding one\n- Finding two\n"),
                ("AGENT_REPORT_20260319.md", "## Check B\n- Finding three\n"),
            ],
        )

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            result = aes.analyze()

        assert result == 0
        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"SELF_IMPROVEMENT_{today}.md").read_text(encoding="utf-8")
        assert "Agent Report History" in report
        assert "Total reports" in report

    def test_includes_handler_analysis(self, tmp_path):
        """analyze() report includes handler analysis with verdict."""
        _setup_repo(tmp_path, handler_lines=10)  # SHALLOW

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            aes.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"SELF_IMPROVEMENT_{today}.md").read_text(encoding="utf-8")
        assert "Handler Analysis" in report
        assert "SHALLOW" in report

    def test_includes_recommendations_from_unaddressed_patterns(self, tmp_path):
        """analyze() generates recommendations from unaddressed patterns."""
        _setup_repo(
            tmp_path,
            patterns={
                "windows_crash": {
                    "count": 5,
                    "fix_hint": "",
                    "first_seen": "2026-01-01",
                    "last_seen": "2026-03-01",
                },
            },
        )

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            aes.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"SELF_IMPROVEMENT_{today}.md").read_text(encoding="utf-8")
        assert "Recommendations" in report
        assert "windows_crash" in report
        assert "fix_hint" in report or "auto-fix" in report

    def test_recurring_themes_when_headers_repeat(self, tmp_path):
        """analyze() includes recurring themes when headers appear across reports."""
        _setup_repo(
            tmp_path,
            reports=[
                ("AGENT_REPORT_20260318.md", "## Coverage Gaps\n- gap one\n"),
                ("AGENT_REPORT_20260319.md", "## Coverage Gaps\n- gap two\n"),
                ("WEEKLY_REPORT_20260319.md", "## Summary\n- done\n"),
            ],
        )

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            aes.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"SELF_IMPROVEMENT_{today}.md").read_text(encoding="utf-8")
        assert "Recurring Themes" in report
        assert "coverage gaps" in report.lower()

    def test_summary_mode_prints_compact_line(self, tmp_path, capsys):
        """analyze() --summary prints compact one-liner."""
        _setup_repo(
            tmp_path,
            reports=[
                ("AGENT_REPORT_20260318.md", "## Check\n- finding\n"),
            ],
        )

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py", "--summary"]):
            aes.analyze()

        out = capsys.readouterr().out
        assert "reports" in out
        assert "handlers" in out
        assert "recommendations" in out

    def test_empty_state_no_critical_issues(self, tmp_path):
        """analyze() with no reports/patterns/handlers produces 'no critical issues'."""
        _setup_repo(tmp_path)
        # Remove agent_research.py to get no handlers
        (tmp_path / "scripts" / "agent_research.py").unlink()

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            aes.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"SELF_IMPROVEMENT_{today}.md").read_text(encoding="utf-8")
        assert "No critical issues" in report or "evolves well" in report

    def test_report_frequency_warning_when_gap_exceeds_7_days(self, tmp_path):
        """analyze() report includes frequency warning when max gap > 7 days."""
        _setup_repo(
            tmp_path,
            reports=[
                ("AGENT_REPORT_20260101.md", "## Check\n- finding\n"),
                ("AGENT_REPORT_20260120.md", "## Check\n- finding\n"),
            ],
        )

        with patch.object(aes, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            aes.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"SELF_IMPROVEMENT_{today}.md").read_text(encoding="utf-8")
        assert "WARNING" in report or "gap" in report.lower()
