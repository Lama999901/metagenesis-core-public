---
phase: "15"
plan: "01"
subsystem: "protocol-self-audit"
tags: [self-audit, integrity, ed25519, recursive-verification]
dependency-graph:
  requires: [mg_ed25519.py, agent_evolution.py]
  provides: [mg_self_audit.py, core_integrity.json, check_self_audit]
  affects: [agent_evolution.py]
tech-stack:
  added: []
  patterns: [Ed25519-signed-baseline, CRLF-canonicalized-hashing]
key-files:
  created:
    - scripts/mg_self_audit.py
    - tests/test_mg_self_audit.py
  modified:
    - scripts/agent_evolution.py
decisions:
  - Used CRLF canonicalization (replace CRLF with LF before hashing) for cross-platform determinism
  - Reuses existing mg_ed25519.py infrastructure for signing rather than creating new key management
  - Missing baseline is advisory (exit 0) to support fresh clones without --init
metrics:
  duration: "~8 min"
  completed: "2026-04-04"
  tasks_completed: 3
  tasks_total: 3
  tests_added: 21
---

# Phase 15 Plan 01: Protocol Self-Audit Summary

SHA-256 recursive integrity verifier for 8 core scripts, Ed25519-signed baseline, with Check #20 (Recursive Inquisitor) in agent_evolution.py and 21 tests.

## What Was Built

### scripts/mg_self_audit.py (SELF-01 through SELF-04)
- Hashes 8 core scripts (mg.py, steward_audit.py, agent_evolution.py, check_stale_docs.py, mg_ed25519.py, mg_sign.py, mg_client.py, agent_pilot.py) using SHA-256 with CRLF canonicalization
- Signs baseline with Ed25519 using existing mg_ed25519.py key infrastructure
- Three modes: `--init` (create baseline), `--update` (re-baseline with confirmation), default (verify against baseline)
- `--json` flag for machine-readable output
- Missing baseline returns exit 0 with advisory warning (SELF-04)
- Saves to reports/core_integrity.json

### Check #20 in agent_evolution.py (SELF-05)
- New `check_self_audit()` function added as the 20th Mechanicus check
- Key: `self_audit`, label: "Recursive Inquisitor verified", code: `SELFAUDIT`
- Handles three states: PASS (integrity intact), ADVISORY (no baseline), FAIL (tampering detected)

### tests/test_mg_self_audit.py (SELF-06)
- 21 tests covering all requirements:
  - Tamper detection (modify script -> FAIL)
  - Signature validation (corrupt sig -> FAIL)
  - --update workflow (mock input for y/n/EOF)
  - Missing baseline -> advisory, exit 0
  - Missing core file -> ALERT
  - --init creates valid baseline with correct structure
  - All 8 scripts listed
  - JSON output mode (PASS and FAIL)
  - CRLF canonicalization (BUG 2 prevention)
  - Empty file and binary content edge cases
  - Invalid baseline structure detection
  - CLI integration via subprocess

## Commits

| # | Hash | Message | Files |
|---|------|---------|-------|
| 1 | f367785 | feat(15-01): add mg_self_audit.py recursive integrity verifier | scripts/mg_self_audit.py |
| 2 | 2fc3931 | feat(15-01): add Check #20 (Recursive Inquisitor) to agent_evolution.py | scripts/agent_evolution.py |
| 3 | f8ee682 | test(15-01): add 21 tests for mg_self_audit.py | tests/test_mg_self_audit.py |

## Verification Results

- `python scripts/mg_self_audit.py --init` -> baseline created with 8 scripts
- `python scripts/mg_self_audit.py` -> SELF-AUDIT PASS -- all 8 scripts verified
- `python -m pytest tests/test_mg_self_audit.py -v` -> 21 passed
- `python scripts/steward_audit.py` -> STEWARD AUDIT: PASS
- `python -m pytest tests/ -q` -> 1774 passed, 2 skipped
- Test count increased from 1753 to 1774 (+21)

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

1. **CRLF canonicalization**: Used `raw.replace(b"\r\n", b"\n")` before hashing to match the project's existing approach in `fingerprint_file()` and prevent cross-platform hash mismatches (BUG 2).
2. **Key reuse**: Leveraged existing `mg_ed25519.generate_key_files()` and `signing_key.json` pattern rather than creating a separate key management system.
3. **Advisory exit code**: Missing baseline returns exit 0 (not 1) so fresh clones can run all verification gates without manual --init step first.

## Known Stubs

None -- all functionality is fully wired.

## Self-Check: PASSED

- [x] scripts/mg_self_audit.py exists
- [x] tests/test_mg_self_audit.py exists
- [x] Commit f367785 exists
- [x] Commit 2fc3931 exists
- [x] Commit f8ee682 exists
- [x] 21 tests pass
- [x] Full suite: 1774 passed
