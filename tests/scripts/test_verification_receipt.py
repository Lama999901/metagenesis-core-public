"""Tests for the verification receipt feature (--receipt flag on mg.py verify)."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture
def demo_bundle(tmp_path):
    """Create a minimal valid bundle for receipt testing."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    # Minimal evidence
    ev_dir = bundle / "evidence" / "ML_BENCH-01" / "normal"
    ev_dir.mkdir(parents=True)

    run_artifact = {
        "trace_id": "trace-receipt-001",
        "canary_mode": False,
        "job_snapshot": {
            "job_id": "job-receipt-001",
            "status": "SUCCEEDED",
            "payload": {"kind": "mlbench1_accuracy_certificate"},
            "result": {
                "mtr_phase": "ML_BENCH-01",
                "inputs": {"seed": 42},
                "result": {"pass": True},
                "execution_trace": [
                    {"step": 1, "name": "init_params", "hash": "a" * 64},
                    {"step": 2, "name": "compute", "hash": "b" * 64},
                    {"step": 3, "name": "metrics", "hash": "c" * 64},
                    {"step": 4, "name": "threshold_check", "hash": "d" * 64},
                ],
                "trace_root_hash": "d" * 64,
            },
        },
    }
    (ev_dir / "run_artifact.json").write_text(
        json.dumps(run_artifact), encoding="utf-8"
    )
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        json.dumps({"trace_id": "trace-receipt-001", "action": "job_completed"}) + "\n",
        encoding="utf-8",
    )

    evidence_index = {
        "ML_BENCH-01": {
            "job_kind": "mlbench1_accuracy_certificate",
            "normal": {
                "run_relpath": "evidence/ML_BENCH-01/normal/run_artifact.json",
                "ledger_relpath": "evidence/ML_BENCH-01/normal/ledger_snapshot.jsonl",
            },
        }
    }
    (bundle / "evidence_index.json").write_text(
        json.dumps(evidence_index), encoding="utf-8"
    )

    # Build pack_manifest
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
    manifest = {"version": "v1", "protocol_version": 1,
                "files": files_list, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    return bundle


class TestVerificationReceipt:
    """Tests for the --receipt flag."""

    def test_receipt_written_on_pass(self, demo_bundle, tmp_path):
        from scripts.mg import _verify_pack
        ok, msg, report = _verify_pack(demo_bundle)
        assert ok

        # Import and call the receipt writer directly
        # (since it's defined inside main(), we test via subprocess)
        import subprocess
        receipt_path = tmp_path / "receipt.json"
        result = subprocess.run(
            [sys.executable, "scripts/mg.py", "verify",
             "--pack", str(demo_bundle), "--receipt", str(receipt_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert result.returncode == 0
        assert receipt_path.exists()

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert receipt["result"] == "PASS"
        assert receipt["receipt_version"] == "1.0"
        assert receipt["bundle_root_hash"] != ""
        assert "receipt_hash" in receipt
        assert len(receipt["layers_checked"]) > 0

    def test_receipt_hash_is_valid(self, demo_bundle, tmp_path):
        import subprocess
        receipt_path = tmp_path / "receipt.json"
        subprocess.run(
            [sys.executable, "scripts/mg.py", "verify",
             "--pack", str(demo_bundle), "--receipt", str(receipt_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        # Verify receipt_hash integrity
        stored_hash = receipt.pop("receipt_hash")
        recomputed = hashlib.sha256(
            json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert stored_hash == recomputed, "Receipt hash does not match recomputed hash"

    def test_receipt_on_fail(self, tmp_path):
        # Empty bundle should fail verification
        bad_bundle = tmp_path / "bad_bundle"
        bad_bundle.mkdir()

        import subprocess
        receipt_path = tmp_path / "fail_receipt.json"
        result = subprocess.run(
            [sys.executable, "scripts/mg.py", "verify",
             "--pack", str(bad_bundle), "--receipt", str(receipt_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert result.returncode == 1
        assert receipt_path.exists()

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        assert receipt["result"] == "FAIL"
        assert len(receipt["errors"]) > 0
