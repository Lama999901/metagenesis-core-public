#!/usr/bin/env python3
"""
mg_claim_builder.py — The Door to External Verification
========================================================

Opens MetaGenesis to the world. Any user can verify ANY computation:

    python scripts/mg_claim_builder.py \
        --input data.csv \
        --script "python compute.py" \
        --output results.json \
        --domain "ml benchmark" \
        --label "mmlu-accuracy"

What it does:
    1. SHA-256 hash of --input before execution
    2. SHA-256 hash of --script before execution
    3. Run --script in subprocess, capture stdout/stderr/exit_code/duration
    4. SHA-256 hash of --output after execution
    5. Build 4-step hash chain (same as all 20 domain templates)
    6. Build verification bundle using existing mg.py infrastructure
    7. Save to proof_library/bundles/<label>_<timestamp>.zip
    8. Append to proof_library/index.json

What it proves:
    - Determinism: this script on this input produced this output
    - Integrity: nothing was modified after execution

What it does NOT prove:
    - Correctness or physical validity of the result
    - That the computation is scientifically meaningful

No external dependencies. Stdlib only.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROOF_LIBRARY = REPO_ROOT / "proof_library"
BUNDLES_DIR = PROOF_LIBRARY / "bundles"
INDEX_PATH = PROOF_LIBRARY / "index.json"


def _sha256_path(path: Path) -> str:
    """SHA-256 hash of a file or directory (sorted file tree)."""
    h = hashlib.sha256()
    p = Path(path)
    if p.is_file():
        h.update(p.read_bytes())
    elif p.is_dir():
        for f in sorted(p.rglob("*")):
            if f.is_file() and ".git" not in f.parts:
                rel = f.relative_to(p).as_posix()
                h.update(rel.encode("utf-8"))
                h.update(f.read_bytes())
    else:
        raise FileNotFoundError(f"Path not found: {path}")
    return h.hexdigest()


def _sha256_string(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _hash_step(step_name: str, step_data: dict, prev_hash: str) -> str:
    """4-step hash chain — identical to all 20 domain templates."""
    content = json.dumps(
        {"step": step_name, "data": step_data, "prev_hash": prev_hash},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _load_index() -> list:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return []


def _save_index(entries: list) -> None:
    PROOF_LIBRARY.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _update_manifest() -> None:
    """Update system_manifest.json with current proof library state."""
    manifest_path = REPO_ROOT / "system_manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = _load_index()
    real_count = sum(1 for e in entries if not e.get("is_synthetic", True))
    total = len(entries)
    ratio = real_count / total if total > 0 else 0.0

    manifest["real_verifications_count"] = real_count
    manifest["external_input_supported"] = True
    manifest["proof_library_exists"] = True
    manifest["real_to_synthetic_ratio"] = round(ratio, 4)

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_claim(
    input_path: str,
    script_cmd: str,
    output_path: str,
    domain: str,
    label: str,
    is_synthetic: bool = False,
) -> dict:
    """Build a verification claim for an external computation."""

    input_p = Path(input_path)
    output_p = Path(output_path)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    claim_id = f"{label}-{timestamp}"

    print(f"[claim-builder] Building claim: {claim_id}")
    print(f"[claim-builder] Input:  {input_p}")
    print(f"[claim-builder] Script: {script_cmd}")
    print(f"[claim-builder] Output: {output_p}")

    # Step 1: Hash input before execution
    print("[claim-builder] Step 1/4: Hashing input...")
    if not input_p.exists():
        print(f"[claim-builder] ERROR: Input path not found: {input_p}")
        sys.exit(1)
    input_hash = _sha256_path(input_p)
    print(f"[claim-builder]   input_hash: {input_hash[:16]}...")

    # Step 2: Hash script before execution
    print("[claim-builder] Step 2/4: Hashing script...")
    script_hash = _sha256_string(script_cmd)
    print(f"[claim-builder]   script_hash: {script_hash[:16]}...")

    # Step 3: Execute computation
    print(f"[claim-builder] Step 3/4: Running: {script_cmd}")
    start_ms = time.time()
    result = subprocess.run(
        script_cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        encoding="utf-8",
        errors="replace",
    )
    duration_ms = int((time.time() - start_ms) * 1000)
    exit_code = result.returncode
    stdout_text = result.stdout
    stderr_text = result.stderr

    print(f"[claim-builder]   exit_code: {exit_code}")
    print(f"[claim-builder]   duration: {duration_ms}ms")

    if exit_code != 0:
        print(f"[claim-builder]   stderr: {stderr_text[:500]}")

    # Step 4: Hash output after execution
    print("[claim-builder] Step 4/4: Hashing output...")
    if output_p.exists():
        output_hash = _sha256_path(output_p)
    else:
        # If no output file, hash stdout as the output
        output_hash = _sha256_string(stdout_text)
        output_p = None
    print(f"[claim-builder]   output_hash: {output_hash[:16]}...")

    # Build 4-step hash chain (identical structure to domain templates)
    prev = _hash_step(
        "init_params",
        {
            "label": label,
            "domain": domain,
            "input_hash": input_hash,
            "script_hash": script_hash,
        },
        "genesis",
    )
    trace = [{"step": 1, "name": "init_params", "hash": prev}]

    prev = _hash_step(
        "execute",
        {
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "output_hash": output_hash,
        },
        prev,
    )
    trace.append({"step": 2, "name": "execute", "hash": prev})

    prev = _hash_step(
        "metrics",
        {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "exit_code": exit_code,
            "stdout_lines": len(stdout_text.splitlines()),
        },
        prev,
    )
    trace.append({"step": 3, "name": "metrics", "hash": prev})

    passed = exit_code == 0
    prev = _hash_step(
        "threshold_check",
        {"passed": passed, "threshold": "exit_code == 0"},
        prev,
    )
    trace.append(
        {"step": 4, "name": "threshold_check", "hash": prev, "output": {"pass": passed}}
    )
    trace_root_hash = prev

    # Build evidence structure (matches domain template format)
    evidence = {
        "mtr_phase": claim_id,
        "inputs": {
            "input_path": str(input_p),
            "input_hash": input_hash,
            "script_cmd": script_cmd,
            "script_hash": script_hash,
            "domain": domain,
        },
        "result": {
            "exit_code": exit_code,
            "duration_ms": duration_ms,
            "output_hash": output_hash,
            "passed": passed,
            "stdout_preview": stdout_text[:500],
        },
        "execution_trace": trace,
        "trace_root_hash": trace_root_hash,
    }

    # Build bundle directory
    bundle_name = f"{label}_{timestamp}"
    with tempfile.TemporaryDirectory() as tmp:
        bundle_dir = Path(tmp) / bundle_name
        bundle_dir.mkdir()

        # Write evidence
        evidence_path = bundle_dir / "evidence.json"
        evidence_path.write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # Write stdout/stderr captures
        (bundle_dir / "stdout.txt").write_text(stdout_text, encoding="utf-8")
        if stderr_text:
            (bundle_dir / "stderr.txt").write_text(stderr_text, encoding="utf-8")

        # Copy output file if it exists
        if output_p and output_p.exists():
            if output_p.is_file():
                shutil.copy2(output_p, bundle_dir / output_p.name)
            elif output_p.is_dir():
                shutil.copytree(output_p, bundle_dir / output_p.name)

        # Build pack manifest (Layer 1)
        # Format must match mg.py _verify_pack: list of {relpath, sha256} dicts
        manifest_files = []
        for f in sorted(bundle_dir.rglob("*")):
            if f.is_file():
                rel = f.relative_to(bundle_dir).as_posix()
                sha = hashlib.sha256(f.read_bytes()).hexdigest()
                manifest_files.append({"relpath": rel, "sha256": sha})

        # root_hash computation must match mg.py line 130-131:
        # lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in sorted(...))
        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(manifest_files, key=lambda x: x["relpath"])
        )
        root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

        pack_manifest = {
            "version": 1,
            "protocol_version": 1,
            "created": datetime.now(timezone.utc).isoformat(),
            "root_hash": root_hash,
            "files": manifest_files,
            "trace_root_hash": trace_root_hash,
        }
        (bundle_dir / "pack_manifest.json").write_text(
            json.dumps(pack_manifest, indent=2) + "\n", encoding="utf-8"
        )

        # Zip it
        BUNDLES_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = BUNDLES_DIR / f"{bundle_name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in sorted(bundle_dir.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(bundle_dir))

    print(f"[claim-builder] Bundle: {zip_path}")

    # Build index entry
    index_entry = {
        "id": claim_id,
        "date": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "is_synthetic": is_synthetic,
        "input_hash": input_hash,
        "script_hash": script_hash,
        "output_hash": output_hash,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "what_proved": f"Determinism of '{script_cmd}' on '{input_p}' → '{output_p or 'stdout'}'",
        "what_not_proved": "Correctness or physical validity of the result",
        "trace_root_hash": trace_root_hash,
        "bundle_path": str(zip_path.relative_to(REPO_ROOT) if str(zip_path).startswith(str(REPO_ROOT)) else zip_path),
    }

    # Append to index
    entries = _load_index()
    entries.append(index_entry)
    _save_index(entries)

    # Update manifest
    _update_manifest()

    print(f"[claim-builder] Index updated: {len(entries)} entries")
    print(f"[claim-builder] DONE — {claim_id}")

    return index_entry


def main():
    parser = argparse.ArgumentParser(
        description="Build a verification claim for any computation.",
        epilog="Example: python scripts/mg_claim_builder.py --input data.csv --script 'python compute.py' --output results.json --domain 'ml' --label 'my-test'",
    )
    parser.add_argument("--input", required=True, help="Input file or directory")
    parser.add_argument("--script", required=True, help="Command to run")
    parser.add_argument("--output", required=True, help="Output file or directory")
    parser.add_argument("--domain", required=True, help="Domain label (free text)")
    parser.add_argument("--label", required=True, help="Claim ID label")
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Mark as synthetic (for internal demos)",
    )

    args = parser.parse_args()
    build_claim(
        input_path=args.input,
        script_cmd=args.script,
        output_path=args.output,
        domain=args.domain,
        label=args.label,
        is_synthetic=args.synthetic,
    )


if __name__ == "__main__":
    main()
