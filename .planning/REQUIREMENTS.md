# Requirements: MetaGenesis Core v0.4.0

**Defined:** 2026-03-17
**Core Value:** Every verification claim must be independently auditable offline with cryptographic proof of integrity, provenance, and temporal commitment.

## v1 Requirements

### Ed25519 Signing

- [ ] **SIGN-01**: Pure-Python Ed25519 implementation based on RFC 8032 with test vector validation
- [x] **SIGN-02**: Ed25519 key pair generation (private key + public key) via CLI command
- [x] **SIGN-03**: Bundle signing with Ed25519 private key produces verifiable signature
- [x] **SIGN-04**: Signature verification with Ed25519 public key confirms bundle authenticity
- [x] **SIGN-05**: Public key export for third-party auditors (standalone file)
- [x] **SIGN-06**: Dual-algorithm auto-detection from key file version field (hmac-sha256-v1 vs ed25519-v1)
- [x] **SIGN-07**: Existing HMAC-signed bundles continue to verify without modification
- [x] **SIGN-08**: Downgrade attack prevention — verifier's key type is authoritative, not bundle's self-declared version

### Temporal Commitment

- [x] **TEMP-01**: NIST Beacon pulse capture at bundle sign time via urllib.request
- [x] **TEMP-02**: Cryptographic binding — SHA-256(root_hash + beacon_value + beacon_timestamp)
- [x] **TEMP-03**: Graceful degradation — temporal layer returns "not available" when beacon unreachable
- [x] **TEMP-04**: Layer 5 independent verification — checks temporal commitment without depending on Layers 1-4
- [x] **TEMP-05**: Offline verification of temporal data — checks embedded structure, no network calls
- [x] **TEMP-06**: Pre-commitment hash scheme — prove bundle existed before beacon pulse (two-phase commitment)

### Adversarial Proofs

- [ ] **CERT-01**: deep_verify Test 11 — bundle signing integrity proof
- [ ] **CERT-02**: deep_verify Test 12 — cross-environment reproducibility proof
- [ ] **CERT-03**: deep_verify Test 13 — temporal commitment verification proof
- [ ] **CERT-04**: 5-layer independence proof — each layer catches attacks the others miss
- [x] **CERT-05**: CERT-09 signing attack gauntlet (Ed25519-specific attack scenarios)
- [x] **CERT-06**: CERT-10 temporal attack gauntlet (replay, future-date, beacon forge attacks)

### Documentation & Counters

- [ ] **DOCS-01**: All counter updates across index.html (11+ places), README.md, AGENTS.md, llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md
- [ ] **DOCS-02**: system_manifest.json protocol version bump
- [ ] **DOCS-03**: reports/scientific_claim_index.md updated with new capabilities
- [ ] **DOCS-04**: paper.md references updated to cite implemented innovations

## v2 Requirements

### Advanced Temporal

- **TEMP-V2-01**: Cross-claim temporal chain (temporal DAG linking multiple claims)
- **TEMP-V2-02**: RFC 3161 TSA integration as alternative temporal authority
- **TEMP-V2-03**: Temporal chain explorer CLI command

### Advanced Signing

- **SIGN-V2-01**: Multi-party signing (multiple signers on one bundle)
- **SIGN-V2-02**: Key rotation with signature chain continuity
- **SIGN-V2-03**: Hardware security module (HSM) integration

## Out of Scope

| Feature | Reason |
|---------|--------|
| New claim domains (15+) | This milestone is protocol hardening only, not claim expansion |
| Blockchain integration | Contradicts banned terms; NIST Beacon is the temporal authority |
| Real-time beacon dependency | Offline-first principle — beacon is optional for verification |
| Removing HMAC signing | Backward compatibility required for existing v0.3.0 bundles |
| Modifying steward_audit.py | Sealed, CI-locked governance file |
| Major mg.py rewrites | Core verifier — minimal, surgical changes only |
| Third-party dependencies | stdlib-only constraint for all new code |
| Cross-claim temporal chain | High complexity, deferred to v0.5.0 per research |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SIGN-01 | Phase 1 | Pending |
| SIGN-02 | Phase 1 | Complete |
| SIGN-03 | Phase 2 | Complete |
| SIGN-04 | Phase 2 | Complete |
| SIGN-05 | Phase 1 | Complete |
| SIGN-06 | Phase 2 | Complete |
| SIGN-07 | Phase 2 | Complete |
| SIGN-08 | Phase 2 | Complete |
| TEMP-01 | Phase 3 | Complete |
| TEMP-02 | Phase 3 | Complete |
| TEMP-03 | Phase 3 | Complete |
| TEMP-04 | Phase 3 | Complete |
| TEMP-05 | Phase 3 | Complete |
| TEMP-06 | Phase 3 | Complete |
| CERT-01 | Phase 4 | Pending |
| CERT-02 | Phase 4 | Pending |
| CERT-03 | Phase 4 | Pending |
| CERT-04 | Phase 4 | Pending |
| CERT-05 | Phase 4 | Complete |
| CERT-06 | Phase 4 | Complete |
| DOCS-01 | Phase 4 | Pending |
| DOCS-02 | Phase 4 | Pending |
| DOCS-03 | Phase 4 | Pending |
| DOCS-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-03-17*
*Last updated: 2026-03-16 after roadmap creation*
