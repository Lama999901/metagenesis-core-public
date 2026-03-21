#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Impact Analyzer (Dependency Tracker)
==============================================================
Reads UPDATE_PROTOCOL.md to understand which files must be updated
when different types of changes occur. Then checks git diff to see
if all required files were actually updated.

Usage:
    python scripts/agent_impact.py                    # full check against last commit
    python scripts/agent_impact.py --summary          # one-line summary
    python scripts/agent_impact.py --verify-last-commit  # same as default
"""

import subprocess
import sys
import io
import re
import os
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent


def run(cmd, cwd=REPO_ROOT):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       cwd=cwd, env=env, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.returncode


# Dependency rules derived from UPDATE_PROTOCOL.md
DEPENDENCY_RULES = {
    "new_claim": {
        "trigger_paths": ["backend/progress/"],
        "trigger_description": "New claim implementation added",
        "required_files": [
            "backend/progress/runner.py",
            "reports/scientific_claim_index.md",
            "system_manifest.json",
            "index.html",
            "README.md",
            "AGENTS.md",
            "llms.txt",
            "CONTEXT_SNAPSHOT.md",
        ],
    },
    "new_tests": {
        "trigger_paths": ["tests/"],
        "trigger_description": "Test files added or changed",
        "required_files": [
            "system_manifest.json",
            "README.md",
            "AGENTS.md",
            "llms.txt",
            "index.html",
        ],
    },
    "new_layer": {
        "trigger_paths": ["scripts/mg_"],
        "trigger_description": "New verification layer script added",
        "required_files": [
            "scripts/mg.py",
            "docs/PROTOCOL.md",
            "docs/ARCHITECTURE.md",
            "README.md",
            "SECURITY.md",
            "CLAUDE.md",
            "index.html",
        ],
    },
    "new_release": {
        "trigger_paths": ["system_manifest.json"],
        "trigger_description": "Version changed in system_manifest.json",
        "required_files": [
            "README.md",
            "llms.txt",
            "CONTEXT_SNAPSHOT.md",
            "index.html",
        ],
    },
    "new_innovation": {
        "trigger_paths": ["ppa/"],
        "trigger_description": "Patent/innovation file changed",
        "required_files": [
            "ppa/README_PPA.md",
            "COMMERCIAL.md",
            "README.md",
            "CLAUDE.md",
            "system_manifest.json",
        ],
    },
}


def parse_update_protocol():
    """Read UPDATE_PROTOCOL.md and return the dependency rules.

    Currently returns hardcoded rules derived from the protocol.
    Future: parse the markdown directly for dynamic updates.
    """
    return DEPENDENCY_RULES


def detect_change_type(changed_files):
    """Given list of changed files, detect the change type(s).

    Returns list of matching change types (can be multiple).
    """
    rules = parse_update_protocol()
    detected = []

    for change_type, rule in rules.items():
        for trigger in rule["trigger_paths"]:
            for f in changed_files:
                if f.startswith(trigger) or trigger in f:
                    # For new_claim: must be a NEW .py file in backend/progress/
                    if change_type == "new_claim":
                        if f.endswith(".py") and f.startswith("backend/progress/") and f != "backend/progress/runner.py":
                            detected.append(change_type)
                            break
                    # For new_tests: must be test_*.py files
                    elif change_type == "new_tests":
                        if f.endswith(".py") and "test_" in Path(f).name:
                            detected.append(change_type)
                            break
                    else:
                        detected.append(change_type)
                        break

    return list(set(detected))


def check_impact(changed_files):
    """Run full impact analysis.

    Returns dict with:
        change_types: list of detected change types
        missing: list of files that should have been updated but weren't
        updated: list of required files that were correctly updated
        total_required: total number of required files
    """
    change_types = detect_change_type(changed_files)

    if not change_types:
        return {
            "change_types": [],
            "missing": [],
            "updated": [],
            "total_required": 0,
        }

    # Collect all required files from all detected change types
    required = set()
    rules = parse_update_protocol()
    for ct in change_types:
        required.update(rules[ct]["required_files"])

    # Remove files that were themselves the trigger (they're already changed)
    changed_set = set(changed_files)

    missing = []
    updated = []
    for req in sorted(required):
        if req in changed_set or any(c.startswith(req) for c in changed_set):
            updated.append(req)
        else:
            missing.append(req)

    return {
        "change_types": change_types,
        "missing": missing,
        "updated": updated,
        "total_required": len(required),
    }


def main():
    summary_only = "--summary" in sys.argv

    # Get changed files from last commit
    out, code = run("git diff --name-only HEAD~1 HEAD 2>/dev/null")
    if not out:
        # Try diff against main
        out, code = run("git diff --name-only origin/main...HEAD 2>/dev/null")

    if not out:
        if summary_only:
            print("no diff available | advisory")
        else:
            print("No diff available -- nothing to analyze.")
        return 0

    changed_files = [f.strip() for f in out.splitlines() if f.strip()]
    result = check_impact(changed_files)

    if summary_only:
        if not result["change_types"]:
            print(f"{len(changed_files)} files changed | no impact rules triggered")
        elif result["missing"]:
            print(f"{','.join(result['change_types'])} | {len(result['missing'])} MISSING: {', '.join(result['missing'][:3])}")
        else:
            print(f"{','.join(result['change_types'])} | {len(result['updated'])}/{result['total_required']} files updated | PASS")
        return 0

    # Full output
    print(f"\nMetaGenesis Core -- Dependency Impact Analysis")
    print(f"{'=' * 50}")
    print(f"Changed files: {len(changed_files)}")

    if not result["change_types"]:
        print(f"\nNo impact rules triggered -- routine change.")
        return 0

    print(f"\nDetected change types: {', '.join(result['change_types'])}")

    if result["updated"]:
        print(f"\nUpdated ({len(result['updated'])}):")
        for f in result["updated"]:
            print(f"  + {f}")

    if result["missing"]:
        print(f"\nMISSING ({len(result['missing'])}):")
        for f in result["missing"]:
            print(f"  ! {f}")
        print(f"\nResult: {len(result['missing'])} files need updating")
    else:
        print(f"\nAll {result['total_required']} required files updated. PASS")

    return 0  # Advisory -- never fails


if __name__ == "__main__":
    sys.exit(main())
