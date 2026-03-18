---
phase: 06-layer-hardening
plan: 02
subsystem: testing
tags: [cross-claim-chain, anchor-hash, protocol-version, rollback-attack, cascade]

requires:
  - phase: 06-01
    provides: "semantic edge case hardening and threshold validation"
provides:
  - "Full 4-hop anchor chain test coverage (MTR-1->DT-FEM-01->DRIFT-01->DT-CALIB-LOOP-01)"
  - "Protocol version rollback attack detection in _verify_pack()"
  - "MINIMUM_PROTOCOL_VERSION constant in mg.py"
affects: [07-flagship-proofs, CERT-11]

tech-stack:
  added: []
  patterns: ["protocol_version integer validation in _verify_pack", "4-hop anchor chain test pattern"]

key-files:
  created:
    - tests/steward/test_manifest_rollback.py
  modified:
    - tests/steward/test_cross_claim_chain.py
    - scripts/mg.py
    - scripts/steward_submission_pack.py
    - tests/cli/test_verify_json01_report.py
    - tests/steward/test_cert_5layer_independence.py

key-decisions:
  - "protocol_version uses integer format (1) instead of string ('v1.0') per user decision"
  - "Protocol version check placed after manifest structure validation, before integrity checks"

patterns-established:
  - "4-hop chain test pattern: _run_full_chain() helper returns all 4 claim results"
  - "Pack helper _write_manifest() for building test packs with correct SHA-256 and protocol_version"

requirements-completed: [CASCADE-01, CASCADE-02, CASCADE-03, ADV-07]

duration: 6min
completed: 2026-03-18
---

# Phase 6 Plan 2: Cross-Claim Chain and Rollback Attack Summary

**Full 4-hop anchor chain (MTR-1->DT-FEM-01->DRIFT-01->DT-CALIB-LOOP-01) tested with 9 new tests plus protocol_version rollback attack detection with 5 tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-18T05:30:31Z
- **Completed:** 2026-03-18T05:36:31Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Full 4-hop cross-claim anchor chain tested end-to-end (CASCADE-01/02/03)
- Upstream tamper propagation proven through all 4 hops with hash uniqueness
- _verify_chain() detection mechanism tested with tampered pack directories
- Protocol version rollback attack rejected: missing, non-integer, zero, negative all fail
- MINIMUM_PROTOCOL_VERSION=1 constant enforced in _verify_pack()

## Task Commits

Each task was committed atomically:

1. **Task 1: Full 4-hop anchor chain tests** - `0fe31ee` (test)
2. **Task 2: Manifest protocol_version rollback attack** - `1183ae9` (feat)

_Note: TDD tasks - tests written first (RED confirmed for Task 2), then production code (GREEN)._

## Files Created/Modified
- `tests/steward/test_cross_claim_chain.py` - Added TestFullAnchorChain class with 9 tests (15 total)
- `tests/steward/test_manifest_rollback.py` - New TestManifestRollback class with 5 tests
- `scripts/mg.py` - Added MINIMUM_PROTOCOL_VERSION and protocol_version validation in _verify_pack()
- `scripts/steward_submission_pack.py` - Changed protocol_version from "v1.0" to integer 1
- `tests/cli/test_verify_json01_report.py` - Updated to integer protocol_version
- `tests/steward/test_cert_5layer_independence.py` - Added protocol_version to test manifests

## Decisions Made
- protocol_version uses integer format (1) instead of string ("v1.0") per user decision
- Protocol version check placed after manifest structure validation, before integrity checks

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing tests to use integer protocol_version**
- **Found during:** Task 2 (protocol_version validation)
- **Issue:** test_verify_json01_report.py and test_cert_5layer_independence.py built manifests with string protocol_version "v1.0" or no protocol_version, which now fails validation
- **Fix:** Updated to integer protocol_version=1 in both test files
- **Files modified:** tests/cli/test_verify_json01_report.py, tests/steward/test_cert_5layer_independence.py
- **Verification:** Full test suite passes (496 passed, 2 skipped)
- **Committed in:** 1183ae9 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Necessary regression fix from protocol_version enforcement. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Layer hardening phase complete (06-01 semantic + 06-02 cascade/rollback)
- Full 4-hop anchor chain proven tamper-evident
- Protocol version rollback attack vector closed
- Ready for Phase 7 flagship proofs (CERT-11 attack-to-layer attribution)

---
*Phase: 06-layer-hardening*
*Completed: 2026-03-18*
