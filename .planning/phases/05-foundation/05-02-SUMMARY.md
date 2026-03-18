---
phase: 05-foundation
plan: 02
subsystem: testing
tags: [step-chain, semantic-verification, adversarial-proofs, mg.py]

# Dependency graph
requires:
  - phase: 04-adversarial-proofs-and-polish
    provides: "Existing _verify_semantic with step chain hash validation"
provides:
  - "Step ordering and count validation in _verify_semantic (rejects misordered, duplicate, extra, fewer steps)"
  - "4 new ordering invariant tests in test_cert03"
affects: [07-flagship-proofs, CERT-11]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Step count == 4 enforcement", "Step number sequence [1,2,3,4] enforcement"]

key-files:
  created: []
  modified:
    - scripts/mg.py
    - tests/steward/test_cert03_step_chain_verify.py

key-decisions:
  - "Step count and ordering checks inserted between non-empty list check and per-step hash validation loop"
  - "Exact sequence [1,2,3,4] check catches both misordering and duplicate step numbers in one comparison"

patterns-established:
  - "Step chain structural validation: count then order then hash format then root match"

requirements-completed: [CHAIN-02, CHAIN-03, CHAIN-04]

# Metrics
duration: 2min
completed: 2026-03-18
---

# Phase 5 Plan 02: Step Ordering Validation Summary

**Step ordering and count validation added to _verify_semantic, with 4 adversarial tests proving misordered, duplicate, extra, and fewer step traces are rejected**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T04:15:15Z
- **Completed:** 2026-03-18T04:17:29Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added step count validation (must be exactly 4) to _verify_semantic in scripts/mg.py
- Added step ordering validation (must be [1,2,3,4]) catching misordering and duplicates
- 4 new tests prove all attack vectors: wrong order (1,3,2,4), duplicates (1,2,2,4), extra steps (5), fewer steps (3)
- All 10 cert03 tests pass, full test suite has zero regressions from these changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Add step ordering and count validation to _verify_semantic** - `aae0328` (feat)
2. **Task 2: Add ordering invariant tests to test_cert03** - `247be7a` (test)

## Files Created/Modified
- `scripts/mg.py` - Added ~10 lines of step count and ordering validation in _verify_semantic
- `tests/steward/test_cert03_step_chain_verify.py` - Added _VALID_HASH_E constant and 4 new test methods

## Decisions Made
- Step count and ordering checks placed between non-empty list check and per-step hash validation loop, maintaining the logical flow: exists -> count -> order -> format -> root match
- Used `step_numbers != [1, 2, 3, 4]` comparison which simultaneously catches misordering and duplicate step numbers

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Step chain structural validation complete, prerequisite for CERT-11 coordinated attack proofs in Phase 7
- _verify_semantic now validates: non-empty list, exactly 4 steps, sequential [1,2,3,4] ordering, valid hex hashes, root hash match

---
*Phase: 05-foundation*
*Completed: 2026-03-18*
