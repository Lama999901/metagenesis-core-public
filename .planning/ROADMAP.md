# Roadmap: MetaGenesis Core

## Overview

This roadmap tracks MetaGenesis Core milestones. v0.4.0 added Ed25519 signing and temporal commitment. v0.5.0 hardened coverage with adversarial proof suites CERT-11/12. v1.0.0 made the project client-ready with pilot onboarding automation, 91.9% coverage, and academic citation infrastructure. v2.0.0 transforms the protocol into a self-verifying, client-ready standard with response infrastructure, recursive integrity, and architectural seeds for the future. v3.0.0 pushes real_ratio to 50% by verifying all 20 claims with real external data and delivering end-to-end client demo flow.

## Milestones

- **v0.4.0 Protocol Hardening** - Phases 1-4 (shipped 2026-03-18)
- **v0.5.0 Coverage Hardening** - Phases 5-8 (shipped 2026-03-18)
- **v1.0.0 First Client** - Phases 9-13 (shipped 2026-04-04)
- **v2.0.0 Autonomous Evolution** - Phases 14-22 (shipped 2026-04-04)
- **v3.0.0 Client-Ready Protocol** - Phases 23-26 (in progress)

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

<details>
<summary>v0.5.0 Coverage Hardening (Phases 5-8) - SHIPPED 2026-03-18</summary>

- [x] **Phase 5: Foundation** - Step chain structural tests for all 14 claims, runner error paths, governance meta-tests
- [x] **Phase 6: Layer Hardening** - Semantic edge cases, cross-claim cascade failures, manifest rollback attack
- [x] **Phase 7: Flagship Proofs** - CERT-11 coordinated multi-vector attack, CERT-12 encoding attacks
- [x] **Phase 8: Counter Updates** - All documentation counters reflect final test count

</details>

<details>
<summary>v1.0.0 First Client (Phases 9-13) - SHIPPED 2026-04-04</summary>

- [x] **Phase 9: Academic Infrastructure** - Zenodo DOI metadata, CITATION.cff currency, README badge, paper.md cross-references (completed 2026-04-03)
- [x] **Phase 10: Coverage Hardening** - Dedicated tests for check_stale_docs, agent_evolve_self, agent_research, agent_coverage to reach 90%+ (completed 2026-04-03)
- [x] **Phase 11: Client Onboarding Automation** - agent_pilot.py end-to-end: form ingestion, domain detection, bundle generation, email draft, queue tracking (completed 2026-04-03)
- [x] **Phase 12: Agent Evolution** - Pilot queue staleness detector (#5) in agent_pr_creator.py with tests (completed 2026-04-03)
- [x] **Phase 13: System Hardening** - Gap analysis, counter consistency, all verification gates green (completed 2026-04-03)

See `.planning/milestones/v1.0.0-ROADMAP.md` for full phase details.

</details>

<details>
<summary>v2.0.0 Autonomous Evolution (Phases 14-22) - SHIPPED 2026-04-04</summary>

- [x] **Phase 14: Health Check and Coverage Foundation** — gates green, ENV_002, policy gate (completed 2026-04-04)
- [x] **Phase 15: Protocol Self-Audit** — mg_self_audit.py Ed25519-signed baseline, Check #20 (completed 2026-04-04)
- [x] **Phase 16: Verification Receipt** — mg_receipt.py human-readable proof (completed 2026-04-04)
- [x] **Phase 17: Response Infrastructure** — agent_responder.py 60-second reply kits (completed 2026-04-04)
- [x] **Phase 18: Evolution Council** — agent_evolution_council.py self-analysis, 40 tests (completed 2026-04-04)
- [x] **Phase 19: Agent Charter and Governance** — docs/AGENT_CHARTER.md 7-section governance (completed 2026-04-04)
- [x] **Phase 20: Protocol Hardening** — PROTOCOL.md prose, mg.py WHY comments, CLAUDE.md updates (completed 2026-04-04)
- [x] **Phase 21: Hidden Potential Audit** — mg_verify_standalone.py zero-dependency verifier (completed 2026-04-04)
- [x] **Phase 22: Vision Seeds and Counter Sync** — docs/ROADMAP_VISION.md, counter sync (completed 2026-04-04)

See `.planning/milestones/v2.0.0-ROADMAP.md` for full phase details.

</details>

### v3.0.0 Client-Ready Protocol (In Progress)

**Milestone Goal:** Push real_ratio from 4.8% to 50% by verifying all 20 active claims with real external data, delivering end-to-end client demo flow, and hardening all gates for ship.

- [x] **Phase 23: Real Verification** - Run all 20 active claims with real external data via mg_claim_builder.py, produce signed bundles grouped by domain (completed 2026-04-07)
- [x] **Phase 24: Client Demo Flow** - Single-command demo script: pick domain, run claims, bundle, verify, receipt -- works offline (completed 2026-04-07)
- [x] **Phase 25: Client-Facing Documentation** - COMMERCIAL.md, SECURITY.md, docs/PROTOCOL.md for client trust (completed 2026-04-07)
- [ ] **Phase 26: Counter Sync and Gate Hardening** - All counters consistent, check_stale_docs rules updated, all 5 gates green at ship

## Phase Details

### Phase 23: Real Verification
**Goal**: All 20 active claims are verified with real external data, producing signed bundles that any auditor can independently verify offline
**Depends on**: Phase 22 (v2.0.0 complete)
**Requirements**: REAL-01, REAL-02, REAL-03, REAL-04, REAL-05
**Success Criteria** (what must be TRUE):
  1. Running `mg_claim_builder.py` with real external data produces a signed bundle for each of the 20 active claims
  2. Bundles are organized in proof_library/bundles/ grouped by domain (ML, pharma, finance, digital_twin, materials, physics)
  3. Every bundle passes `python scripts/mg.py verify --pack <bundle>` independently
  4. `python scripts/agent_evolution.py` check #21 (real_ratio) shows 50% (20 real / 40 total) and reports PASS
**Plans:** 3/3 plans complete
Plans:
- [x] 23-01-PLAN.md — Create 20 real input data files and run_single_claim.py helper
- [x] 23-02-PLAN.md — Create batch runner and execute all 20 claim verifications
- [x] 23-03-PLAN.md — Tests and final verification (all bundles PASS, check #21 PASS)

### Phase 24: Client Demo Flow
**Goal**: A prospective client can run a single command to see the full verification flow for any domain -- from data to bundle to receipt
**Depends on**: Phase 23 (bundles exist to demo)
**Requirements**: DEMO-01, DEMO-02, DEMO-03
**Success Criteria** (what must be TRUE):
  1. User runs one command, picks a domain, and sees claims run, bundle created, verification PASS, and human-readable receipt printed
  2. Each domain demo produces a receipt file via mg_receipt.py that a non-technical person can read and understand
  3. Demo completes fully with no network access (temporal layer degrades gracefully)
**Plans:** 1/1 plans complete
Plans:
- [x] 24-01-PLAN.md -- mg_demo.py script + tests (domain picker, bundle verification, receipt generation)

### Phase 25: Client-Facing Documentation
**Goal**: A prospective client finds answers to "how much does it cost," "is it secure," and "how does the protocol work" without reading source code
**Depends on**: Phase 23 (real bundles inform documentation claims)
**Requirements**: DOCS-03, DOCS-04, DOCS-05
**Success Criteria** (what must be TRUE):
  1. COMMERCIAL.md exists with pricing ($299), pilot flow description, and Stripe payment link
  2. SECURITY.md exists with threat model and explanation of how each of the 5 verification layers defends against specific attack classes
  3. docs/PROTOCOL.md exists with protocol specification prose that explains the verification flow end-to-end
**Plans:** 1/1 plans complete
Plans:
- [x] 25-01-PLAN.md — Update COMMERCIAL.md (Stripe link, pilot flow) and SECURITY.md (attack class table, threat model)

### Phase 26: Counter Sync and Gate Hardening
**Goal**: Every counter, every gate, and every stale-docs rule is consistent and green -- the project ships clean
**Depends on**: Phase 23, Phase 24, Phase 25 (all work complete, final counts known)
**Requirements**: DOCS-01, DOCS-02, GATE-01, GATE-02, GATE-03, GATE-04, GATE-05
**Success Criteria** (what must be TRUE):
  1. All counters match across index.html, README.md, AGENTS.md, llms.txt, system_manifest.json, and CONTEXT_SNAPSHOT.md
  2. check_stale_docs.py rules are updated to match final counts and `python scripts/check_stale_docs.py --strict` passes
  3. All 5 verification gates pass: steward_audit PASS, pytest passes with current count, deep_verify 13/13, agent_evolution 21/21 checks, agent_diff_review PASS
**Plans:** 1/2 plans executed
Plans:
- [x] 26-01-PLAN.md — Counter sync across all documentation files + check_stale_docs.py rules
- [ ] 26-02-PLAN.md — Run all 5 verification gates and fix failures

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1-4 | v0.4.0 | - | Complete | 2026-03-18 |
| 5-8 | v0.5.0 | - | Complete | 2026-03-18 |
| 9-13 | v1.0.0 | - | Complete | 2026-04-04 |
| 14-22 | v2.0.0 | - | Complete | 2026-04-04 |
| 23. Real Verification | v3.0.0 | 3/3 | Complete   | 2026-04-07 |
| 24. Client Demo Flow | v3.0.0 | 1/1 | Complete   | 2026-04-07 |
| 25. Client-Facing Docs | v3.0.0 | 1/1 | Complete   | 2026-04-07 |
| 26. Counter Sync + Gates | v3.0.0 | 1/2 | In Progress|  |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-04-07 -- Phase 26 planned: 2 plans in 2 waves
