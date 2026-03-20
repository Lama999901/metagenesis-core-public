---
phase: quick-260319-nwt
plan: 01
subsystem: agent-drift-claim
tags: [claim-15, agent-drift, v0.6.0, counter-sync]
dependency_graph:
  requires: []
  provides: [AGENT-DRIFT-01-claim, v0.6.0-counters]
  affects: [runner.py, scientific_claim_index.md, canonical_state.md, system_manifest.json]
tech_stack:
  added: []
  patterns: [weighted-composite-drift, 4-step-chain]
key_files:
  created:
    - backend/progress/agent_drift_monitor.py
    - tests/agent/__init__.py
    - tests/agent/test_agent_drift01.py
  modified:
    - backend/progress/runner.py
    - reports/scientific_claim_index.md
    - reports/canonical_state.md
    - system_manifest.json
    - index.html
    - README.md
    - CLAUDE.md
    - AGENTS.md
    - CONTEXT_SNAPSHOT.md
    - llms.txt
    - CONTRIBUTING.md
    - paper.md
    - CITATION.cff
    - CURSOR_MASTER_PROMPT_v2_3.md
    - ppa/README_PPA.md
    - reports/known_faults.yaml
    - scripts/deep_verify.py
    - scripts/check_stale_docs.py
    - docs/ARCHITECTURE.md
    - docs/ROADMAP.md
    - docs/HOW_TO_ADD_CLAIM.md
    - docs/REAL_DATA_GUIDE.md
    - docs/USE_CASES.md
decisions:
  - "Test count uses 'passed' convention (532) not 'collected' (534) -- 2 tests are skipped"
  - "AGENT-DRIFT-01 added to SCOPE_001 affected_claims (no physical anchor)"
metrics:
  duration: 12min
  completed: 2026-03-20
---

# Quick Task 260319-nwt: Claim #15 AGENT-DRIFT-01 + v0.6.0 Counter Sync

Weighted composite drift monitor for AI agent quality with 4-step cryptographic chain, 6 tests, and full counter sync across 20+ files to v0.6.0.

## Tasks Completed

### Task 1: Implement AGENT-DRIFT-01 claim + register (Steps 1-4)

- Created `backend/progress/agent_drift_monitor.py` with:
  - `compute_agent_drift()`: weighted composite drift across 4 metrics (tests_per_phase, pass_rate, regressions, verifier_iterations)
  - `run_agent_drift_monitor()`: full claim with 4-step cryptographic chain (init_params -> compute -> metrics -> threshold_check)
  - Default baseline: tests_per_phase=47, pass_rate=1.0, regressions=0, verifier_iterations=1.2
  - Default weights: 0.3/0.3/0.2/0.2, threshold 20%
  - Special handling for zero-baseline regressions (denominator becomes 1e-9)
- Added dispatch block in `runner.py` before registered list
- Registered in `scientific_claim_index.md` with full V&V table
- Added to `canonical_state.md` claims list
- **Commit:** 3ea8476

### Task 2: Create 6 tests for AGENT-DRIFT-01

- Created `tests/agent/__init__.py` and `tests/agent/test_agent_drift01.py`
- 6 tests: test_pass_no_drift, test_fail_high_drift, test_determinism, test_step_chain_tamper_detection, test_semantic_stripping, test_boundary_exactly_20pct
- Boundary test uses custom baseline (regressions=5) to avoid zero-denominator edge case
- All 6 tests pass
- **Commit:** d0792a6

### Task 3: Counter sync 14->15 claims, 526->532 tests, v0.5.0->v0.6.0

- Updated counters across 20+ files including index.html (multiple element patterns), README.md, CLAUDE.md, AGENTS.md, CONTEXT_SNAPSHOT.md, llms.txt, system_manifest.json, CONTRIBUTING.md, paper.md, CITATION.cff, CURSOR_MASTER_PROMPT_v2_3.md, ppa/README_PPA.md, known_faults.yaml, docs/*.md
- Updated `scripts/deep_verify.py`: claim_files dict, test_calls list, HTML assertion, manifest assertion
- Updated `scripts/check_stale_docs.py` CONTENT_CHECKS for new values
- **Commit:** b0ca0d5

## Verification Results

| Gate | Result |
|------|--------|
| `python scripts/steward_audit.py` | STEWARD AUDIT: PASS |
| `python -m pytest tests/ -q` | 532 passed, 2 skipped |
| `python scripts/deep_verify.py` | ALL 13 TESTS PASSED |
| `python scripts/check_stale_docs.py` | All OK |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test count convention: passed vs collected**
- **Found during:** Task 3
- **Issue:** Plan specified 526->532, but `pytest --co` showed 534 collected. The project convention uses "passed" count (526 passed, 2 skipped). 526 + 6 new = 532 passed.
- **Fix:** Used 532 (passed count) consistently, matching project convention.
- **Files modified:** All counter files

**2. [Rule 3 - Blocking] deep_verify.py hardcoded claim count and claim list**
- **Found during:** Task 3
- **Issue:** `deep_verify.py` had hardcoded `assert len(manifest["active_claims"]) == 14`, `assert ">14<" in html`, and a static claim_files dict without AGENT-DRIFT-01.
- **Fix:** Updated assertion to 15, added agent_drift_monitor to claim_files and test_calls.
- **Files modified:** scripts/deep_verify.py
- **Commit:** b0ca0d5

**3. [Rule 3 - Blocking] index.html claim counter in multiple HTML element patterns**
- **Found during:** Task 3
- **Issue:** PowerShell replace of "14 claims" only caught text patterns. The HTML had standalone "14" inside `<span class="hv">`, `<span class="tn">`, `<span class="hbproof-val ok">`, `<div class="osi-num">`, and `<span id="cn1">` elements.
- **Fix:** Targeted PowerShell replacements for each HTML pattern.
- **Files modified:** index.html
- **Commit:** b0ca0d5

## Branch

`feat/claim-15-v060` pushed to origin.
