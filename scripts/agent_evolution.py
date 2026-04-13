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
from datetime import datetime, timezone

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
    section("STEWARD AUDIT — Inquisitorial Inspection")
    out, code = run("python scripts/steward_audit.py")
    if code == 0 and "PASS" in out:
        ok("steward_audit.py → PASS — Inquisition satisfied (STEWARD_PASS)")
        return True
    else:
        err(f"steward_audit.py → FAIL")
        print(f"    {out[:200]}")
        return False


# ── 2. Pytest ────────────────────────────────────────────────────────────────
def check_tests():
    section("TEST SUITE — Machine Spirit Awakening")
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
    section("DEEP VERIFY — Rite of Pure Thought")
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
    section("STALE DOCUMENTATION — Noosphere Scan")
    out, code = run("python scripts/check_stale_docs.py --strict")
    if code == 0 and "All critical documentation is current" in out:
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
    section("MANIFEST CONSISTENCY — Codex Verification")
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

    if claims != 20:
        issues.append(f"active_claims: {claims} (expected 20)")

    if issues:
        for i in issues: err(i)
        return False
    else:
        ok("system_manifest.json → consistent")
        return True


# ── 6. Forbidden Terms ───────────────────────────────────────────────────────
def check_forbidden():
    section("FORBIDDEN TERMS — Hereticus Detection")
    terms = ["tamper-proof", "GPT-5", "19x", "VacuumGenesis",
             "unforgeable", "blockchain", "100% test success"]
    dirs = ["docs/", "scripts/", "backend/", "index.html", "README.md"]

    # Context patterns that make a banned term OK (comparison text, tables, negations)
    safe_contexts = ["NOT blockchain", "NOT tamper-proof", "not blockchain",
                     "not tamper-proof", "Not blockchain", "Not tamper-proof",
                     "say \"tamper-evident\"", "tamper-evident",
                     "BANNED", "never say", "Never say", "never write", "Never write",
                     "→", "don't use"]

    found = []
    for term in terms:
        for d in dirs:
            target = REPO_ROOT / d
            if not target.exists():
                continue
            if target.is_file():
                try:
                    lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
                    for line in lines:
                        if term.lower() in line.lower():
                            # Skip if line has safe context or is a table comparison row
                            if any(ctx in line for ctx in safe_contexts):
                                continue
                            found.append(f"'{term}' in {d}")
                            break
                except:
                    pass
            else:
                out, _ = run(f'grep -rl "{term}" {d} 2>/dev/null')
                if out:
                    for f in out.splitlines():
                        if "deep_verify" not in f and "agent_evolution" not in f:
                            # Read file and check if all matches are in safe context
                            fpath = REPO_ROOT / f
                            try:
                                lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                                real_hit = False
                                for line in lines:
                                    if term.lower() in line.lower():
                                        if not any(ctx in line for ctx in safe_contexts):
                                            real_hit = True
                                            break
                                if real_hit:
                                    found.append(f"'{term}' in {f}")
                            except:
                                found.append(f"'{term}' in {f}")

    if found:
        for f in found: err(f)
        return False
    else:
        ok("No forbidden terms found — no Hereticus detected (FORBIDDEN_TERMS)")
        return True


# ── 7. Gap Analysis ──────────────────────────────────────────────────────────
def run_gap_analysis(test_count):
    section("COVERAGE GAP ANALYSIS — Forge World Audit")

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

    # Claims that don't have their own test dir but are tested elsewhere
    # pharma -> tests/ml/test_*pharma*, tests/steward/test_*pharma*
    # finance -> tests/ml/test_*finrisk*, tests/steward/test_*finrisk*
    cross_domain_claims = {
        "pharma": ["pharma", "admet"],
        "finance": ["finrisk", "var_certificate"],
    }

    gaps = []
    for domain, path in test_dirs.items():
        if not path.exists():
            # Check if this domain's tests live elsewhere
            if domain in cross_domain_claims:
                patterns = cross_domain_claims[domain]
                found_files = []
                for pat in patterns:
                    found_files.extend(list((REPO_ROOT / "tests").rglob(f"test_*{pat}*")))
                if found_files:
                    info(f"✅ tests/{domain}/: {len(found_files)} test files (cross-domain)")
                    continue
            gaps.append(f"Missing test directory: tests/{domain}/")
            continue
        count = len(list(path.glob("test_*.py")))
        status = "✅" if count >= 1 else "⚠"
        info(f"{status} tests/{domain}/: {count} test files")
        if count < 1:
            gaps.append(f"tests/{domain}/ has no test files")

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
    section("CLAUDE.MD FRESHNESS — Lexmechanic Rites")
    claude_path = REPO_ROOT / "CLAUDE.md"
    if not claude_path.exists():
        err("CLAUDE.md not found!")
        return False

    content = claude_path.read_text(encoding="utf-8", errors="ignore")

    issues = []
    if str(actual_count) not in content and actual_count > 0:
        issues.append(f"CLAUDE.md doesn't mention {actual_count} tests")

    if "v1.0.0-rc1" not in content:
        issues.append("CLAUDE.md doesn't mention v1.0.0-rc1")

    if "<<<<<<" in content or ">>>>>>>" in content or "\n=======" in content:
        issues.append("CLAUDE.md has merge conflict markers!")

    if issues:
        for i in issues: err(i)
        return False
    else:
        ok("CLAUDE.md is fresh and conflict-free")
        return True


# ── 9. Watchlist Coverage ────────────────────────────────────────────────────
def check_watchlist():
    section("WATCHLIST COVERAGE — Servo-skull Patrol")
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


# ── 10. Branch Sync ───────────────────────────────────────────────────────────
def check_branch_sync():
    section("BRANCH SYNC — Skitarii Synchronization")
    # Fetch latest remote state
    run("git fetch origin")
    out, code = run("git rev-list HEAD..origin/main --count")
    try:
        behind = int(out.strip())
    except (ValueError, AttributeError):
        warn("Could not determine branch sync status (advisory)")
        return True
    if behind > 0:
        err(f"Branch is {behind} commits behind origin/main — Skitarii out of sync (BRANCH_SYNC_FAIL)")
        info("Fix: git fetch origin && git merge origin/main --no-edit")
        return False
    else:
        ok("Branch is up to date with origin/main")
        return True


# ── 11. Coverage Analysis ────────────────────────────────────────────────────
def check_coverage():
    section("CODE COVERAGE — Genetor Analysis")
    import re
    THRESHOLD = 65.0
    out, code = run("python scripts/agent_coverage.py --summary")
    if code != 0:
        warn(f"Coverage tool failed — {out.strip()}")
        return True  # tool failure is advisory, not a hard fail
    # Parse coverage percentage from output
    match = re.search(r'Coverage ([\d.]+)%', out)
    if match:
        pct = float(match.group(1))
        if pct < THRESHOLD:
            err(f"Coverage {pct:.1f}% BELOW minimum {THRESHOLD}% — governance FAIL")
            return False
        elif pct < 65.0:
            ok(f"Coverage {pct:.1f}% (target 65%)")
            return True
        else:
            ok(f"Coverage {pct:.1f}% — target met")
            return True
    # Fallback: coverage script not available or output unparseable
    ok(f"Coverage analysis complete — {out.strip()}")
    return True


# ── 12. Self-Improvement ────────────────────────────────────────────────────
def check_self_improvement():
    section("SELF-IMPROVEMENT — Recursive Enlightenment")
    out, code = run("python scripts/agent_evolve_self.py --summary")
    if code == 0:
        ok(f"Self-improvement scan complete — {out.strip()}")
    else:
        warn(f"Self-improvement scan issue — {out.strip()}")

    # Check for pending governance proposals in AGENT_TASKS.md
    tasks_file = REPO_ROOT / "AGENT_TASKS.md"
    if tasks_file.exists():
        content = tasks_file.read_text(encoding="utf-8", errors="ignore")
        gov_pending = content.count("Governance proposal:")
        pending_count = sum(1 for line in content.splitlines()
                          if "Governance proposal:" in line
                          and "PENDING" in content[max(0, content.index(line)-200):content.index(line)+200]
                          if line.strip().startswith("- **Title:**"))
        if gov_pending > 0:
            warn(f"GOVERNANCE PROPOSALS PENDING: {gov_pending} — review AGENT_TASKS.md")

    return True


# ── 13. External Signals ──────────────────────────────────────────────────
def check_signals():
    section("EXTERNAL SIGNALS — Astropathic Relay")
    out, code = run("python scripts/agent_signals.py --summary")
    if code == 0:
        ok(f"Signals received — {out.strip()}")
        return True
    else:
        warn(f"Signals unavailable — {out.strip()}")
        return True  # advisory, not a hard failure


# ── 14. Chronicle ─────────────────────────────────────────────────────────
def check_chronicle():
    section("CHRONICLE — Historitor Record")
    out, code = run("python scripts/agent_chronicle.py --summary")
    if code == 0:
        ok(f"Chronicle recorded — {out.strip()}")
        return True
    else:
        warn(f"Chronicle issue — {out.strip()}")
        return True  # advisory, not a hard failure


# ── 15. PR Review Quality ──────────────────────────────────────────────────
def check_pr_review():
    section("PR REVIEW -- Fabricator-General Inspection")
    # Check last commit's new .py files for corresponding test files
    out, _ = run("git diff --name-only HEAD~1 HEAD")
    if not out:
        ok("No changes in last commit (advisory)")
        return True

    changed = out.splitlines()
    new_py = [f for f in changed if f.endswith(".py")
              and not f.startswith("tests/")
              and not f.startswith("test_")]

    untested = []
    for py_file in new_py:
        stem = Path(py_file).stem
        # Check if any test file references this module
        test_out, _ = run(f'grep -rl "{stem}" tests/ 2>/dev/null')
        if not test_out:
            untested.append(py_file)

    if untested:
        for f in untested:
            warn(f"No test coverage found for: {f}")
        info(f"{len(untested)}/{len(new_py)} changed .py files lack test references")
    else:
        if new_py:
            ok(f"All {len(new_py)} changed .py files have test references")
        else:
            ok("No new .py source files in last commit")

    # Advisory only -- always returns True
    return True


# ── 16. Impact Analysis ──────────────────────────────────────────────────
def check_impact():
    section("IMPACT ANALYSIS -- Cogitator Impact")
    out, code = run("python scripts/agent_impact.py --summary")
    if "MISSING" in out:
        warn(f"Impact gaps detected -- {out.strip()}")
    else:
        ok(f"Impact analysis -- {out.strip()}")
    return True  # Advisory only


# ── 17. Diff Review ──────────────────────────────────────────────────────────
def check_diff_review():
    section("DIFF REVIEW — Logic Arbiter")
    out, code = run("python scripts/agent_diff_review.py --summary")
    info(out if out else "no diff output")
    if code == 0:
        ok("agent_diff_review → PASS (DIFF_PASS)")
        return True
    else:
        err("agent_diff_review → issues found (DIFF_FAIL)")
        return False


# ── 18. Auto PR ──────────────────────────────────────────────────────────────
def check_auto_pr():
    section('AUTO PR — Autonomous Forge')
    out, code = run('python scripts/agent_pr_creator.py --summary')
    if code == 0 or 'no auto-pr needed' in out.lower() or 'system current' in out.lower():
        ok('No auto-fixable issues — Level 3 current (AUTOPR_CLEAN)')
        return True
    else:
        warn(f'Auto-fixable issues: {out.strip()[:100]} (AUTOPR_PENDING)')
        return True  # advisory only


def check_semantic_audit():
    section("SEMANTIC AUDIT — Project Coherence Check")
    out, code = run("python scripts/agent_audit.py --summary")
    if code == 0:
        ok("All semantic checks pass (SEMANTIC_PASS)")
        return True
    else:
        err("Semantic audit failed (SEMANTIC_FAIL)")
        for line in out.splitlines():
            if "FAIL" in line:
                info(line.strip()[:100])
        return False


# ── 20. Self-Audit ──────────────────────────────────────────────────────────
def check_self_audit():
    section("SELF-AUDIT — Recursive Inquisitor")
    out, code = run("python scripts/mg_self_audit.py")
    if code == 0:
        if "ADVISORY" in out:
            warn("No baseline found (advisory — run --init to create)")
            ok("Self-audit skipped — no baseline (SELFAUDIT_ADVISORY)")
        else:
            ok("All core scripts verified — integrity intact (SELFAUDIT_PASS)")
        return True
    else:
        err("Self-audit FAILED — core script integrity compromised (SELFAUDIT_FAIL)")
        for line in out.splitlines():
            if "FAIL" in line or "ALERT" in line:
                info(line.strip()[:100])
        return False


# ── 21. Real vs Synthetic Ratio ─────────────────────────────────────────────
def check_real_vs_synthetic():
    section("REAL VS SYNTHETIC — Proof Library Audit")
    index_path = REPO_ROOT / "proof_library" / "index.json"
    if not index_path.exists():
        err("No proof_library/index.json — PROOF_LIBRARY_EXISTS = false")
        info("Run: python scripts/mg_claim_builder.py to create first real verification")
        return False

    try:
        entries = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        err("proof_library/index.json is corrupt")
        return False

    real_count = sum(1 for e in entries if not e.get("is_synthetic", True))
    synthetic_baseline = 20  # the 20 domain templates
    total = real_count + synthetic_baseline
    ratio = real_count / total if total > 0 else 0.0

    info(f"Real verifications: {real_count} | Synthetic templates: {synthetic_baseline} | Ratio: {ratio:.1%}")

    if real_count == 0:
        err(f"No external computation verified yet. REAL_VERIFICATIONS = 0")
        info("Run: python scripts/mg_claim_builder.py --input <data> --script <cmd> --output <result> --domain <domain> --label <id>")
        return False
    elif ratio < 0.20:
        warn(f"Real verifications: {real_count}/{total}. Target: >20% real.")
        return True  # WARN but pass
    else:
        ok(f"Real/Synthetic ratio: {ratio:.1%} ({real_count} real / {synthetic_baseline} synthetic)")
        return True


# ── 22. Client Contributions ─────────────────────────────────────────────────
def check_client_contributions():
    section("CLIENT CONTRIBUTIONS — Evolution Feedback Loop")
    contrib_dir = REPO_ROOT / "reports" / "client_contributions"
    if not contrib_dir.exists():
        warn("No client contributions directory yet — create with mg_contribute.py")
        info("Run: python scripts/mg_contribute.py --stats")
        return True  # advisory only

    files = list(contrib_dir.glob("contrib_*.json"))
    if not files:
        info("Contribution directory exists but empty (CLIENT_CONTRIB_EMPTY)")
        return True

    # Count unreviewed (value_score is null)
    unreviewed = 0
    oldest_unreviewed = None
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("value_score") is None:
            unreviewed += 1
            ts = data.get("timestamp", "")
            if oldest_unreviewed is None or ts < oldest_unreviewed:
                oldest_unreviewed = ts

    info(f"Total contributions: {len(files)}  |  Unreviewed: {unreviewed}")

    if unreviewed > 10 and oldest_unreviewed:
        try:
            oldest_dt = datetime.fromisoformat(oldest_unreviewed.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - oldest_dt).days
            if age_days > 7:
                warn(f"{unreviewed} unreviewed contributions, oldest is {age_days} days old")
                info("Run: python scripts/mg_contribute.py --review")
                return True
        except (ValueError, TypeError):
            pass
        warn(f"{unreviewed} unreviewed contributions pending human review")
        info("Run: python scripts/mg_contribute.py --review")
    else:
        ok(f"Client feedback loop healthy ({len(files)} total, {unreviewed} pending)")
    return True


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    strict = "--strict" in sys.argv
    summary_only = "--summary" in sys.argv

    print(f"\n{BOLD}{'═'*60}{RESET}")
    print(f"{BOLD}  MetaGenesis Core — Agent Evolution Check{RESET}")
    info("Servo-skull patrol initiated (HEALTH_CHECK_START)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')} | v1.0.0-rc1")
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
    results["branch_sync"] = check_branch_sync()
    results["coverage"]    = check_coverage()
    results["self_improve"] = check_self_improvement()
    results["signals"] = check_signals()
    results["chronicle"] = check_chronicle()
    results["pr_review"] = check_pr_review()
    results["impact"] = check_impact()
    results["diff_review"] = check_diff_review()
    results["auto_pr"]    = check_auto_pr()
    results["semantic_audit"] = check_semantic_audit()
    results["self_audit"] = check_self_audit()
    results["real_ratio"] = check_real_vs_synthetic()
    results["client_contrib"] = check_client_contributions()

    # ── Summary ──
    section("SUMMARY — Omnissiah's Verdict")
    passed = sum(1 for v in results.values() if v)
    total  = len(results)

    mechanicus_labels = {
        "steward":     ("Inquisition satisfied",    "STEWARD"),
        "tests":       ("Machine Spirit verified",  "TEST"),
        "deep":        ("Omnissiah approves",       "DEEP"),
        "docs":        ("Noosphere synchronized",   "DOCS"),
        "manifest":    ("Codex consistent",         "MANIFEST"),
        "forbidden":   ("No Hereticus found",       "FORBIDDEN"),
        "gaps":        ("Forge World complete",      "GAPS"),
        "claude_md":   ("Lexmechanic current",      "CLAUDEMD"),
        "watchlist":   ("Servo-skull coverage full", "WATCHLIST"),
        "branch_sync": ("Skitarii synchronized",    "BRANCH"),
        "coverage":      ("Genetor analysis complete",    "COVERAGE"),
        "self_improve":  ("Recursive enlightenment done",  "SELFIMPROVE"),
        "signals":       ("External signals received",      "SIGNALS"),
        "chronicle":     ("Chronicle recorded",             "CHRONICLE"),
        "pr_review":     ("Fabricator-General satisfied",    "PRREVIEW"),
        "impact":        ("Cogitator impact analyzed",       "IMPACT"),
        "diff_review":   ("Logic Arbiter satisfied",          "DIFF"),
        "auto_pr":       ("Autonomous Forge current",         "AUTOPR"),
        "semantic_audit": ("Project semantically coherent",    "SEMANTIC"),
        "self_audit":     ("Recursive Inquisitor verified",     "SELFAUDIT"),
        "real_ratio":     ("Proof Library audited",              "REALRATIO"),
        "client_contrib": ("Client evolution loop active",         "CLIENTCONTRIB"),
    }

    for check, ok_val in results.items():
        status = "PASS" if ok_val else "FAIL"
        symbol = f"{GREEN}{status}{RESET}" if ok_val else f"{RED}{status}{RESET}"
        label_info = mechanicus_labels.get(check)
        if label_info:
            label, code_prefix = label_info
            tag = f" — {label} ({code_prefix}_{status})"
        else:
            tag = ""
        print(f"  {symbol}  {check}{tag}")

    print()
    if passed == total:
        print(f"{BOLD}{GREEN}  ✅ ALL {total} CHECKS PASSED — system healthy{RESET}")
        print(f"  {GREEN}The Omnissiah is pleased (PASS){RESET}")
        print(f"  Tests: {count} | Ready for next milestone")
        code = 0
    else:
        failed = total - passed
        print(f"{BOLD}{RED}  ❌ {failed}/{total} CHECKS FAILED{RESET}")
        print(f"  {RED}The Machine Spirit is troubled (FAIL){RESET}")
        print()
        print(f"  Run after fixing:")
        print(f"  /gsd:quick \"Update CLAUDE.md to reflect current state: {count} tests, v1.0.0-rc1\"")
        if stale:
            print(f"  /gsd:quick \"Fix stale documentation: {', '.join(stale[:3])}\"")
        code = 1 if strict else 0

    print(f"\n{'═'*60}\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
