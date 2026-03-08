# Contributing to MetaGenesis Core

## Before you start

Run the acceptance suite to confirm your environment is clean:
```bash
python scripts/steward_audit.py
python -m pytest tests/steward tests/materials tests/ml tests/systems tests/data -q
```
Both must pass before and after any change.

## What you can contribute

- New verified claims (must follow claim lifecycle in reports/scientific_claim_index.md)
- Bug fixes in backend/progress/ or scripts/
- Additional tests in tests/

## What NOT to change

- reports/canonical_state.md (steward-managed)
- reports/scientific_claim_index.md (claim registry — requires steward PASS)
- Any path locked in scripts/mg_policy_gate_policy.json

## Pull request requirements

1. python scripts/steward_audit.py → PASS
2. python -m pytest tests/steward tests/materials tests/ml tests/systems tests/data -q → PASS
3. No "tamper-proof", "GPT-5", "19x" in any changed file
