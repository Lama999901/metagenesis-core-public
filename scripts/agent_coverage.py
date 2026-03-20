#!/usr/bin/env python3
"""
MetaGenesis Core -- Code Coverage Analyst (Genetor Analysis)
=============================================================
Runs pytest-cov, parses JSON output, finds uncovered functions,
cross-references AGENT_TASKS.md to avoid duplicate suggestions.

The Genetor probes every gene-sequence of the Machine Spirit's code,
seeking dormant logic untouched by the rites of verification.

Usage:
    python scripts/agent_coverage.py             # full analysis + report
    python scripts/agent_coverage.py --summary   # one-line summary
"""

import subprocess
import sys
import io
import os
import re
import json
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent

# -- Colors ----------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(msg):   print(f"  {GREEN}+{RESET} {msg}")
def err(msg):  print(f"  {RED}x{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}!{RESET} {msg}")
def info(msg): print(f"  {CYAN}>{RESET} {msg}")


def run(cmd, cwd=REPO_ROOT):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       cwd=cwd, env=env, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.returncode


def extract_functions(filepath):
    """Extract function definitions with their line numbers from a Python file."""
    functions = []
    try:
        lines = filepath.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return functions

    for i, line in enumerate(lines, 1):
        m = re.match(r'^(\s*)def\s+(\w+)\s*\(', line)
        if m:
            indent = len(m.group(1))
            name = m.group(2)
            # Find the end of this function (next def at same or lower indent, or EOF)
            end_line = len(lines)
            for j in range(i, len(lines)):
                next_line = lines[j]
                nm = re.match(r'^(\s*)def\s+\w+\s*\(', next_line)
                if nm and len(nm.group(1)) <= indent:
                    end_line = j  # 0-indexed, so line j+1
                    break
            functions.append({
                "name": name,
                "start": i,
                "end": end_line,
                "indent": indent,
            })
    return functions


def get_function_coverage(functions, missing_lines, executed_lines):
    """For each function, compute coverage percentage."""
    results = []
    all_covered = set(executed_lines)
    all_missing = set(missing_lines)

    for func in functions:
        func_lines = set(range(func["start"], func["end"] + 1))
        # Only count lines that appear in either executed or missing (actual code lines)
        func_code_lines = func_lines & (all_covered | all_missing)
        if not func_code_lines:
            continue
        func_missing = func_code_lines & all_missing
        func_covered = func_code_lines & all_covered
        total = len(func_code_lines)
        covered = len(func_covered)
        pct = (covered / total * 100) if total > 0 else 0

        results.append({
            "name": func["name"],
            "start": func["start"],
            "end": func["end"],
            "total_lines": total,
            "covered_lines": covered,
            "missing_lines": len(func_missing),
            "coverage_pct": round(pct, 1),
        })
    return results


def load_pending_tasks():
    """Load PENDING task titles from AGENT_TASKS.md to avoid duplicates."""
    tasks_path = REPO_ROOT / "AGENT_TASKS.md"
    if not tasks_path.exists():
        return []
    content = tasks_path.read_text(encoding="utf-8", errors="ignore")
    titles = []
    for line in content.splitlines():
        if "PENDING" in line:
            # Look for title on previous or nearby lines
            pass
    # Parse task blocks
    blocks = re.split(r"^### (TASK-\d+)", content, flags=re.MULTILINE)
    pending_titles = []
    i = 1
    while i < len(blocks) - 1:
        task_id = blocks[i]
        body = blocks[i + 1]
        if "PENDING" in body:
            m = re.search(r'\*\*Title:\*\*\s*(.+)', body)
            if m:
                pending_titles.append(m.group(1).strip())
        i += 2
    return pending_titles


def analyze():
    """Main analysis: run pytest-cov, parse, find gaps, write report."""
    summary_only = "--summary" in sys.argv

    cov_json_path = REPO_ROOT / "coverage.json"

    # Step 1: Run pytest with coverage
    if not summary_only:
        print(f"\n{BOLD}{CYAN}== GENETOR COVERAGE ANALYSIS =={RESET}")
        info("Initiating coverage scan of the Machine Spirit's gene-code...")

    cmd = ("python -m pytest tests/ "
           "--cov=backend --cov=scripts "
           "--cov-report=json --cov-report=term-missing "
           "-q --tb=no")
    out, code = run(cmd)

    if not cov_json_path.exists():
        err("coverage.json not generated -- pytest-cov may not be installed")
        if summary_only:
            print("FAIL: no coverage data")
        return 1

    # Step 2: Parse coverage.json
    try:
        cov_data = json.loads(cov_json_path.read_text(encoding="utf-8"))
    except Exception as e:
        err(f"Failed to parse coverage.json: {e}")
        return 1

    files_data = cov_data.get("files", {})
    totals = cov_data.get("totals", {})
    overall_pct = totals.get("percent_covered", 0)

    if not summary_only:
        info(f"Overall coverage: {overall_pct:.1f}%")
        info(f"Files analyzed: {len(files_data)}")

    # Step 3: Analyze per-function coverage
    zero_coverage = []    # functions with 0% coverage
    low_coverage = []     # functions with < 50% coverage
    files_below_50 = []   # files with < 50% overall coverage

    for filepath_str, file_info in files_data.items():
        file_pct = file_info.get("summary", {}).get("percent_covered", 100)
        missing = file_info.get("missing_lines", [])
        executed = file_info.get("executed_lines", [])

        if file_pct < 50:
            files_below_50.append((filepath_str, round(file_pct, 1)))

        if not missing:
            continue

        # Read source and extract functions
        abs_path = REPO_ROOT / filepath_str
        if not abs_path.exists():
            continue

        functions = extract_functions(abs_path)
        func_results = get_function_coverage(functions, missing, executed)

        for fr in func_results:
            entry = {
                "file": filepath_str,
                "function": fr["name"],
                "lines": f"{fr['start']}-{fr['end']}",
                "coverage_pct": fr["coverage_pct"],
                "total_lines": fr["total_lines"],
            }
            if fr["coverage_pct"] == 0:
                zero_coverage.append(entry)
            elif fr["coverage_pct"] < 50:
                low_coverage.append(entry)

    # Step 4: Cross-reference AGENT_TASKS.md
    pending_titles = load_pending_tasks()
    pending_lower = [t.lower() for t in pending_titles]

    # Step 5: Build suggestions (avoid duplicates)
    suggestions = []
    for zc in zero_coverage:
        title = f"Write tests for {zc['function']} in {Path(zc['file']).name}"
        # Check if similar task already exists
        if any(zc['function'].lower() in pt for pt in pending_lower):
            continue
        if any(title.lower() in pt for pt in pending_lower):
            continue
        suggestions.append({
            "title": title,
            "file": zc["file"],
            "function": zc["function"],
        })

    # Step 6: Write report
    today = datetime.now().strftime("%Y%m%d")
    report_path = REPO_ROOT / "reports" / f"COVERAGE_REPORT_{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Coverage Report {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"> Generated by `scripts/agent_coverage.py` -- Genetor Analysis",
        f"> The Genetor probes the Machine Spirit's untested gene-sequences.",
        "",
        "## Coverage Summary",
        "",
        f"- **Overall coverage:** {overall_pct:.1f}%",
        f"- **Files analyzed:** {len(files_data)}",
        f"- **Files below 50%:** {len(files_below_50)}",
        f"- **Zero-coverage functions:** {len(zero_coverage)}",
        f"- **Low-coverage functions (<50%):** {len(low_coverage)}",
        "",
    ]

    if files_below_50:
        lines.append("### Files Below 50% Coverage")
        lines.append("")
        lines.append("| File | Coverage % |")
        lines.append("|------|-----------|")
        for f, pct in sorted(files_below_50, key=lambda x: x[1]):
            lines.append(f"| `{f}` | {pct}% |")
        lines.append("")

    if zero_coverage:
        lines.append("## Zero-Coverage Functions")
        lines.append("")
        lines.append("| File | Function | Lines |")
        lines.append("|------|----------|-------|")
        for zc in sorted(zero_coverage, key=lambda x: x["file"]):
            lines.append(f"| `{zc['file']}` | `{zc['function']}` | {zc['lines']} |")
        lines.append("")

    if low_coverage:
        lines.append("## Low-Coverage Functions (< 50%)")
        lines.append("")
        lines.append("| File | Function | Coverage % |")
        lines.append("|------|----------|-----------|")
        for lc in sorted(low_coverage, key=lambda x: x["coverage_pct"]):
            lines.append(f"| `{lc['file']}` | `{lc['function']}` | {lc['coverage_pct']}% |")
        lines.append("")

    if suggestions:
        lines.append("## Suggested Tasks")
        lines.append("")
        lines.append("Tasks for zero-coverage functions (not already in AGENT_TASKS.md):")
        lines.append("")
        for s in suggestions[:20]:  # cap at 20 suggestions
            lines.append(f"- **{s['title']}** -- `{s['file']}`")
        lines.append("")

    if not suggestions and not zero_coverage:
        lines.append("## Suggested Tasks")
        lines.append("")
        lines.append("No zero-coverage functions found -- the Machine Spirit's gene-code is well-tested.")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    # Step 7: Print summary
    if not summary_only:
        print()
        if zero_coverage:
            warn(f"{len(zero_coverage)} zero-coverage functions found")
        if low_coverage:
            warn(f"{len(low_coverage)} low-coverage functions (<50%)")
        if suggestions:
            info(f"{len(suggestions)} new task suggestions generated")
        ok(f"Report written: {report_path.relative_to(REPO_ROOT)}")
        print()

    # Step 8: Clean up coverage.json
    try:
        cov_json_path.unlink()
    except Exception:
        pass

    # Summary mode output
    if summary_only:
        print(f"Coverage {overall_pct:.1f}% | {len(zero_coverage)} zero-cov | {len(low_coverage)} low-cov | {len(files_data)} files")

    # Step 9: Exit code
    return 0 if overall_pct > 60 else 1


if __name__ == "__main__":
    sys.exit(analyze())
