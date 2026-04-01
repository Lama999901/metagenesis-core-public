#!/usr/bin/env python3
"""Coverage tests for scripts/mg_policy_gate.py — 22 tests."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.mg_policy_gate import PolicyGate


# ── helpers ───────────────────────────────────────────────────────────


def _write_policy(tmp_path, policy=None):
    """Write a valid policy file and return its path."""
    if policy is None:
        policy = {
            "version": "1.0.0",
            "locked_paths": [
                "secrets/keyfile.json",
                "demos/locked/**",
            ],
            "allow_globs": [
                "*.md",
                "*.txt",
                "scripts/**",
                "tests/**",
                "docs/**",
            ],
        }
    p = tmp_path / "policy.json"
    p.write_text(json.dumps(policy), encoding="utf-8")
    return str(p)


def _gate(tmp_path, policy=None):
    path = _write_policy(tmp_path, policy)
    return PolicyGate(path)


# ── _load_policy validation ──────────────────────────────────────────


def test_load_policy_valid(tmp_path):
    gate = _gate(tmp_path)
    assert gate.policy["version"] == "1.0.0"


def test_load_policy_file_not_found():
    with pytest.raises(SystemExit) as exc_info:
        PolicyGate("/nonexistent/path/policy.json")
    assert exc_info.value.code == 3


def test_load_policy_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{bad json!!!", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        PolicyGate(str(p))
    assert exc_info.value.code == 3


def test_load_policy_missing_version(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"locked_paths": [], "allow_globs": []}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        PolicyGate(str(p))
    assert exc_info.value.code == 3


def test_load_policy_missing_locked_paths(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"version": "1", "allow_globs": []}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        PolicyGate(str(p))
    assert exc_info.value.code == 3


def test_load_policy_missing_allow_globs(tmp_path):
    p = tmp_path / "p.json"
    p.write_text(json.dumps({"version": "1", "locked_paths": []}), encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        PolicyGate(str(p))
    assert exc_info.value.code == 3


# ── matches_pattern ──────────────────────────────────────────────────


def test_matches_pattern_exact(tmp_path):
    gate = _gate(tmp_path)
    assert gate.matches_pattern("README.md", "*.md")


def test_matches_pattern_no_match(tmp_path):
    gate = _gate(tmp_path)
    assert not gate.matches_pattern("README.md", "*.py")


def test_matches_pattern_directory_glob(tmp_path):
    gate = _gate(tmp_path)
    assert gate.matches_pattern("scripts/mg.py", "scripts/**")


def test_matches_pattern_nested_directory(tmp_path):
    gate = _gate(tmp_path)
    assert gate.matches_pattern("scripts/sub/deep.py", "scripts/**")


def test_matches_pattern_exact_file(tmp_path):
    gate = _gate(tmp_path)
    assert gate.matches_pattern("secrets/keyfile.json", "secrets/keyfile.json")


def test_matches_pattern_directory_no_match(tmp_path):
    gate = _gate(tmp_path)
    assert not gate.matches_pattern("other/file.py", "scripts/**")


# ── check_locked_paths ───────────────────────────────────────────────


def test_check_locked_no_violation(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_locked_paths(["README.md", "scripts/mg.py"])
    assert violations == []


def test_check_locked_exact_match(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_locked_paths(["secrets/keyfile.json"])
    assert len(violations) == 1
    assert violations[0][0] == "secrets/keyfile.json"


def test_check_locked_directory_match(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_locked_paths(["demos/locked/evidence.json"])
    assert len(violations) == 1


def test_check_locked_multiple_files(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_locked_paths([
        "README.md",
        "secrets/keyfile.json",
        "demos/locked/x.json",
    ])
    assert len(violations) == 2


# ── check_allowlist ──────────────────────────────────────────────────


def test_allowlist_pass(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_allowlist(["README.md", "tests/test_x.py"])
    assert violations == []


def test_allowlist_fail(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_allowlist(["binary.exe"])
    assert "binary.exe" in violations


def test_allowlist_mixed(tmp_path):
    gate = _gate(tmp_path)
    violations = gate.check_allowlist(["README.md", "binary.exe", "notes.txt"])
    assert violations == ["binary.exe"]


# ── get_changed_files_list ───────────────────────────────────────────


def test_parse_single_file(tmp_path):
    gate = _gate(tmp_path)
    assert gate.get_changed_files_list("file.py") == ["file.py"]


def test_parse_comma_separated(tmp_path):
    gate = _gate(tmp_path)
    result = gate.get_changed_files_list("a.py, b.md, c.txt")
    assert result == ["a.py", "b.md", "c.txt"]


def test_parse_empty_string(tmp_path):
    gate = _gate(tmp_path)
    assert gate.get_changed_files_list("") == []


# ── enforce ──────────────────────────────────────────────────────────


def test_enforce_no_files(tmp_path):
    gate = _gate(tmp_path)
    assert gate.enforce([]) is True


def test_enforce_all_allowed(tmp_path):
    gate = _gate(tmp_path)
    assert gate.enforce(["README.md", "scripts/mg.py"]) is True


def test_enforce_locked_fails(tmp_path):
    gate = _gate(tmp_path)
    assert gate.enforce(["secrets/keyfile.json"]) is False


def test_enforce_not_allowed_fails(tmp_path):
    gate = _gate(tmp_path)
    assert gate.enforce(["malware.exe"]) is False
