---
phase: quick
plan: 260320-m4j
subsystem: agent-evolution
tags: [agent, coverage, architecture, pr-review]
dependency_graph:
  requires: []
  provides: [generate_coverage_tasks, docs/AGENT_SYSTEM.md, check_pr_review]
  affects: [scripts/agent_research.py, scripts/agent_evolution.py, scripts/check_stale_docs.py]
tech_stack:
  added: []
  patterns: [coverage-report-parsing, advisory-checks]
key_files:
  created:
    - docs/AGENT_SYSTEM.md
  modified:
    - scripts/agent_research.py
    - scripts/agent_evolution.py
    - scripts/check_stale_docs.py
decisions:
  - "generate_coverage_tasks excludes all infrastructure scripts via prefix matching"
  - "check_pr_review is advisory-only (always returns True) to avoid blocking CI"
  - "Coverage tasks require >= 2 uncovered functions per file to reduce noise"
metrics:
  duration: 4min
  completed: "2026-03-20"
  tasks_completed: 3
  tasks_total: 3
---

# Quick Task 260320-m4j: Three Agent Evolution Upgrades Summary

**One-liner:** Auto-task generator from coverage reports, 3-level architecture docs, and PR review check 15 in agent_evolution.py

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | Add generate_coverage_tasks() to agent_research.py | 4b5dc19 | scripts/agent_research.py |
| 2 | Create docs/AGENT_SYSTEM.md with 3-level architecture | 797cf9e | docs/AGENT_SYSTEM.md, scripts/check_stale_docs.py |
| 3 | Add check_pr_review() as check 15 to agent_evolution.py | 28860dd | scripts/agent_evolution.py, scripts/check_stale_docs.py |

## What Was Done

### Task 1: generate_coverage_tasks()
Added function to `scripts/agent_research.py` that:
- Finds most recent `reports/COVERAGE_REPORT_*.md` via sorted glob
- Parses the "Zero-Coverage Functions" table using regex
- Excludes infrastructure scripts (agent_*, auto_watchlist_scan, check_stale_docs, deep_verify, mg_policy_gate, steward_audit)
- Groups uncovered functions by file, requires >= 2 per file
- Appends PENDING tasks to AGENT_TASKS.md with proper TASK-NNN numbering
- Called from main() after existing generate_tasks()

### Task 2: docs/AGENT_SYSTEM.md
Created comprehensive 3-level architecture documentation:
- Level 1: GOVERNANCE (steward_audit, policy gate, stale docs)
- Level 2: VERIFICATION (mg.py, 5-layer verification, 544 tests)
- Level 3: EVOLUTION (7 agents, 15 checks, recursive self-verification)
- Includes Mechanicus parallel, file map table, claim coverage list
- Added to CONTENT_CHECKS with required: ["Level 1", "Level 2", "Level 3", "AGENT-DRIFT-01", "15 checks"]

### Task 3: check_pr_review()
Added check 15 to `scripts/agent_evolution.py`:
- Checks last commit's changed .py files for corresponding test references
- Uses grep to search tests/ directory for module stem references
- Advisory only (always returns True) -- warns but does not block
- Added to mechanicus_labels as "Fabricator-General satisfied"
- Updated CONTENT_CHECKS to require "check_pr_review" in agent_evolution.py

## Verification Results

- `python -c "from scripts.agent_research import generate_coverage_tasks"` -- PASS
- `python -c "from scripts.agent_evolution import check_pr_review"` -- PASS
- `python scripts/steward_audit.py` -- STEWARD AUDIT: PASS
- `python scripts/check_stale_docs.py` -- All critical documentation is current

## Deviations from Plan

None -- plan executed exactly as written.

## Self-Check: PASSED
