# Contributing to MetaGenesis Core

Thank you for your interest in contributing to MetaGenesis Core. This document
describes how to set up your environment, submit changes, and add new
verification claims.

## Before you start

Run the acceptance suite to confirm your environment is clean:
```bash
python scripts/steward_audit.py  # → STEWARD AUDIT: PASS
python -m pytest tests/ -q       # → 1050 passed
python scripts/deep_verify.py    # → ALL 13 TESTS PASSED
```
All three must pass before and after any change.

**Current state:** 20 claims, 1050 tests, 5 verification layers.

## Git Workflow

Always branch from `main` — never push directly to `main`.

```bash
git checkout -b feat/description   # new feature
git checkout -b fix/description    # bug fix
# ... make changes ...
git add <files>
git commit -m "type: description"
git push origin feat/description
```

Open a pull request on GitHub. CI must pass before merge.

## What you can contribute

- New verified claims (must follow the 6-step procedure below)
- Bug fixes in `backend/progress/` or `scripts/`
- Additional tests in `tests/`
- Documentation improvements

## Adding a New Claim — Mandatory 6 Steps

Every new claim must follow these six steps exactly. Skipping any step will
cause the steward audit to fail.

### Step 1. Create the claim implementation

Create `backend/progress/<claim_id>.py` with the 4-step Step Chain:

```python
def _hash_step(step_name, step_data, prev_hash):
    import hashlib, json as _j
    content = _j.dumps({"step": step_name, "data": step_data,
                        "prev_hash": prev_hash},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

_prev = _hash_step("init_params", {params}, "genesis")
_trace = [{"step": 1, "name": "init_params", "hash": _prev}]
_prev = _hash_step("compute", {results}, _prev)
_trace.append({"step": 2, "name": "compute", "hash": _prev})
_prev = _hash_step("metrics", {metrics}, _prev)
_trace.append({"step": 3, "name": "metrics", "hash": _prev})
_passed = result_value <= threshold
_prev = _hash_step("threshold_check",
                   {"passed": _passed, "threshold": threshold}, _prev)
_trace.append({"step": 4, "name": "threshold_check",
               "hash": _prev, "output": {"pass": _passed}})
trace_root_hash = _prev
```

The function must return this exact structure:

```python
return {
    "mtr_phase": "CLAIM-ID",
    "inputs": {...},
    "result": {...},
    "execution_trace": _trace,
    "trace_root_hash": trace_root_hash,
}
```

### Step 2. Register in the runner

Add a dispatch block to `backend/progress/runner.py` so the runner can
execute the new claim.

### Step 3. Register in the claim index

Add an entry to `reports/scientific_claim_index.md` with the claim ID,
domain, threshold, and physical anchor status.

### Step 4. Update canonical state

Add the new claim to `reports/canonical_state.md` in the `current_claims_list`.

### Step 5. Write tests

Create `tests/<domain>/test_<claim_id>.py` with at minimum:
- A **pass** test (inputs within threshold)
- A **fail** test (inputs exceeding threshold)
- A **determinism** test (two runs produce identical `trace_root_hash`)

### Step 6. Update counters

Update the claim/test counts in **all** of these files:

- `index.html` (11 places including prose text)
- `README.md`
- `AGENTS.md`
- `llms.txt`
- `system_manifest.json`
- `CONTEXT_SNAPSHOT.md`
- `known_faults.yaml`

## What NOT to change

These files are sealed or steward-managed. Do not modify them without
explicit approval:

- `scripts/steward_audit.py` (CI-locked, SEALED)
- `scripts/mg_policy_gate_policy.json` (policy gate config)
- `ppa/CLAIMS_DRAFT.md` (frozen PPA document)
- `reports/canonical_state.md` (steward-managed)
- `demos/open_data_demo_01/evidence_index.json` (locked artifact)
- `.github/workflows/total_audit_guard.yml` (CI gate)
- `.github/workflows/mg_policy_gate.yml` (CI gate)

## Pull request requirements

1. `python scripts/steward_audit.py` passes
2. `python -m pytest tests/ -q` passes
3. No banned terms in any changed file: "tamper-proof" (use "tamper-evident"),
   "blockchain" (use "cryptographic hash chain"), "unforgeable", "GPT-5",
   "100% test success"

## Full verification (proof, not trust)

Run the deep verification script before any major release or claim:
```bash
python scripts/deep_verify.py
# → ALL 13 TESTS PASSED
```
This script verifies: governance, 1050 tests, 20 JOB_KINDs in runner,
Step Chain in all 20 claims, Cross-Claim Chain, forbidden terms,
site numbers, demo end-to-end, bypass attack caught, verify-chain CLI,
Ed25519 signing integrity, Ed25519 reproducibility, temporal commitment.
