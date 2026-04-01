"""Tests for scripts/agent_chronicle.py — pure read functions."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from agent_chronicle import read_manifest, read_claim_domains, count_tasks


class TestReadManifest:
    def test_returns_dict(self):
        result = read_manifest()
        assert isinstance(result, dict)

    def test_has_test_count(self):
        result = read_manifest()
        assert "test_count" in result

    def test_has_version(self):
        result = read_manifest()
        assert "version" in result

    def test_non_empty(self):
        result = read_manifest()
        assert len(result) > 0


class TestReadClaimDomains:
    def test_returns_list(self):
        result = read_claim_domains()
        assert isinstance(result, list)

    def test_non_empty(self):
        result = read_claim_domains()
        assert len(result) > 0


class TestCountTasks:
    def test_returns_tuple(self):
        result = count_tasks()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_both_non_negative(self):
        pending, done = count_tasks()
        assert pending >= 0
        assert done >= 0
