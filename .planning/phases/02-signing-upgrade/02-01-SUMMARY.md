---
phase: 02-signing-upgrade
plan: 01
subsystem: signing
tags: [ed25519, hmac, bundle-signing, dual-algorithm, downgrade-prevention]

requires:
  - phase: 01-ed25519-foundation
    provides: "Pure-Python Ed25519 sign/verify/generate_keypair via scripts/mg_ed25519.py"
provides:
  - "Dual-algorithm bundle signing dispatch in mg_sign.py (HMAC + Ed25519)"
  - "_detect_algorithm() for key version field routing"
  - "Ed25519 bundle signing with 128-char hex signatures"
  - "Ed25519 verification using public-key-only .pub.json files"
  - "Downgrade attack prevention (algorithm mismatch rejection)"
  - "15 new signing tests in test_signing_upgrade.py"
affects: [02-signing-upgrade, mg-cli-integration, bundle-verification]

tech-stack:
  added: []
  patterns:
    - "Lazy import of mg_ed25519 inside Ed25519 branches (avoid loading crypto math for HMAC-only use)"
    - "Key version field as single algorithm discriminator (no CLI flags)"
    - "Downgrade attack check before any cryptographic operation"

key-files:
  created:
    - tests/steward/test_signing_upgrade.py
  modified:
    - scripts/mg_sign.py

key-decisions:
  - "Ed25519 imports are lazy (inside function bodies) to avoid loading Ed25519 math when only HMAC is used"
  - "Downgrade attack check runs before fingerprint check in verification -- fail fast on algorithm mismatch"
  - "SIGNATURE_VERSION constant kept as hmac-sha256-v1 for backward compatibility; Ed25519 uses literal ed25519-v1"

patterns-established:
  - "Algorithm dispatch via _detect_algorithm(key_data) using version field"
  - "Dual-path verification: HMAC uses hmac.compare_digest, Ed25519 uses mg_ed25519.verify"

requirements-completed: [SIGN-03, SIGN-04, SIGN-06, SIGN-07, SIGN-08]

duration: 2min
completed: 2026-03-18
---

# Phase 2 Plan 1: Signing Upgrade Summary

**Dual-algorithm bundle signing with Ed25519 dispatch, public-key verification, and downgrade attack prevention in mg_sign.py**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T00:18:55Z
- **Completed:** 2026-03-18T00:21:37Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Ed25519 keys can sign bundles producing bundle_signature.json with version "ed25519-v1" and 128-char hex signatures
- Ed25519-signed bundles verify with both private key files and public-only .pub.json files
- Algorithm mismatch between key type and bundle signature version is rejected (downgrade attack prevention)
- All 11 existing HMAC tests pass unmodified (backward compatibility confirmed)
- Full test suite: 357 passed, 2 skipped (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test scaffold for Ed25519 signing upgrade** - `f744dce` (test) -- TDD RED phase, 15 tests across 4 classes
2. **Task 2: Implement dual-algorithm dispatch in mg_sign.py** - `22e53a1` (feat) -- TDD GREEN phase, all 28 signing tests pass

## Files Created/Modified
- `tests/steward/test_signing_upgrade.py` - 15 tests: algorithm dispatch, Ed25519 sign/verify, downgrade attacks, dual-format key loading
- `scripts/mg_sign.py` - Added _detect_algorithm, _compute_ed25519_signature, updated load_key/sign_bundle/verify_bundle_signature for dual-algorithm support

## Decisions Made
- Ed25519 imports are lazy (inside function bodies) to avoid loading Ed25519 math when only HMAC is used
- Downgrade attack check runs before fingerprint check -- fail fast on algorithm mismatch
- SIGNATURE_VERSION constant kept as "hmac-sha256-v1" for backward compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Dual-algorithm signing is complete; mg.py CLI integration (Plan 02) can now add --type flag to keygen
- Ed25519 key files from Phase 1 work seamlessly with the upgraded mg_sign.py
- Public-key-only verification enables third-party auditor workflow

---
*Phase: 02-signing-upgrade*
*Completed: 2026-03-18*
