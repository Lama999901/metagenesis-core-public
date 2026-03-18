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

# Allow direct invocation from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SIGNATURE_FILE = "bundle_signature.json"
SIGNATURE_VERSION = "hmac-sha256-v1"
KEY_VERSION = "hmac-sha256-v1"


# ---------------------------------------------------------------------------
# Algorithm detection
# ---------------------------------------------------------------------------

def _detect_algorithm(key_data: dict) -> str:
    """Detect signing algorithm from key file version field."""
    version = key_data.get("version", "")
    if version == "hmac-sha256-v1":
        return "hmac"
    elif version == "ed25519-v1":
        return "ed25519"
    else:
        raise ValueError(f"Unknown key version: {version!r}")


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
    """Load signing key from JSON file. Supports HMAC and Ed25519 formats."""
    try:
        data = json.loads(Path(key_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Cannot load key from {key_path}: {e}")
    version = data.get("version", "")
    if version == "hmac-sha256-v1":
        if "key_hex" not in data:
            raise ValueError(f"HMAC key file missing 'key_hex': {key_path}")
    elif version == "ed25519-v1":
        if "public_key_hex" not in data:
            raise ValueError(f"Ed25519 key file missing 'public_key_hex': {key_path}")
    else:
        raise ValueError(f"Unknown key version {version!r} in {key_path}")
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


def _compute_ed25519_signature(root_hash: str, key_data: dict) -> str:
    """Compute Ed25519 signature over root_hash."""
    from scripts.mg_ed25519 import sign as ed25519_sign
    private_seed = bytes.fromhex(key_data["private_key_hex"])
    message = root_hash.encode("utf-8")
    sig_bytes = ed25519_sign(private_seed, message)
    return sig_bytes.hex()


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
    algo = _detect_algorithm(key_data)

    if algo == "hmac":
        signature = _compute_signature(root_hash, key_data["key_hex"])
        sig_version = SIGNATURE_VERSION  # "hmac-sha256-v1"
    elif algo == "ed25519":
        if "private_key_hex" not in key_data:
            raise ValueError(
                "Ed25519 signing requires a private key file "
                "(not a public-only .pub.json)"
            )
        signature = _compute_ed25519_signature(root_hash, key_data)
        sig_version = "ed25519-v1"
    else:
        raise ValueError(f"Unsupported algorithm: {algo}")

    fingerprint = key_data["fingerprint"]

    sig_dict = {
        "version": sig_version,
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

    # --- Check 3: Cryptographic verification (if key provided) ---
    if key_path is not None:
        key_data = load_key(key_path)

        # Downgrade attack prevention (SIGN-08)
        key_algo = _detect_algorithm(key_data)
        sig_version = sig_data["version"]
        expected_algo_map = {"hmac-sha256-v1": "hmac", "ed25519-v1": "ed25519"}
        sig_algo = expected_algo_map.get(sig_version)

        if sig_algo is None:
            return False, f"Unknown signature algorithm: {sig_version!r}"

        if key_algo != sig_algo:
            return False, (
                f"SIGNATURE INVALID: algorithm mismatch.\n"
                f"  bundle signed with: {sig_version}\n"
                f"  verifier key type:  {key_data['version']}\n"
                f"  This may indicate a downgrade attack."
            )

        # Verify key fingerprint matches
        if key_data["fingerprint"] != sig_data["key_fingerprint"]:
            return False, (
                "SIGNATURE INVALID: key fingerprint mismatch.\n"
                f"  bundle was signed with key fingerprint: {sig_data['key_fingerprint']}\n"
                f"  provided key fingerprint:               {key_data['fingerprint']}"
            )

        # Algorithm-dispatched verification
        if key_algo == "hmac":
            expected_sig = _compute_signature(
                sig_data["signed_root_hash"], key_data["key_hex"]
            )
            if not hmac.compare_digest(sig_data["signature"], expected_sig):
                return False, (
                    "SIGNATURE INVALID: HMAC verification failed.\n"
                    "The signature does not match the bundle content + key."
                )
        elif key_algo == "ed25519":
            from scripts.mg_ed25519 import verify as ed25519_verify
            pub_key = bytes.fromhex(key_data["public_key_hex"])
            msg = sig_data["signed_root_hash"].encode("utf-8")
            sig_bytes = bytes.fromhex(sig_data["signature"])
            if not ed25519_verify(pub_key, msg, sig_bytes):
                return False, (
                    "SIGNATURE INVALID: Ed25519 verification failed.\n"
                    "The signature does not match the bundle content + public key."
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
    key_type = getattr(args, 'type', 'hmac')
    if key_type == 'ed25519':
        from scripts.mg_ed25519 import generate_key_files
        out_path = Path(args.out)
        key_data = generate_key_files(out_path)
        stem = out_path.stem
        pub_path = out_path.parent / f"{stem}.pub.json"
        print(f"Ed25519 signing key: {out_path}")
        print(f"Public key:          {pub_path}")
        print(f"Fingerprint:         {key_data['fingerprint']}")
        print(f"KEEP {out_path} SECRET. Share {pub_path} with auditors.")
    else:
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
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Auto-create temporal commitment (Layer 5)
    try:
        from scripts.mg_temporal import create_temporal_commitment, write_temporal_commitment
        temporal = create_temporal_commitment(sig["signed_root_hash"])
        write_temporal_commitment(Path(args.pack), temporal)
        if temporal["beacon_status"] == "available":
            print(f"  temporal:        beacon-backed ({temporal['beacon_timestamp']})")
        else:
            print(f"  temporal:        local timestamp only", file=sys.stderr)
            print(f"WARNING: NIST Beacon unreachable -- temporal commitment using local timestamp only", file=sys.stderr)
            if getattr(args, 'strict', False):
                print("ERROR: --strict mode requires beacon availability", file=sys.stderr)
                return 1
    except Exception as e:
        print(f"WARNING: Temporal commitment failed: {e}", file=sys.stderr)
        if getattr(args, 'strict', False):
            return 1
    return 0


def cmd_temporal(args):
    """Create temporal commitment for a signed bundle."""
    pack_dir = Path(args.pack)
    manifest_path = pack_dir / "pack_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: pack_manifest.json not found in {pack_dir}", file=sys.stderr)
        return 1
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        root_hash = manifest.get("root_hash", "")
        if not root_hash:
            print("ERROR: pack_manifest.json missing root_hash", file=sys.stderr)
            return 1
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: Cannot read pack_manifest.json: {e}", file=sys.stderr)
        return 1

    from scripts.mg_temporal import create_temporal_commitment, write_temporal_commitment
    print(f"Pre-commitment: {hashlib.sha256(root_hash.encode('utf-8')).hexdigest()}")
    print("Fetching beacon...")
    temporal = create_temporal_commitment(root_hash)
    tc_path = write_temporal_commitment(pack_dir, temporal)

    if temporal["beacon_status"] == "available":
        print(f"Temporal commitment: {temporal['temporal_binding']}")
        print(f"  beacon_timestamp: {temporal['beacon_timestamp']}")
        print(f"  file: {tc_path}")
    else:
        print(f"WARNING: NIST Beacon unreachable -- temporal commitment using local timestamp only", file=sys.stderr)
        print(f"  local_timestamp: {temporal['local_timestamp']}")
        print(f"  file: {tc_path}")
        if args.strict:
            print("ERROR: --strict mode requires beacon availability", file=sys.stderr)
            return 1
    return 0


def cmd_verify(args):
    key_path = getattr(args, "key", None)
    fingerprint = getattr(args, "fingerprint", None)
    ok, msg = verify_bundle_signature(
        Path(args.pack),
        key_path=Path(key_path) if key_path else None,
        expected_fingerprint=fingerprint,
    )
    print(msg)
    if not ok:
        return 1

    # Layer 5: Temporal commitment check
    try:
        from scripts.mg_temporal import verify_temporal_commitment
        tc_ok, tc_msg = verify_temporal_commitment(Path(args.pack))
        print(f"  {tc_msg}")
        if not tc_ok:
            return 1
    except Exception as e:
        print(f"  Temporal: check failed ({e})")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="MetaGenesis Core — Bundle Signing (Innovation #6)"
    )
    sub = ap.add_subparsers(dest="command", required=True)

    # keygen
    kg = sub.add_parser("keygen", help="Generate a new signing key pair")
    kg.add_argument("--out", "-o", required=True, help="Output key file path (.json)")
    kg.add_argument("--type", "-t", choices=["hmac", "ed25519"],
                    default="hmac", help="Key type (default: hmac)")
    kg.set_defaults(func=cmd_keygen)

    # sign
    sg = sub.add_parser("sign", help="Sign a bundle")
    sg.add_argument("--pack", "-p", required=True, help="Bundle directory to sign")
    sg.add_argument("--key", "-k", required=True, help="Signing key file (.json)")
    sg.add_argument("--strict", action="store_true", default=False,
                    help="Fail if NIST Beacon is unreachable (for CI pipelines)")
    sg.set_defaults(func=cmd_sign)

    # verify
    vr = sub.add_parser("verify", help="Verify a bundle signature")
    vr.add_argument("--pack", "-p", required=True, help="Bundle directory to verify")
    vr.add_argument("--key", "-k", default=None, help="Signing key file (full HMAC verify)")
    vr.add_argument("--fingerprint", "-f", default=None, help="Key fingerprint (presence check)")
    vr.set_defaults(func=cmd_verify)

    # temporal
    tp = sub.add_parser("temporal", help="Create standalone temporal commitment")
    tp.add_argument("--pack", "-p", required=True, help="Bundle directory")
    tp.add_argument("--strict", action="store_true", default=False,
                    help="Fail if NIST Beacon is unreachable")
    tp.set_defaults(func=cmd_temporal)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
