#!/usr/bin/env python3
"""
MetaGenesis Core — Autonomous PR Creator (Level 3)
Detects auto-fixable issues, creates branch, commits, pushes.
Yehor reviews and merges. Never touches main directly.

Usage:
    python scripts/agent_pr_creator.py            # run all fixers
    python scripts/agent_pr_creator.py --dry-run  # show what would happen
    python scripts/agent_pr_creator.py --summary  # list pending issues
"""

import subprocess
import sys
import re
import io
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/Lama999901/metagenesis-core-public"
STALE_DOCS = REPO_ROOT / "scripts" / "check_stale_docs.py"

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"
TODAY = datetime.now().strftime("%Y%m%d")


# ── Helpers ─────────────────────────────────────────────────────────────────
def run(cmd):
    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, text=True,
                       cwd=REPO_ROOT, env=env, encoding="utf-8", errors="replace",
                       stderr=subprocess.DEVNULL)
    return r.stdout.strip(), r.returncode


def git_is_clean():
    out, _ = run("git status --porcelain")
    return out == ""


def git_create_branch(branch):
    run("git checkout main")
    run("git pull --no-rebase")
    run(f"git checkout -b {branch}")


def git_commit_push(branch, message, files):
    for f in files:
        run(f'git add "{f}"')
    run(f'git commit -m "{message}"')
    run(f"git push origin {branch}")
    run("git checkout main")
    print(f"\n{G}  PR ready:{X} {REPO_URL}/pull/new/{branch}")


# ── Fix 1: Unwatched files ─────────────────────────────────────────────────
def fix_watchlist(dry_run=False):
    out, _ = run("python scripts/auto_watchlist_scan.py")
    warnings = re.findall(r"WARNING:\s+(\S+)\s+is NOT", out)
    if not warnings:
        return [], 0

    print(f"  {Y}→{X} {len(warnings)} unwatched files found")
    for w in warnings:
        print(f"    {w}")

    if dry_run:
        return [], len(warnings)

    # Append entries to CONTENT_CHECKS in check_stale_docs.py
    content = STALE_DOCS.read_text(encoding="utf-8")
    # Find last entry before closing brace of CONTENT_CHECKS
    insert_entries = ""
    for w in warnings:
        entry = f'    "{w}": {{\n        "banned": [],\n        "required": [],\n    }},\n'
        if w not in content:
            insert_entries += entry

    if not insert_entries:
        return [], 0

    # Insert before the closing } of CONTENT_CHECKS (last lone "}")
    # Find the pattern: last entry's closing },\n}
    idx = content.rfind("\n}\n\n")
    if idx == -1:
        idx = content.rfind("\n}\n")
    if idx == -1:
        print(f"  {R}ERROR: could not find CONTENT_CHECKS end{X}")
        return [], 0

    content = content[:idx] + "\n" + insert_entries + content[idx:]
    STALE_DOCS.write_text(content, encoding="utf-8")

    return ["scripts/check_stale_docs.py"], len(warnings)


# ── Fix 2: Stale counters ──────────────────────────────────────────────────
def fix_stale_counters(dry_run=False):
    out, code = run("python scripts/check_stale_docs.py --strict")
    if code == 0:
        return [], 0

    # Parse BANNED lines: "BANNED: '544 passing'" from file context
    banned_hits = re.findall(r"CONTENT\s+(\S+)\s*\n\s*→ BANNED: '([^']+)'", out)
    if not banned_hits:
        # Try alternate parse: ❌ CONTENT   file\n  → BANNED: 'text'
        lines = out.splitlines()
        banned_hits = []
        current_file = None
        for line in lines:
            m = re.search(r"CONTENT\s+(\S+)", line)
            if m:
                current_file = m.group(1)
            m = re.search(r"BANNED: '([^']+)'", line)
            if m and current_file:
                banned_hits.append((current_file, m.group(1)))

    if not banned_hits:
        return [], 0

    print(f"  {Y}→{X} {len(banned_hits)} stale counters found")
    changed = set()

    # Only fix pure numeric/version counter swaps
    counter_re = re.compile(r'^[\d]+|v[\d.]+')

    for filepath, banned_text in banned_hits:
        if not counter_re.match(banned_text.split()[0]):
            continue
        print(f"    {filepath}: '{banned_text}'")
        if dry_run:
            continue

        full = REPO_ROOT / filepath
        if not full.exists():
            continue
        text = full.read_text(encoding="utf-8")
        if banned_text in text:
            # We don't auto-replace without knowing the correct value
            # Just flag it — this keeps the agent safe
            changed.add(filepath)

    return list(changed), len(banned_hits)


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    dry_run = "--dry-run" in sys.argv
    summary = "--summary" in sys.argv

    print(f"\n{B}{C}══ AUTONOMOUS PR CREATOR — Level 3 ══{X}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Scan for issues
    wl_files, wl_count = fix_watchlist(dry_run=True)
    sc_files, sc_count = fix_stale_counters(dry_run=True)

    total = wl_count + sc_count

    if summary:
        if total == 0:
            print(f"  {G}System current — no auto-PR needed{X}")
        else:
            print(f"  {Y}{total} auto-fixable issues: {wl_count} unwatched, {sc_count} stale{X}")
        return 0

    if dry_run:
        print(f"\n  {C}DRY RUN — {total} issues detected, no changes made{X}")
        return 0

    if total == 0:
        print(f"  {G}System current — no auto-PR needed{X}")
        return 0

    if not git_is_clean():
        print(f"  {R}ERROR: working directory not clean — commit or stash first{X}")
        return 1

    # Fix 1: Watchlist
    if wl_count > 0:
        branch = f"fix/auto-watchlist-{TODAY}"
        print(f"\n  {C}→ Creating branch: {branch}{X}")
        git_create_branch(branch)
        fix_watchlist(dry_run=False)
        git_commit_push(branch,
                        f"fix: add {wl_count} unwatched files to watchlist (auto)",
                        ["scripts/check_stale_docs.py"])
        return 0

    # Fix 2: Stale counters
    if sc_count > 0:
        branch = f"fix/auto-stale-{TODAY}"
        print(f"\n  {C}→ Creating branch: {branch}{X}")
        git_create_branch(branch)
        changed, _ = fix_stale_counters(dry_run=False)
        if changed:
            git_commit_push(branch,
                            f"fix: update {sc_count} stale counters (auto)",
                            changed)
        else:
            print(f"  {Y}Stale counters detected but no safe auto-fix available{X}")
            run("git checkout main")
            run(f"git branch -D {branch}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
