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
import io
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Critical files and what code they describe ──────────────────────────────
CRITICAL_FILES = {
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
        "description": "Machine-readable canonical state (test_count, active_claims, version)",
    },
    "index.html": {
        "tracks": ["system_manifest.json", "tests/", "scripts/"],
        "description": "Site — contains test counters in 11+ places",
    },
    "AGENT_TASKS.md": {
        "tracks": ["scripts/agent_research.py"],
        "description": "Agent research task queue",
    },
    "reports/canonical_state.md": {
        "tracks": ["reports/scientific_claim_index.md", "system_manifest.json"],
        "description": "Canonical state record (steward-managed)",
    },
}


# ── Content validation — banned/required strings per file ──────────────────
CONTENT_CHECKS = {
    "llms.txt": {
        "banned": ["595 passing", "595 passed", "16 evolution checks", "Claims: 18", "Domains: 7 ("],
        "required": ["651", "v0.8", "20 active claims", "PHYS-01", "PHYS-02"],
    },
    "CONTEXT_SNAPSHOT.md": {
        "banned": ["595 passing", "595 passed", "v0.6.0", "Domains | 7"],
        "required": ["651", "v0.8"],
    },
    "AGENTS.md": {
        "banned": ["16 agent checks", "17 agent checks"],
        "required": ["651", "v0.8.0", "20 claims", "18 agent checks"],
    },
    "CONTRIBUTING.md": {
        "banned": ["223 passed", "295 passed", "511 passed", "526 passed", "544 passed", "586 passed", "595 passed", "601 passed", "608 passed", "601", "ALL 10 TESTS", "3 verification layers"],
        "required": ["651", "ALL 13 TESTS", "5 verification layers"],
    },
    "CITATION.cff": {
        "banned": ["version: 0.2", "version: 0.3", "version: 0.4", "version: 0.5", "version: 0.6", "version: 0.7", "three independent", "601"],
        "required": ["version: 0.8", "five independent", "651"],
    },
    "docs/PROTOCOL.md": {
        "banned": ["MVP v0.2", "MVP v0.3", "MVP v0.4", "MVP v0.5", "Three verification layers", "5 patentable"],
        "required": ["(MVP) v0.8", "Five verification layers", "8 innovations"],
    },
    "docs/AGENT_SYSTEM.md": {
        "banned": ["15 checks", "15-check", "17 checks", "17-check"],
        "required": ["Level 1", "Level 2", "Level 3", "AGENT-DRIFT-01", "18 checks"],
    },
    "docs/ARCHITECTURE.md": {
        "banned": ["282 tests", "511 tests", "544 tests", "595 tests", "601 tests", "Architecture v0.2", "Three verification layers"],
        "required": ["651 tests", "Five verification layers"],
    },
    "docs/ROADMAP.md": {
        "banned": ["Current version: 0.2", "Current version: 0.3", "Current version: 0.4", "282 adversarial", "595 adversarial", "601 adversarial"],
        "required": ["0.8.0", "651 adversarial"],
    },
    "ppa/README_PPA.md": {
        "banned": ["282 tests", "511 tests", "544 tests", "595 tests", "601 tests", "Current state (2026-03-17)"],
        "required": ["651 tests", "8 innovations"],
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
        "banned": ["295 passing", "511 passing", "526 passing", "544 passing", "595 passing", "601 passing", "601", "6 innovations", "7 innovations", "14 agent checks", "17 agent checks", "The 14 Checks", "The 17 Checks", "ALL 14 CHECKS PASSED", "ALL 17 CHECKS PASSED", "10 automated", "18 verified claims", "17 autonomous", "15 Active Verification"],
        "required": ["651", "8 innovations", "18 agent checks", "The 18 Checks", "ALL 18 CHECKS PASSED", "20 claims", "PHYS-01", "PHYS-02"],
    },
    "index.html": {
        "banned": ["<span>10</span>", "14 active domain claims", "Fourteen</span> claims", "Fifteen</span> claims", "15 active domain claims", "18 active domain claims", "Eighteen</span> claims", "hv\">v0.7.0"],
        "required": ["<span>17</span>", "20 active domain claims", "Twenty</span> claims", "hv\">v0.8.0"],
    },
    "paper.md": {
        "banned": ["389 adversarial", "511 adversarial", "526 adversarial", "544 adversarial", "595 adversarial", "601 adversarial", "17 March 2026"],
        "required": ["651 adversarial", "18 March 2026"],
    },
    "reports/known_faults.yaml": {
        "banned": ["282 tests", "295 passed", "295 tests", "511 tests", "511 passed", "526 tests", "544 tests", "544 passed", "595 tests", "595 passed", "601 tests", "601 passed"],
        "required": ["651 tests", "651 passed"],
    },
    "CLAUDE.md": {
        "banned": ["10-test proof", "12 counters", "15 claims", "16 claims", "17 claims", "18 claims", "19 claims", "601 tests"],
        "required": ["13-test proof", "8 innovations", "20 claims", "651 tests"],
    },
    "UPDATE_PROTOCOL.md": {
        "banned": ["ALL 10 PASSED", "ALL 10 TESTS PASSED", "v1.0 — 2026-03-16"],
        "required": ["ALL 13 PASSED", "v1.1"],
    },
    "CURSOR_MASTER_PROMPT_v2_3.md": {
        "banned": ["271 tests", "295 tests", "526 tests", "544 tests", "595 tests", "601 tests", "3 verification layers", "MVP v0.2", "ALL 10 TESTS", "MVP v0.6"],
        "required": ["651 tests", "5 verification layers", "MVP v0.8", "ALL 13 TESTS"],
    },
    "docs/HOW_TO_ADD_CLAIM.md": {
        "banned": ["ALL 10", "271", "282", "295", "389", "601", "v0.2", "v0.3", "v0.4", "v0.6"],
        "required": ["651", "v0.8"],
    },
    "docs/REAL_DATA_GUIDE.md": {
        "banned": ["ALL 10", "271", "282", "295", "389", "601", "v0.2", "v0.3", "v0.4", "v0.6"],
        "required": ["651", "v0.8"],
    },
    "docs/USE_CASES.md": {
        "banned": ["ALL 10", "271", "282", "295", "389", "601", "v0.2", "v0.3", "v0.4", "v0.6"],
        "required": ["651", "v0.8"],
    },
    "reports/scientific_claim_index.md": {
        "banned": ["282", "295", "601"],
        "required": ["20 claims", "651"],
    },
    "CODE_OF_CONDUCT.md": {
        "banned": [],
        "required": ["Contributor Covenant"],
    },
    "EVOLUTION_LOG.md": {
        "banned": [],
        "required": [],
    },
    "requirements.txt": {
        "banned": [],
        "required": [],
    },
    "reports/AGENT_REPORT_20260318.md": {
        "banned": [],
        "required": [],
    },
    "reports/AGENT_REPORT_20260319.md": {
        "banned": [],
        "required": [],
    },
    "reports/WEEKLY_REPORT_20260318.md": {
        "banned": [],
        "required": [],
    },
    "reports/WEEKLY_REPORT_20260319.md": {
        "banned": [],
        "required": [],
    },
    "reports/phase_registry_v0_1.md": {
        "banned": [],
        "required": [],
    },
    "demos/open_data_demo_01/data/SOURCE.md": {
        "banned": [],
        "required": [],
    },
    "docs/INTEGRATION_GUIDE.md": {
        "banned": [],
        "required": ["MLflow", "DVC", "WandB"],
    },
    "scripts/agent_coverage.py": {
        "banned": [],
        "required": ["Genetor"],
    },
    "scripts/agent_evolve_self.py": {
        "banned": [],
        "required": ["Recursive"],
    },
    "tests/agent/test_agent_drift01.py": {
        "banned": [],
        "required": ["AGENT-DRIFT-01", "TestAgentDrift01"],
    },
    "backend/progress/agent_drift_monitor.py": {
        "banned": [],
        "required": ["AGENT-DRIFT-01"],
    },
    "scripts/mg_policy_gate_policy.json": {
        "banned": [],
        "required": [],
    },
    ".github/workflows/mg_policy_gate.yml": {
        "banned": [],
        "required": [],
    },
    "reports/COVERAGE_REPORT_20260319.md": {
        "banned": [],
        "required": [],
    },
    "reports/SELF_IMPROVEMENT_20260319.md": {
        "banned": [],
        "required": [],
    },
    "scripts/agent_signals.py": {
        "banned": [],
        "required": ["GitHub API", "SIGNALS_"],
    },
    "scripts/agent_chronicle.py": {
        "banned": [],
        "required": ["CHRONICLE_", "system_manifest"],
    },
    "reports/SIGNALS_20260319.md": {
        "banned": [],
        "required": [],
    },
    "reports/CHRONICLE_0_6_0_20260319.md": {
        "banned": [],
        "required": [],
    },
    "scripts/agent_evolution.py": {
        "banned": [],
        "required": ["check_signals", "check_chronicle", "check_pr_review", "check_impact", "v0.8.0"],
    },
    "scripts/agent_impact.py": {
        "banned": [],
        "required": ["parse_update_protocol", "detect_change_type", "check_impact"],
    },
    "tests/test_coverage_boost.py": {
        "banned": [],
        "required": ["generate_key", "run_self_test"],
    },
    "reports/CHRONICLE_0_6_0_20260320.md": {
        "banned": [],
        "required": [],
    },
    "reports/COVERAGE_REPORT_20260320.md": {
        "banned": [],
        "required": [],
    },
    "reports/COVERAGE_REPORT_20260321.md": {
        "banned": [],
        "required": [],
    },
    "reports/COVERAGE_REPORT_20260326.md": {
        "banned": [],
        "required": [],
    },
    "reports/COVERAGE_REPORT_20260329.md": {
        "banned": [],
        "required": [],
    },
    "reports/SELF_IMPROVEMENT_20260320.md": {
        "banned": [],
        "required": [],
    },
    "reports/SELF_IMPROVEMENT_20260321.md": {
        "banned": [],
        "required": [],
    },
    "reports/SELF_IMPROVEMENT_20260326.md": {
        "banned": [],
        "required": [],
    },
    "reports/SELF_IMPROVEMENT_20260329.md": {
        "banned": [],
        "required": [],
    },
    "reports/AGENT_REPORT_20260329.md": {
        "banned": [],
        "required": [],
    },
    "backend/progress/phys01_boltzmann.py": {
        "banned": [],
        "required": ["PHYS-01", "BOLTZMANN_K"],
    },
    "backend/progress/phys02_avogadro.py": {
        "banned": [],
        "required": ["PHYS-02", "AVOGADRO_N"],
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

    all_clean = len(stale) == 0 and len(content_stale) == 0

    if stale:
        print("\n  ❌ STALE FILES NEED UPDATE:")
        for f in stale:
            print(f"     {f}")
        print()
        if strict:
            print("  EXIT 1 (--strict mode)")

    if not stale and not content_stale:
        print("\n  ✅ All critical documentation is current.")

    print("═" * 60 + "\n")

    if not all_clean and strict:
        return False
    return all_clean


if __name__ == "__main__":
    strict = "--strict" in sys.argv
    ok = check_stale_docs(strict=strict)
    sys.exit(0 if ok else 1)
