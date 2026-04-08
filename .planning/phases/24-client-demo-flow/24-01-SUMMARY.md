---
phase: 24-client-demo-flow
plan: 01
subsystem: cli
tags: [demo, verification, receipt, proof-library, argparse]

# Dependency graph
requires:
  - phase: 23-real-verification
    provides: proof_library/bundles/ with 20 signed bundles and index.json
provides:
  - scripts/mg_demo.py -- single-command domain demo with interactive menu
  - demos/receipts/ directory with human-readable domain receipts
  - 7 pytest tests covering demo flow, offline operation, receipt content
affects: [25-documentation, 26-outreach]

# Tech tracking
tech-stack:
  added: []
  patterns: [short claim ID extraction from full mtr_phase, ZIP security validation]

key-files:
  created:
    - scripts/mg_demo.py
    - demos/receipts/.gitkeep
    - tests/test_mg_demo.py
  modified: []

key-decisions:
  - "Extract short claim ID from mtr_phase for proper CLAIM_DESCRIPTIONS/PHYSICAL_ANCHORS lookup"
  - "Guard UTF-8 encoding wrapper under __name__=='__main__' to avoid breaking pytest capture"
  - "ZIP member name validation before extraction (T-24-02 mitigation)"
  - "Bundle path must resolve within REPO_ROOT (T-24-01 mitigation)"

patterns-established:
  - "Domain demo pattern: load index.json, filter by domain, extract ZIP to temp, verify, generate receipt, clean up"
  - "Combined domain receipt with Summary/Claims/Result/Reproduce sections"

requirements-completed: [DEMO-01, DEMO-02, DEMO-03]

# Metrics
duration: 4min
completed: 2026-04-07
---

# Phase 24 Plan 01: Client Demo Flow Summary

**Single-command domain demo script verifying pre-built bundles through 5 cryptographic layers with human-readable receipts for all 8 domains**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-07T06:26:35Z
- **Completed:** 2026-04-07T06:30:33Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created mg_demo.py (437 lines) with interactive domain menu, --domain, and --all flags
- All 8 domains (materials, physics, ml, pharma, finance, digital_twin, systems, agent) verified with receipts
- Receipt files contain all 4 required sections: Summary, Claims Verified, Verification Result, How to Reproduce
- 7 tests covering menu display, receipt generation, offline operation, error handling, path normalization, all-domains flag
- ZIP path traversal protection and bundle path containment checks (threat model T-24-01, T-24-02)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create mg_demo.py demo script** - `cafe917` (feat)
2. **Task 2: Create tests for mg_demo.py** - `ffea7fc` (test)

## Files Created/Modified
- `scripts/mg_demo.py` - Domain demo script with interactive menu, 5-layer verification, receipt generation
- `demos/receipts/.gitkeep` - Output directory for demo receipts
- `tests/test_mg_demo.py` - 7 pytest tests for demo functionality

## Decisions Made
- Extracted short claim IDs (e.g. "MTR-1") from full mtr_phase strings (e.g. "MTR-1_materials-20260407T052827Z") by matching against known CLAIM_DESCRIPTIONS keys, ensuring proper physical anchor and description lookup in receipts
- Guarded UTF-8 encoding wrapper under `__name__ == "__main__"` to avoid breaking pytest stdout capture (same pattern as mg_verify_all_real.py)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed claim ID lookup in receipts**
- **Found during:** Task 1 (mg_demo.py creation)
- **Issue:** Evidence.json mtr_phase field contains full ID (e.g. "MTR-1_materials-20260407T052827Z") but CLAIM_DESCRIPTIONS/PHYSICAL_ANCHORS use short IDs (e.g. "MTR-1"), causing receipts to show "Tamper-evident provenance only" instead of actual physical anchors
- **Fix:** Added `_short_claim_id()` helper that matches against known claim IDs, and modified receipt evidence dict to use short ID before calling `format_receipt()`
- **Files modified:** scripts/mg_demo.py
- **Verification:** Receipt now shows "E = 70 GPa (aluminum, NIST measured)" for MTR-1
- **Committed in:** cafe917 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Fix was necessary for correct receipt content. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Demo script ready for client demonstrations
- All 8 domain receipts generated and verified
- Ready for documentation phase (25) and outreach phase (26)

---
*Phase: 24-client-demo-flow*
*Completed: 2026-04-07*
