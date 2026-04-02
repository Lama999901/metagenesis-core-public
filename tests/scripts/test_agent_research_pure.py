#!/usr/bin/env python3
"""Coverage tests for scripts/agent_research.py -- 20 tests."""

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agent_research import (  # noqa: E402
    parse_tasks, find_first_pending, mark_task_done,
    generate_tasks, generate_coverage_tasks,
)

SAMPLE_TASKS = """# Agent Tasks

### TASK-001
- **Title:** Test task one
- **Status:** DONE (2026-03-01)
- **Priority:** P1
- **Output:** reports/test.md
- **Description:** First task

### TASK-002
- **Title:** Test task two
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/test2.md
- **Description:** Second task

### TASK-003
- **Title:** Test task three
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/test3.md
- **Description:** Third task
"""


# -- parse_tasks ---------------------------------------------------------------

class TestParseTasks:
    def test_parse_tasks_returns_list(self):
        result = parse_tasks(SAMPLE_TASKS)
        assert len(result) == 3

    def test_parse_tasks_extracts_id(self):
        result = parse_tasks(SAMPLE_TASKS)
        assert result[0]["id"] == "TASK-001"

    def test_parse_tasks_extracts_title(self):
        result = parse_tasks(SAMPLE_TASKS)
        assert result[0]["title"] == "Test task one"

    def test_parse_tasks_extracts_status_done(self):
        result = parse_tasks(SAMPLE_TASKS)
        assert result[0]["status"] == "DONE (2026-03-01)"

    def test_parse_tasks_extracts_status_pending(self):
        result = parse_tasks(SAMPLE_TASKS)
        assert result[1]["status"] == "PENDING"

    def test_parse_tasks_empty_content_returns_empty(self):
        assert parse_tasks("") == []

    def test_parse_tasks_no_valid_tasks_returns_empty(self):
        assert parse_tasks("# Heading\nsome content\n") == []


# -- find_first_pending --------------------------------------------------------

class TestFindFirstPending:
    def test_find_first_pending_finds_task002(self):
        tasks = parse_tasks(SAMPLE_TASKS)
        result = find_first_pending(tasks)
        assert result is not None
        assert result["id"] == "TASK-002"

    def test_find_first_pending_none_when_all_done(self):
        tasks = [{"id": "T-1", "status": "DONE (2026-01-01)"}]
        assert find_first_pending(tasks) is None

    def test_find_first_pending_empty_list(self):
        assert find_first_pending([]) is None

    def test_find_first_pending_case_insensitive(self):
        """find_first_pending uses .upper() so lowercase 'pending' should match."""
        tasks = [{"id": "T-1", "status": "pending"}]
        result = find_first_pending(tasks)
        assert result is not None


# -- mark_task_done ------------------------------------------------------------

class TestMarkTaskDone:
    def test_mark_task_done_updates_file(self, tmp_path):
        p = tmp_path / "AGENT_TASKS.md"
        p.write_text(SAMPLE_TASKS, encoding="utf-8")
        mark_task_done("TASK-002", p)
        updated = p.read_text(encoding="utf-8")
        # TASK-002 should now say DONE
        assert "TASK-002" in updated
        # Check PENDING replaced with DONE for TASK-002
        task002_section = updated[updated.index("### TASK-002"):updated.index("### TASK-003")]
        assert "DONE" in task002_section

    def test_mark_task_done_preserves_other_tasks(self, tmp_path):
        p = tmp_path / "AGENT_TASKS.md"
        p.write_text(SAMPLE_TASKS, encoding="utf-8")
        mark_task_done("TASK-002", p)
        updated = p.read_text(encoding="utf-8")
        assert "TASK-001" in updated
        assert "TASK-003" in updated

    def test_mark_task_done_works_with_multiple_tasks(self, tmp_path):
        p = tmp_path / "AGENT_TASKS.md"
        p.write_text(SAMPLE_TASKS, encoding="utf-8")
        mark_task_done("TASK-003", p)
        updated = p.read_text(encoding="utf-8")
        task003_section = updated[updated.index("### TASK-003"):]
        assert "DONE" in task003_section


# -- generate_tasks ------------------------------------------------------------

class TestGenerateTasks:
    def test_generate_tasks_no_patterns_file_returns_zero(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            assert generate_tasks(tasks_path) == 0

    def test_generate_tasks_empty_patterns_returns_zero(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        (mem / "patterns.json").write_text("{}", encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            assert generate_tasks(tasks_path) == 0

    def test_generate_tasks_adds_task_for_unaddressed_pattern(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        patterns = {
            "recurring_encoding_error_on_windows_cp1252": {
                "count": 3,
                "fix_hint": "",
            }
        }
        (mem / "patterns.json").write_text(json.dumps(patterns), encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            result = generate_tasks(tasks_path)
        assert result == 1

    def test_generate_tasks_skips_pattern_with_hint(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        patterns = {
            "some_pattern_key_for_testing_purposes": {
                "count": 5,
                "fix_hint": "use GSD",
            }
        }
        (mem / "patterns.json").write_text(json.dumps(patterns), encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            assert generate_tasks(tasks_path) == 0

    def test_generate_tasks_returns_correct_count(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        patterns = {
            "pattern_alpha_long_key_for_uniqueness_test": {"count": 2, "fix_hint": ""},
            "pattern_beta_long_key_for_uniqueness_tests": {"count": 3, "fix_hint": ""},
        }
        (mem / "patterns.json").write_text(json.dumps(patterns), encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            result = generate_tasks(tasks_path)
        assert result == 2


# -- generate_coverage_tasks ---------------------------------------------------

class TestGenerateCoverageTasks:
    def test_generate_coverage_tasks_no_report_returns_zero(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            assert generate_coverage_tasks(tasks_path) == 0

    def test_generate_coverage_tasks_no_zero_section_returns_zero(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "COVERAGE_REPORT_20260401.md").write_text(
            "# Coverage\n## Summary\nAll good\n", encoding="utf-8"
        )
        with patch("agent_research.REPO_ROOT", tmp_path):
            assert generate_coverage_tasks(tasks_path) == 0

    def test_generate_coverage_tasks_with_excluded_file_returns_zero(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        reports = tmp_path / "reports"
        reports.mkdir()
        report = (
            "# Coverage\n"
            "## Zero-Coverage Functions\n\n"
            "| File | Function | Lines |\n"
            "|------|----------|-------|\n"
            "| `scripts/agent_evolution.py` | `func_a` | 1-10 |\n"
            "| `scripts/agent_evolution.py` | `func_b` | 11-20 |\n"
        )
        (reports / "COVERAGE_REPORT_20260401.md").write_text(report, encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            assert generate_coverage_tasks(tasks_path) == 0

    def test_generate_coverage_tasks_with_non_excluded_file(self, tmp_path):
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text("# Tasks\n", encoding="utf-8")
        reports = tmp_path / "reports"
        reports.mkdir()
        report = (
            "# Coverage\n"
            "## Zero-Coverage Functions\n\n"
            "| File | Function | Lines |\n"
            "|------|----------|-------|\n"
            "| `backend/ledger/models.py` | `func_a` | 1-10 |\n"
            "| `backend/ledger/models.py` | `func_b` | 11-20 |\n"
        )
        (reports / "COVERAGE_REPORT_20260401.md").write_text(report, encoding="utf-8")
        with patch("agent_research.REPO_ROOT", tmp_path):
            result = generate_coverage_tasks(tasks_path)
        assert result == 1
