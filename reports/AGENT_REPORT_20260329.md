# Agent Report — 2026-03-29

## TASK-019: Coverage Audit for MTR-4, MTR-5, MTR-6

### Test Function Count

| Claim | Test File | Functions | Status |
|-------|-----------|-----------|--------|
| MTR-4 | `tests/materials/test_mtr4_titanium.py` | 3 | PASS |
| MTR-5 | `tests/materials/test_mtr5_steel.py` | 3 | PASS |
| MTR-6 | `tests/materials/test_mtr6_copper.py` | 3 | PASS |

**Total: 9 test functions across 3 files.**

### Test Breakdown Per Claim

Each claim follows the standard 3-test pattern:

1. **test_a_e2e_create_run_normal_canary_artifacts_evidence** — end-to-end proof-loop with canary mode validation, artifact persistence checks, evidence API integration
2. **test_b_vv_relative_error_threshold** — V&V threshold assertion against NIST physical anchor
3. **test_c_reproducibility_same_payload_twice_shape_matches** — deterministic reproducibility (structure-level, excluding non-deterministic fields)

### Physical Anchor Thresholds Verified

| Claim | Material | Property | NIST Value | V&V Threshold | Algorithm |
|-------|----------|----------|------------|---------------|-----------|
| MTR-4 | Ti-6Al-4V (Titanium) | Young's Modulus (E) | 114 GPa | rel_err ≤ 0.01 (1%) | OLS through origin |
| MTR-5 | SS316L (Stainless Steel) | Young's Modulus (E) | 193 GPa | rel_err ≤ 0.01 (1%) | OLS through origin |
| MTR-6 | Cu (Copper) | Thermal Conductivity (k) | 401 W/(m·K) | rel_err ≤ 0.02 (2%) | OLS through origin |

**Code references:**
- MTR-4 threshold: `backend/progress/mtr4_titanium_calibration.py:179` → `relative_error <= 0.01`
- MTR-5 threshold: `backend/progress/mtr5_steel_calibration.py:179` → `relative_error <= 0.01`
- MTR-6 threshold: `backend/progress/mtr6_copper_conductivity.py:113` → `relative_error <= 0.02`

### Adversarial Test Gaps

**No critical gaps found.** All three claims have:
- E2E artifact tests (normal + canary mode)
- V&V threshold checks with NIST anchors
- Reproducibility tests

**Proposed additional adversarial tests (optional, P3):**
- High-noise calibration: increase `noise_scale` to stress-test threshold margins
- Boundary seeds: test with adversarial seeds that maximize error
- Zero/negative input rejection: verify payload validation for invalid E_true/k_true values

---

## TASK-020: Claim Dependency Graph Update

### Current Dependency Graph (18 claims)

```
MTR-1 ──→ DRIFT-01 ──→ DT-CALIB-LOOP-01
MTR-1 ──→ DT-FEM-01
ML_BENCH-01 ──→ ML_BENCH-02
ML_BENCH-01 ──→ ML_BENCH-03

Standalone (no inbound/outbound):
  MTR-2, MTR-3, MTR-4, MTR-5, MTR-6
  SYSID-01, DATA-PIPE-01
  PHARMA-01, FINRISK-01
  DT-SENSOR-01, AGENT-DRIFT-01
```

### MTR-4/5/6 Dependency Status

MTR-4, MTR-5, MTR-6 are **base-layer physical anchor claims** with:
- **0 upstream dependencies** — they depend on nothing
- **0 downstream dependents** — no other claim references them as anchors (yet)

**Note:** DRIFT-01 accepts configurable `anchor_claim_id` (default: MTR-1). MTR-4/5/6 could serve as alternative drift anchors for domain-specific monitoring (e.g., titanium drift in aerospace pipelines).

### Recommendation

No graph update needed — MTR-4/5/6 are correctly isolated as independent base claims. When domain-specific drift monitoring is added, these can become upstream anchors.

---

## TASK-021: scientific_claim_index.md Verification

### Status: ALL PRESENT

| Claim | Listed | Location | Thresholds Correct |
|-------|--------|----------|--------------------|
| MTR-4 | YES | lines 369-379 | rel_err ≤ 0.01, E = 114 GPa Ti-6Al-4V (NIST) |
| MTR-5 | YES | lines 382-392 | rel_err ≤ 0.01, E = 193 GPa SS316L (NIST) |
| MTR-6 | YES | lines 395-405 | rel_err ≤ 0.02, k = 401 W/(m·K) Cu (NIST) |

All entries include:
- Correct `claim_id`, `domain`, `job_kind`
- Reproduction command (`python -m pytest tests/materials/test_mtrX_*.py -v`)
- V&V thresholds matching backend code
- Application domain notes

**system_manifest.json:** All three present in `active_claims` array (18 total).

**No fixes needed.**
