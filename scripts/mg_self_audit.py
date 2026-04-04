#!/usr/bin/env python3
"""
MetaGenesis Core -- Protocol Self-Audit (Recursive Integrity Verifier)
=====================================================================
Hashes 8 core scripts with SHA-256, signs the baseline with Ed25519,
and detects tampering on subsequent runs.

Usage:
    python scripts/mg_self_audit.py              # Verify against baseline
    python scripts/mg_self_audit.py --init       # Create initial baseline
    python scripts/mg_self_audit.py --update     # Re-baseline after changes
    python scripts/mg_self_audit.py --json       # Output JSON result
"""

import argparse
import hashlib
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding (BUG 4 from CLAUDE.md)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent

# The 8 core scripts to audit
CORE_SCRIPTS = [
    "scripts/mg.py",
    "scripts/steward_audit.py",
    "scripts/agent_evolution.py",
    "scripts/check_stale_docs.py",
    "scripts/mg_ed25519.py",
    "scripts/mg_sign.py",
    "scripts/mg_client.py",
    "scripts/agent_pilot.py",
]

BASELINE_PATH = REPO_ROOT / "reports" / "core_integrity.json"
KEY_PATH = REPO_ROOT / "signing_key.json"


def _hash_file(filepath):
    """
    Hash a file with SHA-256 using canonicalized bytes (CRLF -> LF).
    Uses the same canonicalization approach as fingerprint_file from
    backend.progress.data_integrity to avoid BUG 2 (CRLF mismatch).
    """
    raw = filepath.read_bytes()
    # Canonicalize: CRLF -> LF
    canonical = raw.replace(b"\r\n", b"\n")
    digest = hashlib.sha256(canonical).hexdigest()
    return digest, len(canonical)


def _get_scripts_dict():
    """Build the scripts hash dictionary for all 8 core scripts."""
    scripts = {}
    missing = []
    for rel_path in CORE_SCRIPTS:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            missing.append(rel_path)
            continue
        digest, size = _hash_file(full_path)
        scripts[rel_path] = {"hash": digest, "size": size}
    return scripts, missing


def _sign_scripts_dict(scripts_dict):
    """
    Sign the scripts dict JSON with Ed25519 using existing infrastructure.
    Returns (signature_hex, public_key_hex).
    """
    # Import Ed25519 from existing infrastructure
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import mg_ed25519

    # Load or generate key
    if KEY_PATH.exists():
        key_data = json.loads(KEY_PATH.read_text(encoding="utf-8"))
        private_seed = bytes.fromhex(key_data["private_key_hex"])
        public_key = bytes.fromhex(key_data["public_key_hex"])
    else:
        # Generate key pair using existing infrastructure
        print("  No signing key found. Generating new Ed25519 key pair...")
        key_data = mg_ed25519.generate_key_files(KEY_PATH)
        private_seed = bytes.fromhex(key_data["private_key_hex"])
        public_key = bytes.fromhex(key_data["public_key_hex"])

    # Serialize scripts dict deterministically
    message = json.dumps(scripts_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = mg_ed25519.sign(private_seed, message)

    return signature.hex(), public_key.hex()


def _verify_signature(scripts_dict, signature_hex, public_key_hex):
    """Verify the Ed25519 signature on the scripts dict."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import mg_ed25519

    message = json.dumps(scripts_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = bytes.fromhex(signature_hex)
    public_key = bytes.fromhex(public_key_hex)

    return mg_ed25519.verify(public_key, message, signature)


def cmd_init(_args=None):
    """Create initial baseline: hash all 8 scripts, sign, save."""
    scripts, missing = _get_scripts_dict()

    if missing:
        for m in missing:
            print(f"  ALERT: Core script missing: {m}")
        print(f"SELF-AUDIT INIT FAIL -- {len(missing)} core script(s) missing")
        return 1

    signature_hex, public_key_hex = _sign_scripts_dict(scripts)

    now = datetime.now(timezone.utc).isoformat()
    baseline = {
        "version": "1.0",
        "created": now,
        "updated": now,
        "scripts": scripts,
        "signature": signature_hex,
        "public_key": public_key_hex,
    }

    BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_PATH.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    print(f"SELF-AUDIT INIT -- baseline created with {len(scripts)} scripts")
    print(f"  Baseline: {BASELINE_PATH}")
    return 0


def cmd_verify(args=None):
    """Default mode: compare current hashes against baseline."""
    json_output = args and getattr(args, "json_output", False)

    # SELF-04: Missing baseline is advisory, not a hard fail
    if not BASELINE_PATH.exists():
        msg = "SELF-AUDIT ADVISORY -- no baseline found (run --init to create)"
        if json_output:
            print(json.dumps({"status": "advisory", "message": msg}))
        else:
            print(msg)
        return 0

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

    # Validate baseline structure
    required_keys = {"version", "created", "updated", "scripts", "signature", "public_key"}
    if not required_keys.issubset(baseline.keys()):
        print("SELF-AUDIT FAIL -- baseline file has invalid structure")
        return 1

    # Verify Ed25519 signature on baseline
    if not _verify_signature(baseline["scripts"], baseline["signature"], baseline["public_key"]):
        print("SELF-AUDIT FAIL -- baseline signature invalid (possible tampering)")
        return 1

    # Compare current hashes against baseline
    scripts_now, missing_now = _get_scripts_dict()
    baseline_scripts = baseline["scripts"]

    mismatches = []
    missing_files = []

    for rel_path in CORE_SCRIPTS:
        if rel_path in missing_now:
            # File existed in baseline but is now missing
            if rel_path in baseline_scripts:
                missing_files.append(rel_path)
            continue

        if rel_path not in baseline_scripts:
            # File exists now but wasn't in baseline (shouldn't happen with fixed list)
            continue

        expected_hash = baseline_scripts[rel_path]["hash"]
        actual_hash = scripts_now[rel_path]["hash"]
        if expected_hash != actual_hash:
            mismatches.append({
                "file": rel_path,
                "expected": expected_hash,
                "found": actual_hash,
            })

    # Check for missing files
    for m in missing_now:
        if m in baseline_scripts:
            missing_files.append(m)

    if json_output:
        result = {
            "status": "PASS" if not mismatches and not missing_files else "FAIL",
            "scripts_verified": len(scripts_now),
            "mismatches": mismatches,
            "missing": missing_files,
        }
        print(json.dumps(result, indent=2))
    else:
        if mismatches:
            for mm in mismatches:
                print(f"SELF-AUDIT FAIL -- {mm['file']} hash mismatch")
                print(f"  Expected: {mm['expected']}")
                print(f"  Found: {mm['found']}")
        if missing_files:
            for mf in missing_files:
                print(f"SELF-AUDIT ALERT -- {mf} missing from filesystem")

        if not mismatches and not missing_files:
            print(f"SELF-AUDIT PASS -- all {len(scripts_now)} scripts verified")

    return 1 if mismatches or missing_files else 0


def cmd_update(_args=None):
    """Re-baseline after intentional changes. Requires confirmation."""
    if not BASELINE_PATH.exists():
        print("No existing baseline found. Use --init instead.")
        return 1

    # Show what changed
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    scripts_now, missing_now = _get_scripts_dict()

    if missing_now:
        for m in missing_now:
            print(f"  ALERT: Core script missing: {m}")

    changes = []
    for rel_path in CORE_SCRIPTS:
        if rel_path in missing_now:
            continue
        if rel_path not in baseline["scripts"]:
            changes.append(f"  NEW: {rel_path}")
            continue
        old_hash = baseline["scripts"][rel_path]["hash"]
        new_hash = scripts_now[rel_path]["hash"]
        if old_hash != new_hash:
            changes.append(f"  CHANGED: {rel_path}")

    if not changes:
        print("No changes detected. Baseline is current.")
        return 0

    print("Changes detected:")
    for c in changes:
        print(c)

    # Prompt for confirmation
    try:
        answer = input("\nRe-baseline with these changes? [y/N] ").strip().lower()
    except EOFError:
        print("No input received. Aborting update.")
        return 1

    if answer != "y":
        print("Update cancelled.")
        return 0

    # Re-baseline
    signature_hex, public_key_hex = _sign_scripts_dict(scripts_now)

    now = datetime.now(timezone.utc).isoformat()
    baseline["updated"] = now
    baseline["scripts"] = scripts_now
    baseline["signature"] = signature_hex
    baseline["public_key"] = public_key_hex

    BASELINE_PATH.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(f"SELF-AUDIT UPDATE -- baseline updated with {len(scripts_now)} scripts")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="MetaGenesis Core -- Protocol Self-Audit (Recursive Integrity Verifier)"
    )
    ap.add_argument("--init", action="store_true", help="Create initial baseline")
    ap.add_argument("--update", action="store_true", help="Re-baseline after changes")
    ap.add_argument("--json", dest="json_output", action="store_true", help="Output JSON result")

    args = ap.parse_args()

    if args.init:
        return cmd_init(args)
    elif args.update:
        return cmd_update(args)
    else:
        return cmd_verify(args)


if __name__ == "__main__":
    sys.exit(main())
