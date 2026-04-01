"""Tests for scripts/mg_policy_gate.py — PolicyGate pattern matching and enforcement."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mg_policy_gate import PolicyGate, PolicyViolation

POLICY_PATH = str(REPO_ROOT / "scripts" / "mg_policy_gate_policy.json")


def _gate():
    return PolicyGate(POLICY_PATH)


class TestMatchesPattern:
    def test_md_in_reports(self):
        assert _gate().matches_pattern("reports/foo.md", "reports/*.md") is True

    def test_py_not_in_reports_md(self):
        assert _gate().matches_pattern("scripts/foo.py", "reports/*.md") is False

    def test_deep_path_with_doublestar(self):
        assert _gate().matches_pattern("backend/vision/ingest.py", "backend/vision/**") is True

    def test_scripts_doublestar(self):
        assert _gate().matches_pattern("scripts/mg.py", "scripts/**") is True

    def test_root_md_glob(self):
        assert _gate().matches_pattern("README.md", "*.md") is True


class TestCheckLockedPaths:
    def test_empty_list(self):
        assert _gate().check_locked_paths([]) == []

    def test_locked_file_returns_violations(self):
        violations = _gate().check_locked_paths(["scripts/steward_audit.py"])
        assert len(violations) > 0

    def test_unlocked_file_returns_empty(self):
        assert _gate().check_locked_paths(["README.md"]) == []


class TestCheckAllowlist:
    def test_scripts_allowed(self):
        assert _gate().check_allowlist(["scripts/mg.py"]) == []

    def test_tests_allowed(self):
        assert _gate().check_allowlist(["tests/test_foo.py"]) == []
