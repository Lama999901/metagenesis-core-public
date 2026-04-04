#!/usr/bin/env python3
"""
MetaGenesis Core -- Pilot Onboarding Agent
==========================================
Autonomous agent that processes pilot form submissions:
  CSV in -> domain detection -> bundle generation -> email drafts -> queue tracking

Converts a 2-hour manual pilot onboarding process into 2 minutes.
Each verified bundle proves computation integrity for the $299 conversion pipeline.

Usage:
    python scripts/agent_pilot.py --process submissions.csv
    python scripts/agent_pilot.py --status
    python scripts/agent_pilot.py --mark-sent alice@example.com

PPA: USPTO #63/996,819
"""

import argparse
import csv
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding (CLAUDE.md BUG 4)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import mg_client after path setup
from scripts.mg_client import run_claim, create_bundle, verify_bundle  # noqa: E402

# ---- Paths ------------------------------------------------------------------

QUEUE_PATH = REPO_ROOT / "reports" / "pilot_queue.json"
DRAFTS_DIR = REPO_ROOT / "reports" / "pilot_drafts"
BUNDLES_DIR = REPO_ROOT / "reports" / "pilot_bundles"

# ---- Domain detection (PILOT-01) -------------------------------------------

DOMAIN_KEYWORDS = {
    "ml": [
        "ml", "ai", "model", "accuracy", "benchmark", "neural",
        "deep learning", "machine learning", "classification",
        "regression", "training", "inference",
    ],
    "pharma": [
        "drug", "pharma", "admet", "fda", "clinical", "compound",
        "pharmaceutical", "biotech", "molecule", "toxicity",
    ],
    "materials": [
        "material", "steel", "aluminum", "titanium", "copper",
        "modulus", "conductivity", "alloy", "metal", "composite",
    ],
    "finance": [
        "var", "risk", "basel", "portfolio", "finance",
        "financial", "trading", "hedge", "credit", "market risk",
    ],
    "digital_twin": [
        "fem", "sensor", "twin", "iot", "displacement",
        "calibration", "simulation", "digital twin", "actuator",
    ],
}


def detect_domain(description: str) -> str:
    """Detect domain from description text using keyword matching.

    Returns the domain string (ml, pharma, materials, finance, digital_twin).
    Returns 'ml' as default if no keywords match.
    """
    if not description:
        return "ml"
    text = description.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[domain] = score
    if not scores:
        return "ml"
    return max(scores, key=scores.get)


# ---- CSV reading (PILOT-01) ------------------------------------------------

def read_submissions(csv_path: str) -> list:
    """Read pilot submissions from CSV file.

    Expected columns: name, email, company, domain_description, date
    Skips rows with missing name or email.
    Returns list of dicts.
    """
    submissions = []
    csv_file = Path(csv_path)
    if not csv_file.exists():
        print(f"ERROR: CSV file not found: {csv_path}", file=sys.stderr)
        return submissions

    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):  # line 2 = first data row
            name = (row.get("name") or "").strip()
            email = (row.get("email") or "").strip()
            if not name or not email:
                print(
                    f"WARNING: Skipping row {i} -- missing name or email",
                    file=sys.stderr,
                )
                continue
            submissions.append({
                "name": name,
                "email": email,
                "company": (row.get("company") or "").strip(),
                "domain_description": (row.get("domain_description") or "").strip(),
                "date": (row.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")).strip(),
            })
    return submissions


# ---- Queue management (PILOT-04) -------------------------------------------

def load_queue() -> dict:
    """Load pilot queue from reports/pilot_queue.json.

    Creates empty queue if file does not exist.
    """
    if QUEUE_PATH.exists():
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def save_queue(queue: dict) -> None:
    """Save pilot queue to reports/pilot_queue.json."""
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, sort_keys=True)
        f.write("\n")


def _find_entry_by_email(queue: dict, email: str) -> dict:
    """Find queue entry by email address. Returns None if not found."""
    for entry in queue.get("entries", []):
        if entry.get("email", "").lower() == email.lower():
            return entry
    return None


# ---- Email draft generation (PILOT-03) -------------------------------------

def _sanitize_name(name: str) -> str:
    """Sanitize name for filename: lowercase, replace spaces with underscores."""
    clean = re.sub(r"[^\w\s-]", "", name)
    return re.sub(r"\s+", "_", clean).lower()


def generate_draft(entry: dict, claim_result: dict, bundle_dir: Path, verified: bool) -> Path:
    """Generate a plain-text email draft for a pilot submission.

    Returns path to the draft file.
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_name(entry["name"])
    date_str = entry.get("date", "unknown")
    draft_path = DRAFTS_DIR / f"{safe_name}_{date_str}.txt"

    domain_detected = entry.get("domain_detected", "unknown")
    result_str = "PASS" if verified else "FAIL"

    lines = [
        f"Subject: MetaGenesis Core -- Verification Bundle Ready",
        "",
        f"Hi {entry['name']},",
        "",
        "Your MetaGenesis Core pilot verification is complete.",
        "",
        f"Company: {entry.get('company', 'N/A')}",
        f"Domain: {domain_detected}",
        f"Result: {result_str}",
        f"Bundle: {bundle_dir}",
    ]

    if not verified:
        lines.append("")
        lines.append("Note: The verification result requires manual review.")
        lines.append("Our team will follow up with details.")

    lines.extend([
        "",
        "Your verified bundle proves that the computation produced exactly this",
        "result, at exactly this time, in exactly this way. It is independently",
        "auditable offline -- no trust required.",
        "",
        "Questions? Reply to this email.",
        "",
        "Best,",
        "Yehor Bazhynov",
        "MetaGenesis Core",
        "yehor@metagenesis-core.dev",
    ])

    draft_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return draft_path


# ---- Main pipeline (PILOT-02 + orchestration) ------------------------------

def process_submissions(csv_path: str) -> int:
    """Process all submissions from CSV: detect domain, run claim, create bundle,
    verify, generate email draft, update queue.

    Returns 0 on success, 1 on any failure.
    """
    submissions = read_submissions(csv_path)
    if not submissions:
        print("No valid submissions found in CSV.")
        return 1

    queue = load_queue()
    processed_count = 0
    fail_count = 0
    domains_seen = set()

    for sub in submissions:
        name = sub["name"]
        email = sub["email"]
        date_str = sub["date"]

        # Skip already-processed entries
        existing = _find_entry_by_email(queue, email)
        if existing and existing.get("status") in ("processed", "sent"):
            print(f"  SKIP: {name} <{email}> -- already {existing['status']}")
            continue

        # Detect domain
        domain = detect_domain(sub["domain_description"])
        flagged = (domain == "ml" and not any(
            kw in sub["domain_description"].lower()
            for kw in DOMAIN_KEYWORDS["ml"]
        ))
        domains_seen.add(domain)

        print(f"  Processing: {name} <{email}>")
        print(f"    Domain: {domain}" + (" (flagged for review)" if flagged else ""))

        # Run claim via mg_client
        try:
            claim_result = run_claim(domain)
        except Exception as e:
            print(f"    ERROR: Claim failed -- {e}", file=sys.stderr)
            fail_count += 1
            continue

        # Create bundle
        safe_name = _sanitize_name(name)
        bundle_output = str(BUNDLES_DIR / f"{safe_name}_{date_str}")
        try:
            bundle_dir = create_bundle(claim_result, output_dir=bundle_output)
        except Exception as e:
            print(f"    ERROR: Bundle creation failed -- {e}", file=sys.stderr)
            fail_count += 1
            continue

        # Verify bundle
        try:
            verified, layer_results = verify_bundle(bundle_dir)
        except Exception as e:
            print(f"    ERROR: Verification failed -- {e}", file=sys.stderr)
            verified = False
            layer_results = []

        result_str = "PASS" if verified else "FAIL"
        print(f"    Verification: {result_str}")

        # Build queue entry
        entry = {
            "name": name,
            "email": email,
            "company": sub.get("company", ""),
            "domain_description": sub.get("domain_description", ""),
            "date": date_str,
            "domain_detected": domain,
            "status": "processed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "bundle_path": str(bundle_dir),
            "draft_path": "",
            "flagged_for_review": flagged,
            "verified": verified,
        }

        # Generate email draft
        try:
            draft_path = generate_draft(entry, claim_result, bundle_dir, verified)
            entry["draft_path"] = str(draft_path)
            print(f"    Draft: {draft_path.name}")
        except Exception as e:
            print(f"    ERROR: Draft generation failed -- {e}", file=sys.stderr)

        # Update queue (replace existing or append)
        if existing:
            idx = queue["entries"].index(existing)
            queue["entries"][idx] = entry
        else:
            queue["entries"].append(entry)

        processed_count += 1

    save_queue(queue)

    # Summary
    print()
    print(f"  Processed: {processed_count} submission(s)")
    print(f"  Domains:   {', '.join(sorted(domains_seen)) if domains_seen else 'none'}")
    if fail_count:
        print(f"  Failures:  {fail_count}")
    else:
        print("  Result:    All PASS")

    return 1 if fail_count > 0 else 0


# ---- Status display ---------------------------------------------------------

def show_status() -> int:
    """Display current queue status."""
    queue = load_queue()
    entries = queue.get("entries", [])

    if not entries:
        print("Pilot queue is empty.")
        return 0

    # Table header
    print(f"  {'Name':<20} {'Email':<30} {'Domain':<14} {'Status':<10} {'Processed At'}")
    print(f"  {'-'*20} {'-'*30} {'-'*14} {'-'*10} {'-'*20}")

    for e in entries:
        name = e.get("name", "?")[:20]
        email = e.get("email", "?")[:30]
        domain = e.get("domain_detected", "?")[:14]
        status = e.get("status", "?")
        processed = e.get("processed_at", "?")[:19]
        flag = " *" if e.get("flagged_for_review") else ""
        print(f"  {name:<20} {email:<30} {domain:<14} {status:<10} {processed}{flag}")

    # Counts
    pending = sum(1 for e in entries if e.get("status") == "pending")
    processed = sum(1 for e in entries if e.get("status") == "processed")
    sent = sum(1 for e in entries if e.get("status") == "sent")
    print()
    print(f"  Total: {len(entries)} | Pending: {pending} | Processed: {processed} | Sent: {sent}")
    if any(e.get("flagged_for_review") for e in entries):
        print("  * = flagged for manual review (domain auto-detected)")

    return 0


# ---- Mark sent --------------------------------------------------------------

def mark_sent(email: str) -> int:
    """Mark a processed entry as sent."""
    queue = load_queue()
    entry = _find_entry_by_email(queue, email)

    if not entry:
        print(f"ERROR: No entry found for {email}", file=sys.stderr)
        return 1

    if entry.get("status") != "processed":
        print(
            f"ERROR: Entry for {email} has status '{entry.get('status')}' "
            f"-- can only mark 'processed' entries as sent",
            file=sys.stderr,
        )
        return 1

    entry["status"] = "sent"
    entry["sent_at"] = datetime.now(timezone.utc).isoformat()
    save_queue(queue)
    print(f"  Marked as sent: {entry['name']} <{email}>")
    return 0


# ---- CLI (PILOT-05) --------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="agent_pilot",
        description="MetaGenesis Core -- Pilot Onboarding Agent",
        epilog=(
            "Examples:\n"
            "  python scripts/agent_pilot.py --process submissions.csv\n"
            "  python scripts/agent_pilot.py --status\n"
            "  python scripts/agent_pilot.py --mark-sent alice@example.com\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--process",
        metavar="FILE",
        help="Process a CSV file of pilot submissions",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current pilot queue status",
    )
    parser.add_argument(
        "--mark-sent",
        metavar="EMAIL",
        help="Mark a processed entry as sent by email address",
    )

    args = parser.parse_args()

    if args.process:
        return process_submissions(args.process)
    elif args.status:
        return show_status()
    elif args.mark_sent:
        return mark_sent(args.mark_sent)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
