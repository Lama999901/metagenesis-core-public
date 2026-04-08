---
phase: 26-counter-sync-and-gate-hardening
plan: 01
subsystem: infra
tags: [documentation, counters, check_stale_docs, ci-gates]

# Dependency graph
requires:
  - phase: 23-25 (prior phases that added tests)
    provides: new tests bringing count from 2063 to 2078
provides:
  - All 20 counter files synced to true pytest count 2078
  - check_stale_docs.py rules updated (2063 banned, 2078 required)
  - system_manifest.json test_count updated to 2078
affects: [any future phase that changes test count]

# Tech tracking
tech-stack:
  added: []
  patterns: [TRAP-STALE-RULES enforcement - counter + rules updated atomically]

key-files:
  created: []
  modified:
    - system_manifest.json
    - scripts/check_stale_docs.py
    - index.html
    - README.md
    - AGENTS.md
    - llms.txt
    - CONTEXT_SNAPSHOT.md
    - CLAUDE.md
    - CONTRIBUTING.md
    - CITATION.cff
    - docs/ARCHITECTURE.md
    - docs/ROADMAP.md
    - docs/AGENT_SYSTEM.md
    - ppa/README_PPA.md
    - paper.md
    - reports/known_faults.yaml
    - CURSOR_MASTER_PROMPT_v2_3.md
    - docs/HOW_TO_ADD_CLAIM.md
    - docs/REAL_DATA_GUIDE.md
    - docs/USE_CASES.md
    - reports/scientific_claim_index.md
    - .zenodo.json

key-decisions:
  - "Used pytest as single source of truth: 2078 passed (2063 was stale)"
  - "Updated docs/AGENT_SYSTEM.md and .zenodo.json in addition to plan-listed files (both contained stale 2063)"

patterns-established:
  - "Counter sync: always run pytest first, then propagate count to all files + check_stale_docs.py in same commit"

requirements-completed: [DOCS-01, DOCS-02]

# Metrics
duration: 3min
completed: 2026-04-07
---

# Phase 26 Plan 01: Counter Sync Summary

**Synced all 22 documentation files from stale count 2063 to true pytest count 2078, with check_stale_docs.py rules atomically updated**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-07T06:47:36Z
- **Completed:** 2026-04-07T06:50:01Z
- **Tasks:** 3
- **Files modified:** 22

## Accomplishments
- Determined true test count via pytest: 2078 passed (15 new tests since last sync)
- Updated system_manifest.json as authoritative source
- Updated check_stale_docs.py: moved "2063" to banned lists, set "2078" in required lists for all 18 content-checked entries
- Replaced "2063" with "2078" in all 20 counter files (63 total occurrences)
- check_stale_docs.py --strict passes with all OK

## Task Commits

Each task was committed atomically:

1. **Task 1: Update check_stale_docs.py + system_manifest.json** - `c6e4895` (chore)
2. **Task 2: Update all counter files to new test count** - `b84aec3` (chore)
3. **Task 3: Validate check_stale_docs.py --strict passes** - validation only, no file changes

## Files Created/Modified
- `system_manifest.json` - test_count 2063 -> 2078
- `scripts/check_stale_docs.py` - 18 entries: 2063 moved to banned, 2078 set in required
- `index.html` - 14 occurrences updated (counters, badges, prose)
- `README.md` - 7 occurrences (badge URL, prose, context snapshot ref)
- `CLAUDE.md` - 6 occurrences (header, banned terms, pytest, footer)
- `AGENTS.md` - 5 occurrences
- `reports/known_faults.yaml` - 5 occurrences
- `CURSOR_MASTER_PROMPT_v2_3.md` - 5 occurrences
- `CONTRIBUTING.md` - 3 occurrences
- `docs/ROADMAP.md` - 3 occurrences
- `llms.txt` - 2 occurrences
- `CONTEXT_SNAPSHOT.md` - 2 occurrences
- `ppa/README_PPA.md` - 2 occurrences
- `paper.md` - 2 occurrences
- `CITATION.cff` - 1 occurrence
- `docs/ARCHITECTURE.md` - 1 occurrence
- `docs/AGENT_SYSTEM.md` - 1 occurrence
- `docs/HOW_TO_ADD_CLAIM.md` - 1 occurrence
- `docs/REAL_DATA_GUIDE.md` - 1 occurrence
- `docs/USE_CASES.md` - 1 occurrence
- `reports/scientific_claim_index.md` - 1 occurrence
- `.zenodo.json` - 1 occurrence

## Decisions Made
- Used pytest count (2078) as single source of truth rather than any hardcoded value
- Updated docs/AGENT_SYSTEM.md and .zenodo.json which were not in the original plan file list but contained stale "2063" (Rule 2: auto-fix missing critical functionality)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Updated docs/AGENT_SYSTEM.md and .zenodo.json**
- **Found during:** Task 2 (counter file updates)
- **Issue:** These files contained "2063" but were not listed in the plan's file list
- **Fix:** Included them in the global replacement
- **Files modified:** docs/AGENT_SYSTEM.md, .zenodo.json
- **Verification:** grep confirms no stale "2063" in any documentation file

---

**Total deviations:** 1 auto-fixed (1 missing critical - 2 extra files needed updating)
**Impact on plan:** Essential for consistency. Without this, check_stale_docs.py would pass but these files would remain stale.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All counters synced to 2078
- check_stale_docs.py --strict passes
- Ready for Phase 26 Plan 02 or any future phase

---
## Self-Check: PASSED

- All key files exist (system_manifest.json, check_stale_docs.py, index.html, README.md, AGENTS.md, llms.txt, CONTEXT_SNAPSHOT.md, CLAUDE.md)
- Commit c6e4895 (Task 1) verified
- Commit b84aec3 (Task 2) verified
- check_stale_docs.py --strict exits 0

---
*Phase: 26-counter-sync-and-gate-hardening*
*Completed: 2026-04-07*
