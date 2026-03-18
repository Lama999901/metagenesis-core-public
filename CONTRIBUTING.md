# Contributing to MetaGenesis Core

## Before you start

Run the acceptance suite to confirm your environment is clean:
```bash
python scripts/steward_audit.py  # → STEWARD AUDIT: PASS
python -m pytest tests/ -q       # → 511 passed
python scripts/deep_verify.py    # → ALL 13 TESTS PASSED ✅
```
All three must pass before and after any change.

**Current state:** 14 claims, 511 tests, 5 verification layers.

## What you can contribute

- New verified claims (must follow claim lifecycle in reports/scientific_claim_index.md)
- Bug fixes in backend/progress/ or scripts/
- Additional tests in tests/

## What NOT to change

- reports/canonical_state.md (steward-managed)
- reports/scientific_claim_index.md (claim registry — requires steward PASS)
- reports/known_faults.yaml (fault registry — do not remove or downgrade faults)
- ppa/CLAIMS_DRAFT.md (frozen PPA document — never edit)
- docs/ROADMAP.md (do not change version numbers without steward PASS)
- Any path locked in scripts/mg_policy_gate_policy.json

## Pull request requirements

1. python scripts/steward_audit.py → PASS
2. python -m pytest tests/ -q → PASS
3. No "tamper-proof", "GPT-5", "19x" in any changed file

## Full verification (proof, not trust)

Run the deep verification script before any major release or claim:
```bash
python scripts/deep_verify.py
# → ALL 13 TESTS PASSED ✅
```
This script verifies: governance, 511 tests, 14 JOB_KINDs in runner,
Step Chain in all 14 claims, Cross-Claim Chain, forbidden terms,
site numbers, demo end-to-end, bypass attack caught, verify-chain CLI,
Ed25519 signing integrity, Ed25519 reproducibility, temporal commitment.
