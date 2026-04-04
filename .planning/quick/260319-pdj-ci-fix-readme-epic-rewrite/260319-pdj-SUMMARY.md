---
phase: quick
plan: 260319-pdj
subsystem: docs + ci
tags: [ci-fix, readme, documentation, stale-docs]
key-files:
  modified:
    - scripts/check_stale_docs.py
    - README.md
decisions:
  - "Expanded Mechanicus Parallel to 15 rows with agent system mappings"
  - "Added concrete attack examples for each of the 5 layers with test file references"
  - "Kept banned term enforcement -- rewrote 'tamper-proof' reference to avoid literal usage"
metrics:
  duration: ~15min
  completed: 2026-03-19
---

# Quick Task 260319-pdj: CI Fix + README Epic Rewrite Summary

**One-liner:** Fixed check_stale_docs.py watchlist with 6 missing entries; rewrote README from 430 to 603 lines with Problem, Layers In Depth, Agent Evolution, and Honest Limitations sections.

## Task 1: check_stale_docs.py CI Fix

Added 6 missing entries to CONTENT_CHECKS:
- `tests/agent/test_agent_drift01.py` -- required: `['AGENT-DRIFT-01', 'TestAgentDrift01']`
- `backend/progress/agent_drift_monitor.py` -- required: `['AGENT-DRIFT-01']`
- `scripts/mg_policy_gate_policy.json` -- empty checks (existence only)
- `.github/workflows/mg_policy_gate.yml` -- empty checks (existence only)
- `reports/COVERAGE_REPORT_20260319.md` -- empty checks (existence only)
- `reports/SELF_IMPROVEMENT_20260319.md` -- empty checks (existence only)

**Verification:** `python scripts/check_stale_docs.py --strict` exits 0. All 39 content checks PASS.

## Task 2: README.md Epic Rewrite

Expanded from 430 to 603 lines. All existing technical content preserved. New sections added:

1. **The Problem** -- Nature 2016 (70% irreproducibility), Kapoor & Narayanan 2023 (294 ML papers), NeurIPS 2025 Leaderboard Illusion, FDA 2025 credibility framework, concrete reviewer scenarios
2. **Why SHA-256 Alone Is Not Enough** -- 4-layer attack escalation showing each layer catching what previous layers miss
3. **The Five Layers In Depth** -- for each layer: what attack it catches, what the other 4 miss, exact test file, one line of output
4. **The Mechanicus Parallel** -- expanded from 10 to 15 rows (added Noosphere, Servo-skulls, Heresy, Lexmechanic, Machine Spirit, Skitarii, Cogitator, Genetor, Recursive Enlightenment)
5. **The Agent Evolution System** -- 12 checks table, self-improvement loop explanation, AGENT-DRIFT-01 recursive self-verification
6. **Honest Limitations** -- SCOPE_001 and ENV_001 expanded with WHY each limitation exists, explicit non-goals with detailed explanations
7. **The Founder's Story** -- expanded with 14-day timeline breakdown

**Banned terms check:** No "tamper-proof", "blockchain", "unforgeable", "GPT-5", or "100% test success" in the README.

## Verification

- `python scripts/check_stale_docs.py --strict` -- EXIT 0
- `python scripts/agent_evolution.py --summary` -- ALL 12 CHECKS PASSED
- README.md line count: 603 (target: 600-700)
- Branch: `fix/readme-epic`
- Commit: 287efdc

## Deviations from Plan

None -- plan executed exactly as written.

## Self-Check: PASSED

- [x] scripts/check_stale_docs.py modified with 6 new entries
- [x] README.md rewritten to 603 lines
- [x] check_stale_docs.py --strict exits 0
- [x] agent_evolution.py --summary ALL 12 PASS
- [x] Branch fix/readme-epic created and pushed
- [x] Commit 287efdc verified
- [x] No banned terms in README
