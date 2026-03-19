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
    """Stub: Design claim 15 AGENT-DRIFT-01."""
    return "Not yet implemented"


def execute_task_003():
    """Stub: Audit index.html and stale docs for v0.5.0."""
    return "Not yet implemented"


def execute_task_004():
    """Stub: Predict JOSS reviewer questions."""
    return "Not yet implemented"


def execute_task_005():
    """Stub: Draft integration API sketch."""
    return "Not yet implemented"


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

    # Run agent_learn.py observe
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    learn_script = REPO_ROOT / "scripts" / "agent_learn.py"
    if learn_script.exists():
        subprocess.run(
            [sys.executable, str(learn_script), "observe"],
            cwd=REPO_ROOT, env=env, encoding="utf-8", errors="replace"
        )

    print("Done.")


if __name__ == "__main__":
    main()
