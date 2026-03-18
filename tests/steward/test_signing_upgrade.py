#!/usr/bin/env python3
"""
Ed25519 Signing Upgrade Tests — Phase 2, Plan 01.

Tests dual-algorithm bundle signing (Ed25519 + HMAC-SHA256 backward compatibility):
- Algorithm auto-detection from key file version field (SIGN-06)
- Ed25519 bundle signing and verification (SIGN-03, SIGN-04)
- Downgrade attack prevention (SIGN-08)
- Dual-format key loading (SIGN-06)

Existing HMAC tests in test_cert07_bundle_signing.py remain unmodified (SIGN-07).
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
    load_key,
    generate_key,
    SIGNATURE_FILE,
)
from scripts.mg_sign import _detect_algorithm  # noqa: E402
from scripts.mg_ed25519 import generate_key_files  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bundle(tmp_path: Path) -> Path:
    """Create a minimal valid bundle with pack_manifest.json. Returns bundle dir."""
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
    return bundle


def _make_ed25519_signed_bundle(tmp_path: Path):
    """
    Create a minimal bundle signed with Ed25519.

    Returns:
        (bundle_dir, key_data, key_file_path, pub_key_file_path)
    """
    bundle = _make_bundle(tmp_path)

    key_file = tmp_path / "ed25519_key.json"
    key_data = generate_key_files(key_file)

    sign_bundle(bundle, key_file)

    pub_key_file = tmp_path / "ed25519_key.pub.json"
    return bundle, key_data, key_file, pub_key_file


def _make_hmac_signed_bundle(tmp_path: Path):
    """
    Create a minimal bundle signed with HMAC.

    Returns:
        (bundle_dir, key_data, key_file_path)
    """
    bundle = _make_bundle(tmp_path)

    key_data = generate_key()
    key_file = tmp_path / "hmac_key.json"
    key_file.write_text(json.dumps(key_data, indent=2), encoding="utf-8")

    sign_bundle(bundle, key_file)

    return bundle, key_data, key_file


# ---------------------------------------------------------------------------
# TestAlgorithmDispatch (SIGN-06)
# ---------------------------------------------------------------------------

class TestAlgorithmDispatch:
    """Tests for _detect_algorithm() — key version field dispatch."""

    def test_hmac_key_detected(self):
        """HMAC key version detected correctly."""
        result = _detect_algorithm({"version": "hmac-sha256-v1", "key_hex": "aa" * 32})
        assert result == "hmac"

    def test_ed25519_key_detected(self):
        """Ed25519 key version detected correctly."""
        result = _detect_algorithm({"version": "ed25519-v1", "public_key_hex": "bb" * 32})
        assert result == "ed25519"

    def test_unknown_version_rejected(self):
        """Unknown key version raises ValueError."""
        with pytest.raises(ValueError, match="Unknown key version"):
            _detect_algorithm({"version": "unknown-v1"})


# ---------------------------------------------------------------------------
# TestEd25519BundleSigning (SIGN-03, SIGN-04)
# ---------------------------------------------------------------------------

class TestEd25519BundleSigning:
    """Tests for Ed25519 bundle signing and verification."""

    def test_sign_creates_ed25519_signature(self, tmp_path):
        """Ed25519 signing produces bundle_signature.json with version ed25519-v1."""
        bundle, key_data, key_file, _ = _make_ed25519_signed_bundle(tmp_path)

        sig_path = bundle / SIGNATURE_FILE
        assert sig_path.exists(), f"{SIGNATURE_FILE} was not created"

        sig = json.loads(sig_path.read_text(encoding="utf-8"))
        assert sig["version"] == "ed25519-v1"
        assert "signed_root_hash" in sig
        assert "signature" in sig
        assert "key_fingerprint" in sig

        # Ed25519 signature is 64 bytes = 128 hex chars
        assert len(sig["signature"]) == 128
        assert all(c in "0123456789abcdef" for c in sig["signature"])

        # Fingerprint matches key
        assert sig["key_fingerprint"] == key_data["fingerprint"]

    def test_ed25519_sign_verify_roundtrip(self, tmp_path):
        """Sign then verify with same key returns (True, msg) containing VALID."""
        bundle, _, key_file, _ = _make_ed25519_signed_bundle(tmp_path)

        ok, msg = verify_bundle_signature(bundle, key_path=key_file)
        assert ok is True, f"Expected PASS, got: {msg}"
        assert "VALID" in msg

    def test_verify_with_public_key_only(self, tmp_path):
        """Verify with .pub.json file (no private_key_hex) returns (True, msg)."""
        bundle, _, _, pub_key_file = _make_ed25519_signed_bundle(tmp_path)

        assert pub_key_file.exists(), f"Public key file not found: {pub_key_file}"

        ok, msg = verify_bundle_signature(bundle, key_path=pub_key_file)
        assert ok is True, f"Public-key-only verification failed: {msg}"
        assert "VALID" in msg

    def test_forged_ed25519_signature_fails(self, tmp_path):
        """Tampering with signature hex returns (False, msg) containing INVALID."""
        bundle, _, key_file, _ = _make_ed25519_signed_bundle(tmp_path)

        # Tamper with the signature
        sig_path = bundle / SIGNATURE_FILE
        sig_data = json.loads(sig_path.read_text(encoding="utf-8"))
        sig_data["signature"] = "f" * 128  # Forged signature
        sig_path.write_text(json.dumps(sig_data, indent=2), encoding="utf-8")

        ok, msg = verify_bundle_signature(bundle, key_path=key_file)
        assert ok is False, "Forged Ed25519 signature was NOT detected"
        assert "INVALID" in msg

    def test_wrong_ed25519_key_fails(self, tmp_path):
        """Verify with different Ed25519 key returns (False, msg)."""
        bundle, _, _, _ = _make_ed25519_signed_bundle(tmp_path)

        # Generate a different Ed25519 key
        wrong_key_file = tmp_path / "wrong_ed25519_key.json"
        generate_key_files(wrong_key_file)

        ok, msg = verify_bundle_signature(bundle, key_path=wrong_key_file)
        assert ok is False, "Wrong Ed25519 key should fail verification"
        assert "fingerprint" in msg.lower() or "mismatch" in msg.lower() or "INVALID" in msg

    def test_bundle_modified_after_ed25519_signing(self, tmp_path):
        """Modify evidence + rebuild manifest after signing returns (False, msg)."""
        bundle, _, key_file, _ = _make_ed25519_signed_bundle(tmp_path)

        # Verify passes before attack
        ok_before, _ = verify_bundle_signature(bundle, key_path=key_file)
        assert ok_before is True, "Bundle should be valid before attack"

        # ATTACK: modify evidence and rebuild manifest (sophisticated attacker)
        evidence_file = bundle / "evidence.json"
        tampered = {"claim": "ML_BENCH-01", "result": "PASS", "accuracy": 0.99}
        evidence_file.write_text(json.dumps(tampered), encoding="utf-8")

        new_sha = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
        manifest_path = bundle / "pack_manifest.json"
        mf = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in mf["files"]:
            if entry["relpath"] == "evidence.json":
                entry["sha256"] = new_sha
                entry["bytes"] = evidence_file.stat().st_size
                break
        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(mf["files"], key=lambda x: x["relpath"])
        )
        mf["root_hash"] = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        manifest_path.write_text(json.dumps(mf, indent=2), encoding="utf-8")

        ok_after, msg = verify_bundle_signature(bundle, key_path=key_file)
        assert ok_after is False, "Bundle modification was NOT detected"
        assert "modified after signing" in msg or "root_hash" in msg


# ---------------------------------------------------------------------------
# TestDowngradeAttack (SIGN-08)
# ---------------------------------------------------------------------------

class TestDowngradeAttack:
    """Tests for downgrade attack prevention."""

    def test_hmac_key_ed25519_bundle_rejected(self, tmp_path):
        """HMAC key used to verify Ed25519-signed bundle returns algorithm mismatch."""
        # Create Ed25519-signed bundle
        bundle, _, _, _ = _make_ed25519_signed_bundle(tmp_path / "ed25519_bundle")

        # Create HMAC key
        hmac_key_data = generate_key()
        hmac_key_file = tmp_path / "hmac_key.json"
        hmac_key_file.write_text(json.dumps(hmac_key_data, indent=2), encoding="utf-8")

        ok, msg = verify_bundle_signature(bundle, key_path=hmac_key_file)
        assert ok is False, "HMAC key should not verify Ed25519 bundle"
        assert "algorithm mismatch" in msg.lower()

    def test_ed25519_key_hmac_bundle_rejected(self, tmp_path):
        """Ed25519 key used to verify HMAC-signed bundle returns algorithm mismatch."""
        # Create HMAC-signed bundle
        bundle, _, _ = _make_hmac_signed_bundle(tmp_path / "hmac_bundle")

        # Create Ed25519 key
        ed25519_key_file = tmp_path / "ed25519_key.json"
        generate_key_files(ed25519_key_file)

        ok, msg = verify_bundle_signature(bundle, key_path=ed25519_key_file)
        assert ok is False, "Ed25519 key should not verify HMAC bundle"
        assert "algorithm mismatch" in msg.lower()


# ---------------------------------------------------------------------------
# TestLoadKeyDualFormat (SIGN-06)
# ---------------------------------------------------------------------------

class TestLoadKeyDualFormat:
    """Tests for load_key() supporting both HMAC and Ed25519 key formats."""

    def test_load_hmac_key(self, tmp_path):
        """load_key with HMAC key file returns dict with key_hex."""
        key_data = generate_key()
        key_file = tmp_path / "hmac_key.json"
        key_file.write_text(json.dumps(key_data, indent=2), encoding="utf-8")

        loaded = load_key(key_file)
        assert "key_hex" in loaded
        assert loaded["version"] == "hmac-sha256-v1"

    def test_load_ed25519_private_key(self, tmp_path):
        """load_key with Ed25519 private key returns dict with private_key_hex and public_key_hex."""
        key_file = tmp_path / "ed25519_key.json"
        generate_key_files(key_file)

        loaded = load_key(key_file)
        assert "private_key_hex" in loaded
        assert "public_key_hex" in loaded
        assert loaded["version"] == "ed25519-v1"

    def test_load_ed25519_public_key(self, tmp_path):
        """load_key with Ed25519 public-only key returns dict with public_key_hex and no private_key_hex."""
        key_file = tmp_path / "ed25519_key.json"
        generate_key_files(key_file)
        pub_key_file = tmp_path / "ed25519_key.pub.json"

        loaded = load_key(pub_key_file)
        assert "public_key_hex" in loaded
        assert "private_key_hex" not in loaded
        assert loaded["version"] == "ed25519-v1"

    def test_sign_with_public_only_key_fails(self, tmp_path):
        """sign_bundle with Ed25519 public-only key raises ValueError containing 'private key'."""
        bundle = _make_bundle(tmp_path)

        key_file = tmp_path / "ed25519_key.json"
        generate_key_files(key_file)
        pub_key_file = tmp_path / "ed25519_key.pub.json"

        with pytest.raises(ValueError, match="private key"):
            sign_bundle(bundle, pub_key_file)
