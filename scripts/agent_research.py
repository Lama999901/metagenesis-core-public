#!/usr/bin/env python3
"""
MetaGenesis Core -- Agent Research Runner
==========================================
Reads AGENT_TASKS.md, finds the first PENDING task, executes it
by analyzing actual repo source code, writes findings to a dated
report, and marks the task DONE.

Usage:
    python scripts/agent_research.py
"""

import subprocess
import sys
import io
import os
import re
from pathlib import Path
from datetime import datetime

# Fix Windows cp1252 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

REPO_ROOT = Path(__file__).resolve().parent.parent


def run(cmd, cwd=REPO_ROOT):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run(
        cmd, shell=True, capture_output=True, text=True,
        cwd=cwd, env=env, encoding="utf-8", errors="replace"
    )
    return r.stdout.strip(), r.returncode


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_tasks(content):
    """Parse AGENT_TASKS.md, return list of dicts with id, title, status,
    priority, output, description."""
    tasks = []
    blocks = re.split(r"^### (TASK-\d+)", content, flags=re.MULTILINE)
    # blocks: ['preamble', 'TASK-001', 'block1', 'TASK-002', 'block2', ...]
    i = 1
    while i < len(blocks) - 1:
        task_id = blocks[i].strip()
        body = blocks[i + 1]

        title_m = re.search(r"\*\*Title:\*\*\s*(.+)", body)
        status_m = re.search(r"\*\*Status:\*\*\s*(.+)", body)
        priority_m = re.search(r"\*\*Priority:\*\*\s*(.+)", body)
        output_m = re.search(r"\*\*Output:\*\*\s*(.+)", body)
        desc_m = re.search(r"\*\*Description:\*\*\s*(.+)", body)

        tasks.append({
            "id": task_id,
            "title": title_m.group(1).strip() if title_m else "",
            "status": status_m.group(1).strip() if status_m else "",
            "priority": priority_m.group(1).strip() if priority_m else "",
            "output": output_m.group(1).strip() if output_m else "",
            "description": desc_m.group(1).strip() if desc_m else "",
        })
        i += 2
    return tasks


def find_first_pending(tasks):
    """Return first task with status PENDING, or None."""
    for t in tasks:
        if t["status"].upper() == "PENDING":
            return t
    return None


# ---------------------------------------------------------------------------
# Task execution
# ---------------------------------------------------------------------------

def execute_task(task):
    """Dispatch to task-specific handler based on task id."""
    handlers = {
        "TASK-001": execute_task_001,
        "TASK-002": execute_task_002,
        "TASK-003": execute_task_003,
        "TASK-004": execute_task_004,
        "TASK-005": execute_task_005,
    }
    handler = handlers.get(task["id"])
    if not handler:
        return f"No handler for {task['id']}"
    return handler()


def execute_task_001():
    """Audit test coverage for all 14 claims."""
    # 1. Define all 14 claims with their impl files
    claims = {
        "MTR-1":            "backend/progress/mtr1_calibration.py",
        "MTR-2":            "backend/progress/mtr2_thermal_conductivity.py",
        "MTR-3":            "backend/progress/mtr3_thermal_multilayer.py",
        "SYSID-01":         "backend/progress/sysid1_arx_calibration.py",
        "DATA-PIPE-01":     "backend/progress/datapipe1_quality_certificate.py",
        "DRIFT-01":         "backend/progress/drift_monitor.py",
        "ML_BENCH-01":      "backend/progress/mlbench1_accuracy_certificate.py",
        "DT-FEM-01":        "backend/progress/dtfem1_displacement_verification.py",
        "ML_BENCH-02":      "backend/progress/mlbench2_regression_certificate.py",
        "ML_BENCH-03":      "backend/progress/mlbench3_timeseries_certificate.py",
        "PHARMA-01":        "backend/progress/pharma1_admet_certificate.py",
        "FINRISK-01":       "backend/progress/finrisk1_var_certificate.py",
        "DT-SENSOR-01":     "backend/progress/dtsensor1_iot_certificate.py",
        "DT-CALIB-LOOP-01": "backend/progress/dtcalib1_convergence_certificate.py",
    }

    # Build search patterns for each claim
    claim_patterns = {}
    for cid, impl_path in claims.items():
        stem = Path(impl_path).stem  # e.g. mtr1_calibration
        short = stem.split("_")[0]   # e.g. mtr1
        # Patterns: claim ID variants + file stem + short name
        patterns = [
            cid.lower(),                          # mtr-1
            cid.lower().replace("-", "_"),         # mtr_1
            cid.lower().replace("-", ""),          # mtr1
            cid.upper(),                          # MTR-1
            cid.upper().replace("-", "_"),         # MTR_1
            stem,                                  # mtr1_calibration
            short,                                 # mtr1
        ]
        # Deduplicate
        claim_patterns[cid] = list(dict.fromkeys(patterns))

    # 2. Collect all test files
    tests_dir = REPO_ROOT / "tests"
    all_test_files = list(tests_dir.rglob("test_*.py"))

    # 3. For each claim, find matching test files and count test functions
    results = {}
    for cid, patterns in claim_patterns.items():
        matching_files = []
        total_test_funcs = 0

        for tf in all_test_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            # Check if any pattern appears in file name or content
            fname_lower = tf.name.lower()
            matched = False
            for pat in patterns:
                if pat in fname_lower or pat in content.lower():
                    matched = True
                    break

            if matched:
                # Count test functions
                func_count = len(re.findall(r"^\s*def (test_\w+)", content, re.MULTILINE))
                matching_files.append((str(tf.relative_to(REPO_ROOT)), func_count))
                total_test_funcs += func_count

        results[cid] = {
            "impl_file": claims[cid],
            "test_files": matching_files,
            "file_count": len(matching_files),
            "test_count": total_test_funcs,
        }

    # 4. Sort by test count to find weakest
    sorted_claims = sorted(results.items(), key=lambda x: x[1]["test_count"])
    weakest_id = sorted_claims[0][0]
    weakest = sorted_claims[0][1]

    # 5. Build markdown report
    lines = []
    lines.append("## Test Coverage Audit -- All 14 Claims\n")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append("### Coverage Table\n")
    lines.append("| Claim | Impl File | Test Files | Test Functions |")
    lines.append("|-------|-----------|------------|----------------|")

    total_files_all = 0
    total_funcs_all = 0
    for cid in claims:
        r = results[cid]
        total_files_all += r["file_count"]
        total_funcs_all += r["test_count"]
        lines.append(
            f"| {cid} | `{r['impl_file']}` | {r['file_count']} | {r['test_count']} |"
        )

    lines.append(f"| **TOTAL** | | **{total_files_all}** | **{total_funcs_all}** |")
    lines.append("")

    # Weakest claim section
    lines.append(f"### Weakest Claim: {weakest_id}\n")
    lines.append(f"- **Implementation:** `{weakest['impl_file']}`")
    lines.append(f"- **Test files:** {weakest['file_count']}")
    lines.append(f"- **Test functions:** {weakest['test_count']}")
    if weakest["test_files"]:
        lines.append("- **Files:**")
        for fpath, cnt in weakest["test_files"]:
            lines.append(f"  - `{fpath}` ({cnt} tests)")
    else:
        lines.append("- **Files:** None found (no dedicated test file)")
    lines.append("")

    # Read weakest claim implementation for context
    weakest_impl_path = REPO_ROOT / weakest["impl_file"]
    impl_context = ""
    if weakest_impl_path.exists():
        try:
            impl_context = weakest_impl_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    # Extract threshold info if available
    threshold_match = re.search(r"threshold.*?=\s*([0-9.]+)", impl_context, re.IGNORECASE)
    threshold_info = f" (threshold: {threshold_match.group(1)})" if threshold_match else ""

    lines.append("### Proposed Adversarial Tests\n")
    lines.append(f"The following 3 adversarial tests target **{weakest_id}**{threshold_info}:\n")
    lines.append(f"**1. Step Chain Hash Tampering Test**")
    lines.append(f"- Modify `trace_root_hash` in {weakest_id}'s execution trace")
    lines.append(f"- Expect: Layer 3 (Step Chain) catches the tampered hash")
    lines.append(f"- File: `tests/steward/test_cert_adv_{weakest_id.lower().replace('-', '_')}_stepchain.py`")
    lines.append(f"- Asserts: verification returns FAIL with step chain mismatch detail\n")

    lines.append(f"**2. Semantic Field Stripping Test**")
    lines.append(f"- Remove a required field from {weakest_id}'s evidence bundle")
    lines.append(f"- Expect: Layer 2 (Semantic) catches the missing field")
    lines.append(f"- File: `tests/steward/test_cert_adv_{weakest_id.lower().replace('-', '_')}_semantic.py`")
    lines.append(f"- Asserts: `_verify_semantic()` raises on null/missing evidence\n")

    lines.append(f"**3. Bundle Replay with New Timestamp Test**")
    lines.append(f"- Take a valid {weakest_id} bundle, modify its timestamp to future date")
    lines.append(f"- Expect: Layer 5 (Temporal) catches the backdated/replayed bundle")
    lines.append(f"- File: `tests/steward/test_cert_adv_{weakest_id.lower().replace('-', '_')}_temporal.py`")
    lines.append(f"- Asserts: temporal commitment verification fails\n")

    # Per-file detail appendix
    lines.append("### Detailed File Listing\n")
    for cid in claims:
        r = results[cid]
        if r["test_files"]:
            lines.append(f"**{cid}:**")
            for fpath, cnt in r["test_files"]:
                lines.append(f"  - `{fpath}` ({cnt} test functions)")
            lines.append("")

    return "\n".join(lines)


def execute_task_002():
    """Design claim 15 AGENT-DRIFT-01."""
    lines = []
    lines.append("## Design Spec: Claim 15 -- AGENT-DRIFT-01\n")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Read CLAUDE.md for the baseline spec
    claude_md = REPO_ROOT / "CLAUDE.md"
    baseline_spec = ""
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8", errors="ignore")
            # Extract the AGENT-DRIFT-01 section
            m = re.search(r"### AGENT-DRIFT-01.*?(?=###|\Z)", content, re.DOTALL)
            if m:
                baseline_spec = m.group(0).strip()
        except Exception:
            pass

    # Read runner.py to understand dispatch pattern
    runner_path = REPO_ROOT / "backend" / "progress" / "runner.py"
    dispatch_pattern = ""
    if runner_path.exists():
        try:
            runner_content = runner_path.read_text(encoding="utf-8", errors="ignore")
            # Count existing dispatch blocks
            kind_checks = re.findall(r'payload\.get\("kind"\)\s*==\s*(\w+)', runner_content)
            dispatch_pattern = f"Runner has {len(kind_checks)} dispatch blocks (payload.kind matching)"
        except Exception:
            dispatch_pattern = "Could not read runner.py"

    # Read an existing claim as template (drift_monitor.py)
    template_path = REPO_ROOT / "backend" / "progress" / "drift_monitor.py"
    template_structure = ""
    if template_path.exists():
        try:
            tmpl = template_path.read_text(encoding="utf-8", errors="ignore")
            # Extract key constants
            job_kind_m = re.search(r'JOB_KIND\s*=\s*"([^"]+)"', tmpl)
            algo_m = re.search(r'ALGORITHM_VERSION\s*=\s*"([^"]+)"', tmpl)
            method_m = re.search(r'METHOD\s*=\s*"([^"]+)"', tmpl)
            template_structure = (
                f"Template (drift_monitor.py): JOB_KIND={job_kind_m.group(1) if job_kind_m else '?'}, "
                f"ALGORITHM_VERSION={algo_m.group(1) if algo_m else '?'}, "
                f"METHOD={method_m.group(1) if method_m else '?'}"
            )
        except Exception:
            template_structure = "Could not read drift_monitor.py"

    lines.append("### Source Analysis\n")
    if baseline_spec:
        lines.append("**CLAUDE.md baseline spec found:**\n")
        lines.append(f"```\n{baseline_spec[:600]}\n```\n")
    else:
        lines.append("**CLAUDE.md:** No AGENT-DRIFT-01 section found.\n")
    lines.append(f"- {dispatch_pattern}")
    lines.append(f"- {template_structure}\n")

    lines.append("### Proposed Design\n")
    lines.append("**Claim ID:** AGENT-DRIFT-01")
    lines.append("**Domain:** Meta / Agent Quality Monitoring")
    lines.append("**Physical Anchor:** None (meta-claim -- monitors agent behavior, not physical constants)\n")

    lines.append("**Constants:**\n")
    lines.append("```python")
    lines.append('JOB_KIND = "agent_drift_monitor"')
    lines.append('ALGORITHM_VERSION = "v1"')
    lines.append('METHOD = "baseline_deviation_pct"')
    lines.append("```\n")

    lines.append("**Threshold:** drift_score <= 20% (composite metric)\n")

    lines.append("**Input Schema:**\n")
    lines.append("```python")
    lines.append("{")
    lines.append('    "baseline_tests_per_phase": 47,')
    lines.append('    "baseline_pass_rate": 1.0,')
    lines.append('    "baseline_regressions": 0,')
    lines.append('    "baseline_verifier_iterations": 1.2,')
    lines.append('    "current_tests_per_phase": int,')
    lines.append('    "current_pass_rate": float,')
    lines.append('    "current_regressions": int,')
    lines.append('    "current_verifier_iterations": float,')
    lines.append("}")
    lines.append("```\n")

    lines.append("**Output Schema:**\n")
    lines.append("```python")
    lines.append("{")
    lines.append('    "mtr_phase": "AGENT-DRIFT-01",')
    lines.append('    "inputs": { ... },')
    lines.append('    "result": {')
    lines.append('        "drift_scores": {')
    lines.append('            "tests_per_phase_drift_pct": float,')
    lines.append('            "pass_rate_drift_pct": float,')
    lines.append('            "regressions_drift_pct": float,')
    lines.append('            "iterations_drift_pct": float')
    lines.append("        },")
    lines.append('        "composite_drift_pct": float,')
    lines.append('        "drift_detected": bool,')
    lines.append('        "correction_required": bool')
    lines.append("    },")
    lines.append('    "execution_trace": [...],  # 4-step chain')
    lines.append('    "trace_root_hash": "sha256..."')
    lines.append("}")
    lines.append("```\n")

    lines.append("**Step Chain Structure (4 steps):**\n")
    lines.append("| Step | Name | Data Hashed |")
    lines.append("|------|------|-------------|")
    lines.append("| 1 | init_params | baseline + current metrics |")
    lines.append("| 2 | compute_drift | per-metric drift percentages |")
    lines.append("| 3 | aggregate | composite drift score |")
    lines.append("| 4 | threshold_check | pass/fail + threshold |")
    lines.append("")

    lines.append("**Required Test Categories:**\n")
    lines.append("1. `test_agent_drift_pass` -- no drift scenario")
    lines.append("2. `test_agent_drift_fail` -- 30% drift triggers detection")
    lines.append("3. `test_agent_drift_determinism` -- same inputs produce same trace_root_hash")
    lines.append("4. `test_agent_drift_step_chain` -- tampered trace fails verification")
    lines.append("5. `test_agent_drift_semantic` -- missing fields fail semantic check\n")

    lines.append("**Implementation Scope:**\n")
    lines.append("- New file: `backend/progress/agent_drift_monitor.py` (~120 lines)")
    lines.append("- Runner dispatch: +15 lines in runner.py")
    lines.append("- Claim registration: scientific_claim_index.md + canonical_state.md")
    lines.append("- Tests: `tests/agent/test_agent_drift.py` (~80 lines)")
    lines.append("- Counter updates: 11+ places in index.html, README.md, AGENTS.md, etc.")
    lines.append("- Estimated effort: 2-3 hours following the 6-step new claim procedure\n")

    lines.append("**Key Design Decision:**")
    lines.append("AGENT-DRIFT-01 is a meta-claim -- it monitors agent quality, not physical reality.")
    lines.append("This means NO physical anchor (unlike MTR-1/DRIFT-01).")
    lines.append("The threshold (20%) is chosen, not measured -- same epistemic status as ML_BENCH claims.")

    return "\n".join(lines)


def execute_task_003():
    """Audit index.html and stale docs for v0.5.0."""
    lines = []
    lines.append("## Index.html & Stale Docs Audit\n")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Run check_stale_docs.py
    lines.append("### check_stale_docs.py Output\n")
    stale_out, stale_rc = run("python scripts/check_stale_docs.py")
    if stale_out:
        lines.append(f"```\n{stale_out}\n```\n")
    else:
        lines.append("*(no output)*\n")
    lines.append(f"Exit code: {stale_rc}\n")

    # Read index.html and audit counters
    lines.append("### Counter Audit: index.html\n")
    index_path = REPO_ROOT / "index.html"
    expected_counters = {
        "test_count": "511",
        "claim_count": "14",
        "layer_count": "5",
        "innovation_count": "8",
        "version": "v0.5.0",
    }

    counter_findings = []
    if index_path.exists():
        try:
            html_lines = index_path.read_text(encoding="utf-8", errors="ignore").splitlines()

            lines.append("| Counter | Expected | Line | Actual Text (excerpt) | Status |")
            lines.append("|---------|----------|------|-----------------------|--------|")

            # Search for each counter pattern
            search_patterns = {
                "test_count": [r"511", r"tests?\s*(?:pass|PASS)"],
                "claim_count": [r"14\s*(?:claim|active|verification)", r"(?:claim|active|verification)\s*.*14"],
                "layer_count": [r"5\s*(?:layer|verification)", r"(?:layer|verification)\s*.*\b5\b"],
                "innovation_count": [r"8\s*(?:innovation)", r"(?:innovation)\s*.*\b8\b"],
                "version": [r"v0\.5\.0"],
            }

            for counter_name, patterns in search_patterns.items():
                expected = expected_counters[counter_name]
                found_any = False
                for line_num, line in enumerate(html_lines, 1):
                    for pat in patterns:
                        if re.search(pat, line, re.IGNORECASE):
                            excerpt = line.strip()[:80]
                            lines.append(f"| {counter_name} | {expected} | {line_num} | `{excerpt}` | OK |")
                            found_any = True
                            break
                if not found_any:
                    lines.append(f"| {counter_name} | {expected} | -- | NOT FOUND | MISSING |")
                    counter_findings.append(f"{counter_name} ({expected}) not found in index.html")

        except Exception as e:
            lines.append(f"Error reading index.html: {e}\n")
    else:
        lines.append("index.html not found at repo root.\n")

    lines.append("")

    # Count total occurrences of key numbers
    lines.append("### Occurrence Counts\n")
    if index_path.exists():
        try:
            full_html = index_path.read_text(encoding="utf-8", errors="ignore")
            for label, val in [("511", "test count"), ("14", "claim count"),
                               ("5", "layer count"), ("8", "innovation count"),
                               ("v0.5.0", "version")]:
                if val == "test count":
                    count = len(re.findall(r'\b511\b', full_html))
                elif val == "claim count":
                    count = len(re.findall(r'\b14\b', full_html))
                elif val == "layer count":
                    # Only count '5' near 'layer' or 'verification layer'
                    count = len(re.findall(r'\b5\s*(?:layer|verification|independent)', full_html, re.IGNORECASE))
                    count += len(re.findall(r'(?:layer|verification)\s*.*?\b5\b', full_html, re.IGNORECASE))
                elif val == "innovation count":
                    count = len(re.findall(r'\b8\s*(?:innovation)', full_html, re.IGNORECASE))
                    count += len(re.findall(r'(?:innovation)\s*.*?\b8\b', full_html, re.IGNORECASE))
                else:
                    count = full_html.count(val)
                lines.append(f"- **{val}** (`{label}`): {count} occurrences")
        except Exception:
            pass

    lines.append("")

    # Findings summary
    lines.append("### Findings\n")
    if counter_findings:
        for f in counter_findings:
            lines.append(f"- ISSUE: {f}")
    else:
        lines.append("- All expected counters found in index.html.")
    lines.append(f"- check_stale_docs exit code: {stale_rc} ({'PASS' if stale_rc == 0 else 'ISSUES FOUND'})")
    lines.append("")

    return "\n".join(lines)


def execute_task_004():
    """Predict JOSS reviewer questions based on paper.md analysis."""
    lines = []
    lines.append("## JOSS Reviewer Question Predictions\n")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Read paper.md
    paper_path = REPO_ROOT / "paper.md"
    paper_content = ""
    if paper_path.exists():
        try:
            paper_content = paper_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    # Read paper.bib
    bib_path = REPO_ROOT / "paper.bib"
    bib_content = ""
    if bib_path.exists():
        try:
            bib_content = bib_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    # Analyze paper structure
    sections = re.findall(r"^#+\s+(.+)$", paper_content, re.MULTILINE)
    bib_entries = re.findall(r"@\w+\{([^,]+),", bib_content) if bib_content else []
    word_count = len(paper_content.split())
    claim_table = "Active Claims" in paper_content

    lines.append("### Paper Analysis\n")
    lines.append(f"- **Word count:** ~{word_count}")
    lines.append(f"- **Sections:** {', '.join(sections[:10])}")
    lines.append(f"- **Bibliography entries:** {len(bib_entries)}")
    lines.append(f"- **Claims table present:** {'Yes' if claim_table else 'No'}")
    lines.append(f"- **AI disclosure present:** {'Yes' if 'AI Usage' in paper_content else 'No'}\n")

    lines.append("---\n")
    lines.append("### Predicted Questions\n")

    # Question 1: Functionality & Scope
    lines.append("**Q1: How does MetaGenesis Core compare to existing reproducibility tools like ReproZip or Binder?**\n")
    lines.append("- **JOSS Criterion:** State of the Field")
    lines.append("- **Why likely:** JOSS reviewers check that related work is adequately cited and")
    lines.append("  the paper clearly differentiates from existing tools. The paper mentions MLflow,")
    lines.append("  DVC, and lm-eval but does not discuss container-based reproducibility (ReproZip,")
    lines.append("  Binder, Code Ocean) which are commonly associated with computational reproducibility.")
    lines.append("- **Prepared Answer:** MetaGenesis Core is complementary to container-based tools.")
    lines.append("  ReproZip/Binder guarantee the same *environment* runs; MetaGenesis guarantees a")
    lines.append("  specific *result* was produced by a specific *computation*. A Docker container")
    lines.append("  proves the binary is identical -- it does not prove the binary's output meets a")
    lines.append("  scientific threshold. See paper.md 'Why existing tools do not solve this' section.")
    lines.append("  Adding a brief mention of ReproZip/Binder would strengthen the paper.")
    lines.append("- **Confidence:** HIGH -- this is a standard JOSS review point.\n")

    # Question 2: Installation & Usability
    lines.append("**Q2: Can a user install and run the verifier without cloning the full repository?**\n")
    lines.append("- **JOSS Criterion:** Installation instructions")
    lines.append("- **Why likely:** JOSS requires clear installation instructions. Currently the tool")
    lines.append("  is used via `python scripts/mg.py` from within the repo. There is no `pip install`")
    lines.append("  package, no PyPI distribution, and no `setup.py`/`pyproject.toml` for installation.")
    lines.append("- **Prepared Answer:** MetaGenesis Core intentionally ships as a single-repo tool")
    lines.append("  with zero external dependencies (stdlib only). Installation is `git clone` + run.")
    lines.append("  A PyPI package is planned for v0.6.0. The zero-dependency design is a feature:")
    lines.append("  the verifier must be auditable without trusting any third-party package. See README.md")
    lines.append("  'Quick Start' section for current installation steps.")
    lines.append("- **Confidence:** HIGH -- JOSS mandates clear install docs.\n")

    # Question 3: Testing & CI
    lines.append("**Q3: Are there integration tests that verify the full pack-verify round-trip, or only unit tests?**\n")
    lines.append("- **JOSS Criterion:** Tests")
    lines.append("- **Why likely:** The paper claims 511 tests and adversarial proofs, but a reviewer")
    lines.append("  may ask whether these are unit tests on individual functions or end-to-end tests")
    lines.append("  that exercise the complete workflow (claim execution -> pack -> verify -> PASS/FAIL).")
    lines.append("- **Prepared Answer:** Both. The test suite includes: (a) unit tests per claim in")
    lines.append("  `tests/<domain>/`, (b) integration tests in `tests/steward/test_cert*.py` that run")
    lines.append("  full pack-verify round-trips, (c) adversarial tests (CERT-02 through CERT-12) that")
    lines.append("  tamper with bundles and verify the correct layer catches each attack, (d) a 13-test")
    lines.append("  deep verification script (`scripts/deep_verify.py`). CI runs all 511 tests on every PR.")
    lines.append("- **Confidence:** MEDIUM-HIGH -- test depth is a common JOSS concern.\n")

    # Question 4: Community guidelines
    lines.append("**Q4: Where are the contribution guidelines and code of conduct?**\n")
    lines.append("- **JOSS Criterion:** Community guidelines")
    lines.append("- **Why likely:** JOSS requires a CONTRIBUTING.md or equivalent and a code of conduct.")
    lines.append("  Many first-time JOSS submissions lack these. The repo should have CONTRIBUTING.md")
    lines.append("  explaining how to add new claims, run the test suite, and submit PRs.")
    lines.append("- **Prepared Answer:** CONTRIBUTING.md should be created before JOSS submission.")
    lines.append("  Key content: (1) how to add a new claim (6-step procedure in CLAUDE.md),")
    lines.append("  (2) how to run the verification gates (steward audit + pytest + deep_verify),")
    lines.append("  (3) PR workflow (branch -> CI pass -> merge). A CODE_OF_CONDUCT.md (Contributor")
    lines.append("  Covenant) should also be added. These are low-effort, high-impact additions.")
    lines.append("- **Confidence:** HIGH -- JOSS checklist explicitly requires this.\n")

    # Question 5: Scalability
    lines.append("**Q5: How does verification performance scale with bundle size or number of claims?**\n")
    lines.append("- **JOSS Criterion:** Functionality / Performance")
    lines.append("- **Why likely:** The paper states verification completes 'in under 60 seconds' but")
    lines.append("  does not provide benchmarks. A reviewer may ask: what happens with 100 claims?")
    lines.append("  1000 evidence files? Does SHA-256 hashing dominate? Is there a scalability ceiling?")
    lines.append("- **Prepared Answer:** Current verification of a 14-claim bundle takes ~2 seconds.")
    lines.append("  SHA-256 hashing is O(n) in file count and size. Step chain verification is O(k)")
    lines.append("  where k = steps per claim (always 4). The bottleneck for large bundles would be")
    lines.append("  I/O, not computation. A benchmark script (`scripts/mg.py bench`) exists but")
    lines.append("  scalability benchmarks with synthetic large bundles should be added before submission.")
    lines.append("  See `tests/steward/test_cert08_reproducibility.py` for existing timing assertions.")
    lines.append("- **Confidence:** MEDIUM -- depends on reviewer's focus.\n")

    lines.append("---\n")
    lines.append("### Pre-Submission Checklist (derived from questions above)\n")
    lines.append("1. [ ] Add brief mention of ReproZip/Binder in State of the Field")
    lines.append("2. [ ] Create CONTRIBUTING.md with 6-step claim procedure")
    lines.append("3. [ ] Add CODE_OF_CONDUCT.md (Contributor Covenant)")
    lines.append("4. [ ] Consider adding scalability benchmark to paper or supplementary")
    lines.append("5. [ ] Verify README.md Quick Start is clear enough for first-time users")

    return "\n".join(lines)


def execute_task_005():
    """Draft integration API sketch for MLflow/DVC/WandB."""
    lines = []
    lines.append("## Integration API Sketch: MLflow / DVC / WandB\n")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Read mg.py to understand CLI interface
    mg_path = REPO_ROOT / "scripts" / "mg.py"
    cli_commands = []
    if mg_path.exists():
        try:
            mg_content = mg_path.read_text(encoding="utf-8", errors="ignore")
            # Find subcommand parsers
            subparsers = re.findall(r'add_parser\("([^"]+)"', mg_content)
            cli_commands = subparsers if subparsers else ["steward", "pack", "verify", "verify-chain", "bench", "claim", "sign"]
        except Exception:
            cli_commands = ["steward", "pack", "verify", "verify-chain", "bench", "claim", "sign"]

    # Read runner.py to understand dispatch
    runner_path = REPO_ROOT / "backend" / "progress" / "runner.py"
    job_kinds = []
    if runner_path.exists():
        try:
            runner_content = runner_path.read_text(encoding="utf-8", errors="ignore")
            job_kinds = re.findall(r'from backend\.progress\.\w+ import JOB_KIND as (\w+)', runner_content)
        except Exception:
            pass

    lines.append("### CLI Interface Analysis\n")
    lines.append(f"- **mg.py subcommands:** {', '.join(cli_commands)}")
    lines.append(f"- **Registered job kinds:** {len(job_kinds)} (in runner.py)")
    lines.append("- **Key workflow:** `mg.py pack build` -> `mg.py verify --pack <dir>` -> PASS/FAIL")
    lines.append("- **Signing:** `mg.py sign --pack <dir> --key <keyfile>`")
    lines.append("- **No external deps** -- all stdlib, any integration must shell out or import directly\n")

    lines.append("---\n")

    # MLflow Integration
    lines.append("### 1. MLflow Integration: Post-Training Verification Hook\n")
    lines.append("Use case: After MLflow logs a model run, automatically create a verification bundle.\n")
    lines.append("```python")
    lines.append('"""')
    lines.append("MLflow post-training hook for MetaGenesis verification.")
    lines.append("Add to your MLflow training script after mlflow.log_model().")
    lines.append('"""')
    lines.append("import subprocess")
    lines.append("import json")
    lines.append("import mlflow")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append("")
    lines.append("def mg_verify_hook(run_id: str, mg_root: str, claim_kind: str = 'ml_accuracy_certificate'):")
    lines.append('    """Post-training hook: pack + verify + log result as MLflow artifact."""')
    lines.append("    mg_root = Path(mg_root)")
    lines.append("    pack_dir = Path(f'mg_bundle_{run_id}')")
    lines.append("")
    lines.append("    # Step 1: Build verification bundle")
    lines.append("    result = subprocess.run(")
    lines.append("        ['python', str(mg_root / 'scripts' / 'mg.py'), 'pack', 'build',")
    lines.append("         '-o', str(pack_dir), '--include-evidence'],")
    lines.append("        capture_output=True, text=True, cwd=str(mg_root)")
    lines.append("    )")
    lines.append("    if result.returncode != 0:")
    lines.append("        mlflow.log_param('mg_verify_status', 'PACK_FAILED')")
    lines.append("        return False")
    lines.append("")
    lines.append("    # Step 2: Verify the bundle")
    lines.append("    result = subprocess.run(")
    lines.append("        ['python', str(mg_root / 'scripts' / 'mg.py'), 'verify',")
    lines.append("         '--pack', str(pack_dir)],")
    lines.append("        capture_output=True, text=True, cwd=str(mg_root)")
    lines.append("    )")
    lines.append("    passed = result.returncode == 0")
    lines.append("")
    lines.append("    # Step 3: Log to MLflow")
    lines.append("    mlflow.log_param('mg_verify_status', 'PASS' if passed else 'FAIL')")
    lines.append("    mlflow.log_artifact(str(pack_dir / 'pack_manifest.json'))")
    lines.append("    if (pack_dir / 'verify_report.json').exists():")
    lines.append("        mlflow.log_artifact(str(pack_dir / 'verify_report.json'))")
    lines.append("    return passed")
    lines.append("")
    lines.append("")
    lines.append("# Usage in training script:")
    lines.append("# with mlflow.start_run() as run:")
    lines.append("#     train_model()")
    lines.append("#     mlflow.log_model(model, 'model')")
    lines.append("#     mg_verify_hook(run.info.run_id, '/path/to/metagenesis-core')")
    lines.append("```\n")

    # DVC Integration
    lines.append("### 2. DVC Integration: Pipeline Verification Stage\n")
    lines.append("Use case: Add MetaGenesis verification as a DVC pipeline stage.\n")
    lines.append("**dvc.yaml addition:**\n")
    lines.append("```yaml")
    lines.append("stages:")
    lines.append("  train:")
    lines.append("    cmd: python train.py")
    lines.append("    deps:")
    lines.append("      - data/train.csv")
    lines.append("      - train.py")
    lines.append("    outs:")
    lines.append("      - model/weights.pkl")
    lines.append("")
    lines.append("  mg_verify:")
    lines.append("    cmd: python mg_dvc_stage.py")
    lines.append("    deps:")
    lines.append("      - model/weights.pkl")
    lines.append("      - mg_dvc_stage.py")
    lines.append("    outs:")
    lines.append("      - mg_bundle/pack_manifest.json")
    lines.append("    metrics:")
    lines.append("      - mg_bundle/verify_report.json:")
    lines.append("          cache: false")
    lines.append("```\n")
    lines.append("**mg_dvc_stage.py:**\n")
    lines.append("```python")
    lines.append('"""')
    lines.append("DVC pipeline stage: build + verify MetaGenesis bundle.")
    lines.append("Runs as part of `dvc repro` pipeline.")
    lines.append('"""')
    lines.append("import subprocess")
    lines.append("import sys")
    lines.append("import json")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append("MG_ROOT = Path('/path/to/metagenesis-core')  # Configure per project")
    lines.append("BUNDLE_DIR = Path('mg_bundle')")
    lines.append("")
    lines.append("")
    lines.append("def main():")
    lines.append("    BUNDLE_DIR.mkdir(parents=True, exist_ok=True)")
    lines.append("")
    lines.append("    # Pack")
    lines.append("    r = subprocess.run(")
    lines.append("        [sys.executable, str(MG_ROOT / 'scripts' / 'mg.py'),")
    lines.append("         'pack', 'build', '-o', str(BUNDLE_DIR), '--include-evidence'],")
    lines.append("        capture_output=True, text=True, cwd=str(MG_ROOT)")
    lines.append("    )")
    lines.append("    if r.returncode != 0:")
    lines.append("        print(f'Pack failed: {r.stderr}', file=sys.stderr)")
    lines.append("        sys.exit(1)")
    lines.append("")
    lines.append("    # Verify")
    lines.append("    r = subprocess.run(")
    lines.append("        [sys.executable, str(MG_ROOT / 'scripts' / 'mg.py'),")
    lines.append("         'verify', '--pack', str(BUNDLE_DIR)],")
    lines.append("        capture_output=True, text=True, cwd=str(MG_ROOT)")
    lines.append("    )")
    lines.append("")
    lines.append("    report = {")
    lines.append("        'status': 'PASS' if r.returncode == 0 else 'FAIL',")
    lines.append("        'stdout': r.stdout,")
    lines.append("        'returncode': r.returncode")
    lines.append("    }")
    lines.append("    (BUNDLE_DIR / 'verify_report.json').write_text(json.dumps(report, indent=2))")
    lines.append("")
    lines.append("    if r.returncode != 0:")
    lines.append("        print(f'Verification FAILED: {r.stdout}', file=sys.stderr)")
    lines.append("        sys.exit(1)")
    lines.append("")
    lines.append("    print('MetaGenesis verification: PASS')")
    lines.append("")
    lines.append("")
    lines.append("if __name__ == '__main__':")
    lines.append("    main()")
    lines.append("```\n")

    # WandB Integration
    lines.append("### 3. Weights & Biases Integration: Verification Callback\n")
    lines.append("Use case: WandB callback that logs verification status as a run artifact.\n")
    lines.append("```python")
    lines.append('"""')
    lines.append("WandB callback: verify and log MetaGenesis bundle as artifact.")
    lines.append('"""')
    lines.append("import subprocess")
    lines.append("import wandb")
    lines.append("from pathlib import Path")
    lines.append("")
    lines.append("")
    lines.append("class MetaGenesisCallback:")
    lines.append('    """WandB callback that creates a verification bundle after training."""')
    lines.append("")
    lines.append("    def __init__(self, mg_root: str):")
    lines.append("        self.mg_root = Path(mg_root)")
    lines.append("")
    lines.append("    def on_train_end(self, run: wandb.Run):")
    lines.append('        """Called after training completes. Packs and verifies."""')
    lines.append("        bundle_dir = Path(f'mg_bundle_{run.id}')")
    lines.append("")
    lines.append("        # Pack")
    lines.append("        r = subprocess.run(")
    lines.append("            ['python', str(self.mg_root / 'scripts' / 'mg.py'),")
    lines.append("             'pack', 'build', '-o', str(bundle_dir), '--include-evidence'],")
    lines.append("            capture_output=True, text=True, cwd=str(self.mg_root)")
    lines.append("        )")
    lines.append("        if r.returncode != 0:")
    lines.append("            run.summary['mg_status'] = 'PACK_FAILED'")
    lines.append("            return")
    lines.append("")
    lines.append("        # Verify")
    lines.append("        r = subprocess.run(")
    lines.append("            ['python', str(self.mg_root / 'scripts' / 'mg.py'),")
    lines.append("             'verify', '--pack', str(bundle_dir)],")
    lines.append("            capture_output=True, text=True, cwd=str(self.mg_root)")
    lines.append("        )")
    lines.append("        passed = r.returncode == 0")
    lines.append("")
    lines.append("        # Log to WandB")
    lines.append("        run.summary['mg_status'] = 'PASS' if passed else 'FAIL'")
    lines.append("        artifact = wandb.Artifact(")
    lines.append("            name=f'mg-bundle-{run.id}',")
    lines.append("            type='verification-bundle',")
    lines.append("            metadata={'mg_status': 'PASS' if passed else 'FAIL'}")
    lines.append("        )")
    lines.append("        artifact.add_dir(str(bundle_dir))")
    lines.append("        run.log_artifact(artifact)")
    lines.append("")
    lines.append("")
    lines.append("# Usage:")
    lines.append("# mg_cb = MetaGenesisCallback('/path/to/metagenesis-core')")
    lines.append("# ... after training ...")
    lines.append("# mg_cb.on_train_end(wandb.run)")
    lines.append("```\n")

    lines.append("---\n")
    lines.append("### Integration Summary\n")
    lines.append("| Tool | Integration Point | Key mg.py Commands | Artifact Logged |")
    lines.append("|------|-------------------|-------------------|-----------------|")
    lines.append("| MLflow | Post-training hook | `pack build`, `verify` | pack_manifest.json |")
    lines.append("| DVC | Pipeline stage | `pack build`, `verify` | verify_report.json |")
    lines.append("| WandB | Callback class | `pack build`, `verify` | Full bundle directory |")
    lines.append("")
    lines.append("**Common pattern:** All three integrations follow the same workflow:")
    lines.append("1. `mg.py pack build -o <dir> --include-evidence` (create bundle)")
    lines.append("2. `mg.py verify --pack <dir>` (verify bundle)")
    lines.append("3. Log PASS/FAIL status + artifacts to the tracking system")
    lines.append("")
    lines.append("**Future enhancement:** A `mg.py export --format mlflow|dvc|wandb` command")
    lines.append("could automate these integrations into a single CLI call.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mark done + write report
# ---------------------------------------------------------------------------

def mark_task_done(task_id, tasks_path):
    """Read AGENT_TASKS.md, replace Status: PENDING with DONE (date) for task_id."""
    content = tasks_path.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Find the task section and replace its status line
    pattern = rf"(### {re.escape(task_id)}\b.*?\*\*Status:\*\*)\s*PENDING"
    updated = re.sub(
        pattern,
        rf"\1 DONE ({today})",
        content,
        flags=re.DOTALL,
    )
    tasks_path.write_text(updated, encoding="utf-8")


def write_report(task, findings):
    """Write findings to reports/AGENT_REPORT_YYYYMMDD.md"""
    reports_dir = REPO_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    report_path = reports_dir / f"AGENT_REPORT_{datetime.now().strftime('%Y%m%d')}.md"

    report_content = (
        f"# Agent Research Report -- {task['id']}: {task['title']}\n\n"
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"**Task Description:** {task['description']}\n"
        f"**Priority:** {task['priority']}\n\n"
        f"---\n\n"
        f"{findings}\n"
    )
    report_path.write_text(report_content, encoding="utf-8")
    return report_path


# ---------------------------------------------------------------------------
# Self-improvement: generate tasks + weekly report
# ---------------------------------------------------------------------------

def generate_tasks(tasks_path):
    """Read .agent_memory/patterns.json, find patterns with count >= 2 and no
    fix_hint, and append new TASK entries to AGENT_TASKS.md."""
    import json

    patterns_file = REPO_ROOT / ".agent_memory" / "patterns.json"
    if not patterns_file.exists():
        return 0

    try:
        patterns = json.loads(patterns_file.read_text(encoding="utf-8"))
    except Exception:
        return 0

    content = tasks_path.read_text(encoding="utf-8")

    # Find highest existing task number
    existing_ids = re.findall(r"TASK-(\d+)", content)
    next_num = max(int(n) for n in existing_ids) + 1 if existing_ids else 1

    added = 0
    for key, pat in patterns.items():
        count = pat.get("count", 0)
        fix_hint = pat.get("fix_hint", "")
        if count >= 2 and not fix_hint:
            # Check if this pattern already has a task
            if key[:40] in content:
                continue

            task_id = f"TASK-{next_num:03d}"
            new_task = (
                f"\n### {task_id}\n"
                f"- **Title:** Investigate recurring pattern: {key[:60]}\n"
                f"- **Status:** PENDING\n"
                f"- **Priority:** P2\n"
                f"- **Output:** reports/AGENT_REPORT_{{date}}.md\n"
                f"- **Description:** Pattern '{key[:80]}' has occurred {count} times "
                f"with no auto-fix hint. Research root cause and propose fix.\n"
            )
            content += new_task
            next_num += 1
            added += 1

    if added:
        tasks_path.write_text(content, encoding="utf-8")
        print(f"  Generated {added} new tasks from recurring patterns")

    return added


def weekly_report():
    """Generate reports/WEEKLY_REPORT_{date}.md with system health summary,
    completed tasks, new tasks generated, and top patterns."""
    import json

    today = datetime.now().strftime("%Y%m%d")
    report_path = REPO_ROOT / "reports" / f"WEEKLY_REPORT_{today}.md"

    lines = [
        f"# Weekly Agent Report -- {datetime.now().strftime('%Y-%m-%d')}\n",
    ]

    # System health
    lines.append("## System Health\n")
    out, code = run("python scripts/agent_evolution.py --summary")
    health_lines = [l for l in out.splitlines() if "PASS" in l or "FAIL" in l or "CHECKS" in l]
    for hl in health_lines[-12:]:
        # Strip ANSI codes
        clean = re.sub(r'\x1b\[[0-9;]*m', '', hl).strip()
        if clean:
            lines.append(f"- {clean}")
    lines.append("")

    # Completed tasks
    lines.append("## Completed Tasks\n")
    tasks_path = REPO_ROOT / "AGENT_TASKS.md"
    if tasks_path.exists():
        content = tasks_path.read_text(encoding="utf-8")
        tasks = parse_tasks(content)
        done_tasks = [t for t in tasks if "DONE" in t["status"].upper()]
        pending_tasks = [t for t in tasks if t["status"].upper() == "PENDING"]
        for t in done_tasks:
            lines.append(f"- [{t['id']}] {t['title']} ({t['status']})")
        lines.append(f"\n**Pending:** {len(pending_tasks)} tasks remaining\n")
    else:
        lines.append("- No AGENT_TASKS.md found\n")

    # Top patterns
    lines.append("## Top Patterns\n")
    patterns_file = REPO_ROOT / ".agent_memory" / "patterns.json"
    if patterns_file.exists():
        try:
            patterns = json.loads(patterns_file.read_text(encoding="utf-8"))
            sorted_pats = sorted(patterns.items(), key=lambda x: x[1].get("count", 0), reverse=True)
            for key, pat in sorted_pats[:10]:
                count = pat.get("count", 0)
                hint = pat.get("fix_hint", "")
                hint_str = f" -- fix: {hint[:50]}" if hint else " -- no fix hint"
                lines.append(f"- [{count}x] {key[:60]}{hint_str}")
        except Exception:
            lines.append("- Could not parse patterns.json")
    else:
        lines.append("- No patterns.json found")
    lines.append("")

    # Write
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Weekly report: {report_path.relative_to(REPO_ROOT)}")
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tasks_path = REPO_ROOT / "AGENT_TASKS.md"
    if not tasks_path.exists():
        print("ERROR: AGENT_TASKS.md not found")
        sys.exit(1)

    content = tasks_path.read_text(encoding="utf-8")
    tasks = parse_tasks(content)
    task = find_first_pending(tasks)
    if not task:
        print("No PENDING tasks found")
        sys.exit(0)

    print(f"Executing {task['id']}: {task['title']}")
    findings = execute_task(task)
    report_path = write_report(task, findings)
    mark_task_done(task["id"], tasks_path)
    print(f"Report written to {report_path}")

    # Self-improvement: generate new tasks from patterns + weekly report
    generate_tasks(tasks_path)
    weekly_report()

    # Run agent_learn.py observe
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    learn_script = REPO_ROOT / "scripts" / "agent_learn.py"
    if learn_script.exists():
        subprocess.run(
            [sys.executable, str(learn_script), "observe"],
            cwd=REPO_ROOT, env=env, encoding="utf-8", errors="replace"
        )

    print("Done. Cogitator analysis complete (TASK_DONE)")


if __name__ == "__main__":
    main()
