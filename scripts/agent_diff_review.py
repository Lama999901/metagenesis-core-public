#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Diff Review (AST Structural Diff)
============================================================
Performs AST-level structural analysis of changed Python files
to detect logic regressions: removed functions, changed signatures,
missing return statements, and broken hash chains.

Usage:
    python scripts/agent_diff_review.py              # full review
    python scripts/agent_diff_review.py --summary    # one-line summary
"""

import ast
import subprocess
import sys
import io
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
    r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                       text=True, cwd=cwd, env=env, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.returncode


def get_changed_py_files():
    """Get Python files changed in the last commit."""
    out, _ = run("git diff --name-only HEAD~1 HEAD 2>/dev/null")
    if not out:
        # No commits to compare -- check staged/unstaged
        out, _ = run("git diff --name-only HEAD 2>/dev/null")
    if not out:
        return []
    return [f for f in out.splitlines() if f.endswith(".py")]


def extract_structure(source):
    """Extract function/class names and their signatures from Python source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    structure = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            has_return = any(isinstance(n, ast.Return) for n in ast.walk(node))
            structure[node.name] = {
                "type": "function",
                "args": args,
                "has_return": has_return,
                "lineno": node.lineno,
            }
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            structure[node.name] = {
                "type": "class",
                "methods": methods,
                "lineno": node.lineno,
            }
    return structure


def get_old_source(filepath):
    """Get the previous version of a file from git."""
    out, code = run(f"git show HEAD~1:{filepath} 2>/dev/null")
    if code != 0:
        return None
    return out


def review_file(filepath):
    """Review a single file for structural regressions."""
    issues = []
    full_path = REPO_ROOT / filepath

    # Check current file parses
    if not full_path.exists():
        return issues  # file was deleted, not a regression per se

    try:
        current_source = full_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return issues

    current_struct = extract_structure(current_source)
    if current_struct is None:
        issues.append(f"{filepath}: syntax error in current version")
        return issues

    # Compare with previous version
    old_source = get_old_source(filepath)
    if old_source is None:
        return issues  # new file, nothing to compare

    old_struct = extract_structure(old_source)
    if old_struct is None:
        return issues  # old version had syntax errors, improvement

    # Check for removed functions/classes
    for name, info in old_struct.items():
        if name not in current_struct:
            if not name.startswith("_"):
                issues.append(f"{filepath}: public {info['type']} '{name}' was removed")
        elif info["type"] == "function" and current_struct[name]["type"] == "function":
            old_args = info["args"]
            new_args = current_struct[name]["args"]
            if old_args != new_args:
                issues.append(
                    f"{filepath}: '{name}' signature changed: "
                    f"({', '.join(old_args)}) -> ({', '.join(new_args)})"
                )
            # Check return removed
            if info["has_return"] and not current_struct[name]["has_return"]:
                issues.append(f"{filepath}: '{name}' lost its return statement")

    # Check hash chain integrity for claim files
    if "backend/progress/" in filepath and "_hash_step" in current_source:
        if "trace_root_hash" not in current_source:
            issues.append(f"{filepath}: has _hash_step but missing trace_root_hash")
        if "execution_trace" not in current_source:
            issues.append(f"{filepath}: has _hash_step but missing execution_trace")

    return issues


def main():
    summary_only = "--summary" in sys.argv

    changed = get_changed_py_files()
    all_issues = []

    for f in changed:
        issues = review_file(f)
        all_issues.extend(issues)

    if summary_only:
        if all_issues:
            print(f"DIFF_FAIL | {len(all_issues)} issues in {len(changed)} files")
        else:
            print(f"DIFF_PASS | {len(changed)} files reviewed, no structural regressions")
        return 1 if all_issues else 0

    # Full output
    print(f"Agent Diff Review — {len(changed)} Python files changed")
    print("=" * 50)

    if not changed:
        print("No Python files changed in last commit.")
        print("\nDIFF REVIEW PASSED")
        return 0

    for f in changed:
        print(f"  reviewed: {f}")

    if all_issues:
        print(f"\n{len(all_issues)} issue(s) found:")
        for issue in all_issues:
            print(f"  !! {issue}")
        print("\nDIFF REVIEW: ISSUES FOUND")
        return 1
    else:
        print("\nNo structural regressions detected.")
        print("\nDIFF REVIEW PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())
