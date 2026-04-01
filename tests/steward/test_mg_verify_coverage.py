#!/usr/bin/env python3
"""Coverage tests for scripts/mg.py _verify_pack and _verify_semantic — 15 tests."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.mg import _verify_pack, _verify_semantic


# ── helpers ───────────────────────────────────────────────────────────


def _file_sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_bundle(tmp_path, files_dict=None, protocol_version=1, extra_manifest=None):
    """
    Build a valid bundle.

    files_dict: {relpath: content_str}
    Returns (pack_dir, manifest_dict).
    """
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir(parents=True, exist_ok=True)

    if files_dict is None:
        files_dict = {"data.txt": "hello world"}

    file_entries = []
    for relpath, content in files_dict.items():
        fp = pack_dir / relpath
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        sha = _file_sha(fp)
        file_entries.append({"relpath": relpath, "sha256": sha})

    # Compute root_hash same way mg.py does
    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(file_entries, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "version": "v1",
        "protocol_version": protocol_version,
        "root_hash": root_hash,
        "files": file_entries,
    }
    if extra_manifest:
        manifest.update(extra_manifest)

    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return pack_dir, manifest


# ── _verify_pack tests ───────────────────────────────────────────────


def test_verify_pack_valid(tmp_path):
    pack_dir, _ = _build_bundle(tmp_path)
    ok, msg, report = _verify_pack(pack_dir)
    assert ok
    assert report["manifest_ok"] is True


def test_verify_pack_no_manifest(tmp_path):
    pack_dir = tmp_path / "empty"
    pack_dir.mkdir()
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "pack_manifest.json not found" in msg


def test_verify_pack_invalid_json(tmp_path):
    pack_dir = tmp_path / "bad"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text("{bad!", encoding="utf-8")
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "Failed to load manifest" in msg


def test_verify_pack_missing_files_key(tmp_path):
    pack_dir = tmp_path / "nof"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps({"version": "v1", "protocol_version": 1, "root_hash": "a" * 64}),
        encoding="utf-8",
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "files" in msg


def test_verify_pack_missing_root_hash(tmp_path):
    pack_dir = tmp_path / "norh"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps({"version": "v1", "protocol_version": 1, "files": []}),
        encoding="utf-8",
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "root_hash" in msg


def test_verify_pack_missing_protocol_version(tmp_path):
    pack_dir = tmp_path / "nopv"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps({"version": "v1", "files": [], "root_hash": "a" * 64}),
        encoding="utf-8",
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "protocol_version" in msg


def test_verify_pack_protocol_version_string(tmp_path):
    pack_dir = tmp_path / "pvstr"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps({"version": "v1", "protocol_version": "1", "files": [], "root_hash": "a" * 64}),
        encoding="utf-8",
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "integer" in msg


def test_verify_pack_protocol_version_zero(tmp_path):
    pack_dir = tmp_path / "pvz"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps({"version": "v1", "protocol_version": 0, "files": [], "root_hash": "a" * 64}),
        encoding="utf-8",
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "minimum" in msg


def test_verify_pack_sha_mismatch(tmp_path):
    pack_dir, _ = _build_bundle(tmp_path)
    # tamper with file content
    (pack_dir / "data.txt").write_text("tampered!", encoding="utf-8")
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "SHA256 mismatch" in msg


def test_verify_pack_missing_file(tmp_path):
    pack_dir, _ = _build_bundle(tmp_path)
    (pack_dir / "data.txt").unlink()
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "File missing" in msg


def test_verify_pack_root_hash_mismatch(tmp_path):
    pack_dir, manifest = _build_bundle(tmp_path)
    manifest["root_hash"] = "bb" * 32
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "root_hash mismatch" in msg


def test_verify_pack_path_traversal(tmp_path):
    pack_dir = tmp_path / "trav"
    pack_dir.mkdir()
    (pack_dir / "pack_manifest.json").write_text(
        json.dumps({
            "version": "v1",
            "protocol_version": 1,
            "root_hash": "a" * 64,
            "files": [{"relpath": "../escape.txt", "sha256": "a" * 64}],
        }),
        encoding="utf-8",
    )
    ok, msg, report = _verify_pack(pack_dir)
    assert not ok
    assert "Invalid relpath" in msg


# ── _verify_semantic tests ───────────────────────────────────────────


def _build_evidence_bundle(tmp_path, claim_id="MTR-1", job_kind="mtr1_calibration"):
    """Build a bundle with evidence_index.json and matching artifacts."""
    pack_dir = tmp_path / "epack"
    pack_dir.mkdir(parents=True, exist_ok=True)

    # Create run artifact
    final_hash = hashlib.sha256(b"step4").hexdigest()
    run_artifact = {
        "trace_id": "test-trace-001",
        "canary_mode": False,
        "job_snapshot": {
            "payload": {"kind": job_kind},
            "result": {
                "mtr_phase": claim_id,
                "inputs": {"E_ref": 70e9},
                "result": {"relative_error": 0.005},
                "execution_trace": [
                    {"step": 1, "name": "init", "hash": hashlib.sha256(b"step1").hexdigest()},
                    {"step": 2, "name": "compute", "hash": hashlib.sha256(b"step2").hexdigest()},
                    {"step": 3, "name": "metrics", "hash": hashlib.sha256(b"step3").hexdigest()},
                    {"step": 4, "name": "threshold", "hash": final_hash},
                ],
                "trace_root_hash": final_hash,
            },
        },
    }
    run_path = pack_dir / "runs" / "run_normal.json"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_path.write_text(json.dumps(run_artifact), encoding="utf-8")

    # Create ledger
    ledger_path = pack_dir / "ledger" / "ledger.jsonl"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text('{"entry": 1}\n', encoding="utf-8")

    # Create evidence index
    evidence = {
        claim_id: {
            "job_kind": job_kind,
            "normal": {
                "run_relpath": "runs/run_normal.json",
                "ledger_relpath": "ledger/ledger.jsonl",
            },
        },
    }
    ei_path = pack_dir / "evidence_index.json"
    ei_path.write_text(json.dumps(evidence), encoding="utf-8")

    return pack_dir, ei_path


def test_verify_semantic_valid(tmp_path):
    pack_dir, ei_path = _build_evidence_bundle(tmp_path)
    ok, msg, warnings = _verify_semantic(pack_dir, ei_path)
    assert ok
    assert msg == "PASS"


def test_verify_semantic_missing_run_file(tmp_path):
    pack_dir, ei_path = _build_evidence_bundle(tmp_path)
    (pack_dir / "runs" / "run_normal.json").unlink()
    ok, msg, errors = _verify_semantic(pack_dir, ei_path)
    assert not ok
    assert "missing" in msg.lower()


def test_verify_semantic_broken_step_chain(tmp_path):
    pack_dir, ei_path = _build_evidence_bundle(tmp_path)
    # Tamper: set trace_root_hash to something else
    run_path = pack_dir / "runs" / "run_normal.json"
    art = json.loads(run_path.read_text(encoding="utf-8"))
    art["job_snapshot"]["result"]["trace_root_hash"] = "00" * 32
    run_path.write_text(json.dumps(art), encoding="utf-8")
    ok, msg, errors = _verify_semantic(pack_dir, ei_path)
    assert not ok
    assert "Step Chain broken" in msg
