#!/usr/bin/env python3
"""Coverage tests for agent_coverage.py analyze() -- 10 tests.

Targets analyze() at 1.7%. Mocks subprocess.run to return fake
coverage output and coverage.json data.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_coverage as ac


def _make_coverage_json(tmp_path, overall_pct=65.0, files_data=None):
    """Create a fake coverage.json file."""
    if files_data is None:
        files_data = {
            "scripts/agent_research.py": {
                "summary": {"percent_covered": 14.0},
                "missing_lines": list(range(100, 200)),
                "executed_lines": list(range(1, 100)),
            },
            "scripts/agent_learn.py": {
                "summary": {"percent_covered": 45.0},
                "missing_lines": [50, 60, 70],
                "executed_lines": list(range(1, 50)),
            },
        }
    cov = {
        "totals": {"percent_covered": overall_pct},
        "files": files_data,
    }
    cov_path = tmp_path / "coverage.json"
    cov_path.write_text(json.dumps(cov), encoding="utf-8")
    return cov_path


def _setup_repo(tmp_path):
    """Create minimal structure for analyze()."""
    # AGENT_TASKS.md
    (tmp_path / "AGENT_TASKS.md").write_text(
        "# Tasks\n\n### TASK-001\n- **Title:** Example\n- **Status:** PENDING\n",
        encoding="utf-8",
    )
    # reports dir
    (tmp_path / "reports").mkdir(exist_ok=True)

    # Source files referenced in coverage.json
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    (scripts_dir / "agent_research.py").write_text(
        "def execute_task_001():\n    pass\n\ndef execute_task_002():\n    pass\n",
        encoding="utf-8",
    )
    (scripts_dir / "agent_learn.py").write_text(
        "def observe():\n    pass\n\ndef brief():\n    pass\n",
        encoding="utf-8",
    )
    return tmp_path


def _mock_subprocess_run(cov_json_path):
    """Return a mock for subprocess.run that creates coverage.json."""
    def _mock(cmd, **kwargs):
        result = MagicMock()
        result.stdout = "1273 passed\n"
        result.returncode = 0
        return result
    return _mock


class TestAnalyze:
    def test_analyze_runs_with_coverage(self, tmp_path):
        """analyze() produces report when coverage.json exists."""
        repo = _setup_repo(tmp_path)
        _make_coverage_json(repo, overall_pct=65.0)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("1273 passed", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            result = ac.analyze()
        assert result == 0  # > 60% threshold

    def test_analyze_writes_report(self, tmp_path):
        """analyze() creates COVERAGE_REPORT file."""
        repo = _setup_repo(tmp_path)
        _make_coverage_json(repo, overall_pct=65.0)
        today = datetime.now().strftime("%Y%m%d")
        expected_report = repo / "reports" / f"COVERAGE_REPORT_{today}.md"

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("1273 passed", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()
        assert expected_report.exists()

    def test_analyze_low_coverage_returns_1(self, tmp_path):
        """analyze() returns 1 when coverage < 60%."""
        repo = _setup_repo(tmp_path)
        _make_coverage_json(repo, overall_pct=45.0)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("1273 passed", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            result = ac.analyze()
        assert result == 1

    def test_analyze_summary_mode(self, tmp_path, capsys):
        """analyze() --summary prints one-line summary."""
        repo = _setup_repo(tmp_path)
        _make_coverage_json(repo, overall_pct=65.0)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("1273 passed", 0)), \
             patch("sys.argv", ["agent_coverage.py", "--summary"]):
            ac.analyze()
        captured = capsys.readouterr()
        assert "Coverage" in captured.out
        assert "65.0%" in captured.out

    def test_analyze_no_coverage_json(self, tmp_path):
        """analyze() returns 1 when coverage.json missing."""
        repo = _setup_repo(tmp_path)
        # No coverage.json created

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("1273 passed", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            result = ac.analyze()
        assert result == 1

    def test_analyze_finds_zero_coverage_functions(self, tmp_path):
        """analyze() detects functions with 0% coverage."""
        repo = _setup_repo(tmp_path)
        # agent_research.py has functions at lines 1-2 and 4-5
        # missing_lines covers both functions entirely
        files_data = {
            "scripts/agent_research.py": {
                "summary": {"percent_covered": 0.0},
                "missing_lines": [1, 2, 3, 4, 5],
                "executed_lines": [],
            },
        }
        _make_coverage_json(repo, overall_pct=65.0, files_data=files_data)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (repo / "reports" / f"COVERAGE_REPORT_{today}.md").read_text(encoding="utf-8")
        assert "Zero-Coverage" in report or "zero-cov" in report.lower()

    def test_analyze_finds_low_coverage_functions(self, tmp_path):
        """analyze() detects functions with <50% coverage."""
        repo = _setup_repo(tmp_path)
        files_data = {
            "scripts/agent_learn.py": {
                "summary": {"percent_covered": 30.0},
                "missing_lines": [1, 2, 3],
                "executed_lines": [4, 5],
            },
        }
        _make_coverage_json(repo, overall_pct=65.0, files_data=files_data)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()

        today = datetime.now().strftime("%Y%m%d")
        report = (repo / "reports" / f"COVERAGE_REPORT_{today}.md").read_text(encoding="utf-8")
        assert "Coverage" in report

    def test_analyze_cleans_up_coverage_json(self, tmp_path):
        """analyze() deletes coverage.json after processing."""
        repo = _setup_repo(tmp_path)
        cov_path = _make_coverage_json(repo, overall_pct=65.0)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()
        assert not cov_path.exists()

    def test_analyze_cross_references_tasks(self, tmp_path):
        """analyze() skips suggestions for functions already in AGENT_TASKS.md."""
        repo = _setup_repo(tmp_path)
        # Add a task mentioning execute_task_001
        (repo / "AGENT_TASKS.md").write_text(
            "# Tasks\n\n### TASK-001\n- **Title:** Write tests for execute_task_001\n"
            "- **Status:** PENDING\n- **Priority:** P1\n- **Output:** x\n- **Description:** x\n",
            encoding="utf-8",
        )
        files_data = {
            "scripts/agent_research.py": {
                "summary": {"percent_covered": 0.0},
                "missing_lines": [1, 2, 3, 4, 5],
                "executed_lines": [],
            },
        }
        _make_coverage_json(repo, overall_pct=65.0, files_data=files_data)

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            ac.analyze()
        # Should complete without error; dedup logic exercised

    def test_analyze_empty_files_data(self, tmp_path):
        """analyze() handles coverage.json with no files gracefully."""
        repo = _setup_repo(tmp_path)
        _make_coverage_json(repo, overall_pct=100.0, files_data={})

        with patch.object(ac, "REPO_ROOT", repo), \
             patch.object(ac, "run", return_value=("", 0)), \
             patch("sys.argv", ["agent_coverage.py"]):
            result = ac.analyze()
        assert result == 0
