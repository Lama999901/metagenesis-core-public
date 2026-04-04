#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Evolution Council
============================================
Reads 6 data sources, synthesizes evidence-based improvement proposals,
and ranks them by impact/effort ratio.

Data sources:
  1. agent_learn.py recall   -- recurring patterns (systemic issues)
  2. Coverage report         -- functions below 70%
  3. known_faults.yaml       -- documented but unmitigated faults
  4. agent_evolution.py      -- non-PASS checks
  5. response_queue.json     -- client pain points
  6. git log --oneline -30   -- hot spots (most changed files)

Output:
  .planning/EVOLUTION_PROPOSALS.md  -- up to 10 ranked proposals

Usage:
    python scripts/agent_evolution_council.py              # full analysis
    python scripts/agent_evolution_council.py --summary    # top 3 only
    python scripts/agent_evolution_council.py --json       # machine-readable
"""

import subprocess
import sys
import io
import json
import re
import os
from pathlib import Path
from datetime import datetime
from collections import Counter

# Fix Windows cp1252 encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(cmd, cwd=None):
    """Run a shell command, return (stdout, returncode)."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=cwd or REPO_ROOT, env=env,
        encoding="utf-8", errors="replace",
    )
    return r.stdout.strip(), r.returncode


# ---------------------------------------------------------------------------
# Source 1: agent_learn.py recall -- recurring patterns
# ---------------------------------------------------------------------------

def read_agent_learn():
    """Parse agent_learn.py recall output for patterns recurring 3+ times."""
    issues = []
    out, code = _run("python scripts/agent_learn.py recall")
    if code != 0 or not out:
        return issues, False

    # Look for lines like [Nx] description
    for line in out.splitlines():
        m = re.search(r"\[(\d+)x\]\s+(.+)", line)
        if m:
            count = int(m.group(1))
            desc = m.group(2).strip()
            if count >= 3:
                issues.append({"source": "agent_learn", "count": count, "description": desc})
    return issues, True


# ---------------------------------------------------------------------------
# Source 2: Coverage report -- modules below 70%
# ---------------------------------------------------------------------------

def read_coverage():
    """Run pytest --cov and find modules below 70% coverage."""
    gaps = []
    out, code = _run(
        "python -m pytest tests/ -q --tb=no --no-header "
        "--cov=scripts --cov=backend --cov-report=term-missing 2>&1"
    )
    if code not in (0, 1) or not out:
        # Fallback: try agent_coverage.py
        out2, code2 = _run("python scripts/agent_coverage.py --summary")
        if code2 == 0 and out2:
            m = re.search(r"Coverage ([\d.]+)%", out2)
            if m:
                pct = float(m.group(1))
                if pct < 70:
                    gaps.append({
                        "source": "coverage",
                        "module": "overall",
                        "coverage_pct": pct,
                        "description": f"Overall coverage {pct:.1f}% below 70% target",
                    })
            return gaps, True
        return gaps, False

    # Parse coverage table lines: "scripts/foo.py    120    30    75%"
    for line in out.splitlines():
        m = re.match(r"([\w/\\_.-]+\.py)\s+(\d+)\s+(\d+)\s+(\d+)%", line)
        if m:
            module = m.group(1)
            pct = int(m.group(4))
            if pct < 70:
                gaps.append({
                    "source": "coverage",
                    "module": module,
                    "coverage_pct": pct,
                    "description": f"{module} has {pct}% coverage (below 70%)",
                })
    return gaps, True


# ---------------------------------------------------------------------------
# Source 3: known_faults.yaml -- unmitigated faults
# ---------------------------------------------------------------------------

def read_known_faults():
    """Parse known_faults.yaml for improvement targets."""
    faults = []
    faults_path = REPO_ROOT / "reports" / "known_faults.yaml"
    if not faults_path.exists():
        return faults, False

    content = faults_path.read_text(encoding="utf-8", errors="ignore")

    # Try yaml import first, fall back to regex
    try:
        import yaml
        data = yaml.safe_load(content)
        if data and "known_faults" in data:
            for fault in data["known_faults"]:
                faults.append({
                    "source": "known_faults",
                    "fault_id": fault.get("fault_id", "unknown"),
                    "severity": fault.get("severity", "unknown"),
                    "status": fault.get("status", "unknown"),
                    "description": fault.get("description", "").strip()[:200],
                    "mitigation": fault.get("mitigation", "").strip()[:200],
                })
        return faults, True
    except ImportError:
        pass

    # Regex fallback: extract fault blocks
    fault_blocks = re.split(r"- fault_id:", content)
    for block in fault_blocks[1:]:  # skip header
        fault_id = re.search(r'"([^"]+)"', block)
        severity = re.search(r'severity:\s*"([^"]+)"', block)
        status = re.search(r'status:\s*"([^"]+)"', block)
        desc = re.search(r'description:\s*>\s*\n\s+(.+?)(?:\n\s+\w|\Z)', block, re.DOTALL)
        mitigation = re.search(r'mitigation:\s*"([^"]*)"', block)

        faults.append({
            "source": "known_faults",
            "fault_id": fault_id.group(1) if fault_id else "unknown",
            "severity": severity.group(1) if severity else "unknown",
            "status": status.group(1) if status else "unknown",
            "description": (desc.group(1).strip()[:200] if desc else ""),
            "mitigation": (mitigation.group(1).strip()[:200] if mitigation else ""),
        })
    return faults, True


# ---------------------------------------------------------------------------
# Source 4: agent_evolution.py --summary -- non-PASS checks
# ---------------------------------------------------------------------------

def read_agent_evolution():
    """Run agent_evolution.py --summary and extract non-PASS checks."""
    failures = []
    out, code = _run("python scripts/agent_evolution.py --summary")
    if not out:
        return failures, False

    for line in out.splitlines():
        # Look for FAIL lines
        if "FAIL" in line and "PASS" not in line:
            # Clean ANSI codes
            clean = re.sub(r"\033\[[0-9;]*m", "", line).strip()
            failures.append({
                "source": "agent_evolution",
                "description": clean[:200],
            })
    return failures, True


# ---------------------------------------------------------------------------
# Source 5: response_queue.json -- client pain points
# ---------------------------------------------------------------------------

def read_response_queue():
    """Read response_queue.json for what prospects ask about."""
    insights = []
    # Try multiple possible locations
    candidates = [
        REPO_ROOT / "reports" / "response_queue.json",
        REPO_ROOT / "reports" / "pilot_queue.json",
    ]
    queue_path = None
    for c in candidates:
        if c.exists():
            queue_path = c
            break

    if not queue_path:
        return insights, False

    try:
        data = json.loads(queue_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return insights, False

    entries = data if isinstance(data, list) else data.get("entries", [])
    if not entries:
        return insights, True

    # Count domains requested
    domain_counts = Counter()
    for entry in entries:
        domain = entry.get("domain_detected") or entry.get("domain", "unknown")
        domain_counts[domain] += 1

    for domain, count in domain_counts.most_common():
        insights.append({
            "source": "response_queue",
            "domain": domain,
            "count": count,
            "description": f"Domain '{domain}' requested {count} time(s) by prospects",
        })

    return insights, True


# ---------------------------------------------------------------------------
# Source 6: git log --oneline -30 -- hot spots
# ---------------------------------------------------------------------------

def read_git_hotspots():
    """Analyze recent git log for frequently changed files."""
    hotspots = []
    out, code = _run("git log --oneline -30 --name-only")
    if code != 0 or not out:
        return hotspots, False

    file_counts = Counter()
    for line in out.splitlines():
        line = line.strip()
        # Skip commit message lines (start with hex hash)
        if not line or re.match(r"^[0-9a-f]{7,}", line):
            continue
        # Count file changes
        if "/" in line or line.endswith(".py") or line.endswith(".md"):
            file_counts[line] += 1

    # Files changed 3+ times in last 30 commits are hot spots
    for filepath, count in file_counts.most_common(10):
        if count >= 2:
            hotspots.append({
                "source": "git_log",
                "file": filepath,
                "change_count": count,
                "description": f"{filepath} changed {count} times in last 30 commits",
            })

    return hotspots, True


# ---------------------------------------------------------------------------
# Proposal Generation
# ---------------------------------------------------------------------------

IMPACT_SCORES = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
EFFORT_SCORES = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}


def _classify_impact(item):
    """Classify impact level based on source and content."""
    source = item.get("source", "")
    desc = item.get("description", "").lower()

    # Client-facing issues are CRITICAL
    if source == "response_queue":
        return "HIGH"
    # Evolution check failures are HIGH
    if source == "agent_evolution":
        return "HIGH"
    # Recurring patterns (3+ times) are HIGH
    if source == "agent_learn" and item.get("count", 0) >= 5:
        return "CRITICAL"
    if source == "agent_learn":
        return "HIGH"
    # Coverage gaps
    if source == "coverage":
        pct = item.get("coverage_pct", 100)
        if pct < 40:
            return "CRITICAL"
        if pct < 60:
            return "HIGH"
        return "MEDIUM"
    # Known faults
    if source == "known_faults":
        sev = item.get("severity", "").upper()
        if "CRITICAL" in sev:
            return "CRITICAL"
        return "MEDIUM"
    # Hot spots
    if source == "git_log":
        changes = item.get("change_count", 0)
        if changes >= 5:
            return "HIGH"
        return "MEDIUM"
    return "LOW"


def _classify_effort(item):
    """Classify effort level based on source and content."""
    source = item.get("source", "")
    desc = item.get("description", "").lower()

    if source == "coverage":
        return "MEDIUM"
    if source == "known_faults":
        if "structural" in desc or "circular" in desc:
            return "HIGH"
        return "MEDIUM"
    if source == "agent_evolution":
        return "MEDIUM"
    if source == "response_queue":
        return "LOW"
    if source == "git_log":
        return "LOW"
    if source == "agent_learn":
        if "counter" in desc or "stale" in desc:
            return "LOW"
        return "MEDIUM"
    return "MEDIUM"


def _generate_solution(item):
    """Generate a concrete solution suggestion."""
    source = item.get("source", "")
    desc = item.get("description", "").lower()

    if source == "coverage":
        module = item.get("module", "unknown")
        return f"Add targeted tests for {module} to reach 70% coverage"
    if source == "known_faults":
        return f"Address fault {item.get('fault_id', '?')}: {item.get('mitigation', 'See known_faults.yaml')}"
    if source == "agent_evolution":
        return "Fix the failing evolution check to bring all 20 checks to PASS"
    if source == "response_queue":
        domain = item.get("domain", "unknown")
        return f"Strengthen {domain} domain documentation and demo bundles for prospects"
    if source == "git_log":
        f = item.get("file", "unknown")
        return f"Refactor {f} to reduce churn -- frequent changes signal instability"
    if source == "agent_learn":
        if "stale" in desc or "counter" in desc:
            return "Automate counter synchronization to prevent recurring staleness"
        return "Investigate root cause of recurring pattern and add automated prevention"
    return "Investigate and resolve the identified issue"


def _risk_assessment(item):
    """What existing tests catch regressions if we fix this."""
    source = item.get("source", "")
    if source == "coverage":
        return "New tests added as part of fix; existing 1753 tests catch regressions"
    if source == "known_faults":
        return "steward_audit.py + deep_verify.py catch structural regressions"
    if source == "agent_evolution":
        return "agent_evolution.py 20 checks + pytest suite catch regressions"
    if source == "response_queue":
        return "Bundle verification (mg.py verify) catches any broken bundles"
    if source == "git_log":
        return "Full test suite (1753 tests) + steward_audit catch regressions"
    if source == "agent_learn":
        return "check_stale_docs.py + agent_learn.py observe catch recurrence"
    return "Full test suite catches regressions"


def generate_proposals(sources_data):
    """Generate ranked proposals from all source data."""
    all_items = []
    for source_name, (items, success) in sources_data.items():
        if success:
            all_items.extend(items)

    # Deduplicate by description similarity
    seen = set()
    unique_items = []
    for item in all_items:
        key = item.get("description", "")[:50].lower()
        if key not in seen:
            seen.add(key)
            unique_items.append(item)

    # Score and rank
    proposals = []
    for i, item in enumerate(unique_items):
        impact = _classify_impact(item)
        effort = _classify_effort(item)
        impact_score = IMPACT_SCORES.get(impact, 1)
        effort_score = EFFORT_SCORES.get(effort, 2)
        ratio = impact_score / effort_score

        proposals.append({
            "rank": 0,  # set after sorting
            "title": _make_title(item),
            "problem": item.get("description", "Unknown issue"),
            "evidence": _make_evidence(item),
            "solution": _generate_solution(item),
            "effort": effort,
            "impact": impact,
            "risk": _risk_assessment(item),
            "score": ratio,
            "source": item.get("source", "unknown"),
        })

    # Sort by score descending, then by impact descending
    proposals.sort(key=lambda p: (p["score"], IMPACT_SCORES.get(p["impact"], 0)), reverse=True)

    # Assign ranks and limit to 10
    for i, p in enumerate(proposals[:10]):
        p["rank"] = i + 1

    return proposals[:10]


def _make_title(item):
    """Create a short title for a proposal."""
    source = item.get("source", "")
    desc = item.get("description", "Unknown")

    if source == "coverage":
        module = item.get("module", "unknown")
        return f"Increase test coverage for {module}"
    if source == "known_faults":
        return f"Address known fault {item.get('fault_id', '?')}"
    if source == "agent_evolution":
        return "Fix failing evolution check"
    if source == "response_queue":
        domain = item.get("domain", "unknown")
        return f"Strengthen {domain} domain for client outreach"
    if source == "git_log":
        f = item.get("file", "unknown")
        return f"Stabilize frequently-changed file: {Path(f).name}"
    if source == "agent_learn":
        return f"Resolve recurring pattern: {desc[:60]}"
    return desc[:60]


def _make_evidence(item):
    """Create evidence string for a proposal."""
    source = item.get("source", "")
    if source == "coverage":
        return f"Coverage report: {item.get('module', '?')} at {item.get('coverage_pct', '?')}%"
    if source == "known_faults":
        return f"reports/known_faults.yaml :: {item.get('fault_id', '?')}"
    if source == "agent_evolution":
        return f"agent_evolution.py --summary output: {item.get('description', '?')[:100]}"
    if source == "response_queue":
        return f"response_queue/pilot_queue: domain={item.get('domain','?')} count={item.get('count',0)}"
    if source == "git_log":
        return f"git log -30: {item.get('file','?')} changed {item.get('change_count',0)} times"
    if source == "agent_learn":
        return f"agent_learn.py recall: [{item.get('count',0)}x] {item.get('description','?')[:80]}"
    return "See source output"


# ---------------------------------------------------------------------------
# Output: EVOLUTION_PROPOSALS.md
# ---------------------------------------------------------------------------

def write_proposals_md(proposals, sources_data):
    """Write .planning/EVOLUTION_PROPOSALS.md."""
    planning_dir = REPO_ROOT / ".planning"
    planning_dir.mkdir(parents=True, exist_ok=True)
    out_path = planning_dir / "EVOLUTION_PROPOSALS.md"

    successful_sources = [name for name, (_, ok) in sources_data.items() if ok]

    lines = [
        "# Evolution Proposals",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Sources analyzed: {', '.join(successful_sources)}",
        "",
    ]

    if not proposals:
        lines.append("No proposals generated -- all sources returned empty results.")
    else:
        for p in proposals:
            lines.append(f"## PROP-{p['rank']:03d}: {p['title']}")
            lines.append(f"**Problem:** {p['problem']}")
            lines.append(f"**Evidence:** {p['evidence']}")
            lines.append(f"**Solution:** {p['solution']}")
            lines.append(f"**Effort:** {p['effort']}")
            lines.append(f"**Impact:** {p['impact']}")
            lines.append(f"**Risk:** {p['risk']}")
            lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def collect_all_sources():
    """Read all 6 data sources. Returns dict of source_name -> (items, success)."""
    sources = {}
    sources["agent_learn"] = read_agent_learn()
    sources["coverage"] = read_coverage()
    sources["known_faults"] = read_known_faults()
    sources["agent_evolution"] = read_agent_evolution()
    sources["response_queue"] = read_response_queue()
    sources["git_log"] = read_git_hotspots()
    return sources


def print_summary(proposals):
    """Print top 3 proposals to stdout in brief format."""
    top = proposals[:3]
    if not top:
        print("No proposals generated.")
        return

    print("Evolution Council -- Top 3 Proposals")
    print("=" * 50)
    for p in top:
        print(f"\n  PROP-{p['rank']:03d}: {p['title']}")
        print(f"    Impact: {p['impact']}  |  Effort: {p['effort']}")
        print(f"    {p['solution'][:80]}")
    print()


def main():
    summary_only = "--summary" in sys.argv
    json_output = "--json" in sys.argv

    sources = collect_all_sources()
    proposals = generate_proposals(sources)

    if json_output:
        print(json.dumps(proposals, indent=2, ensure_ascii=False))
        return 0

    # Always write proposals file
    out_path = write_proposals_md(proposals, sources)

    if summary_only:
        print_summary(proposals)
    else:
        successful = sum(1 for _, (_, ok) in sources.items() if ok)
        print(f"Evolution Council analyzed {successful}/6 sources")
        print(f"Generated {len(proposals)} proposals -> {out_path}")
        print()
        print_summary(proposals)

    return 0


if __name__ == "__main__":
    sys.exit(main())
