#!/usr/bin/env python3
"""Coverage tests for scripts/agent_coverage.py -- 20 tests."""

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agent_coverage import (  # noqa: E402
    extract_functions, get_function_coverage, load_pending_tasks,
)


# -- extract_functions ---------------------------------------------------------

class TestExtractFunctions:
    def test_empty_file_returns_empty(self, tmp_path):
        p = tmp_path / "empty.py"
        p.write_text("", encoding="utf-8")
        assert extract_functions(p) == []

    def test_single_function(self, tmp_path):
        p = tmp_path / "one.py"
        p.write_text("def hello():\n    return 1\n", encoding="utf-8")
        result = extract_functions(p)
        assert len(result) == 1
        assert result[0]["name"] == "hello"

    def test_two_functions(self, tmp_path):
        p = tmp_path / "two.py"
        p.write_text("def a():\n    pass\n\ndef b():\n    pass\n", encoding="utf-8")
        result = extract_functions(p)
        assert len(result) == 2

    def test_correct_fields(self, tmp_path):
        p = tmp_path / "fields.py"
        p.write_text("def foo(x):\n    return x\n", encoding="utf-8")
        result = extract_functions(p)
        func = result[0]
        assert "name" in func
        assert "start" in func
        assert "end" in func
        assert "indent" in func
        assert func["indent"] == 0

    def test_nonexistent_file_returns_empty(self, tmp_path):
        p = tmp_path / "no_such_file.py"
        assert extract_functions(p) == []

    def test_returns_list_of_dicts(self, tmp_path):
        p = tmp_path / "multi.py"
        p.write_text("def a():\n    pass\ndef b():\n    pass\n", encoding="utf-8")
        result = extract_functions(p)
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)

    def test_indented_method(self, tmp_path):
        p = tmp_path / "cls.py"
        p.write_text("class Foo:\n    def bar(self):\n        pass\n", encoding="utf-8")
        result = extract_functions(p)
        assert len(result) == 1
        assert result[0]["name"] == "bar"
        assert result[0]["indent"] == 4


# -- get_function_coverage -----------------------------------------------------

class TestGetFunctionCoverage:
    def test_empty_functions_returns_empty(self):
        assert get_function_coverage([], [1, 2], [3, 4]) == []

    def test_fully_covered_100(self):
        funcs = [{"name": "f", "start": 1, "end": 3, "indent": 0}]
        result = get_function_coverage(funcs, missing_lines=[], executed_lines=[1, 2, 3])
        assert len(result) == 1
        assert result[0]["coverage_pct"] == 100.0

    def test_zero_coverage(self):
        funcs = [{"name": "f", "start": 1, "end": 3, "indent": 0}]
        result = get_function_coverage(funcs, missing_lines=[1, 2, 3], executed_lines=[])
        assert len(result) == 1
        assert result[0]["coverage_pct"] == 0.0

    def test_partial_coverage(self):
        funcs = [{"name": "f", "start": 1, "end": 5, "indent": 0}]
        result = get_function_coverage(
            funcs, missing_lines=[3, 4, 5], executed_lines=[1, 2]
        )
        assert len(result) == 1
        assert result[0]["coverage_pct"] == 40.0

    def test_no_code_lines_skipped(self):
        """Function whose lines don't appear in either set -> skipped."""
        funcs = [{"name": "f", "start": 100, "end": 103, "indent": 0}]
        result = get_function_coverage(funcs, missing_lines=[1], executed_lines=[2])
        assert result == []

    def test_multiple_functions(self):
        funcs = [
            {"name": "a", "start": 1, "end": 2, "indent": 0},
            {"name": "b", "start": 3, "end": 4, "indent": 0},
        ]
        result = get_function_coverage(
            funcs, missing_lines=[3, 4], executed_lines=[1, 2]
        )
        assert len(result) == 2

    def test_all_fields_present(self):
        funcs = [{"name": "f", "start": 1, "end": 3, "indent": 0}]
        result = get_function_coverage(funcs, missing_lines=[2], executed_lines=[1, 3])
        r = result[0]
        assert "name" in r
        assert "start" in r
        assert "end" in r
        assert "total_lines" in r
        assert "covered_lines" in r
        assert "missing_lines" in r
        assert "coverage_pct" in r

    def test_rounding(self):
        funcs = [{"name": "f", "start": 1, "end": 3, "indent": 0}]
        result = get_function_coverage(
            funcs, missing_lines=[3], executed_lines=[1, 2]
        )
        assert result[0]["coverage_pct"] == 66.7


# -- load_pending_tasks --------------------------------------------------------

class TestLoadPendingTasks:
    def test_no_file_returns_empty(self, tmp_path):
        with patch("agent_coverage.REPO_ROOT", tmp_path):
            assert load_pending_tasks() == []

    def test_returns_pending_titles(self, tmp_path):
        content = (
            "# Tasks\n\n"
            "### TASK-001\n"
            "- **Title:** Fix the widget\n"
            "- **Status:** PENDING\n"
            "- **Description:** Broken widget\n"
        )
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_coverage.REPO_ROOT", tmp_path):
            result = load_pending_tasks()
        assert len(result) == 1
        assert "Fix the widget" in result[0]

    def test_skips_done_tasks(self, tmp_path):
        content = (
            "# Tasks\n\n"
            "### TASK-001\n"
            "- **Title:** Done task\n"
            "- **Status:** DONE (2026-01-01)\n"
            "- **Description:** Already done\n"
        )
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_coverage.REPO_ROOT", tmp_path):
            result = load_pending_tasks()
        assert result == []

    def test_returns_list(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text("# Tasks\n", encoding="utf-8")
        with patch("agent_coverage.REPO_ROOT", tmp_path):
            result = load_pending_tasks()
        assert isinstance(result, list)

    def test_multiple_pending(self, tmp_path):
        content = (
            "# Tasks\n\n"
            "### TASK-001\n"
            "- **Title:** First pending\n"
            "- **Status:** PENDING\n"
            "- **Description:** Desc1\n\n"
            "### TASK-002\n"
            "- **Title:** Second pending\n"
            "- **Status:** PENDING\n"
            "- **Description:** Desc2\n"
        )
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_coverage.REPO_ROOT", tmp_path):
            result = load_pending_tasks()
        assert len(result) == 2
