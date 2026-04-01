#!/usr/bin/env python3
"""
MetaGenesis Core — Semantic Audit
=================================
Verifies project coherence: physical anchors, claim matrix, innovations,
demo scenarios, triple sync, patent integrity. Stdlib only. No subprocess.

Usage:
    python scripts/agent_audit.py              # full check
    python scripts/agent_audit.py --summary    # summary only
"""

import io
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

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

def ok(msg):   print(f"  {GREEN}\u2705{RESET} {msg}")
def err(msg):  print(f"  {RED}\u274c{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}\u26a0 {RESET} {msg}")
def info(msg): print(f"  {CYAN}\u2192{RESET} {msg}")

def section(title):
    print(f"\n{BOLD}{CYAN}\u2550\u2550 {title} \u2550\u2550{RESET}")


# ── Helpers ─────────────────────────────────────────────────────────────────

def load_config():
    p = REPO_ROOT / "reports" / "audit_config.json"
    if not p.exists():
        err(f"audit_config.json not found at {p.relative_to(REPO_ROOT)}")
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_manifest():
    p = REPO_ROOT / "system_manifest.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def build_jobkind_to_file_map():
    """Scan backend/progress/*.py for JOB_KIND constants."""
    result = {}
    progress_dir = REPO_ROOT / "backend" / "progress"
    if not progress_dir.exists():
        return result
    pat = re.compile(r'^JOB_KIND\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
    for f in progress_dir.glob("*.py"):
        content = f.read_text(encoding="utf-8", errors="ignore")
        m = pat.search(content)
        if m:
            rel = f.relative_to(REPO_ROOT).as_posix()
            result[m.group(1)] = rel
    return result


def get_job_kind_for_claim(claim_id, index_content):
    pat = rf"## {re.escape(claim_id)}.*?job_kind.*?`([^`]+)`"
    m = re.search(pat, index_content, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else None


def find_test_files_for_claim(claim_id, job_kind):
    search_terms = {
        claim_id.lower(),
        claim_id.lower().replace("-", "_"),
        claim_id.lower().replace("-", ""),
    }
    if job_kind:
        search_terms.add(job_kind.lower())
        parts = job_kind.split("_")
        if parts:
            search_terms.add(parts[0])
    found = []
    tests_dir = REPO_ROOT / "tests"
    if not tests_dir.exists():
        return found
    for tf in tests_dir.rglob("test_*.py"):
        name_lower = tf.name.lower()
        matched = any(t in name_lower for t in search_terms)
        if not matched:
            try:
                content = tf.read_text(encoding="utf-8", errors="ignore").lower()
                matched = any(t in content for t in search_terms)
            except OSError:
                pass
        if matched:
            count = 0
            try:
                content = tf.read_text(encoding="utf-8", errors="ignore")
                count = len(re.findall(r'def test_', content))
            except OSError:
                pass
            found.append((tf.relative_to(REPO_ROOT).as_posix(), count))
    return found


# ── CHECK A: Physical Anchor Hierarchy ──────────────────────────────────────

def check_physical_anchors(config):
    section("CHECK A \u2014 PHYSICAL ANCHOR HIERARCHY")
    all_ok = True

    for claim_id, spec in config.get("physical_anchor_constants", {}).items():
        fpath = REPO_ROOT / spec["file"]
        if not fpath.exists():
            err(f"{claim_id}: file {spec['file']} not found")
            all_ok = False
            continue
        content = fpath.read_text(encoding="utf-8", errors="ignore")
        pat = rf'{re.escape(spec["constant_name"])}\s*=\s*([\d.eE+\-]+)'
        m = re.search(pat, content)
        if not m:
            err(f"{claim_id}: constant {spec['constant_name']} not found")
            all_ok = False
            continue
        actual = float(m.group(1))
        expected = spec["expected_value"]
        if abs(actual - expected) < spec["tolerance"]:
            ok(f"{claim_id}: {spec['constant_name']} = {actual} ({spec['anchor_type']})")
        else:
            err(f"{claim_id}: {spec['constant_name']} = {actual}, expected {expected}")
            all_ok = False

    manifest = load_manifest()
    jobkind_map = build_jobkind_to_file_map()
    for claim_id in manifest.get("active_claims", []):
        if claim_id.startswith("MTR-") or claim_id.startswith("PHYS-"):
            found = any(claim_id.lower().replace("-", "_") in v.lower() or
                        claim_id.lower().replace("-", "") in v.lower()
                        for v in jobkind_map.values())
            if found:
                ok(f"{claim_id}: implementation file exists")
            else:
                err(f"{claim_id}: no implementation file found")
                all_ok = False

    chain_test = REPO_ROOT / "tests" / "steward" / "test_cross_claim_chain.py"
    if chain_test.exists():
        content = chain_test.read_text(encoding="utf-8", errors="ignore")
        count = len(re.findall(r'def test_', content))
        ok(f"Cross-claim chain test: {count} test functions")
    else:
        err("test_cross_claim_chain.py not found")
        all_ok = False

    return all_ok


# ── CHECK B: Claim x Completeness Matrix ───────────────────────────────────

def check_claim_matrix():
    section("CHECK B \u2014 CLAIM x COMPLETENESS MATRIX")
    manifest = load_manifest()
    active_claims = manifest.get("active_claims", [])

    index_path = REPO_ROOT / "reports" / "scientific_claim_index.md"
    index_content = index_path.read_text(encoding="utf-8", errors="ignore") if index_path.exists() else ""
    runner_path = REPO_ROOT / "backend" / "progress" / "runner.py"
    runner_content = runner_path.read_text(encoding="utf-8", errors="ignore") if runner_path.exists() else ""
    jobkind_map = build_jobkind_to_file_map()

    info(f"{'Claim':<20} {'impl':>5} {'runner':>7} {'test':>5} {'index':>6}")
    n_ok = 0
    all_ok = True

    for claim_id in active_claims:
        job_kind = get_job_kind_for_claim(claim_id, index_content)
        impl_ok = job_kind is not None and job_kind in jobkind_map and (REPO_ROOT / jobkind_map[job_kind]).exists()

        runner_ok = False
        if job_kind and job_kind in jobkind_map:
            impl_file_stem = Path(jobkind_map[job_kind]).stem
            runner_ok = impl_file_stem in runner_content

        test_files = find_test_files_for_claim(claim_id, job_kind)
        test_ok = len(test_files) > 0
        index_ok = f"## {claim_id}" in index_content

        sym = lambda b: f"{GREEN}\u2713{RESET}" if b else f"{RED}\u2717{RESET}"
        row_ok = impl_ok and runner_ok and test_ok and index_ok
        info(f"{claim_id:<20} {sym(impl_ok):>14} {sym(runner_ok):>16} {sym(test_ok):>14} {sym(index_ok):>15}")

        if row_ok:
            n_ok += 1
        else:
            parts = []
            if not impl_ok: parts.append("impl")
            if not runner_ok: parts.append("runner")
            if not test_ok: parts.append("test")
            if not index_ok: parts.append("index")
            err(f"{claim_id}: missing {', '.join(parts)}")
            all_ok = False

    if all_ok:
        ok(f"All {len(active_claims)} claims complete")
    return all_ok, n_ok, len(active_claims)


# ── CHECK C: Innovations x Test Proof ──────────────────────────────────────

def check_innovations(config):
    section("CHECK C \u2014 INNOVATIONS x TEST PROOF")
    manifest_innovations = load_manifest().get("verified_innovations", [])
    if len(manifest_innovations) != 8:
        err(f"Expected 8 innovations, found {len(manifest_innovations)}")

    innovations_map = config.get("innovations_test_map", {})
    all_ok = True

    for innovation in manifest_innovations:
        test_path_rel = innovations_map.get(innovation)
        if not test_path_rel:
            warn(f"{innovation}: no test mapping in audit_config.json (advisory)")
            continue
        test_path = REPO_ROOT / test_path_rel
        if not test_path.exists():
            err(f"{innovation}: test file not found: {test_path_rel}")
            all_ok = False
            continue
        content = test_path.read_text(encoding="utf-8", errors="ignore")
        count = len(re.findall(r'def test_', content))
        if count >= 1:
            ok(f"{innovation}: {count} tests in {test_path_rel}")
        else:
            err(f"{innovation}: no test functions found")
            all_ok = False

    return all_ok


# ── CHECK D: Demo Scenarios x Regulatory ───────────────────────────────────

def check_demo_scenarios(config):
    section("CHECK D \u2014 DEMO SCENARIOS x REGULATORY")
    demos_root = REPO_ROOT / "demos" / "client_scenarios"
    if not demos_root.exists():
        err("demos/client_scenarios/ not found")
        return False

    demo_folders = sorted(
        [d for d in demos_root.iterdir() if d.is_dir() and d.name[0:1].isdigit()],
        key=lambda d: d.name
    )
    regulatory_keywords = config.get("demo_regulatory_keywords", {})
    all_ok = True

    for demo_dir in demo_folders:
        folder_name = demo_dir.name
        run_ok = (demo_dir / "run_scenario.py").exists()
        report_path = demo_dir / "VERIFY_REPORT.json"
        verify_ok = False
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
                verify_ok = (report.get("manifest_ok") is True
                             and report.get("semantic_ok") is True
                             and len(report.get("errors", [])) == 0)
            except (json.JSONDecodeError, OSError):
                pass

        keyword_ok = False
        readme_path = demo_dir / "README.md"
        if readme_path.exists():
            readme = readme_path.read_text(encoding="utf-8", errors="ignore")
            keywords = regulatory_keywords.get(folder_name,
                ["FDA", "Basel", "NeurIPS", "AS9100", "NASA-STD", "SOC 2", "21 CFR"])
            keyword_ok = any(kw in readme for kw in keywords)

        scenario_ok = run_ok and verify_ok
        status = f"{GREEN}PASS{RESET}" if scenario_ok else f"{RED}FAIL{RESET}"
        info(f"{folder_name}: {status} (run={run_ok}, verify={verify_ok})")
        if not keyword_ok:
            warn(f"  {folder_name}: no regulatory keywords in README (advisory)")
        if not scenario_ok:
            all_ok = False

    return all_ok


# ── CHECK E: Manifest <-> README <-> Site Sync ────────────────────────────

def check_triple_sync():
    section("CHECK E \u2014 MANIFEST <-> README <-> SITE SYNC")
    manifest = load_manifest()
    manifest_tests = manifest.get("test_count", 0)
    manifest_version = manifest.get("version", "")
    all_ok = True

    readme_path = REPO_ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8", errors="ignore") if readme_path.exists() else ""
    readme_match = re.search(r'\b(\d{3,4})\s*(?:tests?|passing|passed)', readme)
    readme_tests = int(readme_match.group(1)) if readme_match else None

    if readme_tests == manifest_tests:
        ok(f"README test count matches manifest: {manifest_tests}")
    else:
        err(f"README test count {readme_tests} != manifest {manifest_tests}")
        all_ok = False

    if manifest_version in readme:
        ok(f"README contains version {manifest_version}")
    else:
        err(f"README missing version {manifest_version}")
        all_ok = False

    html_path = REPO_ROOT / "index.html"
    if html_path.exists():
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        # Look for test count in specific HTML patterns (spans, counters)
        site_match = re.search(r'id="cn2">(\d+)<', html)
        if not site_match:
            site_match = re.search(r'class="tn">(\d+)<', html)
        if site_match:
            site_tests = int(site_match.group(1))
            if site_tests == manifest_tests:
                ok(f"Site test count matches manifest: {manifest_tests}")
            else:
                err(f"Site test count {site_tests} != manifest {manifest_tests}")
                all_ok = False
        else:
            warn("Could not detect test count in index.html")
    else:
        warn("index.html not found")

    rdg = REPO_ROOT / "docs" / "REAL_DATA_GUIDE.md"
    if rdg.exists():
        content = rdg.read_text(encoding="utf-8", errors="ignore")
        if "yehor@metagenesis-core.dev" in content:
            ok("REAL_DATA_GUIDE.md contains contact email")
        else:
            warn("REAL_DATA_GUIDE.md missing contact email (advisory)")
    else:
        warn("REAL_DATA_GUIDE.md not found")

    return all_ok


# ── CHECK F: Patent and Limitations ────────────────────────────────────────

def check_patent_integrity(config):
    section("CHECK F \u2014 PATENT AND LIMITATIONS")
    patent_cfg = config.get("patent", {})
    manifest = load_manifest()
    all_ok = True

    ppa_ok = manifest.get("ppa_number", "") == patent_cfg.get("ppa_number", "")
    if ppa_ok:
        ok(f"PPA number matches: {patent_cfg.get('ppa_number', '?')}")
    else:
        err(f"PPA number mismatch: manifest={manifest.get('ppa_number')}, config={patent_cfg.get('ppa_number')}")
        all_ok = False

    try:
        filed = datetime.strptime(manifest.get("ppa_filed", ""), "%Y-%m-%d")
        deadline = filed.replace(year=filed.year + 1)
        days = (deadline - datetime.now()).days
        if days < 0:
            err(f"DEADLINE PASSED: non-provisional was due {deadline.date()}")
            all_ok = False
        elif days < patent_cfg.get("fail_days_before_deadline", 30):
            err(f"URGENT: {days} days to non-provisional deadline ({deadline.date()})")
            all_ok = False
        elif days < patent_cfg.get("warn_days_before_deadline", 90):
            warn(f"Patent deadline {deadline.date()} ({days} days remaining)")
        else:
            ok(f"Patent deadline {deadline.date()} ({days} days remaining)")
    except (ValueError, TypeError):
        err("Could not parse ppa_filed date from manifest")
        all_ok = False

    innovations = manifest.get("verified_innovations", [])
    if len(innovations) == 8:
        ok(f"8 verified innovations in manifest")
    else:
        err(f"Expected 8 innovations, found {len(innovations)}")
        all_ok = False

    faults_path = REPO_ROOT / "reports" / "known_faults.yaml"
    if faults_path.exists():
        faults = faults_path.read_text(encoding="utf-8", errors="ignore")
        if "SCOPE_001" in faults:
            ok("SCOPE_001 documented in known_faults.yaml")
        else:
            err("SCOPE_001 missing from known_faults.yaml")
            all_ok = False
        if "tamper-evident" in faults:
            ok("tamper-evident language confirmed in known_faults.yaml")
        else:
            warn("tamper-evident not found in known_faults.yaml (advisory)")
    else:
        err("known_faults.yaml not found")
        all_ok = False

    return all_ok


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    summary_only = "--summary" in sys.argv
    config = load_config()
    if config is None:
        return 1

    manifest = load_manifest()
    version = manifest.get("version", "?")

    results = {}
    results["physical_anchors"] = check_physical_anchors(config)
    ok_b, n_ok, n_total = check_claim_matrix()
    results["claim_matrix"] = ok_b
    results["innovations"] = check_innovations(config)
    results["demo_scenarios"] = check_demo_scenarios(config)
    results["triple_sync"] = check_triple_sync()
    results["patent_integrity"] = check_patent_integrity(config)

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    all_pass = passed == total

    # Summary
    print(f"\n{BOLD}{'='*57}{RESET}")
    print(f"{BOLD}  SEMANTIC AUDIT \u2014 MetaGenesis Core v{version}{RESET}")
    print(f"{BOLD}{'='*57}{RESET}")

    labels = {
        "physical_anchors": "A: Physical Anchor Hierarchy",
        "claim_matrix":     "B: Claim x Completeness Matrix",
        "innovations":      "C: Innovations x Test Proof",
        "demo_scenarios":   "D: Demo Scenarios x Regulatory",
        "triple_sync":      "E: Manifest <-> README <-> Site",
        "patent_integrity": "F: Patent and Limitations",
    }

    for key, ok_val in results.items():
        status = "PASS" if ok_val else "FAIL"
        color = GREEN if ok_val else RED
        label = labels.get(key, key)
        print(f"  {color}{status}{RESET}  {label}")

    print(f"{BOLD}{'='*57}{RESET}")
    if all_pass:
        print(f"{BOLD}{GREEN}  ALL 6 CHECKS PASS \u2014 project coherent{RESET}")
    else:
        print(f"{BOLD}{RED}  {total - passed}/{total} CHECKS FAIL{RESET}")
    print(f"{BOLD}{'='*57}{RESET}")

    # Write report
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = REPO_ROOT / "reports" / f"AUDIT_SEMANTIC_{date_str}.md"
    lines = [
        f"# Semantic Audit \u2014 MetaGenesis Core v{version}",
        f"",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"| Check | Result |",
        f"|-------|--------|",
    ]
    for key, ok_val in results.items():
        label = labels.get(key, key)
        lines.append(f"| {label} | {'PASS' if ok_val else 'FAIL'} |")
    lines.append(f"")
    lines.append(f"**Verdict:** {'ALL 6 CHECKS PASS' if all_pass else f'{total - passed}/{total} CHECKS FAIL'}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    info(f"Report: {report_path.relative_to(REPO_ROOT)}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
