---
phase: quick
plan: 260320-q3r
subsystem: agent-tooling
tags: [windows-compat, subprocess, post-phase-hook]
dependency_graph:
  requires: []
  provides: [windows-compatible-agent-impact, post-phase-impact-check]
  affects: [scripts/agent_impact.py, .planning/config.json]
tech_stack:
  patterns: [subprocess.DEVNULL for cross-platform stderr suppression]
key_files:
  modified:
    - scripts/agent_impact.py
    - .planning/config.json
decisions:
  - "Replace shell 2>/dev/null with subprocess.DEVNULL for Windows compatibility"
  - "Use stdout=subprocess.PIPE + stderr=subprocess.DEVNULL instead of capture_output=True"
metrics:
  duration: "3min"
  completed: "2026-03-21T02:52:39Z"
  tasks_completed: 2
  tasks_total: 2
---

# Quick Task 260320-q3r: Fix agent_impact.py Windows Compat + Post-Phase Task

**One-liner:** Cross-platform stderr suppression via subprocess.DEVNULL replacing shell 2>/dev/null, plus post_phase_tasks registration.

## What Changed

### Task 1: Fix Windows compat in agent_impact.py and add to post_phase_tasks

- Replaced `capture_output=True` with `stdout=subprocess.PIPE, stderr=subprocess.DEVNULL` in the `run()` helper function
- Removed `2>/dev/null` from two git diff command strings in `main()`
- Added `"python scripts/agent_impact.py --verify-last-commit"` to `post_phase_tasks` array in `.planning/config.json`
- **Commit:** ed8fa9a

### Task 2: Run all 16 evolution checks and push

- `python scripts/agent_evolution.py --summary` -- ALL 16 CHECKS PASSED
- `python scripts/agent_impact.py --summary` -- runs without errors
- `grep "2>/dev/null" scripts/agent_impact.py` -- zero matches
- Pushed to `fix/agent-impact-windows` branch on origin

## Deviations from Plan

### Minor: .planning/config.json is gitignored

The `.planning/` directory is in `.gitignore`, so `config.json` changes were not committed to git. The file was modified locally as specified. Only `scripts/agent_impact.py` was committed. This is expected behavior -- `.planning/` is local agent state.

## Verification Results

| Check | Result |
|-------|--------|
| `python scripts/agent_impact.py --summary` | PASS -- "2 files changed, no impact rules triggered" |
| `grep "2>/dev/null" scripts/agent_impact.py` | 0 matches |
| `grep "agent_impact.py" .planning/config.json` | Found in post_phase_tasks |
| `python scripts/agent_evolution.py --summary` | ALL 16 CHECKS PASSED |
| Branch pushed | fix/agent-impact-windows on origin |

## Commits

| Hash | Message |
|------|---------|
| ed8fa9a | fix(260320-q3r): agent_impact.py Windows compat + post_phase_task registration |

## Self-Check: PASSED
