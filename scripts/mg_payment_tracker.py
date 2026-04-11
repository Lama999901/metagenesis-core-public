#!/usr/bin/env python3
"""
MetaGenesis Core -- Payment Funnel Tracker

Tracks anonymous conversion funnel:
  started_onboarding -> completed_verification -> saw_payment -> converted

All tracking is anonymous (session hash only, no personal data).

Usage:
    python scripts/mg_payment_tracker.py --stats
    python scripts/mg_payment_tracker.py --reset

Programmatic:
    from scripts.mg_payment_tracker import track_event
    track_event("started_onboarding", domain="ml", language="en")

PPA: USPTO #63/996,819
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
FUNNEL_PATH = REPO_ROOT / "reports" / "payment_funnel.json"

# ---- Terminal colors --------------------------------------------------------

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
B = "\033[1m"
DIM = "\033[2m"
X = "\033[0m"

# ---- Constants --------------------------------------------------------------

FUNNEL_STAGES = [
    "started_onboarding",
    "completed_verification",
    "saw_payment",
    "converted",
]


def _load_funnel() -> dict:
    """Load funnel data from disk."""
    if FUNNEL_PATH.exists():
        try:
            return json.loads(FUNNEL_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "sessions": {stage: 0 for stage in FUNNEL_STAGES},
        "by_domain": {},
        "by_language": {},
        "conversion_rate": 0.0,
        "last_updated": None,
    }


def _save_funnel(data: dict):
    """Save funnel data to disk."""
    FUNNEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    # Recalculate conversion rate
    total = data["sessions"].get("started_onboarding", 0)
    converted = data["sessions"].get("converted", 0)
    data["conversion_rate"] = converted / total if total > 0 else 0.0

    FUNNEL_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def track_event(stage: str, domain: str = None, language: str = None,
                session_hash: str = None):
    """Track a funnel event.

    Args:
        stage: One of FUNNEL_STAGES
        domain: Optional domain (ml, pharma, finance, etc.)
        language: Optional language code (en, ru, ja, etc.)
        session_hash: Optional anonymous session identifier
    """
    if stage not in FUNNEL_STAGES:
        return

    data = _load_funnel()

    # Increment stage counter
    data["sessions"][stage] = data["sessions"].get(stage, 0) + 1

    # Track by domain
    if domain:
        if domain not in data["by_domain"]:
            data["by_domain"][domain] = {s: 0 for s in FUNNEL_STAGES}
        data["by_domain"][domain][stage] = data["by_domain"][domain].get(stage, 0) + 1

    # Track by language
    if language:
        if language not in data["by_language"]:
            data["by_language"][language] = {s: 0 for s in FUNNEL_STAGES}
        data["by_language"][language][stage] = data["by_language"][language].get(stage, 0) + 1

    _save_funnel(data)


def show_stats():
    """Display funnel statistics."""
    print()
    print(f"{B}{C}  MetaGenesis Core -- Payment Funnel{X}")
    print()

    data = _load_funnel()
    sessions = data.get("sessions", {})

    if all(v == 0 for v in sessions.values()):
        print(f"  {DIM}No funnel data yet.{X}")
        print(f"  {DIM}Run mg_onboard.py to start tracking.{X}")
        print()
        return

    # Overall funnel
    print(f"  {B}Conversion Funnel{X}")
    print(f"  {'=' * 50}")

    prev = None
    for stage in FUNNEL_STAGES:
        count = sessions.get(stage, 0)
        drop = ""
        if prev is not None and prev > 0:
            drop_pct = (1 - count / prev) * 100 if prev > 0 else 0
            drop = f"  {DIM}({drop_pct:.0f}% drop){X}" if drop_pct > 0 else ""
        label = stage.replace("_", " ").title()
        bar_len = min(count, 40)
        bar = "#" * bar_len
        print(f"  {label:.<30} {count:>5}  {G}{bar}{X}{drop}")
        prev = count

    rate = data.get("conversion_rate", 0)
    print(f"  {'=' * 50}")
    print(f"  {B}Conversion rate: {rate:.1%}{X}")
    print()

    # By domain
    by_domain = data.get("by_domain", {})
    if by_domain:
        print(f"  {B}By Domain{X}")
        for domain, stages in sorted(by_domain.items()):
            started = stages.get("started_onboarding", 0)
            converted = stages.get("converted", 0)
            print(f"    {domain:.<20} {started} started, {converted} converted")
        print()

    # By language
    by_lang = data.get("by_language", {})
    if by_lang:
        print(f"  {B}By Language{X}")
        for lang, stages in sorted(by_lang.items()):
            started = stages.get("started_onboarding", 0)
            converted = stages.get("converted", 0)
            print(f"    {lang:.<20} {started} started, {converted} converted")
        print()

    if data.get("last_updated"):
        print(f"  {DIM}Last updated: {data['last_updated']}{X}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mg_payment_tracker",
        description="MetaGenesis Core -- Payment Funnel Tracker",
    )
    parser.add_argument("--stats", action="store_true", help="Show funnel statistics")
    parser.add_argument("--reset", action="store_true", help="Reset funnel data")

    args = parser.parse_args()

    if args.reset:
        data = {
            "sessions": {stage: 0 for stage in FUNNEL_STAGES},
            "by_domain": {},
            "by_language": {},
            "conversion_rate": 0.0,
            "last_updated": None,
        }
        _save_funnel(data)
        print(f"{G}Funnel data reset.{X}")
        return 0

    show_stats()
    return 0


if __name__ == "__main__":
    sys.exit(main())
