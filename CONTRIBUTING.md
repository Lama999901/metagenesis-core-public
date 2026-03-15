# Contributing to MetaGenesis Core

## Before you start

Run the acceptance suite to confirm your environment is clean:
```bash
python scripts/steward_audit.py  # → STEWARD AUDIT: PASS
python -m pytest tests/ -q       # → 223 passed
```
Both must pass before and after any change.

**Current state:** 14 claims, 223 tests, 3 verification layers.

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
