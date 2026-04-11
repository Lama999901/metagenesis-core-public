#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Pattern Promoter
==========================================
The Biologis studies recurring patterns in the agent memory
and promotes high-frequency issues into formal evolution proposals.

When a pattern recurs >= 3 times, it has earned the right to become
a permanent check in agent_evolution.py. This script writes the
promotion proposals to .planning/EVOLUTION_PROPOSALS.md with exact
code skeletons — the Fabricator-General need only review and merge.

Files:
  .agent_memory/patterns.json          -- source: recurring issue patterns
  .planning/EVOLUTION_PROPOSALS.md     -- target: append new proposals
  scripts/agent_evolution.py           -- reference: existing checks

Usage:
    python scripts/agent_pattern_promoter.py             -- run promotion
    python scripts/agent_pattern_promoter.py --dry-run   -- show what would be proposed
    python scripts/agent_pattern_promoter.py --stats      -- show pattern frequency stats
"""

import json
import sys
import re
import io
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT      = Path(__file__).resolve().parent.parent
MEMORY_DIR     = REPO_ROOT / ".agent_memory"
PATTERNS_FILE  = MEMORY_DIR / "patterns.json"
EVOLUTION_FILE = REPO_ROOT / "scripts" / "agent_evolution.py"
PROPOSALS_FILE = REPO_ROOT / ".planning" / "EVOLUTION_PROPOSALS.md"

# ── Colors ──────────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"; B = "\033[1m"; X = "\033[0m"


# ── Data Loading ────────────────────────────────────────────────────────────
def load_patterns():
    """Load patterns from agent memory."""
    if not PATTERNS_FILE.exists():
        return {}
    try:
        return json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"{R}Error reading patterns.json: {exc}{X}", file=sys.stderr)
        return {}


def load_evolution_source():
    """Load agent_evolution.py source for coverage checks."""
    if not EVOLUTION_FILE.exists():
        return ""
    return EVOLUTION_FILE.read_text(encoding="utf-8", errors="ignore")


def load_existing_proposals():
    """Load existing EVOLUTION_PROPOSALS.md content."""
    if not PROPOSALS_FILE.exists():
        return ""
    return PROPOSALS_FILE.read_text(encoding="utf-8", errors="ignore")


# ── Analysis ────────────────────────────────────────────────────────────────
def find_high_frequency(patterns, threshold=3):
    """Return patterns with count >= threshold, sorted by count desc."""
    high = []
    for key, data in patterns.items():
        count = data.get("count", 0)
        if count >= threshold:
            high.append((key, data))
    high.sort(key=lambda x: x[1].get("count", 0), reverse=True)
    return high


def pattern_key_to_slug(key):
    """Convert a pattern key to a short slug for function naming."""
    slug = re.sub(r'[^a-zA-Z0-9_]+', '_', key.lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug[:50]


def is_covered_by_evolution(key, evo_source):
    """Check if agent_evolution.py already has a check covering this pattern."""
    evo_lower = evo_source.lower()
    # Extract meaningful keywords from the pattern key (3+ char words)
    words = re.findall(r'[a-zA-Z]{3,}', key)
    if not words:
        return False

    # A pattern is "covered" if multiple keywords appear together in evolution source
    matches = sum(1 for w in words if w.lower() in evo_lower)
    # Require at least 2 keyword matches or >50% of keywords
    return matches >= 2 and matches / len(words) >= 0.4


def get_next_prop_number(existing_content):
    """Find the highest PROP-xxx number and return next."""
    numbers = re.findall(r'PROP-(\d+)', existing_content)
    if numbers:
        return max(int(n) for n in numbers) + 1
    return 1


def estimate_effort(pattern_data):
    """Estimate effort based on pattern characteristics."""
    severity = pattern_data.get("severity", "WARNING")
    if severity == "CRITICAL":
        return "MEDIUM"
    if pattern_data.get("auto_fix"):
        return "LOW"
    return "MEDIUM"


def estimate_impact(pattern_data):
    """Estimate impact based on count and severity."""
    count = pattern_data.get("count", 0)
    severity = pattern_data.get("severity", "WARNING")
    if severity == "CRITICAL" or count >= 5:
        return "HIGH"
    if count >= 3:
        return "MEDIUM"
    return "LOW"


def estimate_risk(pattern_data):
    """Estimate risk of adding this check."""
    severity = pattern_data.get("severity", "WARNING")
    if severity == "FALSE_POSITIVE":
        return "LOW -- pattern may be noise"
    if severity == "CRITICAL":
        return "MEDIUM -- critical path; test thoroughly"
    return "LOW -- advisory check with full test suite as safety net"


def generate_check_function(key, data, slug):
    """Generate a Python function skeleton for agent_evolution.py."""
    safe_key = key.replace('"', '\\"')
    lines = [
        f'def check_{slug}():',
        f'    """Auto-promoted check for recurring pattern: {safe_key}"""',
        f'    section("{safe_key[:50]} -- Promoted Pattern")',
        f'    # Pattern seen {data.get("count", 0)}x from {data.get("first_seen", "?")} to {data.get("last_seen", "?")}',
    ]

    # If there's an auto_fix hint, include detection logic
    if data.get("auto_fix"):
        lines.append(f'    out, code = run("{data["auto_fix"][:80]}")')
        lines.append(f'    if code == 0 and not out.strip():')
        lines.append(f'        ok("Pattern resolved")')
        lines.append(f'        return True')
        lines.append(f'    else:')
        lines.append(f'        err("Pattern still active: {safe_key[:60]}")')
        lines.append(f'        return False')
    else:
        lines.append(f'    # TODO: implement detection logic')
        lines.append(f'    # Hint: {data.get("fix_hint", "manual review needed")[:80]}')
        lines.append(f'    warn("Check not yet implemented -- advisory only")')
        lines.append(f'    return True  # advisory until implemented')

    return "\n".join(f"    {l}" if not l.startswith("def") else l for l in lines)


# ── Proposal Generation ────────────────────────────────────────────────────
def generate_proposals(high_freq, evo_source, existing_content):
    """Generate proposal entries for uncovered high-frequency patterns."""
    next_num = get_next_prop_number(existing_content)
    proposals = []

    for key, data in high_freq:
        # Skip if already covered
        if is_covered_by_evolution(key, evo_source):
            continue

        # Skip if already proposed (check by key substring)
        key_fragment = key[:40]
        if key_fragment in existing_content:
            continue

        slug = pattern_key_to_slug(key)
        code_skeleton = generate_check_function(key, data, slug)
        effort = estimate_effort(data)
        impact = estimate_impact(data)
        risk = estimate_risk(data)

        prop = {
            "number": next_num,
            "key": key,
            "data": data,
            "slug": slug,
            "code": code_skeleton,
            "effort": effort,
            "impact": impact,
            "risk": risk,
        }
        proposals.append(prop)
        next_num += 1

    return proposals


def format_proposal(prop):
    """Format a single proposal as Markdown."""
    data = prop["data"]
    lines = [
        f'## PROP-{prop["number"]:03d}: Promote pattern check -- {prop["key"][:60]}',
        f'**Problem:** Recurring pattern detected {data.get("count", 0)} times: {prop["key"]}',
        f'**Evidence:** count={data.get("count", 0)}, '
        f'first_seen={data.get("first_seen", "?")}, '
        f'last_seen={data.get("last_seen", "?")}',
        f'**Severity:** {data.get("severity", "WARNING")}',
        f'**Solution:** Add check to `agent_evolution.py`:',
        f'```python',
        prop["code"],
        f'```',
        f'**Effort:** {prop["effort"]}',
        f'**Impact:** {prop["impact"]}',
        f'**Risk:** {prop["risk"]}',
        f'',
    ]
    return "\n".join(lines)


# ── Commands ────────────────────────────────────────────────────────────────
def cmd_promote():
    """Run promotion -- find high-frequency patterns, write proposals."""
    print(f"\n{B}{C}== PATTERN PROMOTER -- Biologis Promotion Rite =={X}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    patterns = load_patterns()
    if not patterns:
        print(f"  {Y}No patterns found in {PATTERNS_FILE}{X}")
        return 0

    evo_source = load_evolution_source()
    existing_content = load_existing_proposals()

    high_freq = find_high_frequency(patterns, threshold=3)
    print(f"{C}->{X} Patterns with count >= 3: {len(high_freq)}")

    if not high_freq:
        print(f"  {G}No high-frequency patterns to promote{X}")
        return 0

    # Check coverage
    covered = 0
    uncovered = 0
    for key, data in high_freq:
        if is_covered_by_evolution(key, evo_source):
            covered += 1
            print(f"  {G}COVERED{X}  [{data.get('count', 0)}x] {key[:60]}")
        else:
            uncovered += 1
            print(f"  {Y}UNCOVERED{X} [{data.get('count', 0)}x] {key[:60]}")

    print(f"\n{C}->{X} Covered: {covered} | Uncovered: {uncovered}")

    proposals = generate_proposals(high_freq, evo_source, existing_content)
    if not proposals:
        print(f"\n  {G}All high-frequency patterns are already covered or proposed{X}")
        return 0

    # Write proposals
    print(f"\n{C}->{X} Writing {len(proposals)} new proposal(s) to EVOLUTION_PROPOSALS.md...")

    PROPOSALS_FILE.parent.mkdir(parents=True, exist_ok=True)

    new_section = "\n"
    for prop in proposals:
        new_section += format_proposal(prop) + "\n"

    if existing_content:
        # Append to existing file
        updated = existing_content.rstrip() + "\n" + new_section
    else:
        # Create new file with header
        header = (
            f"# Evolution Proposals\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"Sources analyzed: agent_memory/patterns.json\n\n"
        )
        updated = header + new_section

    PROPOSALS_FILE.write_text(updated, encoding="utf-8")

    print(f"\n{B}{'='*50}{X}")
    print(f"{G}  {len(proposals)} proposal(s) written{X}")
    for prop in proposals:
        print(f"  PROP-{prop['number']:03d}: {prop['key'][:55]}")
    print(f"  The Biologis has spoken (PROMOTION_COMPLETE)")
    print(f"{'='*50}\n")

    return 0


def cmd_dry_run():
    """Show what would be proposed without writing anything."""
    print(f"\n{B}{C}== PATTERN PROMOTER -- Dry Run (Biologis Preview) =={X}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    patterns = load_patterns()
    if not patterns:
        print(f"  {Y}No patterns found{X}")
        return 0

    evo_source = load_evolution_source()
    existing_content = load_existing_proposals()

    high_freq = find_high_frequency(patterns, threshold=3)
    if not high_freq:
        print(f"  {G}No high-frequency patterns (threshold: 3){X}")
        return 0

    proposals = generate_proposals(high_freq, evo_source, existing_content)
    if not proposals:
        print(f"  {G}All high-frequency patterns already covered or proposed{X}")
        return 0

    print(f"  Would write {len(proposals)} proposal(s):\n")
    for prop in proposals:
        print(f"  {Y}PROP-{prop['number']:03d}{X}: {prop['key'][:60]}")
        print(f"    count={prop['data'].get('count', 0)} | "
              f"effort={prop['effort']} | impact={prop['impact']}")
        print(f"    function: check_{prop['slug']}()")
        print()

    print(f"  {C}Run without --dry-run to write proposals{X}\n")
    return 0


def cmd_stats():
    """Show pattern frequency statistics."""
    print(f"\n{B}{C}== PATTERN PROMOTER -- Frequency Stats =={X}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    patterns = load_patterns()
    if not patterns:
        print(f"  {Y}No patterns recorded yet{X}")
        return 0

    evo_source = load_evolution_source()

    # Sort by count descending
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1].get("count", 0), reverse=True)

    total = len(sorted_patterns)
    high = sum(1 for _, d in sorted_patterns if d.get("count", 0) >= 3)
    covered = sum(1 for k, d in sorted_patterns
                  if d.get("count", 0) >= 3 and is_covered_by_evolution(k, evo_source))

    print(f"  {B}Summary:{X}")
    print(f"    Total patterns:      {total}")
    print(f"    High-frequency (>=3): {high}")
    print(f"    Covered by evolution: {covered}")
    print(f"    Promotion candidates: {high - covered}")
    print()

    # Severity breakdown
    severity_counts = {}
    for _, data in sorted_patterns:
        sev = data.get("severity", "UNKNOWN")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    print(f"  {B}By Severity:{X}")
    for sev, cnt in sorted(severity_counts.items()):
        print(f"    {sev}: {cnt}")
    print()

    # Full table
    print(f"  {B}All Patterns (by frequency):{X}")
    print(f"  {'Count':>5}  {'Severity':<15} {'Pattern':<55}")
    print(f"  {'─'*5}  {'─'*15} {'─'*55}")
    for key, data in sorted_patterns:
        count = data.get("count", 0)
        severity = data.get("severity", "?")
        marker = f"{G}*{X}" if count >= 3 else " "
        cov = f" {C}[covered]{X}" if (count >= 3 and is_covered_by_evolution(key, evo_source)) else ""
        print(f"  {count:>5}  {severity:<15} {key[:55]}{marker}{cov}")

    print(f"\n  {C}* = promotion candidate (count >= 3){X}\n")
    return 0


# ── Main ────────────────────────────────────────────────────────────────────
def main():
    try:
        if "--dry-run" in sys.argv:
            return cmd_dry_run()
        elif "--stats" in sys.argv:
            return cmd_stats()
        else:
            return cmd_promote()
    except Exception as exc:
        print(f"{R}Error: {exc}{X}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
