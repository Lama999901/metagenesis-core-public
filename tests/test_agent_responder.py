#!/usr/bin/env python3
"""
Tests for scripts/agent_responder.py -- Response Infrastructure Agent

Covers: domain mappings, fuzzy matching, draft format, bundle generation,
queue management, CLI commands, status transitions, edge cases.

25+ tests required by RESP-07.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure repo root on path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_responder import (
    match_domain,
    DOMAIN_MAPPINGS,
    DEFAULT_MAPPING,
    VALID_STATUSES,
    load_queue,
    save_queue,
    generate_draft,
    generate_bundle,
    prepare_response,
    show_status,
    list_domains,
    update_status,
    _find_entry_by_contact,
    _sanitize_name,
    QUEUE_PATH,
    DRAFTS_DIR,
    BUNDLES_DIR,
)


# ---- Fixtures ---------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolate_queue(tmp_path, monkeypatch):
    """Redirect queue, drafts, and bundles to temp dirs for isolation."""
    q_path = tmp_path / "response_queue.json"
    d_dir = tmp_path / "response_drafts"
    b_dir = tmp_path / "response_bundles"
    monkeypatch.setattr("scripts.agent_responder.QUEUE_PATH", q_path)
    monkeypatch.setattr("scripts.agent_responder.DRAFTS_DIR", d_dir)
    monkeypatch.setattr("scripts.agent_responder.BUNDLES_DIR", b_dir)
    yield


# ---- Domain mapping tests (RESP-02) ----------------------------------------

class TestDomainMappings:
    """All 7 domain mappings resolve correctly."""

    def test_patronus_mapping(self):
        key, mapping = match_domain("anand patronus")
        assert key == "patronus"
        assert "ML_BENCH-01" in mapping["claims"]

    def test_bureau_veritas_mapping(self):
        key, mapping = match_domain("philipp bureau veritas")
        assert key == "bureau_veritas"
        assert "FINRISK-01" in mapping["claims"]

    def test_chollet_mapping(self):
        key, mapping = match_domain("chollet arc")
        assert key == "chollet"
        assert "ML_BENCH-02" in mapping["claims"]

    def test_percy_liang_mapping(self):
        key, mapping = match_domain("percy liang helm")
        assert key == "percy_liang"
        assert "ML_BENCH-03" in mapping["claims"]

    def test_iqvia_mapping(self):
        key, mapping = match_domain("raja shankar iqvia")
        assert key == "iqvia"
        assert "ML_BENCH-01" in mapping["claims"]
        assert "PHARMA-01" in mapping["claims"]

    def test_lmarena_mapping(self):
        key, mapping = match_domain("lmarena benchmark")
        assert key == "lmarena"
        assert "ML_BENCH-01" in mapping["claims"]

    def test_south_pole_mapping(self):
        key, mapping = match_domain("south pole carbon")
        assert key == "south_pole"
        assert "DATA-PIPE-01" in mapping["claims"]
        assert "ML_BENCH-01" in mapping["claims"]


# ---- Fuzzy matching tests ---------------------------------------------------

class TestFuzzyMatching:
    """Fuzzy matching works with partial names, case insensitive."""

    def test_case_insensitive(self):
        key, _ = match_domain("PATRONUS AI")
        assert key == "patronus"

    def test_partial_name_anand(self):
        key, _ = match_domain("anand")
        assert key == "patronus"

    def test_partial_name_chollet(self):
        key, _ = match_domain("Chollet")
        assert key == "chollet"

    def test_partial_bureau(self):
        key, _ = match_domain("Bureau Veritas")
        assert key == "bureau_veritas"

    def test_mixed_case_percy(self):
        key, _ = match_domain("PERCY liang")
        assert key == "percy_liang"

    def test_keyword_helm(self):
        key, _ = match_domain("helm stanford")
        assert key == "percy_liang"

    def test_keyword_arena(self):
        key, _ = match_domain("chatbot arena")
        assert key == "lmarena"

    def test_keyword_esg(self):
        key, _ = match_domain("esg climate")
        assert key == "south_pole"


# ---- Default domain tests ---------------------------------------------------

class TestDefaultDomain:
    """Default domain for unknown contacts."""

    def test_unknown_contact(self):
        key, mapping = match_domain("random person nobody")
        assert key == "default"
        assert "DATA-PIPE-01" in mapping["claims"]

    def test_empty_string(self):
        key, mapping = match_domain("")
        assert key == "default"

    def test_none_input(self):
        key, mapping = match_domain(None)
        assert key == "default"

    def test_whitespace_only(self):
        key, mapping = match_domain("   ")
        assert key == "default"


# ---- Draft format validation (RESP-03) --------------------------------------

class TestDraftFormat:
    """Draft format: no AI markers, no unicode, no Stripe link."""

    def _make_draft(self, contact="Test Person", mapping=None):
        if mapping is None:
            mapping = DOMAIN_MAPPINGS["patronus"]
        return generate_draft(contact, mapping, "PASS", "2026-04-04")

    def test_draft_file_created(self):
        path = self._make_draft()
        assert path.exists()
        assert path.suffix == ".txt"

    def test_no_ai_markers(self):
        path = self._make_draft()
        text = path.read_text(encoding="utf-8")
        ai_markers = [
            "as an ai", "i'm an ai", "language model", "chatgpt",
            "openai", "claude", "anthropic", "generated by",
        ]
        text_lower = text.lower()
        for marker in ai_markers:
            assert marker not in text_lower, f"Found AI marker: {marker}"

    def test_no_special_unicode(self):
        path = self._make_draft()
        text = path.read_text(encoding="utf-8")
        # No em-dash (U+2014), en-dash (U+2013), smart quotes, etc.
        assert "\u2014" not in text, "Found em-dash"
        assert "\u2013" not in text, "Found en-dash"
        assert "\u201c" not in text, "Found left smart quote"
        assert "\u201d" not in text, "Found right smart quote"

    def test_no_stripe_link(self):
        path = self._make_draft()
        text = path.read_text(encoding="utf-8").lower()
        assert "stripe" not in text
        assert "payment" not in text
        assert "$299" not in text

    def test_has_next_step_question(self):
        path = self._make_draft()
        text = path.read_text(encoding="utf-8")
        assert "?" in text, "Draft should end with a question"

    def test_reads_like_human(self):
        path = self._make_draft()
        text = path.read_text(encoding="utf-8")
        # Should start with Hi, have short paragraphs
        assert text.startswith("Hi ")
        assert "Best," in text
        assert "yehor@metagenesis-core.dev" in text

    def test_shows_pass_result(self):
        path = self._make_draft()
        text = path.read_text(encoding="utf-8")
        assert "PASS" in text

    def test_draft_uses_double_dash(self):
        """Drafts use -- not em-dash."""
        path = self._make_draft()
        text = path.read_text(encoding="utf-8")
        assert "--" in text


# ---- Bundle generation (RESP-04) -------------------------------------------

class TestBundleGeneration:
    """Bundle generation calls existing infrastructure correctly."""

    def test_generate_bundle_returns_tuple(self):
        bundle_dir, claim_result, verified = generate_bundle(
            "test_person", "ml", "2026-04-04"
        )
        assert bundle_dir.exists()
        assert isinstance(claim_result, dict)
        assert isinstance(verified, bool)
        # Cleanup
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)

    def test_bundle_contains_evidence(self):
        bundle_dir, _, _ = generate_bundle("test_person2", "ml", "2026-04-04")
        evidence = bundle_dir / "evidence.json"
        assert evidence.exists()
        data = json.loads(evidence.read_text(encoding="utf-8"))
        assert "mtr_phase" in data
        assert "execution_trace" in data
        # Cleanup
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)

    def test_bundle_for_finance_domain(self):
        bundle_dir, claim_result, verified = generate_bundle(
            "finance_test", "finance", "2026-04-04"
        )
        assert bundle_dir.exists()
        data = json.loads((bundle_dir / "evidence.json").read_text(encoding="utf-8"))
        assert data["mtr_phase"] == "FINRISK-01"
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)


# ---- Queue management (RESP-05) --------------------------------------------

class TestQueueManagement:
    """Queue file created and readable, status transitions work."""

    def test_empty_queue(self):
        queue = load_queue()
        assert queue == {"entries": []}

    def test_save_and_load_queue(self):
        queue = {"entries": [{"contact": "Test", "status": "prepared"}]}
        save_queue(queue)
        loaded = load_queue()
        assert len(loaded["entries"]) == 1
        assert loaded["entries"][0]["contact"] == "Test"

    def test_find_entry_exact_match(self):
        queue = {"entries": [
            {"contact": "Alice Smith", "status": "prepared"},
            {"contact": "Bob Jones", "status": "reviewed"},
        ]}
        entry = _find_entry_by_contact(queue, "Alice Smith")
        assert entry is not None
        assert entry["contact"] == "Alice Smith"

    def test_find_entry_partial_match(self):
        queue = {"entries": [
            {"contact": "Alice Smith", "status": "prepared"},
        ]}
        entry = _find_entry_by_contact(queue, "alice")
        assert entry is not None
        assert entry["contact"] == "Alice Smith"

    def test_find_entry_not_found(self):
        queue = {"entries": []}
        entry = _find_entry_by_contact(queue, "nobody")
        assert entry is None

    def test_valid_statuses(self):
        assert "prepared" in VALID_STATUSES
        assert "reviewed" in VALID_STATUSES
        assert "bundle_sent" in VALID_STATUSES
        assert "replied" in VALID_STATUSES
        assert "converted" in VALID_STATUSES
        assert len(VALID_STATUSES) == 5


# ---- Status command (RESP-06) -----------------------------------------------

class TestStatusCommand:
    """Status command output format."""

    def test_status_empty_queue(self, capsys):
        rc = show_status()
        assert rc == 0
        out = capsys.readouterr().out
        assert "empty" in out.lower()

    def test_status_with_entries(self, capsys):
        queue = {"entries": [{
            "contact": "Test Person",
            "company": "TestCo",
            "status": "prepared",
            "date": "2026-04-04",
            "claims": ["ML_BENCH-01"],
        }]}
        save_queue(queue)
        rc = show_status()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Test Person" in out
        assert "TestCo" in out
        assert "prepared" in out


# ---- List domains command (RESP-06) -----------------------------------------

class TestListDomains:
    """list-domains output format."""

    def test_list_domains_output(self, capsys):
        rc = list_domains()
        assert rc == 0
        out = capsys.readouterr().out
        assert "patronus" in out.lower()
        assert "bureau" in out.lower()
        assert "chollet" in out.lower()
        assert "default" in out.lower()
        assert "8 mappings" in out


# ---- Status transitions (RESP-06) -------------------------------------------

class TestStatusTransitions:
    """Status update validation."""

    def test_update_valid_status(self, capsys):
        queue = {"entries": [{"contact": "Alice", "status": "prepared"}]}
        save_queue(queue)
        rc = update_status("Alice", "reviewed")
        assert rc == 0
        loaded = load_queue()
        assert loaded["entries"][0]["status"] == "reviewed"

    def test_update_invalid_status(self, capsys):
        queue = {"entries": [{"contact": "Alice", "status": "prepared"}]}
        save_queue(queue)
        rc = update_status("Alice", "invalid_status")
        assert rc == 1

    def test_update_nonexistent_contact(self, capsys):
        queue = {"entries": []}
        save_queue(queue)
        rc = update_status("nobody", "reviewed")
        assert rc == 1

    def test_full_status_flow(self):
        queue = {"entries": [{"contact": "Bob", "status": "prepared"}]}
        save_queue(queue)
        for status in ["reviewed", "bundle_sent", "replied", "converted"]:
            rc = update_status("Bob", status)
            assert rc == 0
            loaded = load_queue()
            assert loaded["entries"][0]["status"] == status


# ---- Edge cases -------------------------------------------------------------

class TestEdgeCases:
    """Edge cases: empty name, duplicate contact, sanitize."""

    def test_empty_name_prepare(self, capsys):
        rc = prepare_response("")
        assert rc == 1

    def test_empty_name_prepare_none(self, capsys):
        rc = prepare_response(None)
        assert rc == 1

    def test_sanitize_name_basic(self):
        assert _sanitize_name("Alice Smith") == "alice_smith"

    def test_sanitize_name_special_chars(self):
        result = _sanitize_name("O'Brien-Smith!")
        assert " " not in result
        assert result.islower() or result.replace("_", "").replace("-", "").isalnum()

    def test_duplicate_contact_updates(self):
        """Preparing same contact twice should update, not duplicate."""
        queue = {"entries": [{
            "contact": "Anand Patronus",
            "company": "Patronus AI",
            "status": "prepared",
            "domain": "ML",
            "claims": ["ML_BENCH-01"],
            "bundle_path": "/old",
            "draft_path": "/old",
            "date": "2026-04-03",
            "outreach_subject": "",
        }]}
        save_queue(queue)

        # Run prepare with mocked bundle generation
        with patch("scripts.agent_responder.generate_bundle") as mock_bundle:
            mock_bundle.return_value = (
                Path(tempfile.mkdtemp()),
                {"result": {"pass": True}, "mtr_phase": "ML_BENCH-01"},
                True,
            )
            rc = prepare_response("Anand Patronus ML")

        loaded = load_queue()
        # Should still be exactly 1 entry, not 2
        assert len(loaded["entries"]) == 1

    def test_mapping_count(self):
        """Exactly 7 named mappings."""
        assert len(DOMAIN_MAPPINGS) == 7

    def test_all_mappings_have_required_keys(self):
        required = {"keywords", "claims", "mg_domain", "company",
                     "display_domain", "outreach_context",
                     "result_description", "next_step"}
        for key, mapping in DOMAIN_MAPPINGS.items():
            missing = required - set(mapping.keys())
            assert not missing, f"Mapping '{key}' missing keys: {missing}"

    def test_default_mapping_has_required_keys(self):
        required = {"claims", "mg_domain", "company", "display_domain",
                     "outreach_context", "result_description", "next_step"}
        missing = required - set(DEFAULT_MAPPING.keys())
        assert not missing, f"DEFAULT_MAPPING missing keys: {missing}"


# ---- CLI integration --------------------------------------------------------

class TestCLI:
    """CLI commands via subprocess."""

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_responder.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "Response Infrastructure" in result.stdout

    def test_cli_list_domains(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_responder.py"), "--list-domains"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "patronus" in result.stdout.lower()
