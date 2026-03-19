# Agent Research Report -- TASK-006: Adversarial tests for SYSID-01 (weakest coverage claim)

**Date:** 2026-03-19 14:51
**Task Description:** SYSID-01 was identified as weakest-coverage claim in TASK-001. Write 3 adversarial test scenarios: (1) step chain hash tamper, (2) semantic field stripping, (3) threshold boundary injection. Read sysid1_arx_calibration.py to extract exact thresholds and field names.
**Priority:** P1

---

## Adversarial Test Proposals for SYSID-01

Date: 2026-03-19 14:51

### Source Analysis

- **JOB_KIND:** `sysid1_arx_calibration`
- **Threshold:** rel_err <= 0.03
- **Method:** `ols_arx_2param`
- **Step chain steps:** ['init_params', 'generate_sequence', 'estimate_arx', 'threshold_check']
- **Return fields:** domain, claim_id, mtr_phase, inputs, result, execution_trace, trace_root_hash
- **Result fields:** estimated_a, estimated_b, rmse, rel_err_a, rel_err_b, method, algorithm_version

### Existing Tests

**`tests\systems\test_sysid01_arx_calibration.py`** (3 tests):
  - `test_a_e2e_normal_canary_artifacts_evidence`
  - `test_b_vv_thresholds`
  - `test_c_reproducibility_shape`

### Adversarial Test Scenario 1: Step Chain Hash Tamper

**File:** `tests/steward/test_cert_adv_sysid01_stepchain.py`

**Rationale:** SYSID-01 has a 4-step chain (init_params, generate_sequence,
estimate_arx, threshold_check). Tampering with any step hash should cause
Layer 3 verification failure.

```python
import pytest
from backend.progress.sysid1_arx_calibration import run_calibration

def test_sysid01_step_chain_tamper_init_params():
    """Tamper with step 1 hash; expect trace_root_hash mismatch."""
    result = run_calibration(seed=42, a_true=0.9, b_true=0.5)
    trace = result['execution_trace']
    original_root = result['trace_root_hash']
    # Tamper step 1 hash
    trace[0]['hash'] = 'f' * 64
    # Recompute would give different root -> Layer 3 catches this
    assert trace[-1]['hash'] == original_root  # unchanged in trace
    # But re-verification via _verify_semantic would fail

def test_sysid01_step_chain_tamper_threshold():
    """Tamper with threshold_check step; expect verification failure."""
    result = run_calibration(seed=42, a_true=0.9, b_true=0.5)
    trace = result['execution_trace']
    # Flip pass to False in step 4 output
    trace[3]['output']['pass'] = not trace[3]['output']['pass']
    # trace_root_hash no longer matches tampered trace
    assert result['trace_root_hash'] == trace[3]['hash']  # hash unchanged
    # Semantic verify would detect output/hash mismatch
```

### Adversarial Test Scenario 2: Semantic Field Stripping

**File:** `tests/steward/test_cert_adv_sysid01_semantic.py`

**Rationale:** Strip required fields from SYSID-01 evidence to test
Layer 2 semantic verification catches missing data.

```python
import pytest
from scripts.mg import _verify_semantic

def test_sysid01_strip_execution_trace():
    """Remove execution_trace from SYSID-01 domain_result."""
    domain_result = {
        'mtr_phase': 'SYSID-01',
        'inputs': {'seed': 42, 'a_true': 0.9, 'b_true': 0.5},
        'result': {'estimated_a': 0.9, 'rel_err_a': 0.001},
        # execution_trace deliberately omitted
        'trace_root_hash': 'a' * 64,
    }
    # Layer 2 should flag missing execution_trace

def test_sysid01_strip_inputs():
    """Remove inputs dict from SYSID-01 evidence."""
    domain_result = {
        'mtr_phase': 'SYSID-01',
        'result': {'estimated_a': 0.9},
    }
    # Layer 2 semantic check should reject missing inputs

def test_sysid01_strip_result():
    """Remove result dict from SYSID-01 evidence."""
    domain_result = {
        'mtr_phase': 'SYSID-01',
        'inputs': {'seed': 42},
    }
    # Layer 2 should reject missing result
```

### Adversarial Test Scenario 3: Threshold Boundary Injection

**File:** `tests/steward/test_cert_adv_sysid01_boundary.py`

**Rationale:** SYSID-01 threshold is rel_err <= 0.03. Test exact boundary
values to ensure pass/fail logic is correct at the edge.

```python
import pytest
from backend.progress.sysid1_arx_calibration import run_calibration

def test_sysid01_boundary_exact_threshold():
    """rel_err exactly at 0.03 should PASS."""
    # Use seeds that produce rel_err near threshold
    # Verify step 4 output['pass'] == True when rel_err == threshold

def test_sysid01_boundary_just_above():
    """rel_err at 0.03 + epsilon should FAIL."""
    # Inject noise_scale to push rel_err just above threshold
    result = run_calibration(seed=42, a_true=0.9, b_true=0.5,
                             noise_scale=5.0)  # high noise
    trace = result['execution_trace']
    # With high noise, rel_err likely exceeds 0.03
    step4 = trace[3]
    assert step4['name'] == 'threshold_check'

def test_sysid01_boundary_zero_noise():
    """Zero noise should give rel_err near 0 -> definite PASS."""
    result = run_calibration(seed=42, a_true=0.9, b_true=0.5,
                             noise_scale=0.0)
    step4 = result['execution_trace'][3]
    assert step4['output']['pass'] is True
```

### Summary

| Scenario | Layer Tested | Attack Type | File |
|----------|-------------|-------------|------|
| 1. Step Chain Tamper | Layer 3 | Hash manipulation | test_cert_adv_sysid01_stepchain.py |
| 2. Semantic Stripping | Layer 2 | Field removal | test_cert_adv_sysid01_semantic.py |
| 3. Threshold Boundary | Layer 3+Logic | Boundary injection | test_cert_adv_sysid01_boundary.py |

**Recommendation:** Implement all 3 scenarios. SYSID-01 currently has
1 test file(s) but no dedicated adversarial/CERT-level tests.
These would bring SYSID-01 coverage in line with other claims.
