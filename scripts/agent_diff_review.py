#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Diff Review (Structural AST Analysis)
===============================================================
Analyzes the last commit for structural quality: test coverage references,
forbidden terms, documentation gaps, and manifest consistency.

stdlib only. No LLM. No external dependencies.

Usage:
    python scripts/agent_diff_review.py             # full check
    python scripts/agent_diff_review.py --summary   # one-line summary
"""

import ast
import json
import os
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

# ── Colors ──
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

def ok(msg):  print(f"  {GREEN}✅{RESET} {msg}")
def err(msg): print(f"  {RED}❌{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠ {RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")

def section(title):
    print(f"\n{BOLD}{CYAN}══ {title} ══{RESET}")


def run(cmd, cwd=REPO_ROOT):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                       text=True, cwd=cwd, env=env, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.returncode


FORBIDDEN_TERMS = ["tamper-proof", "unforgeable", "blockchain", "GPT-5"]


def get_changed_files():
    """Get files changed in last commit."""
    out, code = run("git diff --name-only HEAD~1 HEAD")
    if not out:
        out, code = run("git diff --name-only origin/main...HEAD")
    if not out:
        return []
    return [f.strip() for f in out.splitlines() if f.strip()]


def check_test_references(changed_files):
    """Check 1-2: For changed .py in backend/progress/ or scripts/, check test references."""
    section("TEST REFERENCES — Coverage Audit")

    source_files = [f for f in changed_files
                    if f.endswith(".py")
                    and (f.startswith("backend/progress/") or f.startswith("scripts/"))
                    and not f.startswith("tests/")]

    if not source_files:
        ok("No source files changed — skip")
        return []

    warnings = []
    tests_dir = REPO_ROOT / "tests"

    for src in source_files:
        stem = Path(src).stem
        # Search for any test file referencing this module
        found = False
        for test_file in tests_dir.rglob("test_*.py"):
            try:
                content = test_file.read_text(encoding="utf-8", errors="ignore")
                if stem in content:
                    found = True
                    break
            except:
                pass

        if found:
            ok(f"{src} → test reference found")
        else:
            warn(f"{src} → no test file references '{stem}'")
            warnings.append(src)

    return warnings


def check_forbidden_terms(changed_files):
    """Check 3: Scan changed .py for forbidden terms."""
    section("FORBIDDEN TERMS — Heresy Scan")

    py_files = [f for f in changed_files if f.endswith(".py")]
    if not py_files:
        ok("No .py files changed — skip")
        return []

    errors = []
    for f in py_files:
        fpath = REPO_ROOT / f
        if not fpath.exists():
            continue
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore").lower()
            for term in FORBIDDEN_TERMS:
                if term.lower() in content:
                    # Check if in safe context (comments about banning, etc.)
                    lines = content.splitlines()
                    for line in lines:
                        if term.lower() in line and not any(
                            ctx in line for ctx in ["banned", "forbidden", "never", "don't", "→"]
                        ):
                            err(f"FORBIDDEN: '{term}' in {f}")
                            errors.append((f, term))
                            break
        except:
            pass

    if not errors:
        ok("No forbidden terms in changed files")

    return errors


def check_docs_updated(changed_files):
    """Check 4: If core code changed, warn if paper.md not updated."""
    section("DOCUMENTATION GAP — Paper Sync")

    core_changed = any(
        f.startswith("backend/progress/") or f == "scripts/mg.py"
        for f in changed_files
    )
    paper_changed = "paper.md" in changed_files

    if not core_changed:
        ok("No core code changed — skip")
        return False

    if paper_changed:
        ok("Core code + paper.md both updated")
        return False
    else:
        warn("Core code changed but paper.md not in diff (advisory)")
        return True  # warning, not error


def check_manifest_test_count():
    """Check 5: Manifest test_count vs actual test file count."""
    section("MANIFEST SYNC — Test Count Audit")

    manifest_path = REPO_ROOT / "system_manifest.json"
    if not manifest_path.exists():
        err("system_manifest.json not found")
        return True  # error

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_count = manifest.get("test_count", 0)

    # Count actual test files
    test_files = list((REPO_ROOT / "tests").rglob("test_*.py"))

    # Parse each to count test functions
    total_funcs = 0
    for tf in test_files:
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    total_funcs += 1
        except:
            pass

    info(f"manifest test_count: {manifest_count}")
    info(f"test functions found: {total_funcs}")

    diff = abs(manifest_count - total_funcs)
    if diff > 20:
        err(f"Mismatch > 20: manifest={manifest_count}, actual={total_funcs}")
        return True  # error
    else:
        ok(f"Manifest within tolerance (diff={diff})")
        return False


def main():
    summary_only = "--summary" in sys.argv

    changed_files = get_changed_files()

    if summary_only:
        if not changed_files:
            print("no diff | 0 issues")
            return 0
        # Quick scan
        py_files = [f for f in changed_files if f.endswith(".py")]
        errors = 0
        for f in py_files:
            fpath = REPO_ROOT / f
            if fpath.exists():
                content = fpath.read_text(encoding="utf-8", errors="ignore").lower()
                for term in FORBIDDEN_TERMS:
                    if term.lower() in content:
                        errors += 1
        print(f"{len(changed_files)} files | {len(py_files)} .py | {errors} forbidden")
        return 1 if errors > 0 else 0

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}  MetaGenesis Core — Structural Diff Review{RESET}")
    info(f"Analyzing {len(changed_files)} changed files")
    print(f"{BOLD}{'═' * 60}{RESET}")

    if not changed_files:
        info("No diff available — nothing to review")
        return 0

    has_errors = False

    # Check 1-2: Test references
    test_warnings = check_test_references(changed_files)

    # Check 3: Forbidden terms
    forbidden_errors = check_forbidden_terms(changed_files)
    if forbidden_errors:
        has_errors = True

    # Check 4: Docs gap
    check_docs_updated(changed_files)

    # Check 5: Manifest sync
    manifest_error = check_manifest_test_count()
    if manifest_error:
        has_errors = True

    # Summary
    section("SUMMARY")
    print(f"  Changed files: {len(changed_files)}")
    print(f"  Test warnings: {len(test_warnings)}")
    print(f"  Forbidden terms: {len(forbidden_errors)}")
    print(f"  Manifest error: {'YES' if manifest_error else 'no'}")

    if has_errors:
        print(f"\n{RED}  ❌ ISSUES FOUND — review required{RESET}")
        return 1
    else:
        print(f"\n{GREEN}  ✅ DIFF REVIEW PASSED{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
