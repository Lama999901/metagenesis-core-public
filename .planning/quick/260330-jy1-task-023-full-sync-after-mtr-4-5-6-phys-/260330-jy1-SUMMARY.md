---
phase: quick
plan: 260330-jy1
subsystem: documentation-sync
tags: [counter-sync, version-bump, stale-docs]
dependency_graph:
  requires: []
  provides: [v0.8.0-version-sync, 601-test-counters, 20-claim-counters]
  affects: [all-documentation, check_stale_docs.py, agent_evolution.py]
tech_stack:
  added: []
  patterns: [content-checks-validation, version-string-sync]
key_files:
  created: []
  modified:
    - scripts/agent_evolution.py
    - system_manifest.json
    - docs/AGENT_SYSTEM.md
    - scripts/check_stale_docs.py
    - CONTRIBUTING.md
    - CITATION.cff
    - docs/ARCHITECTURE.md
    - docs/ROADMAP.md
    - paper.md
    - reports/known_faults.yaml
    - reports/scientific_claim_index.md
    - docs/HOW_TO_ADD_CLAIM.md
    - docs/REAL_DATA_GUIDE.md
    - docs/USE_CASES.md
    - CURSOR_MASTER_PROMPT_v2_3.md
    - CLAUDE.md
decisions:
  - "CLAUDE.md updated to v0.8.0 (Rule 3 auto-fix: agent_evolution.py claude_md check required it)"
  - "branch_sync check failure accepted as expected on feature branch"
  - "Added 595 to banned lists in check_stale_docs.py to prevent regressions"
metrics:
  duration: "9min"
  completed: "2026-03-30"
  tasks: 3
  files: 16
---

# Quick Task 260330-jy1: Full Counter/Version Sync After MTR-4/5/6 + PHYS-01/02

Full documentation and version string synchronization: v0.7.0 -> v0.8.0, 595 -> 601 tests, 18 -> 20 claims across 16 files including stale-doc checker rules.

## Tasks Completed

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | Update version/config files and stale-doc checker rules | ff1052e | agent_evolution.py v0.8.0, system_manifest.json 0.8.0, AGENT_SYSTEM.md 18 checks/20 claims, check_stale_docs.py rules updated |
| 2 | Update all documentation files with correct counters | 8ee0029 | 11 doc files: 595->601, 18->20 claims, v0.7->v0.8, new claims in tables |
| 3 | Final verification of both gates + CLAUDE.md fix | bff9791 | CLAUDE.md v0.7.0->v0.8.0, both gates verified |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CLAUDE.md required v0.8.0 for agent_evolution.py check**
- **Found during:** Task 3
- **Issue:** agent_evolution.py check_claude_md requires "v0.8.0" in CLAUDE.md, but CLAUDE.md still had v0.7.0
- **Fix:** Updated all v0.7.0 references in CLAUDE.md to v0.8.0
- **Files modified:** CLAUDE.md
- **Commit:** bff9791

**2. [Rule 2 - Missing] Added 595 to banned lists in check_stale_docs.py**
- **Found during:** Task 1
- **Issue:** After changing required strings from 595 to 601, the old value should be banned to prevent regressions
- **Fix:** Added "595 passed", "595 tests", "595 adversarial" to banned lists for relevant files
- **Files modified:** scripts/check_stale_docs.py
- **Commit:** ff1052e

## Verification Results

- `check_stale_docs.py --strict`: EXIT 0 (all content checks pass)
- `agent_evolution.py --summary`: 16/17 checks PASS (branch_sync expected failure on feature branch)
- No references to 595 remain in required strings
- No references to v0.7.0 remain in updated files

## Self-Check: PASSED
