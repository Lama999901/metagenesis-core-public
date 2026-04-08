---
phase: 23-real-verification
plan: 03
subsystem: testing
tags: [batch-runner-tests, bundle-verification, real-ratio, idempotency, proof-library]

# Dependency graph
requires:
  - phase: 23-02
    provides: mg_verify_all_real.py batch runner, 20 signed bundles, proof_library/index.json with 21 entries
provides:
  - tests/scripts/test_mg_verify_all_real.py with 8 tests covering registry, bundles, verification, ratio, idempotency
  - Confirmed all 20 bundles pass mg.py verify --pack (REAL-05)
  - Confirmed real_to_synthetic_ratio = 51.2% (>= 50% target)
  - Confirmed agent_evolution.py check #21 PASS
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [zip extraction for bundle verification testing, ratio computation from index.json as authoritative source]

key-files:
  created:
    - tests/scripts/test_mg_verify_all_real.py
  modified:
    - scripts/mg_verify_all_real.py

key-decisions:
  - "Compute ratio from index.json directly instead of system_manifest.json because other test suites corrupt manifest via build_claim() side effects"
  - "Guard sys.stdout UTF-8 wrapping behind __name__ == __main__ to avoid breaking pytest capture mechanism"

patterns-established:
  - "Bundle verification test pattern: extract ZIP to tmpdir then mg.py verify --pack tmpdir"
  - "Authoritative data source: index.json for ratio, not system_manifest.json (which has write side effects from test suites)"

requirements-completed: [REAL-05]

# Metrics
duration: 5min
completed: 2026-04-07
---

# Phase 23 Plan 03: Batch Runner Tests and Bundle Verification Summary

**8 tests validating all 20 bundles pass mg.py verify --pack, real_ratio at 51.2%, and batch runner idempotency**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-07T05:32:18Z
- **Completed:** 2026-04-07T05:37:00Z
- **Tasks:** 2/2
- **Files modified:** 2

## Accomplishments
- Created test_mg_verify_all_real.py with 8 tests covering: registry structure (20 claims), _already_verified logic (positive/negative/synthetic), bundle existence (20 bundles), bundle verification via mg.py verify --pack (20 PASS), index.json completeness (21 non-synthetic entries across 8 domains), real ratio (51.2% >= 50%), and idempotency
- All 20 bundles independently verified through mg.py verify --pack (REAL-05 satisfied)
- Confirmed agent_evolution.py check #21 (real_ratio) PASS with ratio=0.5122
- Total test suite: 2071 passed, 0 failed (up from 2063)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test_mg_verify_all_real.py with bundle verification tests** - `43a1c2b` (test)
2. **Task 2: Confirm check #21 PASS, fix ratio test resilience** - `fb80755` (fix)

## Files Created/Modified
- `tests/scripts/test_mg_verify_all_real.py` - 8 tests for batch runner and bundle verification
- `scripts/mg_verify_all_real.py` - Guarded sys.stdout wrapping behind __name__ == "__main__"

## Decisions Made
- Computed ratio from index.json instead of system_manifest.json because other test suites (test_mg_claim_builder.py) calling build_claim() trigger _update_manifest() which overwrites system_manifest.json with stale values during pytest collection
- Guarded sys.stdout/stderr UTF-8 wrapping in mg_verify_all_real.py behind __name__ == "__main__" check to prevent breaking pytest's capture mechanism on import

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Guarded sys.stdout wrapping to fix pytest import crash**
- **Found during:** Task 1
- **Issue:** mg_verify_all_real.py wraps sys.stdout/stderr with TextIOWrapper at module level (for Windows UTF-8). When imported by pytest, this closes pytest's capture file handles, causing ValueError on test collection.
- **Fix:** Added `__name__ == "__main__"` guard to the wrapping code
- **Files modified:** scripts/mg_verify_all_real.py
- **Verification:** All 8 tests collect and pass
- **Committed in:** 43a1c2b (Task 1 commit)

**2. [Rule 1 - Bug] Fixed ratio test corrupted by side effects from other test suites**
- **Found during:** Task 2
- **Issue:** test_real_ratio_above_50_percent read from system_manifest.json, but test_mg_claim_builder.py tests call build_claim() which triggers _update_manifest(), resetting real_to_synthetic_ratio to 0.0476 (1/21) during the test run
- **Fix:** Changed ratio computation to read directly from proof_library/index.json (authoritative source), matching agent_evolution.py check #21 logic
- **Files modified:** tests/scripts/test_mg_verify_all_real.py
- **Verification:** Full suite 2071 passed with ratio test stable
- **Committed in:** fb80755 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for test suite to function. No scope creep.

## Issues Encountered
- system_manifest.json in working tree had reverted values (ratio=0.0476 instead of 0.5122) despite correct values in git HEAD. Restored via git checkout HEAD. Root cause: test_mg_claim_builder.py integration tests overwrite the file.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 23 complete: all 3 plans executed
- 20 real bundles verified, ratio at 51.2%, 2071 tests pass
- Ready for counter-sync phase to update documentation from 2063 to 2071

---
*Phase: 23-real-verification*
*Completed: 2026-04-07*
