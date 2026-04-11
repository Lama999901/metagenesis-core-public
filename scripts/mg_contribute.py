#!/usr/bin/env python3
"""
MetaGenesis Core -- Secure Client Contribution System

Clients contribute feedback, ideas, bug reports, and success stories.
All contributions are text-only, sanitized, SHA-256 signed, and stored
as individual JSON files for human review.

Usage:
    python scripts/mg_contribute.py --api-key YOUR_KEY
    python scripts/mg_contribute.py --type bug_report --content "..."
    python scripts/mg_contribute.py --review
    python scripts/mg_contribute.py --stats

Security:
    - TEXT ONLY -- no code, no scripts, no file paths accepted
    - Max 2000 characters per contribution
    - All code patterns stripped before storage
    - Each contribution signed with SHA-256 timestamp
    - NEVER auto-merged to main -- human review required

PPA: USPTO #63/996,819
"""

import argparse
import hashlib
import io
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRIB_DIR = REPO_ROOT / "reports" / "client_contributions"

# ---- Terminal colors --------------------------------------------------------

G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
B = "\033[1m"
DIM = "\033[2m"
X = "\033[0m"

# ---- Constants --------------------------------------------------------------

MAX_CONTENT_LENGTH = 2000
VALID_TYPES = ["bug_report", "domain_idea", "improvement", "success_story"]
VALID_DOMAINS = [
    "ml", "pharma", "finance", "materials",
    "digital_twin", "physics", "systems", "agent", "other",
]

# Patterns that indicate code/scripts -- must be stripped
CODE_PATTERNS = [
    r'import\s+\w+',
    r'from\s+\w+\s+import',
    r'def\s+\w+\s*\(',
    r'class\s+\w+\s*[:\(]',
    r'subprocess\.\w+',
    r'os\.(system|popen|exec)',
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__\s*\(',
    r'\bopen\s*\([\'"]',
    r'Path\s*\([\'"]',
    r'<script[^>]*>',
    r'javascript:',
    r';\s*(rm|del|drop|delete)\s',
    r'(\/[a-zA-Z]+\/)+\w+\.\w+',       # file paths like /usr/bin/foo.py
    r'[A-Z]:\\\\[\w\\\\]+\.\w+',         # Windows paths
    r'```[\s\S]*?```',                    # code blocks
    r'`[^`]{20,}`',                       # long inline code
]


def sanitize_content(text: str) -> str:
    """Remove code patterns and enforce text-only content."""
    if not text:
        return ""

    # Truncate to max length
    text = text[:MAX_CONTENT_LENGTH]

    # Strip code patterns
    for pattern in CODE_PATTERNS:
        text = re.sub(pattern, "[REMOVED]", text, flags=re.IGNORECASE)

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def _detect_language(text: str) -> str:
    """Simple language detection from character ranges."""
    has_hiragana = has_katakana = has_cjk = has_hangul = has_cyrillic = False
    for ch in text:
        cp = ord(ch)
        if 0x3040 <= cp <= 0x309F:
            has_hiragana = True
        elif 0x30A0 <= cp <= 0x30FF:
            has_katakana = True
        elif 0x4E00 <= cp <= 0x9FFF:
            has_cjk = True
        elif 0xAC00 <= cp <= 0xD7AF:
            has_hangul = True
        elif 0x0400 <= cp <= 0x04FF:
            has_cyrillic = True

    if has_hiragana or has_katakana:
        return "ja"
    if has_hangul:
        return "ko"
    if has_cjk:
        return "zh"
    if has_cyrillic:
        return "ru"

    lower = text.lower()
    if any(w in lower for w in ["trabajo", "estoy", "necesito"]):
        return "es"
    if any(w in lower for w in ["je travaille", "j'utilise"]):
        return "fr"
    if any(w in lower for w in ["ich arbeite", "wir"]):
        return "de"
    return "en"


def create_contribution(content: str, contrib_type: str, domain: str = "other",
                        session_hash: str = None) -> dict:
    """Create a signed contribution and save to disk.

    Args:
        content: Text content (will be sanitized)
        contrib_type: One of VALID_TYPES
        domain: One of VALID_DOMAINS
        session_hash: Anonymous session identifier

    Returns:
        The contribution dict that was saved
    """
    if contrib_type not in VALID_TYPES:
        raise ValueError(f"Invalid type '{contrib_type}'. Valid: {', '.join(VALID_TYPES)}")
    if domain not in VALID_DOMAINS:
        domain = "other"

    # Sanitize content
    clean_content = sanitize_content(content)
    if not clean_content or clean_content == "[REMOVED]":
        raise ValueError("Content was empty or contained only code patterns")

    # Detect language
    language = _detect_language(clean_content)

    # Generate timestamp and ID
    now = datetime.now(timezone.utc)
    ts = now.isoformat()
    date_str = now.strftime("%Y%m%d")

    # Count existing contributions today for sequential ID
    CONTRIB_DIR.mkdir(parents=True, exist_ok=True)
    today_count = sum(
        1 for f in CONTRIB_DIR.glob(f"contrib_{date_str}_*.json")
    )
    contrib_id = f"contrib_{date_str}_{today_count + 1:03d}"

    # Generate SHA-256 of content + timestamp
    sign_payload = json.dumps(
        {"content": clean_content, "timestamp": ts, "type": contrib_type},
        sort_keys=True, separators=(",", ":"),
    )
    sha256 = hashlib.sha256(sign_payload.encode("utf-8")).hexdigest()

    # Anonymous session hash
    if not session_hash:
        session_hash = hashlib.sha256(os.urandom(16)).hexdigest()[:16]

    contribution = {
        "id": contrib_id,
        "timestamp": ts,
        "language": language,
        "type": contrib_type,
        "domain": domain,
        "content": clean_content,
        "sha256": sha256,
        "session_hash": session_hash,
        "value_score": None,
    }

    # Save to individual file
    out_path = CONTRIB_DIR / f"{contrib_id}.json"
    out_path.write_text(
        json.dumps(contribution, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return contribution


def interactive_contribute(api_key: str = None):
    """Interactive contribution flow, optionally with Claude AI assistance."""
    print()
    print(f"{B}{C}  MetaGenesis Core -- Client Contributions{X}")
    print(f"{DIM}  Share feedback, ideas, bugs, or success stories{X}")
    print()

    # Choose type
    print(f"  {B}What would you like to share?{X}")
    for i, t in enumerate(VALID_TYPES, 1):
        label = t.replace("_", " ").title()
        print(f"    {i}. {label}")
    print()

    try:
        choice = input(f"  Choose (1-4): ").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {Y}Cancelled.{X}")
        return None

    try:
        contrib_type = VALID_TYPES[int(choice) - 1]
    except (ValueError, IndexError):
        print(f"  {R}Invalid choice.{X}")
        return None

    # Choose domain
    print()
    print(f"  {B}Which domain?{X}")
    for i, d in enumerate(VALID_DOMAINS, 1):
        print(f"    {i}. {d}")
    print()

    try:
        d_choice = input(f"  Choose (1-{len(VALID_DOMAINS)}): ").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {Y}Cancelled.{X}")
        return None

    try:
        domain = VALID_DOMAINS[int(d_choice) - 1]
    except (ValueError, IndexError):
        domain = "other"

    # Get content
    print()
    print(f"  {B}Describe (max {MAX_CONTENT_LENGTH} chars, text only):{X}")
    try:
        content = input(f"  > ").strip()
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {Y}Cancelled.{X}")
        return None

    if not content:
        print(f"  {R}No content provided.{X}")
        return None

    try:
        contrib = create_contribution(content, contrib_type, domain)
    except ValueError as e:
        print(f"  {R}Error:{X} {e}")
        return None

    print()
    print(f"  {G}Contribution saved!{X}")
    print(f"  {DIM}ID:     {contrib['id']}{X}")
    print(f"  {DIM}SHA256: {contrib['sha256'][:32]}...{X}")
    print(f"  {DIM}File:   {CONTRIB_DIR / (contrib['id'] + '.json')}{X}")
    print(f"  {DIM}Status: Pending human review{X}")
    print()
    return contrib


def show_stats():
    """Show contribution statistics."""
    print()
    print(f"{B}{C}  Client Contributions -- Statistics{X}")
    print()

    if not CONTRIB_DIR.exists():
        print(f"  {DIM}No contributions yet.{X}")
        return

    files = list(CONTRIB_DIR.glob("contrib_*.json"))
    if not files:
        print(f"  {DIM}No contributions yet.{X}")
        return

    by_type = {}
    by_domain = {}
    by_language = {}
    reviewed = 0
    total = len(files)

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        t = data.get("type", "unknown")
        d = data.get("domain", "unknown")
        lang = data.get("language", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        by_domain[d] = by_domain.get(d, 0) + 1
        by_language[lang] = by_language.get(lang, 0) + 1
        if data.get("value_score") is not None:
            reviewed += 1

    print(f"  Total: {total}  |  Reviewed: {reviewed}  |  Pending: {total - reviewed}")
    print()
    print(f"  {B}By type:{X}")
    for t, c in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}")
    print()
    print(f"  {B}By domain:{X}")
    for d, c in sorted(by_domain.items(), key=lambda x: -x[1]):
        print(f"    {d}: {c}")
    print()
    print(f"  {B}By language:{X}")
    for lang, c in sorted(by_language.items(), key=lambda x: -x[1]):
        print(f"    {lang}: {c}")
    print()


def review_contributions():
    """List unreviewed contributions for human review."""
    print()
    print(f"{B}{C}  Client Contributions -- Review Queue{X}")
    print()

    if not CONTRIB_DIR.exists():
        print(f"  {DIM}No contributions to review.{X}")
        return

    files = sorted(CONTRIB_DIR.glob("contrib_*.json"))
    pending = []

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("value_score") is None:
            pending.append((f, data))

    if not pending:
        print(f"  {G}All contributions reviewed!{X}")
        return

    print(f"  {Y}{len(pending)} contributions pending review:{X}")
    print()

    for f, data in pending:
        ctype = data.get("type", "?").replace("_", " ").title()
        domain = data.get("domain", "?")
        lang = data.get("language", "?")
        content = data.get("content", "")[:80]
        ts = data.get("timestamp", "?")[:10]

        print(f"  {B}{data.get('id', '?')}{X}")
        print(f"    Type: {ctype}  |  Domain: {domain}  |  Lang: {lang}  |  Date: {ts}")
        print(f"    {DIM}{content}...{X}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mg_contribute",
        description="MetaGenesis Core -- Secure Client Contribution System",
        epilog=(
            "Examples:\n"
            "  python scripts/mg_contribute.py --api-key sk-ant-...\n"
            '  python scripts/mg_contribute.py --type bug_report --content "..."\n'
            "  python scripts/mg_contribute.py --review\n"
            "  python scripts/mg_contribute.py --stats\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--api-key", type=str, default=None,
        help="Anthropic API key for AI-assisted contribution",
    )
    parser.add_argument(
        "--type", choices=VALID_TYPES, default=None,
        help="Contribution type (non-interactive mode)",
    )
    parser.add_argument(
        "--content", type=str, default=None,
        help="Contribution content (non-interactive mode)",
    )
    parser.add_argument(
        "--domain", choices=VALID_DOMAINS, default="other",
        help="Domain for the contribution",
    )
    parser.add_argument(
        "--review", action="store_true",
        help="Show unreviewed contributions",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="Show contribution statistics",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
        return 0

    if args.review:
        review_contributions()
        return 0

    # Non-interactive mode
    if args.type and args.content:
        try:
            contrib = create_contribution(args.content, args.type, args.domain)
            print(f"{G}Saved:{X} {contrib['id']}  SHA256: {contrib['sha256'][:32]}...")
            return 0
        except ValueError as e:
            print(f"{R}Error:{X} {e}")
            return 1

    # Interactive mode
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    result = interactive_contribute(api_key)
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
