# Roadmap: MetaGenesis Core v0.4.0 Protocol Hardening

## Overview

This milestone hardens the MetaGenesis verification protocol from 4 layers to 5, upgrading bundle signing from HMAC to Ed25519 (with backward compatibility), adding temporal commitment via NIST Beacon (Innovation #7), and proving all new capabilities through expanded adversarial proof suites. The work flows in strict dependency order: Ed25519 must be proven correct before integration, signing must be finalized before temporal data embeds in bundles, and adversarial proofs test everything built in prior phases.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Ed25519 Foundation** - Pure-Python Ed25519 implementation validated against RFC 8032 test vectors
- [x] **Phase 2: Signing Upgrade** - Ed25519 integrated into bundle signing with HMAC backward compatibility (completed 2026-03-18)
- [ ] **Phase 3: Temporal Commitment** - NIST Beacon integration and Layer 5 independent verification
- [ ] **Phase 4: Adversarial Proofs and Polish** - Expanded proof suite, deep_verify tests 11-13, documentation updates

## Phase Details

### Phase 1: Ed25519 Foundation
**Goal**: Users can generate Ed25519 key pairs and the implementation passes all RFC 8032 test vectors, proving cryptographic correctness before any integration
**Depends on**: Nothing (first phase)
**Requirements**: SIGN-01, SIGN-02, SIGN-05
**Success Criteria** (what must be TRUE):
  1. Running `python scripts/mg_ed25519.py` test vectors produces PASS for all RFC 8032 vectors
  2. User can generate an Ed25519 key pair via CLI and receives a private key file and a public key file
  3. Public key can be exported as a standalone file suitable for sharing with third-party auditors
  4. All 295 existing tests continue to pass (no regressions from new module)
**Plans:** 2 plans

Plans:
- [ ] 01-01-PLAN.md -- Ed25519 core implementation with RFC 8032 test vector TDD (SIGN-01)
- [ ] 01-02-PLAN.md -- Key generation CLI and public key export (SIGN-02, SIGN-05)

### Phase 2: Signing Upgrade
**Goal**: Users can sign bundles with Ed25519 and verify them, while all existing HMAC-signed bundles continue to verify without modification
**Depends on**: Phase 1
**Requirements**: SIGN-03, SIGN-04, SIGN-06, SIGN-07, SIGN-08
**Success Criteria** (what must be TRUE):
  1. User can sign a bundle with an Ed25519 private key via CLI and the bundle contains a verifiable Ed25519 signature
  2. User can verify an Ed25519-signed bundle using the corresponding public key and gets PASS/FAIL
  3. Existing HMAC-signed bundles from v0.3.0 verify successfully without any modification
  4. Verifier auto-detects signing algorithm from key file version field (hmac-sha256-v1 vs ed25519-v1)
  5. A bundle self-declaring one algorithm while the verifier holds a key of a different type is rejected (downgrade attack prevention)
**Plans:** 2/2 plans complete

Plans:
- [ ] 02-01-PLAN.md -- Dual-algorithm dispatch in mg_sign.py with Ed25519 signing tests (SIGN-03, SIGN-04, SIGN-06, SIGN-07, SIGN-08)
- [ ] 02-02-PLAN.md -- CLI keygen update for mg.py and mg_sign.py with full regression gate (SIGN-03, SIGN-06)

### Phase 3: Temporal Commitment
**Goal**: Users can embed a temporal commitment (proving WHEN a bundle was signed) as an independent Layer 5 that works offline and degrades gracefully
**Depends on**: Phase 2
**Requirements**: TEMP-01, TEMP-02, TEMP-03, TEMP-04, TEMP-05, TEMP-06
**Success Criteria** (what must be TRUE):
  1. Signing a bundle with network access captures a NIST Beacon pulse and embeds a temporal commitment in the bundle
  2. Signing a bundle without network access completes successfully with temporal field set to "not available"
  3. Verifying a bundle with temporal data checks the cryptographic binding (SHA-256 of root_hash + beacon_value + timestamp) independently of Layers 1-4
  4. Temporal verification works fully offline -- checks embedded data structure, never makes network calls during verify
  5. Pre-commitment hash scheme allows proving a bundle existed before the beacon pulse it references
**Plans:** 1/2 plans executed

Plans:
- [ ] 03-01-PLAN.md -- TDD: mg_temporal.py core module with NIST Beacon fetch, pre-commitment, binding, verification (TEMP-01, TEMP-02, TEMP-03, TEMP-04, TEMP-05, TEMP-06)
- [ ] 03-02-PLAN.md -- CLI integration: mg_sign.py auto-temporal + temporal subcommand + mg.py Layer 5 verify (TEMP-01, TEMP-03, TEMP-04, TEMP-05)

### Phase 4: Adversarial Proofs and Polish
**Goal**: All new capabilities are proven through adversarial tests, deep_verify expands to 13 tests, and all documentation counters reflect v0.4.0 state
**Depends on**: Phase 3
**Requirements**: CERT-01, CERT-02, CERT-03, CERT-04, CERT-05, CERT-06, DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. deep_verify.py runs 13 tests (up from 10) and all pass, including Test 11 (signing integrity), Test 12 (reproducibility), Test 13 (temporal commitment)
  2. CERT-09 test gauntlet proves Ed25519-specific attack scenarios are caught
  3. CERT-10 test gauntlet proves temporal attack scenarios (replay, future-date, beacon forge) are caught
  4. 5-layer independence proof demonstrates each layer catches attacks the others miss
  5. All counters across index.html, README.md, AGENTS.md, llms.txt, system_manifest.json, and CONTEXT_SNAPSHOT.md reflect the new test count, layer count, and innovation count
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD
- [ ] 04-03: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Ed25519 Foundation | 2/2 | Complete | 2026-03-17 |
| 2. Signing Upgrade | 2/2 | Complete   | 2026-03-18 |
| 3. Temporal Commitment | 1/2 | In Progress|  |
| 4. Adversarial Proofs and Polish | 0/3 | Not started | - |

---
*Roadmap created: 2026-03-16*
*Last updated: 2026-03-18*
