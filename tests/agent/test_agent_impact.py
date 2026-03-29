"""
Tests for scripts/agent_impact.py — Cogitator Impact Analyzer
42 tests covering parse_update_protocol, detect_change_type,
check_impact, and main() with all branches.
"""
import sys
import pytest
from unittest.mock import patch
from pathlib import Path

# Repo root = tests/agent/../../..
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_impact
from agent_impact import (
    parse_update_protocol,
    detect_change_type,
    check_impact,
    DEPENDENCY_RULES,
)


# ─────────────────────────────────────────────────────
# parse_update_protocol
# ─────────────────────────────────────────────────────

class TestParseUpdateProtocol:

    def test_returns_dict(self):
        rules = parse_update_protocol()
        assert isinstance(rules, dict)

    def test_has_all_change_types(self):
        rules = parse_update_protocol()
        for key in ["new_claim", "new_tests", "new_layer",
                    "new_release", "new_innovation"]:
            assert key in rules

    def test_each_rule_has_required_files(self):
        rules = parse_update_protocol()
        for key, rule in rules.items():
            assert "required_files" in rule, f"{key} missing required_files"
            assert isinstance(rule["required_files"], list)
            assert len(rule["required_files"]) > 0

    def test_each_rule_has_trigger_paths(self):
        rules = parse_update_protocol()
        for key, rule in rules.items():
            assert "trigger_paths" in rule
            assert len(rule["trigger_paths"]) > 0

    def test_new_claim_required_includes_manifest(self):
        rules = parse_update_protocol()
        assert "system_manifest.json" in rules["new_claim"]["required_files"]

    def test_new_tests_required_includes_readme(self):
        rules = parse_update_protocol()
        assert "README.md" in rules["new_tests"]["required_files"]

    def test_returns_same_object_as_dependency_rules(self):
        assert parse_update_protocol() is DEPENDENCY_RULES


# ─────────────────────────────────────────────────────
# detect_change_type
# ─────────────────────────────────────────────────────

class TestDetectChangeType:

    def test_new_claim_detected(self):
        result = detect_change_type(["backend/progress/pharma_new.py"])
        assert "new_claim" in result

    def test_runner_py_not_new_claim(self):
        result = detect_change_type(["backend/progress/runner.py"])
        assert "new_claim" not in result

    def test_non_py_in_backend_not_new_claim(self):
        result = detect_change_type(["backend/progress/README.md"])
        assert "new_claim" not in result

    def test_new_tests_detected(self):
        result = detect_change_type(["tests/materials/test_mtr1_new.py"])
        assert "new_tests" in result

    def test_non_test_py_in_tests_not_new_tests(self):
        result = detect_change_type(["tests/conftest.py"])
        assert "new_tests" not in result

    def test_new_layer_detected_mg_script(self):
        result = detect_change_type(["scripts/mg_newlayer.py"])
        assert "new_layer" in result

    def test_mg_sign_triggers_new_layer(self):
        result = detect_change_type(["scripts/mg_sign.py"])
        assert "new_layer" in result

    def test_new_release_detected(self):
        result = detect_change_type(["system_manifest.json"])
        assert "new_release" in result

    def test_new_innovation_detected(self):
        result = detect_change_type(["ppa/CLAIMS_DRAFT.md"])
        assert "new_innovation" in result

    def test_ppa_readme_triggers_innovation(self):
        result = detect_change_type(["ppa/README_PPA.md"])
        assert "new_innovation" in result

    def test_empty_files_returns_empty(self):
        assert detect_change_type([]) == []

    def test_irrelevant_files_return_empty(self):
        result = detect_change_type(["docs/PROTOCOL.md", "COMMERCIAL.md"])
        assert result == []

    def test_multiple_types_detected(self):
        files = [
            "backend/progress/new_claim.py",
            "tests/materials/test_new_claim.py",
        ]
        result = detect_change_type(files)
        assert "new_claim" in result
        assert "new_tests" in result

    def test_returns_list(self):
        assert isinstance(detect_change_type(["system_manifest.json"]), list)

    def test_no_duplicates_in_result(self):
        files = ["tests/a/test_foo.py", "tests/b/test_bar.py"]
        result = detect_change_type(files)
        assert len(result) == len(set(result))


# ─────────────────────────────────────────────────────
# check_impact
# ─────────────────────────────────────────────────────

class TestCheckImpact:

    def test_no_relevant_files_returns_empty(self):
        result = check_impact(["docs/PROTOCOL.md"])
        assert result["change_types"] == []
        assert result["missing"] == []
        assert result["updated"] == []
        assert result["total_required"] == 0

    def test_empty_input(self):
        result = check_impact([])
        assert result["change_types"] == []
        assert result["total_required"] == 0

    def test_returns_dict_with_all_keys(self):
        result = check_impact([])
        for key in ["change_types", "missing", "updated", "total_required"]:
            assert key in result

    def test_new_release_all_missing(self):
        result = check_impact(["system_manifest.json"])
        assert "new_release" in result["change_types"]
        assert "README.md" in result["missing"]
        assert result["total_required"] > 0

    def test_new_release_all_updated(self):
        files = ["system_manifest.json", "README.md",
                 "llms.txt", "CONTEXT_SNAPSHOT.md", "index.html"]
        result = check_impact(files)
        assert "new_release" in result["change_types"]
        assert len(result["missing"]) == 0

    def test_new_claim_all_required_updated(self):
        files = [
            "backend/progress/new_claim.py",
            "backend/progress/runner.py",
            "reports/scientific_claim_index.md",
            "reports/canonical_state.md",
            "system_manifest.json", "index.html",
            "README.md", "AGENTS.md", "llms.txt", "CONTEXT_SNAPSHOT.md",
            "CONTRIBUTING.md",
            "paper.md",
            "ppa/README_PPA.md",
            "scripts/check_stale_docs.py",
            "CLAUDE.md",
            "COMMERCIAL.md",
        ]
        result = check_impact(files)
        assert "new_claim" in result["change_types"]
        assert len(result["missing"]) == 0

    def test_partial_update_shows_missing(self):
        files = ["system_manifest.json", "README.md"]
        result = check_impact(files)
        assert "new_release" in result["change_types"]
        assert len(result["missing"]) > 0

    def test_updated_list_populated(self):
        files = ["system_manifest.json", "README.md"]
        result = check_impact(files)
        assert "README.md" in result["updated"]

    def test_multiple_change_types_union_required(self):
        files = [
            "backend/progress/another.py",
            "tests/domain/test_another.py",
        ]
        result = check_impact(files)
        assert "new_claim" in result["change_types"]
        assert "new_tests" in result["change_types"]
        expected = len(
            set(DEPENDENCY_RULES["new_claim"]["required_files"]) |
            set(DEPENDENCY_RULES["new_tests"]["required_files"])
        )
        assert result["total_required"] == expected


# ─────────────────────────────────────────────────────
# main()
# ─────────────────────────────────────────────────────

class TestMain:

    def _run(self, argv, git_output=""):
        with patch.object(sys, "argv", ["agent_impact.py"] + argv):
            with patch("agent_impact.run", return_value=(git_output, 0)):
                return agent_impact.main()

    def test_no_diff_default(self, capsys):
        result = self._run([], git_output="")
        out = capsys.readouterr().out
        assert "No diff" in out or result == 0

    def test_no_diff_summary(self, capsys):
        result = self._run(["--summary"], git_output="")
        out = capsys.readouterr().out
        assert "no diff" in out.lower() or "advisory" in out.lower()

    def test_summary_no_impact_rules(self, capsys):
        self._run(["--summary"], git_output="docs/PROTOCOL.md\n")
        out = capsys.readouterr().out
        assert "no impact rules triggered" in out

    def test_summary_pass(self, capsys):
        changed = "system_manifest.json\nREADME.md\nllms.txt\nCONTEXT_SNAPSHOT.md\nindex.html\n"
        self._run(["--summary"], git_output=changed)
        out = capsys.readouterr().out
        assert "PASS" in out or "updated" in out

    def test_summary_missing(self, capsys):
        self._run(["--summary"], git_output="system_manifest.json\n")
        out = capsys.readouterr().out
        assert "MISSING" in out or "missing" in out.lower()

    def test_full_output_no_impact(self, capsys):
        result = self._run([], git_output="docs/PROTOCOL.md\n")
        out = capsys.readouterr().out
        assert "No impact rules triggered" in out
        assert result == 0

    def test_full_output_with_missing(self, capsys):
        self._run([], git_output="system_manifest.json\n")
        out = capsys.readouterr().out
        assert "MISSING" in out or "need updating" in out

    def test_full_output_all_pass(self, capsys):
        changed = "system_manifest.json\nREADME.md\nllms.txt\nCONTEXT_SNAPSHOT.md\nindex.html\n"
        result = self._run([], git_output=changed)
        out = capsys.readouterr().out
        assert "PASS" in out or "required files updated" in out
        assert result == 0

    def test_verify_last_commit_flag(self, capsys):
        result = self._run(["--verify-last-commit"], git_output="docs/PROTOCOL.md\n")
        assert result == 0

    def test_main_returns_int(self):
        result = self._run([], git_output="")
        assert isinstance(result, int)

    def test_git_fallback_to_origin_main(self):
        """HEAD~1 diff empty → falls back to origin/main...HEAD."""
        call_count = [0]

        def mock_run(cmd, cwd=None):
            call_count[0] += 1
            return ("", 0) if call_count[0] == 1 else ("docs/PROTOCOL.md", 0)

        with patch.object(sys, "argv", ["agent_impact.py"]):
            with patch("agent_impact.run", side_effect=mock_run):
                agent_impact.main()
        assert call_count[0] == 2
