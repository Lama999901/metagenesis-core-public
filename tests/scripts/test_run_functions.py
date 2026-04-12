"""Coverage boost v14: tests for run(), main(), and low-coverage functions
across agent scripts. Mocks subprocess.run to avoid real processes."""

import sys
import types
import json
import re
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_completed_process(stdout="", returncode=0, stderr=""):
    cp = MagicMock()
    cp.stdout = stdout
    cp.returncode = returncode
    cp.stderr = stderr
    return cp


# ===========================================================================
# 1. agent_coverage.py  (analyze function, lines 276-328)
# ===========================================================================

class TestAgentCoverageAnalyze:
    """Tests targeting agent_coverage.py analyze() at ~88% coverage."""

    def test_analyze_with_coverage_json(self, tmp_path):
        """Test analyze() report generation with mocked coverage.json."""
        from scripts.agent_coverage import analyze
        cov_json = {
            "totals": {"percent_covered": 75.0},
            "files": {
                "scripts/foo.py": {
                    "summary": {"percent_covered": 0.0, "missing_lines": 5,
                                "covered_lines": 0, "num_statements": 10},
                    "missing_lines": [1, 2, 3, 4, 5],
                    "executed_lines": [],
                }
            }
        }
        with patch("scripts.agent_coverage.REPO_ROOT", tmp_path), \
             patch("scripts.agent_coverage.run") as mock_run, \
             patch("sys.argv", ["agent_coverage.py", "--summary"]):
            mock_run.return_value = ("10 passed", 0)
            (tmp_path / "reports").mkdir()
            (tmp_path / "coverage.json").write_text(json.dumps(cov_json))
            # Also mock AGENT_TASKS.md existence
            (tmp_path / "AGENT_TASKS.md").write_text("# Tasks\n")
            result = analyze()
            assert result in (0, 1)

    def test_analyze_no_coverage_json(self, tmp_path, capsys):
        """Test analyze() when coverage.json does not exist."""
        from scripts.agent_coverage import analyze
        with patch("scripts.agent_coverage.REPO_ROOT", tmp_path), \
             patch("scripts.agent_coverage.run") as mock_run, \
             patch("sys.argv", ["agent_coverage.py", "--summary"]):
            mock_run.return_value = ("10 passed", 0)
            (tmp_path / "reports").mkdir()
            # No coverage.json created
            result = analyze()
            assert result == 1  # Should fail


# ===========================================================================
# 2. agent_diff_review.py  (run, get_old_source, main)
# ===========================================================================

class TestAgentDiffReview:
    """Tests for agent_diff_review.py run(), get_old_source(), main()."""

    def test_run_returns_stdout_and_code(self):
        from scripts.agent_diff_review import run
        with patch("scripts.agent_diff_review.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("hello world", 0)
            out, code = run("echo hi")
            assert code == 0
            assert "hello world" in out

    def test_run_failure_returns_nonzero(self):
        from scripts.agent_diff_review import run
        with patch("scripts.agent_diff_review.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("", 1)
            out, code = run("false")
            assert code == 1

    def test_get_old_source_success(self):
        from scripts.agent_diff_review import get_old_source
        with patch("scripts.agent_diff_review.run") as mock_run:
            mock_run.return_value = ("def foo(): pass", 0)
            result = get_old_source("scripts/foo.py")
            assert result == "def foo(): pass"

    def test_get_old_source_not_found(self):
        from scripts.agent_diff_review import get_old_source
        with patch("scripts.agent_diff_review.run") as mock_run:
            mock_run.return_value = ("", 128)
            result = get_old_source("scripts/nonexistent.py")
            assert result is None

    def test_main_no_changes(self):
        from scripts.agent_diff_review import main
        with patch("scripts.agent_diff_review.get_changed_py_files", return_value=[]), \
             patch("sys.argv", ["agent_diff_review.py"]):
            result = main()
            assert result == 0

    def test_main_summary_mode_pass(self):
        from scripts.agent_diff_review import main
        with patch("scripts.agent_diff_review.get_changed_py_files", return_value=["scripts/foo.py"]), \
             patch("scripts.agent_diff_review.review_file", return_value=[]), \
             patch("sys.argv", ["agent_diff_review.py", "--summary"]):
            result = main()
            assert result == 0

    def test_main_summary_mode_fail(self):
        from scripts.agent_diff_review import main
        with patch("scripts.agent_diff_review.get_changed_py_files", return_value=["scripts/foo.py"]), \
             patch("scripts.agent_diff_review.review_file", return_value=["issue1"]), \
             patch("sys.argv", ["agent_diff_review.py", "--summary"]):
            result = main()
            assert result == 1

    def test_main_full_output_with_issues(self, capsys):
        from scripts.agent_diff_review import main
        with patch("scripts.agent_diff_review.get_changed_py_files", return_value=["a.py"]), \
             patch("scripts.agent_diff_review.review_file", return_value=["public func removed"]), \
             patch("sys.argv", ["agent_diff_review.py"]):
            result = main()
            assert result == 1
            captured = capsys.readouterr()
            assert "issue" in captured.out.lower() or "ISSUES" in captured.out


# ===========================================================================
# 3. agent_evolve_self.py  (run, analyze, parse_report_date, etc.)
# ===========================================================================

class TestAgentEvolveSelf:
    """Tests for agent_evolve_self.py run(), analyze(), helper functions."""

    def test_run_returns_tuple(self):
        from scripts.agent_evolve_self import run
        with patch("scripts.agent_evolve_self.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("ok", 0)
            out, code = run("echo ok")
            assert out == "ok"
            assert code == 0

    def test_parse_report_date_valid(self):
        from scripts.agent_evolve_self import parse_report_date
        result = parse_report_date("AGENT_REPORT_20260319.md")
        assert result is not None
        assert result.year == 2026
        assert result.month == 3

    def test_parse_report_date_invalid(self):
        from scripts.agent_evolve_self import parse_report_date
        result = parse_report_date("README.md")
        assert result is None

    def test_analyze_reports_empty(self, tmp_path):
        from scripts.agent_evolve_self import analyze_reports
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path):
            (tmp_path / "reports").mkdir()
            result = analyze_reports()
            assert result == []

    def test_analyze_reports_with_files(self, tmp_path):
        from scripts.agent_evolve_self import analyze_reports
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        (reports_dir / "AGENT_REPORT_20260319.md").write_text(
            "# Report\n- Finding 1\n- TASK-001 mentioned\n`scripts/mg.py`\n",
            encoding="utf-8"
        )
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path):
            result = analyze_reports()
            assert len(result) == 1
            assert result[0]["task_ids"] == ["TASK-001"]

    def test_analyze_patterns_missing_file(self, tmp_path):
        from scripts.agent_evolve_self import analyze_patterns
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unaddr = analyze_patterns()
            assert all_p == []
            assert unaddr == []

    def test_analyze_patterns_with_data(self, tmp_path):
        from scripts.agent_evolve_self import analyze_patterns
        mem_dir = tmp_path / ".agent_memory"
        mem_dir.mkdir()
        patterns = {
            "stale count": {"count": 3, "fix_hint": "", "first_seen": "2026-01-01", "last_seen": "2026-03-01"},
            "ok pattern": {"count": 1, "fix_hint": "do X", "first_seen": "2026-01-01", "last_seen": "2026-03-01"},
        }
        (mem_dir / "patterns.json").write_text(json.dumps(patterns))
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path):
            all_p, unaddr = analyze_patterns()
            assert len(all_p) == 2
            assert len(unaddr) == 1  # stale count has no fix_hint

    def test_analyze_handlers(self, tmp_path):
        from scripts.agent_evolve_self import analyze_handlers
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "agent_research.py").write_text(
            "def execute_task_001():\n    pass\n\ndef execute_task_002():\n    x = 1\n    return x\n\ndef other():\n    pass\n",
            encoding="utf-8"
        )
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path):
            handlers = analyze_handlers()
            assert len(handlers) == 2
            assert handlers[0]["name"] == "execute_task_001"

    def test_check_report_frequency_insufficient(self):
        from scripts.agent_evolve_self import check_report_frequency
        reports = [{"date": None}]
        status, gap = check_report_frequency(reports)
        assert "insufficient" in status

    def test_check_report_frequency_healthy(self):
        from scripts.agent_evolve_self import check_report_frequency
        d1 = datetime(2026, 3, 1)
        d2 = datetime(2026, 3, 3)
        d3 = datetime(2026, 3, 5)
        reports = [{"date": d1}, {"date": d2}, {"date": d3}]
        status, gap = check_report_frequency(reports)
        assert "healthy" in status
        assert gap == 2

    def test_check_report_frequency_stale(self):
        from scripts.agent_evolve_self import check_report_frequency
        d1 = datetime(2026, 1, 1)
        d2 = datetime(2026, 1, 15)
        reports = [{"date": d1}, {"date": d2}]
        status, gap = check_report_frequency(reports)
        assert "WARNING" in status

    def test_analyze_summary_mode(self, tmp_path, capsys):
        from scripts.agent_evolve_self import analyze
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py", "--summary"]):
            result = analyze()
            assert result == 0
            captured = capsys.readouterr()
            assert "reports" in captured.out or "handlers" in captured.out

    def test_analyze_full_mode(self, tmp_path):
        from scripts.agent_evolve_self import analyze
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with patch("scripts.agent_evolve_self.REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_evolve_self.py"]):
            result = analyze()
            assert result == 0


# ===========================================================================
# 4. agent_research.py  (run, write_report, mark_task_done, main)
# ===========================================================================

class TestAgentResearch:
    """Tests for agent_research.py run(), write_report(), mark_task_done(), main()."""

    def test_run_returns_tuple(self):
        from scripts.agent_research import run
        with patch("scripts.agent_research.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("output", 0)
            out, code = run("cmd")
            assert out == "output"
            assert code == 0

    def test_write_report(self, tmp_path):
        from scripts.agent_research import write_report
        with patch("scripts.agent_research.REPO_ROOT", tmp_path):
            task = {
                "id": "TASK-999",
                "title": "Test task",
                "description": "A test",
                "priority": "P1",
            }
            rpath = write_report(task, "## Findings\nSome text here")
            assert rpath.exists()
            content = rpath.read_text(encoding="utf-8")
            assert "TASK-999" in content
            assert "Findings" in content

    def test_mark_task_done(self, tmp_path):
        from scripts.agent_research import mark_task_done
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text(
            "### TASK-001\n- **Title:** Something\n- **Status:** PENDING\n- **Priority:** P1\n",
            encoding="utf-8"
        )
        mark_task_done("TASK-001", tasks_path)
        content = tasks_path.read_text(encoding="utf-8")
        assert "DONE" in content
        assert "PENDING" not in content

    def test_main_no_tasks_file(self, tmp_path):
        from scripts.agent_research import main
        with patch("scripts.agent_research.REPO_ROOT", tmp_path), \
             pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_main_no_pending(self, tmp_path, capsys):
        from scripts.agent_research import main
        tasks_path = tmp_path / "AGENT_TASKS.md"
        tasks_path.write_text(
            "### TASK-001\n- **Title:** Done task\n- **Status:** DONE (2026-03-01)\n- **Priority:** P1\n",
            encoding="utf-8"
        )
        with patch("scripts.agent_research.REPO_ROOT", tmp_path), \
             pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_parse_tasks(self):
        from scripts.agent_research import parse_tasks
        content = (
            "# Header\n\n"
            "### TASK-001\n"
            "- **Title:** Do something\n"
            "- **Status:** PENDING\n"
            "- **Priority:** P1\n"
            "- **Output:** reports/foo.md\n"
            "- **Description:** Detailed desc\n"
        )
        tasks = parse_tasks(content)
        assert len(tasks) == 1
        assert tasks[0]["id"] == "TASK-001"
        assert tasks[0]["status"] == "PENDING"
        assert tasks[0]["title"] == "Do something"

    def test_find_first_pending(self):
        from scripts.agent_research import find_first_pending
        tasks = [
            {"id": "TASK-001", "status": "DONE (2026-01-01)"},
            {"id": "TASK-002", "status": "PENDING"},
        ]
        result = find_first_pending(tasks)
        assert result["id"] == "TASK-002"

    def test_find_first_pending_none(self):
        from scripts.agent_research import find_first_pending
        tasks = [{"id": "TASK-001", "status": "DONE (2026-01-01)"}]
        assert find_first_pending(tasks) is None


# ===========================================================================
# 5. agent_impact.py  (run, main, check_impact, detect_change_type)
# ===========================================================================

class TestAgentImpact:
    """Tests for agent_impact.py run(), main(), detect_change_type()."""

    def test_run_returns_tuple(self):
        from scripts.agent_impact import run
        with patch("scripts.agent_impact.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("files", 0)
            out, code = run("git diff")
            assert out == "files"
            assert code == 0

    def test_detect_change_type_new_tests(self):
        from scripts.agent_impact import detect_change_type
        files = ["tests/steward/test_new.py"]
        types = detect_change_type(files)
        assert "new_tests" in types

    def test_detect_change_type_new_claim(self):
        from scripts.agent_impact import detect_change_type
        files = ["backend/progress/new_claim.py"]
        types = detect_change_type(files)
        assert "new_claim" in types

    def test_detect_change_type_nothing(self):
        from scripts.agent_impact import detect_change_type
        files = ["docs/README.md"]
        types = detect_change_type(files)
        # docs/ isn't a trigger path
        assert len(types) == 0

    def test_check_impact_no_triggers(self):
        from scripts.agent_impact import check_impact
        result = check_impact(["docs/some.md"])
        assert result["change_types"] == []
        assert result["missing"] == []

    def test_check_impact_with_missing(self):
        from scripts.agent_impact import check_impact
        result = check_impact(["tests/steward/test_new.py"])
        assert "new_tests" in result["change_types"]
        assert len(result["missing"]) > 0

    def test_main_summary_no_diff(self, capsys):
        from scripts.agent_impact import main
        with patch("scripts.agent_impact.run", return_value=("", 128)), \
             patch("sys.argv", ["agent_impact.py", "--summary"]):
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "no diff" in captured.out.lower()

    def test_main_summary_with_changes(self, capsys):
        from scripts.agent_impact import main
        with patch("scripts.agent_impact.run", return_value=("tests/steward/test_new.py", 0)), \
             patch("sys.argv", ["agent_impact.py", "--summary"]):
            result = main()
            assert result == 0

    def test_main_full_no_triggers(self, capsys):
        from scripts.agent_impact import main
        with patch("scripts.agent_impact.run", return_value=("docs/note.md", 0)), \
             patch("sys.argv", ["agent_impact.py"]):
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "routine" in captured.out.lower() or "No impact" in captured.out

    def test_main_full_with_missing(self, capsys):
        from scripts.agent_impact import main
        with patch("scripts.agent_impact.run", return_value=("tests/steward/test_new.py", 0)), \
             patch("sys.argv", ["agent_impact.py"]):
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "MISSING" in captured.out or "updated" in captured.out.lower()


# ===========================================================================
# 6. agent_evolution.py  (run, individual checks, main)
# ===========================================================================

class TestAgentEvolution:
    """Tests for agent_evolution.py run() and individual check functions."""

    def test_run_returns_tuple(self):
        from scripts.agent_evolution import run
        with patch("scripts.agent_evolution.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("output", 0)
            out, code = run("cmd")
            assert out == "output"
            assert code == 0

    def test_check_steward_pass(self, capsys):
        from scripts.agent_evolution import check_steward
        with patch("scripts.agent_evolution.run", return_value=("STEWARD AUDIT: PASS", 0)):
            result = check_steward()
            assert result is True

    def test_check_steward_fail(self, capsys):
        from scripts.agent_evolution import check_steward
        with patch("scripts.agent_evolution.run", return_value=("FAIL: missing", 1)):
            result = check_steward()
            assert result is False

    def test_check_tests_pass(self, capsys):
        from scripts.agent_evolution import check_tests
        with patch("scripts.agent_evolution.run", return_value=("100 passed", 0)):
            ok, count = check_tests()
            assert ok is True
            assert count == 100

    def test_check_tests_fail(self, capsys):
        from scripts.agent_evolution import check_tests
        with patch("scripts.agent_evolution.run", return_value=("2 failed, 98 passed", 1)):
            ok, count = check_tests()
            assert ok is False

    def test_check_impact_advisory(self, capsys):
        from scripts.agent_evolution import check_impact
        with patch("scripts.agent_evolution.run", return_value=("5 files changed | no impact rules triggered", 0)):
            result = check_impact()
            assert result is True  # always advisory

    def test_check_diff_review_pass(self, capsys):
        from scripts.agent_evolution import check_diff_review
        with patch("scripts.agent_evolution.run", return_value=("DIFF_PASS | 3 files reviewed", 0)):
            result = check_diff_review()
            assert result is True

    def test_check_diff_review_fail(self, capsys):
        from scripts.agent_evolution import check_diff_review
        with patch("scripts.agent_evolution.run", return_value=("DIFF_FAIL | 2 issues", 1)):
            result = check_diff_review()
            assert result is False

    def test_check_auto_pr_clean(self, capsys):
        from scripts.agent_evolution import check_auto_pr
        with patch("scripts.agent_evolution.run", return_value=("No auto-pr needed -- system current", 0)):
            result = check_auto_pr()
            assert result is True

    def test_check_semantic_audit_pass(self, capsys):
        from scripts.agent_evolution import check_semantic_audit
        with patch("scripts.agent_evolution.run", return_value=("All checks pass", 0)):
            result = check_semantic_audit()
            assert result is True

    def test_check_semantic_audit_fail(self, capsys):
        from scripts.agent_evolution import check_semantic_audit
        with patch("scripts.agent_evolution.run", return_value=("FAIL: something wrong", 1)):
            result = check_semantic_audit()
            assert result is False

    def test_check_forbidden_no_hits(self, tmp_path, capsys):
        """Test check_forbidden with clean files."""
        from scripts.agent_evolution import check_forbidden
        # The real function scans dirs with `run(grep ...)` -- mock it
        with patch("scripts.agent_evolution.run", return_value=("", 1)), \
             patch("scripts.agent_evolution.REPO_ROOT", tmp_path):
            # Create minimal dirs so the function can scan
            (tmp_path / "scripts").mkdir()
            (tmp_path / "backend").mkdir()
            (tmp_path / "docs").mkdir()
            result = check_forbidden()
            assert result is True


# ===========================================================================
# 7. mg_policy_gate.py  (PolicyGate, main)
# ===========================================================================

class TestMgPolicyGate:
    """Tests for mg_policy_gate.py main() and get_changed_files_git."""

    def test_main_with_files_flag(self, tmp_path, capsys):
        from scripts.mg_policy_gate import main, PolicyGate
        policy = {
            "version": "1.0",
            "allow_globs": ["*.py", "*.md"],
            "locked_paths": [],
        }
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        with patch("sys.argv", ["mg_policy_gate.py", "--policy", str(pol_path), "--files", "foo.py,bar.md"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 0  # all allowed

    def test_main_with_files_flag_violation(self, tmp_path):
        from scripts.mg_policy_gate import main
        policy = {
            "version": "1.0",
            "allow_globs": ["*.py"],
            "locked_paths": [],
        }
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        with patch("sys.argv", ["mg_policy_gate.py", "--policy", str(pol_path), "--files", "secret.bin"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 2  # violation

    def test_main_missing_args(self, tmp_path):
        from scripts.mg_policy_gate import main
        policy = {"version": "1.0", "allow_globs": [], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        with patch("sys.argv", ["mg_policy_gate.py", "--policy", str(pol_path)]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 3

    def test_main_files_with_base_error(self, tmp_path):
        from scripts.mg_policy_gate import main
        policy = {"version": "1.0", "allow_globs": [], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        with patch("sys.argv", ["mg_policy_gate.py", "--policy", str(pol_path),
                                 "--files", "a.py", "--base", "main", "--head", "HEAD"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 3

    def test_get_changed_files_git_success(self, tmp_path):
        from scripts.mg_policy_gate import PolicyGate
        policy = {"version": "1.0", "allow_globs": ["*.py"], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        gate = PolicyGate(str(pol_path))
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("file1.py\nfile2.py", 0)
            mock_sub.return_value.check_returncode = MagicMock()
            files = gate.get_changed_files_git("origin/main", "HEAD")
            assert files == ["file1.py", "file2.py"]

    def test_get_changed_files_git_failure(self, tmp_path):
        import subprocess as sp
        from scripts.mg_policy_gate import PolicyGate
        policy = {"version": "1.0", "allow_globs": ["*.py"], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        gate = PolicyGate(str(pol_path))
        with patch("subprocess.run") as mock_sub:
            mock_sub.side_effect = sp.CalledProcessError(1, "git", stderr="error")
            with pytest.raises(SystemExit) as exc:
                gate.get_changed_files_git("origin/main", "HEAD")
            assert exc.value.code == 3

    def test_enforce_no_files(self, tmp_path, capsys):
        from scripts.mg_policy_gate import PolicyGate
        policy = {"version": "1.0", "allow_globs": ["*.py"], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        gate = PolicyGate(str(pol_path))
        assert gate.enforce([]) is True

    def test_enforce_locked_path(self, tmp_path, capsys):
        from scripts.mg_policy_gate import PolicyGate
        policy = {"version": "1.0", "allow_globs": ["*.py", "*.md"],
                  "locked_paths": ["scripts/steward_audit.py"]}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        gate = PolicyGate(str(pol_path))
        result = gate.enforce(["scripts/steward_audit.py"])
        assert result is False

    def test_matches_pattern_directory_glob(self, tmp_path):
        from scripts.mg_policy_gate import PolicyGate
        policy = {"version": "1.0", "allow_globs": ["backend/**"], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        gate = PolicyGate(str(pol_path))
        assert gate.matches_pattern("backend/progress/foo.py", "backend/**") is True

    def test_get_changed_files_list(self, tmp_path):
        from scripts.mg_policy_gate import PolicyGate
        policy = {"version": "1.0", "allow_globs": [], "locked_paths": []}
        pol_path = tmp_path / "policy.json"
        pol_path.write_text(json.dumps(policy))
        gate = PolicyGate(str(pol_path))
        result = gate.get_changed_files_list("a.py, b.md, c.json")
        assert result == ["a.py", "b.md", "c.json"]


# ===========================================================================
# 8. agent_pr_creator.py  (_auto_fix_stale_counter, detect functions, main)
# ===========================================================================

class TestAgentPrCreator:
    """Tests for agent_pr_creator.py _auto_fix_stale_counter and main."""

    def test_auto_fix_stale_counter(self, tmp_path):
        from scripts.agent_pr_creator import _auto_fix_stale_counter
        manifest = {"test_count": 100, "version": "1.0.0-rc1"}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        with patch("scripts.agent_pr_creator.REPO_ROOT", tmp_path), \
             patch("scripts.agent_pr_creator.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("", 0)
            _auto_fix_stale_counter(manifest_path, manifest, 150)
            # Should have called git checkout -b, git add, git commit, git push
            assert mock_sub.call_count == 4
            # Manifest should be updated on disk
            updated = json.loads(manifest_path.read_text())
            assert updated["test_count"] == 150

    def test_detect_forbidden_terms_clean(self, tmp_path):
        from scripts.agent_pr_creator import detect_forbidden_terms
        with patch("scripts.agent_pr_creator.REPO_ROOT", tmp_path):
            (tmp_path / "docs").mkdir()
            (tmp_path / "docs" / "safe.md").write_text("All is well.", encoding="utf-8")
            result = detect_forbidden_terms()
            assert result == []

    def test_detect_forbidden_terms_found(self, tmp_path):
        from scripts.agent_pr_creator import detect_forbidden_terms
        with patch("scripts.agent_pr_creator.REPO_ROOT", tmp_path):
            (tmp_path / "docs").mkdir()
            (tmp_path / "docs" / "bad.md").write_text("This is tamper-proof and great.", encoding="utf-8")
            result = detect_forbidden_terms()
            assert len(result) >= 1

    def test_detect_manifest_sync(self, tmp_path):
        from scripts.agent_pr_creator import detect_manifest_sync
        manifest = {"version": "1.0.0-rc1"}
        (tmp_path / "system_manifest.json").write_text(json.dumps(manifest))
        with patch("scripts.agent_pr_creator.REPO_ROOT", tmp_path), \
             patch("scripts.agent_pr_creator.subprocess.run") as mock_sub:
            mock_sub.return_value = _make_completed_process("v1.0.0-rc1", 0)
            result = detect_manifest_sync()
            assert result["synced"] is True

    def test_detect_coverage_drop_no_reports(self, tmp_path):
        from scripts.agent_pr_creator import detect_coverage_drop
        with patch("scripts.agent_pr_creator.REPO_ROOT", tmp_path):
            (tmp_path / "reports").mkdir()
            result = detect_coverage_drop()
            assert result is None

    def test_main_all_clean(self, tmp_path, capsys):
        from scripts.agent_pr_creator import main
        manifest = {"test_count": 100, "version": "1.0.0-rc1"}
        (tmp_path / "system_manifest.json").write_text(json.dumps(manifest))
        with patch("scripts.agent_pr_creator.REPO_ROOT", tmp_path), \
             patch("scripts.agent_pr_creator.detect_stale_counters",
                   return_value={"stale": False, "manifest_count": 100, "actual_count": 100}), \
             patch("scripts.agent_pr_creator.detect_forbidden_terms", return_value=[]), \
             patch("scripts.agent_pr_creator.detect_manifest_sync",
                   return_value={"synced": True, "manifest_version": "1.0.0-rc1", "tag_version": "1.0.0-rc1"}), \
             patch("scripts.agent_pr_creator.detect_coverage_drop", return_value=None), \
             patch("sys.argv", ["agent_pr_creator.py", "--summary"]):
            result = main()
            assert result == 0
            captured = capsys.readouterr()
            assert "no auto-pr needed" in captured.out.lower() or "system current" in captured.out.lower()


# ===========================================================================
# 9. agent_learn.py  (recall, brief, stats)
# ===========================================================================

class TestAgentLearn:
    """Tests for agent_learn.py recall(), brief(), stats()."""

    def test_recall_no_sessions(self):
        from scripts import agent_learn
        # Verify recall() runs without error when no sessions
        with patch.object(agent_learn, "load_kb", return_value={"sessions": [], "etalon": {}}), \
             patch.object(agent_learn, "load_patterns", return_value={}):
            agent_learn.recall()  # Should not raise

    def test_recall_with_sessions(self, capsys):
        from scripts import agent_learn
        kb = {
            "sessions": [
                {"timestamp": "2026-03-01T00:00:00", "issue_count": 0, "actual_test_count": 100},
            ],
            "etalon": {"version": "1.0.0-rc1", "test_count": 100, "updated": "2026-01-01T00:00:00"},
        }
        with patch.object(agent_learn, "load_kb", return_value=kb), \
             patch.object(agent_learn, "load_patterns", return_value={}):
            agent_learn.recall()
        captured = capsys.readouterr()
        assert "ETALON" in captured.out or "100" in captured.out

    def test_brief(self, capsys):
        from scripts import agent_learn
        kb = {
            "sessions": [{"timestamp": "2026-03-01T00:00:00", "issue_count": 0}],
            "etalon": {"version": "1.0.0-rc1", "test_count": 100, "updated": "2026-01-01"},
        }
        with patch.object(agent_learn, "load_kb", return_value=kb), \
             patch.object(agent_learn, "load_patterns", return_value={}):
            agent_learn.brief()
        captured = capsys.readouterr()
        assert "1 sessions" in captured.out or "Agent memory" in captured.out

    def test_stats_no_sessions(self, capsys):
        from scripts import agent_learn
        with patch.object(agent_learn, "load_kb", return_value={"sessions": []}), \
             patch.object(agent_learn, "load_patterns", return_value={}):
            agent_learn.stats()
        captured = capsys.readouterr()
        assert "No sessions" in captured.out

    def test_stats_with_sessions(self, capsys):
        from scripts import agent_learn
        kb = {
            "sessions": [
                {"timestamp": "2026-03-01T00:00:00", "issue_count": 2},
                {"timestamp": "2026-03-02T00:00:00", "issue_count": 0},
            ],
        }
        with patch.object(agent_learn, "load_kb", return_value=kb), \
             patch.object(agent_learn, "load_patterns", return_value={}):
            agent_learn.stats()
        captured = capsys.readouterr()
        assert "2" in captured.out  # 2 sessions


# ===========================================================================
# 10. Direct claim certificate tests (covering runner.py dispatch paths)
# ===========================================================================

class TestClaimCertificates:
    """Tests that exercise claim certificate functions, covering runner dispatch lines."""

    def test_mlbench2_regression_certificate(self):
        from backend.progress.mlbench2_regression_certificate import run_certificate
        result = run_certificate(seed=42)
        assert "mtr_phase" in result
        assert "execution_trace" in result

    def test_mlbench3_timeseries_certificate(self):
        from backend.progress.mlbench3_timeseries_certificate import run_certificate
        result = run_certificate(seed=42)
        assert "mtr_phase" in result
        assert "execution_trace" in result

    def test_pharma1_admet_certificate(self):
        from backend.progress.pharma1_admet_certificate import run_certificate
        result = run_certificate(seed=42)
        assert "mtr_phase" in result

    def test_finrisk1_var_certificate(self):
        from backend.progress.finrisk1_var_certificate import run_certificate
        result = run_certificate(seed=42)
        assert "mtr_phase" in result

    def test_dtsensor1_iot_certificate(self):
        from backend.progress.dtsensor1_iot_certificate import run_certificate
        result = run_certificate(seed=42)
        assert "mtr_phase" in result

    def test_dtcalib1_convergence_certificate(self):
        from backend.progress.dtcalib1_convergence_certificate import run_certificate
        result = run_certificate(seed=42)
        assert "mtr_phase" in result

    def test_agent_drift_monitor(self):
        from backend.progress.agent_drift_monitor import run_agent_drift_monitor
        baseline = {"tests_per_phase": 47, "pass_rate": 1.0, "regressions": 0, "verifier_iterations": 1.2}
        current = {"tests_per_phase": 47, "pass_rate": 1.0, "regressions": 0, "verifier_iterations": 1.2}
        result = run_agent_drift_monitor(baseline=baseline, current=current)
        assert "mtr_phase" in result

    def test_mtr4_titanium_calibration(self):
        from backend.progress.mtr4_titanium_calibration import run_calibration
        result = run_calibration(seed=42)
        assert "mtr_phase" in result


# ===========================================================================
# 11. ledger_store.py  (get, list_recent, count)
# ===========================================================================

class TestLedgerStoreOperations:
    """Tests for ledger_store.py get, list_recent, count."""

    def _make_store(self, tmp_path):
        from backend.ledger.ledger_store import LedgerStore
        store = LedgerStore(str(tmp_path / "test_ledger.jsonl"))
        return store

    def _make_entry_dict(self, trace_id="abc123"):
        """Create a dict matching LedgerEntry.from_dict expectations."""
        return {
            "trace_id": trace_id,
            "created_at": "2026-01-01T00:00:00Z",
            "phase": 31,
            "actor": "test",
            "action": "test_action",
            "inputs": {},
            "outputs": {},
            "artifacts": [],
            "legal_sig_refs": [],
            "meta": {},
        }

    def _write_entries(self, tmp_path, entries):
        ledger_file = tmp_path / "test_ledger.jsonl"
        lines = [json.dumps(e, sort_keys=True, separators=(',', ':')) for e in entries]
        ledger_file.write_text("\n".join(lines) + "\n")
        return ledger_file

    def test_get_not_found(self, tmp_path):
        store = self._make_store(tmp_path)
        result = store.get("nonexistent")
        assert result is None

    def test_get_found(self, tmp_path):
        entry = self._make_entry_dict("abc123")
        self._write_entries(tmp_path, [entry])
        store = self._make_store(tmp_path)
        result = store.get("abc123")
        assert result is not None
        assert result.trace_id == "abc123"

    def test_list_recent_empty(self, tmp_path):
        store = self._make_store(tmp_path)
        result = store.list_recent()
        assert result == []

    def test_list_recent_with_entries(self, tmp_path):
        entries = [self._make_entry_dict(f"id_{i}") for i in range(3)]
        self._write_entries(tmp_path, entries)
        store = self._make_store(tmp_path)
        result = store.list_recent(limit=2)
        assert len(result) == 2

    def test_count_empty(self, tmp_path):
        store = self._make_store(tmp_path)
        assert store.count() == 0

    def test_count_with_entries(self, tmp_path):
        entries = [self._make_entry_dict(f"id_{i}") for i in range(5)]
        self._write_entries(tmp_path, entries)
        store = self._make_store(tmp_path)
        assert store.count() == 5

    def test_count_with_invalid_lines(self, tmp_path):
        ledger_file = tmp_path / "test_ledger.jsonl"
        valid = json.dumps(self._make_entry_dict("a"), sort_keys=True, separators=(',', ':'))
        ledger_file.write_text(valid + '\nINVALID JSON\n')
        store = self._make_store(tmp_path)
        assert store.count() == 1


# ===========================================================================
# 12. agent_chronicle.py  (diff section, lines 125-158)
# ===========================================================================

class TestAgentChronicleDiff:
    """Tests targeting uncovered diff section in agent_chronicle.py."""

    def test_read_claim_domains_returns_list(self):
        from scripts.agent_chronicle import read_claim_domains
        result = read_claim_domains()
        assert isinstance(result, list)
        # Each element should be a tuple of (claim_id, domain)
        if result:
            assert len(result[0]) == 2

    def test_count_tasks(self):
        from scripts.agent_chronicle import count_tasks
        result = count_tasks()
        # Returns (pending_count, done_count) tuple
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_read_manifest(self):
        from scripts.agent_chronicle import read_manifest
        result = read_manifest()
        assert isinstance(result, dict)

    def test_main_summary_mode(self, capsys):
        from scripts.agent_chronicle import main
        with patch("sys.argv", ["agent_chronicle.py", "--summary"]):
            result = main()
            assert result == 0
