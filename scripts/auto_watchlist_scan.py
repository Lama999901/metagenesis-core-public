#!/usr/bin/env python3
"""
MetaGenesis Core -- Auto Watchlist Scanner
==========================================
Finds .md/.yaml/.cff/.txt files NOT tracked by check_stale_docs.py watchlists.

Prevents documentation files from escaping the staleness tracking system.
New files added to the repo should be consciously added to the watchlist
or explicitly excluded.

Usage:
    python scripts/auto_watchlist_scan.py           # report only (exit 0)
    python scripts/auto_watchlist_scan.py --strict   # exit 1 if unwatched files exist
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Import watchlists from check_stale_docs.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_stale_docs import CRITICAL_FILES, CONTENT_CHECKS  # noqa: E402

# Build the "watched" set -- union of both watchlists
WATCHED = set(CRITICAL_FILES.keys()) | set(CONTENT_CHECKS.keys())

# Extensions to scan
SCAN_EXTENSIONS = {".md", ".yaml", ".yml", ".cff", ".txt"}

# Directories to scan recursively (beyond repo root)
SCAN_SUBDIRS = ["docs", "ppa", "reports", "demos"]

# Directories to exclude entirely
EXCLUDE_DIRS = {
    ".planning", ".claude", ".git", "__pycache__",
    "node_modules", ".venv", ".mypy_cache", ".pytest_cache",
}


def _should_exclude(path: Path) -> bool:
    """Check if any part of the path is in EXCLUDE_DIRS."""
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def collect_doc_files() -> set:
    """Collect all doc files matching SCAN_EXTENSIONS in scanned paths."""
    found = set()

    # Scan repo root (non-recursive -- root-level files only)
    for f in REPO_ROOT.iterdir():
        if f.is_file() and f.suffix.lower() in SCAN_EXTENSIONS:
            rel = f.relative_to(REPO_ROOT).as_posix()
            found.add(rel)

    # Scan subdirectories recursively
    for subdir in SCAN_SUBDIRS:
        scan_path = REPO_ROOT / subdir
        if not scan_path.exists():
            continue
        for f in scan_path.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in SCAN_EXTENSIONS:
                continue
            rel_path = f.relative_to(REPO_ROOT)
            if _should_exclude(rel_path):
                continue
            found.add(rel_path.as_posix())

    return found


def scan(strict: bool = False) -> int:
    """Run the watchlist coverage scan. Returns exit code."""
    print()
    print("=" * 60)
    print("  MetaGenesis Core -- Watchlist Coverage Scan")
    print("=" * 60)

    found = collect_doc_files()
    unwatched = sorted(found - WATCHED)
    watched = sorted(found & WATCHED)

    if unwatched:
        print()
        for path in unwatched:
            print(f"  WARNING: {path} is NOT in any watchlist")

    print()
    total = len(found)
    watched_count = len(watched)
    unwatched_count = len(unwatched)
    print(f"  {watched_count}/{total} files watched ({unwatched_count} unwatched)")

    if unwatched_count == 0:
        print("  All doc files are tracked.")
    else:
        print()
        print("  To fix: add unwatched files to CRITICAL_FILES or CONTENT_CHECKS")
        print("  in scripts/check_stale_docs.py, or move them to an excluded directory.")

    print()
    print("=" * 60)
    print()

    if strict and unwatched_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    sys.exit(scan(strict=strict))
