#!/usr/bin/env python3
"""
DATA-PIPE-01 Dataset Quality Certificate.

Deterministic dataset integrity + quality checks. Fingerprint, schema, ranges.
Stdlib only. No network. No heavy deps.
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

JOB_KIND = "datapipe1_quality_certificate"
ALGORITHM_VERSION = "v1"
METHOD = "csv_schema_quality_v1"


def _parse_list(val: Any) -> List[str]:
    """Parse required_columns/numeric_columns from list or JSON string."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x).strip() for x in val if x]
    if isinstance(val, str):
        try:
            obj = json.loads(val)
            return [str(x).strip() for x in (obj if isinstance(obj, list) else []) if x]
        except (json.JSONDecodeError, TypeError):
            return [x.strip() for x in val.split(",") if x.strip()]
    return []


def _parse_ranges(ranges_json: Optional[str]) -> Dict[str, Dict[str, float]]:
    """Parse ranges_json -> {col: {min?, max?}}."""
    if not ranges_json or not isinstance(ranges_json, str):
        return {}
    try:
        obj = json.loads(ranges_json)
        if not isinstance(obj, dict):
            return {}
        out = {}
        for col, spec in obj.items():
            if isinstance(spec, dict):
                out[str(col)] = {k: float(v) for k, v in spec.items() if k in ("min", "max")}
        return out
    except (json.JSONDecodeError, TypeError, ValueError):
        return {}


def run_certificate(
    seed: int,
    dataset_relpath: str,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    ranges_json: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run DATA-PIPE-01 quality certificate. Fingerprint, schema, range checks.
    No absolute paths in output.
    """
    from backend.progress.data_integrity import fingerprint_file

    path = REPO_ROOT / dataset_relpath
    if not path.exists():
        raise ValueError(f"Dataset not found: {dataset_relpath}")

    fp = fingerprint_file(path)
    dataset_info = {
        "relpath": dataset_relpath,
        "sha256": fp["sha256"],
        "bytes": fp["bytes"],
        "rows": fp.get("rows"),
        "cols": fp.get("cols"),
    }

    req_cols = _parse_list(required_columns) or []
    num_cols = _parse_list(numeric_columns) or []
    ranges = _parse_ranges(ranges_json)

    issues: List[str] = []
    missing_count = 0
    parse_error_count = 0

    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(text.strip().splitlines())
    rows = list(reader)
    if not rows:
        issues.append("CSV has no data rows")
        return {
            "domain": "DATA",
            "claim_id": "DATA-PIPE-01",
            "mtr_phase": "DATA-PIPE-01",
            "inputs": {
                "dataset": dataset_info,
                "checks": {
                    "required_columns": req_cols,
                    "numeric_columns": num_cols,
                    "ranges": ranges,
                },
            },
            "result": {
                "pass": False,
                "issues": issues,
                "metrics": {
                    "rows": 0,
                    "cols": len(reader.fieldnames or []),
                    "missing_count": 0,
                    "parse_error_count": 0,
                },
            },
            "method": METHOD,
            "algorithm_version": ALGORITHM_VERSION,
        }

    headers = list(rows[0].keys()) if rows[0] else []

    for col in req_cols:
        if col not in headers:
            issues.append(f"Missing required column: {col}")
            missing_count += 1

    for row_idx, row in enumerate(rows):
        for col in num_cols:
            if col not in headers:
                continue
            val = row.get(col, "")
            if val == "" or val is None:
                missing_count += 1
                continue
            try:
                float(val)
            except (ValueError, TypeError):
                parse_error_count += 1
                if len(issues) < 10:
                    issues.append(f"Parse error row {row_idx} col '{col}': {val!r}")

        for col, bounds in ranges.items():
            if col not in headers:
                continue
            val = row.get(col, "")
            if val == "" or val is None:
                continue
            try:
                v = float(val)
                if "min" in bounds and v < bounds["min"]:
                    issues.append(f"Range violation row {row_idx} col '{col}': {v} < {bounds['min']}")
                if "max" in bounds and v > bounds["max"]:
                    issues.append(f"Range violation row {row_idx} col '{col}': {v} > {bounds['max']}")
            except (ValueError, TypeError):
                pass

    pass_ = len(issues) == 0
    metrics = {
        "rows": len(rows),
        "cols": len(headers),
        "missing_count": missing_count,
        "parse_error_count": parse_error_count,
    }

    # --- Step Chain Verification ---
    def _hash_step(step_name, step_data, prev_hash):
        import hashlib, json as _j
        content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    _dataset_sha = dataset_info.get("sha256", "") if isinstance(dataset_info, dict) else ""
    _prev = _hash_step("init_params", {"dataset_relpath": str(dataset_relpath or ""), "required_columns": sorted(req_cols or []), "numeric_columns": sorted(num_cols or [])}, "genesis")
    _trace = [{"step": 1, "name": "init_params", "hash": _prev}]
    _prev = _hash_step("load_dataset", {"rows": len(rows), "cols": len(headers), "sha256": _dataset_sha[:16]}, _prev)
    _trace.append({"step": 2, "name": "load_dataset", "hash": _prev, "output": {"rows": len(rows), "cols": len(headers)}})
    _prev = _hash_step("run_checks", {"missing_count": missing_count, "parse_error_count": parse_error_count, "issues_count": len(issues)}, _prev)
    _trace.append({"step": 3, "name": "run_checks", "hash": _prev, "output": {"issues_count": len(issues)}})
    _prev = _hash_step("threshold_check", {"pass": pass_, "issues_count": len(issues)}, _prev)
    _trace.append({"step": 4, "name": "threshold_check", "hash": _prev, "output": {"pass": pass_}})
    _trace_root_hash = _prev
    # --- End Step Chain ---
    return {
        "domain": "DATA",
        "claim_id": "DATA-PIPE-01",
        "mtr_phase": "DATA-PIPE-01",
        "inputs": {
            "dataset": dataset_info,
            "checks": {
                "required_columns": req_cols,
                "numeric_columns": num_cols,
                "ranges": ranges,
            },
        },
        "result": {
            "pass": pass_,
            "issues": issues[:20],
            "metrics": metrics,
        },
        "method": METHOD,
        "algorithm_version": ALGORITHM_VERSION,
        "execution_trace": _trace,
        "trace_root_hash": _trace_root_hash,
    }
