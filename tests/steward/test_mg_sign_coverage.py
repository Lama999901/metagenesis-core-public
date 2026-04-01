#!/usr/bin/env python3
"""Coverage tests for scripts/mg_sign.py — 20 tests."""

import hashlib
import hmac
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.mg_sign import (
    SIGNATURE_FILE,
    SIGNATURE_VERSION,
    _compute_signature,
    _detect_algorithm,
    generate_key,
    load_key,
    sign_bundle,
    verify_bundle_signature,
)


# ── generate_key ──────────────────────────────────────────────────────


def test_generate_key_returns_required_fields():
    key = generate_key()
    assert set(key.keys()) >= {"version", "key_hex", "fingerprint", "note"}


def test_generate_key_version_is_hmac():
    key = generate_key()
    assert key["version"] == "hmac-sha256-v1"


def test_generate_key_hex_is_64_chars():
    key = generate_key()
    assert len(key["key_hex"]) == 64
    int(key["key_hex"], 16)  # must parse as hex


def test_generate_key_fingerprint_matches_key():
    key = generate_key()
    expected = hashlib.sha256(bytes.fromhex(key["key_hex"])).hexdigest()
    assert key["fingerprint"] == expected


def test_generate_key_unique():
    k1 = generate_key()
    k2 = generate_key()
    assert k1["key_hex"] != k2["key_hex"]


# ── load_key ──────────────────────────────────────────────────────────


def test_load_key_hmac(tmp_path):
    key = generate_key()
    p = tmp_path / "key.json"
    p.write_text(json.dumps(key), encoding="utf-8")
    loaded = load_key(p)
    assert loaded["key_hex"] == key["key_hex"]


def test_load_key_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Cannot load key"):
        load_key(tmp_path / "nope.json")


def test_load_key_invalid_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json!", encoding="utf-8")
    with pytest.raises(ValueError, match="Cannot load key"):
        load_key(p)


def test_load_key_unknown_version(tmp_path):
    p = tmp_path / "k.json"
    p.write_text(json.dumps({"version": "unknown-v9", "key_hex": "aa" * 32}), encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown key version"):
        load_key(p)


def test_load_key_hmac_missing_key_hex(tmp_path):
    p = tmp_path / "k.json"
    p.write_text(json.dumps({"version": "hmac-sha256-v1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing 'key_hex'"):
        load_key(p)


# ── _detect_algorithm ─────────────────────────────────────────────────


def test_detect_algorithm_hmac():
    assert _detect_algorithm({"version": "hmac-sha256-v1"}) == "hmac"


def test_detect_algorithm_ed25519():
    assert _detect_algorithm({"version": "ed25519-v1"}) == "ed25519"


def test_detect_algorithm_unknown():
    with pytest.raises(ValueError, match="Unknown key version"):
        _detect_algorithm({"version": "rsa-v1"})


def test_detect_algorithm_no_version():
    with pytest.raises(ValueError, match="Unknown key version"):
        _detect_algorithm({})


# ── _compute_signature ────────────────────────────────────────────────


def test_compute_signature_deterministic():
    root = "a" * 64
    key_hex = "bb" * 32
    s1 = _compute_signature(root, key_hex)
    s2 = _compute_signature(root, key_hex)
    assert s1 == s2


def test_compute_signature_matches_stdlib():
    root = "cc" * 32
    key_hex = "dd" * 32
    expected = hmac.new(bytes.fromhex(key_hex), root.encode("utf-8"), hashlib.sha256).hexdigest()
    assert _compute_signature(root, key_hex) == expected


# ── sign_bundle / verify_bundle_signature ─────────────────────────────


def _make_bundle(tmp_path, root_hash=None):
    """Create a minimal valid bundle directory."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    data_file = bundle / "data.txt"
    data_file.write_text("hello", encoding="utf-8")
    sha = hashlib.sha256(data_file.read_bytes()).hexdigest()
    if root_hash is None:
        lines = f"data.txt:{sha}"
        root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    manifest = {
        "version": "v1",
        "protocol_version": 1,
        "root_hash": root_hash,
        "files": [{"relpath": "data.txt", "sha256": sha}],
    }
    (bundle / "pack_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return bundle, root_hash


def _make_key_file(tmp_path):
    key = generate_key()
    p = tmp_path / "key.json"
    p.write_text(json.dumps(key), encoding="utf-8")
    return p, key


def test_sign_bundle_creates_signature_file(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    kp, _ = _make_key_file(tmp_path)
    sig = sign_bundle(bundle, kp)
    assert (bundle / SIGNATURE_FILE).exists()
    assert sig["version"] == SIGNATURE_VERSION


def test_sign_bundle_no_manifest(tmp_path):
    bundle = tmp_path / "empty"
    bundle.mkdir()
    kp, _ = _make_key_file(tmp_path)
    with pytest.raises(FileNotFoundError):
        sign_bundle(bundle, kp)


def test_verify_valid_signature(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    kp, _ = _make_key_file(tmp_path)
    sign_bundle(bundle, kp)
    ok, msg = verify_bundle_signature(bundle, key_path=kp)
    assert ok
    assert "VALID" in msg


def test_verify_tampered_bundle(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    kp, _ = _make_key_file(tmp_path)
    sign_bundle(bundle, kp)
    # tamper: change root_hash in manifest
    mp = bundle / "pack_manifest.json"
    m = json.loads(mp.read_text(encoding="utf-8"))
    m["root_hash"] = "00" * 32
    mp.write_text(json.dumps(m), encoding="utf-8")
    ok, msg = verify_bundle_signature(bundle, key_path=kp)
    assert not ok
    assert "modified after signing" in msg


def test_verify_no_signature_file(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    ok, msg = verify_bundle_signature(bundle)
    assert not ok
    assert "missing" in msg


def test_verify_fingerprint_only(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    kp, key = _make_key_file(tmp_path)
    sign_bundle(bundle, kp)
    ok, msg = verify_bundle_signature(bundle, expected_fingerprint=key["fingerprint"])
    assert ok
    assert "FINGERPRINT MATCH" in msg


def test_verify_wrong_fingerprint(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    kp, _ = _make_key_file(tmp_path)
    sign_bundle(bundle, kp)
    ok, msg = verify_bundle_signature(bundle, expected_fingerprint="00" * 32)
    assert not ok
    assert "MISMATCH" in msg


def test_verify_presence_only(tmp_path):
    bundle, _ = _make_bundle(tmp_path)
    kp, _ = _make_key_file(tmp_path)
    sign_bundle(bundle, kp)
    ok, msg = verify_bundle_signature(bundle)
    assert ok
    assert "PRESENT" in msg
