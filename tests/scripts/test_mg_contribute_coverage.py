"""Tests for scripts/mg_contribute.py -- coverage boost."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import scripts.mg_contribute as mod


@pytest.fixture
def contrib_env(tmp_path, monkeypatch):
    """Redirect CONTRIB_DIR to tmp_path."""
    contrib_dir = tmp_path / "contributions"
    contrib_dir.mkdir()
    monkeypatch.setattr(mod, "CONTRIB_DIR", contrib_dir)
    monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
    return contrib_dir


# ---- sanitize_content tests --------------------------------------------------


def test_sanitize_empty():
    assert mod.sanitize_content("") == ""


def test_sanitize_strips_code():
    text = "I found import os in the code and eval(x) is bad"
    result = mod.sanitize_content(text)
    assert "import os" not in result
    assert "[REMOVED]" in result


def test_sanitize_truncates():
    long_text = "a" * 3000
    result = mod.sanitize_content(long_text)
    assert len(result) <= mod.MAX_CONTENT_LENGTH


def test_sanitize_normal_text():
    text = "The verification worked great for our ML pipeline"
    result = mod.sanitize_content(text)
    assert "verification" in result


# ---- _detect_language tests --------------------------------------------------


def test_detect_japanese():
    assert mod._detect_language("This has hiragana: \u3042\u3044\u3046") == "ja"


def test_detect_katakana():
    assert mod._detect_language("Katakana: \u30a2\u30a4\u30a6") == "ja"


def test_detect_korean():
    assert mod._detect_language("Korean: \uac00\ub098\ub2e4") == "ko"


def test_detect_chinese():
    assert mod._detect_language("\u4e2d\u6587\u6d4b\u8bd5") == "zh"


def test_detect_russian():
    assert mod._detect_language("\u041f\u0440\u0438\u0432\u0435\u0442") == "ru"


def test_detect_spanish():
    assert mod._detect_language("estoy trabajando en esto") == "es"


def test_detect_french():
    assert mod._detect_language("je travaille sur ce projet") == "fr"


def test_detect_german():
    assert mod._detect_language("ich arbeite an diesem Projekt") == "de"


def test_detect_english():
    assert mod._detect_language("This is a normal English sentence") == "en"


# ---- create_contribution tests -----------------------------------------------


def test_create_contribution_valid(contrib_env):
    result = mod.create_contribution(
        "Great verification tool", "improvement", "ml"
    )
    assert result["type"] == "improvement"
    assert result["domain"] == "ml"
    assert "sha256" in result
    assert result["id"].startswith("contrib_")
    # Verify file written
    files = list(contrib_env.glob("contrib_*.json"))
    assert len(files) == 1


def test_create_contribution_sequential_id(contrib_env):
    mod.create_contribution("First", "bug_report", "other")
    mod.create_contribution("Second", "bug_report", "other")
    files = sorted(contrib_env.glob("contrib_*.json"))
    assert len(files) == 2
    d1 = json.loads(files[0].read_text(encoding="utf-8"))
    d2 = json.loads(files[1].read_text(encoding="utf-8"))
    assert d1["id"] != d2["id"]


def test_create_contribution_invalid_type(contrib_env):
    with pytest.raises(ValueError, match="Invalid type"):
        mod.create_contribution("some text", "not_a_type", "other")


def test_create_contribution_code_only(contrib_env):
    with pytest.raises(ValueError, match="empty or contained only code"):
        mod.create_contribution("import os", "bug_report", "other")


def test_create_contribution_invalid_domain_defaults(contrib_env):
    result = mod.create_contribution("Good text here", "improvement", "nonexistent")
    assert result["domain"] == "other"


# ---- show_stats tests --------------------------------------------------------


def test_show_stats_no_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "CONTRIB_DIR", tmp_path / "nonexistent")
    mod.show_stats()
    out = capsys.readouterr().out
    assert "No contributions yet" in out


def test_show_stats_empty_dir(contrib_env, capsys):
    mod.show_stats()
    out = capsys.readouterr().out
    assert "No contributions yet" in out


def test_show_stats_with_data(contrib_env, capsys):
    mod.create_contribution("Test feedback", "bug_report", "ml")
    mod.show_stats()
    out = capsys.readouterr().out
    assert "Total: 1" in out
    assert "bug_report" in out


# ---- review_contributions tests ----------------------------------------------


def test_review_no_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(mod, "CONTRIB_DIR", tmp_path / "nonexistent")
    mod.review_contributions()
    out = capsys.readouterr().out
    assert "No contributions to review" in out


def test_review_all_reviewed(contrib_env, capsys):
    # Create and then mark as reviewed
    c = mod.create_contribution("Feedback", "improvement", "other")
    f = contrib_env / f"{c['id']}.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    data["value_score"] = 5
    f.write_text(json.dumps(data), encoding="utf-8")
    mod.review_contributions()
    out = capsys.readouterr().out
    assert "All contributions reviewed" in out


def test_review_with_pending(contrib_env, capsys):
    mod.create_contribution("Pending feedback", "bug_report", "ml")
    mod.review_contributions()
    out = capsys.readouterr().out
    assert "1 contributions pending review" in out


# ---- interactive_contribute tests --------------------------------------------


def test_interactive_eof(contrib_env, monkeypatch):
    monkeypatch.setattr("builtins.input", mock.Mock(side_effect=EOFError))
    result = mod.interactive_contribute()
    assert result is None


def test_interactive_keyboard_interrupt(contrib_env, monkeypatch):
    monkeypatch.setattr("builtins.input", mock.Mock(side_effect=KeyboardInterrupt))
    result = mod.interactive_contribute()
    assert result is None


def test_interactive_invalid_choice(contrib_env, monkeypatch):
    monkeypatch.setattr("builtins.input", mock.Mock(return_value="99"))
    result = mod.interactive_contribute()
    assert result is None


def test_interactive_success(contrib_env, monkeypatch):
    inputs = iter(["1", "1", "This is great feedback for ML"])
    monkeypatch.setattr("builtins.input", mock.Mock(side_effect=inputs))
    result = mod.interactive_contribute()
    assert result is not None
    assert result["type"] == "bug_report"
    assert result["domain"] == "ml"


def test_interactive_empty_content(contrib_env, monkeypatch):
    inputs = iter(["1", "1", ""])
    monkeypatch.setattr("builtins.input", mock.Mock(side_effect=inputs))
    result = mod.interactive_contribute()
    assert result is None


def test_interactive_eof_on_domain(contrib_env, monkeypatch):
    call_count = 0

    def side_effect(prompt=""):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "1"  # type choice
        raise EOFError

    monkeypatch.setattr("builtins.input", side_effect)
    result = mod.interactive_contribute()
    assert result is None


# ---- main tests --------------------------------------------------------------


def test_main_stats(contrib_env, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["mg_contribute.py", "--stats"])
    ret = mod.main()
    assert ret == 0


def test_main_review(contrib_env, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["mg_contribute.py", "--review"])
    ret = mod.main()
    assert ret == 0


def test_main_noninteractive(contrib_env, monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["mg_contribute.py", "--type", "bug_report", "--content", "Great tool"],
    )
    ret = mod.main()
    assert ret == 0
    files = list(contrib_env.glob("contrib_*.json"))
    assert len(files) == 1


def test_main_noninteractive_code_content(contrib_env, monkeypatch):
    monkeypatch.setattr(
        sys, "argv",
        ["mg_contribute.py", "--type", "bug_report", "--content", "import os"],
    )
    ret = mod.main()
    assert ret == 1


def test_main_interactive_fallback(contrib_env, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["mg_contribute.py"])
    monkeypatch.setattr("builtins.input", mock.Mock(side_effect=EOFError))
    ret = mod.main()
    assert ret == 1
