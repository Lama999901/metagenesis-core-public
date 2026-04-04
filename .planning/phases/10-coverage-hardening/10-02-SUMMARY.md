---
phase: 10-coverage-hardening
plan: 02
subsystem: testing
tags: [pytest, monkeypatch, coverage, agent-scripts]

requires:
  - phase: 10-01
    provides: "coverage tests for check_stale_docs, deep_verify, check_coverage"
provides:
  - "33 new tests covering agent_research, agent_diff_review, agent_pr_creator, agent_learn"
  - "write_report(), review_file(), detect_stale_counters(), detect_manifest_sync(), recall(), brief(), stats() covered"
affects: [coverage-reports]

tech-stack:
  added: []
  patterns: [patch.object-context-manager-for-module-globals, capsys-for-stdout-testing]

key-files:
  created:
    - tests/scripts/test_agent_research_write_report.py
    - tests/scripts/test_agent_diff_review_main.py
    - tests/scripts/test_agent_pr_creator_detectors.py
    - tests/scripts/test_agent_learn_commands.py
  modified: []

key-decisions:
  - "Used patch.object context manager instead of monkeypatch.setattr for REPO_ROOT patching to avoid module-level binding issues in pytest"
  - "Used MagicMock for subprocess.run return values to isolate from real pytest/git execution"

patterns-established:
  - "patch.object context manager pattern for module-level Path globals in agent scripts"
  - "capsys fixture for testing CLI output (recall, brief, stats)"

requirements-completed: [COV-03, COV-05]

duration: 8min
completed: 2026-04-03
---

# Phase 10 Plan 02: Agent Script Coverage Summary

**33 tests covering write_report, review_file, detect_stale_counters, detect_manifest_sync, recall, brief, stats across 4 agent scripts**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-03T23:06:45Z
- **Completed:** 2026-04-03T23:14:45Z
- **Tasks:** 2
- **Files created:** 4

## Accomplishments
- 8 tests for agent_research.py write_report() and main() entry paths
- 10 tests for agent_diff_review.py review_file() regression detection and main() flow
- 8 tests for agent_pr_creator.py detect_stale_counters, detect_manifest_sync, and main
- 7 tests for agent_learn.py recall, brief, and stats commands

## Task Commits

Each task was committed atomically:

1. **Task 1: agent_research write_report + agent_diff_review review_file/main tests** - `c41d8a8` (test)
2. **Task 2: agent_pr_creator detectors + agent_learn commands tests** - `ee2ca3e` (test)

## Files Created/Modified
- `tests/scripts/test_agent_research_write_report.py` - Tests for write_report() file creation/content and main() entry paths
- `tests/scripts/test_agent_diff_review_main.py` - Tests for review_file() regression detection and main() PASS/FAIL/summary
- `tests/scripts/test_agent_pr_creator_detectors.py` - Tests for detect_stale_counters, detect_manifest_sync, main
- `tests/scripts/test_agent_learn_commands.py` - Tests for recall, brief, stats commands with KB fixtures

## Decisions Made
- Used `patch.object` as context manager (not `monkeypatch.setattr`) for `REPO_ROOT` in agent_diff_review tests due to module-level global binding behavior in pytest
- Used `MagicMock` for `subprocess.run` return values to fully isolate from real pytest/git

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed trace_root_hash test needing old_source and patch.object**
- **Found during:** Task 1 (test_agent_diff_review_main.py)
- **Issue:** review_file() returns early when get_old_source returns None (line 107), and monkeypatch.setattr for REPO_ROOT didn't propagate correctly in pytest for this module
- **Fix:** Provided valid old_source to avoid early return, used patch.object context manager instead of monkeypatch
- **Files modified:** tests/scripts/test_agent_diff_review_main.py
- **Verification:** Test passes consistently
- **Committed in:** c41d8a8 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor test implementation adjustment. No scope change.

## Issues Encountered
None beyond the deviation noted above.

## Known Stubs
None - all tests wire real functions with mocked I/O.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 target scripts now have comprehensive branch coverage
- Combined with Plan 01, coverage gap addressed per COV-03 and COV-05

---
*Phase: 10-coverage-hardening*
*Completed: 2026-04-03*
