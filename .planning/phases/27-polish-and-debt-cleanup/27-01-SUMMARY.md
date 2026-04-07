---
phase: 27-polish-and-debt-cleanup
plan: 01
subsystem: tooling
tags: [receipt, demo, manifest, verification, proof-library]

# Dependency graph
requires:
  - phase: 24-client-demo-flow
    provides: mg_demo.py receipt generation and bundle verification
  - phase: 23-real-verification
    provides: proof_library with 21 real bundles and index.json
provides:
  - Fixed receipt reproduce commands (two-step: unzip then verify --pack on directory)
  - Domain-specific metrics in receipt Result field (from *_output.json)
  - Correct system_manifest.json ratio (21 real, 1.0)
  - Fixed _update_manifest ratio formula in mg_claim_builder.py
  - Test isolation fix preventing tests from overwriting real system_manifest.json
affects: [client-demo, proof-library, system-manifest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Load *_output.json from bundle ZIP for domain metrics alongside evidence.json"
    - "Monkeypatch REPO_ROOT in test fixtures to prevent side-effects on real files"

key-files:
  created: []
  modified:
    - scripts/mg_demo.py
    - system_manifest.json
    - scripts/mg_claim_builder.py
    - tests/scripts/test_mg_claim_builder.py

key-decisions:
  - "Fixed _update_manifest ratio formula to use real/total_in_index instead of real/(real+hardcoded_20) -- root cause of ratio regression"
  - "Monkeypatched REPO_ROOT in test_mg_claim_builder fixture to prevent test side-effects on real system_manifest.json"

patterns-established:
  - "Test fixtures must isolate ALL write paths (not just data paths but also manifest paths)"

requirements-completed: []

# Metrics
duration: 7min
completed: 2026-04-07
---

# Phase 27 Plan 01: Polish and Debt Cleanup Summary

**Fixed receipt reproduce commands (two-step unzip+verify), domain metric extraction from *_output.json, and system_manifest.json ratio regression (21 real, 1.0)**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-07T23:32:38Z
- **Completed:** 2026-04-07T23:39:48Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Receipt "How to Reproduce" now shows two-step: `unzip <path> -d <dir>/` then `python scripts/mg.py verify --pack <dir>/`
- Receipt Result field shows domain-specific metrics (e.g. `rel_err = 0.00e+00`) instead of "See bundle for details"
- system_manifest.json corrected: real_verifications_count=21, real_to_synthetic_ratio=1.0
- Root cause of ratio regression fixed in mg_claim_builder.py `_update_manifest`
- All 5 verification gates pass: steward_audit, pytest (2078), deep_verify (13/13), check_stale_docs, agent_diff_review

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix mg_demo.py -- reproduce commands and domain metric extraction** - `002342d` (feat)
2. **Task 2: Fix system_manifest.json ratio and run all 5 gates** - `2b89b5e` (fix)

## Files Created/Modified
- `scripts/mg_demo.py` - Fixed reproduce commands to show extraction step; load *_output.json for domain metrics in receipt Result field
- `system_manifest.json` - Corrected real_verifications_count=21 and real_to_synthetic_ratio=1.0
- `scripts/mg_claim_builder.py` - Fixed _update_manifest ratio formula (real/total instead of real/(real+20))
- `tests/scripts/test_mg_claim_builder.py` - Monkeypatched REPO_ROOT to prevent test side-effects on real manifest

## Decisions Made
- Fixed `_update_manifest` ratio formula as root cause fix (Rule 1 - bug) rather than just setting the manifest value, which would regress on next `build_claim` call
- Monkeypatched REPO_ROOT in test fixture to prevent any test from overwriting the real system_manifest.json

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _update_manifest ratio formula in mg_claim_builder.py**
- **Found during:** Task 2 (system_manifest.json ratio fix)
- **Issue:** `_update_manifest()` used `real_count / (real_count + 20)` with hardcoded synthetic count of 20, computing 21/41=0.5122 instead of 21/21=1.0. This was the root cause of the ratio regression.
- **Fix:** Changed formula to `real_count / len(entries)` using actual index.json entry count
- **Files modified:** scripts/mg_claim_builder.py
- **Verification:** pytest 2078 passed, manifest values stable after all gates
- **Committed in:** 2b89b5e (Task 2 commit)

**2. [Rule 3 - Blocking] Fixed test isolation in test_mg_claim_builder.py**
- **Found during:** Task 2 (system_manifest.json ratio fix)
- **Issue:** Test fixture monkeypatched INDEX_PATH but not REPO_ROOT, so `_update_manifest()` wrote to the real system_manifest.json during tests, reverting ratio values
- **Fix:** Added `monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)` and created temp manifest
- **Files modified:** tests/scripts/test_mg_claim_builder.py
- **Verification:** Manifest values stable after full pytest run
- **Committed in:** 2b89b5e (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes necessary for correctness. Without them, system_manifest.json would revert on every test run. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 tech debt items from v3.0.0-MILESTONE-AUDIT.md are resolved
- All 5 verification gates pass
- Ready for v3.0.0 milestone closure

---
*Phase: 27-polish-and-debt-cleanup*
*Completed: 2026-04-07*
