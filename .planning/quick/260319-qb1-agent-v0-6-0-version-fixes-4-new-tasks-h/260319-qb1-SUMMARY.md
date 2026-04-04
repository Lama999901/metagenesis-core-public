---
phase: quick
plan: 260319-qb1
subsystem: agent-evolution
tags: [version-fix, coverage, tasks, handlers]
key-files:
  created:
    - tests/steward/test_mg_sign_coverage.py
    - tests/steward/test_mg_temporal_coverage.py
  modified:
    - scripts/agent_evolution.py
    - scripts/agent_research.py
    - AGENT_TASKS.md
    - reports/AGENT_REPORT_20260319.md
    - reports/WEEKLY_REPORT_20260319.md
decisions:
  - "Used HMAC key format (not Ed25519) for coverage tests since generate_key() returns HMAC"
  - "Layer 5 missing temporal file is a skip (True), not failure (False)"
metrics:
  duration: ~5min
  completed: 2026-03-19
  tasks: 3
  files: 7
---

# Quick Task 260319-qb1: Agent v0.6.0 Version Fixes + 4 New Tasks + Handlers + Execute TASK-015

**One-liner:** Updated agent_evolution.py to v0.6.0, added TASK-015 through TASK-018 with substantive handlers reading real repo files, executed TASK-015 generating 31 passing coverage tests for mg_sign.py and mg_temporal.py.

## Tasks Completed

### Task 1: Version Fix
- Changed `v0.5.0` to `v0.6.0` in `scripts/agent_evolution.py` main() print statement (line 375)
- Skipped FIX 2 (.planning/config.json is gitignored)
- Commit: `d1e0aad`

### Task 2: Add 4 New Tasks + Handlers
- Added TASK-015 through TASK-018 to AGENT_TASKS.md with PENDING status
- Added execute_task_015 through execute_task_018 handlers to agent_research.py dispatch table
- Each handler reads real repo files (coverage report, system_manifest.json, paper.md, EVOLUTION_LOG.md)
- Commit: `d058a45`

### Task 3: Execute TASK-015 + Verify
- Ran `python scripts/agent_research.py` -- executed TASK-015 successfully
- Generated test files had 9 failures due to incorrect API assumptions (Ed25519 vs HMAC format)
- Fixed test files to match actual mg_sign.py API (HMAC key format, correct field names)
- Fixed temporal test to handle Layer 5 skip behavior (missing file = True + "skipped")
- All 31 new tests now pass
- Ran `python scripts/agent_evolution.py --summary` -- 10/12 checks pass (2 pre-existing failures: test count mismatch in manifest, deep_verify test count check)
- Pushed feat/agent-v060 branch
- Commit: `cef80ee`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test assertions for HMAC key format**
- **Found during:** Task 3
- **Issue:** Generated tests assumed Ed25519 key format (algorithm, private_key, public_key fields) but generate_key() returns HMAC format (version, key_hex, fingerprint)
- **Fix:** Rewrote test_mg_sign_coverage.py with correct field names and assertions
- **Files modified:** tests/steward/test_mg_sign_coverage.py
- **Commit:** cef80ee

**2. [Rule 1 - Bug] Fixed temporal missing file test assertion**
- **Found during:** Task 3
- **Issue:** Test expected verify_temporal_commitment to return False for missing file, but Layer 5 is optional (returns True with "skipped" message)
- **Fix:** Changed assertion to expect True with "skipped" or "no temporal" in message
- **Files modified:** tests/steward/test_mg_temporal_coverage.py
- **Commit:** cef80ee

**3. [Rule 1 - Bug] Fixed tamper detection test**
- **Found during:** Task 3
- **Issue:** Original test only tampered evidence file but verify_bundle_signature checks signed_root_hash vs manifest root_hash -- evidence change without manifest rebuild doesn't trigger the right check path
- **Fix:** Changed test to tamper with manifest root_hash directly, which correctly triggers "modified after signing" detection
- **Files modified:** tests/steward/test_mg_sign_coverage.py
- **Commit:** cef80ee

## Pre-existing Issues (Not Fixed)

- agent_evolution.py --summary shows 2/12 FAIL: test count mismatch (manifest=532 vs pytest=546) and deep_verify failure. These are pre-existing and out of scope.
- Coverage report still shows 39.7% overall -- the new tests need a coverage re-run to measure impact.

## Commits

| Hash | Message |
|------|---------|
| d1e0aad | fix: update version to v0.6.0 in agent_evolution.py |
| d058a45 | feat: add TASK-015 to TASK-018 with real handlers |
| cef80ee | feat: execute TASK-015 -- coverage tests for mg_sign.py and mg_temporal.py |

## Self-Check: PASSED
- [x] tests/steward/test_mg_sign_coverage.py exists (18 tests)
- [x] tests/steward/test_mg_temporal_coverage.py exists (13 tests)
- [x] All 31 new tests pass
- [x] feat/agent-v060 branch pushed to origin
- [x] Commits d1e0aad, d058a45, cef80ee verified in git log
