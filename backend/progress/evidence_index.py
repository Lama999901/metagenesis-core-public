#!/usr/bin/env python3
"""
Evidence Index v1 - Read-only index of W6-A5 evidence artifacts.

Purpose: Scan progress_runs and ledger_snapshots; return trace_id -> artifacts metadata.
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def build_evidence_index(base_dir: Path = None) -> Dict[str, Dict[str, Any]]:
    """Build a read-only index of evidence artifacts under base_dir.

    Scans:
      - base_dir/progress_runs/*.json  (run artifacts; extract trace_id, kind)
      - base_dir/ledger_snapshots/*.jsonl (ledger snapshots; trace_id from filename)

    Args:
        base_dir: Root for progress_runs and ledger_snapshots.
                  Defaults to Path(os.getenv("MG_PROGRESS_ARTIFACT_DIR", "reports")).

    Returns:
        Mapping trace_id -> { "trace_id": str, "artifacts": [ { "path", "type", "size" }, ... ] }
        Artifact type is "run_artifact" or "ledger_snapshot".
    """
    if base_dir is None:
        base_dir = Path(os.getenv("MG_PROGRESS_ARTIFACT_DIR", "reports"))
    base_dir = Path(base_dir)
    index: Dict[str, Dict[str, Any]] = {}

    def ensure_entry(trace_id: str) -> None:
        if trace_id not in index:
            index[trace_id] = {"trace_id": trace_id, "artifacts": []}

    def add_artifact(trace_id: str, path: Path, artifact_type: str, size: int) -> None:
        ensure_entry(trace_id)
        index[trace_id]["artifacts"].append({
            "path": str(path),
            "type": artifact_type,
            "size": size,
        })

    # progress_runs/*.json
    progress_runs_dir = base_dir / "progress_runs"
    if progress_runs_dir.exists():
        for f in progress_runs_dir.glob("*.json"):
            try:
                with open(f, "r") as fp:
                    data = json.load(fp)
                trace_id = data.get("trace_id")
                if trace_id:
                    add_artifact(trace_id, f, "run_artifact", f.stat().st_size)
            except (json.JSONDecodeError, OSError):
                continue

    # ledger_snapshots/*.jsonl (trace_id from filename trace_<trace_id>.jsonl)
    ledger_snapshots_dir = base_dir / "ledger_snapshots"
    if ledger_snapshots_dir.exists():
        for f in ledger_snapshots_dir.glob("*.jsonl"):
            try:
                # Filename format: trace_<trace_id>.jsonl
                stem = f.stem
                if stem.startswith("trace_"):
                    trace_id = stem[6:]
                    if trace_id:
                        add_artifact(trace_id, f, "ledger_snapshot", f.stat().st_size)
            except OSError:
                continue

    return index
