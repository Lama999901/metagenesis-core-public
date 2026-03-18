# Requirements: MetaGenesis Core v0.5.0

**Defined:** 2026-03-17
**Core Value:** Every verification claim must be independently auditable offline with cryptographic proof of integrity, provenance, and temporal commitment.

## v1 Requirements

### Step Chain Coverage

- [x] **CHAIN-01**: All 14 claims have dedicated structural step chain tests (genesis hash, hash linkage, root hash equality)
- [x] **CHAIN-02**: Step chain verifier rejects traces with wrong step ordering (1,3,2,4)
- [x] **CHAIN-03**: Step chain verifier rejects traces with duplicate step numbers
- [x] **CHAIN-04**: Step chain verifier rejects traces with extra steps beyond 4

### Adversarial Proofs

- [x] **ADV-01**: CERT-11 proves attacker who rebuilds Layer 1 + fakes Layer 2 is caught by Layer 2
- [x] **ADV-02**: CERT-11 proves attacker who rebuilds Layers 1+2 + forges Layer 3 is caught by Layer 3
- [x] **ADV-03**: CERT-11 proves stolen signing key with tampered evidence is caught by Layers 1-3
- [x] **ADV-04**: CERT-11 proves coordinated 3-layer bypass still fails at remaining layers
- [x] **ADV-05**: CERT-12 proves BOM-prefixed files are detected or handled safely
- [x] **ADV-06**: CERT-12 proves null bytes / truncated JSON / Unicode homoglyphs are caught
- [x] **ADV-07**: Manifest version rollback (old protocol_version) is rejected by verifier

### Layer Hardening

- [x] **SEM-01**: Layer 2 rejects partial evidence (some fields present, some missing)
- [x] **SEM-02**: Layer 2 handles extra unexpected fields without false acceptance
- [x] **SEM-03**: Layer 2 rejects semantically meaningless values (empty strings, zero values)
- [x] **CASCADE-01**: Cross-claim test covers full anchor chain MTR-1→DRIFT-01→DT-CALIB-LOOP-01
- [x] **CASCADE-02**: Failed upstream claim (MTR-1) propagates correctly through entire anchor chain
- [x] **CASCADE-03**: Cross-claim chain detects tampered anchor hash at any hop

### Error Paths & Governance

- [x] **ERR-01**: Runner rejects unknown JOB_KIND with clear error
- [x] **ERR-02**: Runner handles mid-computation exceptions gracefully
- [x] **ERR-03**: Runner handles None/empty/wrong-type input data
- [x] **GOV-01**: Meta-test detects drift between scientific_claim_index.md and actual claim implementations
- [x] **GOV-02**: Meta-test detects drift between known_faults.yaml and current code state
- [x] **GOV-03**: Meta-test validates counter consistency across documentation files

### Documentation & Counters

- [x] **DOCS-01**: All counter updates across index.html, README.md, AGENTS.md, llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md reflect new test count

## v2 Requirements

### Advanced Coverage

- **COV-V2-01**: Race condition tests for concurrent pack/sign operations (TOCTOU)
- **COV-V2-02**: Key lifecycle tests (expired keys, key rotation, invalid curve points)
- **COV-V2-03**: Property-based testing for step chain invariants (hypothesis library)
- **COV-V2-04**: Temporal commitment edge cases (clock skew, impossible beacon values)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Production code changes | Tests-only milestone — no changes to scripts/, backend/, core modules unless required for testability |
| Race condition tests (TOCTOU) | Concurrent pack/sign is not a realistic attack vector for single-user CLI |
| Key lifecycle tests | Key metadata does not currently include expiry; deferred to v0.6.0 |
| Property-based testing | Would require hypothesis library, violating stdlib-only constraint |
| Fuzz testing | Excessive for deterministic protocol; targeted encoding attacks (CERT-12) suffice |
| New claim domains | Not adding claims 15+, this is coverage hardening only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CHAIN-01 | Phase 5 | Complete |
| CHAIN-02 | Phase 5 | Complete |
| CHAIN-03 | Phase 5 | Complete |
| CHAIN-04 | Phase 5 | Complete |
| ADV-01 | Phase 7 | Complete |
| ADV-02 | Phase 7 | Complete |
| ADV-03 | Phase 7 | Complete |
| ADV-04 | Phase 7 | Complete |
| ADV-05 | Phase 7 | Complete |
| ADV-06 | Phase 7 | Complete |
| ADV-07 | Phase 6 | Complete |
| SEM-01 | Phase 6 | Complete |
| SEM-02 | Phase 6 | Complete |
| SEM-03 | Phase 6 | Complete |
| CASCADE-01 | Phase 6 | Complete |
| CASCADE-02 | Phase 6 | Complete |
| CASCADE-03 | Phase 6 | Complete |
| ERR-01 | Phase 5 | Complete |
| ERR-02 | Phase 5 | Complete |
| ERR-03 | Phase 5 | Complete |
| GOV-01 | Phase 5 | Complete |
| GOV-02 | Phase 5 | Complete |
| GOV-03 | Phase 5 | Complete |
| DOCS-01 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-17 after roadmap creation*
