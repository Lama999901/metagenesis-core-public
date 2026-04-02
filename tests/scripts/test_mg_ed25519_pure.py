#!/usr/bin/env python3
"""Coverage tests for scripts/mg_ed25519.py -- 30 tests."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from mg_ed25519 import (
    inv, recover_x, point_add, scalar_mult,
    point_encode, point_decode, generate_keypair,
    sign, verify, run_self_test, generate_key_files, P, B, IDENT, L, BY
)

FIXED_SEED = bytes.fromhex(
    "9d61b19deffd5a60ba844af492ec2cc4"
    "4449c5697b326919703bac031cae7f60"
)
FIXED_PUB = bytes.fromhex(
    "d75a980182b10ab7d54bfed3c964073a"
    "0ee172f3daa62325af021a68f707511a"
)


# -- inv ------------------------------------------------------------------

def test_inv_identity():
    assert inv(1) == 1


def test_inv_inverse_property():
    x = 12345
    assert (x * inv(x)) % P == 1


def test_inv_double_inverse():
    x = 99999
    assert inv(inv(x)) % P == x % P


# -- recover_x ------------------------------------------------------------

def test_recover_x_returns_int():
    assert isinstance(recover_x(BY, 0), int)


def test_recover_x_invalid_raises():
    with pytest.raises(ValueError):
        recover_x(2, 0)


# -- point_add -------------------------------------------------------------

def test_point_add_returns_tuple():
    result = point_add(B, B)
    assert isinstance(result, tuple) and len(result) == 4


def test_point_add_identity_left():
    result = point_add(IDENT, B)
    assert isinstance(result, tuple) and len(result) == 4


# -- scalar_mult -----------------------------------------------------------

def test_scalar_mult_zero_gives_identity():
    assert scalar_mult(0, B) == IDENT


def test_scalar_mult_one_gives_point():
    result = scalar_mult(1, B)
    assert isinstance(result, tuple) and len(result) == 4


def test_scalar_mult_deterministic():
    assert scalar_mult(42, B) == scalar_mult(42, B)


# -- point_encode ----------------------------------------------------------

def test_point_encode_32_bytes():
    assert len(point_encode(B)) == 32


# -- point_decode ----------------------------------------------------------

def test_point_decode_wrong_length_none():
    assert point_decode(b"\x00" * 31) is None
    assert point_decode(b"\x00" * 33) is None


def test_point_decode_roundtrip():
    encoded = point_encode(B)
    decoded = point_decode(encoded)
    assert decoded is not None
    assert point_encode(decoded) == encoded


def test_point_decode_fixed_pub():
    decoded = point_decode(FIXED_PUB)
    assert decoded is not None


# -- generate_keypair ------------------------------------------------------

def test_generate_keypair_deterministic():
    seed, pub = generate_keypair(FIXED_SEED)
    assert seed == FIXED_SEED
    assert pub == FIXED_PUB


def test_generate_keypair_random_lengths():
    seed, pub = generate_keypair()
    assert len(seed) == 32
    assert len(pub) == 32


def test_generate_keypair_two_random_differ():
    s1, _ = generate_keypair()
    s2, _ = generate_keypair()
    assert s1 != s2


def test_generate_keypair_different_seeds_different_keys():
    _, pub1 = generate_keypair(FIXED_SEED)
    _, pub2 = generate_keypair(b"\x01" * 32)
    assert pub1 != pub2


# -- sign ------------------------------------------------------------------

def test_sign_returns_64_bytes():
    assert len(sign(FIXED_SEED, b"hello")) == 64


def test_sign_deterministic():
    assert sign(FIXED_SEED, b"test") == sign(FIXED_SEED, b"test")


# -- verify ----------------------------------------------------------------

def test_verify_valid():
    _, pub = generate_keypair(FIXED_SEED)
    sig = sign(FIXED_SEED, b"test message")
    assert verify(pub, b"test message", sig) is True


def test_verify_wrong_message():
    _, pub = generate_keypair(FIXED_SEED)
    sig = sign(FIXED_SEED, b"correct")
    assert verify(pub, b"wrong", sig) is False


def test_verify_tampered_sig():
    _, pub = generate_keypair(FIXED_SEED)
    sig = sign(FIXED_SEED, b"msg")
    assert verify(pub, b"msg", b"\x00" * 64) is False


def test_verify_wrong_sig_length():
    _, pub = generate_keypair(FIXED_SEED)
    assert verify(pub, b"msg", b"\x00" * 32) is False


def test_verify_wrong_pub_length():
    sig = sign(FIXED_SEED, b"msg")
    assert verify(b"\x00" * 16, b"msg", sig) is False


def test_verify_empty_message():
    _, pub = generate_keypair(FIXED_SEED)
    sig = sign(FIXED_SEED, b"")
    assert verify(pub, b"", sig) is True


# -- run_self_test ---------------------------------------------------------

def test_run_self_test_returns_true():
    assert run_self_test() is True


# -- generate_key_files ----------------------------------------------------

def test_generate_key_files_creates_two_files(tmp_path):
    key_path = tmp_path / "mykey.json"
    generate_key_files(key_path)
    assert key_path.exists()
    assert (tmp_path / "mykey.pub.json").exists()


def test_generate_key_files_returns_dict(tmp_path):
    key_path = tmp_path / "mykey.json"
    result = generate_key_files(key_path)
    assert all(k in result for k in ("private_key_hex", "public_key_hex", "fingerprint"))


def test_generate_key_files_pub_has_no_private(tmp_path):
    key_path = tmp_path / "mykey.json"
    generate_key_files(key_path)
    pub = json.loads((tmp_path / "mykey.pub.json").read_text())
    assert "private_key_hex" not in pub
    assert "public_key_hex" in pub
