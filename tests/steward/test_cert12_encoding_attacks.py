#!/usr/bin/env python3
"""
CERT-12: Encoding and Partial Corruption Attack Proofs.

Proves BOM injection, null bytes, truncated JSON, and Unicode homoglyphs
are detected by the verification pipeline. All byte-level attacks use
write_bytes() to control exact byte content.

ADV-05: BOM-prefixed files are detected (3 tests)
ADV-06: Null bytes, truncated JSON, and Unicode homoglyphs are caught (6 tests)

PPA: USPTO #63/996,819
"""

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg import _verify_pack, _verify_semantic  # noqa: E402
from scripts.mg_sign import (  # noqa: E402
    SIGNATURE_FILE,
    sign_bundle,
    verify_bundle_signature,
)
from scripts.mg_ed25519 import generate_key_files  # noqa: E402
from scripts.mg_temporal import (  # noqa: E402
    TEMPORAL_FILE,
    create_temporal_commitment,
    verify_temporal_commitment,
    write_temporal_commitment,
)
from backend.progress.data_integrity import fingerprint_file  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers (copied from test_cert_5layer_independence.py to avoid cross-file
# import fragility)
# ---------------------------------------------------------------------------

def _hash_step(step_name, step_data, prev_hash):
    import json as _j
    content = _j.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _build_valid_trace():
    """Build a valid 4-step execution trace with correct hash chain."""
    params = {"seed": 42, "claimed_accuracy": 0.95}
    prev = _hash_step("init_params", params, "genesis")
    trace = [{"step": 1, "name": "init_params", "hash": prev}]

    results = {"accuracy": 0.95, "passed": True}
    prev = _hash_step("compute", results, prev)
    trace.append({"step": 2, "name": "compute", "hash": prev})

    metrics = {"accuracy": 0.95, "tolerance": 0.02}
    prev = _hash_step("metrics", metrics, prev)
    trace.append({"step": 3, "name": "metrics", "hash": prev})

    prev = _hash_step("threshold_check", {"passed": True, "threshold": 0.02}, prev)
    trace.append({"step": 4, "name": "threshold_check", "hash": prev})

    return trace, prev  # trace, trace_root_hash


def _make_full_5layer_bundle(tmp_path, name="bundle"):
    """
    Create a complete 5-layer valid bundle.

    Returns (bundle_path, key_path, pub_key_path).
    """
    bundle = tmp_path / name
    bundle.mkdir(parents=True, exist_ok=True)

    trace, trace_root_hash = _build_valid_trace()

    claim_id = "ML_BENCH-01"
    job_kind = "mlbench1_accuracy_certificate"

    run_artifact = {
        "w6_phase": "W6-A5",
        "kind": "success",
        "job_id": "job-5layer-001",
        "trace_id": "trace-5layer-001",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": "job-5layer-001",
            "status": "SUCCEEDED",
            "payload": {"kind": job_kind},
            "result": {
                "mtr_phase": claim_id,
                "inputs": {"seed": 42, "claimed_accuracy": 0.95},
                "result": {"accuracy": 0.95, "passed": True,
                           "absolute_error": 0.00, "tolerance": 0.02},
                "execution_trace": trace,
                "trace_root_hash": trace_root_hash,
            },
        },
        "ledger_action": "job_completed",
        "persisted_at": "2026-03-17T00:00:00Z",
    }

    ev_dir = bundle / "evidence" / claim_id / "normal"
    ev_dir.mkdir(parents=True, exist_ok=True)
    run_path = ev_dir / "run_artifact.json"
    run_path.write_text(json.dumps(run_artifact), encoding="utf-8")
    ledger_path = ev_dir / "ledger_snapshot.jsonl"
    ledger_path.write_text(
        json.dumps({
            "trace_id": "trace-5layer-001",
            "action": "job_completed",
            "actor": "scheduler_v1",
            "meta": {"canary_mode": False},
        }) + "\n",
        encoding="utf-8",
    )

    evidence_index = {
        claim_id: {
            "job_kind": job_kind,
            "normal": {
                "run_relpath": f"evidence/{claim_id}/normal/run_artifact.json",
                "ledger_relpath": f"evidence/{claim_id}/normal/ledger_snapshot.jsonl",
            },
        }
    }
    (bundle / "evidence_index.json").write_text(
        json.dumps(evidence_index), encoding="utf-8"
    )

    files_list = []
    for fpath in sorted(bundle.rglob("*")):
        if fpath.is_file() and fpath.name != "pack_manifest.json":
            rel = str(fpath.relative_to(bundle)).replace("\\", "/")
            sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
            files_list.append({
                "relpath": rel,
                "sha256": sha,
                "bytes": fpath.stat().st_size,
            })

    lines_str = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files_list, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines_str.encode("utf-8")).hexdigest()
    manifest = {"version": "v1", "protocol_version": 1, "files": files_list, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    key_path = tmp_path / f"{name}_key.json"
    generate_key_files(key_path)
    pub_key_path = tmp_path / f"{name}_key.pub.json"
    sign_bundle(bundle, key_path)

    mock_beacon = {
        "outputValue": "ab" * 32,
        "timeStamp": "2026-03-17T12:00:00Z",
        "uri": "https://beacon.nist.gov/test",
    }
    with patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=mock_beacon):
        tc = create_temporal_commitment(root_hash)
    write_temporal_commitment(bundle, tc)

    return bundle, key_path, pub_key_path


def _rebuild_manifest(bundle):
    """Rebuild pack_manifest.json hashes for all files in bundle."""
    files_list = []
    for fpath in sorted(bundle.rglob("*")):
        if fpath.is_file() and fpath.name != "pack_manifest.json":
            rel = str(fpath.relative_to(bundle)).replace("\\", "/")
            sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
            files_list.append({
                "relpath": rel,
                "sha256": sha,
                "bytes": fpath.stat().st_size,
            })
    lines_str = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files_list, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines_str.encode("utf-8")).hexdigest()
    manifest = {"version": "v1", "protocol_version": 1, "files": files_list, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return root_hash


class TestCert12EncodingAttacks:
    """
    CERT-12: Encoding and Partial Corruption Attack Proofs.

    Proves that byte-level encoding attacks (BOM injection, null bytes,
    truncated JSON, Unicode homoglyphs) are all detected by the
    MetaGenesis verification pipeline.
    """

    # -----------------------------------------------------------------
    # ADV-05: BOM-prefixed files detected
    # -----------------------------------------------------------------

    def test_adv05_bom_in_evidence_index(self, tmp_path):
        """ADV-05: BOM-prefixed evidence_index.json causes verification failure.

        Attack: Prepend UTF-8 BOM (0xEF 0xBB 0xBF) to evidence_index.json.
        Rebuild manifest so L1 passes. json.loads() rejects BOM with
        JSONDecodeError ("Unexpected UTF-8 BOM").
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        ei_path = bundle / "evidence_index.json"

        # Inject UTF-8 BOM at start of file
        original = ei_path.read_bytes()
        ei_path.write_bytes(b'\xef\xbb\xbf' + original)

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # _verify_semantic reads with encoding="utf-8" -> json.loads rejects BOM
        ok, msg, errors = _verify_semantic(bundle, ei_path)
        assert not ok, f"BOM in evidence_index.json should cause failure: {msg}"
        assert "evidence_index.json" in msg.lower() or "bom" in msg.lower() or "json" in msg.lower(), \
            f"Expected evidence_index/BOM/JSON error, got: {msg}"

        # Also verify via full pipeline
        ok_full, msg_full, _ = _verify_pack(bundle)
        assert not ok_full, f"Full verification should also catch BOM: {msg_full}"

    def test_adv05_bom_in_run_artifact(self, tmp_path):
        """ADV-05: BOM-prefixed run_artifact.json causes verification failure.

        Attack: Prepend UTF-8 BOM to run_artifact.json bytes.
        Rebuild manifest so L1 passes. Semantic check fails when
        loading the BOM-prefixed run artifact JSON.
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        run_path = list(bundle.rglob("run_artifact.json"))[0]

        # Inject BOM prefix
        original = run_path.read_bytes()
        run_path.write_bytes(b'\xef\xbb\xbf' + original)

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Full pipeline should catch the BOM-corrupted run artifact
        ok, msg, _ = _verify_pack(bundle)
        assert not ok, f"BOM in run_artifact.json should cause failure: {msg}"

    def test_adv05_bom_changes_fingerprint(self, tmp_path):
        """ADV-05: BOM changes SHA-256 fingerprint, proving L1 would catch it.

        Without manifest rebuild, BOM-prefixed file produces a different
        SHA-256 hash, so Layer 1 integrity check would catch it.
        """
        # Create a temp JSON file with valid content
        test_file = tmp_path / "test.json"
        test_file.write_text('{"key": "value"}', encoding="utf-8")

        # Compute fingerprint of clean file
        fp_clean = fingerprint_file(test_file)
        hash_clean = fp_clean["sha256"]

        # Prepend BOM
        test_file.write_bytes(b'\xef\xbb\xbf' + test_file.read_bytes())

        # Compute fingerprint of BOM-prefixed file
        fp_bom = fingerprint_file(test_file)
        hash_bom = fp_bom["sha256"]

        # BOM changes the SHA-256 hash, proving L1 would catch it
        assert hash_clean != hash_bom, \
            "BOM prefix must change SHA-256 hash (L1 integrity catch)"

    # -----------------------------------------------------------------
    # ADV-06: Null bytes caught
    # -----------------------------------------------------------------

    def test_adv06_null_bytes_in_run_artifact(self, tmp_path):
        """ADV-06: Null bytes in run_artifact.json cause verification failure.

        Attack: Inject null byte into a string field value. json.loads()
        rejects null bytes with "Invalid control character".
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        run_path = list(bundle.rglob("run_artifact.json"))[0]

        # Inject null byte into JSON content
        original = run_path.read_bytes()
        # Replace "SUCCEEDED" with null-byte-injected version
        corrupted = original.replace(b'"SUCCEEDED"', b'"SUCCEE\x00DED"')
        assert corrupted != original, "Null byte injection must modify the file"
        run_path.write_bytes(corrupted)

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Full pipeline should catch null byte corruption
        ok, msg, _ = _verify_pack(bundle)
        assert not ok, f"Null bytes in run_artifact should cause failure: {msg}"

    def test_adv06_null_bytes_in_evidence_index(self, tmp_path):
        """ADV-06: Null bytes in evidence_index.json cause verification failure.

        Attack: Inject null byte into the claim ID field in evidence_index.json.
        json.loads() rejects null bytes.
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        ei_path = bundle / "evidence_index.json"

        # Inject null byte into claim ID
        original = ei_path.read_bytes()
        corrupted = original.replace(b'"ML_BENCH-01"', b'"ML_BENCH\x00-01"')
        assert corrupted != original, "Null byte injection must modify the file"
        ei_path.write_bytes(corrupted)

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Semantic check should fail on null-byte-corrupted evidence_index
        ok, msg, errors = _verify_semantic(bundle, ei_path)
        assert not ok, f"Null bytes in evidence_index should cause failure: {msg}"

    # -----------------------------------------------------------------
    # ADV-06: Truncated JSON caught
    # -----------------------------------------------------------------

    def test_adv06_truncated_run_artifact(self, tmp_path):
        """ADV-06: Truncated run_artifact.json causes graceful verification failure.

        Attack: Write first 50% of run_artifact.json bytes (missing closing
        braces). Verification must fail gracefully (no unhandled exception).
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        run_path = list(bundle.rglob("run_artifact.json"))[0]

        # Truncate to half the file
        original = run_path.read_bytes()
        run_path.write_bytes(original[:len(original) // 2])

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Full pipeline should catch truncated JSON gracefully
        ok, msg, _ = _verify_pack(bundle)
        assert not ok, f"Truncated run_artifact should cause failure: {msg}"
        # No unhandled exception -- if we got here, it was caught gracefully

    def test_adv06_truncated_evidence_index(self, tmp_path):
        """ADV-06: Truncated evidence_index.json causes graceful verification failure.

        Attack: Write first 50% of evidence_index.json bytes. The JSON
        parser should reject it with JSONDecodeError, caught gracefully.
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        ei_path = bundle / "evidence_index.json"

        # Truncate to half the file
        original = ei_path.read_bytes()
        ei_path.write_bytes(original[:len(original) // 2])

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Semantic check should fail gracefully on truncated JSON
        ok, msg, errors = _verify_semantic(bundle, ei_path)
        assert not ok, f"Truncated evidence_index should cause failure: {msg}"
        # No unhandled exception -- if we got here, it was caught gracefully

    # -----------------------------------------------------------------
    # ADV-06: Homoglyphs caught
    # -----------------------------------------------------------------

    def test_adv06_homoglyph_claim_id(self, tmp_path):
        """ADV-06: Cyrillic homoglyph in claim ID causes verification failure.

        Attack: Replace Latin 'B' in 'ML_BENCH-01' with Cyrillic '\u0412'
        (visually identical). The homoglyph claim ID creates a path mismatch
        with the actual evidence directory, causing semantic verification to
        fail when looking up the run artifact.
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        ei_path = bundle / "evidence_index.json"

        # Read evidence_index and replace claim ID with homoglyph version
        index = json.loads(ei_path.read_text(encoding="utf-8"))
        original_claim = "ML_BENCH-01"
        # Replace Latin 'B' with Cyrillic 'B' (\u0412) -- visually identical
        homoglyph_claim = "ML_\u0412ENCH-01"
        assert original_claim != homoglyph_claim, "Homoglyph must differ from original"

        # Rebuild evidence_index with homoglyph claim ID and updated paths
        entry = index[original_claim]
        # Update relpaths to use homoglyph claim ID (these paths won't exist)
        entry["normal"]["run_relpath"] = f"evidence/{homoglyph_claim}/normal/run_artifact.json"
        entry["normal"]["ledger_relpath"] = f"evidence/{homoglyph_claim}/normal/ledger_snapshot.jsonl"
        new_index = {homoglyph_claim: entry}

        ei_path.write_text(json.dumps(new_index), encoding="utf-8")

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Semantic check fails: run_relpath points to nonexistent path
        # because the evidence directory uses Latin 'B', not Cyrillic 'B'
        ok, msg, errors = _verify_semantic(bundle, ei_path)
        assert not ok, f"Homoglyph claim ID should cause failure: {msg}"

    def test_adv06_homoglyph_in_job_kind(self, tmp_path):
        """ADV-06: Cyrillic homoglyph in job_kind causes semantic verification failure.

        Attack: Replace Latin 'e' in 'mlbench1_accuracy_certificate' with
        Cyrillic '\u0435' (visually identical). The job_kind no longer matches
        payload.kind in the run artifact, causing semantic verification to fail.
        """
        bundle, _, _ = _make_full_5layer_bundle(tmp_path)
        ei_path = bundle / "evidence_index.json"

        # Read evidence_index and change job_kind to homoglyph version
        index = json.loads(ei_path.read_text(encoding="utf-8"))
        claim_id = "ML_BENCH-01"
        original_kind = index[claim_id]["job_kind"]
        # Replace Latin 'e' with Cyrillic 'e' (\u0435) -- visually identical
        homoglyph_kind = "mlb\u0435nch1_accuracy_certificate"
        assert original_kind != homoglyph_kind, "Homoglyph must differ from original"

        index[claim_id]["job_kind"] = homoglyph_kind
        ei_path.write_text(json.dumps(index), encoding="utf-8")

        # Rebuild manifest to bypass L1
        _rebuild_manifest(bundle)

        # Semantic check: payload.kind in run_artifact is still
        # "mlbench1_accuracy_certificate" (Latin), but evidence_index
        # job_kind is now "mlb\u0435nch1_accuracy_certificate" (Cyrillic).
        # The mismatch causes verification failure at line:
        # if payload.get("kind") != job_kind
        ok, msg, errors = _verify_semantic(bundle, ei_path)
        assert not ok, f"Homoglyph in job_kind should cause failure: {msg}"
        assert "job_kind" in msg or "payload" in msg, \
            f"Expected job_kind/payload mismatch error, got: {msg}"
