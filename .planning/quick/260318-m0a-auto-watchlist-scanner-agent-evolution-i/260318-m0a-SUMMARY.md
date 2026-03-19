---
phase: quick
plan: 260318-m0a
subsystem: tooling
tags: [watchlist, scanner, agent-evolution, stale-docs]

requires:
  - phase: none
    provides: check_stale_docs.py CRITICAL_FILES and CONTENT_CHECKS dicts
provides:
  - Auto-watchlist scanner detecting untracked doc files
  - Agent evolution check #9 (watchlist coverage)
  - config.json post_phase_tasks entry for scanner
affects: [agent-evolution, stale-docs, ci]

tech-stack:
  added: []
  patterns: [import-from-sibling-script, advisory-check-pattern]

key-files:
  created:
    - scripts/auto_watchlist_scan.py
  modified:
    - scripts/agent_evolution.py
    - .planning/config.json

key-decisions:
  - "Watchlist check is advisory (returns True even with unwatched files) -- not a hard gate"
  - "Scanner imports CRITICAL_FILES and CONTENT_CHECKS directly from check_stale_docs.py via sys.path"
  - "Scan covers repo root (non-recursive) plus docs/, ppa/, reports/, demos/ (recursive)"

patterns-established:
  - "Advisory check pattern: warn but do not fail, letting user decide when to add files to watchlist"

requirements-completed: [QUICK-WATCHLIST]

duration: 2min
completed: 2026-03-18
---

# Quick 260318-m0a: Auto Watchlist Scanner Summary

**Auto-watchlist scanner finding 29 untracked doc files, integrated as agent_evolution.py check #9 with config.json registration**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-18T23:52:49Z
- **Completed:** 2026-03-18T23:55:04Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Created auto_watchlist_scan.py that detects .md/.yaml/.cff/.txt files not in check_stale_docs.py watchlists
- Integrated as check #9 in agent_evolution.py (advisory, not blocking)
- Added scanner to config.json post_phase_tasks pipeline
- Pushed all changes on feat/agent-completeness branch

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scripts/auto_watchlist_scan.py** - `70dd57c` (feat)
2. **Task 2: Add watchlist check #9 to agent_evolution.py + update config.json** - `3ad97a9` (feat)
3. **Task 3: Git branch, commit, and push** - branch feat/agent-completeness created and pushed

## Files Created/Modified
- `scripts/auto_watchlist_scan.py` - Watchlist coverage scanner (117 lines)
- `scripts/agent_evolution.py` - Added check_watchlist() function and results["watchlist"] call
- `.planning/config.json` - Added auto_watchlist_scan.py to post_phase_tasks array

## Decisions Made
- Watchlist check is advisory (not a hard failure) -- warns about unwatched files but returns True so it does not block the evolution check
- Scanner imports dicts directly from check_stale_docs.py using sys.path insertion for sibling-script imports
- Excluded directories (.planning, .claude, .git, __pycache__, etc.) to avoid scanning infrastructure files

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- .planning directory is in .gitignore; required `git add -f` to stage config.json

## User Setup Required
None - no external service configuration required.

## Next Steps
- Review the 29 unwatched files and decide which to add to CRITICAL_FILES or CONTENT_CHECKS
- Consider adding --strict to CI pipeline once watchlists are complete

---
*Quick task: 260318-m0a*
*Completed: 2026-03-18*
