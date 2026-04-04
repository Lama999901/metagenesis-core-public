---
phase: "20"
plan: "01"
subsystem: protocol-hardening
tags: [documentation, protocol, inline-comments, CLAUDE.md]
dependency_graph:
  requires: []
  provides: [HARD-01, HARD-02, HARD-04]
  affects: [docs/PROTOCOL.md, scripts/mg.py, CLAUDE.md]
tech_stack:
  added: []
  patterns: [inline-WHY-comments]
key_files:
  created: []
  modified:
    - docs/PROTOCOL.md
    - scripts/mg.py
    - CLAUDE.md
decisions:
  - "Placed physical anchor prose after existing SI 2019 paragraph, before scope disclaimer"
  - "Added 5 WHY comments at semantically appropriate locations in mg.py"
  - "Expanded outreach contacts from 3 to 9 across 6 domains"
metrics:
  duration: "7m 32s"
  completed: "2026-04-04T06:10:52Z"
  tasks_completed: 3
  tasks_total: 3
---

# Phase 20 Plan 01: Protocol Hardening v2 Summary

Physical anchor prose in PROTOCOL.md, inline WHY comments in mg.py, CLAUDE.md updates for new scripts and 20 Mechanicus checks.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | PROTOCOL.md physical anchor prose | 9f39e3a | docs/PROTOCOL.md |
| 2 | mg.py inline WHY comments | 981acc9 | scripts/mg.py |
| 3 | CLAUDE.md updates | aaa0f93 | CLAUDE.md |

## What Changed

### HARD-01: PROTOCOL.md Physical Anchor Prose
Added two paragraphs to the Physical Anchor Chain section of docs/PROTOCOL.md:
- Boltzmann constant (kB) permanence paragraph explaining SI 2019 exact definition
- Avogadro number (NA) permanence paragraph explaining zero-uncertainty defined constants
- Inserted after existing SI 2019 explanation, before the "What this does NOT apply to" scope disclaimer

### HARD-02: mg.py Inline WHY Comments
Added 5 multi-line WHY comments to scripts/mg.py at semantically appropriate locations:
1. WHY 5 LAYERS -- near top-level constants (CERT-11 independence proof)
2. WHY SEMANTIC LAYER -- before _verify_semantic() (catches evidence stripping)
3. WHY NIST BEACON -- before temporal commitment check (proves WHEN signed)
4. WHY STEP CHAIN -- before step chain verification (proves HOW computed)
5. WHY ED25519 -- before sign subcommand (enables third-party verification)

### HARD-04: CLAUDE.md Updates
- Added 4 new scripts to KEY FILES: mg_self_audit.py, mg_receipt.py, agent_responder.py, agent_evolution_council.py
- Added 2 new docs to KEY FILES: docs/AGENT_CHARTER.md, docs/ROADMAP_VISION.md
- Updated Mechanicus checks count: 19 -> 20 (in CURRENT STATE, KEY FILES, and footer)
- Expanded Wave-2 outreach from 3 contacts to 9 contacts across 6 domains (ML/AI, Science, Pharma, Finance, Digital Twin, Climate)

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- steward_audit.py: PASS (canonical sync PASS, all claims dispatched)
- check_stale_docs.py: PASS (7 CURRENT, 0 STALE)
- pytest: 1753 passed, 2 skipped

## Known Stubs

None -- all changes are documentation/comments only, no code stubs introduced.
