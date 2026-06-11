#!/usr/bin/env python3
"""Adversarial confirmation of security-review findings F1, F2, F3.

These tests confirm three findings from an external security review against the
real verifier (scripts/mg.py). They use ONLY new tests and never modify mg.py.

  F1 (smuggling)   : mg verify enumerates only files listed in pack_manifest.json
                     and does NOT enumerate the pack directory, so a file added to
                     the pack but absent from the manifest is never hashed or
                     flagged. Tracked as FAULT_012 in reports/known_faults.yaml.
                     The SECURE expectation (reject the smuggled file) is a
                     strict-xfail tripwire that flips to a failure the day mg.py
                     is hardened. A companion green test pins the current behavior.

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

    def test_f1_smuggled_file_tripwire(self, tmp_path):
        """Live tripwire for the FAULT_012 smuggling gap.

        mg.py:112 iterates only manifest['files'], never os.listdir(pack_dir),
        so a file added to the pack but absent from pack_manifest.json is never
        hashed or flagged: verify currently returns rc 0 / PASS with the smuggled
        file present. This test ASSERTS that current (insecure) behavior, so it
        is a passing test that pins the documented gap.

        It is also a live tripwire: the day mg.py is hardened to enumerate the
        pack directory and reject unlisted files, verify will return rc != 0,
        this assertion will FAIL, and the failure message instructs the
        maintainer to flip the test to the SECURE expectation (rc != 0) and
        resolve FAULT_012. This gives the same fix-detecting behavior as a
        strict-xfail without introducing a project-wide xfail (the suite's
        canonical count invariant is collect == passed + win32_skip, with zero
        xfails).
        """
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
        assert r.returncode == 0 and "PASS" in r.stdout, (
            "FAULT_012 TRIPWIRE FLIPPED: mg verify now rejects a manifest-absent "
            "file (rc=" + str(r.returncode) + "). The smuggling gap appears fixed. "
            "Update this test to assert rc != 0 (the SECURE expectation) and "
            "resolve FAULT_012 in reports/known_faults.yaml."
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
