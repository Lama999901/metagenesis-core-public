# Roadmap: MetaGenesis Core v0.5.0 Coverage Hardening

## Overview

This milestone closes all 10 test coverage gaps identified in the v0.4.0 gap analysis, bringing the test suite from 391 to 450+ tests. The work flows in strict dependency order: step chain structural tests and error paths first (foundation for all subsequent testing), then semantic edge cases and cascade failures (characterize individual layers), then flagship adversarial proofs CERT-11 and CERT-12 (synthesize all prior work into coordinated attack gauntlets), and finally counter updates (require final test count). Phase numbering continues from v0.4.0 which ended at Phase 4.

## Milestones

- **v0.4.0 Protocol Hardening** - Phases 1-4 (shipped 2026-03-18)
- **v0.5.0 Coverage Hardening** - Phases 5-8 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (5.1, 5.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>v0.4.0 Protocol Hardening (Phases 1-4) - SHIPPED 2026-03-18</summary>

- [x] **Phase 1: Ed25519 Foundation** - Pure-Python Ed25519 validated against RFC 8032
- [x] **Phase 2: Signing Upgrade** - Ed25519 bundle signing with HMAC backward compatibility
- [x] **Phase 3: Temporal Commitment** - NIST Beacon Layer 5 with offline graceful degradation
- [x] **Phase 4: Adversarial Proofs and Polish** - CERT-09, CERT-10, deep_verify 11-13, counter updates

</details>

### v0.5.0 Coverage Hardening

- [ ] **Phase 5: Foundation** - Step chain structural tests for all 14 claims, runner error paths, governance meta-tests
- [ ] **Phase 6: Layer Hardening** - Semantic edge cases, cross-claim cascade failures, manifest rollback attack
- [ ] **Phase 7: Flagship Proofs** - CERT-11 coordinated multi-vector attack, CERT-12 encoding attacks
- [ ] **Phase 8: Counter Updates** - All documentation counters reflect final test count

## Phase Details

### Phase 5: Foundation
**Goal**: Every claim has verified step chain structure, every runner error path is tested, and governance drift detection is active for all subsequent phases
**Depends on**: Phase 4 (v0.4.0 complete, 391 tests baseline)
**Requirements**: CHAIN-01, CHAIN-02, CHAIN-03, CHAIN-04, ERR-01, ERR-02, ERR-03, GOV-01, GOV-02, GOV-03
**Success Criteria** (what must be TRUE):
  1. Running pytest on step chain tests shows all 14 claims pass structural assertions (genesis hash, hash linkage, 4-step count, root hash equality)
  2. Step chain verifier rejects a trace with misordered steps (1,3,2,4), duplicate step numbers, or extra steps beyond 4
  3. Runner produces a clear error message when given an unknown JOB_KIND, and does not crash on None/empty/wrong-type input or mid-computation exceptions
  4. Governance meta-tests detect when scientific_claim_index.md, known_faults.yaml, or documentation counters drift from actual code state
  5. All 391 existing tests continue to pass (zero regressions)
**Plans**: 3 plans

Plans:
- [ ] 05-01: Step chain structural tests for 7 missing claims (CHAIN-01)
- [ ] 05-02: Step chain ordering, duplicate, and extra-step rejection tests (CHAIN-02, CHAIN-03, CHAIN-04)
- [ ] 05-03: Runner error paths and governance meta-tests (ERR-01, ERR-02, ERR-03, GOV-01, GOV-02, GOV-03)

### Phase 6: Layer Hardening
**Goal**: Layer 2 semantic verification is hardened against edge cases, cross-claim cascade failures propagate correctly through the full anchor chain, and manifest rollback attacks are rejected
**Depends on**: Phase 5
**Requirements**: SEM-01, SEM-02, SEM-03, CASCADE-01, CASCADE-02, CASCADE-03, ADV-07
**Success Criteria** (what must be TRUE):
  1. Layer 2 rejects evidence bundles with partial fields, extra unexpected fields, and semantically meaningless values (empty strings, zero values where physical quantities are expected)
  2. Cross-claim test covers the full anchor chain MTR-1 to DRIFT-01 to DT-CALIB-LOOP-01, and a failed upstream claim propagates failure through every downstream hop
  3. Cross-claim chain detects a tampered anchor hash at any position in the chain
  4. Verifier rejects a bundle with a rolled-back manifest protocol_version
**Plans**: TBD

Plans:
- [ ] 06-01: Layer 2 semantic edge case tests (SEM-01, SEM-02, SEM-03)
- [ ] 06-02: Cross-claim cascade failure and manifest rollback tests (CASCADE-01, CASCADE-02, CASCADE-03, ADV-07)

### Phase 7: Flagship Proofs
**Goal**: CERT-11 proves the 5-layer independence thesis under coordinated multi-vector attack, and CERT-12 proves encoding attacks (BOM, null bytes, homoglyphs, truncated JSON) are caught
**Depends on**: Phase 6
**Requirements**: ADV-01, ADV-02, ADV-03, ADV-04, ADV-05, ADV-06
**Success Criteria** (what must be TRUE):
  1. CERT-11 proves an attacker who rebuilds Layer 1 and fakes Layer 2 is caught specifically by Layer 2 (not trivially by Layer 1)
  2. CERT-11 proves an attacker who bypasses Layers 1+2 and forges Layer 3 is caught specifically by Layer 3
  3. CERT-11 proves a stolen signing key with tampered evidence is caught by Layers 1-3, and a coordinated 3-layer bypass still fails at remaining layers
  4. CERT-12 proves BOM-prefixed files, null bytes, truncated JSON, and Unicode homoglyphs are detected or handled safely
**Plans**: TBD

Plans:
- [ ] 07-01: CERT-11 coordinated multi-vector attack gauntlet (ADV-01, ADV-02, ADV-03, ADV-04)
- [ ] 07-02: CERT-12 encoding and partial corruption attacks (ADV-05, ADV-06)

### Phase 8: Counter Updates
**Goal**: All documentation and site files reflect the final v0.5.0 test count, maintaining counter consistency across the project
**Depends on**: Phase 7
**Requirements**: DOCS-01
**Success Criteria** (what must be TRUE):
  1. Running pytest reports the final test count and all counters in index.html (11 places), README.md, AGENTS.md, llms.txt, system_manifest.json, and CONTEXT_SNAPSHOT.md match that count
  2. Governance meta-tests from Phase 5 pass with the updated counters (no drift detected)
**Plans**: TBD

Plans:
- [ ] 08-01: Documentation counter updates across all files (DOCS-01)

## Progress

**Execution Order:**
Phases execute in numeric order: 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Foundation | 0/3 | Not started | - |
| 6. Layer Hardening | 0/2 | Not started | - |
| 7. Flagship Proofs | 0/2 | Not started | - |
| 8. Counter Updates | 0/1 | Not started | - |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-03-17*
