---
phase: quick
plan: 01
subsystem: documentation
tags: [counter-sync, test-count, 608]
dependency_graph:
  requires: []
  provides: [test-count-608-synced]
  affects: [check_stale_docs, all-documentation]
tech_stack:
  added: []
  patterns: [powershell-batch-replace, python-bulk-replace]
key_files:
  created: []
  modified:
    - scripts/check_stale_docs.py
    - system_manifest.json
    - README.md
    - CLAUDE.md
    - index.html
    - CONTRIBUTING.md
    - CITATION.cff
    - CURSOR_MASTER_PROMPT_v2_3.md
    - paper.md
    - reports/known_faults.yaml
    - reports/scientific_claim_index.md
    - docs/ARCHITECTURE.md
    - docs/ROADMAP.md
    - docs/HOW_TO_ADD_CLAIM.md
    - docs/REAL_DATA_GUIDE.md
    - docs/USE_CASES.md
    - ppa/README_PPA.md
decisions:
  - "608 = 601 passed + 7 new tests from test_agent_pr_creator.py"
  - "agent_pr_creator --collect-only reports 610 (includes 2 skipped) -- pre-existing, out of scope"
metrics:
  duration: 3min
  completed: "2026-03-31T06:37:53Z"
---

# Quick Task 260330-vbc: Counter Sync 601->608 Summary

Synced test count from 601 to 608 across 17 files and updated check_stale_docs.py validation rules to ban 601 and require 608.

## Tasks Completed

### Task 1: Update check_stale_docs.py banned/required lists (601->608)

**Commit:** 3493bad

Updated CONTENT_CHECKS dictionary in check_stale_docs.py for 15 file entries:
- Moved all "601" variants from `required` to `banned` lists
- Added "608" variants to `required` lists
- Patterns: "601 tests", "601 passed", "601 adversarial", "601 passing", bare "601"

### Task 2: Update 601->608 in all documentation files

**Commit:** a36714d

Updated 16 documentation files:
- index.html: 11 occurrences via PowerShell batch replace
- README.md: 8 occurrences
- CURSOR_MASTER_PROMPT_v2_3.md: 7 occurrences
- CLAUDE.md: 5 occurrences
- reports/known_faults.yaml: 4 occurrences
- CONTRIBUTING.md: 3 occurrences
- docs/ROADMAP.md, paper.md: 2 each
- system_manifest.json, CITATION.cff, docs/ARCHITECTURE.md, ppa/README_PPA.md, docs/HOW_TO_ADD_CLAIM.md, docs/REAL_DATA_GUIDE.md, docs/USE_CASES.md, reports/scientific_claim_index.md: 1 each

Files with no "601" (skipped): AGENTS.md, llms.txt, CONTEXT_SNAPSHOT.md

## Verification Results

| Check | Result |
|-------|--------|
| `python -m pytest tests/ -q` | 608 passed, 2 skipped |
| `python scripts/check_stale_docs.py --strict` | exit 0 -- all OK |
| `python scripts/agent_evolution.py --summary` | ALL 18 CHECKS PASSED |
| `python scripts/agent_pr_creator.py --summary` | Reports manifest=608 actual=610 (pre-existing: --collect-only counts skipped) |

## Deviations from Plan

None -- plan executed exactly as written.

## Notes

- agent_pr_creator.py reports 610 "actual" because it uses `--collect-only` which counts all collected tests including 2 skipped. The project convention tracks passed tests (608). This discrepancy pre-dates this task.
