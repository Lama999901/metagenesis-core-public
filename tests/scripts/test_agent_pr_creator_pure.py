"""Tests for scripts/agent_pr_creator.py -- detect_forbidden_terms (10 tests)."""
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
