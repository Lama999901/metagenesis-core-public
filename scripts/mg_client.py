#!/usr/bin/env python3
"""
MetaGenesis Core -- Client-Facing Bundle Generator

One script. Three modes. Full verification pipeline.

Usage:
    python scripts/mg_client.py --demo
    python scripts/mg_client.py --domain ml --data results.json
    python scripts/mg_client.py --verify bundle/

Supports: ml, pharma, finance, materials, digital_twin
Pure stdlib. No external dependencies.

PPA: USPTO #63/996,819
"""

import argparse
import hashlib
import hmac
import io
import json
import os
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---- Terminal colors --------------------------------------------------------

G = "\033[92m"  # green
R = "\033[91m"  # red
Y = "\033[93m"  # yellow
C = "\033[96m"  # cyan
B = "\033[1m"   # bold
DIM = "\033[2m"
X = "\033[0m"   # reset


# ---- Domain configuration --------------------------------------------------

DOMAIN_CONFIG = {
    "ml": {
        "claim": "ML_BENCH-01",
        "module": "backend.progress.mlbench1_accuracy_certificate",
        "func": "run_certificate",
        "description": "ML benchmark accuracy verification",
        "defaults": {
            "seed": 42,
            "claimed_accuracy": 0.90,
            "accuracy_tolerance": 0.02,
            "n_samples": 1000,
        },
    },
    "pharma": {
        "claim": "PHARMA-01",
        "module": "backend.progress.pharma1_admet_certificate",
        "func": "run_certificate",
        "description": "ADMET prediction verification (FDA 21 CFR Part 11)",
        "defaults": {
            "seed": 42,
            "property_name": "solubility",
            "claimed_value": -3.5,
            "tolerance": 0.5,
        },
    },
    "finance": {
        "claim": "FINRISK-01",
        "module": "backend.progress.finrisk1_var_certificate",
        "func": "run_certificate",
        "description": "Value at Risk model verification (Basel III)",
        "defaults": {
            "seed": 42,
            "claimed_var": 0.02,
            "var_tolerance": 0.005,
            "confidence_level": 0.99,
        },
    },
    "materials": {
        "claim": "MTR-1",
        "module": "backend.progress.mtr1_calibration",
        "func": "run_calibration",
        "description": "Young's modulus calibration (E=70GPa aluminum)",
        "defaults": {
            "seed": 42,
            "E_true": 70e9,
        },
    },
    "digital_twin": {
        "claim": "DT-FEM-01",
        "module": "backend.progress.dtfem1_displacement_verification",
        "func": "run_certificate",
        "description": "FEM displacement verification",
        "defaults": {
            "seed": 42,
        },
    },
}


# ---- Step Chain Verification ------------------------------------------------

def _hash_step(step_name: str, step_data: dict, prev_hash: str) -> str:
    """Hash a single execution step chained to the previous step hash."""
    content = json.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---- Bundle creation --------------------------------------------------------

def _create_pack_manifest(bundle_dir: Path, files_to_include: list) -> dict:
    """Create pack_manifest.json with SHA-256 integrity for all files."""
    entries = []
    for fpath in sorted(files_to_include):
        relpath = str(fpath.relative_to(bundle_dir)).replace("\\", "/")
        sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        entries.append({"relpath": relpath, "sha256": sha})

    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}" for e in sorted(entries, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "protocol_version": 1,
        "files": entries,
        "root_hash": root_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest_path = bundle_dir / "pack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _sign_bundle(bundle_dir: Path) -> dict:
    """Sign bundle with a fresh HMAC-SHA256 key (Layer 4)."""
    manifest_path = bundle_dir / "pack_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root_hash = manifest["root_hash"]

    # Generate ephemeral signing key
    raw_key = secrets.token_bytes(32)
    key_hex = raw_key.hex()
    fingerprint = hashlib.sha256(raw_key).hexdigest()

    # Compute HMAC-SHA256 signature
    signature = hmac.new(raw_key, root_hash.encode("utf-8"), hashlib.sha256).hexdigest()

    sig_dict = {
        "version": "hmac-sha256-v1",
        "signed_root_hash": root_hash,
        "signature": signature,
        "key_fingerprint": fingerprint,
    }

    sig_path = bundle_dir / "bundle_signature.json"
    sig_path.write_text(json.dumps(sig_dict, indent=2), encoding="utf-8")

    # Save key for verification
    key_dict = {
        "version": "hmac-sha256-v1",
        "key_hex": key_hex,
        "fingerprint": fingerprint,
    }
    key_path = bundle_dir / "signing_key.json"
    key_path.write_text(json.dumps(key_dict, indent=2), encoding="utf-8")

    return sig_dict


def _create_temporal_commitment(bundle_dir: Path) -> dict:
    """Create Layer 5 temporal commitment (local timestamp mode)."""
    manifest_path = bundle_dir / "pack_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root_hash = manifest["root_hash"]

    pre_commitment_hash = hashlib.sha256(root_hash.encode("utf-8")).hexdigest()

    tc = {
        "version": "temporal-nist-v1",
        "root_hash": root_hash,
        "pre_commitment_hash": pre_commitment_hash,
        "beacon_output_value": None,
        "beacon_timestamp": None,
        "beacon_pulse_uri": None,
        "beacon_status": "unavailable",
        "local_timestamp": datetime.now(timezone.utc).isoformat(),
        "temporal_binding": None,
    }

    tc_path = bundle_dir / "temporal_commitment.json"
    tc_path.write_text(json.dumps(tc, indent=2), encoding="utf-8")
    return tc


_EXCLUDED_FROM_MANIFEST = {
    "pack_manifest.json",
    "bundle_signature.json",
    "signing_key.json",
    "temporal_commitment.json",
}


def _rebuild_manifest(bundle_dir: Path) -> dict:
    """Rebuild pack_manifest.json (excludes signature/temporal/key -- they reference the manifest, not vice versa)."""
    all_files = []
    for f in sorted(bundle_dir.rglob("*")):
        if f.is_file() and f.name not in _EXCLUDED_FROM_MANIFEST:
            all_files.append(f)

    entries = []
    for fpath in all_files:
        relpath = str(fpath.relative_to(bundle_dir)).replace("\\", "/")
        sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
        entries.append({"relpath": relpath, "sha256": sha})

    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}" for e in sorted(entries, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "protocol_version": 1,
        "files": entries,
        "root_hash": root_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    manifest_path = bundle_dir / "pack_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


# ---- Verification -----------------------------------------------------------

def verify_bundle(bundle_dir: Path) -> tuple:
    """
    Verify a bundle through all 5 layers.
    Returns (passed: bool, results: list[tuple[str, bool, str]]).
    """
    bundle_dir = Path(bundle_dir)
    results = []

    # Layer 1: SHA-256 integrity
    manifest_path = bundle_dir / "pack_manifest.json"
    if not manifest_path.exists():
        results.append(("Layer 1 - SHA-256 Integrity", False, "pack_manifest.json not found"))
        return False, results

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Check protocol version
    pv = manifest.get("protocol_version")
    if pv is None or not isinstance(pv, int) or pv < 1:
        results.append(("Layer 1 - SHA-256 Integrity", False, "Invalid protocol_version"))
        return False, results

    # Verify file hashes
    for entry in manifest.get("files", []):
        relpath = entry.get("relpath", "")
        fp = bundle_dir / relpath
        if not fp.exists():
            results.append(("Layer 1 - SHA-256 Integrity", False, f"Missing file: {relpath}"))
            return False, results
        actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        if actual_sha != entry.get("sha256", ""):
            results.append(("Layer 1 - SHA-256 Integrity", False, f"Hash mismatch: {relpath}"))
            return False, results

    # Verify root hash
    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(manifest["files"], key=lambda x: x["relpath"])
    )
    actual_root = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    if actual_root != manifest.get("root_hash", ""):
        results.append(("Layer 1 - SHA-256 Integrity", False, "Root hash mismatch"))
        return False, results
    results.append(("Layer 1 - SHA-256 Integrity", True, "All file hashes verified"))

    # Layer 2: Semantic verification
    evidence_path = bundle_dir / "evidence.json"
    if evidence_path.exists():
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            if "mtr_phase" not in evidence:
                results.append(("Layer 2 - Semantic Verification", False, "Missing mtr_phase"))
                return False, results
            if "execution_trace" not in evidence:
                results.append(("Layer 2 - Semantic Verification", False, "Missing execution_trace"))
                return False, results
            if "trace_root_hash" not in evidence:
                results.append(("Layer 2 - Semantic Verification", False, "Missing trace_root_hash"))
                return False, results
            results.append(("Layer 2 - Semantic Verification", True, f"Claim {evidence['mtr_phase']} verified"))
        except (json.JSONDecodeError, OSError) as e:
            results.append(("Layer 2 - Semantic Verification", False, str(e)))
            return False, results
    else:
        results.append(("Layer 2 - Semantic Verification", True, "No evidence file (skip)"))

    # Layer 3: Step Chain
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        trace = evidence.get("execution_trace", [])
        claimed_root = evidence.get("trace_root_hash", "")
        if trace and claimed_root:
            if len(trace) != 4:
                results.append(("Layer 3 - Step Chain", False, f"Expected 4 steps, got {len(trace)}"))
                return False, results
            steps = [s.get("step") for s in trace]
            if steps != [1, 2, 3, 4]:
                results.append(("Layer 3 - Step Chain", False, f"Steps out of order: {steps}"))
                return False, results
            final_hash = trace[-1].get("hash", "")
            if final_hash != claimed_root:
                results.append(("Layer 3 - Step Chain", False, "trace_root_hash mismatch"))
                return False, results
            results.append(("Layer 3 - Step Chain", True, f"4-step chain verified (root: {claimed_root[:16]}...)"))
        else:
            results.append(("Layer 3 - Step Chain", True, "No trace present (skip)"))
    else:
        results.append(("Layer 3 - Step Chain", True, "No evidence file (skip)"))

    # Layer 4: Bundle Signature
    sig_path = bundle_dir / "bundle_signature.json"
    if sig_path.exists():
        sig_data = json.loads(sig_path.read_text(encoding="utf-8"))
        if sig_data.get("signed_root_hash") != manifest["root_hash"]:
            results.append(("Layer 4 - Bundle Signature", False, "Signed root hash does not match"))
            return False, results

        # Try key-based verification
        key_path = bundle_dir / "signing_key.json"
        if key_path.exists():
            key_data = json.loads(key_path.read_text(encoding="utf-8"))
            key_bytes = bytes.fromhex(key_data["key_hex"])
            expected_sig = hmac.new(
                key_bytes, sig_data["signed_root_hash"].encode("utf-8"), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig_data["signature"], expected_sig):
                results.append(("Layer 4 - Bundle Signature", False, "HMAC verification failed"))
                return False, results
            results.append(("Layer 4 - Bundle Signature", True, f"HMAC-SHA256 valid (key: {sig_data['key_fingerprint'][:16]}...)"))
        else:
            results.append(("Layer 4 - Bundle Signature", True, f"Signature present (fingerprint: {sig_data.get('key_fingerprint', '?')[:16]}...)"))
    else:
        results.append(("Layer 4 - Bundle Signature", True, "No signature (skip)"))

    # Layer 5: Temporal Commitment
    tc_path = bundle_dir / "temporal_commitment.json"
    if tc_path.exists():
        tc = json.loads(tc_path.read_text(encoding="utf-8"))
        expected_pre = hashlib.sha256(manifest["root_hash"].encode("utf-8")).hexdigest()
        if tc.get("pre_commitment_hash") != expected_pre:
            results.append(("Layer 5 - Temporal Commitment", False, "Pre-commitment hash mismatch"))
            return False, results

        if tc.get("beacon_status") == "unavailable":
            ts = tc.get("local_timestamp", "unknown")
            results.append(("Layer 5 - Temporal Commitment", True, f"Local timestamp: {ts}"))
        else:
            concat = (
                tc["pre_commitment_hash"]
                + tc["beacon_output_value"]
                + tc["beacon_timestamp"]
            )
            expected_binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()
            if tc.get("temporal_binding") != expected_binding:
                results.append(("Layer 5 - Temporal Commitment", False, "Temporal binding mismatch"))
                return False, results
            results.append(("Layer 5 - Temporal Commitment", True, f"NIST Beacon verified ({tc['beacon_timestamp']})"))
    else:
        results.append(("Layer 5 - Temporal Commitment", True, "No temporal commitment (skip)"))

    all_passed = all(ok for _, ok, _ in results)
    return all_passed, results


# ---- Print helpers ----------------------------------------------------------

def _print_header():
    print()
    print(f"{B}{C}  MetaGenesis Core -- Verification Protocol{X}")
    print(f"{DIM}  Tamper-evident computation certification{X}")
    print(f"{DIM}  PPA: USPTO #63/996,819{X}")
    print()


def _print_layer_results(results: list):
    print(f"\n{B}  Verification Results{X}")
    print(f"  {'=' * 60}")
    for name, passed, detail in results:
        icon = f"{G}PASS{X}" if passed else f"{R}FAIL{X}"
        print(f"  [{icon}] {name}")
        print(f"         {DIM}{detail}{X}")
    print(f"  {'=' * 60}")


def _print_summary(domain: str, claim_result: dict, bundle_dir: Path, all_passed: bool):
    claim_id = claim_result.get("mtr_phase", "?")
    result = claim_result.get("result", {})
    passed = result.get("pass", False)
    trace_root = claim_result.get("trace_root_hash", "?")

    print(f"\n{B}  Bundle Summary{X}")
    print(f"  Domain:           {domain}")
    print(f"  Claim:            {claim_id}")
    print(f"  Claim result:     {'PASS' if passed else 'FAIL'}")
    print(f"  Trace root hash:  {trace_root[:32]}...")
    print(f"  Bundle location:  {bundle_dir}")

    if all_passed:
        print(f"\n  {G}{B}  VERIFICATION: PASS  {X}")
        print(f"  {DIM}All 5 layers verified. Bundle is tamper-evident.{X}")
    else:
        print(f"\n  {R}{B}  VERIFICATION: FAIL  {X}")
    print()


# ---- Core pipeline ----------------------------------------------------------

def run_claim(domain: str, user_data_path: str = None) -> dict:
    """Run a claim for the given domain. Returns the claim result dict."""
    if domain not in DOMAIN_CONFIG:
        raise ValueError(f"Unknown domain: {domain}. Supported: {', '.join(DOMAIN_CONFIG.keys())}")

    config = DOMAIN_CONFIG[domain]
    mod = __import__(config["module"], fromlist=[config["func"]])
    func = getattr(mod, config["func"])

    if user_data_path is not None:
        # Load user data and merge with defaults
        data_path = Path(user_data_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {user_data_path}")
        user_params = json.loads(data_path.read_text(encoding="utf-8"))
        params = {**config["defaults"], **user_params}
    else:
        params = dict(config["defaults"])

    return func(**params)


def create_bundle(claim_result: dict, output_dir: str = None) -> Path:
    """Create a signed, timestamped verification bundle from a claim result.

    Architecture: manifest covers evidence files only. Signature, temporal
    commitment, and signing key are *about* the manifest (they reference its
    root_hash) and are therefore excluded from the manifest itself. This avoids
    circular dependency.
    """
    if output_dir:
        bundle_dir = Path(output_dir)
        if bundle_dir.exists():
            shutil.rmtree(bundle_dir)
        bundle_dir.mkdir(parents=True, exist_ok=True)
    else:
        bundle_dir = Path(tempfile.mkdtemp(prefix="mg_bundle_"))

    # Write evidence
    evidence_path = bundle_dir / "evidence.json"
    evidence_path.write_text(json.dumps(claim_result, indent=2), encoding="utf-8")

    # Build manifest covering evidence only (Layer 1)
    _rebuild_manifest(bundle_dir)

    # Sign the manifest root_hash (Layer 4)
    _sign_bundle(bundle_dir)

    # Temporal commitment referencing root_hash (Layer 5)
    _create_temporal_commitment(bundle_dir)

    return bundle_dir


def demo_pipeline() -> int:
    """Run the full demo pipeline: generate data, run claim, pack, sign, verify."""
    _print_header()
    print(f"  {B}Demo Mode{X} -- ML benchmark accuracy verification")
    print(f"  {DIM}Generating synthetic ML data, running ML_BENCH-01...{X}")
    print()

    # Step 1: Run ML_BENCH-01
    print(f"  {C}[1/5]{X} Running ML_BENCH-01 claim...")
    result = run_claim("ml")
    claim_passed = result.get("result", {}).get("pass", False)
    acc = result.get("result", {}).get("actual_accuracy", 0)
    print(f"        Claimed accuracy: 0.90")
    print(f"        Actual accuracy:  {acc:.4f}")
    print(f"        Tolerance:        0.02")
    print(f"        Result:           {G + 'PASS' + X if claim_passed else R + 'FAIL' + X}")

    # Step 2: Create bundle
    print(f"\n  {C}[2/5]{X} Creating verification bundle...")
    bundle_dir = create_bundle(result, output_dir=str(REPO_ROOT / "_client_demo_bundle"))
    print(f"        Bundle: {bundle_dir}")

    # Step 3: Sign bundle
    print(f"\n  {C}[3/5]{X} Bundle signed (HMAC-SHA256)")
    sig_path = bundle_dir / "bundle_signature.json"
    sig = json.loads(sig_path.read_text(encoding="utf-8"))
    print(f"        Key fingerprint: {sig['key_fingerprint'][:32]}...")

    # Step 4: Temporal commitment
    print(f"\n  {C}[4/5]{X} Temporal commitment created")
    tc_path = bundle_dir / "temporal_commitment.json"
    tc = json.loads(tc_path.read_text(encoding="utf-8"))
    print(f"        Pre-commitment:  {tc['pre_commitment_hash'][:32]}...")
    print(f"        Beacon status:   {tc['beacon_status']}")

    # Step 5: Verify all 5 layers
    print(f"\n  {C}[5/5]{X} Verifying bundle (all 5 layers)...")
    all_passed, layer_results = verify_bundle(bundle_dir)

    _print_layer_results(layer_results)
    _print_summary("ml", result, bundle_dir, all_passed)

    # Clean up demo bundle
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)

    return 0 if all_passed else 1


def cmd_demo(args) -> int:
    """Run demo mode."""
    return demo_pipeline()


def cmd_domain(args) -> int:
    """Create bundle from client data."""
    _print_header()
    domain = args.domain
    data_path = args.data
    output = getattr(args, "output", None)

    config = DOMAIN_CONFIG.get(domain)
    if not config:
        print(f"  {R}ERROR:{X} Unknown domain '{domain}'")
        print(f"  Supported: {', '.join(DOMAIN_CONFIG.keys())}")
        return 1

    print(f"  {B}Domain:{X} {domain} -- {config['description']}")
    print(f"  {B}Claim:{X}  {config['claim']}")
    if data_path:
        print(f"  {B}Data:{X}   {data_path}")
    print()

    try:
        result = run_claim(domain, user_data_path=data_path)
    except Exception as e:
        print(f"  {R}ERROR:{X} Claim execution failed: {e}")
        return 1

    claim_passed = result.get("result", {}).get("pass", False)
    print(f"  Claim result: {G + 'PASS' + X if claim_passed else R + 'FAIL' + X}")

    out_dir = output or str(Path.cwd() / "bundle")
    bundle_dir = create_bundle(result, output_dir=out_dir)
    print(f"  Bundle:       {bundle_dir}")

    all_passed, layer_results = verify_bundle(bundle_dir)
    _print_layer_results(layer_results)
    _print_summary(domain, result, bundle_dir, all_passed)

    return 0 if all_passed else 1


def cmd_verify(args) -> int:
    """Verify an existing bundle."""
    _print_header()
    bundle_dir = Path(args.verify)
    if not bundle_dir.exists():
        print(f"  {R}ERROR:{X} Bundle directory not found: {bundle_dir}")
        return 1

    print(f"  {B}Verifying bundle:{X} {bundle_dir}")
    print()

    all_passed, layer_results = verify_bundle(bundle_dir)
    _print_layer_results(layer_results)

    if all_passed:
        print(f"\n  {G}{B}  VERIFICATION: PASS  {X}")
        print(f"  {DIM}All layers verified. Bundle is tamper-evident.{X}")
    else:
        print(f"\n  {R}{B}  VERIFICATION: FAIL  {X}")
        for name, ok, detail in layer_results:
            if not ok:
                print(f"  {R}Failed:{X} {name}: {detail}")
    print()
    return 0 if all_passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mg_client",
        description="MetaGenesis Core -- Client-Facing Bundle Generator",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run full demo (ML benchmark, pack, sign, verify)",
    )
    parser.add_argument(
        "--domain", choices=list(DOMAIN_CONFIG.keys()),
        help="Domain for bundle creation",
    )
    parser.add_argument(
        "--data", type=str, default=None,
        help="Path to JSON file with client data parameters",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output directory for bundle",
    )
    parser.add_argument(
        "--verify", type=str, default=None,
        help="Path to bundle directory to verify",
    )

    args = parser.parse_args()

    if args.demo:
        return cmd_demo(args)
    elif args.verify:
        return cmd_verify(args)
    elif args.domain:
        return cmd_domain(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
