---
phase: 05-foundation
plan: 03
subsystem: testing
tags: [runner, error-paths, governance, drift-detection, meta-tests]

requires:
  - phase: 05-foundation
    provides: "existing runner.py dispatch, steward_audit extractors, system_manifest.json"
provides:
  - "Runner error path test coverage (unknown kind, bad payload, mid-computation exception, _hash_step defense)"
  - "Self-maintaining governance meta-tests for documentation drift detection"
  - "Counter consistency validation across 6 documentation files"
affects: [06-layer-hardening, 07-flagship-proofs, 08-counters]

tech-stack:
  added: []
  patterns: ["relational assertions against manifest (no hardcoded counts)", "custom YAML parser without PyYAML dependency", "prefer_authoritative pattern for index.html claim extraction"]

key-files:
  created:
    - tests/steward/test_runner_error_paths.py
    - tests/steward/test_stew08_documentation_drift.py
  modified: []

key-decisions:
  - "Used custom YAML parser for known_faults.yaml instead of PyYAML (not installed)"
  - "Added prefer_authoritative flag to claim count extraction to handle index.html partial counts (e.g. 'Test 5 claims')"
  - "Fixed _extract_claim_index_claim_ids call to pass required path argument"

patterns-established:
  - "Governance meta-tests use relational assertions against system_manifest.json as single source of truth"
  - "Custom YAML parsing for simple structures avoids adding dependencies"

requirements-completed: [ERR-01, ERR-02, ERR-03, GOV-01, GOV-02, GOV-03]

duration: 4min
completed: 2026-03-18
---

# Phase 5 Plan 3: Runner Error Paths and Governance Meta-Tests Summary

**Runner error path tests (10 tests) and self-maintaining governance drift detection (12 tests) with zero hardcoded counts**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T04:15:20Z
- **Completed:** 2026-03-18T04:19:01Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Runner error paths cover unknown JOB_KIND, None/empty/wrong-type payload, mid-computation exception, and _hash_step non-serializable defense
- Governance meta-tests validate claim index vs runner dispatch (set equality), known_faults.yaml references, and counter consistency across 6 documentation files
- All 22 new tests use relational assertions -- zero hardcoded counts means they self-maintain as claims are added
- index.html highest-drift-risk file specifically validated with authoritative pattern matching

## Task Commits

Each task was committed atomically:

1. **Task 1: Runner error path tests and _hash_step defense** - `1aae6b9` (test)
2. **Task 2: Governance meta-tests for documentation drift** - `2dada9c` (test)

_Note: Tests verify existing code behavior -- no implementation changes needed_

## Files Created/Modified
- `tests/steward/test_runner_error_paths.py` - 10 tests: unknown kind, bad payload, mid-computation exception, _hash_step non-serializable defense
- `tests/steward/test_stew08_documentation_drift.py` - 12 tests: claim index drift, known_faults drift, counter consistency across README/AGENTS/llms.txt/CONTEXT_SNAPSHOT/index.html

## Decisions Made
- Used custom YAML parser for known_faults.yaml because PyYAML is not installed (avoids adding dependency)
- Added `prefer_authoritative=True` flag for index.html claim extraction to avoid matching partial counts like "Test 5 claims in browser"
- Fixed `_extract_claim_index_claim_ids` call to pass required `path` argument (function signature differs from plan's interface spec)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed _extract_claim_index_claim_ids call signature**
- **Found during:** Task 2
- **Issue:** Plan assumed `_extract_claim_index_claim_ids()` takes no args, but actual signature requires `path` parameter
- **Fix:** Added path argument: `_extract_claim_index_claim_ids(_ROOT / "reports" / "scientific_claim_index.md")`
- **Files modified:** tests/steward/test_stew08_documentation_drift.py
- **Committed in:** 2dada9c

**2. [Rule 1 - Bug] Fixed index.html claim count extraction matching partial count**
- **Found during:** Task 2
- **Issue:** Regex `(\d+)\s+claims?` matched "Test 5 claims in browser" before "All 14 claims"
- **Fix:** Added `prefer_authoritative` flag that prioritizes "all N claims" pattern
- **Files modified:** tests/steward/test_stew08_documentation_drift.py
- **Committed in:** 2dada9c

**3. [Rule 3 - Blocking] Replaced PyYAML with custom YAML parser**
- **Found during:** Task 2
- **Issue:** Plan used `import yaml` but PyYAML is not installed
- **Fix:** Wrote minimal `_parse_known_faults_yaml()` regex-based parser for the known structure
- **Files modified:** tests/steward/test_stew08_documentation_drift.py
- **Committed in:** 2dada9c

---

**Total deviations:** 3 auto-fixed (2 bug fixes, 1 blocking dependency)
**Impact on plan:** All fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Governance meta-tests are now active and will catch documentation drift during Phases 6-8
- Runner error paths confirm graceful failure handling for all edge cases
- Full test suite: 463 passed, 2 skipped, zero regressions

---
*Phase: 05-foundation*
*Completed: 2026-03-18*
