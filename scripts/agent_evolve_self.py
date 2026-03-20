#!/usr/bin/env python3
"""
MetaGenesis Core -- Recursive Self-Improvement Analyst
=======================================================
Reads all agent reports, analyzes patterns.json, audits
agent_research.py handlers, and produces actionable
improvement recommendations.

The Machine Spirit contemplates its own reflection --
seeking inefficiencies in its own rituals of analysis.

Usage:
    python scripts/agent_evolve_self.py             # full analysis + report
    python scripts/agent_evolve_self.py --summary   # one-line summary
"""

import subprocess
import sys
import io
import os
import re
import json
from pathlib import Path
from datetime import datetime, timedelta

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


def parse_report_date(filename):
    """Extract date from report filename like AGENT_REPORT_20260319.md."""
    m = re.search(r'(\d{8})', filename)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y%m%d")
        except ValueError:
            pass
    return None


def analyze_reports():
    """Read all AGENT_REPORT and WEEKLY_REPORT files, extract themes."""
    reports_dir = REPO_ROOT / "reports"
    agent_reports = sorted(reports_dir.glob("AGENT_REPORT_*.md"))
    weekly_reports = sorted(reports_dir.glob("WEEKLY_REPORT_*.md"))

    all_reports = []

    for rpath in list(agent_reports) + list(weekly_reports):
        try:
            content = rpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        date = parse_report_date(rpath.name)
        # Extract section headers
        headers = re.findall(r'^#{1,3}\s+(.+)', content, re.MULTILINE)
        # Extract task IDs mentioned
        task_ids = re.findall(r'TASK-\d+', content)
        # Extract key findings (bulleted items under ### headers)
        findings = re.findall(r'^- (.+)', content, re.MULTILINE)
        # Extract file paths mentioned
        file_paths = re.findall(r'`([a-zA-Z_/]+\.(?:py|md|json|yaml))`', content)

        all_reports.append({
            "path": str(rpath.name),
            "date": date,
            "headers": headers,
            "task_ids": list(set(task_ids)),
            "findings_count": len(findings),
            "findings_sample": findings[:10],
            "files_mentioned": list(set(file_paths)),
            "line_count": len(content.splitlines()),
        })

    return all_reports


def analyze_patterns():
    """Load patterns.json and find patterns with count >= 2 but no fix_hint."""
    patterns_path = REPO_ROOT / ".agent_memory" / "patterns.json"
    if not patterns_path.exists():
        return [], []

    try:
        patterns = json.loads(patterns_path.read_text(encoding="utf-8"))
    except Exception:
        return [], []

    unaddressed = []
    all_patterns = []
    for key, data in patterns.items():
        count = data.get("count", 0)
        hint = data.get("fix_hint", "")
        all_patterns.append({
            "pattern": key,
            "count": count,
            "has_hint": bool(hint),
            "first_seen": data.get("first_seen", ""),
            "last_seen": data.get("last_seen", ""),
        })
        if count >= 2 and not hint:
            unaddressed.append({
                "pattern": key,
                "count": count,
                "first_seen": data.get("first_seen", ""),
            })

    return all_patterns, unaddressed


def analyze_handlers():
    """Analyze agent_research.py handlers: count lines, flag shallow/complex."""
    research_path = REPO_ROOT / "scripts" / "agent_research.py"
    if not research_path.exists():
        return []

    try:
        content = research_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    lines = content.splitlines()
    # Find all execute_task_NNN functions
    handlers = []
    handler_defs = []
    for i, line in enumerate(lines):
        m = re.match(r'^def (execute_task_\d+)\(', line)
        if m:
            handler_defs.append((i, m.group(1)))

    # Calculate line counts
    for idx, (start_line, name) in enumerate(handler_defs):
        if idx + 1 < len(handler_defs):
            end_line = handler_defs[idx + 1][0]
        else:
            # Find next top-level def or EOF
            end_line = len(lines)
            for j in range(start_line + 1, len(lines)):
                if re.match(r'^def \w+', lines[j]) and not lines[j].startswith('def execute_task_'):
                    end_line = j
                    break

        line_count = end_line - start_line
        if line_count < 50:
            verdict = "SHALLOW"
        elif line_count > 200:
            verdict = "COMPLEX"
        else:
            verdict = "OK"

        handlers.append({
            "name": name,
            "lines": line_count,
            "verdict": verdict,
            "start": start_line + 1,
        })

    return handlers


def check_report_frequency(reports):
    """Check if reports are being generated regularly."""
    dates = [r["date"] for r in reports if r["date"] is not None]
    if len(dates) < 2:
        return "insufficient data", 0

    dates.sort()
    gaps = []
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        gaps.append(gap)

    max_gap = max(gaps) if gaps else 0
    avg_gap = sum(gaps) / len(gaps) if gaps else 0

    if max_gap > 7:
        return f"WARNING: max gap {max_gap} days (stale research)", max_gap
    return f"healthy: avg {avg_gap:.1f} days between reports", max_gap


def analyze():
    """Main analysis: read reports, patterns, handlers, produce recommendations."""
    summary_only = "--summary" in sys.argv

    if not summary_only:
        print(f"\n{BOLD}{CYAN}== RECURSIVE SELF-IMPROVEMENT ANALYSIS =={RESET}")
        info("The Machine Spirit contemplates its own reflection...")

    # Step 1: Analyze reports
    reports = analyze_reports()
    if not summary_only:
        info(f"Found {len(reports)} agent/weekly reports")

    # Step 2: Analyze patterns
    all_patterns, unaddressed = analyze_patterns()
    if not summary_only:
        info(f"Known patterns: {len(all_patterns)} ({len(unaddressed)} unaddressed)")

    # Step 3: Analyze handlers
    handlers = analyze_handlers()
    shallow = [h for h in handlers if h["verdict"] == "SHALLOW"]
    complex_h = [h for h in handlers if h["verdict"] == "COMPLEX"]
    if not summary_only:
        info(f"Research handlers: {len(handlers)} ({len(shallow)} shallow, {len(complex_h)} complex)")

    # Step 4: Check report frequency
    freq_status, max_gap = check_report_frequency(reports)
    if not summary_only:
        info(f"Report frequency: {freq_status}")

    # Step 5: Build recommendations
    recommendations = []

    for h in shallow:
        recommendations.append(
            f"Enrich `{h['name']}` (only {h['lines']} lines) -- "
            f"add deeper source analysis, more cross-references"
        )

    for h in complex_h:
        recommendations.append(
            f"Consider splitting `{h['name']}` ({h['lines']} lines) -- "
            f"extract helper functions for readability"
        )

    for u in unaddressed:
        recommendations.append(
            f"Pattern `{u['pattern'][:50]}` seen {u['count']}x but has no auto-fix hint -- "
            f"add fix_hint to patterns.json"
        )

    if max_gap > 7:
        recommendations.append(
            f"Report generation gap of {max_gap} days detected -- "
            f"ensure agent_research.py runs regularly"
        )

    # Check for themes across reports
    all_headers = []
    for r in reports:
        all_headers.extend(r["headers"])
    header_counts = {}
    for h in all_headers:
        key = h.lower().strip()
        header_counts[key] = header_counts.get(key, 0) + 1
    recurring_themes = [(h, c) for h, c in header_counts.items() if c >= 2]

    if not recommendations:
        recommendations.append("No critical issues found -- the Machine Spirit evolves well.")

    # Step 6: Write report
    today = datetime.now().strftime("%Y%m%d")
    report_path = REPO_ROOT / "reports" / f"SELF_IMPROVEMENT_{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines_out = [
        f"# Self-Improvement Report {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"> Generated by `scripts/agent_evolve_self.py` -- Recursive Enlightenment",
        f"> The Machine Spirit examines its own rites for inefficiency.",
        "",
        "## Agent Report History",
        "",
        f"- **Total reports:** {len(reports)}",
    ]

    if reports:
        dates = [r["date"] for r in reports if r["date"]]
        if dates:
            lines_out.append(f"- **Date range:** {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")
        lines_out.append(f"- **Frequency:** {freq_status}")
        total_findings = sum(r["findings_count"] for r in reports)
        lines_out.append(f"- **Total findings across reports:** {total_findings}")

        # List reports
        lines_out.append("")
        lines_out.append("| Report | Date | Findings | Tasks Referenced |")
        lines_out.append("|--------|------|----------|-----------------|")
        for r in reports:
            date_str = r["date"].strftime("%Y-%m-%d") if r["date"] else "unknown"
            tasks = ", ".join(r["task_ids"][:5]) if r["task_ids"] else "none"
            lines_out.append(f"| `{r['path']}` | {date_str} | {r['findings_count']} | {tasks} |")
    lines_out.append("")

    # Handler analysis
    lines_out.append("## Handler Analysis")
    lines_out.append("")
    if handlers:
        lines_out.append("| Handler | Lines | Verdict |")
        lines_out.append("|---------|-------|---------|")
        for h in handlers:
            verdict_icon = {"SHALLOW": "!!!", "COMPLEX": "!!!", "OK": "ok"}[h["verdict"]]
            lines_out.append(f"| `{h['name']}` | {h['lines']} | {verdict_icon} {h['verdict']} |")
        lines_out.append("")
        lines_out.append(f"- **Shallow handlers (<50 lines):** {len(shallow)}")
        lines_out.append(f"- **Complex handlers (>200 lines):** {len(complex_h)}")
        lines_out.append(f"- **OK handlers:** {len(handlers) - len(shallow) - len(complex_h)}")
    else:
        lines_out.append("No handlers found in agent_research.py.")
    lines_out.append("")

    # Patterns without handlers
    lines_out.append("## Recurring Patterns Without Fix Hints")
    lines_out.append("")
    if unaddressed:
        lines_out.append("| Pattern | Count | First Seen |")
        lines_out.append("|---------|-------|-----------|")
        for u in unaddressed:
            lines_out.append(f"| `{u['pattern'][:60]}` | {u['count']} | {u['first_seen'][:10]} |")
    else:
        lines_out.append("All recurring patterns have fix hints -- the Binary Cant is complete.")
    lines_out.append("")

    # Recurring themes
    if recurring_themes:
        lines_out.append("## Recurring Themes Across Reports")
        lines_out.append("")
        for theme, count in sorted(recurring_themes, key=lambda x: -x[1])[:10]:
            lines_out.append(f"- **{theme}** (appears in {count} reports)")
        lines_out.append("")

    # Recommendations
    lines_out.append("## Recommendations")
    lines_out.append("")
    for i, rec in enumerate(recommendations, 1):
        lines_out.append(f"{i}. {rec}")
    lines_out.append("")

    report_path.write_text("\n".join(lines_out), encoding="utf-8")

    # Step 7: Print summary
    if not summary_only:
        print()
        if shallow:
            warn(f"{len(shallow)} shallow handlers need enrichment")
        if complex_h:
            warn(f"{len(complex_h)} complex handlers may need splitting")
        if unaddressed:
            warn(f"{len(unaddressed)} patterns without fix hints")
        ok(f"Report written: {report_path.relative_to(REPO_ROOT)}")
        info(f"{len(recommendations)} recommendations generated")
        print()

    if summary_only:
        print(f"{len(reports)} reports | {len(handlers)} handlers ({len(shallow)} shallow) | {len(recommendations)} recommendations")

    return 0


if __name__ == "__main__":
    sys.exit(analyze())
