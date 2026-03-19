#!/usr/bin/env python3
"""
MetaGenesis Core — Agent Evolution Runner
=========================================
Runs automatically after every merge into main.
Checks all critical files, finds gaps, reports state.

Usage:
    python scripts/agent_evolution.py              # full check
    python scripts/agent_evolution.py --strict     # fail on any issue
    python scripts/agent_evolution.py --summary    # short output only
"""

import subprocess
import sys
import json
import io
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent

# ── Colors ──────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✅{RESET} {msg}")
def err(msg): print(f"  {RED}❌{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠ {RESET} {msg}")
def info(msg): print(f"  {CYAN}→{RESET} {msg}")

def run(cmd, cwd=REPO_ROOT):
    import os
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, env=env, encoding="utf-8", errors="replace")
    return r.stdout.strip(), r.returncode


def section(title):
    print(f"\n{BOLD}{CYAN}══ {title} ══{RESET}")


# ── 1. Steward Audit ────────────────────────────────────────────────────────
def check_steward():
    section("STEWARD AUDIT")
    out, code = run("python scripts/steward_audit.py")
    if code == 0 and "PASS" in out:
        ok("steward_audit.py → PASS")
        return True
    else:
        err(f"steward_audit.py → FAIL")
        print(f"    {out[:200]}")
        return False


# ── 2. Pytest ────────────────────────────────────────────────────────────────
def check_tests():
    section("TEST SUITE")
    out, code = run("python -m pytest tests/ -q --tb=no")
    lines = out.splitlines()
    summary = next((l for l in reversed(lines) if "passed" in l), "")
    if code == 0:
        ok(f"pytest → {summary}")
        # Extract count
        import re
        m = re.search(r"(\d+) passed", summary)
        return True, int(m.group(1)) if m else 0
    else:
        err(f"pytest → FAIL: {summary}")
        return False, 0


# ── 3. Deep Verify ───────────────────────────────────────────────────────────
def check_deep_verify():
    section("DEEP VERIFY")
    out, code = run("python scripts/deep_verify.py")
    if "ALL" in out and "PASSED" in out:
        last = [l for l in out.splitlines() if "PASSED" in l or "passed" in l]
        ok(f"deep_verify.py → {last[-1].strip() if last else 'PASS'}")
        return True
    else:
        err("deep_verify.py → FAIL")
        print(f"    {out[-300:]}")
        return False


# ── 4. Stale Docs ────────────────────────────────────────────────────────────
def check_stale_docs():
    section("STALE DOCUMENTATION")
    out, code = run("python scripts/check_stale_docs.py")
    if "All critical documentation is current" in out:
        ok("All critical docs → CURRENT")
        return True, []
    else:
        stale = [l.strip() for l in out.splitlines() if "STALE" in l and "❌" in l]
        if stale:
            for s in stale:
                err(s)
            return False, stale
        else:
            ok("Docs check passed")
            return True, []


# ── 5. System Manifest Consistency ──────────────────────────────────────────
def check_manifest(actual_test_count):
    section("MANIFEST CONSISTENCY")
    manifest_path = REPO_ROOT / "system_manifest.json"
    if not manifest_path.exists():
        err("system_manifest.json not found")
        return False

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_count = manifest.get("test_count", 0)
    version = manifest.get("version", "unknown")
    claims = len(manifest.get("active_claims", []))

    info(f"version: {version} | claims: {claims} | test_count: {manifest_count}")

    issues = []
    if actual_test_count > 0 and manifest_count != actual_test_count:
        issues.append(f"test_count: manifest={manifest_count} vs actual={actual_test_count}")

    if claims != 14:
        issues.append(f"active_claims: {claims} (expected 14)")

    if issues:
        for i in issues: err(i)
        return False
    else:
        ok("system_manifest.json → consistent")
        return True


# ── 6. Forbidden Terms ───────────────────────────────────────────────────────
def check_forbidden():
    section("FORBIDDEN TERMS")
    terms = ["tamper-proof", "GPT-5", "19x", "VacuumGenesis",
             "unforgeable", "blockchain", "100% test success"]
    dirs = ["docs/", "scripts/", "backend/", "index.html", "README.md"]

    found = []
    for term in terms:
        for d in dirs:
            target = REPO_ROOT / d
            if not target.exists():
                continue
            if target.is_file():
                try:
                    content = target.read_text(encoding="utf-8", errors="ignore")
                    if term in content:
                        found.append(f"'{term}' in {d}")
                except:
                    pass
            else:
                out, _ = run(f'grep -rl "{term}" {d} 2>/dev/null')
                if out:
                    for f in out.splitlines():
                        # Exclude deep_verify.py and this script (contain as search strings)
                        if "deep_verify" not in f and "agent_evolution" not in f:
                            found.append(f"'{term}' in {f}")

    if found:
        for f in found: err(f)
        return False
    else:
        ok("No forbidden terms found")
        return True


# ── 7. Gap Analysis ──────────────────────────────────────────────────────────
def run_gap_analysis(test_count):
    section("COVERAGE GAP ANALYSIS")

    # Count tests per domain
    test_dirs = {
        "steward":     REPO_ROOT / "tests" / "steward",
        "materials":   REPO_ROOT / "tests" / "materials",
        "ml":          REPO_ROOT / "tests" / "ml",
        "systems":     REPO_ROOT / "tests" / "systems",
        "data":        REPO_ROOT / "tests" / "data",
        "digital_twin": REPO_ROOT / "tests" / "digital_twin",
        "pharma":      REPO_ROOT / "tests" / "pharma",
        "finance":     REPO_ROOT / "tests" / "finance",
    }

    gaps = []
    for domain, path in test_dirs.items():
        if not path.exists():
            gaps.append(f"Missing test directory: tests/{domain}/")
            continue
        count = len(list(path.glob("test_*.py")))
        status = "✅" if count >= 3 else "⚠"
        info(f"{status} tests/{domain}/: {count} test files")
        if count < 3:
            gaps.append(f"tests/{domain}/ has only {count} test files (min: 3)")

    # Check CERT coverage
    cert_files = list((REPO_ROOT / "tests" / "steward").glob("test_cert*.py"))
    info(f"✅ CERT suite: {len(cert_files)} files")

    # Check step chain coverage
    out, _ = run("python -m pytest tests/ -q --collect-only 2>/dev/null | grep step_chain | wc -l")
    info(f"✅ Step chain tests: ~{out.strip()} collected")

    if gaps:
        print()
        warn("Coverage gaps found:")
        for g in gaps: warn(f"  → {g}")
    else:
        ok("Coverage looks complete")

    return gaps


# ── 8. CLAUDE.md Freshness ───────────────────────────────────────────────────
def check_claude_md(actual_count):
    section("CLAUDE.MD FRESHNESS")
    claude_path = REPO_ROOT / "CLAUDE.md"
    if not claude_path.exists():
        err("CLAUDE.md not found!")
        return False

    content = claude_path.read_text(encoding="utf-8", errors="ignore")

    issues = []
    if str(actual_count) not in content and actual_count > 0:
        issues.append(f"CLAUDE.md doesn't mention {actual_count} tests")

    if "v0.5.0" not in content:
        issues.append("CLAUDE.md doesn't mention v0.5.0")

    if "conflict" in content.lower() or "<<<<<<" in content:
        issues.append("CLAUDE.md has merge conflict markers!")

    if issues:
        for i in issues: err(i)
        return False
    else:
        ok("CLAUDE.md is fresh and conflict-free")
        return True


# ── 9. Watchlist Coverage ────────────────────────────────────────────────────
def check_watchlist():
    section("WATCHLIST COVERAGE")
    out, code = run("python scripts/auto_watchlist_scan.py")
    import re
    m = re.search(r"(\d+)/(\d+) files watched \((\d+) unwatched\)", out)
    if m:
        watched, total, unwatched = int(m.group(1)), int(m.group(2)), int(m.group(3))
        info(f"{watched}/{total} files watched ({unwatched} unwatched)")
        if unwatched == 0:
            ok("All doc files are in watchlists")
        else:
            warn(f"{unwatched} files not in any watchlist")
        # Advisory -- not a hard failure, just a warning
        return True
    else:
        if code == 0:
            ok("Watchlist scan completed")
            return True
        else:
            err("Watchlist scan failed")
            return False


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    strict = "--strict" in sys.argv
    summary_only = "--summary" in sys.argv

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  MetaGenesis Core — Agent Evolution Check{RESET}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | v0.5.0")
    print(f"{BOLD}{'═'*60}{RESET}")

    results = {}

    results["steward"]   = check_steward()
    ok_tests, count      = check_tests()
    results["tests"]     = ok_tests
    results["deep"]      = check_deep_verify()
    ok_docs, stale       = check_stale_docs()
    results["docs"]      = ok_docs
    results["manifest"]  = check_manifest(count)
    results["forbidden"] = check_forbidden()
    gaps                 = run_gap_analysis(count)
    results["gaps"]      = len(gaps) == 0
    results["claude_md"] = check_claude_md(count)
    results["watchlist"] = check_watchlist()

    # ── Summary ──
    section("SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total  = len(results)

    for check, ok_val in results.items():
        symbol = f"{GREEN}PASS{RESET}" if ok_val else f"{RED}FAIL{RESET}"
        print(f"  {symbol}  {check}")

    print()
    if passed == total:
        print(f"{BOLD}{GREEN}  ✅ ALL {total} CHECKS PASSED — system healthy{RESET}")
        print(f"  Tests: {count} | Ready for next milestone")
        code = 0
    else:
        failed = total - passed
        print(f"{BOLD}{RED}  ❌ {failed}/{total} CHECKS FAILED{RESET}")
        print()
        print(f"  Run after fixing:")
        print(f"  /gsd:quick \"Update CLAUDE.md to reflect current state: {count} tests, v0.5.0\"")
        if stale:
            print(f"  /gsd:quick \"Fix stale documentation: {', '.join(stale[:3])}\"")
        code = 1 if strict else 0

    print(f"\n{'═'*60}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
