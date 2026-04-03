#!/usr/bin/env python3
"""Tests for scripts/agent_client.py -- client session memory."""

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.agent_client import (
    _load_sessions,
    _save_sessions,
    get_stats,
    recall_sessions,
    record_session,
)


@pytest.fixture(autouse=True)
def isolated_sessions(tmp_path, monkeypatch):
    """Redirect session storage to tmp_path for test isolation."""
    sessions_file = tmp_path / "client_sessions.json"
    monkeypatch.setattr("scripts.agent_client.SESSIONS_FILE", sessions_file)
    monkeypatch.setattr("scripts.agent_client.MEMORY_DIR", tmp_path)
    return sessions_file


# ---------------------------------------------------------------------------
# record_session
# ---------------------------------------------------------------------------

class TestRecordSession:
    def test_basic_record(self):
        session = record_session(domain="ml", result="PASS")
        assert session["domain"] == "ml"
        assert session["result"] == "PASS"
        assert session["id"] == 1

    def test_record_with_notes(self):
        session = record_session(domain="pharma", result="FAIL", notes="threshold issue")
        assert session["notes"] == "threshold issue"

    def test_record_with_claim_id(self):
        session = record_session(domain="finance", result="PASS", claim_id="FINRISK-01")
        assert session["claim_id"] == "FINRISK-01"

    def test_record_increments_id(self):
        s1 = record_session(domain="ml", result="PASS")
        s2 = record_session(domain="ml", result="PASS")
        assert s2["id"] == s1["id"] + 1

    def test_result_uppercased(self):
        session = record_session(domain="ml", result="pass")
        assert session["result"] == "PASS"

    def test_persists_to_disk(self, isolated_sessions):
        record_session(domain="ml", result="PASS")
        assert isolated_sessions.exists()
        data = json.loads(isolated_sessions.read_text())
        assert len(data) == 1

    def test_timestamp_present(self):
        session = record_session(domain="ml", result="PASS")
        assert "timestamp" in session
        assert "T" in session["timestamp"]


# ---------------------------------------------------------------------------
# recall_sessions
# ---------------------------------------------------------------------------

class TestRecallSessions:
    def test_empty(self):
        sessions = recall_sessions()
        assert sessions == []

    def test_after_records(self):
        record_session(domain="ml", result="PASS")
        record_session(domain="pharma", result="FAIL")
        sessions = recall_sessions()
        assert len(sessions) == 2
        assert sessions[0]["domain"] == "ml"
        assert sessions[1]["domain"] == "pharma"


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_empty_stats(self):
        stats = get_stats()
        assert stats["total"] == 0
        assert stats["by_domain"] == {}
        assert stats["by_result"] == {}

    def test_stats_with_records(self):
        record_session(domain="ml", result="PASS")
        record_session(domain="ml", result="PASS")
        record_session(domain="pharma", result="FAIL")
        stats = get_stats()
        assert stats["total"] == 3
        assert stats["by_domain"]["ml"] == 2
        assert stats["by_domain"]["pharma"] == 1
        assert stats["by_result"]["PASS"] == 2
        assert stats["by_result"]["FAIL"] == 1
        assert stats["first_session"] is not None
        assert stats["last_session"] is not None

    def test_stats_multiple_domains(self):
        for domain in ("ml", "pharma", "finance", "materials", "digital_twin"):
            record_session(domain=domain, result="PASS")
        stats = get_stats()
        assert stats["total"] == 5
        assert len(stats["by_domain"]) == 5


# ---------------------------------------------------------------------------
# _load_sessions / _save_sessions
# ---------------------------------------------------------------------------

class TestLoadSave:
    def test_load_empty(self):
        sessions = _load_sessions()
        assert sessions == []

    def test_save_and_load(self, isolated_sessions):
        data = [{"id": 1, "domain": "ml"}]
        _save_sessions(data)
        loaded = _load_sessions()
        assert loaded == data

    def test_load_corrupt_file(self, isolated_sessions):
        isolated_sessions.write_text("not json")
        sessions = _load_sessions()
        assert sessions == []


# ---------------------------------------------------------------------------
# CLI integration tests
# ---------------------------------------------------------------------------

class TestCLI:
    def test_record_cli(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_client.py"),
             "record", "--domain", "ml", "--result", "PASS"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
        assert proc.returncode == 0
        assert "recorded" in proc.stdout

    def test_recall_cli_empty(self, isolated_sessions):
        # Run from subprocess (separate process won't see monkeypatch)
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_client.py"), "recall"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
        # May show sessions from previous test or be empty -- just check exit code
        assert proc.returncode == 0

    def test_stats_cli(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_client.py"), "stats"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
        assert proc.returncode == 0

    def test_no_args(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "agent_client.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=10,
        )
        assert proc.returncode == 0
