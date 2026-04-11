"""Tests for scripts/mg_onboard.py -- coverage boost for onboarding CLI."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_onboard import (
    _call_claude,
    _detect_language,
    _log_session,
    detect_domain_local,
    main,
    run_onboarding,
)


# ---- detect_domain_local tests -----------------------------------------------


def test_detect_domain_ml():
    domain, claim = detect_domain_local("I train a neural network for classification")
    assert domain == "ml"
    assert claim == "ML_BENCH-01"


def test_detect_domain_pharma():
    domain, claim = detect_domain_local("ADMET drug solubility prediction")
    assert domain == "pharma"
    assert claim == "PHARMA-01"


def test_detect_domain_finance():
    domain, claim = detect_domain_local("Basel III value at risk portfolio")
    assert domain == "finance"
    assert claim == "FINRISK-01"


def test_detect_domain_materials():
    domain, claim = detect_domain_local("aluminum young's modulus calibration")
    assert domain == "materials"
    assert claim == "MTR-1"


def test_detect_domain_digital_twin():
    domain, claim = detect_domain_local("finite element simulation displacement mesh")
    assert domain == "digital_twin"
    assert claim == "DT-FEM-01"


def test_detect_domain_physics():
    domain, claim = detect_domain_local("boltzmann constant thermodynamics entropy")
    assert domain == "physics"
    assert claim == "PHYS-01"


def test_detect_domain_systems():
    domain, claim = detect_domain_local("system identification arx transfer function")
    assert domain == "systems"
    assert claim == "SYSID-01"


def test_detect_domain_agent():
    domain, claim = detect_domain_local("agent drift monitoring pipeline ci/cd")
    assert domain == "agent"
    assert claim == "AGENT-DRIFT-01"


def test_detect_domain_fallback():
    """Unknown text should fall back to ml."""
    domain, claim = detect_domain_local("completely unrelated random gibberish text")
    assert domain == "ml"
    assert claim == "ML_BENCH-01"


# ---- _detect_language tests --------------------------------------------------


def test_detect_language_english():
    assert _detect_language("I work with machine learning models") == "en"


def test_detect_language_spanish():
    assert _detect_language("Trabajo con modelos de prediccion") == "es"


def test_detect_language_french():
    assert _detect_language("Je travaille avec des simulations") == "fr"


def test_detect_language_german():
    assert _detect_language("Ich arbeite mit Berechnung") == "de"


def test_detect_language_japanese():
    # Hiragana characters
    assert _detect_language("\u3053\u3093\u306b\u3061\u306f") == "ja"


def test_detect_language_korean():
    assert _detect_language("\uc548\ub155\ud558\uc138\uc694") == "ko"


def test_detect_language_chinese():
    assert _detect_language("\u836f\u7269\u7814\u7a76") == "zh"


def test_detect_language_russian():
    assert _detect_language("\u041f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440") == "ru"


def test_detect_language_unknown_defaults_english():
    assert _detect_language("asdf xyz 12345") == "en"


# ---- _log_session tests -----------------------------------------------------


def test_log_session_creates_file(tmp_path, monkeypatch):
    """_log_session writes a valid JSON array to the log file."""
    monkeypatch.setattr("scripts.mg_onboard.REPO_ROOT", tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    entry = _log_session("ml", "ML_BENCH-01", "en", True,
                         "test description", "abc123")
    assert entry["domain"] == "ml"
    assert entry["claim"] == "ML_BENCH-01"
    assert entry["verification_passed"] is True

    log_path = reports_dir / "onboarding_log.json"
    assert log_path.exists()
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 1


def test_log_session_appends(tmp_path, monkeypatch):
    """Multiple calls append to the same log file."""
    monkeypatch.setattr("scripts.mg_onboard.REPO_ROOT", tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    _log_session("ml", "ML_BENCH-01", "en", True, "first", "hash1")
    _log_session("pharma", "PHARMA-01", "es", False, "second", "hash2")

    log_path = reports_dir / "onboarding_log.json"
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(data) == 2
    assert data[1]["domain"] == "pharma"


def test_log_session_handles_corrupt_log(tmp_path, monkeypatch):
    """_log_session handles corrupt existing log gracefully."""
    monkeypatch.setattr("scripts.mg_onboard.REPO_ROOT", tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    log_path = reports_dir / "onboarding_log.json"
    log_path.write_text("not valid json!", encoding="utf-8")

    entry = _log_session("ml", "ML_BENCH-01", "en", True, "test", "h1")
    assert entry["domain"] == "ml"
    # Should have overwritten with fresh list
    data = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(data) == 1


# ---- _call_claude tests -----------------------------------------------------


def test_call_claude_sends_message_and_returns():
    """_call_claude appends messages and returns assistant text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello from Claude")]
    mock_client.messages.create.return_value = mock_response

    messages = []
    result = _call_claude(mock_client, messages, "test input")

    assert result == "Hello from Claude"
    assert len(messages) == 2
    assert messages[0] == {"role": "user", "content": "test input"}
    assert messages[1] == {"role": "assistant", "content": "Hello from Claude"}
    mock_client.messages.create.assert_called_once()


# ---- run_onboarding mock_mode tests ----------------------------------------


def test_run_onboarding_mock_mode(monkeypatch, tmp_path):
    """run_onboarding with mock_mode=True completes the 3-step flow."""
    monkeypatch.setattr("scripts.mg_onboard.REPO_ROOT", tmp_path)
    (tmp_path / "reports").mkdir()

    mock_responses = [
        "Welcome! I detected your ML domain.",
        "Verification complete! Here is your $299 link.",
    ]

    # Mock the mg_client functions that run_onboarding imports
    mock_run_claim = MagicMock(return_value={
        "mtr_phase": "ML_BENCH-01",
        "result": {"pass": True, "actual_accuracy": 0.94},
        "execution_trace": [],
        "trace_root_hash": "a" * 64,
    })
    mock_create_bundle = MagicMock(return_value=str(tmp_path / "bundle"))
    mock_verify_bundle = MagicMock(return_value=(True, [
        ("Layer 1", True, "OK"),
        ("Layer 2", True, "OK"),
        ("Layer 3", True, "OK"),
        ("Layer 4", True, "OK"),
        ("Layer 5", True, "OK"),
    ]))

    with patch("scripts.mg_onboard.run_onboarding.__module__", "scripts.mg_onboard"), \
         patch.dict("sys.modules", {"scripts.mg_client": MagicMock(
             run_claim=mock_run_claim,
             create_bundle=mock_create_bundle,
             verify_bundle=mock_verify_bundle,
         )}):
        # We need to mock the import inside run_onboarding
        with patch("scripts.mg_client.run_claim", mock_run_claim), \
             patch("scripts.mg_client.create_bundle", mock_create_bundle), \
             patch("scripts.mg_client.verify_bundle", mock_verify_bundle):
            result = run_onboarding(
                api_key="fake-key",
                mock_mode=True,
                mock_input="I train neural networks for accuracy benchmarks",
                mock_responses=mock_responses,
            )

    assert result is not None
    assert result["domain"] == "ml"
    assert result["passed"] is True
    assert result["language"] == "en"


def test_run_onboarding_empty_input(monkeypatch, tmp_path):
    """run_onboarding returns None on empty input."""
    monkeypatch.setattr("scripts.mg_onboard.REPO_ROOT", tmp_path)

    # mock_input="" is falsy so run_onboarding calls real input().
    # Provide empty input via monkeypatch on builtins.input instead.
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    result = run_onboarding(
        api_key="fake-key",
        mock_mode=True,
        mock_input=None,
    )
    assert result is None


# ---- main() tests -----------------------------------------------------------


def test_main_no_api_key(monkeypatch):
    """main() returns 1 when no API key provided."""
    monkeypatch.setattr("sys.argv", ["mg_onboard.py"])
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main() == 1


def test_main_with_api_key_none_result(monkeypatch):
    """main() returns 1 when run_onboarding returns None."""
    monkeypatch.setattr("sys.argv", ["mg_onboard.py", "--api-key", "fake-key"])
    with patch("scripts.mg_onboard.run_onboarding", return_value=None):
        assert main() == 1


def test_main_with_api_key_pass(monkeypatch):
    """main() returns 0 when verification passes."""
    monkeypatch.setattr("sys.argv", ["mg_onboard.py", "--api-key", "fake-key"])
    with patch("scripts.mg_onboard.run_onboarding", return_value={
        "domain": "ml", "claim": "ML_BENCH-01", "passed": True,
        "language": "en", "session_hash": "abc",
    }):
        assert main() == 0


def test_main_with_api_key_fail(monkeypatch):
    """main() returns 1 when verification fails."""
    monkeypatch.setattr("sys.argv", ["mg_onboard.py", "--api-key", "fake-key"])
    with patch("scripts.mg_onboard.run_onboarding", return_value={
        "domain": "ml", "claim": "ML_BENCH-01", "passed": False,
        "language": "en", "session_hash": "abc",
    }):
        assert main() == 1
