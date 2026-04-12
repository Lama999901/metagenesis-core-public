"""Tests for scripts/session_close.py — cross-session memory."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.session_close import (
    _get_ratio,
    _get_version,
    _read_manifest,
    _write_manifest,
    append_session_log,
    close_session,
    read_state,
    update_claude_md,
    update_manifest_session,
    update_what_we_learned,
)


@pytest.fixture
def tmp_env(tmp_path, monkeypatch):
    """Redirect all file paths to temp dir."""
    import scripts.session_close as mod

    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        '# Test\n\n> Last updated: 2026-01-01\n\n---\n\n## CURRENT STATE (v1.0.0-rc1)\n\n```\nTests: 100\n```\n\n---\n',
        encoding="utf-8",
    )
    manifest = tmp_path / "system_manifest.json"
    manifest.write_text(
        json.dumps({"version": "1.0.0-rc1", "test_count": 2043}, indent=2),
        encoding="utf-8",
    )
    proof_lib = tmp_path / "proof_library"
    proof_lib.mkdir()
    index = proof_lib / "index.json"
    index.write_text("[]", encoding="utf-8")
    session_log = tmp_path / "session_log.jsonl"

    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mod, "CLAUDE_MD", claude_md)
    monkeypatch.setattr(mod, "MANIFEST", manifest)
    monkeypatch.setattr(mod, "SESSION_LOG", session_log)
    monkeypatch.setattr(mod, "PROOF_INDEX", index)
    monkeypatch.setattr(mod, "WHAT_WE_LEARNED", proof_lib / "WHAT_WE_LEARNED.md")

    return tmp_path


# ── Manifest Tests ──────────────────────────────────────────────────────────


class TestManifest:
    def test_read_manifest(self, tmp_env):
        m = _read_manifest()
        assert m["version"] == "1.0.0-rc1"
        assert m["test_count"] == 2043

    def test_write_manifest_roundtrip(self, tmp_env):
        m = _read_manifest()
        m["new_field"] = "hello"
        _write_manifest(m)
        m2 = _read_manifest()
        assert m2["new_field"] == "hello"

    def test_read_missing_manifest(self, tmp_env):
        import scripts.session_close as mod
        mod.MANIFEST.unlink()
        m = _read_manifest()
        assert m == {}


# ── Ratio Tests ─────────────────────────────────────────────────────────────


class TestRatio:
    def test_empty_index_returns_zero(self, tmp_env):
        count, ratio = _get_ratio()
        assert count == 0
        assert ratio == 0.0

    def test_one_real_entry(self, tmp_env):
        import scripts.session_close as mod
        mod.PROOF_INDEX.write_text(
            json.dumps([{"id": "test-1", "is_synthetic": False}]),
            encoding="utf-8",
        )
        count, ratio = _get_ratio()
        assert count == 1
        assert abs(ratio - 1 / 21) < 0.001

    def test_synthetic_entries_not_counted(self, tmp_env):
        import scripts.session_close as mod
        mod.PROOF_INDEX.write_text(
            json.dumps([
                {"id": "real-1", "is_synthetic": False},
                {"id": "synth-1", "is_synthetic": True},
            ]),
            encoding="utf-8",
        )
        count, ratio = _get_ratio()
        assert count == 1

    def test_missing_index(self, tmp_env):
        import scripts.session_close as mod
        mod.PROOF_INDEX.unlink()
        count, ratio = _get_ratio()
        assert count == 0
        assert ratio == 0.0


# ── State Read Tests ────────────────────────────────────────────────────────


class TestReadState:
    def test_returns_dict_with_required_keys(self, tmp_env):
        state = read_state()
        assert "version" in state
        assert "tests" in state
        assert "real_verifications" in state
        assert "ratio" in state
        assert "last_session" in state
        assert "next_priority" in state

    def test_version_from_manifest(self, tmp_env):
        state = read_state()
        assert state["version"] == "1.0.0-rc1"

    def test_no_previous_session(self, tmp_env):
        state = read_state()
        assert "No previous session" in state["last_session"]


# ── Session Log Tests ───────────────────────────────────────────────────────


class TestSessionLog:
    def test_append_creates_file(self, tmp_env):
        import scripts.session_close as mod
        state = {"tests": 100, "ratio": 0.05, "real_verifications": 1}
        append_session_log("test summary", state, ["file1"], "next thing")
        assert mod.SESSION_LOG.exists()
        lines = mod.SESSION_LOG.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["summary"] == "test summary"
        assert entry["tests"] == 100
        assert entry["next"] == "next thing"

    def test_append_accumulates(self, tmp_env):
        import scripts.session_close as mod
        state = {"tests": 100, "ratio": 0.0, "real_verifications": 0}
        append_session_log("first", state, [], "n1")
        append_session_log("second", state, [], "n2")
        lines = mod.SESSION_LOG.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["summary"] == "first"
        assert json.loads(lines[1])["summary"] == "second"

    def test_read_state_picks_up_last_session(self, tmp_env):
        import scripts.session_close as mod
        state = {"tests": 100, "ratio": 0.0, "real_verifications": 0}
        append_session_log("my summary", state, [], "my next")
        new_state = read_state()
        assert "my summary" in new_state["last_session"]
        assert new_state["next_priority"] == "my next"


# ── CLAUDE.md Update Tests ──────────────────────────────────────────────────


class TestClaudeMdUpdate:
    def test_updates_current_state_section(self, tmp_env):
        import scripts.session_close as mod
        state = {"version": "1.0.0-rc1", "tests": 2043, "ratio": 0.048, "real_verifications": 1}
        update_claude_md(state, "test session", "do next thing")
        text = mod.CLAUDE_MD.read_text(encoding="utf-8")
        assert "2043 passing" in text
        assert "4.8%" in text
        assert "test session" in text

    def test_updates_header_date(self, tmp_env):
        import scripts.session_close as mod
        state = {"version": "1.0.0-rc1", "tests": 2043, "ratio": 0.0, "real_verifications": 0}
        update_claude_md(state, "s", "n")
        text = mod.CLAUDE_MD.read_text(encoding="utf-8")
        assert "2026-04-" in text or "Last updated:" in text


# ── Manifest Session Update Tests ───────────────────────────────────────────


class TestManifestSession:
    def test_adds_session_fields(self, tmp_env):
        update_manifest_session("my summary", "my next")
        m = _read_manifest()
        assert m["last_session_summary"] == "my summary"
        assert m["next_priority"] == "my next"
        assert "last_session_date" in m

    def test_truncates_long_summary(self, tmp_env):
        long = "x" * 500
        update_manifest_session(long, "n")
        m = _read_manifest()
        assert len(m["last_session_summary"]) <= 200


# ── What We Learned Tests ──────────────────────────────────────────────────


class TestWhatWeLearned:
    def test_creates_file_on_first_entry(self, tmp_env):
        import scripts.session_close as mod
        mod.PROOF_INDEX.write_text(
            json.dumps([{
                "id": "test-entry-1",
                "domain": "test",
                "what_proved": "determinism",
                "what_not_proved": "correctness",
                "duration_ms": 100,
            }]),
            encoding="utf-8",
        )
        state = {"ratio": 0.05, "real_verifications": 1}
        update_what_we_learned(state)
        assert mod.WHAT_WE_LEARNED.exists()
        text = mod.WHAT_WE_LEARNED.read_text(encoding="utf-8")
        assert "test-entry-1" in text
        assert "determinism" in text

    def test_no_duplicates(self, tmp_env):
        import scripts.session_close as mod
        mod.PROOF_INDEX.write_text(
            json.dumps([{"id": "entry-1", "domain": "t", "what_proved": "p", "what_not_proved": "n", "duration_ms": 1}]),
            encoding="utf-8",
        )
        state = {"ratio": 0.05, "real_verifications": 1}
        update_what_we_learned(state)
        update_what_we_learned(state)
        text = mod.WHAT_WE_LEARNED.read_text(encoding="utf-8")
        assert text.count("entry-1") == 1


# ── Integration: close_session ──────────────────────────────────────────────


class TestCloseSession:
    def test_full_close(self, tmp_env):
        import scripts.session_close as mod
        state = close_session("integration test", "next step", ["file1"])
        assert mod.SESSION_LOG.exists()
        m = _read_manifest()
        assert m["last_session_summary"] == "integration test"
        text = mod.CLAUDE_MD.read_text(encoding="utf-8")
        assert "integration test" in text
