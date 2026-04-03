---
phase: quick
plan: 260331-ov3
subsystem: documentation
tags: [counter-sync, llms-txt, context-snapshot, stale-docs]
dependency_graph:
  requires: [system_manifest.json]
  provides: [llms.txt current, CONTEXT_SNAPSHOT.md current]
  affects: [AI agent context, LLM summaries]
tech_stack:
  added: []
  patterns: [counter-sync from system_manifest.json]
key_files:
  created: []
  modified: [llms.txt, CONTEXT_SNAPSHOT.md]
decisions:
  - "Added PHYS-01/02 to llms.txt claims list (plan said list was complete but it had only 18 of 20)"
  - "Added PHYS-01/02 to CONTEXT_SNAPSHOT.md claims table and updated SCOPE_001 line"
  - "Removed dead python3 snippet artifact from top of llms.txt"
metrics:
  duration: 2min
  completed: 2026-04-01
---

# Quick Task 260331-ov3: Fix Stale Counters in llms.txt and CONTEXT_SNAPSHOT.md

Counter sync to v0.8.0 / 608 tests / 20 claims / 8 domains / 8 innovations across both LLM-facing context files, plus adding missing PHYS-01/02 claims entries.

## Tasks Completed

### Task 1: Fix all stale values in llms.txt
- **Commit:** 748f3b1
- **Changes:**
  - Removed dead `python3 -c` snippet artifact (lines 1-3)
  - `MVP v0.6` -> `MVP v0.8`
  - `595 passed` -> `608 passed`
  - `Current state (2026-03-21)` -> `Current state (2026-03-31)`
  - `Claims: 18` -> `Claims: 20`
  - `Tests: 595 passing` -> `Tests: 608 passing`
  - `Domains: 7` -> `Domains: 8` (added fundamental_physics)
  - `GitHub Release: v0.6.0` -> `GitHub Release: v0.8.0`
  - `16 evolution checks` -> `18 evolution checks`
  - Added PHYS-01 and PHYS-02 to claims list (was 18, now all 20)
  - Updated SCOPE_001 to include MTR-4/5/6 and PHYS-01/02

### Task 2: Fix all stale values in CONTEXT_SNAPSHOT.md
- **Commit:** 96a8a46
- **Changes:**
  - `Updated: 2026-03-21` -> `Updated: 2026-03-31` (header + footer)
  - `595 passing` -> `608 passing`
  - `Domains | 7` -> `Domains | 8`
  - `GitHub Release | v0.6.0` -> `GitHub Release | v0.8.0`
  - Added PHYS-01 and PHYS-02 rows to claims table (was 18, now all 20)
  - Updated SCOPE_001 line to include PHYS-01/02
  - `updated to 595` -> `updated to 608` in What is next checklist

### Task 3: Run stale docs checker to confirm all files pass
- **Result:** check_stale_docs.py reports all 7 critical files CURRENT, 0 STALE
- **Result:** steward_audit.py reports STEWARD AUDIT: PASS

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Content] Added PHYS-01/02 to llms.txt claims list**
- **Found during:** Task 1
- **Issue:** Plan stated "Do NOT change the claims list (lines 32-49) -- it already correctly lists all 20 claims" but the list only had 18 entries (PHYS-01 and PHYS-02 were missing)
- **Fix:** Added PHYS-01 and PHYS-02 entries after MTR-6
- **Files modified:** llms.txt
- **Commit:** 748f3b1

**2. [Rule 2 - Missing Content] Updated SCOPE_001 in llms.txt**
- **Found during:** Task 1
- **Issue:** SCOPE_001 physical anchor line only listed "MTR-1/2/3" but MTR-4/5/6 and PHYS-01/02 also have physical anchors
- **Fix:** Updated to "MTR-1/2/3/4/5/6, PHYS-01/02"
- **Files modified:** llms.txt
- **Commit:** 748f3b1

## Known Stubs

None.

## Verification

- check_stale_docs.py: PASS (all 7 critical files CURRENT)
- steward_audit.py: STEWARD AUDIT: PASS
- No "595", "v0.6", "Claims: 18", or "Domains: 7" remain in either file
