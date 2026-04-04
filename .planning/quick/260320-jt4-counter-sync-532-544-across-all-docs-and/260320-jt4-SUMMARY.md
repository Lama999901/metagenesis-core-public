---
phase: quick
plan: 260320-jt4
subsystem: documentation
tags: [counter-sync, tests, docs]
dependency_graph:
  requires: []
  provides: [test-count-544-synced]
  affects: [all-docs, index.html, system_manifest.json, check_stale_docs.py]
tech_stack:
  added: []
  patterns: [global-replace]
key_files:
  created: []
  modified:
    - system_manifest.json
    - index.html
    - CLAUDE.md
    - AGENTS.md
    - CITATION.cff
    - CONTEXT_SNAPSHOT.md
    - CONTRIBUTING.md
    - CURSOR_MASTER_PROMPT_v2_3.md
    - README.md
    - llms.txt
    - paper.md
    - ppa/README_PPA.md
    - docs/ARCHITECTURE.md
    - docs/HOW_TO_ADD_CLAIM.md
    - docs/REAL_DATA_GUIDE.md
    - docs/ROADMAP.md
    - docs/USE_CASES.md
    - reports/known_faults.yaml
    - reports/scientific_claim_index.md
    - scripts/check_stale_docs.py
decisions:
  - Global replace 532->544 is safe because all occurrences in target files are test counters
metrics:
  duration: 3min
  completed: "2026-03-20T22:23:00Z"
---

# Quick Task 260320-jt4: Counter Sync 532 -> 544 Summary

**One-liner:** Synced test counter from 532 to 544 across 20 files after 12 new coverage-boost tests were added.

## What Was Done

### Task 1: Replace 532 with 544 in all documentation and index.html
- Updated 19 files with global find-and-replace of "532" -> "544"
- All occurrences confirmed as test counter references
- Verified zero "532" remains in any target file
- **Commit:** 04297bd

### Task 2: Update check_stale_docs.py CONTENT_CHECKS
- Replaced all 15 occurrences of "532" in CONTENT_CHECKS required strings with "544"
- Ensures stale docs checker validates against correct current test count
- **Commit:** 01a2cd5

### Task 3: Verification gates
- pytest: 544 passed, 2 skipped in 8.98s
- steward_audit: STEWARD AUDIT: PASS
- check_stale_docs --strict: All critical documentation is current (0 stale)
- Pushed to fix/counter-544 branch

## Verification Results

| Gate | Result |
|------|--------|
| pytest -q | 544 passed, 2 skipped |
| steward_audit.py | STEWARD AUDIT: PASS |
| check_stale_docs.py --strict | All current, 0 stale |

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | 04297bd | fix(quick-jt4): replace test counter 532 with 544 across all docs |
| 2 | 01a2cd5 | fix(quick-jt4): update check_stale_docs.py CONTENT_CHECKS 532 -> 544 |

## Self-Check: PASSED

All 20 modified files confirmed present. Both task commits (04297bd, 01a2cd5) verified in git log.
