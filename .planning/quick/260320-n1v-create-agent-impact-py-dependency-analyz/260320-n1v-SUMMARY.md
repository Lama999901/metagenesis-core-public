---
phase: quick
plan: 260320-n1v
subsystem: agent-tooling
tags: [dependency-analysis, impact-check, agent-evolution]
dependency_graph:
  requires: [UPDATE_PROTOCOL.md, agent_evolution.py]
  provides: [agent_impact.py, check-16-impact]
  affects: [agent_evolution.py, check_stale_docs.py]
tech_stack:
  added: []
  patterns: [advisory-check, dependency-rule-engine]
key_files:
  created:
    - scripts/agent_impact.py
  modified:
    - scripts/agent_evolution.py
    - scripts/check_stale_docs.py
decisions:
  - "Hardcoded trigger patterns (UPDATE_PROTOCOL.md lacks machine-readable triggers)"
  - "Advisory only (exit 0 always) to avoid blocking CI on informational gaps"
metrics:
  duration: ~3min
  completed: 2026-03-21
---

# Quick Task 260320-n1v: Agent Impact Analyzer Summary

**One-liner:** Dependency impact analyzer that detects change types and checks if all required downstream files were updated, wired as evolution check 16.

## What Was Done

### Task 1: Created scripts/agent_impact.py
- Dependency impact analyzer with 5 change type rules (new_claim, new_tests, new_layer, new_release, new_innovation)
- `parse_update_protocol()` returns hardcoded rules derived from UPDATE_PROTOCOL.md
- `detect_change_type()` matches changed files against trigger patterns
- `check_impact()` collects required files and identifies missing updates
- `main()` supports `--summary` mode for single-line output
- Advisory only -- never returns non-zero exit code
- Commit: b662738

### Task 2: Added check 16 to agent_evolution.py + watchlist
- Added `check_impact()` function as check 16 "Cogitator Impact"
- Added to mechanicus_labels dict with IMPACT code prefix
- Added `agent_impact.py` to CONTENT_CHECKS in check_stale_docs.py
- Added `check_impact` to required strings for agent_evolution.py watchlist entry
- Commit: b01267c

### Task 3: Verification and push
- Steward audit: PASS
- All 16 evolution checks present (15 PASS, 1 advisory branch_sync FAIL -- expected on feature branch)
- Impact check shows as PASS in evolution summary
- Pushed to feat/agent-impact branch on origin

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | b662738 | feat(quick-n1v): add agent_impact.py dependency analyzer |
| 2 | b01267c | feat(quick-n1v): add impact check 16 to agent_evolution.py + watchlist |

## Self-Check: PASSED
