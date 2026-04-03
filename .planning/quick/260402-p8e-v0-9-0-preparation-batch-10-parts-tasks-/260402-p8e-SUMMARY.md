---
phase: quick
plan: 260402-p8e
subsystem: v0.9.0-preparation
tags: [docs, governance, outreach, ci, coverage, zenodo]
key-files:
  created:
    - .zenodo.json
    - reports/AGENT_REPORT_20260402b.md
    - reports/WAVE2_OUTREACH_DRAFTS.md
    - reports/AUDIT_TRUTH_20260402.md
  modified:
    - UPDATE_PROTOCOL.md
    - ppa/README_PPA.md
    - AGENT_TASKS.md
    - scripts/agent_evolution.py
    - scripts/agent_pr_creator.py
    - tests/scripts/test_agent_pr_creator_pure.py
    - tests/scripts/test_agent_evolution_mocked.py
    - .github/workflows/weekly_agent_health.yml
    - CONTEXT_SNAPSHOT.md
    - scripts/check_stale_docs.py
    - system_manifest.json
    - 20+ documentation files (counter sync)
decisions:
  - Coverage threshold permanently locked at 65% (was 49%)
  - 4th detector (coverage drop) added to agent_pr_creator.py
  - CI weekly agent health gets write permissions for auto-commit
metrics:
  duration: ~15min
  completed: 2026-04-02
  tasks: 10
  files: 28+
---

# Quick Task 260402-p8e: v0.9.0 Preparation Batch Summary

v0.9.0 preparation: 10-part batch covering TASK-023 through TASK-027, Zenodo metadata, coverage governance, 4th PR detector, CI upgrade, and CONTEXT_SNAPSHOT refresh.

## Parts Completed

| Part | Description | Commit | Key Changes |
|------|-------------|--------|-------------|
| 1 | TASK-023: UPDATE_PROTOCOL.md v1.1 | ffbfcb9 | Date update, check_stale_docs rule added |
| 2 | TASK-024: ppa/README_PPA.md state table | ffbfcb9 | Current verification state table appended |
| 3 | TASK-025: PHYS-01/02 audit | ffbfcb9 | 6 tests found, constants verified in README/paper |
| 4 | TASK-026: Wave-2 outreach drafts | ffbfcb9 | 3 email drafts (Chollet, LMArena, Percy Liang) |
| 5 | TASK-027: Full technical truth audit | 230f6a3 | 46 checks, 45 PASS, 1 pre-existing advisory |
| 6 | Zenodo metadata | 86cd083 | .zenodo.json for v0.9.0 DOI |
| 7 | Coverage threshold 65% | 86cd083 | agent_evolution.py THRESHOLD 49->65 |
| 8 | 4th PR detector | 86cd083 | detect_coverage_drop() + 8 tests |
| 9 | CI write permissions | 7ffea7d | contents: write + auto-commit step |
| 10 | CONTEXT_SNAPSHOT refresh | 7ffea7d | Date, coverage, checks, PHYS claims, stale items |
| -- | Counter sync 1313->1321 | 490e64b | 24 files + check_stale_docs.py banned/required |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed coverage threshold test**
- **Found during:** Part 7 (coverage threshold change)
- **Issue:** test_check_coverage_pass used 56.0% mock value, below new 65% threshold
- **Fix:** Updated mock value to 81.0%
- **Files modified:** tests/scripts/test_agent_evolution_mocked.py
- **Commit:** 490e64b

**2. [Rule 2 - Critical] Counter sync required by UPDATE_PROTOCOL v1.1**
- **Found during:** Verification gates (8 new tests changed count 1313->1321)
- **Issue:** New tests from Part 8 changed test count, requiring full counter propagation
- **Fix:** Updated all 24 files with new count, updated check_stale_docs.py banned/required lists
- **Commit:** 490e64b

## Verification Gates

| Gate | Result |
|------|--------|
| steward_audit.py | PASS |
| pytest tests/ -q | 1321 passed, 2 skipped |
| deep_verify.py | ALL 13 TESTS PASSED |
| check_stale_docs.py --strict | All critical documentation is current |

## Known Stubs

None -- all changes are functional and verified.

## Self-Check: PASSED
