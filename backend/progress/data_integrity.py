#!/usr/bin/env python3
"""
DATA-01 Data Integrity Layer.

Deterministic dataset_fingerprint (sha256 over canonicalized bytes).
No heavy deps (stdlib only). Part of MetaGenesis Core verification pipeline (MVP v0.2)
"""

import csv
import hashlib
from pathlib import Path
from typing import Dict, Any


def canonicalize_bytes(b: bytes) -> bytes:
    """Normalize CRLF -> LF, ensure single trailing newline."""
    text = b.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text and not text.endswith("\n"):
        text += "\n"
    return text.encode("utf-8")


def sha256_hex(b: bytes) -> str:
    """Return hex digest of bytes."""
    return hashlib.sha256(b).hexdigest()


def fingerprint_file(path: Path) -> Dict[str, Any]:
    """
    Read file, canonicalize, compute sha256. Optionally return rows/cols for CSV.
    Returns dict: {sha256, bytes (length), rows?, cols?}.
    """
    raw = path.read_bytes()
    canonical = canonicalize_bytes(raw)
    digest = sha256_hex(canonical)
    out = {"sha256": digest, "bytes": len(canonical)}
    try:
        text = canonical.decode("utf-8")
        reader = csv.reader(text.strip().splitlines())
        rows = list(reader)
        if rows:
            out["rows"] = len(rows)
            out["cols"] = len(rows[0]) if rows[0] else 0
    except Exception:
        pass
    return out
