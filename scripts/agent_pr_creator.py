#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent PR Creator (Autonomous Forge)
=======================================================
Level 3 autonomous agent: scans for auto-fixable issues,
creates branches/PRs for stale counters when safe.

Three detectors:
  1. Stale counter  -- system_manifest.json test_count vs actual
  2. Forbidden terms -- banned words in docs/scripts/backend
  3. Manifest sync   -- version vs latest git tag

Usage:
    python scripts/agent_pr_creator.py              # full scan + auto-fix
    python scripts/agent_pr_creator.py --summary    # report only
    python scripts/agent_pr_creator.py --dry-run    # report only (alias)
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. Stale counter detection
# ---------------------------------------------------------------------------
def detect_stale_counters(dry_run=False):
    """Compare system_manifest.json test_count against actual pytest count."""
    manifest_path = REPO_ROOT / "system_manifest.json"
    with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
        manifest = json.load(f)
    manifest_count = manifest.get("test_count", 0)

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "--collect-only", "-q"],
        stdout=subprocess.PIPE, text=True, cwd=str(REPO_ROOT),
        stderr=subprocess.DEVNULL, encoding="utf-8", errors="ignore",
    )
    actual_count = 0
    m = re.search(r"(\d+) tests? collected", proc.stdout)
    if m:
        actual_count = int(m.group(1))

    stale = manifest_count != actual_count and actual_count > 0
    result = {
        "stale": stale,
        "manifest_count": manifest_count,
        "actual_count": actual_count,
    }

    if stale and not dry_run:
        _auto_fix_stale_counter(manifest_path, manifest, actual_count)

    return result


def _auto_fix_stale_counter(manifest_path, manifest, actual_count):
    """Create branch, update manifest test_count, commit, push."""
    branch = f"auto-fix/stale-counter-{datetime.now().strftime('%Y%m%d')}"
    subprocess.run(
        ["git", "checkout", "-b", branch],
        cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL,
        encoding="utf-8", errors="ignore",
    )
    manifest["test_count"] = actual_count
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    subprocess.run(
        ["git", "add", str(manifest_path)],
        cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL,
        encoding="utf-8", errors="ignore",
    )
    subprocess.run(
        ["git", "commit", "-m", f"fix: update test_count {actual_count}"],
        cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL,
        encoding="utf-8", errors="ignore",
    )
    subprocess.run(
        ["git", "push", "-u", "origin", branch],
        cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL,
        encoding="utf-8", errors="ignore",
    )


# ---------------------------------------------------------------------------
# 2. Forbidden term detection
# ---------------------------------------------------------------------------
def detect_forbidden_terms():
    """Scan docs/scripts/backend for banned terms, respecting safe contexts."""
    terms = [
        "tamper-proof", "GPT-5", "unforgeable",
        "blockchain", "100% test success",
    ]
    scan_targets = ["docs/", "scripts/", "backend/", "index.html", "README.md"]
    safe_contexts = [
        "NOT blockchain", "NOT tamper-proof", "not blockchain",
        "not a blockchain", "Not a blockchain",
        "not tamper-proof", "Not blockchain", "Not tamper-proof",
        'say "tamper-evident"', "tamper-evident",
        "BANNED", "never say", "Never say", "never write", "Never write",
        "never use", "Never use", "\u2192", "don't use",
    ]
    skip_names = {"agent_pr_creator", "deep_verify", "agent_evolution"}

    findings = []
    for target_rel in scan_targets:
        target = REPO_ROOT / target_rel
        if not target.exists():
            continue
        files = [target] if target.is_file() else list(target.rglob("*"))
        for fpath in files:
            if not fpath.is_file():
                continue
            if any(sk in fpath.name for sk in skip_names):
                continue
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
            except (OSError, PermissionError):
                continue
            for term in terms:
                for line in text.splitlines():
                    if term.lower() in line.lower():
                        if any(ctx in line for ctx in safe_contexts):
                            continue
                        rel = fpath.relative_to(REPO_ROOT)
                        findings.append(f"'{term}' in {rel}")
                        break  # one finding per term per file
    return findings


# ---------------------------------------------------------------------------
# 3. Manifest sync detection
# ---------------------------------------------------------------------------
def detect_manifest_sync():
    """Compare system_manifest.json version against latest git tag."""
    manifest_path = REPO_ROOT / "system_manifest.json"
    with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
        manifest = json.load(f)
    manifest_version = manifest.get("version", "unknown")

    proc = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        stdout=subprocess.PIPE, text=True, cwd=str(REPO_ROOT),
        stderr=subprocess.DEVNULL, encoding="utf-8", errors="ignore",
    )
    tag_version = proc.stdout.strip().lstrip("v") if proc.returncode == 0 else "unknown"

    return {
        "synced": manifest_version == tag_version,
        "manifest_version": manifest_version,
        "tag_version": tag_version,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    dry_run = "--summary" in sys.argv or "--dry-run" in sys.argv

    print("Agent PR Creator -- scanning...")

    # 1. Stale counters
    stale = detect_stale_counters(dry_run=dry_run)
    if stale["stale"]:
        print(f"  STALE COUNTER: manifest={stale['manifest_count']} "
              f"actual={stale['actual_count']}")
    else:
        print(f"  Counters OK: {stale['manifest_count']} tests")

    # 2. Forbidden terms
    forbidden = detect_forbidden_terms()
    if forbidden:
        print(f"  FORBIDDEN TERMS: {len(forbidden)} finding(s)")
        for f in forbidden:
            print(f"    - {f}")
    else:
        print("  Forbidden terms: clean")

    # 3. Manifest sync
    sync = detect_manifest_sync()
    if not sync["synced"]:
        print(f"  MANIFEST SYNC: manifest={sync['manifest_version']} "
              f"tag={sync['tag_version']}")
    else:
        print(f"  Manifest sync OK: {sync['manifest_version']}")

    # Summary
    issues = stale["stale"] or len(forbidden) > 0 or not sync["synced"]
    if not issues:
        print("No auto-pr needed -- system current")

    return 0


if __name__ == "__main__":
    sys.exit(main())
