"""Tests for agent_pr_creator.py detect_pilot_queue_stale() — detector #5."""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _patch_repo_root(monkeypatch, tmp_path):
    """Redirect REPO_ROOT to tmp_path so tests don't touch real files."""
    import scripts.agent_pr_creator as mod
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    (tmp_path / "reports").mkdir(parents=True, exist_ok=True)
    return tmp_path


def _write_queue(tmp_path, entries):
    """Write queue in the same dict format that agent_pilot.py produces."""
    queue_path = tmp_path / "reports" / "pilot_queue.json"
    with open(queue_path, "w", encoding="utf-8") as f:
        json.dump({"entries": entries}, f)


class TestDetectPilotQueueStale:
    """Tests for detect_pilot_queue_stale detector."""

    def test_no_queue_file(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        result = detect_pilot_queue_stale()
        assert result == []

    def test_empty_queue(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        _write_queue(tmp_path, [])
        result = detect_pilot_queue_stale()
        assert result == []

    def test_fresh_pending_not_stale(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        now = datetime.now(timezone.utc).isoformat()
        _write_queue(tmp_path, [
            {"email": "a@test.com", "status": "pending",
             "processed_at": now, "domain_detected": "ml"}
        ])
        result = detect_pilot_queue_stale()
        assert result == []

    def test_old_pending_is_stale(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        old = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        _write_queue(tmp_path, [
            {"email": "stale@test.com", "status": "pending",
             "processed_at": old, "domain_detected": "pharma"}
        ])
        result = detect_pilot_queue_stale()
        assert len(result) == 1
        assert "stale@test.com" in result[0]
        assert "STALE" in result[0]

    def test_old_processed_is_stale(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        _write_queue(tmp_path, [
            {"email": "proc@test.com", "status": "processed",
             "processed_at": old, "domain_detected": "finance"}
        ])
        result = detect_pilot_queue_stale()
        assert len(result) == 1
        assert "proc@test.com" in result[0]

    def test_sent_entries_not_flagged(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        old = (datetime.now(timezone.utc) - timedelta(hours=72)).isoformat()
        _write_queue(tmp_path, [
            {"email": "done@test.com", "status": "sent",
             "processed_at": old, "domain_detected": "ml"}
        ])
        result = detect_pilot_queue_stale()
        assert result == []

    def test_mixed_entries(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        old = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
        fresh = datetime.now(timezone.utc).isoformat()
        _write_queue(tmp_path, [
            {"email": "stale@test.com", "status": "pending",
             "processed_at": old, "domain_detected": "ml"},
            {"email": "fresh@test.com", "status": "pending",
             "processed_at": fresh, "domain_detected": "pharma"},
            {"email": "done@test.com", "status": "sent",
             "processed_at": old, "domain_detected": "materials"},
        ])
        result = detect_pilot_queue_stale()
        assert len(result) == 1
        assert "stale@test.com" in result[0]

    def test_malformed_json(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        queue_path = tmp_path / "reports" / "pilot_queue.json"
        queue_path.write_text("not valid json", encoding="utf-8")
        result = detect_pilot_queue_stale()
        assert result == []

    def test_uses_submitted_at_fallback(self, tmp_path):
        from scripts.agent_pr_creator import detect_pilot_queue_stale
        old = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        _write_queue(tmp_path, [
            {"email": "sub@test.com", "status": "pending",
             "submitted_at": old, "domain_detected": "ml"}
        ])
        result = detect_pilot_queue_stale()
        assert len(result) == 1
