# MetaGenesis Core - Operations & Contribution Protocol
## Version: 1.0 | Date: 2026-03-08 | PPA: 63/996,819

This document defines the **only approved workflow** for modifying MetaGenesis Core.
Every change must maintain: `steward_audit PASS` + `91 tests PASS` + USPTO enablement.

---

## PART 1 - SYSTEM ARCHITECTURE (read-only context)

### What MetaGenesis Core IS
A **verification protocol layer** that makes computational claims:
- Tamper-evident (not tamper-proof -- this distinction is legally required)
- Reproducible by any third party offline
- Independently auditable without trusting any single party

### What it is NOT
- Not a simulation platform
- Not an AI system
- Not a GPT wrapper

### The 4 Patentable Innovations (DO NOT alter without patent attorney)

1. Governance-Enforced Bidirectional Claim Coverage
   -> scripts/steward_audit.py :: _claim_coverage_bidirectional()

2. Tamper-Evident Bundle with Semantic Verification Layer
   -> scripts/mg.py :: _verify_pack() + _verify_semantic()
   -> PROOF: tests/steward/test_cert02 (adversarial tamper test PASS)

3. Policy-Gate-Enforced Immutable Evidence Anchor
   -> scripts/mg_policy_gate_policy.json :: locked_paths (4 sealed paths + steward_audit.py)
   -> .github/workflows/mg_policy_gate.yml :: CI enforcement

4. Dual-Mode Canary Execution Pipeline
   -> backend/progress/runner.py :: ProgressRunner.run_job(canary_mode=True/False)

### Active Claims (7 total, all verified)

| Claim ID     | Domain             | JOB_KIND                                    | Backend file                                      |
|--------------|--------------------|--------------------------------------------|---------------------------------------------------|
| MTR-1        | Materials Science  | mtr1_youngs_modulus_calibration             | backend/progress/mtr1_calibration.py              |
| MTR-2        | Materials Science  | mtr2_thermal_paste_conductivity_calibration | backend/progress/mtr2_thermal_conductivity.py     |
| MTR-3        | Materials Science  | mtr3_thermal_multilayer_contact_calibration | backend/progress/mtr3_thermal_multilayer.py       |
| SYSID-01     | System ID          | sysid1_arx_calibration                      | backend/progress/sysid1_arx_calibration.py        |
| DATA-PIPE-01 | Data Pipeline      | datapipe1_quality_certificate               | backend/progress/datapipe1_quality_certificate.py |
| DRIFT-01     | Drift Monitoring   | drift_calibration_monitor                   | backend/progress/drift_monitor.py                 |
| ML_BENCH-01  | ML Benchmarking    | mlbench1_accuracy_certificate               | backend/progress/mlbench1_accuracy_certificate.py |

### Sealed Files (locked by policy gate -- DO NOT MODIFY)

  reports/canonical_state.md                   <- PPA filing basis / source of truth
  reports/scientific_claim_index.md             <- claim registry with V&V thresholds
  demos/open_data_demo_01/evidence_index.json  <- demo provenance
  system_manifest.json                          <- PPA metadata
  scripts/steward_audit.py                      <- governance enforcer (CI-locked)

NOTE: scripts/mg_policy_gate_policy.json is intentionally NOT in locked_paths
to prevent operational deadlock (self_seal_removed by design).

---

## PART 2 - HOW TO ADD A NEW CLAIM (complete 10-step checklist)

### STEP 1 -- Write the backend module
Create: backend/progress/<claimid>_<name>.py

Required structure:
```python
JOB_KIND = 'unique_job_kind_snake_case'   # globally unique across all modules
ALGORITHM_VERSION = 'v1'
METHOD = 'your_method'

def run_certificate(...) -> dict:
    return {
        'mtr_phase': 'CLAIM-ID',   # must match claim_id exactly
        'inputs': { ... },         # all inputs, deterministic
        'result': {
            'pass': True or False,
            # ...domain-specific metrics
        }
    }
```

Rules:
- JOB_KIND must be unique across all backend/progress/*.py files
- mtr_phase in result must exactly match the claim ID string
- Function must be deterministic (same inputs -> same outputs, always)
- Stdlib only -- no new pip dependencies

### STEP 2 -- Register dispatch in runner
File: backend/progress/runner.py -> _execute_job_logic()

Add before the fallthrough return:
```python
from backend.progress.<module> import JOB_KIND as NEW_KIND, run_certificate as run_new
if payload.get('kind') == NEW_KIND:
    return run_new(seed=int(payload.get('seed', 42)), ...)
```

Verify: python scripts/steward_audit.py -> PASS
(steward checks bidirectional coverage -- new kind in runner must also be in claim index)

### STEP 3 -- Write the test
Create: tests/<domain>/test_<claimid>_<name>.py

Minimum 3 tests:
  - pass case: result['result']['pass'] is True, metric within threshold
  - fail case: result['result']['pass'] is False (degraded inputs)
  - runner integration: create_job -> run_job -> status SUCCEEDED

### STEP 4 -- Add to scientific_claim_index.md

Append new section at bottom of reports/scientific_claim_index.md:

  ## CLAIM-ID
  | Field | Value |
  |-------|--------|
  | **claim_id** | CLAIM-ID |
  | **domain** | Your Domain |
  | **job_kind** | `your_job_kind` |
  | **reproduction** | `python -m pytest tests/<domain>/test_<claimid>.py -v` |
  | **V&V thresholds** | relative_error <= 0.02; result.pass is True. |
  | **notes (canary vs normal)** | job runs in normal or canary mode via run_job(..., canary_mode=...) |

CRITICAL: job_kind in backticks must exactly match JOB_KIND in your Python file.

### STEP 5 -- Update canonical_state.md
Find: | **current_claims_list** | MTR-1, ..., ML_BENCH-01 |
Replace: | **current_claims_list** | MTR-1, ..., ML_BENCH-01, CLAIM-ID |
Also append to merged_milestones.

### STEP 6 -- Update system_manifest.json
  "active_claims": ["MTR-1", ..., "ML_BENCH-01", "CLAIM-ID"]
  "domains": [..., "your_domain"]

### STEP 7 -- Update index.html
  7a. Nav dropdown: add claim link
  7b. Claims grid: add .claim card (.claimid, .claimdomain, .claimname, .claimth)
  7c. Governance terminal: update .tok lists with new claim ID
  7d. If previously (planned): change proto-rule -> proto-rule ok, remove (planned) span
  7e. Pricing: update 'all 7 claims' -> 'all 8 claims'

### STEP 8 -- Update known_faults.yaml
Run tests, update count:
  # Last updated: YYYY-MM-DD (steward_audit PASS, NN tests PASS)
  ci_impact: 'NONE -- NN tests pass, steward_audit PASS'

### STEP 9 -- Run full acceptance suite
```bash
python scripts/steward_audit.py
# -> STEWARD AUDIT: PASS

python -m pytest tests/ -q
# -> 0 failed

# Claim list consistency check
python -c "
import json
m = json.load(open('system_manifest.json'))
c = open('reports/canonical_state.md').read()
line = [l for l in c.split(chr(10)) if 'current_claims_list' in l][0]
print('manifest:', sorted(m['active_claims']))
print('canonical:', line)
"
# -> both must contain identical claim IDs

# Bidirectional coverage check
python -c "
import sys; sys.path.insert(0,'.')
from scripts.steward_audit import _extract_runner_dispatch_kinds, _extract_claim_index_job_kinds
rk = _extract_runner_dispatch_kinds()
ck = _extract_claim_index_job_kinds()
diff = rk.symmetric_difference(ck)
print('diff (must be empty set):', diff)
"
```

### STEP 10 -- Git commit
```bash
git add backend/progress/<new>.py backend/progress/runner.py
git add tests/<domain>/test_<new>.py
git add reports/scientific_claim_index.md reports/canonical_state.md
git add reports/known_faults.yaml system_manifest.json index.html
git commit -m 'feat: CLAIM-ID description -- claim, backend, test, index, canonical'
git push
```

---

## PART 3 - HOW TO UPDATE AN EXISTING CLAIM

### Changing a V&V threshold
1. Backend: update constant in backend/progress/<claim>.py
2. scientific_claim_index.md: update V&V thresholds row
3. index.html: update .claimth display value
4. Test: update threshold assertions in tests/<domain>/test_<claim>.py
5. python scripts/steward_audit.py -> PASS
6. python -m pytest tests/<domain>/ -v -> PASS

### Renaming a JOB_KIND (AVOID -- breaks existing evidence bundles)
If you must rename, update ALL atomically in one PR:
  - backend/progress/<module>.py :: JOB_KIND = 'new_name'
  - reports/scientific_claim_index.md :: job_kind backtick value
  - demos/open_data_demo_01/evidence_index.json :: 'job_kind' value
  - All affected test fixtures

---

## PART 4 - BANNED LANGUAGE (enforced in all files forever)

| Banned                          | Use instead                                              |
|---------------------------------|----------------------------------------------------------|
| tamper-proof                    | tamper-evident under trusted verifier assumptions        |
| 19x performance advantage       | cite with baseline reference only                        |
| 100% test success               | 91 tests PASS (exact count)                              |
| GPT-5 integration               | not in codebase                                          |
| 500+ modules                    | not verified                                             |
| proto-rule ok on planned feats  | proto-rule class + (planned) span                        |
| impossible to forge / unforgeable | tamper-evident under trusted verifier assumptions      |

---

## PART 5 - FILE RESPONSIBILITY MAP

  backend/progress/<claim>.py          -> claim logic, JOB_KIND constant
  backend/progress/runner.py           -> dispatch (Patent Claim 4) -- minimal changes only
  scripts/steward_audit.py             -> audit logic (Patent Claim 1) -- DO NOT TOUCH
  scripts/mg.py                        -> verify logic (Patent Claim 2) -- DO NOT TOUCH
  scripts/mg_policy_gate_policy.json   -> SEALED -- 5 locked paths
  reports/canonical_state.md           -> SEALED -- update claims list only
  reports/scientific_claim_index.md    -> SEALED -- append new sections only
  reports/known_faults.yaml            -> update test count after adding tests
  system_manifest.json                 -> update active_claims + domains
  demos/open_data_demo_01/             -> update evidence if demo regenerated
  index.html                           -> nav, claims grid, governance block, pricing
  tests/<domain>/test_<claim>.py       -> claim-specific tests
  .github/workflows/mg_policy_gate.yml -> DO NOT TOUCH

---

## PART 6 - STEWARD AUDIT MECHANICS

python scripts/steward_audit.py checks:
  1. Required files exist
  2. Phase registry JSON valid + phase 42 locked
  3. Bidirectional coverage: every JOB_KIND in runner has entry in scientific_claim_index AND vice versa
  4. Canonical sync: current_claims_list in canonical_state matches all claim_id in scientific_claim_index

If steward_audit FAILS after your change:
  'Kind(s) in runner but missing from scientific_claim_index'
  -> add job_kind to scientific_claim_index.md

  'job_kind(s) in claim_index but not dispatched in runner'
  -> add dispatch block to runner.py

  'Claims in canonical_state but missing from scientific_claim_index'
  -> add ## CLAIM-ID section to scientific_claim_index.md

---

## PART 7 - QUICK REFERENCE CHECKLIST

Minimum viable new claim:
  [ ] backend/progress/<id>_<n>.py        JOB_KIND + run function + deterministic
  [ ] backend/progress/runner.py           dispatch block added
  [ ] tests/<domain>/test_<id>_<n>.py     3 tests: pass, fail, runner integration
  [ ] reports/scientific_claim_index.md    new ## CLAIM-ID section (job_kind in backticks)
  [ ] reports/canonical_state.md           claim_id appended to current_claims_list
  [ ] reports/known_faults.yaml            test count updated
  [ ] system_manifest.json                 active_claims + domains updated
  [ ] index.html                           nav, grid, governance, pricing, (planned) removed
  [ ] python scripts/steward_audit.py      -> PASS
  [ ] python -m pytest tests/ -q           -> 0 failed
  [ ] git commit + push

Key PPA constants (never change without patent attorney):
  backend/progress/runner.py:
    legal_sig_refs = ['metagenesis-core-ppa-63996819']  # in every ledger entry

  scripts/mg.py :: _verify_semantic() checks:
    trace_id, job_snapshot, canary_mode, mtr_phase, payload.kind == evidence_index.job_kind

---

*MetaGenesis Core -- Proof, Not Trust*
*PPA 63/996,819 | Inventor: Yehor Bazhynov | 2026-03-08*
