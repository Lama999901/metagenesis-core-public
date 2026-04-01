#!/usr/bin/env python3
"""Coverage tests for scripts/mg_temporal.py — 18 tests."""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.mg_temporal import (
    TEMPORAL_FILE,
    TEMPORAL_VERSION,
    create_temporal_commitment,
    verify_temporal_commitment,
    write_temporal_commitment,
)


# ── helpers ───────────────────────────────────────────────────────────

FAKE_BEACON = {
    "outputValue": "ABCD1234" * 8,
    "timeStamp": "2026-03-31T12:00:00Z",
    "uri": "https://beacon.nist.gov/beacon/2.0/chain/last/pulse/12345",
}

ROOT_HASH = hashlib.sha256(b"test-root").hexdigest()


def _make_manifest(pack_dir, root_hash=ROOT_HASH):
    manifest = {
        "version": "v1",
        "protocol_version": 1,
        "root_hash": root_hash,
        "files": [],
    }
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )


# ── create_temporal_commitment with beacon ────────────────────────────


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_create_commitment_with_beacon(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    assert tc["version"] == TEMPORAL_VERSION
    assert tc["beacon_status"] == "available"
    assert tc["root_hash"] == ROOT_HASH


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_create_commitment_pre_hash(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    expected_pre = hashlib.sha256(ROOT_HASH.encode("utf-8")).hexdigest()
    assert tc["pre_commitment_hash"] == expected_pre


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_create_commitment_temporal_binding(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    pre = tc["pre_commitment_hash"]
    concat = pre + FAKE_BEACON["outputValue"] + FAKE_BEACON["timeStamp"]
    expected = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    assert tc["temporal_binding"] == expected


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_create_commitment_stores_beacon_fields(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    assert tc["beacon_output_value"] == FAKE_BEACON["outputValue"]
    assert tc["beacon_timestamp"] == FAKE_BEACON["timeStamp"]
    assert tc["beacon_pulse_uri"] == FAKE_BEACON["uri"]


# ── create_temporal_commitment without beacon ─────────────────────────


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=None)
def test_create_commitment_no_beacon(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    assert tc["beacon_status"] == "unavailable"
    assert tc["temporal_binding"] is None
    assert tc["beacon_output_value"] is None


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=None)
def test_create_commitment_no_beacon_has_local_ts(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    assert "local_timestamp" in tc
    assert tc["local_timestamp"] is not None


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=None)
def test_create_commitment_no_beacon_pre_hash_still_correct(mock_fetch):
    tc = create_temporal_commitment(ROOT_HASH)
    expected_pre = hashlib.sha256(ROOT_HASH.encode("utf-8")).hexdigest()
    assert tc["pre_commitment_hash"] == expected_pre


# ── write_temporal_commitment ─────────────────────────────────────────


def test_write_temporal_commitment_creates_file(tmp_path):
    tc_data = {"version": TEMPORAL_VERSION, "test": True}
    path = write_temporal_commitment(tmp_path, tc_data)
    assert path.exists()
    assert path.name == TEMPORAL_FILE


def test_write_temporal_commitment_content(tmp_path):
    tc_data = {"version": TEMPORAL_VERSION, "root_hash": ROOT_HASH}
    write_temporal_commitment(tmp_path, tc_data)
    loaded = json.loads((tmp_path / TEMPORAL_FILE).read_text(encoding="utf-8"))
    assert loaded["root_hash"] == ROOT_HASH


def test_write_temporal_commitment_overwrites(tmp_path):
    write_temporal_commitment(tmp_path, {"a": 1})
    write_temporal_commitment(tmp_path, {"b": 2})
    loaded = json.loads((tmp_path / TEMPORAL_FILE).read_text(encoding="utf-8"))
    assert "b" in loaded
    assert "a" not in loaded


# ── verify_temporal_commitment ────────────────────────────────────────


def test_verify_no_temporal_file(tmp_path):
    _make_manifest(tmp_path)
    ok, msg = verify_temporal_commitment(tmp_path)
    assert ok
    assert "skipped" in msg.lower() or "no temporal" in msg.lower()


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_verify_valid_beacon_commitment(mock_fetch, tmp_path):
    _make_manifest(tmp_path)
    tc = create_temporal_commitment(ROOT_HASH)
    write_temporal_commitment(tmp_path, tc)
    ok, msg = verify_temporal_commitment(tmp_path)
    assert ok
    assert "VALID" in msg


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=None)
def test_verify_unavailable_beacon(mock_fetch, tmp_path):
    _make_manifest(tmp_path)
    tc = create_temporal_commitment(ROOT_HASH)
    write_temporal_commitment(tmp_path, tc)
    ok, msg = verify_temporal_commitment(tmp_path)
    assert ok
    assert "local timestamp" in msg.lower()


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_verify_tampered_pre_commitment(mock_fetch, tmp_path):
    _make_manifest(tmp_path)
    tc = create_temporal_commitment(ROOT_HASH)
    tc["pre_commitment_hash"] = "00" * 32  # tamper
    write_temporal_commitment(tmp_path, tc)
    ok, msg = verify_temporal_commitment(tmp_path)
    assert not ok
    assert "pre_commitment_hash" in msg


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_verify_tampered_temporal_binding(mock_fetch, tmp_path):
    _make_manifest(tmp_path)
    tc = create_temporal_commitment(ROOT_HASH)
    tc["temporal_binding"] = "ff" * 32  # tamper
    write_temporal_commitment(tmp_path, tc)
    ok, msg = verify_temporal_commitment(tmp_path)
    assert not ok
    assert "mismatch" in msg.lower()


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_verify_different_root_hash_fails(mock_fetch, tmp_path):
    """Commitment made with one root_hash, manifest has another."""
    other_root = hashlib.sha256(b"other-root").hexdigest()
    _make_manifest(tmp_path, root_hash=other_root)
    tc = create_temporal_commitment(ROOT_HASH)
    write_temporal_commitment(tmp_path, tc)
    ok, msg = verify_temporal_commitment(tmp_path)
    assert not ok


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_create_commitment_deterministic_with_same_beacon(mock_fetch):
    tc1 = create_temporal_commitment(ROOT_HASH)
    tc2 = create_temporal_commitment(ROOT_HASH)
    assert tc1["temporal_binding"] == tc2["temporal_binding"]


@patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=FAKE_BEACON)
def test_create_commitment_different_roots_differ(mock_fetch):
    tc1 = create_temporal_commitment(ROOT_HASH)
    other = hashlib.sha256(b"different").hexdigest()
    tc2 = create_temporal_commitment(other)
    assert tc1["temporal_binding"] != tc2["temporal_binding"]
