"""Coverage boost tests for mg_sign.py and mg_ed25519.py."""
import argparse
import json
import pytest
from pathlib import Path

from scripts.mg_sign import generate_key, sign_bundle, load_key, _compute_signature, cmd_keygen
from scripts.mg_ed25519 import run_self_test, generate_keypair, sign, verify, generate_key_files


# ── GROUP 1: mg_sign.py lower-level functions ──

def test_generate_key():
    key = generate_key()
    assert "version" in key
    assert "key_hex" in key
    assert "fingerprint" in key
    assert len(key["key_hex"]) == 64


def test_sign_bundle_creates_signature(tmp_path):
    pack_dir = tmp_path / "bundle"
    pack_dir.mkdir()
    root_hash = "a" * 64
    manifest = {"root_hash": root_hash}
    (pack_dir / "pack_manifest.json").write_text(json.dumps(manifest))
    key = generate_key()
    key_path = tmp_path / "key.json"
    key_path.write_text(json.dumps(key))
    sig = sign_bundle(pack_dir, key_path)
    assert (pack_dir / "bundle_signature.json").exists()
    assert sig["signed_root_hash"] == root_hash


def test_sign_bundle_missing_manifest_raises(tmp_path):
    pack_dir = tmp_path / "empty_bundle"
    pack_dir.mkdir()
    key = generate_key()
    key_path = tmp_path / "key.json"
    key_path.write_text(json.dumps(key))
    with pytest.raises(FileNotFoundError):
        sign_bundle(pack_dir, key_path)


def test_load_key(tmp_path):
    key = generate_key()
    key_path = tmp_path / "key.json"
    key_path.write_text(json.dumps(key))
    loaded = load_key(key_path)
    assert loaded["key_hex"] == key["key_hex"]


def test_compute_signature():
    key = generate_key()
    root_hash = "b" * 64
    sig = _compute_signature(root_hash, key["key_hex"])
    assert isinstance(sig, str)
    assert len(sig) > 0


# ── GROUP 2: mg_ed25519.py (pure crypto) ──

def test_run_self_test():
    assert run_self_test() is True


def test_generate_keypair():
    result = generate_keypair()
    assert len(result) == 2
    private_seed, public_key = result
    assert len(private_seed) == 32
    assert len(public_key) == 32


def test_sign_verify_roundtrip():
    private_seed, public_key = generate_keypair()
    message = b"test"
    signature = sign(private_seed, message)
    assert verify(public_key, message, signature) is True


def test_verify_wrong_message_fails():
    private_seed, public_key = generate_keypair()
    signature = sign(private_seed, b"correct")
    assert verify(public_key, b"wrong", signature) is False


def test_generate_key_files(tmp_path):
    key_path = tmp_path / "key.json"
    key_data = generate_key_files(key_path)
    assert key_path.exists()
    pub_path = tmp_path / "key.pub.json"
    assert pub_path.exists()
    assert "private_key_hex" in key_data
    assert "public_key_hex" in key_data


# ── GROUP 3: mg_sign.py cmd_ functions ──

def test_cmd_keygen_hmac(tmp_path):
    args = argparse.Namespace(out=str(tmp_path / "key.json"), type="hmac")
    result = cmd_keygen(args)
    assert result == 0
    assert (tmp_path / "key.json").exists()


def test_cmd_keygen_ed25519(tmp_path):
    args = argparse.Namespace(out=str(tmp_path / "key.json"), type="ed25519")
    result = cmd_keygen(args)
    assert result == 0
    assert (tmp_path / "key.json").exists()
