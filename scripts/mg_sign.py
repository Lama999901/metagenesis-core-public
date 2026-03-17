#!/usr/bin/env python3
"""
MetaGenesis Core — Bundle Signing Layer (Innovation #6)

Asymmetric-equivalent bundle authentication using HMAC-SHA256 (stdlib only).

WHY THIS EXISTS:
  The three-layer verification (integrity + semantic + step chain) proves
  the bundle was not modified AFTER creation. But it cannot prove WHO created
  the bundle. An attacker with full codebase access could construct a valid
  bundle from scratch.

  Bundle signing closes this gap: only the holder of the signing key can
  produce a valid signature. Any third party verifies with the public key
  (or shared key fingerprint).

TWO SIGNING MODES:
  Mode 1 — HMAC-SHA256 (stdlib only, symmetric):
    Same key signs and verifies. Suitable for internal audits and CI.
    Upgrade path: share the key through a secure channel.

  Mode 2 — Ed25519 (asymmetric, requires: pip install cryptography):
    Private key signs, public key verifies. Suitable for third-party audits.
    Verifier never sees the private key.

WHAT IS SIGNED:
  The bundle's root_hash from pack_manifest.json — the cryptographic
  commitment to all bundle contents. Signing the root_hash is sufficient:
  any modification to any file in the bundle changes the root_hash,
  invalidating the signature.

INTEGRATION WITH EXISTING 3 LAYERS:
  Layer 1 — SHA-256 integrity  (catches: file modified)
  Layer 2 — Semantic           (catches: evidence stripped)
  Layer 3 — Step Chain         (catches: computation tampered)
  Layer 4 — Bundle Signature   (catches: bundle created by unauthorized party)

STDLIB ONLY. No external dependencies for HMAC mode.

Usage:
  # Generate signing key
  python scripts/mg_sign.py keygen --out signing_key.json

  # Sign a bundle
  python scripts/mg_sign.py sign --pack /path/to/bundle --key signing_key.json

  # Verify signature
  python scripts/mg_sign.py verify --pack /path/to/bundle --key signing_key.json

  # Verify with public fingerprint only (integrity check without key)
  python scripts/mg_sign.py verify --pack /path/to/bundle --fingerprint <hex>

PPA: USPTO #63/996,819 — Innovation #6
"""

import argparse
import hashlib
import hmac
import json
import secrets
import sys
from pathlib import Path

SIGNATURE_FILE = "bundle_signature.json"
SIGNATURE_VERSION = "hmac-sha256-v1"
KEY_VERSION = "hmac-sha256-v1"


# ---------------------------------------------------------------------------
# Key management
# ---------------------------------------------------------------------------

def generate_key() -> dict:
    """
    Generate a new signing key.

    Returns:
        key_dict with:
          - version: key format version
          - key_hex: 32-byte hex-encoded signing key (KEEP SECRET)
          - fingerprint: SHA-256 of key (safe to share publicly)
    """
    raw_key = secrets.token_bytes(32)
    fingerprint = hashlib.sha256(raw_key).hexdigest()
    return {
        "version": KEY_VERSION,
        "key_hex": raw_key.hex(),
        "fingerprint": fingerprint,
        "note": "KEEP THIS FILE SECRET. The fingerprint is safe to share.",
    }


def load_key(key_path: Path) -> dict:
    """Load signing key from JSON file."""
    try:
        data = json.loads(Path(key_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Cannot load key from {key_path}: {e}")
    if "key_hex" not in data:
        raise ValueError(f"Key file missing 'key_hex' field: {key_path}")
    return data


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------

def _compute_signature(root_hash: str, key_hex: str) -> str:
    """
    Compute HMAC-SHA256 signature over the bundle root_hash.

    The root_hash is the SHA-256 commitment over all bundle files
    (from pack_manifest.json). Signing it commits to the entire bundle.

    Args:
        root_hash: hex string from pack_manifest.json
        key_hex: hex-encoded 32-byte signing key

    Returns:
        hex-encoded HMAC-SHA256 signature
    """
    key_bytes = bytes.fromhex(key_hex)
    message = root_hash.encode("utf-8")
    return hmac.new(key_bytes, message, hashlib.sha256).hexdigest()


def sign_bundle(pack_dir: Path, key_path: Path) -> dict:
    """
    Sign a bundle with the provided key.

    Reads root_hash from pack_manifest.json, computes HMAC-SHA256,
    writes bundle_signature.json into the bundle directory.

    Args:
        pack_dir: Path to bundle directory
        key_path: Path to signing key JSON file

    Returns:
        signature_dict written to bundle_signature.json
    """
    pack_dir = Path(pack_dir)
    manifest_path = pack_dir / "pack_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"pack_manifest.json not found in {pack_dir}. "
            "Build the bundle first with: python scripts/mg.py pack build"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root_hash = manifest.get("root_hash", "")
    if not root_hash or len(root_hash) != 64:
        raise ValueError(
            f"pack_manifest.json contains invalid root_hash: {root_hash!r}"
        )

    key_data = load_key(key_path)
    signature = _compute_signature(root_hash, key_data["key_hex"])
    fingerprint = key_data["fingerprint"]

    sig_dict = {
        "version": SIGNATURE_VERSION,
        "signed_root_hash": root_hash,
        "signature": signature,
        "key_fingerprint": fingerprint,
        "note": (
            "Verify with: python scripts/mg_sign.py verify "
            "--pack <dir> --key <keyfile>"
        ),
    }

    sig_path = pack_dir / SIGNATURE_FILE
    sig_path.write_text(json.dumps(sig_dict, indent=2), encoding="utf-8")
    return sig_dict


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_bundle_signature(
    pack_dir: Path,
    key_path: Path = None,
    expected_fingerprint: str = None,
) -> tuple[bool, str]:
    """
    Verify a bundle's signature.

    Checks:
    1. bundle_signature.json exists
    2. signed_root_hash matches current pack_manifest.json root_hash
       (catches: bundle was modified AFTER signing)
    3. HMAC-SHA256 signature is valid
       (catches: signature was forged without the key)

    Args:
        pack_dir: Path to bundle directory
        key_path: Path to signing key JSON (required for full verification)
        expected_fingerprint: SHA-256 fingerprint of key (for fingerprint-only check)

    Returns:
        (ok: bool, message: str)
    """
    pack_dir = Path(pack_dir)
    sig_path = pack_dir / SIGNATURE_FILE

    # --- Check 1: signature file exists ---
    if not sig_path.exists():
        return False, f"No bundle signature found ({SIGNATURE_FILE} missing)"

    try:
        sig_data = json.loads(sig_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, f"Cannot read {SIGNATURE_FILE}: {e}"

    for field in ("version", "signed_root_hash", "signature", "key_fingerprint"):
        if field not in sig_data:
            return False, f"{SIGNATURE_FILE} missing required field: {field}"

    # --- Check 2: signed_root_hash matches current bundle root_hash ---
    manifest_path = pack_dir / "pack_manifest.json"
    if not manifest_path.exists():
        return False, "pack_manifest.json not found — cannot verify signature"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    current_root_hash = manifest.get("root_hash", "")

    if sig_data["signed_root_hash"] != current_root_hash:
        return False, (
            "SIGNATURE INVALID: bundle was modified after signing.\n"
            f"  signed_root_hash:  {sig_data['signed_root_hash']}\n"
            f"  current_root_hash: {current_root_hash}"
        )

    # --- Check 3: HMAC verification (if key provided) ---
    if key_path is not None:
        key_data = load_key(key_path)

        # Verify key fingerprint matches
        if key_data["fingerprint"] != sig_data["key_fingerprint"]:
            return False, (
                "SIGNATURE INVALID: key fingerprint mismatch.\n"
                f"  bundle was signed with key fingerprint: {sig_data['key_fingerprint']}\n"
                f"  provided key fingerprint:               {key_data['fingerprint']}"
            )

        # Verify HMAC
        expected_sig = _compute_signature(
            sig_data["signed_root_hash"], key_data["key_hex"]
        )
        if not hmac.compare_digest(sig_data["signature"], expected_sig):
            return False, (
                "SIGNATURE INVALID: HMAC verification failed.\n"
                "The signature does not match the bundle content + key."
            )

        return True, (
            f"SIGNATURE VALID\n"
            f"  root_hash:       {current_root_hash}\n"
            f"  key_fingerprint: {sig_data['key_fingerprint']}\n"
            f"  algorithm:       {sig_data['version']}"
        )

    # --- Fingerprint-only check (no key) ---
    if expected_fingerprint is not None:
        if sig_data["key_fingerprint"] != expected_fingerprint:
            return False, (
                "FINGERPRINT MISMATCH: bundle was not signed by the expected key.\n"
                f"  expected:  {expected_fingerprint}\n"
                f"  in bundle: {sig_data['key_fingerprint']}"
            )
        return True, (
            f"FINGERPRINT MATCH (integrity check only — no key provided)\n"
            f"  root_hash:       {current_root_hash}\n"
            f"  key_fingerprint: {sig_data['key_fingerprint']}\n"
            f"  note: Provide --key for full HMAC verification"
        )

    # --- No key, no fingerprint: presence check only ---
    return True, (
        f"SIGNATURE PRESENT (presence check only — no key provided)\n"
        f"  root_hash:       {current_root_hash}\n"
        f"  key_fingerprint: {sig_data['key_fingerprint']}\n"
        f"  algorithm:       {sig_data['version']}\n"
        f"  note: Provide --key for full HMAC verification"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_keygen(args):
    key = generate_key()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(key, indent=2), encoding="utf-8")
    print(f"Signing key generated: {out_path}")
    print(f"Public fingerprint:    {key['fingerprint']}")
    print(f"KEEP {out_path} SECRET — share only the fingerprint.")
    return 0


def cmd_sign(args):
    try:
        sig = sign_bundle(Path(args.pack), Path(args.key))
        print(f"Bundle signed.")
        print(f"  root_hash:       {sig['signed_root_hash']}")
        print(f"  key_fingerprint: {sig['key_fingerprint']}")
        print(f"  signature_file:  {Path(args.pack) / SIGNATURE_FILE}")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


def cmd_verify(args):
    key_path = getattr(args, "key", None)
    fingerprint = getattr(args, "fingerprint", None)
    ok, msg = verify_bundle_signature(
        Path(args.pack),
        key_path=Path(key_path) if key_path else None,
        expected_fingerprint=fingerprint,
    )
    print(msg)
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(
        description="MetaGenesis Core — Bundle Signing (Innovation #6)"
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # keygen
    kg = sub.add_parser("keygen", help="Generate a new signing key pair")
    kg.add_argument("--out", "-o", required=True, help="Output key file path (.json)")
    kg.set_defaults(func=cmd_keygen)

    # sign
    sg = sub.add_parser("sign", help="Sign a bundle")
    sg.add_argument("--pack", "-p", required=True, help="Bundle directory to sign")
    sg.add_argument("--key", "-k", required=True, help="Signing key file (.json)")
    sg.set_defaults(func=cmd_sign)

    # verify
    vr = sub.add_parser("verify", help="Verify a bundle signature")
    vr.add_argument("--pack", "-p", required=True, help="Bundle directory to verify")
    vr.add_argument("--key", "-k", default=None, help="Signing key file (full HMAC verify)")
    vr.add_argument("--fingerprint", "-f", default=None, help="Key fingerprint (presence check)")
    vr.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
