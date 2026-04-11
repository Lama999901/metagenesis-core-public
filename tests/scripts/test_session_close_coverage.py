"""Tests for scripts/session_close.py -- coverage gaps (_get_test_count, print_state, main)."""

import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import scripts.session_close as mod


@pytest.fixture
def sc_env(tmp_path, monkeypatch):
    """Redirect all file paths to temp dir (same pattern as test_session_close.py)."""
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        '# Test\n\n> Last updated: 2026-01-01\n\n---\n\n## CURRENT STATE (v0.9.0)\n\n```\nTests: 100\n```\n\n---\n',
        encoding="utf-8",
    )
    manifest = tmp_path / "system_manifest.json"
    manifest.write_text(
        json.dumps({"version": "0.9.0", "test_count": 2358}, indent=2),
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


# ---- _get_test_count tests ---------------------------------------------------


def test_get_test_count_success(sc_env, monkeypatch):
    """Mock subprocess.run to return pytest --co output with :: lines."""
    fake_output = (
        "tests/test_a.py::test_one\n"
        "tests/test_a.py::test_two\n"
        "tests/test_b.py::test_three\n"
        "\n3 tests collected\n"
    )
    mock_result = mock.Mock()
    mock_result.stdout = fake_output
    monkeypatch.setattr(subprocess, "run", mock.Mock(return_value=mock_result))
    count = mod._get_test_count()
    assert count == 3


def test_get_test_count_no_tests(sc_env, monkeypatch):
    """Empty output => 0 tests, falls back to manifest."""
    mock_result = mock.Mock()
    mock_result.stdout = "\nno tests ran\n"
    monkeypatch.setattr(subprocess, "run", mock.Mock(return_value=mock_result))
    count = mod._get_test_count()
    # No :: lines -> 0, but then len(lines)==0 is falsy -> returns 0
    assert count == 0


def test_get_test_count_timeout(sc_env, monkeypatch):
    """TimeoutExpired => fallback to manifest count."""
    monkeypatch.setattr(
        subprocess, "run",
        mock.Mock(side_effect=subprocess.TimeoutExpired(cmd="pytest", timeout=60)),
    )
    count = mod._get_test_count()
    assert count == 2358  # from manifest


def test_get_test_count_os_error(sc_env, monkeypatch):
    """OSError => fallback to manifest count."""
    monkeypatch.setattr(
        subprocess, "run",
        mock.Mock(side_effect=OSError("no such executable")),
    )
    count = mod._get_test_count()
    assert count == 2358


# ---- print_state tests -------------------------------------------------------


def test_print_state_basic(sc_env, capsys):
    state = {
        "version": "0.9.0",
        "tests": 2358,
        "real_verifications": 21,
        "ratio": 0.512,
        "last_session": "test session",
        "next_priority": "next thing",
    }
    mod.print_state(state)
    out = capsys.readouterr().out
    assert "v0.9.0" in out
    assert "2358" in out
    assert "51.2%" in out
    assert "test session" in out
    assert "next thing" in out


def test_print_state_door_open(sc_env, capsys):
    """When PROOF_INDEX exists, door should be OPEN."""
    state = {
        "version": "0.9.0", "tests": 100, "real_verifications": 0,
        "ratio": 0.0, "last_session": "x", "next_priority": "y",
    }
    mod.print_state(state)
    out = capsys.readouterr().out
    assert "OPEN" in out


def test_print_state_door_closed(sc_env, capsys, monkeypatch):
    """When PROOF_INDEX does not exist, door should be CLOSED."""
    monkeypatch.setattr(mod, "PROOF_INDEX", sc_env / "nonexistent" / "index.json")
    state = {
        "version": "0.9.0", "tests": 100, "real_verifications": 0,
        "ratio": 0.0, "last_session": "x", "next_priority": "y",
    }
    mod.print_state(state)
    out = capsys.readouterr().out
    assert "CLOSED" in out


# ---- main tests --------------------------------------------------------------


def test_main_read_flag(sc_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["session_close.py", "--read"])
    with mock.patch.object(mod, "read_state", return_value={
        "version": "0.9.0", "tests": 2358, "real_verifications": 21,
        "ratio": 0.512, "last_session": "test", "next_priority": "next",
    }):
        ret = mod.main()
    assert ret == 0
    out = capsys.readouterr().out
    assert "v0.9.0" in out


def test_main_summary_flag(sc_env, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv",
        ["session_close.py", "--summary", "Did something great"],
    )
    with mock.patch.object(mod, "close_session", return_value={
        "version": "0.9.0", "tests": 2358, "real_verifications": 21,
        "ratio": 0.512, "last_session": "Did something great", "next_priority": "next",
    }) as m:
        ret = mod.main()
    assert ret == 0
    m.assert_called_once()
    out = capsys.readouterr().out
    assert "Session closed" in out


def test_main_default_shows_state(sc_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["session_close.py"])
    with mock.patch.object(mod, "read_state", return_value={
        "version": "0.9.0", "tests": 100, "real_verifications": 0,
        "ratio": 0.0, "last_session": "none", "next_priority": "start",
    }):
        ret = mod.main()
    assert ret == 0
    out = capsys.readouterr().out
    assert "v0.9.0" in out
