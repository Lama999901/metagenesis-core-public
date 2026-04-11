"""Tests for scripts/agent_pattern_promoter.py — proposal generation from learned patterns."""

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_pattern_promoter as promoter  # noqa: E402


# ── load_patterns ───────────────────────────────────────────────────────────

class TestLoadPatternsEmpty:

    def test_missing_file_returns_empty(self, tmp_path):
        fake = tmp_path / "patterns.json"
        with patch.object(promoter, "PATTERNS_FILE", fake):
            result = promoter.load_patterns()
        assert result == {}

    def test_empty_object_returns_empty(self, tmp_path):
        fake = tmp_path / "patterns.json"
        fake.write_text("{}", encoding="utf-8")
        with patch.object(promoter, "PATTERNS_FILE", fake):
            result = promoter.load_patterns()
        assert result == {}

    def test_empty_file_returns_empty(self, tmp_path):
        """Empty file (not valid JSON) should return {} gracefully."""
        fake = tmp_path / "patterns.json"
        fake.write_text("", encoding="utf-8")
        with patch.object(promoter, "PATTERNS_FILE", fake):
            result = promoter.load_patterns()
        assert result == {}


# ── find_high_frequency ────────────────────────────────────────────────────

class TestFindHighFrequencyPatterns:

    def test_filters_below_threshold(self):
        patterns = {
            "rare_issue": {"count": 1, "first_seen": "2026-01-01"},
            "uncommon":   {"count": 2, "first_seen": "2026-01-02"},
        }
        result = promoter.find_high_frequency(patterns, threshold=3)
        assert len(result) == 0

    def test_includes_at_threshold(self):
        patterns = {
            "frequent": {"count": 3, "first_seen": "2026-01-01"},
        }
        result = promoter.find_high_frequency(patterns, threshold=3)
        assert len(result) == 1
        assert result[0][0] == "frequent"
        assert result[0][1]["count"] == 3

    def test_includes_above_threshold(self):
        patterns = {
            "low":  {"count": 1, "first_seen": "2026-01-01"},
            "high": {"count": 5, "first_seen": "2026-01-02"},
            "mid":  {"count": 3, "first_seen": "2026-01-03"},
        }
        result = promoter.find_high_frequency(patterns, threshold=3)
        assert len(result) == 2
        keys = [r[0] for r in result]
        assert "high" in keys
        assert "mid" in keys
        assert "low" not in keys

    def test_sorted_by_count_desc(self):
        patterns = {
            "mid":  {"count": 3},
            "high": {"count": 7},
            "low":  {"count": 4},
        }
        result = promoter.find_high_frequency(patterns, threshold=3)
        counts = [r[1]["count"] for r in result]
        assert counts == sorted(counts, reverse=True)

    def test_empty_patterns(self):
        result = promoter.find_high_frequency({}, threshold=3)
        assert result == []


# ── is_covered_by_evolution ────────────────────────────────────────────────

class TestSkipAlreadyCoveredPattern:

    def test_skips_covered_pattern(self):
        evo_source = "def check_stale():\n    # handles STALE COUNT in README\n    pass\n"
        assert promoter.is_covered_by_evolution("STALE COUNT in README.md", evo_source)

    def test_keeps_uncovered_pattern(self):
        evo_source = "def check_something_else():\n    pass\n"
        assert not promoter.is_covered_by_evolution("MEMORY LEAK in worker pool", evo_source)

    def test_empty_evolution_keeps_all(self):
        assert not promoter.is_covered_by_evolution("some issue here", "")


# ── generate_proposals ─────────────────────────────────────────────────────

class TestGenerateProposalFormat:

    def _make_proposals(self, high_freq, evo_source="", existing_content=""):
        return promoter.generate_proposals(high_freq, evo_source, existing_content)

    def test_single_proposal_has_all_fields(self):
        high_freq = [
            ("STALE COUNT in docs", {
                "count": 5,
                "first_seen": "2026-01-01",
                "last_seen": "2026-03-15",
                "fix_hint": "sync test count",
            }),
        ]
        proposals = self._make_proposals(high_freq)
        assert len(proposals) == 1
        prop = proposals[0]
        assert "number" in prop
        assert "key" in prop
        assert "effort" in prop
        assert "impact" in prop
        assert "risk" in prop
        assert "code" in prop

    def test_format_proposal_text(self):
        high_freq = [
            ("test_issue", {"count": 5, "first_seen": "2026-01-01", "fix_hint": "fix"}),
        ]
        proposals = self._make_proposals(high_freq)
        text = promoter.format_proposal(proposals[0])
        for field in ["PROP-", "Problem", "Evidence", "Solution", "Effort", "Impact", "Risk"]:
            assert field in text, f"Missing field: {field}"

    def test_evidence_includes_count(self):
        high_freq = [
            ("recurring_bug", {"count": 12, "first_seen": "2026-01-01"}),
        ]
        proposals = self._make_proposals(high_freq)
        text = promoter.format_proposal(proposals[0])
        assert "12" in text

    def test_multiple_proposals_unique_numbers(self):
        high_freq = [
            ("issue_a", {"count": 3, "first_seen": "2026-01-01"}),
            ("issue_b", {"count": 5, "first_seen": "2026-02-01"}),
        ]
        proposals = self._make_proposals(high_freq)
        assert len(proposals) == 2
        numbers = [p["number"] for p in proposals]
        assert numbers[0] != numbers[1]


# ── get_next_prop_number ───────────────────────────────────────────────────

class TestProposalNumbering:

    def test_starts_at_one_for_empty_content(self):
        assert promoter.get_next_prop_number("") == 1

    def test_starts_at_one_for_no_props(self):
        assert promoter.get_next_prop_number("# Evolution Proposals\n") == 1

    def test_continues_from_highest(self):
        content = "## PROP-003\nblah\n## PROP-001\nblah\n## PROP-005\nblah\n"
        assert promoter.get_next_prop_number(content) == 6

    def test_single_prop(self):
        assert promoter.get_next_prop_number("## PROP-010\n") == 11


# ── dry_run vs real run ────────────────────────────────────────────────────

class TestDryRun:

    def test_cmd_dry_run_does_not_crash(self, tmp_path):
        """Dry run should execute without errors even with empty data."""
        patterns_file = tmp_path / "patterns.json"
        patterns_file.write_text("{}", encoding="utf-8")
        proposals_file = tmp_path / "EVOLUTION_PROPOSALS.md"

        with patch.object(promoter, "PATTERNS_FILE", patterns_file), \
             patch.object(promoter, "PROPOSALS_FILE", proposals_file), \
             patch.object(promoter, "EVOLUTION_FILE", tmp_path / "evo.py"):
            promoter.cmd_dry_run()

        assert not proposals_file.exists()


# ── pattern_key_to_slug ────────────────────────────────────────────────────

class TestPatternKeyToSlug:

    def test_basic_slug(self):
        slug = promoter.pattern_key_to_slug("STALE COUNT in README.md")
        assert re.match(r'^[a-z0-9_]+$', slug)
        assert len(slug) <= 50

    def test_special_chars_removed(self):
        slug = promoter.pattern_key_to_slug("ERROR: [foo] bar's (baz)")
        assert ":" not in slug
        assert "[" not in slug
        assert "'" not in slug
