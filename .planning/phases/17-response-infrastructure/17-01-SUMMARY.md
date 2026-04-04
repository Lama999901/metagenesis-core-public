---
phase: "17"
plan: "01"
subsystem: response-infrastructure
tags: [agent, cli, outreach, bundle-generation, queue-management]
dependency_graph:
  requires: [mg_client.py, mg.py, backend/progress/*]
  provides: [agent_responder.py, response_queue.json, response_drafts/*, response_bundles/*]
  affects: [outreach workflow, client response time]
tech_stack:
  added: []
  patterns: [fuzzy-keyword-matching, template-draft-generation, queue-file-tracking]
key_files:
  created:
    - scripts/agent_responder.py
    - tests/test_agent_responder.py
  modified: []
decisions:
  - Weighted fuzzy matching by keyword length (longer keywords score higher) for reliable contact resolution
  - Draft templates use plain string formatting -- no AI/LLM APIs
  - Bundle generation delegates to existing mg_client.run_claim + create_bundle pipeline
  - Queue uses flat JSON file consistent with pilot_queue.json pattern
metrics:
  duration: 4m
  completed: "2026-04-04"
---

# Phase 17 Plan 01: Response Infrastructure Summary

**One-liner:** agent_responder.py prepares complete response kits (draft + domain-specific bundle + queue entry) for 7 named contacts in under 60 seconds using fuzzy keyword matching and existing verification infrastructure.

## What Was Built

### scripts/agent_responder.py (390 lines)
- **--prepare "contact text"**: Fuzzy-matches contact to domain, generates verification bundle via mg_client, creates plain-text draft, adds queue entry -- all in one command
- **--status**: Shows queue entries with age in days and status counts
- **--list-domains**: Displays all 8 mappings (7 named + 1 default) with claims and descriptions
- **--update-status "contact" "status"**: Updates entry status with validation (prepared/reviewed/bundle_sent/replied/converted)

### 7 Domain Mappings (RESP-02)
| Contact | Company | Claims | mg_client Domain |
|---------|---------|--------|-----------------|
| Patronus AI / Anand | Patronus AI | ML_BENCH-01 | ml |
| Bureau Veritas / Philipp | Bureau Veritas | FINRISK-01 | finance |
| Chollet / ARC | ARC / Chollet | ML_BENCH-02 | ml |
| Percy Liang / HELM | Stanford HELM | ML_BENCH-03 | ml |
| IQVIA / Raja Shankar | IQVIA | ML_BENCH-01, PHARMA-01 | pharma |
| LMArena | LMArena | ML_BENCH-01 | ml |
| South Pole | South Pole | DATA-PIPE-01, ML_BENCH-01 | ml |
| (default) | Unknown | DATA-PIPE-01 | ml |

### Draft Quality (RESP-03)
- Plain text, short paragraphs, reads like human-written
- Uses -- (double dash) not em-dashes, no special unicode
- References contact-specific outreach context
- Shows PASS result for their domain
- Ends with ONE specific next-step question
- No Stripe link in first reply

### tests/test_agent_responder.py (53 tests)
- 7 domain mapping resolution tests
- 8 fuzzy matching tests (partial names, case insensitive)
- 4 default domain tests (unknown, empty, None, whitespace)
- 8 draft format validation tests
- 3 real bundle generation tests
- 6 queue management tests
- 2 status command output tests
- 1 list-domains output test
- 4 status transition tests (including full flow)
- 8 edge case tests (empty name, duplicates, sanitize, key completeness)
- 2 CLI integration tests

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | 074f5ee | feat(17-01): add agent_responder.py with 7 domain mappings and CLI |
| 2 | 01f4e9e | test(17-01): add 53 tests for agent_responder.py |

## Verification Results

- `python scripts/agent_responder.py --list-domains` -- PASS (8 mappings displayed)
- `python scripts/agent_responder.py --prepare "Anand Patronus ML"` -- PASS (bundle + draft + queue in <5s)
- `python scripts/agent_responder.py --status` -- PASS (shows entry with age)
- `python -m pytest tests/test_agent_responder.py -v` -- 53/53 PASS
- `python scripts/steward_audit.py` -- STEWARD AUDIT: PASS

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None. All functionality is wired to real infrastructure (mg_client.run_claim, create_bundle, verify_bundle).

## Self-Check: PASSED

- scripts/agent_responder.py: FOUND
- tests/test_agent_responder.py: FOUND
- Commit 074f5ee: FOUND
- Commit 01f4e9e: FOUND
