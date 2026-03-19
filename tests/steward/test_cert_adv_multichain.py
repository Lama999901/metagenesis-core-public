#!/usr/bin/env python3
"""
CERT-ADV-MULTICHAIN: Layer 3 + Layer 5 Multi-Vector Attack.

Tests that combine step chain tamper (Layer 3) with temporal replay (Layer 5).
Proves both layers catch attacks independently.

Scenarios:
  1. Tamper trace AND replay temporal -> both L3 and L5 catch
  2. Tamper trace only, temporal valid -> L3 catches
  3. Valid trace, replay temporal only -> L5 catches
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
from scripts.mg_sign import sign_bundle, verify_bundle_signature, SIGNATURE_FILE  # noqa: E402
from scripts.mg_ed25519 import generate_key_files  # noqa: E402
from scripts.mg_temporal import (  # noqa: E402
    create_temporal_commitment,
    verify_temporal_commitment,
    write_temporal_commitment,
    TEMPORAL_FILE,
)


def _hash_step(step_name, step_data, prev_hash):
    """Compute SHA-256 step hash for step chain construction."""
    import json as _j
    content = _j.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


_MOCK_BEACON = {
    "outputValue": "deadbeef" * 16,
    "timeStamp": "2026-03-19T12:00:00Z",
    "uri": "https://beacon.nist.gov/beacon/2.0/chain/test/pulse/1",
}

_MOCK_BEACON_B = {
    "outputValue": "cafebabe" * 16,
    "timeStamp": "2026-03-19T13:00:00Z",
    "uri": "https://beacon.nist.gov/beacon/2.0/chain/test/pulse/2",
}


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

    return trace, prev


def _build_full_bundle(tmp_path, name="bundle", mock_beacon=None):
    """Create a complete 5-layer valid bundle. Returns (bundle, key_path, pub_key_path)."""
    if mock_beacon is None:
        mock_beacon = _MOCK_BEACON

    bundle = tmp_path / name
    bundle.mkdir(parents=True, exist_ok=True)

    trace, trace_root_hash = _build_valid_trace()
    claim_id = "ML_BENCH-01"
    job_kind = "mlbench1_accuracy_certificate"

    run_artifact = {
        "w6_phase": "W6-A5", "kind": "success",
        "job_id": f"job-{name}-001", "trace_id": f"trace-{name}-001",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": f"job-{name}-001", "status": "SUCCEEDED",
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
        "persisted_at": "2026-03-19T00:00:00Z",
    }

    ev_dir = bundle / "evidence" / claim_id / "normal"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / "run_artifact.json").write_text(json.dumps(run_artifact), encoding="utf-8")
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        json.dumps({"trace_id": f"trace-{name}-001", "action": "job_completed",
                     "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
        encoding="utf-8")

    evidence_index = {
        claim_id: {
            "job_kind": job_kind,
            "normal": {
                "run_relpath": f"evidence/{claim_id}/normal/run_artifact.json",
                "ledger_relpath": f"evidence/{claim_id}/normal/ledger_snapshot.jsonl",
            },
        }
    }
    (bundle / "evidence_index.json").write_text(json.dumps(evidence_index), encoding="utf-8")

    # Build manifest
    files_list = []
    for fpath in sorted(bundle.rglob("*")):
        if fpath.is_file() and fpath.name != "pack_manifest.json":
            rel = str(fpath.relative_to(bundle)).replace("\\", "/")
            sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
            files_list.append({"relpath": rel, "sha256": sha, "bytes": fpath.stat().st_size})

    lines_str = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files_list, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines_str.encode("utf-8")).hexdigest()
    manifest = {"version": "v1", "protocol_version": 1, "files": files_list, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Sign
    key_path = tmp_path / f"{name}_key.json"
    generate_key_files(key_path)
    pub_key_path = tmp_path / f"{name}_key.pub.json"
    sign_bundle(bundle, key_path)

    # Temporal
    with patch("scripts.mg_temporal._fetch_beacon_pulse", return_value=mock_beacon):
        tc = create_temporal_commitment(root_hash)
    write_temporal_commitment(bundle, tc)

    return bundle, key_path, pub_key_path


class TestCertAdvMultichain:
    """Layer 3 + Layer 5 multi-vector attack tests."""

    def test_multichain_tamper_trace_and_replay_temporal(self, tmp_path):
        """
        Tamper step chain hash AND replay temporal from different bundle.
        Both Layer 3 and Layer 5 should catch independently.
        """
        bundle_a, key_a, pub_a = _build_full_bundle(tmp_path / "a", "bundle_a", _MOCK_BEACON)
        bundle_b, key_b, pub_b = _build_full_bundle(tmp_path / "b", "bundle_b", _MOCK_BEACON_B)

        # ATTACK: Tamper step chain in bundle_a (L3 target)
        run_path = list(bundle_a.rglob("run_artifact.json"))[0]
        data = json.loads(run_path.read_text(encoding="utf-8"))
        data["job_snapshot"]["result"]["trace_root_hash"] = "00" * 32
        run_path.write_text(json.dumps(data), encoding="utf-8")

        # ATTACK: Replay temporal from bundle_b to bundle_a (L5 target)
        tc_b = (bundle_b / TEMPORAL_FILE).read_text(encoding="utf-8")
        (bundle_a / TEMPORAL_FILE).write_text(tc_b, encoding="utf-8")

        # L3: Step chain catches the forged trace_root_hash
        ei_path = bundle_a / "evidence_index.json"
        ok_l3, msg_l3, _ = _verify_semantic(bundle_a, ei_path)
        assert ok_l3 is False, f"Layer 3 should catch forged trace_root_hash: {msg_l3}"

        # L5: Temporal catches the replayed commitment
        ok_l5, msg_l5 = verify_temporal_commitment(bundle_a)
        assert ok_l5 is False, f"Layer 5 should catch replayed temporal: {msg_l5}"

    def test_multichain_tamper_trace_only(self, tmp_path):
        """Tamper step chain only, temporal valid. Layer 3 catches."""
        bundle, key, pub = _build_full_bundle(tmp_path, "bundle")

        # ATTACK: Tamper trace_root_hash only
        run_path = list(bundle.rglob("run_artifact.json"))[0]
        data = json.loads(run_path.read_text(encoding="utf-8"))
        data["job_snapshot"]["result"]["trace_root_hash"] = "00" * 32
        run_path.write_text(json.dumps(data), encoding="utf-8")

        # L3 catches
        ei_path = bundle / "evidence_index.json"
        ok_l3, msg_l3, _ = _verify_semantic(bundle, ei_path)
        assert ok_l3 is False, f"Layer 3 should catch tampered trace: {msg_l3}"

        # L5 still valid (temporal not touched)
        ok_l5, msg_l5 = verify_temporal_commitment(bundle)
        assert ok_l5 is True, f"Layer 5 should still pass: {msg_l5}"

    def test_multichain_replay_temporal_only(self, tmp_path):
        """Valid step chain, replayed temporal. Layer 5 catches."""
        bundle_a, _, _ = _build_full_bundle(tmp_path / "a", "bundle_a", _MOCK_BEACON)
        bundle_b, _, _ = _build_full_bundle(tmp_path / "b", "bundle_b", _MOCK_BEACON_B)

        # ATTACK: Replay temporal from bundle_b
        tc_b = (bundle_b / TEMPORAL_FILE).read_text(encoding="utf-8")
        (bundle_a / TEMPORAL_FILE).write_text(tc_b, encoding="utf-8")

        # L3 still valid (trace not touched)
        ei_path = bundle_a / "evidence_index.json"
        ok_l3, msg_l3, _ = _verify_semantic(bundle_a, ei_path)
        assert ok_l3 is True, f"Layer 3 should still pass: {msg_l3}"

        # L5 catches replayed temporal
        ok_l5, msg_l5 = verify_temporal_commitment(bundle_a)
        assert ok_l5 is False, f"Layer 5 should catch replayed temporal: {msg_l5}"
