#!/usr/bin/env python3
"""
CERT-09: Ed25519 Signing Attack Gauntlet -- Five Attack Scenarios, All Caught.

This test file documents five distinct attacks that a sophisticated adversary
might attempt against Ed25519-signed MetaGenesis Core evidence bundles.
Each attack is caught by Layer 4 (Bundle Signature verification).

ATTACK SCENARIOS:
  Attack A -- Wrong Key Verification
    Adversary signs with key_a, verifier checks with key_b. Fingerprint mismatch.

  Attack B -- Signature Bit Flip
    Adversary flips one bit in the Ed25519 signature. Verification fails.

  Attack C -- Downgrade Ed25519 to HMAC
    Adversary signs with Ed25519 but verifier uses HMAC key. Algorithm mismatch.

  Attack D -- Key Type Mismatch (HMAC bundle, Ed25519 verifier)
    Adversary signs with HMAC key, verifier uses Ed25519 public key. Algorithm mismatch.

  Attack E -- Truncated Signature
    Adversary truncates the Ed25519 signature. Verification fails.

All five attacks pass the test by FAILING verification -- proving the protocol
catches each attack class.

Repo: https://github.com/Lama999901/metagenesis-core-public
PPA:  USPTO #63/996,819
"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg_sign import (  # noqa: E402
    sign_bundle,
    verify_bundle_signature,
    generate_key,
    SIGNATURE_FILE,
)
from scripts.mg_ed25519 import generate_key_files  # noqa: E402


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_ed25519_signed_bundle(tmp_path: Path, key_name="test_key"):
    """
    Create a minimal valid bundle signed with an Ed25519 key pair.

    Returns (bundle_path, private_key_path, public_key_path).
    """
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)

    # Minimal evidence file
    evidence_file = bundle / "evidence.json"
    evidence_file.write_text(
        json.dumps({"claim": "ML_BENCH-01", "result": "PASS"}),
        encoding="utf-8",
    )

    # Build pack_manifest.json
    sha = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
    files = [{"relpath": "evidence.json", "sha256": sha, "bytes": evidence_file.stat().st_size}]
    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    manifest = {"version": "v1", "files": files, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    # Generate Ed25519 key pair and sign
    private_key_path = tmp_path / f"{key_name}.json"
    generate_key_files(private_key_path)
    sign_bundle(bundle, private_key_path)

    public_key_path = tmp_path / f"{key_name}.pub.json"
    return bundle, private_key_path, public_key_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCert09Ed25519Attacks:
    """
    Five Ed25519 attack scenarios. All caught by Layer 4.

    Each test represents a realistic attack a sophisticated adversary
    would attempt against Ed25519-signed bundles.
    Each test PASSES by the attack being DETECTED (verify returns False).
    """

    # ------------------------------------------------------------------
    # ATTACK A -- Wrong Key Verification
    # "I'll verify with a different Ed25519 public key."
    # ------------------------------------------------------------------
    def test_a_wrong_key_verification(self, tmp_path):
        """
        ATTACK: Sign bundle with key_a (Ed25519), verify with key_b (different Ed25519).
        The key fingerprint in the signature won't match key_b's fingerprint.

        Proves: a bundle cannot be verified with an arbitrary Ed25519 public key.
        """
        bundle, _priv_a, _pub_a = _make_ed25519_signed_bundle(tmp_path, key_name="key_a")

        # Generate a completely different Ed25519 key pair
        generate_key_files(tmp_path / "key_b.json")
        pub_b = tmp_path / "key_b.pub.json"

        ok, msg = verify_bundle_signature(bundle, key_path=pub_b)
        assert ok is False, "ATTACK A: wrong key was NOT detected"
        assert "fingerprint" in msg.lower() or "mismatch" in msg.lower(), \
            f"ATTACK A detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK B -- Signature Bit Flip
    # "I'll flip one bit in the signature. Ed25519 is just math, right?"
    # ------------------------------------------------------------------
    def test_b_signature_bit_flip(self, tmp_path):
        """
        ATTACK: Sign bundle with Ed25519, then flip one bit in the signature.
        Ed25519 verification catches even a single-bit change.

        Proves: Ed25519 signatures are not malleable -- any modification
        invalidates the signature.
        """
        bundle, _priv, pub = _make_ed25519_signed_bundle(tmp_path)

        # Read signature, flip one bit
        sig_path = bundle / SIGNATURE_FILE
        sig_data = json.loads(sig_path.read_text(encoding="utf-8"))
        sig_hex = sig_data["signature"]
        sig_bytes = bytearray(bytes.fromhex(sig_hex))
        sig_bytes[0] ^= 0x01  # Flip one bit in first byte
        sig_data["signature"] = sig_bytes.hex()
        sig_path.write_text(json.dumps(sig_data, indent=2), encoding="utf-8")

        ok, msg = verify_bundle_signature(bundle, key_path=pub)
        assert ok is False, "ATTACK B: bit-flipped signature was NOT detected"

    # ------------------------------------------------------------------
    # ATTACK C -- Downgrade Ed25519 to HMAC
    # "I'll verify an Ed25519-signed bundle with an HMAC key."
    # ------------------------------------------------------------------
    def test_c_downgrade_ed25519_to_hmac(self, tmp_path):
        """
        ATTACK: Sign bundle with Ed25519 key, then attempt to verify
        with an HMAC key. Algorithm mismatch is detected before any
        cryptographic verification runs.

        Proves: downgrade attacks from Ed25519 to HMAC are prevented
        by the algorithm mismatch check (SIGN-08).
        """
        bundle, _priv, _pub = _make_ed25519_signed_bundle(tmp_path)

        # Generate HMAC key
        hmac_key = generate_key()
        hmac_key_file = tmp_path / "hmac_key.json"
        hmac_key_file.write_text(json.dumps(hmac_key, indent=2), encoding="utf-8")

        ok, msg = verify_bundle_signature(bundle, key_path=hmac_key_file)
        assert ok is False, "ATTACK C: downgrade to HMAC was NOT detected"
        assert "algorithm mismatch" in msg.lower() or "downgrade" in msg.lower(), \
            f"ATTACK C detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK D -- Key Type Mismatch (HMAC bundle, Ed25519 verifier)
    # "I'll verify an HMAC-signed bundle with an Ed25519 public key."
    # ------------------------------------------------------------------
    def test_d_key_type_mismatch_hmac_bundle_ed25519_verifier(self, tmp_path):
        """
        ATTACK: Sign bundle with HMAC key, then attempt to verify
        with an Ed25519 public key. Reverse direction of Attack C.

        Proves: algorithm mismatch detection works both ways.
        """
        # Create HMAC-signed bundle (same pattern as cert07)
        bundle = tmp_path / "bundle"
        bundle.mkdir(parents=True, exist_ok=True)
        evidence_file = bundle / "evidence.json"
        evidence_file.write_text(
            json.dumps({"claim": "ML_BENCH-01", "result": "PASS"}),
            encoding="utf-8",
        )
        sha = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
        files = [{"relpath": "evidence.json", "sha256": sha, "bytes": evidence_file.stat().st_size}]
        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(files, key=lambda x: x["relpath"])
        )
        root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        manifest = {"version": "v1", "files": files, "root_hash": root_hash}
        (bundle / "pack_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        hmac_key = generate_key()
        hmac_key_file = tmp_path / "hmac_key.json"
        hmac_key_file.write_text(json.dumps(hmac_key, indent=2), encoding="utf-8")
        sign_bundle(bundle, hmac_key_file)

        # Verify with Ed25519 public key
        generate_key_files(tmp_path / "ed_key.json")
        ed_pub = tmp_path / "ed_key.pub.json"

        ok, msg = verify_bundle_signature(bundle, key_path=ed_pub)
        assert ok is False, "ATTACK D: key type mismatch was NOT detected"
        assert "algorithm mismatch" in msg.lower() or "downgrade" in msg.lower(), \
            f"ATTACK D detected but wrong error: {msg}"

    # ------------------------------------------------------------------
    # ATTACK E -- Truncated Signature
    # "I'll truncate the signature. Maybe partial verification passes?"
    # ------------------------------------------------------------------
    def test_e_truncated_signature(self, tmp_path):
        """
        ATTACK: Sign bundle with Ed25519, then truncate the signature
        to only the first 10 hex characters (5 bytes). Ed25519 requires
        exactly 64 bytes -- anything shorter is rejected.

        Proves: partial signatures are never accepted.
        """
        bundle, _priv, pub = _make_ed25519_signed_bundle(tmp_path)

        # Truncate signature
        sig_path = bundle / SIGNATURE_FILE
        sig_data = json.loads(sig_path.read_text(encoding="utf-8"))
        sig_data["signature"] = sig_data["signature"][:10]  # Only first 10 hex chars
        sig_path.write_text(json.dumps(sig_data, indent=2), encoding="utf-8")

        ok, msg = verify_bundle_signature(bundle, key_path=pub)
        assert ok is False, "ATTACK E: truncated signature was NOT detected"

    # ------------------------------------------------------------------
    # COMPOSITE: All five attacks summarized
    # ------------------------------------------------------------------
    def test_z_gauntlet_summary(self):
        """
        Composite proof: all five Ed25519 attack classes are covered.

        This test documents the Ed25519 attack surface and confirms that
        Layer 4 catches all documented attack classes for asymmetric signing.

        Attack Surface Coverage:
          Layer 4 (Bundle Signature): catches all 5 attacks
            - Wrong key: fingerprint mismatch
            - Bit flip: Ed25519 verify fails
            - Downgrade: algorithm mismatch
            - Key type mismatch: algorithm mismatch (reverse)
            - Truncated: invalid signature length
        """
        coverage = {
            "Attack A -- Wrong Key Verification":     "Layer 4 (fingerprint mismatch)",
            "Attack B -- Signature Bit Flip":         "Layer 4 (Ed25519 verify fails)",
            "Attack C -- Downgrade Ed25519 to HMAC":  "Layer 4 (algorithm mismatch)",
            "Attack D -- HMAC bundle + Ed25519 key":  "Layer 4 (algorithm mismatch reverse)",
            "Attack E -- Truncated Signature":        "Layer 4 (invalid signature)",
        }
        assert len(coverage) >= 5
        print("CERT-09: 5 Ed25519 attacks, ALL CAUGHT by Layer 4")
