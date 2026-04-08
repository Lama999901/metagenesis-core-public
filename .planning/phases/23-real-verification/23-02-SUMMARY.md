---
phase: 23-real-verification
plan: 02
subsystem: verification
tags: [batch-runner, proof-library, bundles, real-ratio, idempotent]

# Dependency graph
requires:
  - phase: 23-01
    provides: 20 real input data files + run_single_claim.py dispatcher
provides:
  - scripts/mg_verify_all_real.py batch runner for all 20 claims
  - 20 signed verification bundles in proof_library/bundles/
  - proof_library/index.json with 21 non-synthetic entries
  - system_manifest.json real_to_synthetic_ratio = 0.5122
affects: [23-03-PLAN (tests for batch runner)]

# Tech tracking
tech-stack:
  added: []
  patterns: [idempotent batch execution with index.json dedup, pack_manifest list-of-dicts format]

key-files:
  created:
    - scripts/mg_verify_all_real.py
    - proof_library/bundles/MTR-1_materials_20260407T052827Z.zip
    - proof_library/bundles/PHYS-01_physics_20260407T052828Z.zip
    - proof_library/real_data/.gitignore
  modified:
    - scripts/mg_claim_builder.py
    - proof_library/index.json
    - system_manifest.json

key-decisions:
  - "Fixed mg_claim_builder.py pack_manifest format to use list-of-dicts files array and protocol_version field matching mg.py _verify_pack expectations"
  - "Intermediate *_output.json files gitignored as runtime artifacts"

patterns-established:
  - "Batch runner pattern: CLAIM_REGISTRY list + idempotency via _already_verified() + build_claim() loop"
  - "Bundle verification: extract ZIP to tmpdir then mg.py verify --pack tmpdir"

requirements-completed: [REAL-01, REAL-02, REAL-04, REAL-03]

# Metrics
duration: 5min
completed: 2026-04-07
---

# Phase 23 Plan 02: Batch Runner and 20 Signed Bundles Summary

**Batch runner executing all 20 claims with real data, producing 21 verified bundles pushing real_ratio from 4.8% to 51.2%**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-07T05:25:11Z
- **Completed:** 2026-04-07T05:30:19Z
- **Tasks:** 2/2
- **Files modified:** 25

## Accomplishments
- Created mg_verify_all_real.py (271 lines) with CLAIM_REGISTRY of all 20 active claims, idempotency check, --dry-run flag, and failure-resilient loop
- Ran all 20 claims successfully through build_claim(is_synthetic=False), producing 20 signed bundles in proof_library/bundles/
- All 20 bundles pass mg.py verify --pack (Layer 1 SHA-256 integrity verification)
- real_to_synthetic_ratio jumped from 0.0476 (1 real) to 0.5122 (21 real / 41 total)
- Idempotency verified: re-run skips all 20 claims

## Task Commits

Each task was committed atomically:

1. **Task 1: Create mg_verify_all_real.py batch runner** - `6691679` (feat)
2. **Task 2: Execute batch runner to produce 20 signed bundles** - `50d28ea` (feat)

## Files Created/Modified
- `scripts/mg_verify_all_real.py` - Batch runner with 20-claim registry, idempotency, --dry-run
- `scripts/mg_claim_builder.py` - Fixed pack_manifest format (protocol_version + list-of-dicts files)
- `proof_library/bundles/*.zip` - 20 new signed bundles (MTR-1 through AGENT-DRIFT-01)
- `proof_library/index.json` - 21 non-synthetic entries (1 baseline + 20 claims)
- `system_manifest.json` - real_to_synthetic_ratio = 0.5122, real_verifications_count = 21
- `proof_library/real_data/.gitignore` - Ignore intermediate *_output.json files

## Decisions Made
- Fixed mg_claim_builder.py pack_manifest to match mg.py verify expectations (was blocking all bundle verification)
- Added .gitignore for intermediate output JSONs rather than committing them

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed mg_claim_builder.py pack_manifest format incompatible with mg.py verify**
- **Found during:** Task 2 (bundle verification step)
- **Issue:** mg_claim_builder.py wrote pack_manifest with `"version": 1` and `files` as a flat dict `{relpath: sha256}`, but mg.py _verify_pack expects `"protocol_version": 1` (integer) and `files` as a list of dicts `[{"relpath": ..., "sha256": ...}]`. Root hash computation also differed.
- **Fix:** Changed pack_manifest to include `protocol_version: 1`, converted files to list-of-dicts format, and aligned root_hash computation with mg.py's `"\n".join(f"{e['relpath']}:{e['sha256']}")` pattern
- **Files modified:** scripts/mg_claim_builder.py
- **Verification:** All 20 bundles pass mg.py verify --pack; all 31 existing mg_claim_builder tests pass
- **Committed in:** 50d28ea (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix -- without it, no bundle would pass mg.py verify --pack. No scope creep.

## Issues Encountered
None beyond the pack_manifest format bug documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 20 bundles ready for test coverage (Plan 03)
- mg_verify_all_real.py can be tested for idempotency and correctness
- Pack_manifest format now compatible with mg.py verify --pack

---
*Phase: 23-real-verification*
*Completed: 2026-04-07*
