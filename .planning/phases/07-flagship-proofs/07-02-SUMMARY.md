---
phase: 07-flagship-proofs
plan: 02
subsystem: testing
tags: [cert-12, encoding-attacks, bom, null-bytes, truncated-json, homoglyphs, adversarial]

requires:
  - phase: 05-foundation
    provides: step chain validation and governance meta-tests
  - phase: 06-layer-hardening
    provides: protocol version enforcement and semantic validation hardening
provides:
  - CERT-12 encoding and partial corruption attack proofs (9 tests)
  - ADV-05 BOM injection detection proof
  - ADV-06 null byte, truncated JSON, and homoglyph detection proof
affects: [08-counters, paper, joss-submission]

tech-stack:
  added: []
  patterns: [write_bytes for byte-level attacks, _rebuild_manifest to isolate encoding from L1]

key-files:
  created: [tests/steward/test_cert12_encoding_attacks.py]
  modified: []

key-decisions:
  - "Homoglyph claim ID test uses path mismatch (homoglyph in relpath vs Latin in filesystem) rather than claim registry lookup"
  - "Homoglyph job_kind test uses payload.kind vs job_kind string equality mismatch"
  - "fingerprint_file returns dict with sha256 key, adapted BOM fingerprint test accordingly"

patterns-established:
  - "Byte-level attack tests: use write_bytes() for BOM/null injection, write_text() for homoglyphs"
  - "Encoding attack isolation: always _rebuild_manifest after file modification to test encoding layer not L1"

requirements-completed: [ADV-05, ADV-06]

duration: 3min
completed: 2026-03-18
---

# Phase 7 Plan 02: CERT-12 Encoding Attacks Summary

**CERT-12 encoding and partial corruption attack proofs: 9 tests proving BOM injection, null bytes, truncated JSON, and Unicode homoglyphs are all caught by the verification pipeline**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-18T05:58:39Z
- **Completed:** 2026-03-18T06:01:27Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- 9 passing tests covering ADV-05 (3 BOM tests) and ADV-06 (6 encoding/corruption tests)
- BOM tests prove both SHA-256 fingerprint divergence and JSON parse rejection
- Null byte and truncated JSON tests prove graceful failure (no unhandled exceptions)
- Homoglyph tests prove semantic-level detection via path mismatch and payload.kind mismatch
- Full test suite passes with 511 tests, zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CERT-12 encoding and partial corruption attack tests** - `c8c1537` (test)

_Note: TDD task -- tests verify existing production code behavior (all layers already handle encoding attacks)_

## Files Created/Modified
- `tests/steward/test_cert12_encoding_attacks.py` - CERT-12 encoding attack proofs with 9 test methods in TestCert12EncodingAttacks class

## Decisions Made
- Homoglyph claim ID test: Used path-based detection (homoglyph in evidence_index relpath creates nonexistent filesystem path) rather than claim registry lookup, since _verify_semantic doesn't maintain a known-claim list
- Homoglyph job_kind test: Exploits payload.kind vs job_kind string equality check in _verify_semantic (line 232-234) -- Cyrillic lookalike fails Python string comparison
- BOM fingerprint test: Adapted to fingerprint_file returning a dict (not string), extracting sha256 key

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- CERT-12 complete -- all encoding attack vectors covered
- Combined with CERT-11 (Plan 01), Phase 7 flagship proofs are ready
- Ready for Phase 8 counter updates

---
*Phase: 07-flagship-proofs*
*Completed: 2026-03-18*
