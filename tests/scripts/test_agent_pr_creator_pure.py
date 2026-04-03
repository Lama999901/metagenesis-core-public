"""Tests for scripts/agent_pr_creator.py -- detect_forbidden_terms + detect_coverage_drop (18 tests)."""
import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pytest
import agent_pr_creator as apc


def _write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestDetectForbiddenTerms:
    """Tests using real file I/O in tmp_path with patched REPO_ROOT."""

    def test_clean_repo(self, tmp_path):
        _write(tmp_path / "README.md", "All good here.\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert result == []

    def test_finds_tamper_proof(self, tmp_path):
        _write(tmp_path / "README.md", "Our system is tamper-proof.\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert any("tamper-proof" in f for f in result)

    def test_finds_blockchain(self, tmp_path):
        _write(tmp_path / "README.md", "We use blockchain technology.\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert any("blockchain" in f for f in result)

    def test_safe_context_not_flagged(self, tmp_path):
        _write(tmp_path / "README.md", 'BANNED: never write "tamper-proof"\n')
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert result == []

    def test_safe_context_banned(self, tmp_path):
        _write(tmp_path / "docs" / "rules.md", "BANNED TERMS: blockchain\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert result == []

    def test_skip_agent_pr_creator(self, tmp_path):
        _write(tmp_path / "scripts" / "agent_pr_creator.py", "tamper-proof blockchain\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert result == []

    def test_skip_deep_verify(self, tmp_path):
        _write(tmp_path / "scripts" / "deep_verify.py", "tamper-proof\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert result == []

    def test_readme_scanned(self, tmp_path):
        _write(tmp_path / "README.md", "GPT-5 is great.\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert len(result) >= 1

    def test_returns_list(self, tmp_path):
        _write(tmp_path / "README.md", "clean\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert isinstance(result, list)

    def test_no_targets_exist(self, tmp_path):
        # tmp_path has none of the scan_targets
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_forbidden_terms()
        assert result == []


class TestDetectCoverageDrop:
    """Tests for detect_coverage_drop() -- 8 tests."""

    def test_detect_coverage_drop_above_threshold(self, tmp_path):
        """Report with 81.2% coverage should return None."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "Overall coverage: 81.2%\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is None

    def test_detect_coverage_drop_below_threshold(self, tmp_path):
        """Report with 50.0% coverage should return warning string."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "Overall coverage: 50.0%\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is not None
        assert "50.0%" in result

    def test_detect_coverage_drop_at_threshold(self, tmp_path):
        """Report with exactly 65.0% should return None (not below)."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "Overall coverage: 65.0%\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is None

    def test_detect_coverage_drop_no_report(self, tmp_path):
        """Empty reports dir should return None."""
        (tmp_path / "reports").mkdir(parents=True, exist_ok=True)
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is None

    def test_detect_coverage_drop_parse_overall_format(self, tmp_path):
        """'Overall coverage: 70.0%' format should parse correctly."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "Overall coverage: 70.0%\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is None

    def test_detect_coverage_drop_parse_summary_format(self, tmp_path):
        """'Coverage 60.0%' format should parse and return warning."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "Coverage 60.0%\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is not None
        assert "60.0%" in result

    def test_detect_coverage_drop_invalid_content(self, tmp_path):
        """Report with no numbers should return None."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "no numbers here\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert result is None

    def test_detect_coverage_drop_returns_string_on_fail(self, tmp_path):
        """Below threshold should return a string."""
        _write(tmp_path / "reports" / "COVERAGE_REPORT_20260402.md",
               "Overall coverage: 30.0%\n")
        with patch("agent_pr_creator.REPO_ROOT", tmp_path):
            result = apc.detect_coverage_drop()
        assert isinstance(result, str)
