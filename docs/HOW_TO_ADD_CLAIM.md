# How to Add a New Verified Claim

This guide walks through adding a new computational claim
to MetaGenesis Core. Follow every step in order.
steward_audit must PASS at the end.

---

## What is a claim?

A claim is a verifiable computational statement with:
- A unique ID (e.g. MTR-1, SYSID-01, YOUR-CLAIM-01)
- A job_kind string that identifies it in the runner
- A deterministic function that produces a result
- V&V thresholds that define pass/fail
- Tests that prove the thresholds hold
- An entry in the claim index and canonical state

---

## Step 1 — Create the implementation

Create: `backend/progress/<your_claim_lower>.py`

Required structure:

```python
JOB_KIND = "your_claim_job_kind"   # unique string, no spaces
ALGORITHM_VERSION = "v1"

def run_<your_claim>(
    # your parameters here
) -> dict:
    # your computation here
    result = ...
    return {
        "mtr_phase": "YOUR-CLAIM-01",   # required — semantic verifier checks this
        "algorithm_version": ALGORITHM_VERSION,
        "inputs": { ... },
        "result": { ... },
        "status": "SUCCEEDED",
    }
```

Rules:
- No new pip dependencies unless absolutely necessary
- Function must be deterministic given same inputs
- Return dict must contain "mtr_phase" key

---

## Step 2 — Register in runner

Open: `backend/progress/runner.py`
Find: `_execute_job_logic()` function
Add before the final `return` statement:

```python
from backend.progress.<your_claim_lower> import JOB_KIND as YOUR_KIND, run_<your_claim>
if payload.get("kind") == YOUR_KIND:
    p = payload
    return run_<your_claim>(
        # map payload fields to function parameters
    )
```

---

## Step 3 — Add to claim index

Open: `reports/scientific_claim_index.md`
Append at the end:

```markdown
---

## YOUR-CLAIM-01

| Field | Value |
|-------|-------|
| **claim_id** | YOUR-CLAIM-01 |
| **job_kind** | `your_claim_job_kind` |
| **domain** | Your domain description |
| **reproduction** | `python -m pytest tests/steward/test_yourclaim.py -v` |
| **V&V thresholds** | your threshold description |
```

The job_kind value must be in backticks — steward_audit parses this.

---

## Step 4 — Update canonical state

Open: `reports/canonical_state.md`
Find the line:
```
| **current_claims_list** | MTR-1, MTR-2, ... |
```
Add YOUR-CLAIM-01 to the comma-separated list.

---

## Step 5 — Write tests

Create: `tests/steward/test_<your_claim_lower>.py`

Minimum required tests:
```python
def test_job_kind_constant():
    assert JOB_KIND == "your_claim_job_kind"

def test_success_case():
    result = run_<your_claim>(...)
    assert result["status"] == "SUCCEEDED"
    assert result["mtr_phase"] == "YOUR-CLAIM-01"
    # check your V&V threshold

def test_failure_case():
    # test that bad inputs produce correct failure signal

def test_adversarial_edge_case():
    # test boundary condition just above/below threshold
```

---

## Step 6 — Verify everything

Run in order — all must pass:

```bash
python scripts/steward_audit.py
# Must output: STEWARD AUDIT: PASS
# Must show YOUR-CLAIM-01 in both lists

python -m pytest tests/steward/test_<your_claim_lower>.py -v
# All tests passed

  python -m pytest tests/ -q
  # All passed (previous count + your new tests)

python demos/open_data_demo_01/run_demo.py
# PASS PASS
```

---

## Step 7 — Commit

```bash
git add backend/progress/<your_claim_lower>.py
git add backend/progress/runner.py
git add reports/scientific_claim_index.md
git add reports/canonical_state.md
git add tests/steward/test_<your_claim_lower>.py
git commit -m "feat: YOUR-CLAIM-01 — short description"
git push
```

---

## Example: DRIFT-01

The complete example of a correctly implemented claim:
- Implementation: `backend/progress/drift_monitor.py`
- Runner dispatch: `backend/progress/runner.py` (search DRIFT01_KIND)
- Claim index: `reports/scientific_claim_index.md` (DRIFT-01 section)
- Canonical state: `reports/canonical_state.md` (DRIFT-01 in list)
- Tests: `tests/steward/test_drift01_calibration_anchor.py` (16 tests)

Study this before adding your own claim.
