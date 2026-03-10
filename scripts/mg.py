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

    return True, "PASS", report


def _verify_semantic(pack_dir: Path, evidence_index_path: Path) -> tuple[bool, str, list]:
    """Semantic verification of evidence bundles. Returns (ok, message, errors_list)."""
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
    return True, "PASS", []


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

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
