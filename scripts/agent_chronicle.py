#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Chronicle (Historitor Record)
=======================================================
Records a versioned snapshot of protocol state:
claims, tests, innovations, tasks, and diffs from previous chronicle.

Writes reports/CHRONICLE_{version}_{YYYYMMDD}.md

Usage:
    python scripts/agent_chronicle.py             # full chronicle
    python scripts/agent_chronicle.py --summary   # one-line summary
"""

import json
import re
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent


def read_manifest():
    """Read system_manifest.json for version, test_count, active_claims, innovations."""
    manifest_path = REPO_ROOT / "system_manifest.json"
    if not manifest_path.exists():
        return {}
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def read_claim_domains():
    """Read scientific_claim_index.md and extract claim-domain pairs."""
    index_path = REPO_ROOT / "reports" / "scientific_claim_index.md"
    if not index_path.exists():
        return []
    content = index_path.read_text(encoding="utf-8", errors="ignore")
    # Parse table rows: | CLAIM-ID | ... | domain | ...
    domains = []
    for line in content.splitlines():
        if line.startswith("|") and "---" not in line and "Claim" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                domains.append((parts[0], parts[1] if len(parts) > 1 else ""))
    return domains


def count_tasks():
    """Count PENDING and DONE tasks in AGENT_TASKS.md."""
    tasks_file = REPO_ROOT / "AGENT_TASKS.md"
    pending, done = 0, 0
    if tasks_file.exists():
        content = tasks_file.read_text(encoding="utf-8", errors="ignore")
        for line in content.splitlines():
            if "Status:" in line and "PENDING" in line:
                pending += 1
            elif "Status:" in line and "DONE" in line:
                done += 1
    return pending, done


def find_previous_chronicle():
    """Find the most recent CHRONICLE_*.md and parse key numbers from it."""
    reports = REPO_ROOT / "reports"
    if not reports.exists():
        return None
    chronicles = sorted(reports.glob("CHRONICLE_*.md"), reverse=True)
    if not chronicles:
        return None

    content = chronicles[0].read_text(encoding="utf-8", errors="ignore")
    prev = {"file": chronicles[0].name}

    # Extract numbers from previous chronicle
    m = re.search(r"Claims:\s*(\d+)", content)
    if m:
        prev["claims"] = int(m.group(1))
    m = re.search(r"Tests:\s*(\d+)", content)
    if m:
        prev["tests"] = int(m.group(1))
    m = re.search(r"Innovations:\s*(\d+)", content)
    if m:
        prev["innovations"] = int(m.group(1))

    return prev


def main():
    summary_only = "--summary" in sys.argv
    today = datetime.now().strftime("%Y%m%d")

    manifest = read_manifest()
    version = manifest.get("version", "unknown")
    test_count = manifest.get("test_count", 0)
    claims = manifest.get("active_claims", [])
    innovations = manifest.get("verified_innovations", [])
    claim_domains = read_claim_domains()
    pending, done = count_tasks()
    prev = find_previous_chronicle()

    if summary_only:
        diff_str = ""
        if prev:
            dt = test_count - prev.get("tests", test_count)
            dc = len(claims) - prev.get("claims", len(claims))
            parts = []
            if dt != 0:
                parts.append(f"tests {'+' if dt > 0 else ''}{dt}")
            if dc != 0:
                parts.append(f"claims {'+' if dc > 0 else ''}{dc}")
            if parts:
                diff_str = f" | delta: {', '.join(parts)}"
            else:
                diff_str = " | no change"
        print(f"v{version} | {len(claims)} claims | {test_count} tests | {len(innovations)} innovations{diff_str}")
        return 0

    # Build diff section
    diff_lines = []
    if prev:
        diff_lines.append(f"## Changes Since Previous Chronicle")
        diff_lines.append(f"")
        diff_lines.append(f"Previous: `{prev['file']}`")
        diff_lines.append(f"")
        diff_lines.append(f"| Metric | Previous | Current | Delta |")
        diff_lines.append(f"|--------|----------|---------|-------|")
        prev_claims = prev.get("claims", "?")
        prev_tests = prev.get("tests", "?")
        prev_innov = prev.get("innovations", "?")
        dc = f"+{len(claims) - prev_claims}" if isinstance(prev_claims, int) and len(claims) - prev_claims > 0 else str(len(claims) - prev_claims) if isinstance(prev_claims, int) else "?"
        dt = f"+{test_count - prev_tests}" if isinstance(prev_tests, int) and test_count - prev_tests > 0 else str(test_count - prev_tests) if isinstance(prev_tests, int) else "?"
        di = f"+{len(innovations) - prev_innov}" if isinstance(prev_innov, int) and len(innovations) - prev_innov > 0 else str(len(innovations) - prev_innov) if isinstance(prev_innov, int) else "?"
        diff_lines.append(f"| Claims | {prev_claims} | {len(claims)} | {dc} |")
        diff_lines.append(f"| Tests | {prev_tests} | {test_count} | {dt} |")
        diff_lines.append(f"| Innovations | {prev_innov} | {len(innovations)} | {di} |")
    else:
        diff_lines.append(f"## Changes Since Previous Chronicle")
        diff_lines.append(f"")
        diff_lines.append(f"*First chronicle -- no previous record found.*")

    # Build full report
    lines = [
        f"# CHRONICLE -- Historitor Record",
        f"",
        f"> Version: {version}",
        f"> Date: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC",
        f"> Claims: {len(claims)}",
        f"> Tests: {test_count}",
        f"> Innovations: {len(innovations)}",
        f"",
        f"---",
        f"",
        f"## Active Claims ({len(claims)})",
        f"",
        f"| # | Claim ID | Domain |",
        f"|---|----------|--------|",
    ]

    if claim_domains:
        for i, (cid, domain) in enumerate(claim_domains, 1):
            lines.append(f"| {i} | {cid} | {domain} |")
    else:
        for i, cid in enumerate(claims, 1):
            lines.append(f"| {i} | {cid} | -- |")

    lines += [
        f"",
        f"## Verified Innovations ({len(innovations)})",
        f"",
    ]
    for inn in innovations:
        lines.append(f"- {inn}")

    lines += [
        f"",
        f"## Agent Task Pipeline",
        f"",
        f"| Status | Count |",
        f"|--------|-------|",
        f"| DONE | {done} |",
        f"| PENDING | {pending} |",
        f"",
    ]

    lines += diff_lines

    lines += [
        f"",
        f"---",
        f"",
        f"*The Historitor records all. The Omnissiah remembers.*",
        f"",
    ]

    # Version in filename uses dots replaced with underscores
    ver_safe = version.replace(".", "_")
    report_path = REPO_ROOT / "reports" / f"CHRONICLE_{ver_safe}_{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Chronicle written: {report_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
