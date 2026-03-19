#!/usr/bin/env python3
"""
CERT-ADV-SIGN-INTEGRITY: Layer 1 + Layer 4 File Mod + Wrong Key Signing.

Tests that:
  1. Modifying evidence + updating manifest (L1 bypass) is caught by L4 (signature mismatch)
  2. Re-signing with wrong key fails verification
  3. Unsigned bundle after content modification shows as unsigned
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
    SIGNATURE_FILE,
)
from scripts.mg_ed25519 import generate_key_files  # noqa: E402


def _make_signed_bundle(tmp_path, key_name="test_key"):
    """Create a minimal valid signed bundle. Returns (bundle, priv_key, pub_key)."""
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)

    evidence_file = bundle / "evidence.json"
    evidence_file.write_text(
        json.dumps({"claim": "ML_BENCH-01", "result": "PASS", "accuracy": 0.95}),
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
        json.dumps(manifest, indent=2), encoding="utf-8")

    priv_key = tmp_path / f"{key_name}.json"
    generate_key_files(priv_key)
    pub_key = tmp_path / f"{key_name}.pub.json"
    sign_bundle(bundle, priv_key)

    return bundle, priv_key, pub_key


def _rebuild_manifest(bundle):
    """Rebuild pack_manifest.json with correct hashes for all files."""
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
    manifest = {"version": "v1", "files": files_list, "root_hash": root_hash}
    (bundle / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return root_hash


class TestCertAdvSignIntegrity:
    """Layer 1 + Layer 4 combined attack tests."""

    def test_modify_evidence_bypass_l1_caught_by_l4(self, tmp_path):
        """
        Modify evidence content, update manifest SHA-256 + root_hash
        (bypasses L1), assert signature verification fails (L4 catches).
        """
        bundle, priv, pub = _make_signed_bundle(tmp_path)

        # ATTACK: Modify evidence content
        ev_path = bundle / "evidence.json"
        ev_path.write_text(
            json.dumps({"claim": "ML_BENCH-01", "result": "PASS", "accuracy": 0.99}),
            encoding="utf-8",
        )

        # Update manifest to bypass L1
        _rebuild_manifest(bundle)

        # L4: Signature no longer matches (signed_root_hash is old)
        ok, msg = verify_bundle_signature(bundle, key_path=pub)
        assert ok is False, f"L4 should catch modified bundle: {msg}"
        assert "modified after signing" in msg, f"Expected signing error, got: {msg}"

    def test_resign_with_wrong_key(self, tmp_path):
        """
        Sign valid bundle with key_a, then re-sign with key_b.
        Verify with key_a's pubkey should fail.
        """
        bundle, priv_a, pub_a = _make_signed_bundle(tmp_path, key_name="key_a")

        # Re-sign with a different key
        priv_b = tmp_path / "key_b.json"
        generate_key_files(priv_b)
        sign_bundle(bundle, priv_b)

        # Verify with original key_a pubkey
        ok, msg = verify_bundle_signature(bundle, key_path=pub_a)
        assert ok is False, f"L4 should catch wrong key: {msg}"
        assert "fingerprint" in msg.lower() or "mismatch" in msg.lower(), \
            f"Expected fingerprint mismatch, got: {msg}"

    def test_unsigned_bundle_after_content_mod(self, tmp_path):
        """
        Modify content + update manifest, remove signature.
        L4 check should show bundle as unsigned.
        """
        bundle, priv, pub = _make_signed_bundle(tmp_path)

        # ATTACK: Modify evidence + update manifest
        ev_path = bundle / "evidence.json"
        ev_path.write_text(
            json.dumps({"claim": "ML_BENCH-01", "result": "FAIL", "accuracy": 0.10}),
            encoding="utf-8",
        )
        _rebuild_manifest(bundle)

        # Remove signature
        sig_path = bundle / SIGNATURE_FILE
        if sig_path.exists():
            sig_path.unlink()

        # L4: No signature file -> verification reports unsigned
        ok, msg = verify_bundle_signature(bundle, key_path=pub)
        assert ok is False, f"Should detect unsigned bundle: {msg}"
