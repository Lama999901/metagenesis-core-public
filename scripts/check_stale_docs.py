#!/usr/bin/env python3
"""
MetaGenesis Core — Stale Documentation Checker

Compares critical documentation files against the last merge into main.
If a critical file was NOT updated since the last merge but the codebase
state has changed — flags it as STALE.

Usage:
    python scripts/check_stale_docs.py           # report only
    python scripts/check_stale_docs.py --strict  # exit 1 if any STALE

Logic:
    1. Find last merge commit into main (git log --merges -1)
    2. Get list of ALL files changed since that merge
    3. Check each critical file:
       - Was it changed since last merge? → CURRENT
       - Was it NOT changed but related code WAS changed? → STALE
       - Was it NOT changed and related code also unchanged? → OK (no need)
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Critical files and what code they describe ──────────────────────────────
CRITICAL_FILES = {
    "CLAUDE.md": {
        "tracks": ["scripts/", "backend/progress/", "tests/steward/"],
        "description": "Agent brain — tracks architecture, test count, innovations",
    },
    "AGENTS.md": {
        "tracks": ["scripts/steward_audit.py", "scripts/mg.py", "tests/"],
        "description": "Hard rules for repo agents",
    },
    "llms.txt": {
        "tracks": ["scripts/", "backend/progress/", "system_manifest.json"],
        "description": "LLM-optimized summary of project state",
    },
    "CONTEXT_SNAPSHOT.md": {
        "tracks": ["system_manifest.json", "reports/scientific_claim_index.md"],
        "description": "Live state snapshot",
    },
    "system_manifest.json": {
        "tracks": ["backend/progress/runner.py", "tests/"],
        "description": "Machine-readable canonical state (test_count, active_claims)",
    },
    "README.md": {
        "tracks": ["scripts/", "tests/", "system_manifest.json"],
        "description": "Public-facing documentation",
    },
    "index.html": {
        "tracks": ["system_manifest.json", "tests/", "scripts/"],
        "description": "Site — contains test counters in 11+ places",
    },
    "ppa/README_PPA.md": {
        "tracks": ["scripts/mg_ed25519.py", "scripts/mg_temporal.py", "scripts/mg_sign.py"],
        "description": "Post-PPA innovations tracking",
    },
    "docs/PROTOCOL.md": {
        "tracks": ["scripts/mg.py", "scripts/mg_sign.py", "scripts/mg_temporal.py"],
        "description": "Protocol specification",
    },
    "docs/ARCHITECTURE.md": {
        "tracks": ["backend/progress/", "scripts/mg.py"],
        "description": "Architecture documentation",
    },
    "paper.md": {
        "tracks": ["scripts/", "tests/steward/", "system_manifest.json"],
        "description": "JOSS paper — must reflect current innovation count",
    },
    "reports/known_faults.yaml": {
        "tracks": ["tests/"],
        "description": "Known limitations — test count must match pytest output",
    },
}


# ── Content validation — banned/required strings per file ──────────────────
CONTENT_CHECKS = {
    "CONTRIBUTING.md": {
        "banned": ["223 passed", "295 passed", "ALL 10 TESTS", "3 verification layers"],
        "required": ["511", "ALL 13 TESTS", "5 verification layers"],
    },
    "CITATION.cff": {
        "banned": ["version: 0.2", "version: 0.3", "version: 0.4", "three independent"],
        "required": ["version: 0.5", "five independent", "511"],
    },
    "docs/PROTOCOL.md": {
        "banned": ["MVP v0.2", "MVP v0.3", "MVP v0.4", "Three verification layers", "5 patentable"],
        "required": ["MVP v0.5", "Five verification layers", "8 innovations"],
    },
    "docs/ARCHITECTURE.md": {
        "banned": ["282 tests", "Architecture v0.2", "Three verification layers"],
        "required": ["511 tests", "Five verification layers"],
    },
    "docs/ROADMAP.md": {
        "banned": ["Current version: 0.2", "Current version: 0.3", "Current version: 0.4", "282 adversarial"],
        "required": ["0.5.0", "511 adversarial"],
    },
    "ppa/README_PPA.md": {
        "banned": ["282 tests", "Current state (2026-03-17)"],
        "required": ["511 tests", "8 innovations"],
    },
    "COMMERCIAL.md": {
        "banned": ["5 innovations"],
        "required": ["8 innovations"],
    },
    "SECURITY.md": {
        "banned": ["three independent layers"],
        "required": ["Layer 4", "Layer 5"],
    },
    "demos/open_data_demo_01/README.md": {
        "banned": ["three independent layers"],
        "required": ["five independent layers"],
    },
    "README.md": {
        "banned": ["295 passing", "6 innovations", "7 innovations"],
        "required": ["511", "8 innovations"],
    },
    "paper.md": {
        "banned": ["389 adversarial", "17 March 2026"],
        "required": ["511 adversarial", "18 March 2026"],
    },
    "reports/known_faults.yaml": {
        "banned": ["282 tests", "295 passed", "295 tests"],
        "required": ["511 tests", "511 passed"],
    },
    "CLAUDE.md": {
        "banned": ["10-test proof", "12 counters"],
        "required": ["13-test proof", "8 innovations"],
    },
    "UPDATE_PROTOCOL.md": {
        "banned": ["ALL 10 PASSED", "ALL 10 TESTS PASSED", "v1.0 — 2026-03-16"],
        "required": ["ALL 13 PASSED", "v1.1"],
    },
    "CURSOR_MASTER_PROMPT_v2_3.md": {
        "banned": ["271 tests", "295 tests", "3 verification layers", "MVP v0.2", "ALL 10 TESTS"],
        "required": ["511 tests", "5 verification layers", "MVP v0.5", "ALL 13 TESTS"],
    },
}


def check_content(doc_file, checks):
    """Check file content for banned/required strings. Returns list of issues."""
    full_path = REPO_ROOT / doc_file
    if not full_path.exists():
        return []
    content = full_path.read_text(encoding="utf-8", errors="ignore")
    issues = []
    for banned in checks.get("banned", []):
        if banned.lower() in content.lower():
            issues.append(f"BANNED: '{banned}'")
    for required in checks.get("required", []):
        if required.lower() not in content.lower():
            issues.append(f"MISSING: '{required}'")
    return issues


def run(cmd, cwd=REPO_ROOT):
    """Run shell command, return stdout."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip()


def get_last_merge_commit():
    """Find the last merge commit into main."""
    # Try: last merge commit in history
    sha = run("git log --merges -1 --format=%H main 2>/dev/null")
    if not sha:
        # Fallback: last commit on main
        sha = run("git log -1 --format=%H origin/main 2>/dev/null")
    if not sha:
        # Last resort: initial commit
        sha = run("git rev-list --max-parents=0 HEAD")
    return sha


def get_files_changed_since(commit_sha):
    """Get all files changed since a commit (relative to REPO_ROOT)."""
    output = run(f"git diff --name-only {commit_sha} HEAD")
    if not output:
        return set()
    return set(output.splitlines())


def files_in_tracked_paths(changed_files, tracked_paths):
    """Check if any changed file falls under tracked paths."""
    for changed in changed_files:
        for tracked in tracked_paths:
            if changed.startswith(tracked) or changed == tracked:
                return True
    return False


def check_stale_docs(strict=False):
    """Main check — returns True if all OK, False if any STALE."""
    print("\n" + "═" * 60)
    print("  MetaGenesis Core — Stale Documentation Check")
    print("═" * 60)

    # 1. Find last merge
    last_merge = get_last_merge_commit()
    if not last_merge:
        print("  ⚠ Could not determine last merge commit. Skipping.")
        return True

    merge_msg = run(f"git log -1 --format='%s (%cr)' {last_merge}")
    print(f"\n  Last merge: {last_merge[:8]}  {merge_msg}")

    # 2. Files changed since last merge
    changed = get_files_changed_since(last_merge)
    print(f"  Files changed since merge: {len(changed)}\n")

    # 2b. Content checks (independent of git — always run)
    content_stale = []
    print("\n  Content validation (version strings):")
    for doc_file, checks in CONTENT_CHECKS.items():
        issues = check_content(doc_file, checks)
        if issues:
            content_stale.append((doc_file, issues))
            print(f"  \u274c CONTENT   {doc_file}")
            for issue in issues:
                print(f"               \u2192 {issue}")
        else:
            print(f"  \u2705 OK        {doc_file}")

    # 3. Check each critical file
    stale = []
    current = []
    ok_no_change_needed = []
    all_clean = True  # default; updated after git + content checks

    for doc_file, meta in CRITICAL_FILES.items():
        doc_path = Path(doc_file)
        full_path = REPO_ROOT / doc_path

        # Does the file exist?
        if not full_path.exists():
            print(f"  ⚠  MISSING   {doc_file}")
            continue

        doc_changed = str(doc_file) in changed
        code_changed = files_in_tracked_paths(changed, meta["tracks"])

        if doc_changed:
            # File was updated since last merge → CURRENT
            current.append(doc_file)
            print(f"  ✅ CURRENT   {doc_file}")
        elif code_changed:
            # Code it tracks changed but doc wasn't updated → STALE
            stale.append(doc_file)
            print(f"  ❌ STALE     {doc_file}")
            print(f"               → {meta['description']}")
            # Show which tracked paths changed
            affected = [
                p for p in meta["tracks"]
                if files_in_tracked_paths(changed, [p])
            ]
            for a in affected:
                print(f"               → changed: {a}")
        else:
            # Neither doc nor its tracked code changed → no update needed
            ok_no_change_needed.append(doc_file)
            print(f"  ○  OK        {doc_file}  (no relevant changes)")

    # 4. Summary
    print("\n" + "─" * 60)
    print(f"  CURRENT : {len(current)}")
    print(f"  OK      : {len(ok_no_change_needed)}")
    print(f"  STALE   : {len(stale)}")

    if stale:
        print("\n  ❌ STALE FILES NEED UPDATE:")
        for f in stale:
            print(f"     {f}")
        print()
        if strict:
            print("  EXIT 1 (--strict mode)")
            return False
        else:
            print("  ⚠  Run with --strict to fail CI on stale docs")
            print("  Fix: update stale files to reflect current state")
    else:
        print("\n  ✅ All critical documentation is current.")

    print("═" * 60 + "\n")
    return all_clean


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    ok = check_stale_docs(strict=strict)
    sys.exit(0 if ok else 1)
