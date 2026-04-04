---
phase: 01-ed25519-foundation
plan: 02
subsystem: crypto
tags: [ed25519, keygen, key-management, cli, rfc-8032]

# Dependency graph
requires:
  - phase: 01-ed25519-foundation plan 01
    provides: "Ed25519 core primitives (generate_keypair, sign, verify, run_self_test)"
provides:
  - "Ed25519 key file generation (generate_key_files)"
  - "CLI keygen subcommand (cmd_keygen via argparse)"
  - "Paired key files: private key.json + public key.pub.json"
  - "Public key file safe for auditor distribution (no private material)"
affects: [02-bundle-signing-upgrade]

# Tech tracking
tech-stack:
  added: [argparse, json, pathlib]
  patterns: ["argparse subcommand CLI with backward-compatible default", "paired key file generation (private + public)"]

key-files:
  created: []
  modified:
    - scripts/mg_ed25519.py
    - tests/steward/test_ed25519.py

key-decisions:
  - "Followed locked CONTEXT.md key file format exactly -- no deviations"
  - "Default CLI behavior (no subcommand) runs self-test for backward compatibility"

patterns-established:
  - "Ed25519 key file format: {version: ed25519-v1, private_key_hex, public_key_hex, fingerprint, note}"
  - "Public key file (.pub.json) excludes private_key_hex -- safe to share"
  - "Fingerprint = SHA-256 of raw public key bytes (32 bytes)"

requirements-completed: [SIGN-02, SIGN-05]

# Metrics
duration: 2min
completed: 2026-03-17
---

# Phase 1 Plan 2: Ed25519 Keygen CLI Summary

**Ed25519 key pair generation CLI with paired private/public JSON files and 6 keygen tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-17T23:41:07Z
- **Completed:** 2026-03-17T23:43:01Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Added `generate_key_files()` producing paired key.json (private+public) and key.pub.json (public only)
- Added `cmd_keygen` CLI subcommand with argparse (`python scripts/mg_ed25519.py keygen --out key.json`)
- Public key file explicitly excludes `private_key_hex` -- safe to share with third-party auditors
- Backward compatible: running without subcommand still executes RFC 8032 self-test
- Added `TestEd25519Keygen` class with 6 tests covering format, fingerprint, no-leak, and sign/verify round-trip

## Task Commits

Each task was committed atomically:

1. **Task 1: Add key file generation and CLI keygen** - `4829e0b` (feat)

## Files Created/Modified
- `scripts/mg_ed25519.py` - Added generate_key_files, cmd_keygen, argparse CLI with keygen/test subcommands
- `tests/steward/test_ed25519.py` - Added TestEd25519Keygen class with 6 tests

## Decisions Made
- Followed locked CONTEXT.md decisions exactly -- key file format, CLI structure, public key separation
- Default behavior (no subcommand) runs self-test for backward compatibility with Plan 01

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Ed25519 foundation complete: core primitives (Plan 01) + key management (Plan 02)
- Ready for Phase 2: Bundle Signing Upgrade (mg_sign.py integration)
- `generate_key_files()` and `generate_keypair()` are the public API for Phase 2 import

---
*Phase: 01-ed25519-foundation*
*Completed: 2026-03-17*
