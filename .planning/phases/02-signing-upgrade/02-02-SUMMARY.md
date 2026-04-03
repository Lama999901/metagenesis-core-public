---
phase: 02-signing-upgrade
plan: 02
subsystem: signing
tags: [ed25519, hmac, cli, keygen, mg.py, mg_sign.py]

# Dependency graph
requires:
  - phase: 02-signing-upgrade/01
    provides: "Dual-algorithm sign/verify in mg_sign.py (HMAC + Ed25519)"
  - phase: 01-ed25519-foundation
    provides: "Pure-Python Ed25519 implementation with generate_key_files()"
provides:
  - "mg.py sign keygen --type flag with ed25519 default"
  - "mg_sign.py keygen --type flag with hmac default"
  - "Full regression verification (357 tests, steward audit)"
affects: [03-temporal-commitment, 04-adversarial-proofs]

# Tech tracking
tech-stack:
  added: []
  patterns: ["lazy import for optional crypto modules", "dual-default CLI pattern (new tool defaults ed25519, legacy defaults hmac)"]

key-files:
  created: []
  modified:
    - scripts/mg.py
    - scripts/mg_sign.py

key-decisions:
  - "mg.py defaults to ed25519 (forward-looking), mg_sign.py defaults to hmac (backward-compatible)"
  - "Added sys.path fix in mg.py for direct CLI invocation (Rule 3 auto-fix)"

patterns-established:
  - "Dual-default pattern: new entry point (mg.py) defaults to new algorithm, legacy entry point (mg_sign.py) defaults to old algorithm"

requirements-completed: [SIGN-03, SIGN-06]

# Metrics
duration: 4min
completed: 2026-03-18
---

# Phase 02 Plan 02: CLI Keygen Integration Summary

**Ed25519/HMAC keygen via --type flag in mg.py (default ed25519) and mg_sign.py (default hmac) with full 357-test regression gate**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-18T00:24:10Z
- **Completed:** 2026-03-18T00:28:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- mg.py sign keygen now defaults to Ed25519 key generation with --type hmac fallback
- mg_sign.py keygen now supports --type ed25519 option with hmac default for backward compatibility
- Full regression gate: 357 tests passed, steward audit PASS

## Task Commits

Each task was committed atomically:

1. **Task 1: Update mg.py and mg_sign.py CLI keygen with --type flag** - `07781fd` (feat)
2. **Task 2: Full regression gate verification** - no commit (verification-only task, no code changes)

## Files Created/Modified
- `scripts/mg.py` - Added --type arg to sign keygen, dual-dispatch in _cmd_sign_keygen, sys.path fix
- `scripts/mg_sign.py` - Added --type arg to keygen parser, dual-dispatch in cmd_keygen

## Decisions Made
- mg.py defaults to ed25519 (forward-looking for v0.4.0), mg_sign.py defaults to hmac (backward-compatible) -- per research recommendation
- Added sys.path insert at module level in mg.py so `from scripts.mg_ed25519 import` works when running `python scripts/mg.py` directly (not just via pytest)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed sys.path for direct CLI invocation of mg.py**
- **Found during:** Task 1 (CLI keygen implementation)
- **Issue:** Running `python scripts/mg.py` fails with ModuleNotFoundError because Python adds `scripts/` to sys.path[0] instead of repo root. All `from scripts.X import` statements fail.
- **Fix:** Added `sys.path.insert(0, str(REPO_ROOT))` after REPO_ROOT definition in mg.py
- **Files modified:** scripts/mg.py
- **Verification:** `python scripts/mg.py sign keygen --out /tmp/test.json` produces valid ed25519 key
- **Committed in:** 07781fd (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Auto-fix necessary for CLI to function. No scope creep.

## Deferred Issues

- **deep_verify.py TEST 7 failure (pre-existing):** `system_manifest.json` has `test_count: 295` but actual count is 357. Also `deep_verify.py` asserts `"v0.2" in manifest["protocol"]` but protocol is v0.3. Both are pre-existing mismatches not caused by this plan. `deep_verify.py` is SEALED and cannot be modified.

## Issues Encountered
- Pre-existing deep_verify TEST 7 failure due to stale system_manifest.json counters and hardcoded version check in sealed deep_verify.py. Does not affect Phase 2 signing functionality.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 2 (Signing Upgrade) is complete: Ed25519 keygen, dual-algorithm sign/verify, CLI integration
- Ready for Phase 3 (Temporal Commitment) which depends on NIST Beacon integration
- Blocker for Phase 3: NIST Beacon 2.0 API operational status unverified

---
*Phase: 02-signing-upgrade*
*Completed: 2026-03-18*
