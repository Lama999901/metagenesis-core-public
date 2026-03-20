#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Signals (External Relay)
===================================================
Fetches external signals: GitHub repo stats, agent memory state,
task pipeline status, manifest version.

Writes reports/SIGNALS_{YYYYMMDD}.md

Usage:
    python scripts/agent_signals.py             # full report
    python scripts/agent_signals.py --summary   # one-line summary
"""

import json
import sys
import io
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent


def fetch_github_stats():
    """Fetch repo stats from GitHub API. Returns dict or None on failure."""
    url = "https://api.github.com/repos/Lama999901/metagenesis-core-public"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MetaGenesis-Agent",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "pushed_at": data.get("pushed_at", "unknown"),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as e:
        return {"error": str(e)}


def count_memory_sessions():
    """Count session JSON files in .agent_memory/."""
    mem_dir = REPO_ROOT / ".agent_memory"
    if not mem_dir.exists():
        return 0
    return len(list(mem_dir.glob("*.json")))


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


def read_manifest():
    """Read version and test_count from system_manifest.json."""
    manifest_path = REPO_ROOT / "system_manifest.json"
    if not manifest_path.exists():
        return "unknown", 0
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data.get("version", "unknown"), data.get("test_count", 0)


def main():
    summary_only = "--summary" in sys.argv
    today = datetime.now().strftime("%Y%m%d")

    # Gather data
    gh = fetch_github_stats()
    sessions = count_memory_sessions()
    pending, done = count_tasks()
    version, test_count = read_manifest()

    if summary_only:
        if "error" in (gh or {}):
            gh_str = "API unavailable"
        else:
            gh_str = f"{gh['stars']}* {gh['forks']}f {gh['open_issues']}i"
        print(f"v{version} | {test_count} tests | GH: {gh_str} | tasks: {done}done/{pending}pending | mem: {sessions} files")
        return 0

    # Build full report
    lines = [
        f"# EXTERNAL SIGNALS -- Astropathic Relay",
        f"",
        f"> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC",
        f"> Protocol version: {version}",
        f"",
        f"---",
        f"",
        f"## GitHub Repository Stats",
        f"",
    ]

    if gh and "error" not in gh:
        lines += [
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Stars | {gh['stars']} |",
            f"| Forks | {gh['forks']} |",
            f"| Open Issues | {gh['open_issues']} |",
            f"| Last Push | {gh['pushed_at']} |",
        ]
    else:
        err_msg = gh.get("error", "unknown") if gh else "unknown"
        lines += [
            f"GitHub API unavailable: {err_msg}",
            f"",
            f"*Astropathic relay disrupted. Proceeding with local data only.*",
        ]

    lines += [
        f"",
        f"## Agent Memory State",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Memory files | {sessions} |",
        f"| Tasks DONE | {done} |",
        f"| Tasks PENDING | {pending} |",
        f"",
        f"## System Manifest",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Version | {version} |",
        f"| Test count | {test_count} |",
        f"",
        f"---",
        f"",
        f"*The Omnissiah sees beyond the local forge. External signals received.*",
        f"",
    ]

    report_path = REPO_ROOT / "reports" / f"SIGNALS_{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Signals report written: {report_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
