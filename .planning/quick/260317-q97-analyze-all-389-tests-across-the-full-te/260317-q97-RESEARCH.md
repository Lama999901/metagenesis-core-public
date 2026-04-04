# Test Suite Gap Analysis - Research

**Researched:** 2026-03-17
**Domain:** Test coverage for MetaGenesis Core verification protocol
**Confidence:** HIGH (based on direct test file inspection)

## Summary

The test suite contains **391 tests** across 47 test files. Coverage is strong for the adversarial proof suite (CERT-01 through CERT-10 plus 5-layer independence) and individual claim correctness. However, there are specific gaps in step chain coverage (only 7 of 14 claims tested in the dedicated step chain file), no negative/failure-path tests for several claims, and missing cross-layer combination attacks.

**Primary finding:** The biggest gap is that `test_step_chain_all_claims.py` only covers 7 of 14 claims (MTR-1/2/3, SYSID-01, DATAPIPE-01, DRIFT-01, DT-FEM-01), leaving ML_BENCH-01/02/03, PHARMA-01, FINRISK-01, DT-SENSOR-01, and DT-CALIB-LOOP-01 without dedicated step chain structural tests.

## Test Distribution by Area

| Area | Files | Tests | Coverage Quality |
|------|-------|-------|-----------------|
| steward/ (adversarial, governance) | 21 files | 195 | Strong |
| ml/ (ML claims) | 7 files | 73 | Good for correctness, gaps in step chain |
| digital_twin/ | 5 files | 47 | Good |
| materials/ | 5 files | 16 | Adequate |
| cli/ (E2E) | 2 files | 13 | Adequate |
| progress/ (store, evidence) | 2 files | 11 | Adequate |
| data/ | 1 file | 3 | Minimal |
| systems/ | 1 file | 3 | Minimal |

## Gap 1: Step Chain Coverage for 7 Missing Claims

`test_step_chain_all_claims.py` has dedicated `TestStepChain*` classes for only 7 claims:
- MTR-1, MTR-2, MTR-3, SYSID-01, DATAPIPE-01, DRIFT-01, DT-FEM-01

**Missing dedicated step chain structural tests for:**
- ML_BENCH-01, ML_BENCH-02, ML_BENCH-03
- PHARMA-01, FINRISK-01
- DT-SENSOR-01, DT-CALIB-LOOP-01

Note: Some of these claims DO have `execution_trace` checks in their own certificate test files (e.g., `TestExecutionTraceChain` in mlbench01), but the dedicated structural validation (4-step chain integrity, hash linkage, genesis hash) is only in the steward file for the 7 above.

**Risk:** A claim could pass its domain tests but have a malformed step chain that would weaken Layer 3.

## Gap 2: Missing Attack Scenarios

### Not tested: Multi-layer coordinated attack
CERT-05 tests 5 individual attack scenarios and the 5-layer independence test checks each layer independently. But there is NO test for an attacker who simultaneously:
- Rebuilds SHA-256 hashes (bypasses Layer 1)
- Adds fake semantic evidence (bypasses Layer 2)
- Attempts to forge the step chain (attacks Layer 3)

This "sophisticated multi-vector attack" is the real-world threat model.

### Not tested: Rollback/version downgrade on pack manifest
No test verifies that an attacker cannot substitute an older valid manifest version to bypass newer verification checks. The `protocol_version` field in manifests is checked but rollback to a valid older version is not tested.

### Not tested: Partial bundle corruption
Tests cover full file tampering but not partial corruption scenarios:
- Truncated evidence files
- Binary garbage in JSON fields
- Unicode/encoding attacks in claim data

### Not tested: Race conditions in bundle creation
No concurrency tests for simultaneous pack/sign operations that could produce inconsistent bundles.

## Gap 3: Edge Cases in Specific Layers

### Layer 1 (SHA-256 Integrity)
- CERT-01 tests basic tamper detection (3 tests) -- minimal
- No test for: empty file handling, very large files, symlink following, CRLF normalization edge cases beyond the known `fingerprint_file` function

### Layer 2 (Semantic)
- CERT-02 has only 2 tests
- No test for: partial evidence (some fields present, some missing), evidence with extra unexpected fields, evidence with correct structure but semantically meaningless values

### Layer 3 (Step Chain)
- CERT-03 has 6 tests covering valid/invalid/missing scenarios -- good
- Gap: No test for step chain with wrong step ORDER (steps 1,3,2,4 instead of 1,2,3,4)
- Gap: No test for duplicate step numbers

### Layer 4 (Bundle Signing)
- CERT-07 (13 tests) + signing_upgrade (15 tests) + ed25519 (37 tests) = strong coverage
- Gap: No test for expired/rotated keys (key lifecycle)
- Gap: No test for signing with zero-length key material

### Layer 5 (Temporal Commitment)
- CERT-10 (6 tests) + test_temporal.py (14 tests) = good coverage
- Gap: No test for clock skew tolerance (what if system clock is wrong?)
- Gap: No test for beacon response with valid format but logically impossible values

## Gap 4: Cross-Claim Interaction Gaps

`test_cross_claim_chain.py` covers 6 scenarios focused on anchor_hash linkage (MTR-1 -> DT-FEM-01, MTR-1 -> DRIFT-01). Missing:

- DT-CALIB-LOOP-01 depends on DRIFT-01 (anchor chain) -- no cross-claim test
- No test for cascading failure: if MTR-1 fails, do downstream claims (DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01) correctly propagate the failure?
- No test for circular dependency detection (defensive -- currently no cycles exist, but nothing prevents one from being introduced)

## Gap 5: Innovation Coverage

| Innovation | Tests | Assessment |
|------------|-------|------------|
| #1-5 (PPA core) | Covered by CERT-01 through CERT-06, step chain tests | Good |
| #6 HMAC signing | CERT-07 (13 tests), signing_upgrade (15 tests) | Strong |
| #6 Ed25519 upgrade | test_ed25519.py (37 tests), CERT-09 (6 tests) | Strong |
| #7 Temporal Commitment | test_temporal.py (14 tests), CERT-10 (6 tests) | Good |

All 7 innovations have test coverage. No gap here.

## Gap 6: Governance/Meta Tests

- `test_stew01` through `test_stew07` cover governance well
- deep_verify.py has 13 tests -- acts as integration smoke tests
- Gap: No test that verifies `known_faults.yaml` entries are still accurate (faults could be fixed but not removed from the file)
- Gap: No test that `scientific_claim_index.md` entries match actual claim implementations (count, IDs)

## Gap 7: Error Path Coverage

Most claim tests focus on the happy path (pass) and basic failure (threshold exceeded). Missing:
- What happens when a claim module raises an unexpected exception mid-computation?
- What happens when `runner.py` receives an unknown JOB_KIND?
- What happens when claim input data is None/empty/wrong type?
- What happens when the step chain `_hash_step` receives non-serializable data?

## Priority-Ranked Gap Summary

| Priority | Gap | Impact | Effort |
|----------|-----|--------|--------|
| P1 | Step chain tests for 7 missing claims | Layer 3 could have undetected structural bugs | Low -- template exists |
| P2 | Multi-vector coordinated attack test | Real-world threat not validated | Medium |
| P3 | Cross-claim cascade failure (MTR-1 chain) | Dependency chain correctness unproven | Medium |
| P4 | Step chain ordering/duplicate step tests | Edge case in Layer 3 | Low |
| P5 | Partial corruption / encoding attacks | Robustness under malformed input | Medium |
| P6 | Layer 2 semantic edge cases (only 2 tests) | Weakest layer by test count | Low |
| P7 | Error path coverage in runner.py | Graceful degradation unproven | Low |
| P8 | DT-CALIB-LOOP-01 cross-claim with DRIFT-01 | Anchor chain gap | Low |
| P9 | Manifest version rollback attack | Theoretical but untested | Low |
| P10 | Governance meta-tests (known_faults, claim_index) | Documentation drift detection | Low |

## Sources

### Primary (HIGH confidence)
- Direct inspection of all 47 test files in tests/ directory
- pytest --collect-only output: 391 tests collected
- deep_verify.py: 13 integration tests
- CLAUDE.md: 14 active claims, 4-layer (now 5-layer) verification model

---

*Research complete. All findings based on direct code inspection.*
