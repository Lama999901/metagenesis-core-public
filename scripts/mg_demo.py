#!/usr/bin/env python3
"""
MetaGenesis Core -- Domain Demo Script

Single-command demo: pick a domain, verify existing bundles through all
5 cryptographic layers, receive a human-readable receipt.  Works fully
offline.  Uses pre-built bundles from proof_library/bundles/.

Usage:
    python scripts/mg_demo.py                     # interactive domain menu
    python scripts/mg_demo.py --domain materials   # skip menu
    python scripts/mg_demo.py --all                # all domains sequentially
    python scripts/mg_demo.py --domain ml --output-dir /tmp/receipts

PPA: USPTO #63/996,819
"""

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows cp1252 encoding (BUG 4 from CLAUDE.md)
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_client import verify_bundle  # noqa: E402
from scripts.mg_receipt import (  # noqa: E402
    CLAIM_DESCRIPTIONS,
    PHYSICAL_ANCHORS,
    format_receipt,
    get_anchor_line,
    get_claim_description,
)

# ---- Terminal colors (same palette as mg_client.py) --------------------------

G = "\033[92m"   # green
R = "\033[91m"   # red
Y = "\033[93m"   # yellow
C = "\033[96m"   # cyan
B = "\033[1m"    # bold
DIM = "\033[2m"
X = "\033[0m"    # reset

# ---- Domain display configuration -------------------------------------------

DOMAIN_DISPLAY = {
    "materials":    {"label": "Materials Science",           "domains": ["materials"]},
    "physics":      {"label": "Fundamental Physics",         "domains": ["physics"]},
    "ml":           {"label": "Machine Learning",            "domains": ["ml"]},
    "pharma":       {"label": "Pharmaceutical (ADMET)",      "domains": ["pharma"]},
    "finance":      {"label": "Financial Risk (Basel III)",   "domains": ["finance"]},
    "digital_twin": {"label": "Digital Twin",                "domains": ["digital_twin"]},
    "systems":      {"label": "Systems Engineering",         "domains": ["systems"]},
    "agent":        {"label": "Agent Monitoring",            "domains": ["agent"]},
}

# Ordered keys for the interactive menu
DOMAIN_ORDER = [
    "materials", "physics", "ml", "pharma",
    "finance", "digital_twin", "systems", "agent",
]

# ---- Helpers -----------------------------------------------------------------


def _load_index() -> list:
    """Load proof_library/index.json."""
    index_path = REPO_ROOT / "proof_library" / "index.json"
    if not index_path.exists():
        print(f"  {R}ERROR:{X} proof_library/index.json not found", file=sys.stderr)
        return []
    return json.loads(index_path.read_text(encoding="utf-8"))


def _entries_for_domain(index: list, domain_key: str) -> list:
    """Filter index entries: matching domain, non-synthetic only."""
    target_domains = DOMAIN_DISPLAY.get(domain_key, {}).get("domains", [domain_key])
    return [
        e for e in index
        if e.get("domain") in target_domains and not e.get("is_synthetic", True)
    ]


def _resolve_bundle_path(entry: dict) -> Path:
    """Resolve bundle_path from index entry (handles backslash paths)."""
    raw = entry.get("bundle_path", "").replace("\\", "/")
    resolved = REPO_ROOT / Path(raw)
    return resolved


def _safe_zip_member(name: str) -> bool:
    """Check a ZIP member name for path traversal (T-24-02 mitigation)."""
    if name.startswith("/") or name.startswith("\\"):
        return False
    if ".." in name.split("/") or ".." in name.split("\\"):
        return False
    if os.path.isabs(name):
        return False
    return True


def _short_claim_id(mtr_phase: str) -> str:
    """Extract short claim ID from mtr_phase (e.g. 'MTR-1' from 'MTR-1_materials-2026...').

    Handles patterns like:
      MTR-1_materials-20260407T052827Z  -> MTR-1
      DT-FEM-01_digital_twin-2026...   -> DT-FEM-01
      AGENT-DRIFT-01_agent-2026...     -> AGENT-DRIFT-01
      ML_BENCH-01_ml-2026...           -> ML_BENCH-01
    """
    # Known claim IDs from the project -- try matching each
    from scripts.mg_receipt import CLAIM_DESCRIPTIONS
    for known_id in sorted(CLAIM_DESCRIPTIONS.keys(), key=len, reverse=True):
        if mtr_phase.startswith(known_id):
            return known_id
    # Fallback: return as-is
    return mtr_phase


def _find_bundle_root(extract_dir: Path) -> Path:
    """Find the directory containing pack_manifest.json after extraction.

    ZIPs may contain files at the root or inside a single top-level folder.
    """
    if (extract_dir / "pack_manifest.json").exists():
        return extract_dir
    # Check one level down
    for child in extract_dir.iterdir():
        if child.is_dir() and (child / "pack_manifest.json").exists():
            return child
    return extract_dir  # fallback


def _extract_and_verify(bundle_zip: Path) -> tuple:
    """Extract a bundle ZIP, verify it, return (passed, results, evidence, tmp_dir).

    Caller must clean up tmp_dir.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="mg_demo_"))
    try:
        with zipfile.ZipFile(str(bundle_zip), "r") as zf:
            # T-24-02: validate member names before extraction
            for member in zf.namelist():
                if not _safe_zip_member(member):
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                    return False, [("ZIP Security", False, f"Unsafe path: {member}")], None, None
            zf.extractall(str(tmp_dir))

        bundle_root = _find_bundle_root(tmp_dir)
        passed, results = verify_bundle(bundle_root)

        # Load evidence.json for receipt generation
        evidence = None
        evidence_path = bundle_root / "evidence.json"
        if evidence_path.exists():
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

        return passed, results, evidence, tmp_dir
    except Exception as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return False, [("Extraction", False, str(exc))], None, None


def _print_layer_results(results: list):
    """Print 5-layer verification results with PASS/FAIL icons."""
    print(f"\n{B}  Verification Results{X}")
    print(f"  {'=' * 60}")
    for name, passed, detail in results:
        icon = f"{G}PASS{X}" if passed else f"{R}FAIL{X}"
        print(f"  [{icon}] {name}")
        print(f"         {DIM}{detail}{X}")
    print(f"  {'=' * 60}")


# ---- Domain demo flow --------------------------------------------------------


def run_domain_demo(domain_key: str, output_dir: Path) -> bool:
    """Run demo for a single domain. Returns True if all claims pass."""
    label = DOMAIN_DISPLAY.get(domain_key, {}).get("label", domain_key)
    print(f"\n{B}{C}  MetaGenesis Core -- Domain Demo{X}")
    print(f"  {B}Domain:{X} {label}")
    print(f"  {DIM}Verifying existing bundles through 5 cryptographic layers...{X}")

    index = _load_index()
    entries = _entries_for_domain(index, domain_key)

    if not entries:
        print(f"\n  {Y}No real (non-synthetic) bundles found for domain '{domain_key}'.{X}")
        return False

    print(f"  {DIM}Found {len(entries)} bundle(s) for {label}{X}")

    all_passed = True
    claim_summaries = []
    bundle_paths_for_receipt = []

    for i, entry in enumerate(entries, 1):
        bundle_zip = _resolve_bundle_path(entry)

        # T-24-01: verify bundle path is within repo
        try:
            bundle_zip.resolve().relative_to(REPO_ROOT.resolve())
        except ValueError:
            print(f"\n  {R}SECURITY:{X} Bundle path escapes repository: {bundle_zip}")
            all_passed = False
            continue

        if not bundle_zip.exists():
            print(f"\n  {Y}WARNING:{X} Bundle not found: {bundle_zip}")
            print(f"  {DIM}Skipping...{X}")
            continue

        claim_id = entry.get("id", "?").split("-2026")[0]  # e.g. MTR-1_materials
        # Extract just the claim part (e.g. MTR-1)
        claim_tag = claim_id.split("_")[0]
        if "-" in claim_id and not claim_tag[-1].isdigit():
            # Handle cases like AGENT-DRIFT-01_agent
            parts = claim_id.rsplit("_", 1)
            claim_tag = parts[0] if len(parts) > 1 else claim_id

        print(f"\n  {C}[{i}/{len(entries)}]{X} Verifying {entry['id']}...")

        passed, results, evidence, tmp_dir = _extract_and_verify(bundle_zip)

        _print_layer_results(results)

        if evidence:
            raw_mtr_phase = evidence.get("mtr_phase", claim_tag)
            claim_tag_from_evidence = _short_claim_id(raw_mtr_phase)
            desc = get_claim_description(claim_tag_from_evidence)
            anchor = get_anchor_line(claim_tag_from_evidence)

            # Print individual receipt (use short claim ID for proper lookup)
            receipt_evidence = dict(evidence)
            receipt_evidence["mtr_phase"] = claim_tag_from_evidence
            receipt_text = format_receipt(receipt_evidence)
            print(f"\n{receipt_text}")

            claim_summaries.append({
                "claim_id": claim_tag_from_evidence,
                "description": desc,
                "anchor": anchor,
                "passed": passed,
                "bundle_zip": str(bundle_zip.relative_to(REPO_ROOT)),
                "trace_root_hash": evidence.get("trace_root_hash", ""),
            })

            bundle_paths_for_receipt.append(
                str(bundle_zip.relative_to(REPO_ROOT)).replace("\\", "/")
            )

        if not passed:
            all_passed = False

        # Clean up temp directory
        if tmp_dir and Path(tmp_dir).exists():
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # ---- Write combined domain receipt ----
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = output_dir / f"{domain_key}_receipt.txt"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    n_claims = len(claim_summaries)
    overall = "PASS" if all_passed and n_claims > 0 else "FAIL"

    lines = [
        "============================================================",
        "METAGENESIS CORE -- DOMAIN DEMO RECEIPT",
        "============================================================",
        "",
        "Summary",
        "-------",
        f"  Domain:          {label}",
        f"  Claims verified: {n_claims}",
        f"  Overall result:  {overall}",
        f"  Timestamp:       {timestamp}",
        "",
        "Claims Verified",
        "---------------",
    ]

    for cs in claim_summaries:
        status = "PASS" if cs["passed"] else "FAIL"
        lines.append(f"  [{status}] {cs['claim_id']}")
        lines.append(f"         {cs['description']}")
        if cs["trace_root_hash"]:
            lines.append(f"         Chain root: {cs['trace_root_hash'][:16]}...")
        lines.append("")

    lines.append("Verification Result")
    lines.append("-------------------")
    if all_passed and n_claims > 0:
        lines.append(
            f"  All {n_claims} claim(s) verified through 5 independent"
            " cryptographic layers."
        )
        lines.append("  Each layer catches attacks the other four miss.")
    else:
        lines.append(f"  {overall}: not all claims passed verification.")
    lines.append("")

    lines.append("How to Reproduce")
    lines.append("----------------")
    lines.append("  Run these commands from the repository root:")
    lines.append("")
    for bp in bundle_paths_for_receipt:
        lines.append(f"  python scripts/mg.py verify --pack {bp}")
    lines.append("")
    lines.append("  Offline. Any machine. No trust required.")
    lines.append("")
    lines.append("============================================================")
    lines.append("MetaGenesis Core | MIT License")
    lines.append("metagenesis-core.dev | PPA #63/996,819")
    lines.append("============================================================")

    receipt_text_combined = "\n".join(lines)
    receipt_path.write_text(receipt_text_combined, encoding="utf-8")

    print(f"\n  {G}Receipt saved:{X} {receipt_path}")

    return all_passed


# ---- Interactive menu --------------------------------------------------------


def interactive_menu() -> str:
    """Show numbered domain menu, return selected domain key."""
    print(f"\n{B}{C}  MetaGenesis Core -- Domain Demo{X}")
    print(f"  {DIM}Select a domain to verify:{X}\n")

    for i, key in enumerate(DOMAIN_ORDER, 1):
        label = DOMAIN_DISPLAY[key]["label"]
        print(f"  {C}{i}.{X} {label}")

    print()
    try:
        choice = input(f"  {B}Enter number (1-{len(DOMAIN_ORDER)}):{X} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(DOMAIN_ORDER):
            return DOMAIN_ORDER[idx]
    except ValueError:
        pass

    print(f"\n  {R}Invalid selection:{X} {choice}")
    return ""


# ---- Main --------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mg_demo",
        description="MetaGenesis Core -- Domain Demo Script",
        epilog="Verifies existing bundles from proof_library/. Fully offline.",
    )
    parser.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Domain to demo (e.g. materials, physics, ml, pharma, finance, "
             "digital_twin, systems, agent)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        dest="run_all",
        help="Run demo for all domains sequentially",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for receipt files (default: demos/receipts/)",
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "demos" / "receipts"
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.run_all:
        all_ok = True
        for domain_key in DOMAIN_ORDER:
            ok = run_domain_demo(domain_key, output_dir)
            if not ok:
                all_ok = False
        return 0 if all_ok else 1

    if args.domain:
        domain_key = args.domain.lower().strip()
        if domain_key not in DOMAIN_DISPLAY:
            print(
                f"  {R}Unknown domain:{X} '{domain_key}'",
                file=sys.stderr,
            )
            print(
                f"  Supported: {', '.join(DOMAIN_ORDER)}",
                file=sys.stderr,
            )
            return 1
        return 0 if run_domain_demo(domain_key, output_dir) else 1

    # Interactive mode
    domain_key = interactive_menu()
    if not domain_key:
        return 1
    return 0 if run_domain_demo(domain_key, output_dir) else 1


if __name__ == "__main__":
    sys.exit(main())
