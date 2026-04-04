---
phase: quick
plan: 260319-qn5
subsystem: agent-evolution
tags: [signals, chronicle, evolution, ci]
key-files:
  created:
    - scripts/agent_signals.py
    - scripts/agent_chronicle.py
    - reports/SIGNALS_20260319.md
    - reports/CHRONICLE_0_6_0_20260319.md
  modified:
    - scripts/agent_evolution.py
    - .github/workflows/weekly_agent_health.yml
decisions:
  - "GitHub API fetch uses 10s timeout + graceful fallback to prevent CI hang"
  - "Both new checks are advisory (return True on failure) to avoid blocking evolution"
  - "Chronicle filename uses version with underscores for filesystem safety"
metrics:
  tasks: 3
  completed: 2026-03-19
---

# Quick Task 260319-qn5: Agent Signals + Chronicle + 14-Check Wiring Summary

External signals relay and versioned chronicle scripts, wired into agent_evolution.py as checks 13 and 14.

## What Was Done

### Task 1: Created both scripts

**scripts/agent_signals.py** -- Fetches GitHub API repo stats (stars, forks, issues, last push), counts agent memory files, parses AGENT_TASKS.md for PENDING/DONE counts, reads system_manifest.json. Writes `reports/SIGNALS_{YYYYMMDD}.md`. Supports `--summary` flag. Handles API failures gracefully with fallback message.

**scripts/agent_chronicle.py** -- Reads manifest for version/claims/tests/innovations, parses scientific_claim_index.md for domains, counts tasks, finds previous CHRONICLE files and computes diffs. Writes `reports/CHRONICLE_{version}_{YYYYMMDD}.md`. Supports `--summary` flag.

### Task 2: Wired into agent_evolution.py

- Added `check_signals()` as check 13 (EXTERNAL SIGNALS -- Astropathic Relay)
- Added `check_chronicle()` as check 14 (CHRONICLE -- Historitor Record)
- Added both to `results` dict and `mechanicus_labels` dict
- Updated display version from v0.5.0 to v0.6.0

### Task 3: CI + verification

- Added `python scripts/agent_signals.py` step to weekly_agent_health.yml
- Ran both scripts successfully, reports generated
- Ran `python scripts/agent_evolution.py --summary` -- ALL 14 CHECKS PASSED

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

- reports/SIGNALS_20260319.md: GENERATED (595 bytes)
- reports/CHRONICLE_0_6_0_20260319.md: GENERATED (13467 bytes)
- agent_evolution.py: ALL 14 CHECKS PASSED
- Branch: feat/agent-divine-v2 pushed to origin

## Commit

- `9cc5653`: feat: add agent_signals.py + agent_chronicle.py, wire into 14-check evolution
