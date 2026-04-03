#!/usr/bin/env python3
"""Coverage tests for agent_research.py write_report() and main() branches."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_research  # noqa: E402


# ---------------------------------------------------------------------------
# write_report() tests
# ---------------------------------------------------------------------------

class TestWriteReport:
    """Tests for write_report() function."""

    def test_write_report_creates_file(self, tmp_path, monkeypatch):
        """write_report() creates a report file in reports/ dir."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        task = {
            "id": "TASK-099",
            "title": "Test task",
            "description": "A test description",
            "priority": "P1",
        }
        result = agent_research.write_report(task, "Some findings here")
        assert result.exists()
        assert result.parent.name == "reports"

    def test_write_report_content_includes_task_fields(self, tmp_path, monkeypatch):
        """write_report() includes task title, description, priority, and findings."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        task = {
            "id": "TASK-042",
            "title": "Coverage gap analysis",
            "description": "Find uncovered functions",
            "priority": "P2",
        }
        findings = "Found 5 uncovered functions in scripts/"
        result = agent_research.write_report(task, findings)
        content = result.read_text(encoding="utf-8")
        assert "TASK-042" in content
        assert "Coverage gap analysis" in content
        assert "Find uncovered functions" in content
        assert "P2" in content
        assert findings in content

    def test_write_report_returns_path(self, tmp_path, monkeypatch):
        """write_report() returns Path to the created report."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        task = {"id": "TASK-001", "title": "T", "description": "D", "priority": "P1"}
        result = agent_research.write_report(task, "f")
        assert isinstance(result, Path)
        assert "AGENT_REPORT_" in result.name

    def test_write_report_creates_reports_dir(self, tmp_path, monkeypatch):
        """write_report() creates the reports/ directory if missing."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        reports_dir = tmp_path / "reports"
        assert not reports_dir.exists()
        task = {"id": "TASK-001", "title": "T", "description": "D", "priority": "P1"}
        agent_research.write_report(task, "findings")
        assert reports_dir.exists()

    def test_write_report_filename_pattern(self, tmp_path, monkeypatch):
        """write_report() uses AGENT_REPORT_YYYYMMDD.md pattern."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        task = {"id": "TASK-001", "title": "T", "description": "D", "priority": "P1"}
        result = agent_research.write_report(task, "f")
        import re
        assert re.match(r"AGENT_REPORT_\d{8}\.md", result.name)


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for main() entry point branches."""

    def test_main_no_tasks_file_exits_1(self, tmp_path, monkeypatch):
        """main() calls sys.exit(1) when AGENT_TASKS.md is missing."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            agent_research.main()
        assert exc_info.value.code == 1

    def test_main_no_pending_tasks_exits_0(self, tmp_path, monkeypatch):
        """main() calls sys.exit(0) when no PENDING tasks exist."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        tasks_file = tmp_path / "AGENT_TASKS.md"
        tasks_file.write_text(
            "# Agent Tasks\n\n### TASK-001\n"
            "- **Title:** Done task\n"
            "- **Status:** DONE (2026-01-01)\n"
            "- **Priority:** P1\n"
            "- **Output:** reports/test.md\n"
            "- **Description:** Already done\n",
            encoding="utf-8",
        )
        with pytest.raises(SystemExit) as exc_info:
            agent_research.main()
        assert exc_info.value.code == 0

    @patch.object(agent_research, "execute_task", return_value="findings text")
    @patch.object(agent_research, "generate_tasks", return_value=0)
    @patch.object(agent_research, "generate_coverage_tasks", return_value=0)
    @patch.object(agent_research, "weekly_report")
    @patch("subprocess.run")
    def test_main_executes_pending_task(
        self, mock_subproc, mock_weekly, mock_cov, mock_gen, mock_exec,
        tmp_path, monkeypatch
    ):
        """main() dispatches to execute_task, write_report, mark_task_done."""
        monkeypatch.setattr(agent_research, "REPO_ROOT", tmp_path)
        tasks_file = tmp_path / "AGENT_TASKS.md"
        tasks_file.write_text(
            "# Agent Tasks\n\n### TASK-001\n"
            "- **Title:** Pending task\n"
            "- **Status:** PENDING\n"
            "- **Priority:** P1\n"
            "- **Output:** reports/test.md\n"
            "- **Description:** A pending task\n",
            encoding="utf-8",
        )
        # main() calls sys.exit only on early returns; normal path just prints
        agent_research.main()
        mock_exec.assert_called_once()
        mock_gen.assert_called_once()
        mock_cov.assert_called_once()
        mock_weekly.assert_called_once()
