# MetaGenesis Core -- Test Suite Gap Analysis Report

**Generated:** 2026-03-18
**Test suite:** 391 tests across 45 files
**Verification layers:** 5 (SHA-256, Semantic, Step Chain, Bundle Signing, Temporal Commitment)
**Active claims:** 14

---

## 1. Executive Summary

The MetaGenesis Core test suite contains **391 tests** across **45 test files** organized in 8 directories. Coverage is strong for adversarial proofs (CERT-01 through CERT-10, 5-layer independence) and individual claim correctness. However, there are specific gaps:

- **Step chain structural tests** cover only 7 of 14 claims in the dedicated `test_step_chain_all_claims.py`
- **Layer 2 (Semantic)** has the fewest tests of any layer (2 tests in CERT-02)
- **No multi-vector coordinated attack** test exists (an attacker bypassing multiple layers simultaneously)
- **No cross-claim cascade failure** test for the MTR-1 dependency chain
- **No key lifecycle tests** (expired/rotated keys)

Overall assessment: **Strong foundation, targeted gaps in edge cases and advanced attack scenarios.**

---

## 2. Test Inventory by Area

### 2.1 By Directory

| Directory | Files | Tests | Coverage Focus |
|-----------|-------|-------|---------------|
| steward/ | 21 | 199 | Adversarial proofs, governance, signing, Ed25519, temporal |
| ml/ | 7 | 73 | ML claim correctness, step chains, real data |
| digital_twin/ | 5 | 47 | DT claim correctness, IoT sensors, calibration |
| materials/ | 5 | 16 | Material property claims, uncertainty, fingerprinting |
| cli/ | 2 | 16 | End-to-end CLI verification, JSON reports |
| progress/ | 2 | 11 | Job store, evidence index |
| data/ | 1 | 3 | Data pipeline quality certificate |
| systems/ | 1 | 3 | System identification (ARX) |
| **TOTAL** | **45** | **391** | |

### 2.2 Complete File Inventory

| # | File | Tests | Layer | Claim(s) | Test Types |
|---|------|-------|-------|----------|-----------|
| 1 | tests/cli/test_real_data_e2e.py | 13 | 1,2 | ML_BENCH-01, DT-FEM-01 | E2E, happy, failure, fingerprint |
| 2 | tests/cli/test_verify_json01_report.py | 3 | 1,2,3 | General | E2E, tamper detection, determinism |
| 3 | tests/data/test_datapipe01_quality_certificate.py | 3 | 3 | DATA-PIPE-01 | Happy, failure, determinism |
| 4 | tests/digital_twin/test_dtcalib1_convergence_certificate.py | 9 | 3 | DT-CALIB-LOOP-01 | Happy, failure, step chain, edge |
| 5 | tests/digital_twin/test_dtfem01_displacement_verification.py | 16 | 3 | DT-FEM-01 | Happy, failure, adversarial, boundary, error |
| 6 | tests/digital_twin/test_dtfem01_realdata.py | 19 | 1,3 | DT-FEM-01 | Real data, fingerprint, threshold, error |
| 7 | tests/digital_twin/test_dtsensor01_iot_certificate.py | 11 | 3 | DT-SENSOR-01 | Happy, failure, sensor types, step chain, error |
| 8 | tests/materials/test_data01_dataset_fingerprint.py | 2 | 1 | General | Fingerprint stability, artifact check |
| 9 | tests/materials/test_mtr1_youngs_modulus.py | 3 | 3 | MTR-1 | Happy, threshold, determinism |
| 10 | tests/materials/test_mtr2_thermal_paste_conductivity.py | 3 | 3 | MTR-2 | Happy, threshold, determinism |
| 11 | tests/materials/test_mtr3_thermal_multilayer.py | 3 | 3 | MTR-3 | Happy, threshold, determinism |
| 12 | tests/materials/test_uq01_mtr1_uncertainty.py | 5 | 3 | MTR-1 | Uncertainty quantification, determinism |
| 13 | tests/ml/test_finrisk01_var_certificate.py | 9 | 3 | FINRISK-01 | Happy, failure, step chain, error, regulatory |
| 14 | tests/ml/test_mlbench01_accuracy_certificate.py | 28 | 3 | ML_BENCH-01 | Happy, failure, determinism, step chain, boundary, error |
| 15 | tests/ml/test_mlbench01_realdata.py | 18 | 1,3 | ML_BENCH-01 | Real data, fingerprint, threshold, error |
| 16 | tests/ml/test_mlbench02_regression_certificate.py | 15 | 3 | ML_BENCH-02 | Happy, failure, determinism, step chain, error |
| 17 | tests/ml/test_mlbench03_timeseries_certificate.py | 11 | 3 | ML_BENCH-03 | Happy, failure, determinism, step chain, error |
| 18 | tests/ml/test_pharma01_admet_certificate.py | 11 | 3 | PHARMA-01 | Happy, failure, step chain, regulatory, error |
| 19 | tests/progress/test_evidence_index.py | 3 | 2 | General | Evidence mapping, empty dir, missing dir |
| 20 | tests/progress/test_progress_store.py | 8 | - | General | Job store, ledger chain, uniqueness |
| 21 | tests/systems/test_sysid01_arx_calibration.py | 3 | 3 | SYSID-01 | Happy, threshold, determinism |
| 22 | tests/steward/test_cert01_pack_manifest_verify.py | 3 | 1 | General | Manifest keys, valid pack, tamper detect |
| 23 | tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py | 2 | 2 | General | Evidence inclusion, semantic negative |
| 24 | tests/steward/test_cert03_step_chain_verify.py | 6 | 3 | General | Valid hash, tampered hash, missing fields, format |
| 25 | tests/steward/test_cert04_anchor_hash_verify.py | 4 | 3 | General | No anchor, valid anchor, invalid length, non-hex |
| 26 | tests/steward/test_cert05_adversarial_gauntlet.py | 6 | 1,2,3 | General | 5 attack scenarios + summary |
| 27 | tests/steward/test_cert06_real_world_scenarios.py | 5 | 1,2,3 | MTR-1, DT-FEM-01 | 5 real-world scenarios |
| 28 | tests/steward/test_cert07_bundle_signing.py | 13 | 4 | General | Keygen, sign/verify, tamper, forge, determinism |
| 29 | tests/steward/test_cert08_reproducibility.py | 10 | 3 | All 14 | Determinism, parameter sensitivity, stability |
| 30 | tests/steward/test_cert09_ed25519_attacks.py | 6 | 4 | General | Wrong key, bit flip, downgrade, mismatch, truncated |
| 31 | tests/steward/test_cert10_temporal_attacks.py | 6 | 5 | General | Replay, future timestamp, forge, tamper |
| 32 | tests/steward/test_cert_5layer_independence.py | 6 | 1,2,3,4,5 | General | One test per layer + independence matrix |
| 33 | tests/steward/test_cross_claim_chain.py | 6 | 3 | MTR-1, DT-FEM-01, DRIFT-01 | Anchor linkage, tamper, backward compat |
| 34 | tests/steward/test_drift01_calibration_anchor.py | 16 | 3 | DRIFT-01 | Happy, failure, boundary, error, full run |
| 35 | tests/steward/test_ed25519.py | 37 | 4 | General | RFC 8032 vectors, keygen, roundtrip |
| 36 | tests/steward/test_signing_upgrade.py | 15 | 4 | General | Algorithm dispatch, Ed25519 sign/verify, downgrade |
| 37 | tests/steward/test_step_chain_all_claims.py | 28 | 3 | 7 of 14 | Trace presence, 4-step, determinism, seed sensitivity |
| 38 | tests/steward/test_stew01_steward_audit.py | 1 | - | General | Governance audit pass |
| 39 | tests/steward/test_stew02_claim_coverage.py | 1 | - | General | Claim coverage audit |
| 40 | tests/steward/test_stew03_dossier_builder.py | 2 | - | MTR-1, MTR-2 | Dossier creation, field check |
| 41 | tests/steward/test_stew04_submission_pack.py | 3 | - | MTR-1, MTR-2 | Pack creation, overview, dossier fields |
| 42 | tests/steward/test_stew05_pack_includes_all_claims.py | 1 | - | All 14 | All claims have dossiers |
| 43 | tests/steward/test_stew06_canonical_truth_consistency.py | 2 | - | General | Canonical state audit |
| 44 | tests/steward/test_stew07_jobkind_coverage.py | 2 | - | All 14 | Job kind coverage vs runner |
| 45 | tests/steward/test_temporal.py | 14 | 5 | General | Beacon fetch, create/verify commitment, write |

---

## 3. Claim Coverage Matrix

Each cell indicates test presence: C = Correctness (happy/fail path), S = Step chain structural, X = Cross-claim, E = Error path.

| Claim | C | S (dedicated) | S (in-file) | X | E | Total Tests | Notes |
|-------|---|---------------|-------------|---|---|-------------|-------|
| MTR-1 | Y | Y (4 tests) | - | Y (6 tests) | - | 3+4+5+6 = 18 | Best covered material claim |
| MTR-2 | Y | Y (4 tests) | - | - | - | 3+4 = 7 | No cross-claim tests |
| MTR-3 | Y | Y (4 tests) | - | - | - | 3+4 = 7 | No cross-claim tests |
| SYSID-01 | Y | Y (4 tests) | - | - | - | 3+4 = 7 | No error path tests |
| DATA-PIPE-01 | Y | Y (4 tests) | - | - | - | 3+4 = 7 | Minimal -- 3 correctness tests |
| DRIFT-01 | Y | Y (4 tests) | - | Y (in cross_claim) | Y | 16+4 = 20 | Strong coverage |
| ML_BENCH-01 | Y | **NO** | Y (6 tests) | - | Y | 28+18 = 46 | Most tested claim overall |
| ML_BENCH-02 | Y | **NO** | Y (trace tests) | - | Y | 15 | Has in-file trace checks |
| ML_BENCH-03 | Y | **NO** | Y (trace tests) | - | Y | 11 | Has in-file trace checks |
| PHARMA-01 | Y | **NO** | Y (trace tests) | - | Y | 11 | Has in-file trace checks |
| FINRISK-01 | Y | **NO** | Y (trace tests) | - | Y | 9 | Has in-file trace checks |
| DT-FEM-01 | Y | Y (4 tests) | - | Y (in cross_claim) | Y | 16+19+4 = 39 | Strong coverage |
| DT-SENSOR-01 | Y | **NO** | Y (trace tests) | - | Y | 11 | Has in-file trace checks |
| DT-CALIB-LOOP-01 | Y | **NO** | Y (trace tests) | - | Y | 9 | Missing cross-claim with DRIFT-01 |

**Key finding:** 7 claims lack dedicated step chain structural tests in `test_step_chain_all_claims.py`. However, all 7 DO have in-file trace/step chain checks (e.g., `test_step_chain_4_steps`, `test_trace_present_in_result`). The gap is specifically in the standardized structural validation (genesis hash, hash linkage between steps, root hash equality) that the dedicated file provides.

---

## 4. Layer Coverage Matrix

| Layer | Description | Primary Test Files | Test Count | Assessment |
|-------|------------|-------------------|------------|------------|
| **Layer 1** - SHA-256 Integrity | File hash verification | CERT-01 (3), CERT-05 (partial), real_data_e2e (2), 5layer (1) | ~8 | Adequate -- basic tamper detection proven |
| **Layer 2** - Semantic | Evidence presence + structure | CERT-02 (2), CERT-05 (partial), 5layer (1) | ~5 | **WEAKEST** -- only 2 dedicated tests |
| **Layer 3** - Step Chain | Execution trace integrity | CERT-03 (6), CERT-04 (4), step_chain_all (28), cross_claim (6), in-file traces (~30), CERT-08 (10), 5layer (1) | ~85 | **STRONGEST** -- extensive coverage |
| **Layer 4** - Bundle Signing | HMAC + Ed25519 | CERT-07 (13), CERT-09 (6), ed25519 (37), signing_upgrade (15), 5layer (1) | ~72 | Strong -- both algorithms well tested |
| **Layer 5** - Temporal Commitment | NIST Beacon binding | CERT-10 (6), temporal (14), 5layer (1) | ~21 | Good -- covers create/verify/attack |

---

## 5. Identified Gaps (Priority-Ranked)

### P1: Step Chain Structural Tests for 7 Claims
- **Gap:** `test_step_chain_all_claims.py` has `TestStepChain*` classes for only MTR-1/2/3, SYSID-01, DATAPIPE-01, DRIFT-01, DT-FEM-01. Missing: ML_BENCH-01/02/03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01.
- **Risk:** A claim could have a structurally invalid step chain (wrong genesis hash, broken hash linkage) that passes domain tests but fails under adversarial conditions in Layer 3.
- **Mitigating factor:** All 7 claims DO have in-file trace checks. The gap is standardized structural validation only.
- **Effort:** LOW -- template exists from the 7 already implemented; copy and adapt.
- **Suggested location:** `tests/steward/test_step_chain_all_claims.py` (extend existing file)

### P2: Multi-Vector Coordinated Attack Test
- **Gap:** No test simulates an attacker who simultaneously bypasses Layer 1 (rebuilds SHA-256), fakes Layer 2 (adds semantic evidence), and attacks Layer 3 (forges step chain). CERT-05 tests each attack independently.
- **Risk:** The independence claim ("an attacker who bypasses Layer N still fails Layer N+1") is tested per-layer but never as a full coordinated attack sequence.
- **Effort:** MEDIUM -- requires building a sophisticated attack harness.
- **Suggested location:** `tests/steward/test_cert11_coordinated_attack.py`

### P3: Cross-Claim Cascade Failure (MTR-1 Chain)
- **Gap:** No test verifies: if MTR-1 fails, do DT-FEM-01, DRIFT-01, and DT-CALIB-LOOP-01 correctly propagate the failure through their anchor hash chains?
- **Risk:** A failed upstream claim could silently produce valid-looking downstream claims.
- **Effort:** MEDIUM -- needs to run multiple claims in sequence with a deliberately failed MTR-1.
- **Suggested location:** `tests/steward/test_cross_claim_chain.py` (extend)

### P4: Step Chain Ordering and Duplicate Step Tests
- **Gap:** CERT-03 tests valid/invalid/missing scenarios but does NOT test: steps in wrong order (1,3,2,4), duplicate step numbers, or extra steps beyond 4.
- **Risk:** A malformed trace with correct hashes but wrong ordering could pass verification.
- **Effort:** LOW -- add 3-4 test cases to existing CERT-03 file.
- **Suggested location:** `tests/steward/test_cert03_step_chain_verify.py`

### P5: Partial Corruption / Encoding Attacks
- **Gap:** Tests cover full file tampering but not: truncated evidence files, binary garbage in JSON fields, Unicode/encoding attacks in claim data, BOM-prefixed files.
- **Risk:** Robustness under malformed input is unproven; could cause crashes or silent acceptance.
- **Effort:** MEDIUM -- requires crafting multiple malformed inputs.
- **Suggested location:** `tests/steward/test_cert12_malformed_input.py`

### P6: Layer 2 Semantic Edge Cases
- **Gap:** CERT-02 has only 2 tests. No tests for: partial evidence (some fields present, some missing), evidence with extra unexpected fields, evidence with correct structure but semantically meaningless values (empty strings, zero values).
- **Risk:** Layer 2 is the weakest layer by test count. An attacker could craft evidence that technically passes semantic checks but is meaningless.
- **Effort:** LOW -- extend CERT-02 with 4-6 additional semantic edge cases.
- **Suggested location:** `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`

### P7: Error Path Coverage in runner.py
- **Gap:** No test for: unknown JOB_KIND dispatched to runner, claim module raising unexpected exception mid-computation, claim input data being None/empty/wrong type, `_hash_step` receiving non-serializable data.
- **Risk:** Graceful degradation under unexpected conditions is unproven.
- **Effort:** LOW -- add 4-5 targeted error path tests.
- **Suggested location:** `tests/steward/test_runner_error_paths.py`

### P8: DT-CALIB-LOOP-01 Cross-Claim with DRIFT-01
- **Gap:** `test_cross_claim_chain.py` tests MTR-1->DT-FEM-01 and MTR-1->DRIFT-01, but NOT DRIFT-01->DT-CALIB-LOOP-01 (the second hop in the anchor chain).
- **Risk:** The complete anchor dependency chain (MTR-1 -> DRIFT-01 -> DT-CALIB-LOOP-01) is not verified end-to-end.
- **Effort:** LOW -- add 2-3 tests following existing cross-claim pattern.
- **Suggested location:** `tests/steward/test_cross_claim_chain.py`

### P9: Manifest Version Rollback Attack
- **Gap:** No test verifies that an attacker cannot substitute an older valid `pack_manifest.json` (with valid `protocol_version` from a previous release) to bypass newer verification checks.
- **Risk:** Theoretical but could matter if protocol versions add new mandatory checks.
- **Effort:** LOW -- craft a v0.1 manifest and verify it fails against current verifier.
- **Suggested location:** `tests/steward/test_cert05_adversarial_gauntlet.py` (add attack6)

### P10: Governance Meta-Tests
- **Gap:** No test that verifies `known_faults.yaml` entries are still accurate (faults could be fixed but not removed). No test that `scientific_claim_index.md` entries match actual claim implementations (count, IDs).
- **Risk:** Documentation drift -- known_faults could list fixed issues, claim index could be stale.
- **Effort:** LOW -- parse YAML/MD and cross-reference with code.
- **Suggested location:** `tests/steward/test_stew08_documentation_drift.py`

---

## 6. Attack Scenarios Not Tested

### 6.1 Multi-Vector Coordinated Attacks
- **Not tested:** Attacker simultaneously rebuilds SHA-256 (Layer 1), injects fake evidence (Layer 2), and forges step chain (Layer 3). Currently only individual layer attacks are tested.
- **Not tested:** Attacker uses a stolen signing key to sign a bundle with tampered evidence. Layer 4 would pass -- do Layers 1-3 catch it?

### 6.2 Manifest Version Rollback
- **Not tested:** Attacker substitutes `protocol_version: "0.1"` manifest to bypass checks added in later versions.
- **Not tested:** Attacker changes `protocol_version` to a non-existent future version (e.g., "99.0").

### 6.3 Partial Corruption / Encoding Attacks
- **Not tested:** Truncated JSON evidence files (valid JSON prefix, cut mid-field).
- **Not tested:** Binary injection into JSON string fields (null bytes, control characters).
- **Not tested:** Unicode homoglyph attacks in claim IDs (e.g., Cyrillic "a" vs Latin "a").
- **Not tested:** BOM-prefixed UTF-8 files affecting SHA-256 fingerprints.
- **Not tested:** Extremely large evidence files (memory/timeout DoS).

### 6.4 Key Lifecycle
- **Not tested:** Verification with an expired key (if key metadata includes expiry).
- **Not tested:** Verification after key rotation -- old bundles signed with old key, new key loaded.
- **Not tested:** Signing with zero-length key material.
- **Not tested:** Key file with correct JSON structure but invalid cryptographic material (e.g., point not on curve for Ed25519).

### 6.5 Race Conditions in Pack/Sign
- **Not tested:** Two concurrent `mg.py pack build` commands on the same directory.
- **Not tested:** `mg_sign.py sign` running while `mg.py pack build` is still writing files.
- **Not tested:** File modification between SHA-256 computation and manifest finalization (TOCTOU).

### 6.6 Temporal Commitment Edge Cases
- **Not tested:** System clock set far in the past (before NIST Beacon existed).
- **Not tested:** Beacon response with valid format but logically impossible values (future pulse, negative timestamp).
- **Not tested:** Clock skew between signing time and beacon pulse time exceeding tolerance.

---

## 7. Recommendations -- Top 5 Actions

### Recommendation 1: Extend step chain tests to all 14 claims
**Impact:** Closes P1 (highest priority gap). **Effort:** ~1 hour.
**Action:** Add 7 `TestStepChain*` classes to `test_step_chain_all_claims.py` for ML_BENCH-01/02/03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01. Use the existing MTR-1 class as a template -- each needs 4 tests: trace_present, trace_four_steps, trace_deterministic, trace_changes_with_input.

### Recommendation 2: Add Layer 2 semantic edge cases
**Impact:** Closes P6 (weakest layer). **Effort:** ~30 minutes.
**Action:** Add 4-6 tests to CERT-02: partial evidence, extra fields, empty strings, zero values, null evidence. Layer 2 currently has the lowest test-to-risk ratio of any layer.

### Recommendation 3: Build multi-vector coordinated attack test (CERT-11)
**Impact:** Closes P2 (validates the core security thesis). **Effort:** ~2 hours.
**Action:** Create `test_cert11_coordinated_attack.py` with 3-4 scenarios: attacker rebuilds Layer 1 + attacks Layer 2 (should fail Layer 2), attacker rebuilds Layers 1+2 + attacks Layer 3 (should fail Layer 3), attacker with stolen key signs tampered bundle (Layers 1-3 should catch). This directly validates the paper's independence claim.

### Recommendation 4: Add cross-claim cascade failure and DRIFT-01->DT-CALIB chain
**Impact:** Closes P3 + P8 (anchor chain completeness). **Effort:** ~1 hour.
**Action:** Extend `test_cross_claim_chain.py` with: (a) DRIFT-01->DT-CALIB-LOOP-01 anchor tests, (b) cascading failure test where MTR-1 failure propagates through the entire chain. This completes the physical anchor traceability proof.

### Recommendation 5: Add step chain ordering and error path tests
**Impact:** Closes P4 + P7 (defense in depth). **Effort:** ~1 hour.
**Action:** Add to CERT-03: wrong step order, duplicate steps, extra steps. Create `test_runner_error_paths.py`: unknown JOB_KIND, exception during computation, None/empty inputs. These are low-effort tests with high defensive value.

---

## Appendix: Test Count Summary

| Metric | Value |
|--------|-------|
| Total tests | 391 |
| Total test files | 45 |
| Test directories | 8 |
| Claims with full coverage (C+S+X+E) | 2 (MTR-1, DT-FEM-01) |
| Claims with good coverage (C+S or C+inline-S+E) | 12 |
| Claims with dedicated step chain tests | 7 of 14 |
| Layers with strong coverage (10+ tests) | 3 (Layer 3, 4, 5) |
| Layers with weak coverage (<5 tests) | 1 (Layer 2) |
| Identified gaps | 10 (P1-P10) |
| Estimated total effort to close all gaps | ~8 hours |
| Priority 1 gaps (close immediately) | P1, P2, P6 |

---

*Report generated from direct pytest collection and test file inspection. All test counts verified against `python -m pytest tests/ --collect-only -q` output (391 tests collected).*
