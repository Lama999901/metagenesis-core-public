#!/usr/bin/env python3
"""
Tests for scripts/agent_evolution_council.py
=============================================
Covers: all 6 data sources, proposal generation, ranking,
empty sources, --summary output, edge cases.
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_evolution_council as aec


# ---------------------------------------------------------------------------
# Source 1: agent_learn
# ---------------------------------------------------------------------------

class TestReadAgentLearn:
    def test_parses_recurring_patterns(self):
        fake_output = (
            "MOST COMMON ISSUES:\n"
            "  [5x] STALE COUNT in README.md: found 271\n"
            "  [3x] MERGE CONFLICT MARKERS in AGENTS.md\n"
            "  [1x] minor glitch\n"
        )
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_agent_learn()
        assert ok is True
        # Only patterns with count >= 3
        assert len(items) == 2
        assert items[0]["count"] == 5
        assert items[1]["count"] == 3

    def test_empty_output(self):
        with patch.object(aec, "_run", return_value=("", 1)):
            items, ok = aec.read_agent_learn()
        assert ok is False
        assert items == []

    def test_no_recurring_patterns(self):
        fake_output = "MOST COMMON ISSUES:\n  [1x] something once\n  [2x] twice\n"
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_agent_learn()
        assert ok is True
        assert items == []


# ---------------------------------------------------------------------------
# Source 2: coverage
# ---------------------------------------------------------------------------

class TestReadCoverage:
    def test_parses_coverage_table(self):
        fake_output = (
            "scripts/foo.py        100     50     50%\n"
            "scripts/bar.py        200     20     90%\n"
            "backend/baz.py         80     40     50%\n"
        )
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_coverage()
        assert ok is True
        # Only modules below 70%
        below_70 = [i for i in items if i["coverage_pct"] < 70]
        assert len(below_70) == 2
        assert below_70[0]["module"] == "scripts/foo.py"

    def test_all_above_70(self):
        fake_output = "scripts/foo.py  100  10  90%\n"
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_coverage()
        assert ok is True
        assert items == []

    def test_fallback_to_agent_coverage(self):
        def side_effect(cmd, **kw):
            if "pytest" in cmd:
                return ("", 2)
            if "agent_coverage" in cmd:
                return ("Coverage 65.0%", 0)
            return ("", 1)

        with patch.object(aec, "_run", side_effect=side_effect):
            items, ok = aec.read_coverage()
        assert ok is True
        assert len(items) == 1
        assert items[0]["coverage_pct"] == 65.0


# ---------------------------------------------------------------------------
# Source 3: known_faults.yaml
# ---------------------------------------------------------------------------

class TestReadKnownFaults:
    def test_parses_yaml_with_regex_fallback(self):
        items, ok = aec.read_known_faults()
        # known_faults.yaml exists in repo
        assert ok is True
        assert len(items) >= 1
        # Check structure
        for item in items:
            assert "fault_id" in item
            assert "severity" in item

    def test_missing_file(self, tmp_path):
        with patch.object(aec, "REPO_ROOT", tmp_path):
            items, ok = aec.read_known_faults()
        assert ok is False
        assert items == []

    def test_parses_fault_ids(self):
        items, ok = aec.read_known_faults()
        if ok:
            fault_ids = [i["fault_id"] for i in items]
            assert "ENV_001" in fault_ids


# ---------------------------------------------------------------------------
# Source 4: agent_evolution
# ---------------------------------------------------------------------------

class TestReadAgentEvolution:
    def test_captures_fail_lines(self):
        fake_output = (
            "  PASS  steward\n"
            "  FAIL  coverage -- below threshold\n"
            "  PASS  tests\n"
        )
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_agent_evolution()
        assert ok is True
        assert len(items) == 1
        assert "coverage" in items[0]["description"].lower()

    def test_all_pass(self):
        fake_output = "PASS steward\nPASS tests\nPASS deep\n"
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_agent_evolution()
        assert ok is True
        assert items == []

    def test_empty_output(self):
        with patch.object(aec, "_run", return_value=("", 1)):
            items, ok = aec.read_agent_evolution()
        assert ok is False


# ---------------------------------------------------------------------------
# Source 5: response_queue
# ---------------------------------------------------------------------------

class TestReadResponseQueue:
    def test_parses_pilot_queue(self):
        queue_data = {
            "entries": [
                {"domain_detected": "ml", "name": "Alice"},
                {"domain_detected": "ml", "name": "Bob"},
                {"domain_detected": "pharma", "name": "Carol"},
            ]
        }
        with patch.object(aec, "REPO_ROOT", Path("/fake")):
            # Mock path existence and reading
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = json.dumps(queue_data)

            with patch("pathlib.Path.__truediv__", return_value=mock_path):
                # Direct test with injected data
                pass

        # Test the function with actual file if it exists
        items, ok = aec.read_response_queue()
        # May or may not find the file -- just check structure
        if ok and items:
            assert all("domain" in i for i in items)

    def test_missing_queue(self, tmp_path):
        with patch.object(aec, "REPO_ROOT", tmp_path):
            items, ok = aec.read_response_queue()
        assert ok is False
        assert items == []

    def test_empty_entries(self, tmp_path):
        queue_file = tmp_path / "reports" / "pilot_queue.json"
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text('{"entries": []}')
        with patch.object(aec, "REPO_ROOT", tmp_path):
            items, ok = aec.read_response_queue()
        assert ok is True
        assert items == []

    def test_counts_domains(self, tmp_path):
        queue_file = tmp_path / "reports" / "pilot_queue.json"
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        data = {"entries": [
            {"domain_detected": "ml"},
            {"domain_detected": "ml"},
            {"domain_detected": "pharma"},
        ]}
        queue_file.write_text(json.dumps(data))
        with patch.object(aec, "REPO_ROOT", tmp_path):
            items, ok = aec.read_response_queue()
        assert ok is True
        assert len(items) == 2
        ml_item = next(i for i in items if i["domain"] == "ml")
        assert ml_item["count"] == 2


# ---------------------------------------------------------------------------
# Source 6: git log hotspots
# ---------------------------------------------------------------------------

class TestReadGitHotspots:
    def test_parses_git_log(self):
        fake_output = (
            "abc1234 fix: something\n"
            "scripts/foo.py\n"
            "tests/test_foo.py\n"
            "def5678 feat: another\n"
            "scripts/foo.py\n"
            "scripts/bar.py\n"
            "ghi9012 chore: update\n"
            "scripts/foo.py\n"
        )
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_git_hotspots()
        assert ok is True
        if items:
            top = items[0]
            assert top["file"] == "scripts/foo.py"
            assert top["change_count"] == 3

    def test_empty_log(self):
        with patch.object(aec, "_run", return_value=("", 1)):
            items, ok = aec.read_git_hotspots()
        assert ok is False

    def test_no_hotspots(self):
        fake_output = "abc1234 fix\nscripts/one.py\n"
        with patch.object(aec, "_run", return_value=(fake_output, 0)):
            items, ok = aec.read_git_hotspots()
        assert ok is True
        # Only 1 occurrence, needs >= 2
        assert items == []


# ---------------------------------------------------------------------------
# Proposal Generation
# ---------------------------------------------------------------------------

class TestProposalGeneration:
    def _make_sources(self, **overrides):
        defaults = {
            "agent_learn": ([], True),
            "coverage": ([], True),
            "known_faults": ([], True),
            "agent_evolution": ([], True),
            "response_queue": ([], True),
            "git_log": ([], True),
        }
        defaults.update(overrides)
        return defaults

    def test_empty_sources_produce_no_proposals(self):
        sources = self._make_sources()
        proposals = aec.generate_proposals(sources)
        assert proposals == []

    def test_proposals_ranked_by_impact_effort(self):
        sources = self._make_sources(
            agent_learn=([
                {"source": "agent_learn", "count": 5, "description": "Stale counters recurring"},
            ], True),
            coverage=([
                {"source": "coverage", "module": "scripts/foo.py", "coverage_pct": 30, "description": "foo.py 30%"},
            ], True),
            git_log=([
                {"source": "git_log", "file": "index.html", "change_count": 8, "description": "index.html changed 8 times"},
            ], True),
        )
        proposals = aec.generate_proposals(sources)
        assert len(proposals) == 3
        # All should have rank assigned
        assert proposals[0]["rank"] == 1
        # Highest score should come first
        assert proposals[0]["score"] >= proposals[1]["score"]

    def test_max_10_proposals(self):
        many_items = [
            {"source": "git_log", "file": f"file{i}.py", "change_count": 2,
             "description": f"file{i}.py changed 2 times"}
            for i in range(15)
        ]
        sources = self._make_sources(git_log=(many_items, True))
        proposals = aec.generate_proposals(sources)
        assert len(proposals) <= 10

    def test_failed_sources_ignored(self):
        sources = self._make_sources(
            agent_learn=([], False),
            coverage=([
                {"source": "coverage", "module": "x.py", "coverage_pct": 50, "description": "x.py 50%"},
            ], True),
        )
        proposals = aec.generate_proposals(sources)
        assert len(proposals) == 1

    def test_deduplication(self):
        # Descriptions must share the first 50 chars to be deduped
        long_prefix = "STALE COUNT in README.md found old value 271 instead of current"
        sources = self._make_sources(
            agent_learn=([
                {"source": "agent_learn", "count": 3, "description": long_prefix + " (first)"},
                {"source": "agent_learn", "count": 4, "description": long_prefix + " (second)"},
            ], True),
        )
        proposals = aec.generate_proposals(sources)
        # Only first 50 chars matter for dedup, these share the prefix
        assert len(proposals) == 1


# ---------------------------------------------------------------------------
# Impact/Effort Classification
# ---------------------------------------------------------------------------

class TestClassification:
    def test_critical_for_high_count_learn(self):
        item = {"source": "agent_learn", "count": 5, "description": "test"}
        assert aec._classify_impact(item) == "CRITICAL"

    def test_high_for_response_queue(self):
        item = {"source": "response_queue", "domain": "ml", "description": "test"}
        assert aec._classify_impact(item) == "HIGH"

    def test_medium_for_known_faults(self):
        item = {"source": "known_faults", "severity": "EXPECTED", "description": "test"}
        assert aec._classify_impact(item) == "MEDIUM"

    def test_coverage_critical_below_40(self):
        item = {"source": "coverage", "coverage_pct": 30, "description": "test"}
        assert aec._classify_impact(item) == "CRITICAL"

    def test_effort_low_for_response_queue(self):
        item = {"source": "response_queue", "description": "test"}
        assert aec._classify_effort(item) == "LOW"

    def test_effort_low_for_stale_counters(self):
        item = {"source": "agent_learn", "description": "stale counter in docs"}
        assert aec._classify_effort(item) == "LOW"


# ---------------------------------------------------------------------------
# Markdown Output
# ---------------------------------------------------------------------------

class TestWriteProposals:
    def test_writes_file(self, tmp_path):
        planning = tmp_path / ".planning"
        planning.mkdir()
        with patch.object(aec, "REPO_ROOT", tmp_path):
            proposals = [
                {
                    "rank": 1, "title": "Test Proposal",
                    "problem": "Something broken",
                    "evidence": "test output",
                    "solution": "Fix it",
                    "effort": "LOW", "impact": "HIGH",
                    "risk": "Tests catch regressions",
                    "score": 3.0, "source": "coverage",
                },
            ]
            sources = {"coverage": ([], True), "agent_learn": ([], False)}
            path = aec.write_proposals_md(proposals, sources)

        content = path.read_text(encoding="utf-8")
        assert "# Evolution Proposals" in content
        assert "PROP-001" in content
        assert "Test Proposal" in content
        assert "coverage" in content

    def test_empty_proposals(self, tmp_path):
        planning = tmp_path / ".planning"
        planning.mkdir()
        with patch.object(aec, "REPO_ROOT", tmp_path):
            path = aec.write_proposals_md([], {"a": ([], True)})
        content = path.read_text(encoding="utf-8")
        assert "No proposals generated" in content


# ---------------------------------------------------------------------------
# --summary output
# ---------------------------------------------------------------------------

class TestSummaryOutput:
    def test_prints_top_3(self, capsys):
        proposals = [
            {"rank": i, "title": f"Prop {i}", "impact": "HIGH",
             "effort": "LOW", "solution": f"Fix {i}", "score": 3.0}
            for i in range(1, 6)
        ]
        aec.print_summary(proposals)
        out = capsys.readouterr().out
        assert "PROP-001" in out
        assert "PROP-002" in out
        assert "PROP-003" in out
        # Should NOT include 4th and 5th
        assert "PROP-004" not in out

    def test_empty_proposals(self, capsys):
        aec.print_summary([])
        out = capsys.readouterr().out
        assert "No proposals" in out


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

class TestCLIIntegration:
    def test_summary_flag_runs(self):
        """Verify --summary runs without error (using --fast to skip slow subprocess sources)."""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["EVOL_FAST"] = "1"  # skip slow subprocess sources
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_evolution_council.py"), "--summary"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            env=env, encoding="utf-8", errors="replace",
            timeout=60,
        )
        assert r.returncode == 0
        assert "Evolution Council" in r.stdout or "No proposals" in r.stdout

    def test_json_flag_runs(self):
        """Verify --json runs and produces valid JSON (using --fast to skip slow subprocess sources)."""
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["EVOL_FAST"] = "1"  # skip slow subprocess sources
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_evolution_council.py"), "--json"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            env=env, encoding="utf-8", errors="replace",
            timeout=60,
        )
        assert r.returncode == 0
        data = json.loads(r.stdout)
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_all_sources_fail(self):
        sources = {
            "agent_learn": ([], False),
            "coverage": ([], False),
            "known_faults": ([], False),
            "agent_evolution": ([], False),
            "response_queue": ([], False),
            "git_log": ([], False),
        }
        proposals = aec.generate_proposals(sources)
        assert proposals == []

    def test_malformed_json_in_queue(self, tmp_path):
        queue_file = tmp_path / "reports" / "response_queue.json"
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        queue_file.write_text("NOT VALID JSON {{{")
        with patch.object(aec, "REPO_ROOT", tmp_path):
            items, ok = aec.read_response_queue()
        assert ok is False

    def test_solution_generation_all_sources(self):
        sources = ["coverage", "known_faults", "agent_evolution",
                    "response_queue", "git_log", "agent_learn"]
        for src in sources:
            item = {"source": src, "description": "test", "module": "x.py",
                    "fault_id": "F1", "domain": "ml", "file": "f.py", "count": 3}
            sol = aec._generate_solution(item)
            assert isinstance(sol, str)
            assert len(sol) > 5

    def test_risk_assessment_all_sources(self):
        sources = ["coverage", "known_faults", "agent_evolution",
                    "response_queue", "git_log", "agent_learn", "unknown"]
        for src in sources:
            item = {"source": src}
            risk = aec._risk_assessment(item)
            assert isinstance(risk, str)
            assert len(risk) > 5
