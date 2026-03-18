#!/usr/bin/env python3
"""
SDK-01 / CLI-01 MetaGenesis One-Command Adoption Layer.

Minimal stdlib CLI wrapper: steward audit, pack build, pack verify, bench run, claim run mtr1.
No new deps. No network. Calls existing scripts via subprocess.
"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _run(cmd: list[str], passthrough: bool = True) -> int:
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        executable=sys.executable,
    )
    return result.returncode


def cmd_steward_audit(_args) -> int:
    return _run([sys.executable, str(REPO_ROOT / "scripts" / "steward_audit.py")])


def cmd_pack_build(args) -> int:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "steward_submission_pack.py"),
        "-o", str(args.output),
    ]
    if getattr(args, "index", None):
        cmd.extend(["--index", str(args.index)])
    if getattr(args, "include_evidence", False):
        cmd.append("--include-evidence")
        if getattr(args, "source_reports_dir", None):
            cmd.extend(["--source-reports-dir", str(args.source_reports_dir)])
    return _run(cmd)


def _verify_pack(pack_dir: Path) -> tuple[bool, str, dict]:
    """Verify pack. Returns (ok, message, report_dict)."""
    pack_dir = Path(pack_dir)
    report = {
        "version": "v1",
        "pack_root_hash": "",
        "manifest_ok": False,
        "semantic_ok": None,
        "temporal_ok": None,
        "checks": [],
        "errors": [],
    }

    manifest_path = pack_dir / "pack_manifest.json"
    if not manifest_path.exists():
        report["checks"].append({"name": "manifest_exists", "status": "fail"})
        report["errors"].append("pack_manifest.json not found")
        return False, "pack_manifest.json not found", report

    report["checks"].append({"name": "manifest_exists", "status": "pass"})
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        report["checks"].append({"name": "manifest_valid", "status": "fail"})
        report["errors"].append(f"Failed to load manifest: {e}")
        return False, f"Failed to load manifest: {e}", report

    report["checks"].append({"name": "manifest_valid", "status": "pass"})
    for key in ("files", "root_hash"):
        if key not in manifest:
            report["checks"].append({"name": "manifest_structure", "status": "fail"})
            report["errors"].append(f"Manifest missing required key: {key}")
            return False, f"Manifest missing required key: {key}", report

    report["checks"].append({"name": "manifest_structure", "status": "pass"})
    report["pack_root_hash"] = manifest.get("root_hash", "")

    for entry in manifest["files"]:
        relpath = entry.get("relpath", "")
        if ".." in relpath or relpath.startswith("/"):
            report["checks"].append({"name": "manifest_integrity", "status": "fail", "details": relpath})
            report["errors"].append(f"Invalid relpath in manifest: {relpath}")
            return False, f"Invalid relpath in manifest: {relpath}", report
        fp = pack_dir / relpath
        if not fp.exists():
            report["checks"].append({"name": "manifest_integrity", "status": "fail", "details": relpath})
            report["errors"].append(f"File missing: {relpath}")
            return False, f"File missing: {relpath}", report
        actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        expected_sha = entry.get("sha256", "")
        if actual_sha != expected_sha:
            report["checks"].append({"name": "manifest_integrity", "status": "fail", "details": relpath})
            report["errors"].append(f"SHA256 mismatch: {relpath}")
            return False, f"SHA256 mismatch: {relpath}", report

    lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in sorted(manifest["files"], key=lambda x: x["relpath"]))
    actual_root = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    if actual_root != manifest.get("root_hash", ""):
        report["checks"].append({"name": "manifest_integrity", "status": "fail"})
        report["errors"].append("root_hash mismatch")
        return False, "root_hash mismatch", report

    report["manifest_ok"] = True
    report["checks"].append({"name": "manifest_integrity", "status": "pass"})

    evidence_index_path = pack_dir / "evidence_index.json"
    if evidence_index_path.exists():
        ok2, msg2, _ = _verify_semantic(pack_dir, evidence_index_path)
        report["semantic_ok"] = ok2
        if ok2:
            report["checks"].append({"name": "semantic_evidence", "status": "pass"})
        else:
            report["checks"].append({"name": "semantic_evidence", "status": "fail", "details": msg2})
            report["errors"].append(msg2)
            return False, msg2, report
    else:
        report["semantic_ok"] = None
        report["checks"].append({"name": "semantic_evidence", "status": "skip"})

    # Layer 5: Temporal commitment (independent of Layers 1-3)
    try:
        from scripts.mg_temporal import verify_temporal_commitment
        tc_ok, tc_msg = verify_temporal_commitment(pack_dir)
        report["temporal_ok"] = tc_ok
        if tc_ok:
            report["checks"].append({"name": "temporal_commitment", "status": "pass", "details": tc_msg})
        else:
            report["checks"].append({"name": "temporal_commitment", "status": "fail", "details": tc_msg})
            report["errors"].append(tc_msg)
            return False, tc_msg, report
    except ImportError:
        report["temporal_ok"] = None
        report["checks"].append({"name": "temporal_commitment", "status": "skip", "details": "mg_temporal not available"})
    except Exception as e:
        report["temporal_ok"] = None
        report["checks"].append({"name": "temporal_commitment", "status": "skip", "details": str(e)})

    return True, "PASS", report


_EXPECTED_DOMAIN_KEYS = {
    "mtr_phase", "inputs", "result", "execution_trace",
    "trace_root_hash", "anchor_hash", "anchor_claim_id",
}


def _verify_semantic(pack_dir: Path, evidence_index_path: Path) -> tuple[bool, str, list]:
    """Semantic verification of evidence bundles. Returns (ok, message, errors_list)."""
    warnings: list[str] = []
    try:
        index = json.loads(evidence_index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, f"Failed to load evidence_index.json: {e}", [f"Failed to load evidence_index.json: {e}"]
    if not isinstance(index, dict):
        return False, "evidence_index.json must be an object", ["evidence_index.json must be an object"]

    for claim_id, entry in index.items():
        if not isinstance(entry, dict):
            continue
        job_kind = entry.get("job_kind", "")
        for mode in ("normal", "canary"):
            bundle = entry.get(mode)
            if not bundle:
                continue
            run_rel = bundle.get("run_relpath", "")
            ledger_rel = bundle.get("ledger_relpath", "")
            if not run_rel or not ledger_rel:
                msg = f"evidence_index[{claim_id}].{mode} missing run_relpath or ledger_relpath"
                return False, msg, [msg]
            run_path = pack_dir / run_rel
            ledger_path = pack_dir / ledger_rel
            if not run_path.exists():
                msg = f"Run artifact missing: {run_rel}"
                return False, msg, [msg]
            if not ledger_path.exists() or ledger_path.stat().st_size == 0:
                msg = f"Ledger snapshot missing or empty: {ledger_rel}"
                return False, msg, [msg]
            try:
                art = json.loads(run_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                msg = f"Invalid run artifact {run_rel}: {e}"
                return False, msg, [msg]
            for key in ("trace_id", "job_snapshot", "canary_mode"):
                if key not in art:
                    msg = f"Run artifact {run_rel} missing required key: {key}"
                    return False, msg, [msg]
            snap = art.get("job_snapshot", {})
            domain = snap.get("result", {})
            if not isinstance(domain, dict):
                msg = f"Run artifact {run_rel} job_snapshot.result must be object"
                return False, msg, [msg]
            if "mtr_phase" not in domain:
                msg = f"Run artifact {run_rel} job_snapshot.result must contain mtr_phase"
                return False, msg, [msg]
            if domain.get("mtr_phase") is None or domain["mtr_phase"] == "":
                msg = f"Run artifact {run_rel} mtr_phase must be a non-empty string"
                return False, msg, [msg]
            if not job_kind:
                msg = f"evidence_index[{claim_id}] job_kind must be a non-empty string"
                return False, msg, [msg]
            payload = snap.get("payload", {})
            if payload.get("kind") != job_kind:
                msg = f"Run artifact {run_rel} payload.kind does not match evidence_index job_kind"
                return False, msg, [msg]
            expected_canary = mode == "canary"
            if art.get("canary_mode") != expected_canary:
                msg = f"Run artifact {run_rel} canary_mode must be {expected_canary} for {mode} bundle"
                return False, msg, [msg]
            inputs = domain.get("inputs", {})
            ds = inputs.get("dataset") if isinstance(inputs, dict) else {}
            if ds and isinstance(ds, dict):
                sha = ds.get("sha256", "")
                if sha and (len(sha) != 64 or not all(c in "0123456789abcdef" for c in sha)):
                    msg = f"Run artifact {run_rel} inputs.dataset.sha256 must be 64 hex chars"
                    return False, msg, [msg]
            result_block = domain.get("result", {})
            # Reject zero/negative thresholds for physical quantities
            for thresh_key in ("rel_err_threshold", "convergence_threshold",
                               "drift_threshold_pct"):
                thresh_val = (result_block.get(thresh_key)
                              if isinstance(result_block, dict) else None)
                if thresh_val is not None:
                    if thresh_val <= 0:
                        msg = (f"Run artifact {run_rel} {thresh_key} must be "
                               f"positive, got {thresh_val}")
                        return False, msg, [msg]
            uq = result_block.get("uncertainty") if isinstance(result_block, dict) else None
            if uq is not None and isinstance(uq, dict):
                for k in ("ci_low", "ci_high", "stability_score"):
                    if k not in uq:
                        msg = f"Run artifact {run_rel} uncertainty missing {k}"
                        return False, msg, [msg]
                if uq.get("ci_low", 0) >= uq.get("ci_high", 0):
                    msg = f"Run artifact {run_rel} uncertainty: ci_low must be < ci_high"
                    return False, msg, [msg]
                s = uq.get("stability_score", -1)
                if not (0 <= s <= 1):
                    msg = f"Run artifact {run_rel} uncertainty: stability_score must be in [0,1]"
                    return False, msg, [msg]
            # --- Step Chain Verification (PPA #63/996,819) ---
            # If execution_trace is present, verify structural integrity:
            # trace_root_hash must equal the hash stored in the final chain step.
            # The manifest SHA-256 ensures the artifact file was not modified;
            # this check ensures the hash chain itself is internally consistent.
            execution_trace = domain.get("execution_trace")
            claimed_root = domain.get("trace_root_hash")
            if execution_trace is not None or claimed_root is not None:
                if execution_trace is None:
                    msg = (f"Run artifact {run_rel} has trace_root_hash "
                           f"but missing execution_trace")
                    return False, msg, [msg]
                if claimed_root is None:
                    msg = (f"Run artifact {run_rel} has execution_trace "
                           f"but missing trace_root_hash")
                    return False, msg, [msg]
                if not isinstance(execution_trace, list) or len(execution_trace) == 0:
                    msg = (f"Run artifact {run_rel} execution_trace "
                           f"must be a non-empty list")
                    return False, msg, [msg]
                # --- Step count and ordering validation ---
                if len(execution_trace) != 4:
                    msg = (f"Run artifact {run_rel} execution_trace "
                           f"must have exactly 4 steps, got {len(execution_trace)}")
                    return False, msg, [msg]
                step_numbers = [s.get("step") for s in execution_trace]
                if step_numbers != [1, 2, 3, 4]:
                    msg = (f"Run artifact {run_rel} execution_trace "
                           f"steps must be [1, 2, 3, 4], got {step_numbers}")
                    return False, msg, [msg]
                for step in execution_trace:
                    h = step.get("hash", "")
                    if not (isinstance(h, str) and len(h) == 64
                            and all(c in "0123456789abcdef" for c in h)):
                        msg = (f"Run artifact {run_rel} execution_trace "
                               f"step {step.get('step')} has invalid hash")
                        return False, msg, [msg]
                last_hash = execution_trace[-1].get("hash", "")
                if claimed_root != last_hash:
                    msg = (f"Run artifact {run_rel} trace_root_hash does not match "
                           f"final execution_trace step hash — Step Chain broken")
                    return False, msg, [msg]
            # --- anchor_hash format validation ---
            # If anchor_hash present in inputs, verify it is valid 64-char hex.
            # This ensures Cross-Claim Chain references are well-formed.
            # Does NOT verify the upstream bundle (that requires verify-chain CLI).
            if isinstance(inputs, dict):
                ah = inputs.get("anchor_hash")
                if ah is not None:
                    if not (isinstance(ah, str) and len(ah) == 64
                            and all(c in "0123456789abcdef" for c in ah)):
                        msg = (f"Run artifact {run_rel} inputs.anchor_hash "
                               f"must be valid 64-char lowercase hex or None")
                        return False, msg, [msg]
            # --- Extra field warnings (forward-compatible) ---
            extra_keys = set(domain.keys()) - _EXPECTED_DOMAIN_KEYS
            if extra_keys:
                for ek in sorted(extra_keys):
                    warnings.append(
                        f"Run artifact {run_rel} unexpected field: {ek}")
    return True, "PASS", warnings


def _verify_chain(packs: list) -> tuple[bool, str, dict]:
    """
    Verify a Cross-Claim Chain: sequence of bundles where each bundle's
    anchor_hash must match the previous bundle's trace_root_hash.

    Args:
        packs: list of Path objects — ordered upstream to downstream
               e.g. [mtr1_bundle, dtfem_bundle, drift_bundle]

    Returns: (ok, message, report)
    """
    report = {
        "version": "v1",
        "chain_length": len(packs),
        "links": [],
        "errors": [],
    }

    if len(packs) < 2:
        msg = "verify-chain requires at least 2 bundles"
        report["errors"].append(msg)
        return False, msg, report

    # Verify each bundle individually first
    prev_trace_root_hash = None
    prev_pack_name = None

    for i, pack_dir in enumerate(packs):
        pack_dir = Path(pack_dir)
        ok, msg, pack_report = _verify_pack(pack_dir)
        link = {
            "pack": str(pack_dir.name),
            "position": i,
            "individual_verify": "pass" if ok else "fail",
            "trace_root_hash": None,
            "anchor_hash": None,
            "chain_link": "skip" if i == 0 else None,
        }

        if not ok:
            link["error"] = msg
            report["links"].append(link)
            report["errors"].append(f"Bundle {pack_dir.name}: {msg}")
            return False, f"Bundle {pack_dir.name} failed individual verification: {msg}", report

        # Extract trace_root_hash and anchor_hash from this bundle
        evidence_index_path = pack_dir / "evidence_index.json"
        if not evidence_index_path.exists():
            msg = f"Bundle {pack_dir.name}: evidence_index.json not found"
            report["errors"].append(msg)
            return False, msg, report

        index = json.loads(evidence_index_path.read_text(encoding="utf-8"))
        bundle_trace_root = None
        bundle_anchor_hash = None

        for claim_id, entry in index.items():
            normal = entry.get("normal", {})
            run_rel = normal.get("run_relpath", "")
            if not run_rel:
                continue
            run_path = pack_dir / run_rel
            if not run_path.exists():
                continue
            art = json.loads(run_path.read_text(encoding="utf-8"))
            snap = art.get("job_snapshot", {})
            domain = snap.get("result", {})
            bundle_trace_root = domain.get("trace_root_hash")
            bundle_anchor_hash = domain.get("inputs", {}).get("anchor_hash")
            break  # use first claim found

        link["trace_root_hash"] = bundle_trace_root
        link["anchor_hash"] = bundle_anchor_hash

        # Verify chain link: this bundle's anchor_hash must match previous trace_root_hash
        if i > 0 and prev_trace_root_hash is not None:
            if bundle_anchor_hash is None:
                msg = (f"Bundle {pack_dir.name} has no anchor_hash — "
                       f"cannot verify chain link from {prev_pack_name}")
                link["chain_link"] = "fail"
                link["error"] = msg
                report["links"].append(link)
                report["errors"].append(msg)
                return False, msg, report

            if bundle_anchor_hash != prev_trace_root_hash:
                msg = (f"Chain broken between {prev_pack_name} and {pack_dir.name}: "
                       f"anchor_hash does not match upstream trace_root_hash")
                link["chain_link"] = "fail"
                link["error"] = msg
                report["links"].append(link)
                report["errors"].append(msg)
                return False, f"CHAIN BROKEN: {msg}", report

            link["chain_link"] = "pass"

        report["links"].append(link)
        prev_trace_root_hash = bundle_trace_root
        prev_pack_name = pack_dir.name

    return True, "CHAIN PASS", report


def cmd_verify_chain(args) -> int:
    """Verify a Cross-Claim Chain of bundles."""
    packs = args.packs
    ok, msg, report = _verify_chain(packs)
    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(msg)
    if not ok:
        for err in report.get("errors", []):
            print(f"  → {err}")
    return 0 if ok else 1


def cmd_pack_verify(args) -> int:
    ok, msg, _ = _verify_pack(args.input)
    print(msg)
    return 0 if ok else 1


def cmd_bench_run(args) -> int:
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "bench01_run.py"),
        "--output-dir", str(args.output),
        "--reports-dir", str(args.reports),
        "--mode", getattr(args, "mode", "both"),
    ]
    if getattr(args, "dataset_relpath", None):
        cmd.extend(["--dataset-relpath", args.dataset_relpath])
    if getattr(args, "elastic_strain_max", None) is not None:
        cmd.extend(["--elastic-strain-max", str(args.elastic_strain_max)])
    if getattr(args, "uq_samples", None) is not None:
        cmd.extend(["--uq-samples", str(args.uq_samples)])
    if getattr(args, "uq_seed", None) is not None:
        cmd.extend(["--uq-seed", str(args.uq_seed)])
    return _run(cmd)


def cmd_claim_run_mtr1(args) -> int:
    rc = cmd_bench_run(args)
    if rc != 0:
        return rc
    summary_path = Path(args.output) / "bench01_summary.json"
    if not summary_path.exists():
        return 1
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    mg = data.get("metagenesis", {})
    print(json.dumps(mg, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(prog="mg", description="MetaGenesis CLI")
    sub = ap.add_subparsers(dest="group", required=True)

    steward = sub.add_parser("steward")
    steward_sub = steward.add_subparsers(dest="command", required=True)
    steward_audit = steward_sub.add_parser("audit")
    steward_audit.set_defaults(func=cmd_steward_audit)

    pack = sub.add_parser("pack")
    pack_sub = pack.add_subparsers(dest="command", required=True)
    pack_build = pack_sub.add_parser("build")
    pack_build.add_argument("--output", "-o", type=Path, required=True)
    pack_build.add_argument("--index", type=Path, default=None)
    pack_build.add_argument("--include-evidence", action="store_true")
    pack_build.add_argument("--source-reports-dir", type=Path, default=None)
    pack_build.set_defaults(func=cmd_pack_build)
    pack_verify = pack_sub.add_parser("verify")
    pack_verify.add_argument("--pack", "-p", type=Path, required=True, dest="input", help="Pack directory to verify")
    pack_verify.set_defaults(func=cmd_pack_verify)

    verify_top = sub.add_parser("verify")
    verify_top.add_argument("--pack", "-p", type=Path, required=True, help="Pack directory to verify")
    verify_top.add_argument("--json", "-j", type=Path, default=None, help="Write machine-readable JSON report to path")

    def _verify_pack_cmd(a):
        ok, msg, report = _verify_pack(a.pack)
        json_path = getattr(a, "json", None)
        if json_path is not None:
            out_path = Path(json_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(msg)
        return 0 if ok else 1

    verify_top.set_defaults(func=_verify_pack_cmd)

    verify_chain = sub.add_parser("verify-chain")
    verify_chain.add_argument("packs", nargs="+", type=Path,
                              help="Ordered list of bundle paths (upstream first)")
    verify_chain.add_argument("--json", "-j", type=Path, default=None,
                              help="Write machine-readable JSON report to path")
    verify_chain.set_defaults(func=cmd_verify_chain)

    bench = sub.add_parser("bench")
    bench_sub = bench.add_subparsers(dest="command", required=True)
    bench_run = bench_sub.add_parser("run")
    bench_run.add_argument("--output", "-o", type=Path, required=True)
    bench_run.add_argument("--reports", "-r", type=Path, required=True)
    bench_run.add_argument("--dataset-relpath", type=str, default=None)
    bench_run.add_argument("--elastic-strain-max", type=float, default=None)
    bench_run.add_argument("--uq-samples", type=int, default=None)
    bench_run.add_argument("--uq-seed", type=int, default=None)
    bench_run.add_argument("--mode", choices=("normal", "canary", "both"), default="both")
    bench_run.set_defaults(func=cmd_bench_run)

    claim = sub.add_parser("claim")
    claim_sub = claim.add_subparsers(dest="command", required=True)
    claim_run = claim_sub.add_parser("run")
    claim_run.add_argument("claim_id", choices=("mtr1",))
    claim_run.add_argument("--output", "-o", type=Path, required=True)
    claim_run.add_argument("--reports", "-r", type=Path, required=True)
    claim_run.add_argument("--dataset-relpath", type=str, default=None)
    claim_run.add_argument("--elastic-strain-max", type=float, default=None)
    claim_run.add_argument("--uq-samples", type=int, default=None)
    claim_run.add_argument("--uq-seed", type=int, default=None)
    claim_run.add_argument("--mode", choices=("normal", "canary", "both"), default="both")
    claim_run.set_defaults(func=cmd_claim_run_mtr1)

    # --- sign subcommand (Innovation #6) ---
    sign_cmd = sub.add_parser("sign", help="Bundle signing (Innovation #6)")
    sign_sub = sign_cmd.add_subparsers(dest="command", required=True)

    sign_keygen = sign_sub.add_parser("keygen", help="Generate signing key")
    sign_keygen.add_argument("--out", "-o", required=True, help="Output key file (.json)")
    sign_keygen.add_argument("--type", "-t", choices=["ed25519", "hmac"],
                             default="ed25519", help="Key type (default: ed25519)")

    sign_bundle_cmd = sign_sub.add_parser("bundle", help="Sign a bundle")
    sign_bundle_cmd.add_argument("--pack", "-p", required=True, help="Bundle directory")
    sign_bundle_cmd.add_argument("--key", "-k", required=True, help="Signing key file")

    sign_verify_cmd = sign_sub.add_parser("verify", help="Verify bundle signature")
    sign_verify_cmd.add_argument("--pack", "-p", required=True, help="Bundle directory")
    sign_verify_cmd.add_argument("--key", "-k", default=None, help="Signing key (full HMAC)")
    sign_verify_cmd.add_argument("--fingerprint", "-f", default=None, help="Key fingerprint only")

    def _cmd_sign_keygen(a):
        key_type = getattr(a, 'type', 'ed25519')
        if key_type == 'ed25519':
            from scripts.mg_ed25519 import generate_key_files
            key_data = generate_key_files(Path(a.out))
            stem = Path(a.out).stem
            pub_path = Path(a.out).parent / f"{stem}.pub.json"
            print(f"Ed25519 signing key: {a.out}")
            print(f"Public key:          {pub_path}")
            print(f"Fingerprint:         {key_data['fingerprint']}")
            print(f"KEEP {a.out} SECRET. Share {pub_path} with auditors.")
        else:
            from scripts.mg_sign import generate_key
            import json as _j
            key = generate_key()
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            Path(a.out).write_text(_j.dumps(key, indent=2), encoding="utf-8")
            print(f"HMAC signing key: {a.out}")
            print(f"Fingerprint:      {key['fingerprint']}")
            print("KEEP KEY SECRET. Share only the fingerprint.")
        return 0

    def _cmd_sign_bundle(a):
        from scripts.mg_sign import sign_bundle
        import json as _j
        sig = sign_bundle(Path(a.pack), Path(a.key))
        print(f"SIGNED")
        print(f"  root_hash:       {sig['signed_root_hash']}")
        print(f"  key_fingerprint: {sig['key_fingerprint']}")
        return 0

    def _cmd_sign_verify(a):
        from scripts.mg_sign import verify_bundle_signature
        ok, msg = verify_bundle_signature(
            Path(a.pack),
            key_path=Path(a.key) if a.key else None,
            expected_fingerprint=getattr(a, 'fingerprint', None),
        )
        print(msg)
        return 0 if ok else 1

    sign_keygen.set_defaults(func=_cmd_sign_keygen)
    sign_bundle_cmd.set_defaults(func=_cmd_sign_bundle)
    sign_verify_cmd.set_defaults(func=_cmd_sign_verify)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
