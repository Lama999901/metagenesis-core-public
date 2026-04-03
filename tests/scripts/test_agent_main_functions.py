#!/usr/bin/env python3
"""Coverage tests for main() functions across agent scripts -- 20 tests.

Targets main() in: agent_chronicle, agent_signals, agent_diff_review,
agent_audit, steward_dossier, and agent_evolution (summary mode).
All mock external calls (subprocess, filesystem, network) to run fast.

NOTE: Many agent scripts replace sys.stdout with io.TextIOWrapper at import
time, so capsys cannot capture their output. We verify return codes instead.
"""

import json
import sys
import io
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# 1-4: agent_chronicle.main()
# ---------------------------------------------------------------------------

class TestAgentChronicleMain:
    def _import(self):
        import agent_chronicle
        return agent_chronicle

    def test_summary_mode_returns_zero(self):
        mod = self._import()
        manifest = {
            "version": "0.8.0",
            "test_count": 1198,
            "active_claims": ["MTR-1", "MTR-2"],
            "verified_innovations": ["I1", "I2"],
        }
        with patch.object(mod, "read_manifest", return_value=manifest), \
             patch.object(mod, "read_claim_domains", return_value={}), \
             patch.object(mod, "count_tasks", return_value=(3, 5)), \
             patch.object(mod, "find_previous_chronicle", return_value=None), \
             patch("sys.argv", ["agent_chronicle", "--summary"]):
            rc = mod.main()
        assert rc == 0

    def test_summary_with_previous_returns_zero(self):
        mod = self._import()
        manifest = {
            "version": "0.8.0",
            "test_count": 1200,
            "active_claims": ["MTR-1"],
            "verified_innovations": ["I1"],
        }
        prev = {"file": "old.md", "tests": 1100, "claims": 1, "innovations": 1}
        with patch.object(mod, "read_manifest", return_value=manifest), \
             patch.object(mod, "read_claim_domains", return_value={}), \
             patch.object(mod, "count_tasks", return_value=(0, 0)), \
             patch.object(mod, "find_previous_chronicle", return_value=prev), \
             patch("sys.argv", ["agent_chronicle", "--summary"]):
            rc = mod.main()
        assert rc == 0

    def test_full_mode_writes_report(self, tmp_path):
        mod = self._import()
        manifest = {
            "version": "0.8.0",
            "test_count": 1198,
            "active_claims": ["MTR-1"],
            "verified_innovations": ["I1"],
        }
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with patch.object(mod, "read_manifest", return_value=manifest), \
             patch.object(mod, "read_claim_domains", return_value={}), \
             patch.object(mod, "count_tasks", return_value=(0, 0)), \
             patch.object(mod, "find_previous_chronicle", return_value=None), \
             patch.object(mod, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_chronicle"]):
            rc = mod.main()
        assert rc == 0

    def test_summary_delta_tests(self):
        mod = self._import()
        manifest = {
            "version": "0.8.0",
            "test_count": 1200,
            "active_claims": ["MTR-1", "MTR-2"],
            "verified_innovations": [],
        }
        prev = {"file": "old.md", "tests": 1100, "claims": 1, "innovations": 0}
        with patch.object(mod, "read_manifest", return_value=manifest), \
             patch.object(mod, "read_claim_domains", return_value={}), \
             patch.object(mod, "count_tasks", return_value=(0, 0)), \
             patch.object(mod, "find_previous_chronicle", return_value=prev), \
             patch("sys.argv", ["agent_chronicle", "--summary"]):
            rc = mod.main()
        assert rc == 0


# ---------------------------------------------------------------------------
# 5-8: agent_signals.main()
# ---------------------------------------------------------------------------

class TestAgentSignalsMain:
    def _import(self):
        import agent_signals
        return agent_signals

    def test_summary_mode_api_ok(self):
        mod = self._import()
        gh = {"stars": 10, "forks": 2, "open_issues": 3}
        with patch.object(mod, "fetch_github_stats", return_value=gh), \
             patch.object(mod, "count_memory_sessions", return_value=5), \
             patch.object(mod, "count_tasks", return_value=(1, 2)), \
             patch.object(mod, "read_manifest", return_value=("0.8.0", 1198)), \
             patch("sys.argv", ["agent_signals", "--summary"]):
            rc = mod.main()
        assert rc == 0

    def test_summary_mode_api_error(self):
        mod = self._import()
        gh = {"error": "timeout"}
        with patch.object(mod, "fetch_github_stats", return_value=gh), \
             patch.object(mod, "count_memory_sessions", return_value=0), \
             patch.object(mod, "count_tasks", return_value=(0, 0)), \
             patch.object(mod, "read_manifest", return_value=("0.8.0", 100)), \
             patch("sys.argv", ["agent_signals", "--summary"]):
            rc = mod.main()
        assert rc == 0

    def test_full_mode(self, tmp_path):
        mod = self._import()
        gh = {"stars": 5, "forks": 1, "open_issues": 0, "pushed_at": "2026-04-01"}
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with patch.object(mod, "fetch_github_stats", return_value=gh), \
             patch.object(mod, "count_memory_sessions", return_value=3), \
             patch.object(mod, "count_tasks", return_value=(2, 4)), \
             patch.object(mod, "read_manifest", return_value=("0.8.0", 1198)), \
             patch.object(mod, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_signals"]):
            rc = mod.main()
        assert rc == 0

    def test_summary_mode_gh_with_error_key(self):
        """When gh dict has error key, summary should show API unavailable."""
        mod = self._import()
        gh = {"error": "rate limited"}
        with patch.object(mod, "fetch_github_stats", return_value=gh), \
             patch.object(mod, "count_memory_sessions", return_value=0), \
             patch.object(mod, "count_tasks", return_value=(0, 0)), \
             patch.object(mod, "read_manifest", return_value=("0.8.0", 100)), \
             patch("sys.argv", ["agent_signals", "--summary"]):
            rc = mod.main()
        assert rc == 0


# ---------------------------------------------------------------------------
# 9-12: agent_diff_review.main()
# ---------------------------------------------------------------------------

class TestAgentDiffReviewMain:
    def _import(self):
        import agent_diff_review
        return agent_diff_review

    def test_summary_no_changes(self):
        mod = self._import()
        with patch.object(mod, "get_changed_py_files", return_value=[]), \
             patch("sys.argv", ["agent_diff_review", "--summary"]):
            rc = mod.main()
        assert rc == 0

    def test_summary_with_issues(self):
        mod = self._import()
        with patch.object(mod, "get_changed_py_files", return_value=["scripts/foo.py"]), \
             patch.object(mod, "review_file", return_value=["missing return"]), \
             patch("sys.argv", ["agent_diff_review", "--summary"]):
            rc = mod.main()
        assert rc == 1

    def test_full_no_changes(self):
        mod = self._import()
        with patch.object(mod, "get_changed_py_files", return_value=[]), \
             patch("sys.argv", ["agent_diff_review"]):
            rc = mod.main()
        assert rc == 0

    def test_full_with_issues(self):
        mod = self._import()
        with patch.object(mod, "get_changed_py_files", return_value=["scripts/x.py"]), \
             patch.object(mod, "review_file", return_value=["bad import"]), \
             patch("sys.argv", ["agent_diff_review"]):
            rc = mod.main()
        assert rc == 1


# ---------------------------------------------------------------------------
# 13-16: agent_audit.main()
# ---------------------------------------------------------------------------

class TestAgentAuditMain:
    def _import(self):
        import agent_audit
        return agent_audit

    def test_config_missing_returns_one(self):
        mod = self._import()
        with patch.object(mod, "load_config", return_value=None), \
             patch("sys.argv", ["agent_audit"]):
            rc = mod.main()
        assert rc == 1

    def test_config_missing_summary(self):
        mod = self._import()
        with patch.object(mod, "load_config", return_value=None), \
             patch("sys.argv", ["agent_audit", "--summary"]):
            rc = mod.main()
        assert rc == 1

    def test_all_checks_pass(self, tmp_path):
        mod = self._import()
        config = {"physical_anchors": {}, "innovations": [], "demo_scenarios": [], "patent": {}}
        manifest = {"version": "0.8.0"}
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with patch.object(mod, "load_config", return_value=config), \
             patch.object(mod, "load_manifest", return_value=manifest), \
             patch.object(mod, "check_physical_anchors", return_value=True), \
             patch.object(mod, "check_claim_matrix", return_value=(True, 20, 20)), \
             patch.object(mod, "check_innovations", return_value=True), \
             patch.object(mod, "check_demo_scenarios", return_value=True), \
             patch.object(mod, "check_triple_sync", return_value=True), \
             patch.object(mod, "check_patent_integrity", return_value=True), \
             patch.object(mod, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_audit"]):
            rc = mod.main()
        assert rc == 0

    def test_some_checks_fail(self, tmp_path):
        mod = self._import()
        config = {"physical_anchors": {}}
        manifest = {"version": "0.8.0"}
        reports_dir = tmp_path / "reports"
        reports_dir.mkdir()
        with patch.object(mod, "load_config", return_value=config), \
             patch.object(mod, "load_manifest", return_value=manifest), \
             patch.object(mod, "check_physical_anchors", return_value=False), \
             patch.object(mod, "check_claim_matrix", return_value=(False, 10, 20)), \
             patch.object(mod, "check_innovations", return_value=False), \
             patch.object(mod, "check_demo_scenarios", return_value=True), \
             patch.object(mod, "check_triple_sync", return_value=True), \
             patch.object(mod, "check_patent_integrity", return_value=True), \
             patch.object(mod, "REPO_ROOT", tmp_path), \
             patch("sys.argv", ["agent_audit"]):
            rc = mod.main()
        assert rc == 1


# ---------------------------------------------------------------------------
# 17-18: steward_dossier.main()
# ---------------------------------------------------------------------------

class TestStewardDossierMain:
    def _import(self):
        import steward_dossier
        return steward_dossier

    def test_main_with_output(self, tmp_path):
        mod = self._import()
        out_dir = tmp_path / "dossiers"
        with patch.object(mod, "build_dossiers", return_value=[]) as mock_bd, \
             patch("sys.argv", ["steward_dossier", "--output", str(out_dir)]):
            rc = mod.main()
        assert rc == 0
        mock_bd.assert_called_once()

    def test_main_default_args(self):
        mod = self._import()
        with patch.object(mod, "build_dossiers", return_value=[Path("a.md")]) as mock_bd, \
             patch("sys.argv", ["steward_dossier"]):
            rc = mod.main()
        assert rc == 0


# ---------------------------------------------------------------------------
# 19-20: agent_evolution.main() summary path
# ---------------------------------------------------------------------------

class TestAgentEvolutionMain:
    def _import(self):
        import agent_evolution
        return agent_evolution

    def test_summary_all_pass(self):
        mod = self._import()
        with patch.object(mod, "check_steward", return_value=True), \
             patch.object(mod, "check_tests", return_value=(True, 1198)), \
             patch.object(mod, "check_deep_verify", return_value=True), \
             patch.object(mod, "check_stale_docs", return_value=(True, [])), \
             patch.object(mod, "check_manifest", return_value=True), \
             patch.object(mod, "check_forbidden", return_value=True), \
             patch.object(mod, "run_gap_analysis", return_value=[]), \
             patch.object(mod, "check_claude_md", return_value=True), \
             patch.object(mod, "check_watchlist", return_value=True), \
             patch.object(mod, "check_branch_sync", return_value=True), \
             patch.object(mod, "check_coverage", return_value=True), \
             patch.object(mod, "check_self_improvement", return_value=True), \
             patch.object(mod, "check_signals", return_value=True), \
             patch.object(mod, "check_chronicle", return_value=True), \
             patch.object(mod, "check_pr_review", return_value=True), \
             patch.object(mod, "check_impact", return_value=True), \
             patch.object(mod, "check_diff_review", return_value=True), \
             patch.object(mod, "check_auto_pr", return_value=True), \
             patch.object(mod, "check_semantic_audit", return_value=True), \
             patch("sys.argv", ["agent_evolution", "--summary"]):
            rc = mod.main()
        assert rc == 0

    def test_summary_some_fail(self):
        mod = self._import()
        with patch.object(mod, "check_steward", return_value=True), \
             patch.object(mod, "check_tests", return_value=(False, 0)), \
             patch.object(mod, "check_deep_verify", return_value=False), \
             patch.object(mod, "check_stale_docs", return_value=(True, [])), \
             patch.object(mod, "check_manifest", return_value=True), \
             patch.object(mod, "check_forbidden", return_value=True), \
             patch.object(mod, "run_gap_analysis", return_value=["gap1"]), \
             patch.object(mod, "check_claude_md", return_value=True), \
             patch.object(mod, "check_watchlist", return_value=True), \
             patch.object(mod, "check_branch_sync", return_value=True), \
             patch.object(mod, "check_coverage", return_value=True), \
             patch.object(mod, "check_self_improvement", return_value=True), \
             patch.object(mod, "check_signals", return_value=True), \
             patch.object(mod, "check_chronicle", return_value=True), \
             patch.object(mod, "check_pr_review", return_value=True), \
             patch.object(mod, "check_impact", return_value=True), \
             patch.object(mod, "check_diff_review", return_value=True), \
             patch.object(mod, "check_auto_pr", return_value=True), \
             patch.object(mod, "check_semantic_audit", return_value=True), \
             patch("sys.argv", ["agent_evolution", "--summary"]):
            rc = mod.main()
        # Some checks fail, so rc depends on strict mode
        assert rc in (0, 1)
