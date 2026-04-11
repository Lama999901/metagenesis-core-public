"""Tests for scripts/mg_payment_tracker.py -- coverage boost."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import scripts.mg_payment_tracker as mod


@pytest.fixture
def funnel_env(tmp_path, monkeypatch):
    """Redirect FUNNEL_PATH to tmp_path."""
    funnel_path = tmp_path / "payment_funnel.json"
    monkeypatch.setattr(mod, "FUNNEL_PATH", funnel_path)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    return funnel_path


# ---- _load_funnel tests ------------------------------------------------------


def test_load_funnel_missing_file(funnel_env):
    data = mod._load_funnel()
    assert "sessions" in data
    assert data["sessions"]["started_onboarding"] == 0
    assert data["conversion_rate"] == 0.0


def test_load_funnel_corrupt_json(funnel_env):
    funnel_env.write_text("not json!", encoding="utf-8")
    data = mod._load_funnel()
    assert data["sessions"]["started_onboarding"] == 0


def test_load_funnel_valid(funnel_env):
    valid_data = {
        "sessions": {"started_onboarding": 5, "completed_verification": 3,
                      "saw_payment": 2, "converted": 1},
        "by_domain": {},
        "by_language": {},
        "conversion_rate": 0.2,
        "last_updated": "2026-04-10T00:00:00Z",
    }
    funnel_env.write_text(json.dumps(valid_data), encoding="utf-8")
    data = mod._load_funnel()
    assert data["sessions"]["started_onboarding"] == 5
    assert data["conversion_rate"] == 0.2


# ---- _save_funnel tests ------------------------------------------------------


def test_save_funnel_creates_file(funnel_env):
    data = mod._load_funnel()
    mod._save_funnel(data)
    assert funnel_env.exists()
    saved = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert "last_updated" in saved
    assert saved["last_updated"] is not None


def test_save_funnel_conversion_rate(funnel_env):
    data = mod._load_funnel()
    data["sessions"]["started_onboarding"] = 10
    data["sessions"]["converted"] = 2
    mod._save_funnel(data)
    saved = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert abs(saved["conversion_rate"] - 0.2) < 0.001


def test_save_funnel_zero_division(funnel_env):
    data = mod._load_funnel()
    data["sessions"]["started_onboarding"] = 0
    data["sessions"]["converted"] = 0
    mod._save_funnel(data)
    saved = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert saved["conversion_rate"] == 0.0


# ---- track_event tests -------------------------------------------------------


def test_track_event_valid_stage(funnel_env):
    mod.track_event("started_onboarding")
    data = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert data["sessions"]["started_onboarding"] == 1


def test_track_event_with_domain(funnel_env):
    mod.track_event("started_onboarding", domain="ml")
    data = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert data["by_domain"]["ml"]["started_onboarding"] == 1


def test_track_event_with_language(funnel_env):
    mod.track_event("started_onboarding", language="ja")
    data = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert data["by_language"]["ja"]["started_onboarding"] == 1


def test_track_event_invalid_stage(funnel_env):
    mod.track_event("invalid_stage")
    assert not funnel_env.exists()


def test_track_event_multiple_stages(funnel_env):
    mod.track_event("started_onboarding", domain="ml")
    mod.track_event("completed_verification", domain="ml")
    mod.track_event("converted", domain="ml")
    data = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert data["sessions"]["started_onboarding"] == 1
    assert data["sessions"]["completed_verification"] == 1
    assert data["sessions"]["converted"] == 1
    assert data["by_domain"]["ml"]["converted"] == 1


# ---- show_stats tests --------------------------------------------------------


def test_show_stats_empty(funnel_env, capsys):
    mod.show_stats()
    out = capsys.readouterr().out
    assert "No funnel data yet" in out


def test_show_stats_with_data(funnel_env, capsys):
    mod.track_event("started_onboarding", domain="ml", language="en")
    mod.track_event("converted", domain="ml", language="en")
    mod.show_stats()
    out = capsys.readouterr().out
    assert "Conversion Funnel" in out
    assert "Started Onboarding" in out
    assert "ml" in out or "Ml" in out


# ---- main tests --------------------------------------------------------------


def test_main_stats(funnel_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["mg_payment_tracker.py", "--stats"])
    ret = mod.main()
    assert ret == 0


def test_main_reset(funnel_env, monkeypatch, capsys):
    # First add some data
    mod.track_event("started_onboarding")
    # Then reset
    monkeypatch.setattr(sys, "argv", ["mg_payment_tracker.py", "--reset"])
    ret = mod.main()
    assert ret == 0
    data = json.loads(funnel_env.read_text(encoding="utf-8"))
    assert data["sessions"]["started_onboarding"] == 0
    out = capsys.readouterr().out
    assert "reset" in out.lower()


def test_main_default_shows_stats(funnel_env, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["mg_payment_tracker.py"])
    ret = mod.main()
    assert ret == 0
