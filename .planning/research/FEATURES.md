# Feature Research

**Domain:** Adversarial test coverage hardening for cryptographic verification protocol
**Researched:** 2026-03-17
**Confidence:** HIGH (based on thorough codebase analysis of existing CERT-02 through CERT-10 patterns, cross-claim chain tests, step chain structural tests, and runner dispatch logic; web search confirmed alignment with industry adversarial testing practices)

## Feature Landscape

This is a TESTS-ONLY milestone. All "features" are test suites that close coverage gaps in the existing 5-layer verification protocol. No production code changes.

### Table Stakes (Users Expect These)

Features that any credible verification protocol test suite must have. Missing these means the JOSS paper's independence thesis is under-tested.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Step chain structural tests for all 14 claims (P1) | 7 of 14 claims lack dedicated step chain tests. A protocol that claims "all 14 claims have tamper-evident step chains" but only tests 7 is incomplete. Any reviewer or auditor will flag this gap. | LOW | Follow established pattern in `test_step_chain_all_claims.py`: 4 tests per claim (trace_present, four_steps, deterministic, changes_with_input). Missing claims: ML_BENCH-01 (partial), ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01. Approximately 28 new tests. |
| Layer 2 semantic edge case tests (P6) | Layer 2 has only 2 dedicated tests (in CERT-02 and CERT-05). It is the weakest-tested layer despite being the primary defense against evidence stripping. Semantic verification is where the protocol catches structurally valid but semantically invalid bundles. | MEDIUM | Edge cases to test: empty evidence_index, missing ledger_snapshot, malformed JSON in run_artifact, evidence_index pointing to nonexistent files, valid structure but wrong claim_id in mtr_phase, status FAILED in job_snapshot, empty execution_trace list. Approximately 8-12 new tests. |
| Runner error path tests (P7) | The runner's `_execute_job_logic` dispatches to 14 claim modules but has zero tests for error paths: unknown job kind, missing payload, exceptions from claim modules. Untested error paths are silent failure vectors. | LOW | Test: unknown `payload.kind` raises ValueError with registered kinds list, None payload handled, empty payload.kind string, claim module exception propagates correctly. Approximately 4-6 new tests. |
| Step chain ordering and structural tests (P4) | Existing step chain tests verify presence and determinism but not ordering invariants: steps must be 1-2-3-4 in order, step names must match expected sequence, no duplicate steps, no extra steps. A broken ordering invariant means the hash chain is structurally compromised. | LOW | Test: step numbers are strictly 1,2,3,4; step names match canonical sequence (init_params, compute/generate, metrics, threshold_check); no duplicate step numbers; hash at step N depends on hash at step N-1 (chain property). Approximately 6-8 new tests. |
| Manifest version rollback attack test (P9) | An attacker who obtains an older version of a bundle (with weaker security or different results) could substitute the entire manifest. Without a rollback test, this attack vector is undocumented. | LOW | Test: create bundle v2 (signed, temporal), substitute manifest from v1 (unsigned) -- Layer 4 catches because signed_root_hash no longer matches. Verify that version field mismatch is detected. 2-3 tests. |
| Governance meta-tests (P10) | Counter drift between documentation files (CLAUDE.md, index.html, README.md, llms.txt) is a recurring manual error. Without automated drift detection, counters diverge silently after every test addition. | LOW | Test: extract claim count, test count, layer count, innovation count from key documentation files; assert all agree. Parse known locations. This is a regression guard, not a security test. 3-5 tests. |

### Differentiators (Competitive Advantage)

Features that elevate MetaGenesis Core beyond a well-tested protocol into a formally proven one. These are what make the JOSS paper's claims defensible under peer review.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| CERT-11: Coordinated multi-vector attack proof (P2) | The flagship test. Existing CERT tests prove each layer catches attacks individually. CERT-11 proves the protocol survives a sophisticated attacker who simultaneously exploits multiple layers in a single coordinated campaign. No other verification protocol publishes a coordinated attack proof. This is the strongest evidence for the independence thesis. | HIGH | See "CERT-11 Design" section below for full specification. 8-10 tests in one gauntlet class. |
| CERT-12: Partial corruption and encoding attack tests (P5) | Tests that go beyond clean attack vectors to messy real-world failures: partial file corruption (truncated JSON), encoding attacks (UTF-8 BOM injection, mixed CRLF/LF, null bytes in hashes), malformed but syntactically valid JSON (NaN values, extremely long strings, deeply nested objects). These attacks exploit parser edge cases rather than cryptographic weaknesses. | MEDIUM | 6-8 tests covering: truncated JSON mid-key, BOM prefix in evidence files, null byte in trace_root_hash, NaN in numeric result fields, manifest with duplicate relpath entries, evidence file that is valid JSON but not a dict. |
| Cross-claim cascade failure tests (P3+P8) | Prove that tampering with an upstream claim (MTR-1) cascades to invalidate all downstream claims (DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01). Existing cross-claim tests cover the MTR-1 -> DT-FEM-01 -> DRIFT-01 chain. Missing: DRIFT-01 -> DT-CALIB-LOOP-01 cascade, and the full 4-claim cascade (MTR-1 tamper invalidates the entire downstream graph). | MEDIUM | Extend `test_cross_claim_chain.py` pattern. Test: tamper MTR-1 trace_root_hash, verify DT-CALIB-LOOP-01 at the end of the chain sees a different anchor. Also test: ML_BENCH-01 -> ML_BENCH-02 cascade (independent chain). 6-8 new tests. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Fuzz testing with random inputs | "Run 10,000 random payloads through the runner and see what breaks" | Fuzz testing is valuable for finding parser bugs but generates non-deterministic test results. MetaGenesis tests MUST be deterministic (same seed = same result). Random failures in CI erode trust. | Targeted edge-case tests with specific malformed inputs (CERT-12 approach). Each input is crafted, each assertion is specific, every run is deterministic. |
| Race condition tests (concurrent pack/sign) | "Test what happens when two processes sign the same bundle simultaneously" | Single-user CLI tool. Concurrent signing is not a realistic attack vector. Adding threading/multiprocessing to tests adds complexity and flakiness without covering a real threat. Already explicitly out of scope in PROJECT.md. | Document in PITFALLS.md that concurrent access is unsupported. If needed later, use file locking, not test coverage. |
| Key lifecycle tests (expiry, rotation) | "Test what happens when a signing key expires" | Key metadata does not currently include expiry fields. Testing nonexistent functionality creates phantom coverage. Already explicitly out of scope in PROJECT.md. | Defer until key metadata includes expiry (v0.6.0+). |
| Performance/load testing | "Run all 14 claims 1000 times and measure timing" | This is a benchmarking concern, not a coverage gap. Performance testing belongs in a separate CI stage, not in the adversarial test suite. | If timing matters later, add a separate `benchmarks/` directory. Do not mix performance tests with correctness tests. |
| Property-based testing (Hypothesis library) | "Use Hypothesis to generate arbitrary claim inputs" | Adds an external dependency (`hypothesis`). The project constraint is "stdlib only, even for test utilities." Property-based testing also generates non-deterministic test cases. | Manually crafted edge cases with full documentation of why each case matters. More readable, more maintainable, zero dependencies. |
| Exhaustive cross-claim permutation testing | "Test every possible ordering of all 14 claims" | 14! permutations = 87 billion. Even testing a subset is combinatorial explosion. Most permutations are independent (ML_BENCH-03 has no relationship to MTR-2). | Test only the documented dependency chains: MTR-1 -> DT-FEM-01 -> DRIFT-01 -> DT-CALIB-LOOP-01, and ML_BENCH-01 -> ML_BENCH-02/03. |

## CERT-11 Coordinated Attack Proof Design

CERT-11 is the flagship test of this milestone. It must convincingly demonstrate that a sophisticated attacker who understands the full protocol specification and coordinates attacks across multiple layers simultaneously is still detected.

### Structure

Follow the established CERT gauntlet pattern (CERT-05, CERT-09, CERT-10): a single test class with 6-8 named attack scenarios, each combining multiple attack vectors, plus a composite summary test.

### Attack Scenarios

| Attack | Layers Targeted | What the Attacker Does | Which Layer Catches It |
|--------|-----------------|------------------------|----------------------|
| A: Strip-and-Resign | L1+L2+L4 | Strip evidence, recompute SHA-256 hashes (bypass L1), re-sign with stolen key (bypass L4). Layer 2 catches the stripped job_snapshot. | L2 (semantic) |
| B: Result Forge with Manifest Rebuild | L1+L3 | Change claim result (0.94 -> 0.99), rebuild manifest hashes (bypass L1). Step chain trace_root_hash no longer matches because compute step hash changed. | L3 (step chain) |
| C: Cross-Domain Swap with Valid Signature | L2+L4 | Take a legitimately signed ML_BENCH-01 bundle, relabel it as PHARMA-01 in evidence_index. Signature is valid (file content unchanged), but semantic job_kind mismatch is caught. | L2 (semantic) |
| D: Temporal Replay with Re-signing | L4+L5 | Take bundle A's temporal commitment, copy it to bundle B, re-sign bundle B with attacker's key. L4 passes (valid signature), but L5 catches the pre_commitment_hash mismatch (computed from A's root_hash, not B's). | L5 (temporal) |
| E: Full Reconstruction (all layers) | L1+L2+L3+L4+L5 | Attacker reconstructs entire bundle from scratch: valid evidence, valid manifest, valid step chain, valid signature with their own key. But the key fingerprint does not match the expected signer -- L4 catches the unauthorized key. | L4 (signing - wrong key) |
| F: Cascade Poisoning with Cover-up | L1+L3+L4 | Tamper with upstream MTR-1 result, rebuild its step chain correctly, rebuild manifest, re-sign. The attacker's MTR-1 trace_root_hash is now different, so downstream DT-FEM-01's anchor_hash no longer matches -- the cross-claim chain is broken. | L3 (step chain via cross-claim anchor mismatch) |

### What Makes CERT-11 Convincing

1. **Each attack targets 2+ layers simultaneously** -- unlike CERT-05 which targets one layer per attack.
2. **The attacker explicitly bypasses N-1 layers** -- proving that even with partial bypass capability, the remaining layer catches the attack.
3. **At least 3 different layers are the "catching" layer across the scenarios** -- proving no single layer is a sufficient defense.
4. **Composite summary test** proves: attacks targeting L1+L2 are caught, attacks targeting L1+L3 are caught, attacks targeting L4+L5 are caught, and the full L1+L2+L3+L4+L5 attack is caught.
5. **Documentation style** matches CERT-05/09/10: each attack has a docstring explaining the attacker's reasoning and why the catching layer is the correct one.

### Dependencies

- Requires `_make_full_5layer_bundle` helper from `test_cert_5layer_independence.py` (or a shared helper module).
- Requires `_verify_semantic` from `scripts.mg`.
- Requires `sign_bundle`, `verify_bundle_signature` from `scripts.mg_sign`.
- Requires `verify_temporal_commitment` from `scripts.mg_temporal`.
- All dependencies already exist in the codebase.

## Feature Dependencies

```
[P1: Step chain structural tests (7 claims)]
    (no dependencies -- standalone)

[P2: CERT-11 coordinated attack proof]
    +--requires--> [P1 complete: ensures all 14 claims have structural tests]
    +--requires--> [existing 5-layer bundle helpers from test_cert_5layer_independence.py]

[P3+P8: Cross-claim cascade failure tests]
    +--requires--> [P1 complete: step chain tests for DT-CALIB-LOOP-01 and ML_BENCH-02/03]

[P4: Step chain ordering tests]
    +--enhances--> [P1: structural tests become ordering-aware]

[P5: CERT-12 encoding/corruption attacks]
    +--requires--> [P6 complete: semantic edge cases establish baseline for malformed input handling]

[P6: Layer 2 semantic edge cases]
    (no dependencies -- standalone, uses existing _verify_semantic)

[P7: Runner error paths]
    (no dependencies -- standalone, uses existing runner.py)

[P9: Manifest rollback attacks]
    +--requires--> [existing bundle signing infrastructure]

[P10: Governance meta-tests]
    (no dependencies -- standalone, reads documentation files)
```

### Dependency Notes

- **P1 (step chain structural) is the foundation:** Most other test categories build on the assumption that all 14 claims have verified step chains. Complete P1 first.
- **P2 (CERT-11) depends on P1:** The coordinated attack proof must reference structurally verified claims. If a claim's step chain is broken, CERT-11 cannot distinguish "attack detected" from "pre-existing structural failure."
- **P6 (semantic edge cases) before P5 (CERT-12):** Semantic edge cases test clean but invalid inputs. CERT-12 tests corrupted inputs. The semantic baseline must exist before testing corruption resilience.
- **P3+P8 (cascade failures) depend on P1:** Cascade tests for DT-CALIB-LOOP-01 require that claim's step chain to be structurally verified first.
- **P7 (runner) and P10 (governance) are independent:** Can be done in any order, in parallel with anything else.

## MVP Definition

### Phase 1: Foundation (first)

Close the structural gaps that everything else depends on.

- [ ] P1: Step chain structural tests for 7 remaining claims (~28 tests)
- [ ] P4: Step chain ordering and invariant tests (~6 tests)
- [ ] P7: Runner error path tests (~4 tests)
- [ ] P10: Governance meta-tests (~4 tests)

### Phase 2: Edge Cases and Cascades (second)

Harden the semantic and cross-claim layers.

- [ ] P6: Layer 2 semantic edge case tests (~10 tests)
- [ ] P3+P8: Cross-claim cascade failure tests (~8 tests)
- [ ] P9: Manifest version rollback attack tests (~3 tests)

### Phase 3: Flagship Proofs (last)

The adversarial capstones that prove the protocol under coordinated attack.

- [ ] P2: CERT-11 coordinated multi-vector attack proof (~8 tests)
- [ ] P5: CERT-12 partial corruption and encoding attacks (~8 tests)

### Ordering Rationale

Phase 1 before Phase 2 because structural coverage (P1) is a prerequisite for meaningful cascade testing (P3). Phase 2 before Phase 3 because semantic edge cases (P6) establish the baseline for corruption attacks (P5), and CERT-11 needs all other layers to be well-tested to distinguish coordinated attacks from pre-existing gaps.

## Feature Prioritization Matrix

| Feature | Proof Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| P1: Step chain structural (7 claims) | HIGH | LOW | P1 |
| P2: CERT-11 coordinated attack | HIGH | HIGH | P1 |
| P3+P8: Cross-claim cascade | HIGH | MEDIUM | P1 |
| P4: Step chain ordering | MEDIUM | LOW | P1 |
| P5: CERT-12 encoding/corruption | MEDIUM | MEDIUM | P1 |
| P6: Layer 2 semantic edge cases | HIGH | MEDIUM | P1 |
| P7: Runner error paths | LOW | LOW | P1 |
| P9: Manifest rollback | MEDIUM | LOW | P1 |
| P10: Governance meta-tests | LOW | LOW | P1 |

**All are P1 for this milestone** because the milestone's purpose is specifically to close all 10 gaps. The ordering within the milestone (Phase 1/2/3 above) determines sequencing, not priority.

**Priority key:**
- P1: Must have for v0.5.0 (this is a coverage-hardening milestone -- all gaps must close)
- P2: Not applicable -- there is no "nice to have" in a gap-closure milestone

## Competitor Feature Analysis

| Test Category | Sigstore | in-toto | TUF (The Update Framework) | MetaGenesis Approach |
|--------------|----------|---------|----------------------------|---------------------|
| Coordinated multi-vector attack | No formal gauntlet | No formal gauntlet | Some multi-role attack tests | CERT-11: 6+ scenarios, each targeting 2+ layers simultaneously |
| Encoding/corruption resilience | Basic input validation | Schema validation | Metadata format validation | CERT-12: truncated JSON, BOM injection, null bytes, NaN values |
| Cascade failure testing | N/A (no claim chains) | Supply chain layout tests | Delegations testing | Full dependency chain: MTR-1 -> DT-FEM-01 -> DRIFT-01 -> DT-CALIB-LOOP-01 |
| Governance drift detection | N/A | N/A | N/A | Automated counter consistency across 6+ documentation files |
| Step chain structural coverage | N/A (no step chains) | Link metadata validation | N/A | 4 structural tests per claim x 14 claims = 56 total |

## Sources

- Codebase analysis: `tests/steward/test_cert05_adversarial_gauntlet.py` (5-attack coordinated pattern -- the template for CERT-11)
- Codebase analysis: `tests/steward/test_cert09_ed25519_attacks.py` (5-attack Ed25519 gauntlet)
- Codebase analysis: `tests/steward/test_cert10_temporal_attacks.py` (5-attack temporal gauntlet)
- Codebase analysis: `tests/steward/test_cert_5layer_independence.py` (5-layer independence proof with full bundle helper)
- Codebase analysis: `tests/steward/test_step_chain_all_claims.py` (structural test pattern for 7/14 claims)
- Codebase analysis: `tests/steward/test_cross_claim_chain.py` (6-test cross-claim chain pattern)
- Codebase analysis: `backend/progress/runner.py` (14-claim dispatch with error path at line 416)
- Project context: `.planning/PROJECT.md` (10 gaps P1-P10, constraints, scope)
- [Adversarial Exposure Validation Guide](https://www.cycognito.com/learn/exposure-management/adversarial-exposure-validation/) -- industry framework for coordinated attack simulation
- [OWASP Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/) -- encoding and corruption attack patterns
- [CMMTree Cryptographic Protocol Testing Methodology](https://www.mdpi.com/2076-3417/13/23/12668) -- systematic protocol test coverage framework

---
*Feature research for: Adversarial test coverage hardening (v0.5.0)*
*Researched: 2026-03-17*
