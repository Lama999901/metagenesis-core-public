#!/usr/bin/env python3
"""
MetaGenesis Core -- Response Infrastructure Agent
==================================================
Prepares complete response kits (draft + bundle + queue entry) for outreach
replies. 7 domain mappings, fuzzy contact matching, 60-second turnaround.

Usage:
    python scripts/agent_responder.py --prepare "Anand Patronus ML"
    python scripts/agent_responder.py --status
    python scripts/agent_responder.py --list-domains
    python scripts/agent_responder.py --update-status "Anand" "reviewed"

PPA: USPTO #63/996,819
"""

import argparse
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

from scripts.mg_client import run_claim, create_bundle, verify_bundle  # noqa: E402

# ---- Paths ------------------------------------------------------------------

QUEUE_PATH = REPO_ROOT / "reports" / "response_queue.json"
DRAFTS_DIR = REPO_ROOT / "reports" / "response_drafts"
BUNDLES_DIR = REPO_ROOT / "reports" / "response_bundles"

# ---- Valid status flow ------------------------------------------------------

VALID_STATUSES = ["prepared", "reviewed", "bundle_sent", "replied", "converted"]

# ---- Domain mappings (RESP-02) ----------------------------------------------

# Each mapping: keywords (for fuzzy match), claims list, mg_client domain,
# display name, and draft-specific context.

DOMAIN_MAPPINGS = {
    "patronus": {
        "keywords": ["patronus", "anand", "patronus ai"],
        "claims": ["ML_BENCH-01"],
        "mg_domain": "ml",
        "company": "Patronus AI",
        "display_domain": "ML benchmark accuracy verification",
        "outreach_context": (
            "We saw your work on AI evaluation and thought MetaGenesis Core "
            "could add a cryptographic layer to benchmark integrity."
        ),
        "result_description": (
            "The attached bundle proves the ML accuracy claim is tamper-evident "
            "and independently verifiable -- no model access required."
        ),
        "next_step": (
            "Would it be useful to run this against one of your own "
            "evaluation datasets so you can see the full chain?"
        ),
    },
    "bureau_veritas": {
        "keywords": ["bureau veritas", "philipp", "bv", "bureau"],
        "claims": ["FINRISK-01"],
        "mg_domain": "finance",
        "company": "Bureau Veritas",
        "display_domain": "Value at Risk model verification (Basel III)",
        "outreach_context": (
            "We reached out because Basel III requires independent VaR "
            "validation -- and MetaGenesis Core does exactly that."
        ),
        "result_description": (
            "The bundle proves the VaR calculation was executed correctly "
            "and can be verified offline by a regulator without model access."
        ),
        "next_step": (
            "Would it help to see this applied to a sample portfolio "
            "that mirrors one of your typical validation engagements?"
        ),
    },
    "chollet": {
        "keywords": ["chollet", "arc", "arc-agi", "francois"],
        "claims": ["ML_BENCH-02"],
        "mg_domain": "ml",
        "company": "ARC / Chollet",
        "display_domain": "ML regression certificate verification",
        "outreach_context": (
            "Your work on measuring real intelligence in AI made us think "
            "MetaGenesis Core could help lock benchmark results cryptographically."
        ),
        "result_description": (
            "The bundle proves the regression benchmark result is tamper-evident "
            "-- anyone can verify it offline with a single command."
        ),
        "next_step": (
            "Would you be interested in seeing this applied to an ARC-style "
            "evaluation to see how the cryptographic chain works end-to-end?"
        ),
    },
    "percy_liang": {
        "keywords": ["percy", "liang", "helm", "stanford"],
        "claims": ["ML_BENCH-03"],
        "mg_domain": "ml",
        "company": "Stanford HELM / Percy Liang",
        "display_domain": "ML time series certificate verification",
        "outreach_context": (
            "HELM set the standard for transparent benchmarking -- MetaGenesis Core "
            "adds a cryptographic proof layer on top."
        ),
        "result_description": (
            "The bundle proves the time-series benchmark result with a "
            "4-step hash chain that breaks if anything is changed."
        ),
        "next_step": (
            "Would it be useful to run this on a HELM leaderboard entry "
            "so you can evaluate the verification independently?"
        ),
    },
    "iqvia": {
        "keywords": ["iqvia", "raja", "shankar", "raja shankar"],
        "claims": ["ML_BENCH-01", "PHARMA-01"],
        "mg_domain": "pharma",
        "company": "IQVIA",
        "display_domain": "ADMET prediction verification (FDA 21 CFR Part 11)",
        "outreach_context": (
            "FDA 2025 requires verifiable AI artifacts for IND filing -- "
            "MetaGenesis Core produces exactly that for $299 per bundle."
        ),
        "result_description": (
            "The bundle proves the ADMET prediction was computed correctly "
            "and meets FDA audit requirements -- verifiable offline."
        ),
        "next_step": (
            "Would it help to see this on one of your internal ADMET "
            "pipelines to evaluate fit with your regulatory workflow?"
        ),
    },
    "lmarena": {
        "keywords": ["lmarena", "arena", "lm arena", "chatbot arena"],
        "claims": ["ML_BENCH-01"],
        "mg_domain": "ml",
        "company": "LMArena",
        "display_domain": "ML benchmark integrity verification",
        "outreach_context": (
            "Benchmark gaming is a real problem -- MetaGenesis Core makes "
            "results tamper-evident so leaderboard entries carry proof."
        ),
        "result_description": (
            "The bundle proves the benchmark accuracy claim with a "
            "cryptographic hash chain. Change any input -- the hash breaks."
        ),
        "next_step": (
            "Would you want to pilot this on a few leaderboard submissions "
            "to see how it integrates with your evaluation pipeline?"
        ),
    },
    "south_pole": {
        "keywords": ["south pole", "southpole", "carbon", "esg", "climate"],
        "claims": ["DATA-PIPE-01", "ML_BENCH-01"],
        "mg_domain": "ml",
        "company": "South Pole",
        "display_domain": "Data pipeline + ML verification for ESG",
        "outreach_context": (
            "Carbon credit models need verifiable proof that the computation "
            "was executed correctly. MetaGenesis Core provides that."
        ),
        "result_description": (
            "The bundle proves the ML model output is tamper-evident -- "
            "auditors can verify the result offline without model access."
        ),
        "next_step": (
            "Would it be useful to see this applied to a sample carbon "
            "credit calculation so you can evaluate the proof chain?"
        ),
    },
}

DEFAULT_MAPPING = {
    "claims": ["DATA-PIPE-01"],
    "mg_domain": "ml",
    "company": "Unknown",
    "display_domain": "Data pipeline quality verification",
    "outreach_context": (
        "MetaGenesis Core certifies computations -- one command verifies "
        "that a result was produced correctly, at a specific time, "
        "without trusting anyone."
    ),
    "result_description": (
        "The attached bundle proves the computation result with a "
        "cryptographic hash chain. Verify it offline with one command."
    ),
    "next_step": (
        "Would you like to see this applied to one of your own "
        "computations so you can evaluate the verification firsthand?"
    ),
}


# ---- Fuzzy matching (RESP-02) -----------------------------------------------

def match_domain(contact_text: str) -> tuple:
    """Match contact text to a domain mapping using fuzzy keyword matching.

    Returns (mapping_key, mapping_dict). Falls back to DEFAULT_MAPPING
    with key "default" if no keywords match.
    """
    if not contact_text:
        return "default", DEFAULT_MAPPING

    text = contact_text.lower().strip()

    # Score each mapping by keyword hits
    best_key = None
    best_score = 0

    for key, mapping in DOMAIN_MAPPINGS.items():
        score = 0
        for kw in mapping["keywords"]:
            if kw in text:
                score += len(kw)  # longer keyword matches are weighted more
        if score > best_score:
            best_score = score
            best_key = key

    if best_key and best_score > 0:
        return best_key, DOMAIN_MAPPINGS[best_key]

    return "default", DEFAULT_MAPPING


# ---- Queue management (RESP-05) --------------------------------------------

def load_queue() -> dict:
    """Load response queue from reports/response_queue.json."""
    if QUEUE_PATH.exists():
        with open(QUEUE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"entries": []}


def save_queue(queue: dict) -> None:
    """Save response queue to reports/response_queue.json."""
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, sort_keys=True)
        f.write("\n")


def _find_entry_by_contact(queue: dict, contact: str) -> dict:
    """Find queue entry by contact name (case-insensitive partial match)."""
    contact_lower = contact.lower().strip()
    for entry in queue.get("entries", []):
        if entry.get("contact", "").lower() == contact_lower:
            return entry
    # Partial match fallback
    for entry in queue.get("entries", []):
        if contact_lower in entry.get("contact", "").lower():
            return entry
    return None


# ---- Sanitize helper --------------------------------------------------------

def _sanitize_name(name: str) -> str:
    """Sanitize name for filename: lowercase, replace spaces with underscores."""
    clean = re.sub(r"[^\w\s-]", "", name)
    return re.sub(r"\s+", "_", clean).lower()


# ---- Draft generation (RESP-03) --------------------------------------------

_DRAFT_TEMPLATE = """\
Hi {contact_name},

{outreach_context}

I put together a quick verification bundle for your domain -- {display_domain}.

Result: {claim_result}

{result_description}

You can verify it yourself with one command:

  python scripts/mg.py verify --pack bundle.zip

Everything is offline. No API keys, no accounts, no trust assumptions.

{next_step}

Best,
Yehor Bazhynov
MetaGenesis Core
yehor@metagenesis-core.dev
"""


def generate_draft(
    contact_name: str,
    mapping: dict,
    claim_result_str: str,
    date_str: str,
) -> Path:
    """Generate a plain-text response draft.

    Returns path to the draft file.
    """
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_name(contact_name)
    draft_path = DRAFTS_DIR / f"{safe_name}_{date_str}.txt"

    text = _DRAFT_TEMPLATE.format(
        contact_name=contact_name,
        outreach_context=mapping.get("outreach_context", DEFAULT_MAPPING["outreach_context"]),
        display_domain=mapping.get("display_domain", DEFAULT_MAPPING["display_domain"]),
        claim_result=claim_result_str,
        result_description=mapping.get("result_description", DEFAULT_MAPPING["result_description"]),
        next_step=mapping.get("next_step", DEFAULT_MAPPING["next_step"]),
    )

    draft_path.write_text(text, encoding="utf-8")
    return draft_path


# ---- Bundle generation (RESP-04) -------------------------------------------

def generate_bundle(contact_name: str, mg_domain: str, date_str: str) -> tuple:
    """Generate a verification bundle for the given domain.

    Returns (bundle_dir, claim_result, verified).
    """
    BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = _sanitize_name(contact_name)
    bundle_output = str(BUNDLES_DIR / f"{safe_name}_{date_str}")

    claim_result = run_claim(mg_domain)
    bundle_dir = create_bundle(claim_result, output_dir=bundle_output)
    verified, _layer_results = verify_bundle(bundle_dir)

    return bundle_dir, claim_result, verified


# ---- Prepare command (RESP-01) ----------------------------------------------

def prepare_response(contact_text: str) -> int:
    """Prepare a complete response kit: draft + bundle + queue entry.

    Args:
        contact_text: Free-form text like "Anand Patronus ML" or "chollet arc"

    Returns 0 on success, 1 on failure.
    """
    if not contact_text or not contact_text.strip():
        print("ERROR: Contact name cannot be empty.", file=sys.stderr)
        return 1

    contact_text = contact_text.strip()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Step 1: Match domain
    mapping_key, mapping = match_domain(contact_text)
    company = mapping.get("company", "Unknown")
    claims = mapping.get("claims", ["DATA-PIPE-01"])
    mg_domain = mapping.get("mg_domain", "ml")

    # Extract contact name (first word or first two words)
    words = contact_text.split()
    contact_name = words[0] if len(words) == 1 else " ".join(words[:2])
    # Capitalize properly
    contact_name = contact_name.title()

    print(f"  Preparing response kit for: {contact_name}")
    print(f"  Company:  {company}")
    print(f"  Domain:   {mapping.get('display_domain', 'unknown')}")
    print(f"  Claims:   {', '.join(claims)}")
    print()

    # Step 2: Generate bundle
    print("  [1/3] Generating verification bundle...")
    try:
        bundle_dir, claim_result, verified = generate_bundle(
            contact_name, mg_domain, date_str
        )
    except Exception as e:
        print(f"  ERROR: Bundle generation failed -- {e}", file=sys.stderr)
        return 1

    claim_passed = claim_result.get("result", {}).get("pass", False)
    result_str = "PASS" if claim_passed else "FAIL"
    print(f"  Bundle:   {bundle_dir}")
    print(f"  Result:   {result_str}")

    # Step 3: Generate draft
    print("  [2/3] Generating response draft...")
    try:
        draft_path = generate_draft(contact_name, mapping, result_str, date_str)
    except Exception as e:
        print(f"  ERROR: Draft generation failed -- {e}", file=sys.stderr)
        return 1
    print(f"  Draft:    {draft_path}")

    # Step 4: Update queue
    print("  [3/3] Updating response queue...")
    queue = load_queue()

    entry = {
        "contact": contact_name,
        "company": company,
        "domain": mapping.get("display_domain", "unknown"),
        "claims": claims,
        "status": "prepared",
        "bundle_path": str(bundle_dir),
        "draft_path": str(draft_path),
        "date": date_str,
        "outreach_subject": "",
    }

    # Check for duplicate -- update if exists
    existing = _find_entry_by_contact(queue, contact_name)
    if existing:
        idx = queue["entries"].index(existing)
        queue["entries"][idx] = entry
        print("  (Updated existing queue entry)")
    else:
        queue["entries"].append(entry)

    save_queue(queue)
    print()
    print(f"  Response kit ready for {contact_name}.")
    print(f"  Review draft at: {draft_path}")
    return 0


# ---- Status command (RESP-06) -----------------------------------------------

def show_status() -> int:
    """Display response queue status with age in days."""
    queue = load_queue()
    entries = queue.get("entries", [])

    if not entries:
        print("Response queue is empty.")
        return 0

    today = datetime.now(timezone.utc).date()

    print(f"  {'Contact':<20} {'Company':<22} {'Status':<14} {'Age (days)':<10} {'Claims'}")
    print(f"  {'-'*20} {'-'*22} {'-'*14} {'-'*10} {'-'*20}")

    for e in entries:
        contact = e.get("contact", "?")[:20]
        company = e.get("company", "?")[:22]
        status = e.get("status", "?")[:14]
        date_str = e.get("date", "")
        claims_str = ", ".join(e.get("claims", []))

        try:
            entry_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            age = (today - entry_date).days
        except (ValueError, TypeError):
            age = "?"

        print(f"  {contact:<20} {company:<22} {status:<14} {str(age):<10} {claims_str}")

    # Counts
    counts = {}
    for e in entries:
        s = e.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    print()
    parts = [f"{s}: {c}" for s, c in sorted(counts.items())]
    print(f"  Total: {len(entries)} | {' | '.join(parts)}")

    return 0


# ---- List domains command (RESP-06) ----------------------------------------

def list_domains() -> int:
    """Show available domain mappings table."""
    print(f"  {'Mapping':<18} {'Company':<26} {'Claims':<30} {'Domain'}")
    print(f"  {'-'*18} {'-'*26} {'-'*30} {'-'*40}")

    for key, mapping in DOMAIN_MAPPINGS.items():
        company = mapping["company"]
        claims_str = ", ".join(mapping["claims"])
        domain = mapping["display_domain"]
        print(f"  {key:<18} {company:<26} {claims_str:<30} {domain}")

    print(f"  {'default':<18} {'(unknown contact)':<26} {'DATA-PIPE-01':<30} {DEFAULT_MAPPING['display_domain']}")
    print()
    print(f"  Total: {len(DOMAIN_MAPPINGS) + 1} mappings (7 named + 1 default)")
    return 0


# ---- Update status command (RESP-06) ----------------------------------------

def update_status(contact: str, new_status: str) -> int:
    """Update an entry's status in the response queue."""
    if new_status not in VALID_STATUSES:
        print(
            f"ERROR: Invalid status '{new_status}'. "
            f"Valid: {', '.join(VALID_STATUSES)}",
            file=sys.stderr,
        )
        return 1

    queue = load_queue()
    entry = _find_entry_by_contact(queue, contact)

    if not entry:
        print(f"ERROR: No entry found for '{contact}'", file=sys.stderr)
        return 1

    old_status = entry.get("status", "unknown")
    entry["status"] = new_status
    entry["status_updated_at"] = datetime.now(timezone.utc).isoformat()
    save_queue(queue)

    print(f"  Updated: {entry['contact']} -- {old_status} -> {new_status}")
    return 0


# ---- CLI (RESP-06) ---------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="agent_responder",
        description="MetaGenesis Core -- Response Infrastructure Agent",
        epilog=(
            "Examples:\n"
            "  python scripts/agent_responder.py --prepare \"Anand Patronus ML\"\n"
            "  python scripts/agent_responder.py --status\n"
            "  python scripts/agent_responder.py --list-domains\n"
            "  python scripts/agent_responder.py --update-status \"Anand\" \"reviewed\"\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--prepare",
        metavar="CONTACT",
        help="Prepare a response kit for a contact (e.g. 'Anand Patronus ML')",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show response queue status",
    )
    parser.add_argument(
        "--list-domains",
        action="store_true",
        help="Show available domain mappings",
    )
    parser.add_argument(
        "--update-status",
        nargs=2,
        metavar=("CONTACT", "STATUS"),
        help="Update a contact's status (e.g. 'Anand' 'reviewed')",
    )

    args = parser.parse_args()

    if args.prepare:
        return prepare_response(args.prepare)
    elif args.status:
        return show_status()
    elif args.list_domains:
        return list_domains()
    elif args.update_status:
        return update_status(args.update_status[0], args.update_status[1])
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
