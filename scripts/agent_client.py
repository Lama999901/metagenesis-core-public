#!/usr/bin/env python3
"""
MetaGenesis Core -- Client Session Memory

Records every client interaction for pipeline analytics and follow-up.

Usage:
    python scripts/agent_client.py record --domain ml --result "PASS"
    python scripts/agent_client.py record --domain pharma --result "FAIL" --notes "threshold too tight"
    python scripts/agent_client.py recall
    python scripts/agent_client.py stats

Pure stdlib. No external dependencies.
"""

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO_ROOT / ".agent_memory"
SESSIONS_FILE = MEMORY_DIR / "client_sessions.json"

# Terminal colors
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
B = "\033[1m"
DIM = "\033[2m"
X = "\033[0m"


def _load_sessions() -> list:
    """Load client sessions from disk."""
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
    return []


def _save_sessions(sessions: list) -> None:
    """Save client sessions to disk."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_FILE.write_text(
        json.dumps(sessions, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def record_session(
    domain: str,
    result: str,
    notes: str = "",
    claim_id: str = "",
    bundle_path: str = "",
) -> dict:
    """Record a client interaction session.

    Args:
        domain: Domain name (ml, pharma, finance, materials, digital_twin)
        result: Result string (PASS, FAIL, ERROR, etc.)
        notes: Optional notes about the session
        claim_id: Optional claim ID that was run
        bundle_path: Optional path to the generated bundle

    Returns:
        The session record dict.
    """
    sessions = _load_sessions()

    session = {
        "id": len(sessions) + 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "result": result.upper(),
        "claim_id": claim_id,
        "bundle_path": bundle_path,
        "notes": notes,
    }

    sessions.append(session)
    _save_sessions(sessions)
    return session


def recall_sessions() -> list:
    """Return all recorded sessions."""
    return _load_sessions()


def get_stats() -> dict:
    """Compute summary statistics over all sessions."""
    sessions = _load_sessions()
    if not sessions:
        return {
            "total": 0,
            "by_domain": {},
            "by_result": {},
            "first_session": None,
            "last_session": None,
        }

    by_domain = {}
    by_result = {}
    for s in sessions:
        d = s.get("domain", "unknown")
        r = s.get("result", "UNKNOWN")
        by_domain[d] = by_domain.get(d, 0) + 1
        by_result[r] = by_result.get(r, 0) + 1

    return {
        "total": len(sessions),
        "by_domain": by_domain,
        "by_result": by_result,
        "first_session": sessions[0].get("timestamp"),
        "last_session": sessions[-1].get("timestamp"),
    }


def cmd_record(args) -> int:
    """Record a new client session."""
    session = record_session(
        domain=args.domain,
        result=args.result,
        notes=getattr(args, "notes", "") or "",
        claim_id=getattr(args, "claim_id", "") or "",
        bundle_path=getattr(args, "bundle_path", "") or "",
    )
    print(f"{G}Session #{session['id']} recorded{X}")
    print(f"  Domain: {session['domain']}")
    print(f"  Result: {session['result']}")
    if session["notes"]:
        print(f"  Notes:  {session['notes']}")
    return 0


def cmd_recall(args) -> int:
    """Show all recorded sessions."""
    sessions = recall_sessions()
    if not sessions:
        print(f"{Y}No client sessions recorded yet.{X}")
        print(f"Record one: python scripts/agent_client.py record --domain ml --result PASS")
        return 0

    print(f"\n{B}Client Sessions ({len(sessions)} total){X}\n")
    print(f"  {'#':<4} {'Timestamp':<26} {'Domain':<14} {'Result':<8} {'Notes'}")
    print(f"  {'-' * 4} {'-' * 26} {'-' * 14} {'-' * 8} {'-' * 30}")
    for s in sessions:
        sid = s.get("id", "?")
        ts = s.get("timestamp", "?")[:19]
        dom = s.get("domain", "?")
        res = s.get("result", "?")
        notes = s.get("notes", "")[:30]
        color = G if res == "PASS" else R if res == "FAIL" else Y
        print(f"  {sid:<4} {ts:<26} {dom:<14} {color}{res:<8}{X} {notes}")
    print()
    return 0


def cmd_stats(args) -> int:
    """Show session statistics."""
    stats = get_stats()
    if stats["total"] == 0:
        print(f"{Y}No sessions recorded yet.{X}")
        return 0

    print(f"\n{B}Client Session Statistics{X}\n")
    print(f"  Total sessions: {stats['total']}")
    print(f"  First:          {stats['first_session']}")
    print(f"  Last:           {stats['last_session']}")

    print(f"\n  {B}By Domain:{X}")
    for domain, count in sorted(stats["by_domain"].items()):
        print(f"    {domain:<16} {count}")

    print(f"\n  {B}By Result:{X}")
    for result, count in sorted(stats["by_result"].items()):
        color = G if result == "PASS" else R if result == "FAIL" else Y
        print(f"    {color}{result:<16}{X} {count}")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="agent_client",
        description="MetaGenesis Core -- Client Session Memory",
    )
    sub = parser.add_subparsers(dest="command")

    rec = sub.add_parser("record", help="Record a client session")
    rec.add_argument("--domain", required=True, help="Domain (ml, pharma, finance, materials, digital_twin)")
    rec.add_argument("--result", required=True, help="Result (PASS, FAIL, ERROR)")
    rec.add_argument("--notes", default="", help="Optional notes")
    rec.add_argument("--claim-id", default="", help="Claim ID that was run")
    rec.add_argument("--bundle-path", default="", help="Path to generated bundle")

    sub.add_parser("recall", help="Show all sessions")
    sub.add_parser("stats", help="Show statistics")

    args = parser.parse_args()

    if args.command == "record":
        return cmd_record(args)
    elif args.command == "recall":
        return cmd_recall(args)
    elif args.command == "stats":
        return cmd_stats(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
