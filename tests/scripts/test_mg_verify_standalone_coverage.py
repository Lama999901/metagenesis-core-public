"""Tests for scripts/mg_verify_standalone.py -- layer3 and evidence_index coverage."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_verify_standalone import (
    _verify_evidence_index,
    _verify_trace,
    verify_layer3_step_chain,
)


# ---- Helper to build a valid 4-step trace ------------------------------------

def _make_trace():
    """Build a valid 4-step execution trace with correct hashes."""
    def _hash_step(step_name, step_data, prev_hash):
        content = json.dumps(
            {"step": step_name, "data": step_data, "prev_hash": prev_hash},
            sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    h1 = _hash_step("init_params", {"seed": 42}, "genesis")
    h2 = _hash_step("compute", {"value": 1.0}, h1)
    h3 = _hash_step("metrics", {"error": 0.001}, h2)
    h4 = _hash_step("threshold_check", {"passed": True, "threshold": 0.01}, h3)

    trace = [
        {"step": 1, "name": "init_params", "hash": h1},
        {"step": 2, "name": "compute", "hash": h2},
        {"step": 3, "name": "metrics", "hash": h3},
        {"step": 4, "name": "threshold_check", "hash": h4, "output": {"pass": True}},
    ]
    return trace, h4


# ---- _verify_trace tests -----------------------------------------------------


def test_verify_trace_valid():
    trace, root = _make_trace()
    ok, msg = _verify_trace(trace, root, "test")
    assert ok is True
    assert "4-step chain verified" in msg


def test_verify_trace_both_none():
    ok, msg = _verify_trace(None, None, "test")
    assert ok is True
    assert "skip" in msg.lower()


def test_verify_trace_missing_trace():
    ok, msg = _verify_trace(None, "abc123", "test")
    assert ok is False
    assert "missing execution_trace" in msg


def test_verify_trace_missing_root():
    trace, _ = _make_trace()
    ok, msg = _verify_trace(trace, None, "test")
    assert ok is False
    assert "missing trace_root_hash" in msg


def test_verify_trace_empty_list():
    ok, msg = _verify_trace([], "abc", "test")
    assert ok is False
    assert "non-empty list" in msg


def test_verify_trace_wrong_step_count():
    trace, root = _make_trace()
    ok, msg = _verify_trace(trace[:3], root, "test")
    assert ok is False
    assert "4 steps" in msg


def test_verify_trace_wrong_step_numbers():
    trace, root = _make_trace()
    trace[0]["step"] = 0  # should be 1
    ok, msg = _verify_trace(trace, root, "test")
    assert ok is False
    assert "must be [1,2,3,4]" in msg or "steps" in msg


def test_verify_trace_invalid_hash():
    trace, root = _make_trace()
    trace[1]["hash"] = "not-a-valid-hex"
    ok, msg = _verify_trace(trace, root, "test")
    assert ok is False
    assert "invalid hash" in msg


def test_verify_trace_root_mismatch():
    trace, _ = _make_trace()
    ok, msg = _verify_trace(trace, "0" * 64, "test")
    assert ok is False
    assert "Step Chain broken" in msg


# ---- verify_layer3_step_chain tests ------------------------------------------


def test_layer3_with_evidence_json(tmp_path):
    trace, root = _make_trace()
    evidence = {
        "mtr_phase": "MTR-1",
        "execution_trace": trace,
        "trace_root_hash": root,
    }
    (tmp_path / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    ok, msg = verify_layer3_step_chain(tmp_path)
    assert ok is True


def test_layer3_tampered_evidence(tmp_path):
    trace, root = _make_trace()
    trace[3]["hash"] = "f" * 64  # tamper the final step hash
    evidence = {
        "mtr_phase": "MTR-1",
        "execution_trace": trace,
        "trace_root_hash": root,  # original root != tampered final hash
    }
    (tmp_path / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    ok, msg = verify_layer3_step_chain(tmp_path)
    assert ok is False


def test_layer3_no_evidence_no_index(tmp_path):
    ok, msg = verify_layer3_step_chain(tmp_path)
    assert ok is True
    assert "verified" in msg.lower()


# ---- _verify_evidence_index tests --------------------------------------------


def test_evidence_index_valid(tmp_path):
    """Build a valid evidence_index.json with run artifacts."""
    # Create run artifact
    runs_dir = tmp_path / "progress_runs"
    runs_dir.mkdir()
    trace, root = _make_trace()
    run_art = {
        "trace_id": "t1",
        "job_snapshot": {
            "result": {
                "mtr_phase": "MTR-1",
                "execution_trace": trace,
                "trace_root_hash": root,
            }
        },
        "canary_mode": False,
    }
    run_path = runs_dir / "run_001.json"
    run_path.write_text(json.dumps(run_art), encoding="utf-8")

    # Create evidence_index.json
    index = {
        "MTR-1": {
            "job_kind": "calibration",
            "normal": {
                "run_relpath": "progress_runs/run_001.json",
                "ledger_relpath": "ledger.jsonl",
            },
        },
    }
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")

    ok, msg, claim_info = _verify_evidence_index(tmp_path, index_path)
    assert ok is True
    assert claim_info is not None
    assert claim_info["claim_id"] == "MTR-1"


def test_evidence_index_missing_file(tmp_path):
    index_path = tmp_path / "evidence_index.json"
    # File doesn't exist
    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False


def test_evidence_index_malformed_json(tmp_path):
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text("not json!", encoding="utf-8")
    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False
    assert "Invalid" in msg


def test_evidence_index_not_object(tmp_path):
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text("[]", encoding="utf-8")
    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False
    assert "must be an object" in msg


def test_evidence_index_missing_job_kind(tmp_path):
    index = {
        "MTR-1": {
            "normal": {
                "run_relpath": "run.json",
                "ledger_relpath": "ledger.jsonl",
            },
        },
    }
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")
    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False
    assert "missing job_kind" in msg


def test_evidence_index_missing_relpath(tmp_path):
    index = {
        "MTR-1": {
            "job_kind": "calibration",
            "normal": {
                "run_relpath": "",
                "ledger_relpath": "ledger.jsonl",
            },
        },
    }
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")
    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False
    assert "missing relpath" in msg


def test_evidence_index_missing_run_artifact(tmp_path):
    index = {
        "MTR-1": {
            "job_kind": "calibration",
            "normal": {
                "run_relpath": "nonexistent.json",
                "ledger_relpath": "ledger.jsonl",
            },
        },
    }
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")
    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False
    assert "missing" in msg.lower()


def test_evidence_index_run_missing_required_key(tmp_path):
    """Run artifact missing trace_id."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    run_art = {
        "job_snapshot": {"result": {"mtr_phase": "MTR-1"}},
        "canary_mode": False,
        # missing trace_id
    }
    (runs_dir / "run.json").write_text(json.dumps(run_art), encoding="utf-8")

    index = {
        "MTR-1": {
            "job_kind": "calibration",
            "normal": {
                "run_relpath": "runs/run.json",
                "ledger_relpath": "ledger.jsonl",
            },
        },
    }
    index_path = tmp_path / "evidence_index.json"
    index_path.write_text(json.dumps(index), encoding="utf-8")

    ok, msg, info = _verify_evidence_index(tmp_path, index_path)
    assert ok is False
    assert "missing" in msg.lower()


# ---- Additional coverage: verify_layer2_semantic, layer4, layer5, format_receipt --


from scripts.mg_verify_standalone import (
    _verify_evidence_json,
    verify_layer2_semantic,
    verify_layer4_signature,
    verify_layer5_temporal,
    format_receipt,
)


# ---- _verify_evidence_json tests ----------------------------------------------


def test_verify_evidence_json_valid(tmp_path):
    trace, root = _make_trace()
    evidence = {
        "mtr_phase": "MTR-1",
        "execution_trace": trace,
        "trace_root_hash": root,
    }
    ep = tmp_path / "evidence.json"
    ep.write_text(json.dumps(evidence), encoding="utf-8")
    ok, msg, info = _verify_evidence_json(ep)
    assert ok is True
    assert info["claim_id"] == "MTR-1"


def test_verify_evidence_json_missing_key(tmp_path):
    ep = tmp_path / "evidence.json"
    ep.write_text(json.dumps({"mtr_phase": "X"}), encoding="utf-8")
    ok, msg, info = _verify_evidence_json(ep)
    assert ok is False
    assert "missing required key" in msg


def test_verify_evidence_json_invalid_json(tmp_path):
    ep = tmp_path / "evidence.json"
    ep.write_text("not json!", encoding="utf-8")
    ok, msg, info = _verify_evidence_json(ep)
    assert ok is False
    assert "Invalid" in msg


# ---- verify_layer2_semantic tests --------------------------------------------


def test_layer2_with_evidence_json(tmp_path):
    trace, root = _make_trace()
    evidence = {
        "mtr_phase": "MTR-1",
        "execution_trace": trace,
        "trace_root_hash": root,
    }
    (tmp_path / "evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    ok, msg, info = verify_layer2_semantic(tmp_path)
    assert ok is True


def test_layer2_no_evidence(tmp_path):
    ok, msg, info = verify_layer2_semantic(tmp_path)
    assert ok is True
    assert "skip" in msg.lower()


# ---- verify_layer4_signature tests -------------------------------------------


def test_layer4_no_signature_file(tmp_path):
    ok, msg = verify_layer4_signature(tmp_path, None)
    assert ok is True
    assert "skip" in msg.lower()


def test_layer4_with_signature_matching(tmp_path):
    import hmac as _hmac
    root_hash = "a" * 64
    key_hex = "deadbeef" * 8
    key_bytes = bytes.fromhex(key_hex)
    sig = _hmac.new(key_bytes, root_hash.encode("utf-8"), hashlib.sha256).hexdigest()
    fp = hashlib.sha256(key_bytes).hexdigest()

    sig_data = {
        "signed_root_hash": root_hash,
        "signature": sig,
        "key_fingerprint": fp,
    }
    (tmp_path / "bundle_signature.json").write_text(
        json.dumps(sig_data), encoding="utf-8"
    )
    key_data = {"key_hex": key_hex}
    (tmp_path / "signing_key.json").write_text(
        json.dumps(key_data), encoding="utf-8"
    )
    manifest = {"root_hash": root_hash}
    ok, msg = verify_layer4_signature(tmp_path, manifest)
    assert ok is True
    assert "HMAC-SHA256 valid" in msg


def test_layer4_signature_root_mismatch(tmp_path):
    sig_data = {
        "signed_root_hash": "a" * 64,
        "signature": "b" * 64,
        "key_fingerprint": "c" * 64,
    }
    (tmp_path / "bundle_signature.json").write_text(
        json.dumps(sig_data), encoding="utf-8"
    )
    manifest = {"root_hash": "d" * 64}
    ok, msg = verify_layer4_signature(tmp_path, manifest)
    assert ok is False
    assert "does not match" in msg


def test_layer4_signature_no_key(tmp_path):
    """Signature present but no signing key -- returns pass with fingerprint."""
    sig_data = {
        "signed_root_hash": "a" * 64,
        "signature": "b" * 64,
        "key_fingerprint": "c" * 64,
    }
    (tmp_path / "bundle_signature.json").write_text(
        json.dumps(sig_data), encoding="utf-8"
    )
    ok, msg = verify_layer4_signature(tmp_path, {"root_hash": "a" * 64})
    assert ok is True
    assert "fingerprint" in msg.lower()


# ---- verify_layer5_temporal tests --------------------------------------------


def test_layer5_no_temporal(tmp_path):
    ok, msg = verify_layer5_temporal(tmp_path, None)
    assert ok is True
    assert "skip" in msg.lower()


def test_layer5_beacon_unavailable(tmp_path):
    tc = {
        "pre_commitment_hash": hashlib.sha256(("a" * 64).encode()).hexdigest(),
        "beacon_status": "unavailable",
        "local_timestamp": "2026-04-11T00:00:00Z",
    }
    (tmp_path / "temporal_commitment.json").write_text(
        json.dumps(tc), encoding="utf-8"
    )
    manifest = {"root_hash": "a" * 64}
    ok, msg = verify_layer5_temporal(tmp_path, manifest)
    assert ok is True
    assert "Local timestamp" in msg


def test_layer5_pre_commitment_mismatch(tmp_path):
    tc = {
        "pre_commitment_hash": "wrong_hash",
        "beacon_status": "unavailable",
        "local_timestamp": "2026-04-11T00:00:00Z",
    }
    (tmp_path / "temporal_commitment.json").write_text(
        json.dumps(tc), encoding="utf-8"
    )
    manifest = {"root_hash": "a" * 64}
    ok, msg = verify_layer5_temporal(tmp_path, manifest)
    assert ok is False
    assert "mismatch" in msg.lower()


def test_layer5_full_beacon_valid(tmp_path):
    root_hash = "a" * 64
    pre = hashlib.sha256(root_hash.encode()).hexdigest()
    beacon_output = "b" * 64
    beacon_ts = "2026-04-11T00:00:00Z"
    binding = hashlib.sha256(
        (pre + beacon_output + beacon_ts).encode()
    ).hexdigest()
    tc = {
        "pre_commitment_hash": pre,
        "beacon_output_value": beacon_output,
        "beacon_timestamp": beacon_ts,
        "temporal_binding": binding,
    }
    (tmp_path / "temporal_commitment.json").write_text(
        json.dumps(tc), encoding="utf-8"
    )
    manifest = {"root_hash": root_hash}
    ok, msg = verify_layer5_temporal(tmp_path, manifest)
    assert ok is True
    assert "NIST Beacon verified" in msg


# ---- format_receipt tests ----------------------------------------------------


def test_format_receipt_with_claim_info(tmp_path):
    results = [
        ("Layer 1 -- SHA-256 Integrity", True, "All verified"),
        ("Layer 2 -- Semantic", True, "Claim MTR-1 verified"),
        ("Layer 3 -- Step Chain", True, "4-step chain verified"),
        ("Layer 4 -- Bundle Signature", True, "HMAC valid"),
        ("Layer 5 -- Temporal", True, "NIST Beacon verified"),
    ]
    claim_info = {
        "claim_id": "MTR-1",
        "evidence": {
            "result": {"relative_error": 0.001, "pass": True},
            "trace_root_hash": "a" * 64,
        },
    }
    receipt = format_receipt(tmp_path, results, claim_info)
    assert "MTR-1" in receipt
    assert "PASS" in receipt
    assert "relative_error" in receipt
    assert "70 GPa" in receipt  # physical anchor for MTR-1


def test_format_receipt_without_claim_info(tmp_path):
    results = [
        ("Layer 1", True, "OK"),
    ]
    receipt = format_receipt(tmp_path, results, None)
    assert "PASS" in receipt
    assert "VERIFICATION RECEIPT" in receipt


def test_format_receipt_fail_verdict(tmp_path):
    results = [
        ("Layer 1", False, "SHA mismatch"),
    ]
    receipt = format_receipt(tmp_path, results, None)
    assert "FAIL" in receipt
