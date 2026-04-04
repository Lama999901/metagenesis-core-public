#!/usr/bin/env python3
"""Tests for agent_coverage.py analyze() run-path branches.

Targets uncovered branches: corrupt JSON, "Files Below 50%" report section,
"No zero-coverage" message, suggestion generation with dedup, and summary mode.
5 tests per COV-04.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_coverage as ac


def _setup_repo(tmp_path, agent_tasks_content=None):
    """Create minimal repo structure for analyze()."""
    (tmp_path / "reports").mkdir(exist_ok=True)
    scripts = tmp_path / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "agent_research.py").write_text(
        "def execute_task_001():\n    pass\n\ndef execute_task_002():\n    pass\n",
        encoding="utf-8",
    )
    (scripts / "agent_learn.py").write_text(
        "def observe():\n    pass\n\ndef brief():\n    pass\n",
        encoding="utf-8",
    )
    if agent_tasks_content is None:
        agent_tasks_content = "# Tasks\n"
    (tmp_path / "AGENT_TASKS.md").write_text(agent_tasks_content, encoding="utf-8")


def _make_coverage_json(tmp_path, overall_pct=65.0, files_data=None):
    """Create a fake coverage.json."""
    if files_data is None:
        files_data = {}
    cov = {
        "totals": {"percent_covered": overall_pct},
        "files": files_data,
    }
    (tmp_path / "coverage.json").write_text(json.dumps(cov), encoding="utf-8")


class TestAnalyzeRunBranches:
    def test_corrupt_coverage_json_returns_1(self, tmp_path):
        """analyze() returns 1 when coverage.json is corrupt."""
        _setup_repo(tmp_path)
        (tmp_path / "coverage.json").write_text("NOT VALID JSON{{{", encoding="utf-8")

        with patch.object(ac, "REPO_ROOT", tmp_path), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            result = ac.analyze()
        assert result == 1

    def test_report_includes_files_below_50(self, tmp_path):
        """analyze() report has 'Files Below 50%' section when applicable."""
        _setup_repo(tmp_path)
        files_data = {
            "scripts/agent_research.py": {
                "summary": {"percent_covered": 14.0},
                "missing_lines": list(range(1, 5)),
                "executed_lines": [],
            },
        }
        _make_coverage_json(tmp_path, overall_pct=65.0, files_data=files_data)

        with patch.object(ac, "REPO_ROOT", tmp_path), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"COVERAGE_REPORT_{today}.md").read_text(encoding="utf-8")
        assert "Files Below 50% Coverage" in report
        assert "agent_research.py" in report

    def test_no_zero_coverage_message(self, tmp_path):
        """analyze() report shows 'no zero-coverage' when all functions covered."""
        _setup_repo(tmp_path)
        files_data = {
            "scripts/agent_learn.py": {
                "summary": {"percent_covered": 80.0},
                "missing_lines": [],
                "executed_lines": list(range(1, 10)),
            },
        }
        _make_coverage_json(tmp_path, overall_pct=80.0, files_data=files_data)

        with patch.object(ac, "REPO_ROOT", tmp_path), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"COVERAGE_REPORT_{today}.md").read_text(encoding="utf-8")
        assert "No zero-coverage" in report or "well-tested" in report

    def test_suggestions_generated_for_zero_coverage(self, tmp_path):
        """analyze() generates suggestions for zero-coverage functions not in tasks."""
        _setup_repo(tmp_path)
        files_data = {
            "scripts/agent_research.py": {
                "summary": {"percent_covered": 0.0},
                "missing_lines": [1, 2, 3, 4, 5],
                "executed_lines": [],
            },
        }
        _make_coverage_json(tmp_path, overall_pct=65.0, files_data=files_data)

        with patch.object(ac, "REPO_ROOT", tmp_path), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (tmp_path / "reports" / f"COVERAGE_REPORT_{today}.md").read_text(encoding="utf-8")
        assert "Suggested Tasks" in report

    def test_summary_mode_compact_output(self, tmp_path, capsys):
        """analyze() --summary prints compact one-liner with coverage percentage."""
        _setup_repo(tmp_path)
        _make_coverage_json(tmp_path, overall_pct=72.5, files_data={})

        with patch.object(ac, "REPO_ROOT", tmp_path), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py", "--summary"]):
            ac.analyze()

        out = capsys.readouterr().out
        assert "72.5%" in out
        assert "zero-cov" in out
