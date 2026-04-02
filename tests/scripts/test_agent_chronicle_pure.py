"""Tests for scripts/agent_chronicle.py — pure-function coverage."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_chronicle  # noqa: E402


# ── read_manifest ────────────────────────────────────────────────────────────

class TestReadManifest:
    def test_empty_when_no_file(self, tmp_path):
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_manifest()
        assert result == {}

    def test_reads_data(self, tmp_path):
        data = {"version": "0.8.0", "test_count": 608}
        (tmp_path / "system_manifest.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_manifest()
        assert result == data

    def test_reads_claims(self, tmp_path):
        data = {"active_claims": ["MTR-1", "PHYS-01"]}
        (tmp_path / "system_manifest.json").write_text(json.dumps(data), encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_manifest()
        assert result["active_claims"] == ["MTR-1", "PHYS-01"]

    def test_invalid_json_raises(self, tmp_path):
        (tmp_path / "system_manifest.json").write_text("{bad", encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            with pytest.raises(json.JSONDecodeError):
                agent_chronicle.read_manifest()


# ── read_claim_domains ───────────────────────────────────────────────────────

class TestReadClaimDomains:
    def test_empty_when_no_file(self, tmp_path):
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert result == []

    def test_returns_tuples(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        content = "## MTR-1\n| key | val |\n| **Domain** | materials |\n"
        (reports / "scientific_claim_index.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert len(result) == 1
        assert isinstance(result[0], tuple)
        assert result[0][0] == "MTR-1"

    def test_multiple_claims(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        content = "## MTR-1\n| **domain** | materials |\n\n## PHYS-01\n| **domain** | physics |\n"
        (reports / "scientific_claim_index.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert len(result) == 2
        ids = [r[0] for r in result]
        assert "MTR-1" in ids
        assert "PHYS-01" in ids

    def test_whitespace_in_domain(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        content = "## MTR-1\n|  **domain**  |  materials science  |\n"
        (reports / "scientific_claim_index.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert len(result) == 1
        assert result[0][1].strip() == "materials science"


# ── count_tasks ──────────────────────────────────────────────────────────────

class TestCountTasks:
    def test_zero_when_no_file(self, tmp_path):
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 0 and d == 0

    def test_counts_pending(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text(
            "Task 1\nStatus: PENDING\nTask 2\nStatus: PENDING\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 2 and d == 0

    def test_counts_done(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text(
            "Task 1\nStatus: DONE\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 0 and d == 1

    def test_returns_tuple(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text("", encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.count_tasks()
        assert isinstance(result, tuple)

    def test_case_sensitive(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text(
            "Status: pending\nStatus: done\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 0 and d == 0

    def test_mixed(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text(
            "Status: PENDING\nStatus: DONE\nStatus: PENDING\nStatus: DONE\nStatus: DONE\n",
            encoding="utf-8",
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 2 and d == 3

    def test_prefix_status(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text(
            "PENDING task here\nDONE task there\nStatus: PENDING\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 1 and d == 0


# ── find_previous_chronicle ─────────────────────────────────────────────────

class TestFindPreviousChronicle:
    def test_none_when_no_reports(self, tmp_path):
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert result is None

    def test_finds_chronicle(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        content = "# CHRONICLE\n> Claims: 18\n> Tests: 500\n> Innovations: 7\n"
        (reports / "CHRONICLE_0_7_0_20260301.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert result is not None
        assert result["file"] == "CHRONICLE_0_7_0_20260301.md"
        assert result["claims"] == 18
        assert result["tests"] == 500
        assert result["innovations"] == 7

    def test_returns_dict_keys(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        content = "# CHRONICLE\n> Claims: 20\n> Tests: 608\n> Innovations: 8\n"
        (reports / "CHRONICLE_0_8_0_20260331.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert "file" in result
        assert "claims" in result
        assert "tests" in result
        assert "innovations" in result


# -- read_manifest extended ---------------------------------------------------

class TestReadManifestExtended:
    def test_returns_version_key(self, tmp_path):
        data = {"version": "1.0.0"}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_manifest()
        assert result["version"] == "1.0.0"

    def test_returns_active_claims(self, tmp_path):
        data = {"active_claims": ["MTR-1"]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_manifest()
        assert "active_claims" in result

    def test_returns_verified_innovations(self, tmp_path):
        data = {"verified_innovations": ["X"]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_manifest()
        assert "verified_innovations" in result


# -- read_claim_domains extended ----------------------------------------------

class TestReadClaimDomainsExtended:
    def test_empty_file(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "scientific_claim_index.md").write_text("", encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert result == []

    def test_no_domain_row(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "scientific_claim_index.md").write_text(
            "## MTR-1\nSome text\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert len(result) == 1
        assert result[0][0] == "MTR-1"
        assert result[0][1] == ""

    def test_multiple_claims_with_domains(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        content = (
            "## MTR-1\n| **domain** | materials |\n\n"
            "## PHYS-01\n| **domain** | physics |\n"
        )
        (reports / "scientific_claim_index.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert len(result) == 2

    def test_heading_must_be_h2(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "scientific_claim_index.md").write_text(
            "### MTR-1\n| **domain** | materials |\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.read_claim_domains()
        assert result == []


# -- count_tasks extended -----------------------------------------------------

class TestCountTasksExtended:
    def test_only_done(self, tmp_path):
        content = "Status: DONE\nStatus: DONE\nStatus: DONE\n"
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 0 and d == 3

    def test_only_pending(self, tmp_path):
        content = "Status: PENDING\nStatus: PENDING\n"
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 2 and d == 0

    def test_empty_file(self, tmp_path):
        (tmp_path / "AGENT_TASKS.md").write_text("", encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            p, d = agent_chronicle.count_tasks()
        assert p == 0 and d == 0


# -- find_previous_chronicle extended -----------------------------------------

class TestFindPreviousChronicleExtended:
    def test_picks_latest_by_sort(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "CHRONICLE_a.md").write_text("# A\n> Claims: 10\n", encoding="utf-8")
        (reports / "CHRONICLE_z.md").write_text("# Z\n> Claims: 20\n", encoding="utf-8")
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert result is not None
        assert result["file"] == "CHRONICLE_z.md"

    def test_extracts_claims_count(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "CHRONICLE_test.md").write_text(
            "# C\n> Claims: 15\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert result["claims"] == 15

    def test_extracts_tests_count(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "CHRONICLE_test.md").write_text(
            "# C\n> Tests: 500\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert result["tests"] == 500

    def test_extracts_innovations_count(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "CHRONICLE_test.md").write_text(
            "# C\n> Innovations: 8\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert result["innovations"] == 8

    def test_missing_numbers_not_in_dict(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "CHRONICLE_test.md").write_text(
            "# C\nNo numbers here\n", encoding="utf-8"
        )
        with patch("agent_chronicle.REPO_ROOT", tmp_path):
            result = agent_chronicle.find_previous_chronicle()
        assert "claims" not in result
