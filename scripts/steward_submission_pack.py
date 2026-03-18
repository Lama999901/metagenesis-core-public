#!/usr/bin/env python3
"""
STEW-04 Deterministic Submission Pack Generator v0.1

Builds a submission-ready doc pack from canonical_state, phase_registry,
scientific_claim_index, and dossiers. Writes ONLY to user-provided output dir.
Generates pack_manifest.json (CERT-01) for tamper-evident verification.
No network. No LLM. No new deps.
"""

import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX = REPO_ROOT / "reports/scientific_claim_index.md"
CANONICAL_PATH = REPO_ROOT / "reports/canonical_state.md"
PHASE_REGISTRY_PATH = REPO_ROOT / "reports/phase_registry_v0_1.md"


def _read(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_canonical_table(text: str) -> dict:
    out = {}
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or "|-------|" in line or "| Field |" in line:
            continue
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) >= 2:
            key = re.sub(r"\*+", "", parts[0]).strip()
            out[key] = parts[1]
    return out


def _extract_fenced_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    return m.group(1).strip() if m else "{}"


def _build_overview(canonical: dict, claim_ids: list[str], claims_parsed: list[dict]) -> str:
    project = canonical.get("project", "MetaGenesis Core")
    owner = canonical.get("owner", "MetaGenesis")
    claims_list = ", ".join(claim_ids) if claim_ids else canonical.get("current_claims_list", "")
    reproductions = []
    for c in claims_parsed:
        r = c.get("reproduction", "").strip().strip("`")
        if r:
            reproductions.append(r)
    repro_block = "\n".join(f"- `{r}`" for r in reproductions) if reproductions else "- (see claim dossiers)"
    return f"""# Submission Pack Overview

## Project

- **Project:** {project}
- **Owner:** {owner}

## Proof-loop summary

Execution → Evidence (progress_runs, ledger_snapshots) → Evidence Index → Evidence API (GET /api/evidence/{{trace_id}}). All domain results live under `job_snapshot.result` in run artifacts.

## Governance invariants

- Policy Gate: all changed paths must match allowlist; locked paths blocked.
- Steward audit: required files exist; phase 42 locked; bidirectional claim coverage (runner mtr* kinds ↔ scientific_claim_index).
- Case opening protocol: contract (kind/payload), normal + canary, evidence artifacts, V&V + reproducibility shape.

## Claims

{claims_list}

## Reproduction commands

{repro_block}

## Evidence location rule

Domain results are stored in **job_snapshot.result** in the run artifact JSON (reports/progress_runs/ or configured artifact dir).
"""


def build_submission_pack(
    output_dir: Path,
    index_path: Path = None,
    canonical_path: Path = None,
    phase_registry_path: Path = None,
    include_evidence: bool = False,
    source_reports_dir: Path = None,
) -> list[Path]:
    """
    Generate full submission pack into output_dir. Returns list of created paths.
    Does not write under reports/.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = index_path or DEFAULT_INDEX
    canonical_path = canonical_path or CANONICAL_PATH
    phase_registry_path = phase_registry_path or PHASE_REGISTRY_PATH
    created = []

    canonical_text = _read(canonical_path)
    canonical = _parse_canonical_table(canonical_text)
    out_canonical = output_dir / "canonical_state_snapshot.md"
    out_canonical.write_text(canonical_text, encoding="utf-8")
    created.append(out_canonical)

    phase_text = _read(phase_registry_path)
    phase_json_str = _extract_fenced_json(phase_text)
    out_phase = output_dir / "phase_registry_snapshot.json"
    out_phase.write_text(phase_json_str, encoding="utf-8")
    created.append(out_phase)

    claims_dir = output_dir / "claims"
    claims_dir.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(REPO_ROOT))
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import steward_dossier as sd
    dossier_paths = sd.build_dossiers(claims_dir, index_path=index_path)
    for p in dossier_paths:
        new_name = p.parent / f"dossier_{p.stem}.md"
        p.rename(new_name)
        created.append(new_name)

    index_text = _read(index_path)
    claims_parsed = sd._parse_claim_sections(index_text)
    claim_ids = [c.get("claim_id", "").strip() for c in claims_parsed if c.get("claim_id")]
    overview_content = _build_overview(canonical, claim_ids, claims_parsed)
    out_overview = output_dir / "overview.md"
    out_overview.write_text(overview_content, encoding="utf-8")
    created.append(out_overview)

    if include_evidence and source_reports_dir:
        _include_evidence_in_pack(output_dir, source_reports_dir, claims_parsed)

    _write_pack_manifest(output_dir)

    return created


def _job_kind_from_claim(c: dict) -> str:
    return c.get("job_kind", "").strip().strip("`")


def _include_evidence_in_pack(
    output_dir: Path,
    source_reports_dir: Path,
    claims_parsed: list[dict],
) -> None:
    """Copy selected evidence into pack; write evidence_index.json."""
    output_dir = Path(output_dir)
    source_reports_dir = Path(source_reports_dir)
    progress_runs = source_reports_dir / "progress_runs"
    ledger_snapshots = source_reports_dir / "ledger_snapshots"
    if not progress_runs.exists():
        return

    arts_by_job_canary = {}
    for f in progress_runs.glob("*.json"):
        try:
            art = json.loads(f.read_text(encoding="utf-8"))
            payload = (art.get("job_snapshot") or {}).get("payload") or {}
            jk = payload.get("kind")
            if not jk:
                continue
            cm = art.get("canary_mode") is True
            key = (jk, cm)
            lst = arts_by_job_canary.setdefault(key, [])
            lst.append(art)
        except (json.JSONDecodeError, OSError):
            continue
    for key in arts_by_job_canary:
        arts_by_job_canary[key].sort(key=lambda a: a.get("persisted_at", ""), reverse=True)

    index_out = {}
    for c in claims_parsed:
        claim_id = c.get("claim_id", "").strip()
        job_kind = _job_kind_from_claim(c)
        if not claim_id or not job_kind:
            continue
        claim_ev = output_dir / "evidence" / claim_id
        index_out[claim_id] = {"job_kind": job_kind, "normal": None, "canary": None}

        for mode, is_canary in [("normal", False), ("canary", True)]:
            arts = arts_by_job_canary.get((job_kind, is_canary), [])
            arts = [a for a in arts if a.get("canary_mode") is is_canary]
            if not arts:
                continue
            art = arts[0]
            tid = art.get("trace_id")
            (claim_ev / mode).mkdir(parents=True, exist_ok=True)
            run_rel = f"evidence/{claim_id}/{mode}/run_artifact.json"
            ledger_rel = f"evidence/{claim_id}/{mode}/ledger_snapshot.jsonl"
            (output_dir / run_rel).write_text(json.dumps(art, indent=2), encoding="utf-8")
            snap_path = ledger_snapshots / f"trace_{tid}.jsonl"
            if snap_path.exists():
                (output_dir / ledger_rel).write_text(snap_path.read_text(encoding="utf-8"), encoding="utf-8")
            index_out[claim_id][mode] = {"trace_id": tid, "run_relpath": run_rel, "ledger_relpath": ledger_rel}

    (output_dir / "evidence_index.json").write_text(json.dumps(index_out, indent=2), encoding="utf-8")


def _write_pack_manifest(pack_root: Path) -> None:
    """Write pack_manifest.json with sha256 for every file (excluding manifest itself)."""
    pack_root = Path(pack_root)
    files_list = []
    for p in sorted(pack_root.rglob("*")):
        if not p.is_file() or p.name == "pack_manifest.json":
            continue
        relpath = str(p.relative_to(pack_root)).replace("\\", "/")
        raw = p.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        files_list.append({"relpath": relpath, "sha256": sha, "bytes": len(raw)})

    lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in sorted(files_list, key=lambda x: x["relpath"]))
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "pack_version": "1",
        "protocol_version": 1,
        "files": files_list,
        "root_hash": root_hash,
    }
    (pack_root / "pack_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main():
    import argparse
    p = argparse.ArgumentParser(description="STEW-04 Submission Pack Generator")
    p.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory (default: temp dir outside reports)",
    )
    p.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="Scientific claim index path")
    p.add_argument("--include-evidence", action="store_true", help="Include evidence bundles from source-reports-dir")
    p.add_argument("--source-reports-dir", type=Path, default=None, help="Source dir for progress_runs/ledger_snapshots")
    args = p.parse_args()
    if args.output is None:
        args.output = Path(tempfile.mkdtemp(prefix="stew_submission_pack_"))
    source_dir = args.source_reports_dir or (REPO_ROOT / "reports") if args.include_evidence else None
    created = build_submission_pack(
        args.output,
        index_path=args.index,
        include_evidence=args.include_evidence,
        source_reports_dir=source_dir,
    )
    print(f"Built submission pack in {args.output}: {len(created)} files")
    for c in sorted(created):
        print(f"  {c.relative_to(args.output)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
