# Agent Research Report -- TASK-001: Audit test coverage per all 14 claims

**Date:** 2026-03-18 20:18
**Task Description:** For each of the 14 active claims (MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01), count test files and test functions. Find the claim with weakest coverage. Propose 3 new adversarial tests.
**Priority:** P1

---

## Test Coverage Audit -- All 14 Claims

Date: 2026-03-18 20:18

### Coverage Table

| Claim | Impl File | Test Files | Test Functions |
|-------|-----------|------------|----------------|
| MTR-1 | `backend/progress/mtr1_calibration.py` | 16 | 182 |
| MTR-2 | `backend/progress/mtr2_thermal_conductivity.py` | 5 | 102 |
| MTR-3 | `backend/progress/mtr3_thermal_multilayer.py` | 4 | 99 |
| SYSID-01 | `backend/progress/sysid1_arx_calibration.py` | 3 | 97 |
| DATA-PIPE-01 | `backend/progress/datapipe1_quality_certificate.py` | 4 | 109 |
| DRIFT-01 | `backend/progress/drift_monitor.py` | 9 | 165 |
| ML_BENCH-01 | `backend/progress/mlbench1_accuracy_certificate.py` | 18 | 272 |
| DT-FEM-01 | `backend/progress/dtfem1_displacement_verification.py` | 12 | 203 |
| ML_BENCH-02 | `backend/progress/mlbench2_regression_certificate.py` | 3 | 109 |
| ML_BENCH-03 | `backend/progress/mlbench3_timeseries_certificate.py` | 3 | 105 |
| PHARMA-01 | `backend/progress/pharma1_admet_certificate.py` | 4 | 111 |
| FINRISK-01 | `backend/progress/finrisk1_var_certificate.py` | 3 | 103 |
| DT-SENSOR-01 | `backend/progress/dtsensor1_iot_certificate.py` | 3 | 105 |
| DT-CALIB-LOOP-01 | `backend/progress/dtcalib1_convergence_certificate.py` | 4 | 118 |
| **TOTAL** | | **91** | **1880** |

### Weakest Claim: SYSID-01

- **Implementation:** `backend/progress/sysid1_arx_calibration.py`
- **Test files:** 3
- **Test functions:** 97
- **Files:**
  - `tests\steward\test_cert08_reproducibility.py` (10 tests)
  - `tests\steward\test_step_chain_all_claims.py` (84 tests)
  - `tests\systems\test_sysid01_arx_calibration.py` (3 tests)

### Proposed Adversarial Tests

The following 3 adversarial tests target **SYSID-01**:

**1. Step Chain Hash Tampering Test**
- Modify `trace_root_hash` in SYSID-01's execution trace
- Expect: Layer 3 (Step Chain) catches the tampered hash
- File: `tests/steward/test_cert_adv_sysid_01_stepchain.py`
- Asserts: verification returns FAIL with step chain mismatch detail

**2. Semantic Field Stripping Test**
- Remove a required field from SYSID-01's evidence bundle
- Expect: Layer 2 (Semantic) catches the missing field
- File: `tests/steward/test_cert_adv_sysid_01_semantic.py`
- Asserts: `_verify_semantic()` raises on null/missing evidence

**3. Bundle Replay with New Timestamp Test**
- Take a valid SYSID-01 bundle, modify its timestamp to future date
- Expect: Layer 5 (Temporal) catches the backdated/replayed bundle
- File: `tests/steward/test_cert_adv_sysid_01_temporal.py`
- Asserts: temporal commitment verification fails

### Detailed File Listing

**MTR-1:**
  - `tests\cli\test_verify_json01_report.py` (3 test functions)
  - `tests\materials\test_data01_dataset_fingerprint.py` (2 test functions)
  - `tests\materials\test_mtr1_youngs_modulus.py` (3 test functions)
  - `tests\materials\test_uq01_mtr1_uncertainty.py` (5 test functions)
  - `tests\steward\test_cert02_pack_includes_evidence_and_semantic_verify.py` (13 test functions)
  - `tests\steward\test_cert04_anchor_hash_verify.py` (4 test functions)
  - `tests\steward\test_cert05_adversarial_gauntlet.py` (6 test functions)
  - `tests\steward\test_cert06_real_world_scenarios.py` (5 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_cross_claim_chain.py` (15 test functions)
  - `tests\steward\test_drift01_calibration_anchor.py` (16 test functions)
  - `tests\steward\test_runner_error_paths.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\steward\test_stew03_dossier_builder.py` (2 test functions)
  - `tests\steward\test_stew04_submission_pack.py` (3 test functions)
  - `tests\steward\test_stew05_pack_includes_all_claims.py` (1 test functions)

**MTR-2:**
  - `tests\materials\test_mtr2_thermal_paste_conductivity.py` (3 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\steward\test_stew03_dossier_builder.py` (2 test functions)
  - `tests\steward\test_stew04_submission_pack.py` (3 test functions)

**MTR-3:**
  - `tests\materials\test_mtr3_thermal_multilayer.py` (3 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\steward\test_stew06_canonical_truth_consistency.py` (2 test functions)

**SYSID-01:**
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\systems\test_sysid01_arx_calibration.py` (3 test functions)

**DATA-PIPE-01:**
  - `tests\data\test_datapipe01_quality_certificate.py` (3 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\steward\test_stew08_documentation_drift.py` (12 test functions)

**DRIFT-01:**
  - `tests\digital_twin\test_dtcalib1_convergence_certificate.py` (9 test functions)
  - `tests\progress\test_progress_store.py` (8 test functions)
  - `tests\steward\test_cert05_adversarial_gauntlet.py` (6 test functions)
  - `tests\steward\test_cert06_real_world_scenarios.py` (5 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_cross_claim_chain.py` (15 test functions)
  - `tests\steward\test_drift01_calibration_anchor.py` (16 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\steward\test_stew08_documentation_drift.py` (12 test functions)

**ML_BENCH-01:**
  - `tests\cli\test_real_data_e2e.py` (13 test functions)
  - `tests\ml\test_mlbench01_accuracy_certificate.py` (28 test functions)
  - `tests\ml\test_mlbench01_realdata.py` (18 test functions)
  - `tests\ml\test_mlbench02_regression_certificate.py` (15 test functions)
  - `tests\steward\test_cert03_step_chain_verify.py` (10 test functions)
  - `tests\steward\test_cert05_adversarial_gauntlet.py` (6 test functions)
  - `tests\steward\test_cert06_real_world_scenarios.py` (5 test functions)
  - `tests\steward\test_cert07_bundle_signing.py` (13 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_cert09_ed25519_attacks.py` (6 test functions)
  - `tests\steward\test_cert10_temporal_attacks.py` (6 test functions)
  - `tests\steward\test_cert11_coordinated_attack.py` (6 test functions)
  - `tests\steward\test_cert12_encoding_attacks.py` (9 test functions)
  - `tests\steward\test_cert_5layer_independence.py` (6 test functions)
  - `tests\steward\test_runner_error_paths.py` (10 test functions)
  - `tests\steward\test_signing_upgrade.py` (15 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)
  - `tests\steward\test_stew08_documentation_drift.py` (12 test functions)

**DT-FEM-01:**
  - `tests\cli\test_real_data_e2e.py` (13 test functions)
  - `tests\digital_twin\test_dtfem01_displacement_verification.py` (16 test functions)
  - `tests\digital_twin\test_dtfem01_realdata.py` (19 test functions)
  - `tests\steward\test_cert02_pack_includes_evidence_and_semantic_verify.py` (13 test functions)
  - `tests\steward\test_cert04_anchor_hash_verify.py` (4 test functions)
  - `tests\steward\test_cert05_adversarial_gauntlet.py` (6 test functions)
  - `tests\steward\test_cert06_real_world_scenarios.py` (5 test functions)
  - `tests\steward\test_cert07_bundle_signing.py` (13 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_cross_claim_chain.py` (15 test functions)
  - `tests\steward\test_manifest_rollback.py` (5 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

**ML_BENCH-02:**
  - `tests\ml\test_mlbench02_regression_certificate.py` (15 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

**ML_BENCH-03:**
  - `tests\ml\test_mlbench03_timeseries_certificate.py` (11 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

**PHARMA-01:**
  - `tests\ml\test_pharma01_admet_certificate.py` (11 test functions)
  - `tests\steward\test_cert05_adversarial_gauntlet.py` (6 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

**FINRISK-01:**
  - `tests\ml\test_finrisk01_var_certificate.py` (9 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

**DT-SENSOR-01:**
  - `tests\digital_twin\test_dtsensor01_iot_certificate.py` (11 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

**DT-CALIB-LOOP-01:**
  - `tests\digital_twin\test_dtcalib1_convergence_certificate.py` (9 test functions)
  - `tests\steward\test_cert08_reproducibility.py` (10 test functions)
  - `tests\steward\test_cross_claim_chain.py` (15 test functions)
  - `tests\steward\test_step_chain_all_claims.py` (84 test functions)

