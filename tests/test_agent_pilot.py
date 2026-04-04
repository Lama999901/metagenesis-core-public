#!/usr/bin/env python3
"""Tests for scripts/agent_pilot.py -- Pilot Onboarding Agent.

Covers all PILOT requirements:
  PILOT-01: CSV parsing + domain detection
  PILOT-02: Bundle generation (mocked mg_client)
  PILOT-03: Email draft content
  PILOT-04: Queue state management
  PILOT-05: CLI flags (--help, --status, --mark-sent)
"""

import csv
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_pilot import (
    _find_entry_by_email,
    _sanitize_name,
    detect_domain,
    generate_draft,
    load_queue,
    mark_sent,
    read_submissions,
    save_queue,
    show_status,
)


# ---------------------------------------------------------------------------
# PILOT-01: Domain Detection
# ---------------------------------------------------------------------------


class TestDomainDetection:
    """Test detect_domain() keyword matching for all 5 domains + fallback."""

    def test_detect_ml_accuracy(self):
        assert detect_domain("ML model accuracy benchmark") == "ml"

    def test_detect_ml_neural(self):
        assert detect_domain("neural network training") == "ml"

    def test_detect_ml_deep_learning(self):
        assert detect_domain("deep learning inference pipeline") == "ml"

    def test_detect_ml_ai(self):
        assert detect_domain("AI classification model") == "ml"

    def test_detect_pharma_drug(self):
        assert detect_domain("drug compound ADMET prediction") == "pharma"

    def test_detect_pharma_fda(self):
        assert detect_domain("FDA clinical trial compound analysis") == "pharma"

    def test_detect_pharma_biotech(self):
        assert detect_domain("pharmaceutical biotech molecule toxicity") == "pharma"

    def test_detect_materials_steel(self):
        assert detect_domain("steel material calibration") == "materials"

    def test_detect_materials_aluminum(self):
        assert detect_domain("aluminum modulus measurement") == "materials"

    def test_detect_materials_copper(self):
        assert detect_domain("copper conductivity alloy test") == "materials"

    def test_detect_materials_titanium(self):
        assert detect_domain("titanium composite metal") == "materials"

    def test_detect_finance_var(self):
        assert detect_domain("VaR risk model") == "finance"

    def test_detect_finance_basel(self):
        assert detect_domain("Basel III portfolio credit analysis") == "finance"

    def test_detect_finance_market(self):
        assert detect_domain("financial trading market risk hedge") == "finance"

    def test_detect_digital_twin_fem(self):
        assert detect_domain("FEM displacement sensor") == "digital_twin"

    def test_detect_digital_twin_iot(self):
        assert detect_domain("IoT sensor digital twin actuator") == "digital_twin"

    def test_detect_digital_twin_simulation(self):
        assert detect_domain("simulation calibration twin") == "digital_twin"

    def test_detect_unknown_defaults_to_ml(self):
        assert detect_domain("random gibberish text xyz") == "ml"

    def test_detect_empty_defaults_to_ml(self):
        assert detect_domain("") == "ml"

    def test_detect_case_insensitive(self):
        assert detect_domain("PHARMA Drug ADMET") == "pharma"

    def test_detect_multiple_ml_keywords(self):
        assert detect_domain("AI deep learning neural network model") == "ml"

    def test_detect_highest_score_wins(self):
        # "drug pharma fda clinical" has 4 pharma keywords vs 1 ml keyword
        assert detect_domain("drug pharma fda clinical model") == "pharma"


# ---------------------------------------------------------------------------
# PILOT-01: CSV Parsing
# ---------------------------------------------------------------------------


class TestCSVParsing:
    """Test read_submissions() CSV file handling."""

    def _write_csv(self, tmp_path, rows, headers=None):
        """Helper: write CSV file and return path."""
        if headers is None:
            headers = ["name", "email", "company", "domain_description", "date"]
        csv_path = tmp_path / "submissions.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
        return str(csv_path)

    def test_read_valid_csv(self, tmp_path):
        path = self._write_csv(tmp_path, [
            ["Alice", "alice@example.com", "Acme", "ML accuracy benchmark", "2026-04-01"],
            ["Bob", "bob@example.com", "Corp", "drug compound analysis", "2026-04-02"],
        ])
        result = read_submissions(path)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["email"] == "alice@example.com"
        assert result[0]["company"] == "Acme"
        assert result[0]["domain_description"] == "ML accuracy benchmark"
        assert result[1]["name"] == "Bob"

    def test_read_empty_csv(self, tmp_path):
        path = self._write_csv(tmp_path, [])
        result = read_submissions(path)
        assert result == []

    def test_read_skips_missing_name(self, tmp_path):
        path = self._write_csv(tmp_path, [
            ["", "alice@example.com", "Acme", "ML", "2026-04-01"],
            ["Bob", "bob@example.com", "Corp", "drug", "2026-04-02"],
        ])
        result = read_submissions(path)
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_read_skips_missing_email(self, tmp_path):
        path = self._write_csv(tmp_path, [
            ["Alice", "", "Acme", "ML", "2026-04-01"],
            ["Bob", "bob@example.com", "Corp", "drug", "2026-04-02"],
        ])
        result = read_submissions(path)
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_read_handles_whitespace(self, tmp_path):
        path = self._write_csv(tmp_path, [
            ["  Alice  ", " alice@example.com ", " Acme ", " ML model ", "2026-04-01"],
        ])
        result = read_submissions(path)
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
        assert result[0]["email"] == "alice@example.com"
        assert result[0]["company"] == "Acme"
        assert result[0]["domain_description"] == "ML model"

    def test_read_nonexistent_file(self):
        result = read_submissions("/nonexistent/path/file.csv")
        assert result == []

    def test_read_preserves_date(self, tmp_path):
        path = self._write_csv(tmp_path, [
            ["Alice", "alice@example.com", "Acme", "ML", "2026-04-01"],
        ])
        result = read_submissions(path)
        assert result[0]["date"] == "2026-04-01"


# ---------------------------------------------------------------------------
# PILOT-04: Queue Management
# ---------------------------------------------------------------------------


class TestQueueManagement:
    """Test load_queue / save_queue / mark_sent and state transitions."""

    def test_load_queue_creates_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", tmp_path / "q.json")
        queue = load_queue()
        assert queue == {"entries": []}

    def test_save_load_roundtrip(self, tmp_path, monkeypatch):
        q_path = tmp_path / "reports" / "pilot_queue.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)

        original = {"entries": [
            {"name": "Alice", "email": "alice@example.com", "status": "processed"},
        ]}
        save_queue(original)
        loaded = load_queue()
        assert loaded["entries"][0]["name"] == "Alice"
        assert loaded["entries"][0]["status"] == "processed"

    def test_queue_entry_schema(self, tmp_path, monkeypatch):
        """Processed entries must have required fields."""
        q_path = tmp_path / "q.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)

        entry = {
            "name": "Alice",
            "email": "alice@example.com",
            "status": "processed",
            "domain_detected": "ml",
            "processed_at": "2026-04-01T00:00:00+00:00",
        }
        save_queue({"entries": [entry]})
        loaded = load_queue()
        e = loaded["entries"][0]
        for key in ("name", "email", "status", "domain_detected", "processed_at"):
            assert key in e, f"Missing required field: {key}"

    def test_mark_sent_transitions(self, tmp_path, monkeypatch):
        q_path = tmp_path / "q.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)

        queue = {"entries": [
            {"name": "Alice", "email": "alice@example.com", "status": "processed"},
        ]}
        save_queue(queue)

        rc = mark_sent("alice@example.com")
        assert rc == 0

        updated = load_queue()
        assert updated["entries"][0]["status"] == "sent"
        assert "sent_at" in updated["entries"][0]

    def test_mark_sent_not_found(self, tmp_path, monkeypatch):
        q_path = tmp_path / "q.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)
        save_queue({"entries": []})

        rc = mark_sent("nobody@example.com")
        assert rc == 1

    def test_mark_sent_already_sent(self, tmp_path, monkeypatch):
        q_path = tmp_path / "q.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)
        save_queue({"entries": [
            {"name": "Alice", "email": "alice@example.com", "status": "sent"},
        ]})

        rc = mark_sent("alice@example.com")
        assert rc == 1

    def test_find_entry_by_email(self):
        queue = {"entries": [
            {"email": "alice@example.com", "name": "Alice"},
            {"email": "bob@example.com", "name": "Bob"},
        ]}
        assert _find_entry_by_email(queue, "bob@example.com")["name"] == "Bob"
        assert _find_entry_by_email(queue, "nobody@x.com") is None

    def test_find_entry_case_insensitive(self):
        queue = {"entries": [
            {"email": "Alice@Example.COM", "name": "Alice"},
        ]}
        assert _find_entry_by_email(queue, "alice@example.com")["name"] == "Alice"


# ---------------------------------------------------------------------------
# PILOT-03: Email Draft Generation
# ---------------------------------------------------------------------------


class TestEmailDrafts:
    """Test generate_draft() content requirements."""

    def _make_entry(self, name="Alice Smith", domain="ml"):
        return {
            "name": name,
            "email": f"{name.split()[0].lower()}@example.com",
            "company": "Acme Corp",
            "domain_description": "ML accuracy benchmark",
            "domain_detected": domain,
            "date": "2026-04-01",
        }

    def _make_claim_result(self):
        return {
            "mtr_phase": "ML_BENCH-01",
            "result": {"pass": True, "actual_accuracy": 0.91},
            "execution_trace": [
                {"step": 1, "name": "init_params", "hash": "aaa"},
                {"step": 2, "name": "compute", "hash": "bbb"},
                {"step": 3, "name": "metrics", "hash": "ccc"},
                {"step": 4, "name": "threshold_check", "hash": "ddd"},
            ],
            "trace_root_hash": "ddd",
        }

    def test_draft_created(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry()
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", True)
        assert draft_path.exists()
        assert draft_path.suffix == ".txt"

    def test_draft_contains_pass(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry()
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", True)
        content = draft_path.read_text(encoding="utf-8")
        assert "PASS" in content

    def test_draft_contains_questions_line(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry()
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", True)
        content = draft_path.read_text(encoding="utf-8")
        assert "Questions? Reply to this email." in content

    def test_draft_contains_greeting(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry()
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", True)
        content = draft_path.read_text(encoding="utf-8")
        assert "Hi Alice Smith" in content

    def test_draft_contains_domain(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry(domain="pharma")
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", True)
        content = draft_path.read_text(encoding="utf-8")
        assert "pharma" in content

    def test_draft_fail_mentions_manual_review(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry()
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", False)
        content = draft_path.read_text(encoding="utf-8")
        assert "FAIL" in content
        assert "manual review" in content.lower()

    def test_draft_fail_still_has_questions(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        entry = self._make_entry()
        draft_path = generate_draft(entry, self._make_claim_result(), tmp_path / "bundle", False)
        content = draft_path.read_text(encoding="utf-8")
        assert "Questions? Reply to this email." in content


# ---------------------------------------------------------------------------
# PILOT-02: Bundle generation (mocked mg_client)
# ---------------------------------------------------------------------------


class TestBundleGeneration:
    """Test process_submissions with mocked mg_client calls."""

    def _write_csv(self, tmp_path, rows):
        headers = ["name", "email", "company", "domain_description", "date"]
        csv_path = tmp_path / "submissions.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
        return str(csv_path)

    def _mock_claim_result(self):
        return {
            "mtr_phase": "ML_BENCH-01",
            "result": {"pass": True, "actual_accuracy": 0.91},
            "execution_trace": [
                {"step": 1, "name": "init_params", "hash": "aaa"},
                {"step": 2, "name": "compute", "hash": "bbb"},
                {"step": 3, "name": "metrics", "hash": "ccc"},
                {"step": 4, "name": "threshold_check", "hash": "ddd"},
            ],
            "trace_root_hash": "ddd",
        }

    def test_process_creates_bundle_and_draft(self, tmp_path, monkeypatch):
        """Full pipeline: CSV -> domain detect -> mock bundle -> draft -> queue."""
        csv_path = self._write_csv(tmp_path, [
            ["Alice", "alice@example.com", "Acme", "ML accuracy benchmark", "2026-04-01"],
        ])

        q_path = tmp_path / "pilot_queue.json"
        drafts_dir = tmp_path / "pilot_drafts"
        bundles_dir = tmp_path / "pilot_bundles"

        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", drafts_dir)
        monkeypatch.setattr("scripts.agent_pilot.BUNDLES_DIR", bundles_dir)

        fake_bundle_dir = tmp_path / "fake_bundle"
        fake_bundle_dir.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr("scripts.agent_pilot.run_claim", lambda domain, **kw: self._mock_claim_result())
        monkeypatch.setattr("scripts.agent_pilot.create_bundle", lambda result, output_dir=None: fake_bundle_dir)
        monkeypatch.setattr("scripts.agent_pilot.verify_bundle", lambda bd: (True, []))

        from scripts.agent_pilot import process_submissions
        rc = process_submissions(csv_path)
        assert rc == 0

        # Queue was updated
        assert q_path.exists()
        queue = json.loads(q_path.read_text(encoding="utf-8"))
        assert len(queue["entries"]) == 1
        assert queue["entries"][0]["status"] == "processed"
        assert queue["entries"][0]["domain_detected"] == "ml"

        # Draft was created
        assert drafts_dir.exists()
        drafts = list(drafts_dir.glob("*.txt"))
        assert len(drafts) == 1

    def test_process_skips_already_processed(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [
            ["Alice", "alice@example.com", "Acme", "ML", "2026-04-01"],
        ])

        q_path = tmp_path / "pilot_queue.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        monkeypatch.setattr("scripts.agent_pilot.BUNDLES_DIR", tmp_path / "bundles")

        # Pre-populate queue
        save_queue({"entries": [
            {"name": "Alice", "email": "alice@example.com", "status": "processed"},
        ]})

        # run_claim should NOT be called
        mock_run = mock.MagicMock()
        monkeypatch.setattr("scripts.agent_pilot.run_claim", mock_run)
        monkeypatch.setattr("scripts.agent_pilot.create_bundle", mock.MagicMock())
        monkeypatch.setattr("scripts.agent_pilot.verify_bundle", mock.MagicMock())

        from scripts.agent_pilot import process_submissions
        process_submissions(csv_path)
        mock_run.assert_not_called()

    def test_process_handles_claim_failure(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [
            ["Alice", "alice@example.com", "Acme", "ML", "2026-04-01"],
        ])

        q_path = tmp_path / "pilot_queue.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)
        monkeypatch.setattr("scripts.agent_pilot.DRAFTS_DIR", tmp_path / "drafts")
        monkeypatch.setattr("scripts.agent_pilot.BUNDLES_DIR", tmp_path / "bundles")

        monkeypatch.setattr("scripts.agent_pilot.run_claim", mock.MagicMock(side_effect=RuntimeError("claim failed")))

        from scripts.agent_pilot import process_submissions
        rc = process_submissions(csv_path)
        assert rc == 1  # failure

    def test_process_empty_csv_returns_1(self, tmp_path, monkeypatch):
        csv_path = self._write_csv(tmp_path, [])
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", tmp_path / "q.json")

        from scripts.agent_pilot import process_submissions
        rc = process_submissions(csv_path)
        assert rc == 1


# ---------------------------------------------------------------------------
# PILOT-05: CLI
# ---------------------------------------------------------------------------


class TestCLI:
    """Test CLI entry points."""

    def test_help_flag(self):
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_pilot.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "agent_pilot" in result.stdout or "Pilot" in result.stdout

    def test_status_empty_queue(self, tmp_path, monkeypatch):
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", tmp_path / "q.json")
        rc = show_status()
        assert rc == 0

    def test_status_with_entries(self, tmp_path, monkeypatch, capsys):
        q_path = tmp_path / "q.json"
        monkeypatch.setattr("scripts.agent_pilot.QUEUE_PATH", q_path)
        save_queue({"entries": [
            {"name": "Alice", "email": "a@x.com", "domain_detected": "ml",
             "status": "processed", "processed_at": "2026-04-01T00:00:00"},
            {"name": "Bob", "email": "b@x.com", "domain_detected": "pharma",
             "status": "sent", "processed_at": "2026-04-01T00:00:00"},
        ]})
        rc = show_status()
        assert rc == 0
        out = capsys.readouterr().out
        assert "Alice" in out
        assert "Bob" in out
        assert "Processed: 1" in out
        assert "Sent: 1" in out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    """Test internal helpers."""

    def test_sanitize_name_basic(self):
        assert _sanitize_name("Alice Smith") == "alice_smith"

    def test_sanitize_name_special_chars(self):
        result = _sanitize_name("Dr. Alice O'Brien")
        assert " " not in result
        assert result == result.lower()

    def test_sanitize_name_extra_spaces(self):
        result = _sanitize_name("  Alice   Smith  ")
        assert "  " not in result
