#!/usr/bin/env python3
"""
MetaGenesis Core — Agent Learning System
=========================================
Agents learn from every verification check.
Each run records findings → knowledge base grows →
next agent starts smarter.

Files:
  .agent_memory/knowledge_base.json  — cumulative learnings
  .agent_memory/lessons.md           — human-readable log
  .agent_memory/patterns.json        — recurring issues → auto-fix hints

Usage:
    python scripts/agent_learn.py observe   — run checks + record findings
    python scripts/agent_learn.py recall    — print what agents learned so far
    python scripts/agent_learn.py brief     — one-line summary for CLAUDE.md injection
    python scripts/agent_learn.py stats     — stats on recurring patterns
"""

import json
import sys
import subprocess
import hashlib
import re
import io
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT   = Path(__file__).resolve().parent.parent
MEMORY_DIR  = REPO_ROOT / ".agent_memory"
KB_FILE     = MEMORY_DIR / "knowledge_base.json"
LESSONS_FILE = MEMORY_DIR / "lessons.md"
PATTERNS_FILE = MEMORY_DIR / "patterns.json"

MEMORY_DIR.mkdir(exist_ok=True)

# ── Colors ──────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"


# ── Knowledge Base ───────────────────────────────────────────────────────────
def load_kb():
    if KB_FILE.exists():
        return json.loads(KB_FILE.read_text(encoding="utf-8"))
    return {"sessions": [], "known_issues": {}, "auto_fixes": {}, "etalon": {}}

def save_kb(kb):
    KB_FILE.write_text(json.dumps(kb, indent=2, ensure_ascii=False), encoding="utf-8")

def load_patterns():
    if PATTERNS_FILE.exists():
        return json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    return {}

def save_patterns(p):
    PATTERNS_FILE.write_text(json.dumps(p, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Checks ───────────────────────────────────────────────────────────────────
def run(cmd):
    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       cwd=REPO_ROOT, env=env, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.returncode

def get_test_count():
    out, _ = run("python -m pytest tests/ -q --tb=no 2>&1")
    m = re.search(r"(\d+) passed", out)
    return int(m.group(1)) if m else 0

def get_manifest_version():
    p = REPO_ROOT / "system_manifest.json"
    if p.exists():
        d = json.loads(p.read_text(encoding="utf-8"))
        return d.get("version", "?"), d.get("test_count", 0)
    return "?", 0

def scan_file_for_stale(path, etalon_count, etalon_version):
    """Scan a file for stale numbers/versions. Returns list of issues."""
    issues = []
    if not path.exists():
        return [f"FILE MISSING: {path.name}"]
    content = path.read_text(encoding="utf-8", errors="ignore")

    # Check for merge conflict markers
    if "<<<<<<" in content or "=======" in content or ">>>>>>>" in content:
        issues.append(f"MERGE CONFLICT MARKERS in {path.name}")

    # Check for old test counts
    skip_282 = path.name == 'README_PPA.md'
    old_counts = [c for c in ["295", "271", "270", "282", "389", "391", "471"]
                  if c in content
                  and str(etalon_count) not in content
                  and not (c == "282" and skip_282)]
    if old_counts and etalon_count > 0:
        issues.append(f"STALE COUNT in {path.name}: found {old_counts}, etalon={etalon_count}")

    # Check for old versions
    old_versions = [v for v in ["v0.1.0", "v0.2.0", "v0.3.0", "v0.4.0", "MVP v0.2", "MVP v0.3"]
                    if v in content]
    if old_versions:
        issues.append(f"STALE VERSION in {path.name}: {old_versions}")

    # Check for wrong innovation count
    if "7 innovations" in content and "8 innovations" not in content:
        issues.append(f"WRONG INNOVATION COUNT in {path.name}: says 7, etalon=8")

    return issues

def check_critical_files(etalon_count, etalon_version):
    """Check all critical files. Returns dict of file → issues."""
    critical = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "llms.txt",
        REPO_ROOT / "CONTEXT_SNAPSHOT.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "system_manifest.json",
        REPO_ROOT / "ppa" / "README_PPA.md",
        REPO_ROOT / "paper.md",
        REPO_ROOT / "reports" / "known_faults.yaml",
    ]
    results = {}
    for f in critical:
        issues = scan_file_for_stale(f, etalon_count, etalon_version)
        results[f.name] = issues
    return results


# ── Observe — run checks + record ───────────────────────────────────────────
def observe():
    print(f"\n{B}{C}══ AGENT LEARNING: OBSERVE ══{X}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    kb = load_kb()
    patterns = load_patterns()

    # Get etalon from manifest
    etalon_version, manifest_count = get_manifest_version()
    actual_count = get_test_count()

    print(f"{C}→{X} Etalon: v{etalon_version} | manifest_count={manifest_count} | pytest_count={actual_count}")

    # ── Run steward audit ──
    out_steward, code_steward = run("python scripts/steward_audit.py")
    steward_ok = code_steward == 0 and "PASS" in out_steward
    print(f"{'  ✅' if steward_ok else '  ❌'} steward_audit: {'PASS' if steward_ok else 'FAIL'}")

    # ── Run deep verify ──
    out_deep, code_deep = run("python scripts/deep_verify.py")
    deep_ok = "ALL" in out_deep and "PASSED" in out_deep
    print(f"{'  ✅' if deep_ok else '  ❌'} deep_verify: {'PASS' if deep_ok else 'FAIL'}")

    # ── Check manifest consistency ──
    manifest_ok = manifest_count == actual_count
    if not manifest_ok:
        print(f"  ❌ manifest test_count={manifest_count} != pytest={actual_count}")
    else:
        print(f"  ✅ manifest consistent: {actual_count} tests")

    # ── Scan critical files ──
    print(f"\n{C}→{X} Scanning critical files...")
    file_issues = check_critical_files(actual_count, etalon_version)
    all_issues = []
    for fname, issues in file_issues.items():
        if issues:
            for issue in issues:
                print(f"  ❌ {issue}")
                all_issues.append(issue)
        else:
            print(f"  ✅ {fname}")

    # ── Record findings ──
    session = {
        "timestamp": datetime.now().isoformat(),
        "etalon_version": etalon_version,
        "actual_test_count": actual_count,
        "manifest_test_count": manifest_count,
        "steward_pass": steward_ok,
        "deep_verify_pass": deep_ok,
        "manifest_consistent": manifest_ok,
        "file_issues": file_issues,
        "issue_count": len(all_issues),
    }
    kb["sessions"].append(session)

    # Update etalon
    if actual_count > 0:
        kb["etalon"] = {
            "version": etalon_version,
            "test_count": actual_count,
            "updated": datetime.now().isoformat(),
        }

    # Track recurring patterns
    for issue in all_issues:
        key = issue[:60]  # normalize
        if key not in patterns:
            patterns[key] = {"count": 0, "first_seen": datetime.now().isoformat(),
                             "fix_hint": ""}
        patterns[key]["count"] += 1
        patterns[key]["last_seen"] = datetime.now().isoformat()

    # ── Generate fix hints for recurring issues ──
    print(f"\n{C}→{X} Learning from patterns...")
    for key, data in patterns.items():
        if data["count"] >= 2 and not data.get("fix_hint"):
            if "innovations" in key:
                data["fix_hint"] = '/gsd:quick "Update all docs: change 7 innovations to 8 everywhere"'
            elif "STALE COUNT" in key:
                data["fix_hint"] = '/gsd:quick "Sync test count to {etalon} in all docs"'
            elif "STALE VERSION" in key:
                data["fix_hint"] = '/gsd:quick "Update version strings to v0.5.0 everywhere"'
            elif "MERGE CONFLICT" in key:
                data["fix_hint"] = "git checkout --ours FILE && git add FILE"
            if data.get("fix_hint"):
                print(f"  💡 Auto-fix hint learned: {key[:40]}... — Binary Cant recorded (AUTO_FIX_LEARNED)")
                print(f"     → {data['fix_hint']}")

    save_kb(kb)
    save_patterns(patterns)

    # ── Write human-readable lessons ──
    _write_lessons_log(session, all_issues, patterns)

    # ── Summary ──
    print(f"\n{B}{'═'*50}{X}")
    if len(all_issues) == 0:
        print(f"{G}  ✅ SYSTEM HEALTHY — no issues found{X}")
        print(f"{G}  Praise the Omnissiah (SYSTEM_HEALTHY){X}")
    else:
        print(f"{R}  ❌ {len(all_issues)} issues found{X}")
        print(f"\n  Fix command:")
        print(f'  /gsd:quick "Fix all stale documentation: {"; ".join(all_issues[:3])}"')

    total_sessions = len(kb["sessions"])
    print(f"\n  Agent memory: {total_sessions} sessions recorded")
    print(f"  Known patterns: {len(patterns)}")
    print(f"  Auto-fix hints: {sum(1 for p in patterns.values() if p.get('fix_hint'))}")
    print(f"{'═'*50}\n")

    return len(all_issues) == 0


def _write_lessons_log(session, issues, patterns):
    """Append to human-readable lessons log."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"\n## Session {ts}",
        f"- Tests: {session['actual_test_count']} | Version: {session['etalon_version']}",
        f"- Steward: {'PASS' if session['steward_pass'] else 'FAIL'}",
        f"- Deep verify: {'PASS' if session['deep_verify_pass'] else 'FAIL'}",
    ]
    if issues:
        lines.append(f"- Issues found ({len(issues)}):")
        for i in issues:
            lines.append(f"  - {i}")

    recurring = [(k, v) for k, v in patterns.items() if v["count"] >= 2]
    if recurring:
        lines.append(f"- Recurring patterns ({len(recurring)}):")
        for k, v in recurring[:5]:
            lines.append(f"  - [{v['count']}x] {k[:60]}")

    entry = "\n".join(lines) + "\n"

    if not LESSONS_FILE.exists():
        LESSONS_FILE.write_text("# Agent Learning Log\n\n", encoding="utf-8")
    with open(LESSONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


# ── Recall — print what agents learned ───────────────────────────────────────
def recall():
    print(f"\n{B}{C}══ AGENT MEMORY ══{X}")
    print(f"  {C}Accessing the Noosphere (MEMORY_RECALL){X}\n")
    kb = load_kb()
    patterns = load_patterns()

    if not kb["sessions"]:
        print("  No sessions recorded yet. Run: python scripts/agent_learn.py observe")
        return

    # Etalon
    e = kb.get("etalon", {})
    print(f"{C}ETALON:{X}")
    print(f"  Version: {e.get('version', '?')} | Tests: {e.get('test_count', '?')}")
    print(f"  Updated: {e.get('updated', '?')[:16]}")

    # Recent sessions
    print(f"\n{C}RECENT SESSIONS ({len(kb['sessions'])}):{X}")
    for s in kb["sessions"][-5:]:
        ts = s["timestamp"][:16]
        issues = s.get("issue_count", 0)
        status = f"{G}✅{X}" if issues == 0 else f"{R}❌ {issues} issues{X}"
        print(f"  {ts}  {status}  | tests={s.get('actual_test_count', '?')}")

    # Recurring patterns with fix hints
    with_hints = [(k, v) for k, v in patterns.items() if v.get("fix_hint")]
    if with_hints:
        print(f"\n{C}AUTO-FIX HINTS LEARNED ({len(with_hints)}):{X}")
        for k, v in with_hints:
            print(f"  [{v['count']}x] {k[:55]}")
            print(f"  💡 Fix: {v['fix_hint']}")
            print()

    # Most common issues
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]["count"], reverse=True)
    if sorted_patterns:
        print(f"\n{C}MOST COMMON ISSUES:{X}")
        for k, v in sorted_patterns[:5]:
            print(f"  [{v['count']}x] {k[:70]}")

    # Strategic context from synthesis
    strategic = MEMORY_DIR / "strategic_memory.json"
    if strategic.exists():
        sm = json.loads(strategic.read_text(encoding="utf-8"))
        print(f"\n{C}STRATEGIC CONTEXT:{X}")
        print(f"  North star: {sm.get('project_north_star', '?')}")
        resolved = sm.get('resolved_forever', [])
        print(f"  Resolved forever: {len(resolved)} ghost patterns")
        active = sm.get('active_known_issues', [])
        print(f"  Active issues: {len(active)}")


# ── Brief — one-line summary for CLAUDE.md injection ─────────────────────────
def brief():
    kb = load_kb()
    patterns = load_patterns()
    sessions = len(kb["sessions"])
    hints = sum(1 for p in patterns.values() if p.get("fix_hint"))
    e = kb.get("etalon", {})
    print(f"Agent memory: {sessions} sessions | {len(patterns)} patterns | {hints} auto-fix hints | etalon: v{e.get('version','?')} {e.get('test_count','?')} tests")


# ── Stats ────────────────────────────────────────────────────────────────────
def stats():
    kb = load_kb()
    patterns = load_patterns()
    sessions = kb["sessions"]
    if not sessions:
        print("No sessions yet.")
        return

    total_issues = sum(s.get("issue_count", 0) for s in sessions)
    clean = sum(1 for s in sessions if s.get("issue_count", 0) == 0)
    print(f"\n{B}Agent Evolution Stats:{X}")
    print(f"  Total sessions:    {len(sessions)}")
    print(f"  Clean sessions:    {clean}/{len(sessions)}")
    print(f"  Total issues seen: {total_issues}")
    print(f"  Known patterns:    {len(patterns)}")
    print(f"  Auto-fix hints:    {sum(1 for p in patterns.values() if p.get('fix_hint'))}")
    if sessions:
        last = sessions[-1]
        print(f"  Last run:          {last['timestamp'][:16]}")
        trend = "improving" if len(sessions) > 1 and sessions[-1].get("issue_count", 0) < sessions[-2].get("issue_count", 1) else "stable"
        print(f"  Trend:             {trend}")


# ── Synthesize — full memory synthesis ──────────────────────────────────────
def synthesize():
    """Full memory synthesis -- process all sessions, resolve ghosts, create strategic files."""
    print(f"\n{B}{C}== AGENT MEMORY: SYNTHESIZE =={X}")

    kb = load_kb()
    patterns = load_patterns()
    sessions = kb.get("sessions", [])

    # 1. Resolve ghost patterns
    resolved_file = MEMORY_DIR / "resolved_patterns.json"
    existing_resolved = json.loads(resolved_file.read_text(encoding="utf-8")) if resolved_file.exists() else {}

    ghost_count = 0
    for key, pat in list(patterns.items()):
        last_seen = pat.get("last_seen", "")[:10]
        if last_seen and last_seen < datetime.now().strftime("%Y-%m-%d"):
            # Check if pattern appeared in last 5 sessions
            recent = sessions[-5:] if len(sessions) >= 5 else sessions
            still_active = False
            for s in recent:
                issues = s.get("file_issues", {})
                if isinstance(issues, dict):
                    all_issue_texts = []
                    for v in issues.values():
                        if isinstance(v, list):
                            all_issue_texts.extend(v)
                    if any(key[:30].lower() in str(i).lower() for i in all_issue_texts):
                        still_active = True
                        break
                elif isinstance(issues, list):
                    if any(key[:30].lower() in str(i).lower() for i in issues):
                        still_active = True
                        break
            if not still_active:
                pat["status"] = "resolved"
                pat["resolution_date"] = last_seen
                existing_resolved[key] = pat
                ghost_count += 1

    resolved_file.write_text(json.dumps(existing_resolved, indent=2, ensure_ascii=False), encoding="utf-8")

    # Clear resolved from active patterns
    active_patterns = {k: v for k, v in patterns.items()
                       if k not in existing_resolved}
    save_patterns(active_patterns)

    # 2. Build trajectory
    trajectory = []
    seen_counts = set()
    for s in sessions:
        tc = s.get("actual_test_count") or s.get("manifest_test_count", 0)
        ts = s.get("timestamp", "")[:10]
        if tc and tc > 0 and tc not in seen_counts:
            seen_counts.add(tc)
            trajectory.append({"date": ts, "tests": tc})
    trajectory.sort(key=lambda x: x["date"])

    traj_file = MEMORY_DIR / "project_trajectory.json"
    traj_data = {
        "trajectory": trajectory,
        "growth_rate": f"{trajectory[-1]['tests']/trajectory[0]['tests']:.1f}x in {len(set(t['date'] for t in trajectory))} snapshots" if trajectory else "no data",
        "synthesized": datetime.now().strftime("%Y-%m-%d")
    }
    traj_file.write_text(json.dumps(traj_data, indent=2), encoding="utf-8")

    # 3. Print summary
    print(f"  Synthesized {len(sessions)} sessions")
    print(f"  Resolved {ghost_count} ghost patterns")
    print(f"  Active patterns: {len(active_patterns)}")
    if trajectory:
        print(f"  Test trajectory: {trajectory[0]['tests']} -> {trajectory[-1]['tests']}")
    print(f"  Created: project_trajectory.json, resolved_patterns.json")

    strategic = MEMORY_DIR / "strategic_memory.json"
    if strategic.exists():
        print(f"  strategic_memory.json: exists")

    print(f"\n{G}  SYNTHESIS COMPLETE{X}")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "observe"
    if cmd == "observe":      observe()
    elif cmd == "recall":     recall()
    elif cmd == "brief":      brief()
    elif cmd == "stats":      stats()
    elif cmd == "synthesize": synthesize()
    else:
        print(f"Usage: agent_learn.py [observe|recall|brief|stats|synthesize]")
