#!/usr/bin/env python3
"""Extended coverage tests for scripts/mg_sign.py -- 20 tests."""

import hashlib
import hmac as _hmac
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mg_sign import (
    _detect_algorithm, generate_key, load_key,
    _compute_signature, _compute_ed25519_signature
)
from mg_ed25519 import generate_key_files


# -- _detect_algorithm edge cases ------------------------------------------

def test_detect_algorithm_hmac():
    assert _detect_algorithm({"version": "hmac-sha256-v1"}) == "hmac"


def test_detect_algorithm_ed25519():
    assert _detect_algorithm({"version": "ed25519-v1"}) == "ed25519"


def test_detect_algorithm_unknown_raises():
    with pytest.raises(ValueError):
        _detect_algorithm({"version": "unknown"})


def test_detect_algorithm_empty_version_raises():
    with pytest.raises(ValueError):
        _detect_algorithm({"version": ""})


def test_detect_algorithm_missing_key_raises():
    with pytest.raises(ValueError):
        _detect_algorithm({})


# -- generate_key ----------------------------------------------------------

def test_generate_key_returns_dict():
    assert isinstance(generate_key(), dict)


def test_generate_key_required_fields():
    result = generate_key()
    assert all(k in result for k in ("version", "key_hex", "fingerprint"))


def test_generate_key_hex_length():
    assert len(generate_key()["key_hex"]) == 64


def test_generate_key_fingerprint_length():
    assert len(generate_key()["fingerprint"]) == 64


def test_generate_key_two_calls_differ():
    assert generate_key()["key_hex"] != generate_key()["key_hex"]


# -- _compute_signature ----------------------------------------------------

def test_compute_signature_hex_string():
    result = _compute_signature("abc123", "a" * 64)
    assert isinstance(result, str) and len(result) == 64


def test_compute_signature_deterministic():
    assert _compute_signature("hash_x", "b" * 64) == _compute_signature("hash_x", "b" * 64)


def test_compute_signature_different_input():
    assert _compute_signature("hash_A", "c" * 64) != _compute_signature("hash_B", "c" * 64)


def test_compute_signature_matches_hmac():
    root = "test_hash"
    key_hex = "dd" * 32
    manual = _hmac.new(
        bytes.fromhex(key_hex), root.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    assert _compute_signature(root, key_hex) == manual


# -- load_key edge cases ---------------------------------------------------

def test_load_key_valid_hmac(tmp_path):
    key = generate_key()
    p = tmp_path / "k.json"
    p.write_text(json.dumps(key), encoding="utf-8")
    loaded = load_key(p)
    assert loaded["version"] == "hmac-sha256-v1"


def test_load_key_invalid_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        load_key(p)


def test_load_key_missing_file_raises(tmp_path):
    with pytest.raises(ValueError):
        load_key(tmp_path / "missing.json")


def test_load_key_unknown_version_raises(tmp_path):
    p = tmp_path / "k.json"
    p.write_text(json.dumps({"version": "rsa-v99", "key_hex": "aa" * 32}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_key(p)


# -- _compute_ed25519_signature -------------------------------------------

def test_compute_ed25519_signature_hex_128(tmp_path):
    key_path = tmp_path / "ed.json"
    generate_key_files(key_path)
    key_data = json.loads(key_path.read_text(encoding="utf-8"))
    result = _compute_ed25519_signature("abc123", key_data)
    assert isinstance(result, str) and len(result) == 128


def test_compute_ed25519_signature_deterministic(tmp_path):
    key_path = tmp_path / "ed.json"
    generate_key_files(key_path)
    key_data = json.loads(key_path.read_text(encoding="utf-8"))
    s1 = _compute_ed25519_signature("test_hash", key_data)
    s2 = _compute_ed25519_signature("test_hash", key_data)
    assert s1 == s2
