#!/usr/bin/env python3
"""
session_close.py — Persistent Cross-Session Memory
====================================================

Every agent starts knowing exactly where the system is.

Usage:
    python scripts/session_close.py --read                    # Show current state (5 lines)
    python scripts/session_close.py --summary "What happened"  # Close session + update state
    python scripts/session_close.py --next "What to do next"   # Override next priority

What it does:
    1. Reads GSD state automatically (version, test count, ratio)
    2. Overwrites CLAUDE.md "## CURRENT STATE" section — never appends, stays short
    3. Appends one JSON line to session_log.jsonl
    4. Updates system_manifest.json with session metadata
    5. If proof_library has new entries, appends insight to WHAT_WE_LEARNED.md

No external dependencies. Stdlib only.
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
MANIFEST = REPO_ROOT / "system_manifest.json"
SESSION_LOG = REPO_ROOT / "session_log.jsonl"
PROOF_INDEX = REPO_ROOT / "proof_library" / "index.json"
WHAT_WE_LEARNED = REPO_ROOT / "proof_library" / "WHAT_WE_LEARNED.md"


def _read_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {}


def _write_manifest(data: dict) -> None:
    MANIFEST.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _get_test_count() -> int:
    """Get actual test count from pytest."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no", "--co", "-q"],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
            encoding="utf-8", errors="replace", timeout=60,
        )
        # Count lines that look like test items (contain ::)
        lines = [l for l in r.stdout.splitlines() if "::" in l]
        return len(lines) if lines else 0
    except (subprocess.TimeoutExpired, OSError):
        # Fallback to manifest
        return _read_manifest().get("test_count", 0)


def _get_ratio() -> tuple[int, float]:
    """Get real verification count and ratio from proof_library."""
    if not PROOF_INDEX.exists():
        return 0, 0.0
    try:
        entries = json.loads(PROOF_INDEX.read_text(encoding="utf-8"))
        real_count = sum(1 for e in entries if not e.get("is_synthetic", True))
        synthetic = 20
        total = real_count + synthetic
        ratio = real_count / total if total > 0 else 0.0
        return real_count, ratio
    except (json.JSONDecodeError, OSError):
        return 0, 0.0


def _get_version() -> str:
    manifest = _read_manifest()
    return manifest.get("version", "unknown")


def read_state() -> dict:
    """Read current system state — the 5-line summary."""
    version = _get_version()
    manifest = _read_manifest()
    test_count = manifest.get("test_count", 0)
    real_count, ratio = _get_ratio()

    # Read last session from log
    last_summary = "No previous session recorded"
    next_priority = "Run session_close.py --summary after your first session"
    if SESSION_LOG.exists():
        lines = SESSION_LOG.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            try:
                last = json.loads(lines[-1])
                last_summary = f"[{last.get('date', '?')[:10]}] {last.get('summary', '?')}"
                next_priority = last.get("next", next_priority)
            except json.JSONDecodeError:
                pass

    state = {
        "version": version,
        "tests": test_count,
        "real_verifications": real_count,
        "ratio": ratio,
        "last_session": last_summary,
        "next_priority": next_priority,
    }
    return state


def print_state(state: dict) -> None:
    """Print the 5-line state summary."""
    print(f"  Version:    v{state['version']} | {state['tests']} tests | {state['real_verifications']} real verifications")
    print(f"  Ratio:      {state['ratio']:.1%} real ({state['real_verifications']}/{ state['real_verifications'] + 20})")
    print(f"  Last:       {state['last_session']}")
    print(f"  Next:       {state['next_priority']}")
    lib_exists = PROOF_INDEX.exists()
    print(f"  Door:       {'OPEN (mg_claim_builder.py)' if lib_exists else 'CLOSED'}")


def update_claude_md(state: dict, summary: str, next_priority: str) -> None:
    """Overwrite the ## CURRENT STATE section in CLAUDE.md."""
    if not CLAUDE_MD.exists():
        return

    text = CLAUDE_MD.read_text(encoding="utf-8")
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    new_section = f"""## CURRENT STATE (v{state['version']})

```
Date:        {date}
Tests:       {state['tests']} passing
Real ratio:  {state['ratio']:.1%} ({state['real_verifications']} real / 20 synthetic)
Templates:   20 domain templates (all have 4-step Step Chain)
Layers:      5 verification (integrity + semantic + step chain + signing + temporal)
Checks:      21 (agent_evolution.py)
Last:        {summary[:100]}
Next:        {next_priority[:100]}
```"""

    # Replace the section between ## CURRENT STATE and the next ---
    pattern = r"## CURRENT STATE \(v[^)]*\)\n\n```\n.*?```"
    if re.search(pattern, text, re.DOTALL):
        text = re.sub(pattern, new_section, text, count=1, flags=re.DOTALL)
    else:
        # Fallback: find ## CURRENT STATE and replace until next ---
        start = text.find("## CURRENT STATE")
        if start >= 0:
            # Find the closing ``` after the opening ```
            code_start = text.find("```\n", start)
            if code_start >= 0:
                code_end = text.find("```", code_start + 4)
                if code_end >= 0:
                    text = text[:start] + new_section + text[code_end + 3:]

    # Update the header line date
    text = re.sub(
        r"> Last updated: .*",
        f"> Last updated: {date} | v{state['version']} LIVE | 20 templates | {state['tests']} tests",
        text,
    )

    CLAUDE_MD.write_text(text, encoding="utf-8")


def append_session_log(summary: str, state: dict, built: list, next_priority: str) -> None:
    """Append one JSON line to session_log.jsonl."""
    entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "tests": state["tests"],
        "ratio": round(state["ratio"], 4),
        "real_verifications": state["real_verifications"],
        "built": built,
        "next": next_priority,
    }
    with open(SESSION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def update_manifest_session(summary: str, next_priority: str) -> None:
    """Update system_manifest.json with session metadata."""
    manifest = _read_manifest()
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    manifest["last_session_date"] = date
    manifest["last_session_summary"] = summary[:200]
    manifest["next_priority"] = next_priority[:200]
    _write_manifest(manifest)


def update_what_we_learned(state: dict) -> None:
    """If proof_library has entries, append insight."""
    if not PROOF_INDEX.exists():
        return
    try:
        entries = json.loads(PROOF_INDEX.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return

    if not entries:
        return

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    latest = entries[-1]

    if not WHAT_WE_LEARNED.exists():
        WHAT_WE_LEARNED.write_text(
            "# What We Learned — Proof Library Insights\n\n",
            encoding="utf-8",
        )

    text = WHAT_WE_LEARNED.read_text(encoding="utf-8")
    # Don't duplicate if latest entry already recorded
    if latest.get("id", "") in text:
        return

    insight = (
        f"## {date}: {latest['id']}\n"
        f"- Domain: {latest.get('domain', '?')}\n"
        f"- Proved: {latest.get('what_proved', '?')}\n"
        f"- NOT proved: {latest.get('what_not_proved', '?')}\n"
        f"- Duration: {latest.get('duration_ms', 0)}ms\n\n"
    )
    WHAT_WE_LEARNED.write_text(text + insight, encoding="utf-8")


def close_session(summary: str, next_priority: str = "", built: list = None) -> dict:
    """Close a session: update all persistent state."""
    if built is None:
        built = []

    state = read_state()

    if not next_priority:
        next_priority = "Verify a real external computation to push ratio toward 20%"

    # 1. Update CLAUDE.md
    update_claude_md(state, summary, next_priority)

    # 2. Append to session log
    append_session_log(summary, state, built, next_priority)

    # 3. Update manifest
    update_manifest_session(summary, next_priority)

    # 4. Update what we learned
    update_what_we_learned(state)

    return state


def main():
    parser = argparse.ArgumentParser(description="Cross-session memory for MetaGenesis Core")
    parser.add_argument("--read", action="store_true", help="Show current state (5 lines)")
    parser.add_argument("--summary", type=str, help="Close session with this summary")
    parser.add_argument("--next", type=str, default="", help="Override next priority")
    parser.add_argument("--built", type=str, nargs="*", default=[], help="List of things built")

    args = parser.parse_args()

    if args.read:
        state = read_state()
        print_state(state)
        return 0

    if args.summary:
        state = close_session(args.summary, args.next, args.built)
        print(f"Session closed. State updated.")
        print_state(state)
        return 0

    # Default: show state
    state = read_state()
    print_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
