# Quick Task 260321-rac: Create scripts/agent_diff_review.py

## One-liner
AST-based structural diff review agent -- scans last commit for test coverage gaps, forbidden terms, doc sync, and manifest consistency.

## What was done

1. **Created `scripts/agent_diff_review.py`** -- New Level 3 agent script with 5 checks:
   - Test reference audit (changed source files have corresponding test references)
   - Forbidden terms scan (tamper-proof, unforgeable, blockchain, GPT-5)
   - Documentation gap detection (core code changed without paper.md update)
   - Manifest test count audit (AST-parsed test function count vs system_manifest.json)
   - Summary mode (`--summary` flag for one-line output)

2. **Updated `scripts/check_stale_docs.py`**:
   - Added content checks entry for `scripts/agent_diff_review.py` (required: REPO_ROOT, ast.parse, forbidden)
   - Changed `docs/AGENT_SYSTEM.md` required string from "15 checks" to "16 checks"

3. **Updated `docs/AGENT_SYSTEM.md`**:
   - Level 3 scripts list: added `agent_diff_review.py (AST structural review)`
   - Recursive loop description: 15 checks -> 16 checks
   - File map table: added `agent_diff_review.py | 3 | AST structural logic review`
   - Agent evolution row: 15-check -> 16-check health monitor

## Verification

- `python scripts/agent_diff_review.py` -- runs without errors (exit 1 is expected due to pre-existing manifest count mismatch, not a bug in the script)
- `python scripts/steward_audit.py` -- STEWARD AUDIT: PASS
- `python scripts/check_stale_docs.py --strict` -- exit 0, all docs current

## Commits

| Hash | Message |
|------|---------|
| 9829f9c | feat: add scripts/agent_diff_review.py AST structural diff analysis |

## Files

| Action | File |
|--------|------|
| Created | `scripts/agent_diff_review.py` |
| Modified | `scripts/check_stale_docs.py` |
| Modified | `docs/AGENT_SYSTEM.md` |

## Branch
`feat/agent-diff-review` pushed to origin.
