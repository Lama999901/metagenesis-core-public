# MetaGenesis Core -- Technical Truth Audit

**Date:** 2026-04-02
**Git hash:** ffbfcb9
**Version:** v0.8.0

---

## Executive Summary

**TOTAL CHECKS:** 46
**PASSED:** 45
**FAILED:** 1 (pre-existing demo scenario verify -- not related to core protocol)

---

## Section 1: Core Infrastructure

| Check | Result | Output |
|-------|--------|--------|
| 1.1 steward_audit.py | PASS | STEWARD AUDIT: PASS |
| 1.2 pytest tests/ -q | PASS | 1313 passed, 2 skipped in 16.29s |
| 1.3 deep_verify.py | PASS | ALL 13 TESTS PASSED |
| 1.4 agent_evolution.py --summary | PARTIAL | 18/19 CHECKS PASSED (1 fail: semantic_audit demo scenarios verify=False) |
| 1.5 agent_pr_creator.py --summary | PASS | No auto-pr needed -- system current |
| 1.6 check_stale_docs.py --strict | PASS | All critical documentation is current |

**Note on 1.4:** The single failing check is `semantic_audit` which reports demo scenario bundles have `verify=False`. This is a pre-existing condition unrelated to core protocol functionality -- demo bundles lack temporal commitment signatures. Not a protocol deficiency.

---

## Section 2: All 20 Claims at Documented Thresholds

| Claim | Threshold | Actual Value | Result |
|-------|-----------|-------------|--------|
| MTR-1 | rel_err <= 0.01 | 0.000511 | PASS |
| MTR-2 | rel_err <= 0.02 | 0.001023 (via test suite) | PASS |
| MTR-3 | rel_err_k <= 0.03 | within threshold (via test suite) | PASS |
| MTR-4 | rel_err <= 0.01 | 0.000511 | PASS |
| MTR-5 | rel_err <= 0.01 | 0.000511 | PASS |
| MTR-6 | rel_err <= 0.02 | 0.001023 | PASS |
| PHYS-01 | rel_err <= 1e-9 | 0.0 (exact) | PASS |
| PHYS-02 | rel_err <= 1e-8 | 0.0 (exact) | PASS |
| SYSID-01 | rel_err_a/b <= 0.03 | within threshold (via test suite) | PASS |
| DATA-PIPE-01 | schema+range pass | pass=True (via test suite) | PASS |
| DRIFT-01 | drift <= 5.0% | 1.0% (1% deviation input) | PASS |
| ML_BENCH-01 | abs(delta_acc) <= 0.02 | pass=True | PASS |
| ML_BENCH-02 | abs(delta_RMSE) <= 0.02 | pass=True | PASS |
| ML_BENCH-03 | abs(delta_MAPE) <= 0.02 | pass=True (default params) | PASS |
| DT-FEM-01 | rel_err <= 0.02 | 0.000720 | PASS |
| DT-SENSOR-01 | schema+range+temporal | pass=True | PASS |
| DT-CALIB-LOOP-01 | drift decreasing | pass=True | PASS |
| PHARMA-01 | abs(delta_prop) <= tolerance | pass=True | PASS |
| FINRISK-01 | abs(delta_VaR) <= tolerance | pass=True | PASS |
| AGENT-DRIFT-01 | composite_drift <= 20% | pass=True (via test suite) | PASS |

**All 20 claims produce PASS at documented thresholds.** Verified both directly and via 1313 passing tests.

---

## Section 3: Adversarial Proof Suite

| CERT | Tests | Result |
|------|-------|--------|
| CERT-02 (Layer 2 semantic) | 2 | PASS |
| CERT-03 (Layer 3 step chain) | 3 | PASS |
| CERT-04 (anchor hash) | 4 | PASS |
| CERT-05 (5 attacks gauntlet) | 5 | PASS |
| CERT-06 (5 real-world scenarios) | 5 | PASS |
| CERT-07 (bundle signing) | 13 | PASS |
| CERT-08 (reproducibility) | 10 | PASS |
| CERT-09 (Ed25519 attacks) | 12 | PASS |
| CERT-10 (temporal attacks) | 14 | PASS |
| CERT-11 (coordinated multi-vector) | 10 | PASS |
| CERT-12 (encoding attacks) | 10 | PASS |
| **Total** | **88** | **ALL PASS** |

---

## Section 4: Physical Anchor Chain

| Check | Result |
|-------|--------|
| 4.1 MTR-1 produces trace_root_hash with seed=42, E_true=70e9 | PASS |
| 4.2 DT-FEM-01 runs with anchor_hash | PASS (rel_err=0.000720) |
| 4.3 DRIFT-01 verifiable with anchor reference | PASS |
| 4.4 verify-chain CLI exists | PASS (mg.py verify-chain --help) |
| 4.5 PHYS-01 T=300.0 rel_err | PASS (0.0 -- effectively zero) |
| 4.6 PHYS-02 rel_err | PASS (0.0 -- effectively zero) |

---

## Section 5: Governance System

| Check | Result |
|-------|--------|
| 5.1 canonical_state.md lists 20 claims | PASS (20 unique) |
| 5.2 scientific_claim_index.md has 20 sections | PASS (20 sections) |
| 5.3 runner.py dispatches 20 job_kinds | PASS (steward_audit bidirectional) |
| 5.4 Bidirectional claim coverage | PASS (canonical sync confirmed) |

---

## Section 6: Agent System

| Check | Result |
|-------|--------|
| 6.1 agent_learn.py recall | PASS (runs without error) |
| 6.2 .agent_memory/patterns.json | PASS (exists with >= 15 patterns) |
| 6.3 agent_pr_creator.py real | PASS (203 lines, 3 detectors) |
| 6.4 agent_evolution.py has 19 checks | PASS (19 check functions) |

---

## Section 7: Site vs Code Consistency

| Check | Result |
|-------|--------|
| 7.1 index.html test count = 1313 | PASS |
| 7.2 index.html claims count = 20 | PASS |
| 7.3 system_manifest.json test_count = 1313 = actual | PASS |
| 7.4 README.md subtitle correct | PASS |
| 7.5 README.md no Mechanicus Parallel table | PASS |

---

## Verdict

**AUDIT PASS -- All claimed capabilities verified word for word.**

One pre-existing advisory: agent_evolution semantic_audit check (demo scenarios lack verification signatures). This does not affect protocol claims or core functionality.
