#!/usr/bin/env python3
"""Adversarial confirmation of security-review findings F1, F2, F3.

These tests confirm three findings from an external security review against the
real verifier (scripts/mg.py).

  F1 (smuggling)   : RESOLVED. mg verify now enumerates the pack directory (not
                     just the files listed in pack_manifest.json) and rejects any
                     file that is neither manifest-listed nor one of the three
                     verification meta-files written outside the manifest
                     (pack_manifest.json, bundle_signature.json,
                     temporal_commitment.json). A file added to the pack but
                     absent from the manifest now causes verify to return rc != 0.
                     Tracked as FAULT_012 (RESOLVED) in reports/known_faults.yaml.
                     The test below asserts this SECURE expectation directly,
                     for both a root-level and a nested smuggled file.

  F2 (sig scope)   : Integrity and authenticity are two distinct steps.
                     mg verify --pack passes on an UNSIGNED pack (integrity),
                     while mg sign verify --pack on the same pack returns rc != 0
                     (no signature present / unknown provenance).

  F3 (timestamp)   : The receipt verification_timestamp derives from the verifier
                     LOCAL clock (mg.py:522 datetime.now(timezone.utc)), not from
                     proof-of-time. Proof-of-time is the temporal commitment layer
                     (NIST Beacon, scripts/mg_temporal.py), a separate layer.
"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
MG_SCRIPT = REPO_ROOT / "scripts" / "mg.py"


def _run_mg(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MG_SCRIPT)] + list(args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


def _build_pack(tmp_path: Path) -> Path:
    """Build a valid pack and confirm it verifies PASS before any tampering."""
    pack_dir = tmp_path / "pack"
    r = _run_mg("pack", "build", "--output", str(pack_dir))
    assert r.returncode == 0, "pack build failed: " + r.stderr
    r = _run_mg("pack", "verify", "--pack", str(pack_dir))
    assert r.returncode == 0 and "PASS" in r.stdout, "clean pack did not verify PASS"
    return pack_dir


class TestSecurityFindingsF1F3:
    """F1/F2/F3 adversarial confirmation against the real verifier."""

    # ── F1: smuggled (manifest-absent) file ────────────────────────────────

    def test_f1_smuggled_file_rejected(self, tmp_path):
        """SECURE expectation for FAULT_012 (RESOLVED): smuggled file → rc != 0.

        mg verify now enumerates the pack directory in addition to the manifest,
        so a file added to the pack but absent from pack_manifest.json is
        detected and rejected. This is the adversarial test required by the fix:
        a valid pack plus an extra unlisted file must FAIL verification. Two
        scenarios are covered to pin the secure behavior:

          1. a root-level smuggled file (INJECTED.md), and
          2. a smuggled file nested in a subdirectory (sub/EVIL.json),

        both of which must drive verify to a non-zero return code. The companion
        check confirms the smuggled file is genuinely invisible to the manifest
        (so rejection comes from directory enumeration, not from a hash change).
        """
        # ── Scenario 1: root-level smuggled file ──────────────────────────────
        pack_dir = _build_pack(tmp_path)
        smuggled = pack_dir / "INJECTED.md"
        smuggled.write_text("smuggled payload not listed in pack_manifest.json")

        # The manifest was not changed, so the smuggled file is invisible to it.
        manifest = json.loads(
            (pack_dir / "pack_manifest.json").read_text(encoding="utf-8")
        )
        listed = {f["relpath"] for f in manifest["files"]}
        assert "INJECTED.md" not in listed, "smuggled file must not be in manifest"

        r = _run_mg("pack", "verify", "--pack", str(pack_dir))
        assert r.returncode != 0, (
            "FAULT_012 regression: a valid pack carrying an extra unlisted "
            "root-level file must FAIL verification (rc != 0), got rc="
            + str(r.returncode)
        )

        # ── Scenario 2: smuggled file nested in a subdirectory ────────────────
        pack_dir2 = _build_pack(tmp_path / "p2")
        nested_dir = pack_dir2 / "sub"
        nested_dir.mkdir()
        (nested_dir / "EVIL.json").write_text("{\"smuggled\": true}")

        manifest2 = json.loads(
            (pack_dir2 / "pack_manifest.json").read_text(encoding="utf-8")
        )
        listed2 = {f["relpath"] for f in manifest2["files"]}
        assert "sub/EVIL.json" not in listed2, "nested smuggled file must not be in manifest"

        r2 = _run_mg("pack", "verify", "--pack", str(pack_dir2))
        assert r2.returncode != 0, (
            "FAULT_012 regression: a valid pack carrying an extra unlisted "
            "file nested in a subdirectory must FAIL verification (rc != 0), "
            "got rc=" + str(r2.returncode)
        )

    # ── F2: integrity passes, authenticity (signature) does not ────────────

    def test_f2_unsigned_pack_passes_integrity(self, tmp_path):
        """Integrity step: mg verify --pack passes on an UNSIGNED pack."""
        pack_dir = _build_pack(tmp_path)
        r = _run_mg("verify", "--pack", str(pack_dir))
        assert r.returncode == 0, "unsigned pack should pass the integrity step"

    def test_f2_unsigned_pack_fails_signature_check(self, tmp_path):
        """Authenticity step: mg sign verify --pack fails on the same UNSIGNED pack.

        Integrity (does the bundle match its manifest?) and authenticity (who
        created the bundle?) are two distinct steps. An unsigned bundle can pass
        integrity yet have unknown provenance.
        """
        pack_dir = _build_pack(tmp_path)
        r = _run_mg("sign", "verify", "--pack", str(pack_dir))
        assert r.returncode != 0, (
            "unsigned pack must fail the signature (authenticity) check"
        )

    # ── F3: receipt timestamp derives from the local clock ─────────────────

    def test_f3_receipt_timestamp_is_local_clock(self, tmp_path):
        """The receipt verification_timestamp tracks the verifier local clock.

        Captures time.time() before/after running mg verify --receipt and asserts
        verification_timestamp parses as an ISO datetime inside that local-clock
        window. Cites mg.py:522 datetime.now(timezone.utc). This proves the
        receipt timestamp is informational (local), not proof-of-time.
        """
        pack_dir = _build_pack(tmp_path)
        receipt_path = tmp_path / "receipt.json"
        t_before = time.time()
        r = _run_mg(
            "verify", "--pack", str(pack_dir), "--receipt", str(receipt_path)
        )
        t_after = time.time()
        assert r.returncode == 0, "verify with receipt should succeed on a valid pack"
        assert receipt_path.exists(), "receipt file should be written"

        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        ts_str = receipt["verification_timestamp"]
        parsed = datetime.fromisoformat(ts_str)
        ts_epoch = parsed.timestamp()

        # Allow a generous margin for subprocess startup and clock resolution.
        margin = 30.0
        assert (t_before - margin) <= ts_epoch <= (t_after + margin), (
            "verification_timestamp is outside the local-clock window: "
            + ts_str
        )

    def test_f3_timestamp_has_no_proof_of_time_source(self, tmp_path):
        """The timestamp field carries no NIST Beacon / proof-of-time markers.

        Proof-of-time lives in the temporal commitment layer (mg_temporal.py),
        not in the receipt timestamp. Assert the timestamp field contains no
        beacon URL or outputValue marker.
        """
        pack_dir = _build_pack(tmp_path)
        receipt_path = tmp_path / "receipt.json"
        r = _run_mg(
            "verify", "--pack", str(pack_dir), "--receipt", str(receipt_path)
        )
        assert r.returncode == 0
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        ts_str = receipt["verification_timestamp"].lower()
        for marker in ("beacon", "nist.gov", "outputvalue", "http"):
            assert marker not in ts_str, (
                "timestamp field must not embed a proof-of-time source: " + marker
            )
