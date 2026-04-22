# Roadmap: MetaGenesis Core

## Overview

This roadmap tracks MetaGenesis Core milestones. v0.4.0 added Ed25519 signing and temporal commitment. v0.5.0 hardened coverage with adversarial proof suites CERT-11/12. v1.0.0 made the project client-ready with pilot onboarding automation, 91.9% coverage, and academic citation infrastructure. v2.0.0 transforms the protocol into a self-verifying, client-ready standard with response infrastructure, recursive integrity, and architectural seeds for the future. v3.0.0 pushes real_ratio to 50% by verifying all 20 claims with real external data and delivering end-to-end client demo flow. v3.1.0 (docs only, no new claims) expands domain coverage and produces century-level client-facing documentation so a domain expert reads once and immediately understands problem, solution, and next action.

## Milestones

- **v0.4.0 Protocol Hardening** - Phases 1-4 (shipped 2026-03-18)
- **v0.5.0 Coverage Hardening** - Phases 5-8 (shipped 2026-03-18)
- **v1.0.0 First Client** - Phases 9-13 (shipped 2026-04-04)
- **v2.0.0 Autonomous Evolution** - Phases 14-22 (shipped 2026-04-04)
- **v3.0.0 Client-Ready Protocol** - Phases 23-27 (shipped 2026-04-11)
- **v3.1.0 Documentation Deep Pass** - Phases 28-32 (in progress)

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

<details>
<summary>v3.0.0 Client-Ready Protocol (Phases 23-27) - SHIPPED 2026-04-11</summary>

- [x] **Phase 23: Real Verification** - Run all 20 active claims with real external data via mg_claim_builder.py, produce signed bundles grouped by domain (completed 2026-04-07)
- [x] **Phase 24: Client Demo Flow** - Single-command demo script: pick domain, run claims, bundle, verify, receipt -- works offline (completed 2026-04-07)
- [x] **Phase 25: Client-Facing Documentation** - COMMERCIAL.md, SECURITY.md, docs/PROTOCOL.md for client trust (completed 2026-04-07)
- [x] **Phase 26: Counter Sync and Gate Hardening** - All counters consistent, check_stale_docs rules updated, all 5 gates green at ship (completed 2026-04-07)
- [x] **Phase 27: Polish and Debt Cleanup** - Fix receipt reproduce commands, system_manifest ratio regression, receipt Result field fidelity, re-run gates (completed 2026-04-07)

</details>

### v3.1.0 Documentation Deep Pass (In Progress)

**Milestone Goal:** Expand domain coverage and produce century-level client-facing documentation so a domain expert reads once and immediately understands problem, solution, and next action — closing the gap between a technically complete protocol (v3.0.0) and a protocol that sells itself to a serious evaluator. Docs only — NO new claims.

- [ ] **Phase 28: USE_CASES Deep Rewrite** - Rewrite docs/USE_CASES.md to cover 14 domains with real incidents, exact regulatory citations, and verified 3-step integration paths
- [ ] **Phase 29: Client Journeys** - Create docs/CLIENT_JOURNEY.md with 6 persona journeys tied to concrete regulatory triggers and verified CLI commands
- [ ] **Phase 30: Why Not Alternatives** - Create docs/WHY_NOT_ALTERNATIVES.md with 10-tool composability comparison, CERT-02 strip-recompute walk-through, and rerun-cost math
- [ ] **Phase 31: Regulatory Gaps and README** - Expand docs/REGULATORY_GAPS.md from 3 to 24+ regulations with exact clauses; update README.md Deep Reading table with new docs
- [ ] **Phase 32: Audit and Readiness Assessment** - Pass 8-gate full audit; create reports/READINESS_ASSESSMENT.md with honest 7-section world-readiness verdict

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
**Plans:** 2/2 plans complete
Plans:
- [x] 26-01-PLAN.md — Counter sync across all documentation files + check_stale_docs.py rules
- [x] 26-02-PLAN.md — Run all 5 verification gates and fix failures

### Phase 27: Polish and Debt Cleanup
**Goal**: Fix integration gap (receipt reproduce commands) and tech debt (system_manifest ratio, receipt Result field) identified by milestone audit
**Depends on**: Phase 26 (all phases complete, audit done)
**Requirements**: Gap closure — no new REQ-IDs
**Gap Closure**: Closes gaps from v3.0.0-MILESTONE-AUDIT.md
**Success Criteria** (what must be TRUE):
  1. Receipt reproduce commands work: `python scripts/mg.py verify --pack <bundle.zip>` succeeds (or receipt shows correct extraction step)
  2. system_manifest.json shows real_to_synthetic_ratio >= 0.50 (matches index.json reality)
  3. Receipt Result field shows domain-specific metric instead of "See bundle for details"
  4. All 5 verification gates still pass after fixes
**Plans:** 1/1 plans complete
Plans:
- [x] 27-01-PLAN.md — Fix receipt reproduce commands, system_manifest ratio, receipt Result field

### Phase 28: USE_CASES Deep Rewrite
**Goal**: A domain expert opens `docs/USE_CASES.md` and finds their domain explained with a real named incident, an exact regulatory citation, and three copy-pasteable commands that actually work against the shipped SDK and CLI
**Depends on**: Phase 27 (v3.0.0 complete, research corpus available in .planning/research/)
**Requirements**: UC-01, UC-02, UC-03, UC-04, UC-05
**Success Criteria** (what must be TRUE):
  1. `docs/USE_CASES.md` exists on disk and covers 14 distinct domains (8 existing + 6 new: algorithmic trading, automotive simulation, quantum computing, scientific research & peer review, aerospace certification, medical devices)
  2. Every one of the 14 domain sections contains all 6 subsections: The computation / What happens when verification fails / The cost equation / Unique MetaGenesis properties / Integration — 3 steps / Regulatory requirement
  3. Every "What happens when verification fails" subsection names a real incident with year, a consequence figure in dollars or lives, and a primary-source URL drawn from `.planning/research/INCIDENTS.md` (22 verified incidents available); the 3 governance-failure incidents (Theranos, Challenger, LIBOR) are framed as "would have bounded the damage," never "would have prevented"
  4. Every "Regulatory requirement" subsection cites at least one exact article, clause, or paragraph number drawn from `.planning/research/REGULATIONS.md`; 0 banned terms across the file per `python scripts/check_stale_docs.py`
  5. Every CLI command shown in an "Integration — 3 steps" subsection is verified against `sdk/metagenesis.py`, `scripts/mg.py`, or `scripts/mg_client.py` with zero invented flags
**Plans**: TBD

### Phase 29: Client Journeys
**Goal**: A prospective client recognizes themselves on page one of `docs/CLIENT_JOURNEY.md`, sees the exact trigger that made someone like them adopt the protocol, and walks through three commands that any engineer on their team could run today
**Depends on**: Phase 27 (v3.0.0 complete, PERSONAS.md research ready)
**Requirements**: CJ-01, CJ-02, CJ-03
**Success Criteria** (what must be TRUE):
  1. `docs/CLIENT_JOURNEY.md` exists on disk and contains 6 complete persona journeys in this order: ML engineer at AI startup, computational chemist at biotech, model risk manager at bank, FEM engineer at aerospace/automotive supplier, quant analyst at hedge fund, research scientist
  2. Every journey has all 6 subsections: Who this person is / The exact trigger moment / Three steps with real commands / What verifier does / What changes after / Time and cost
  3. Every "exact trigger moment" is tied to a specific regulatory citation or concrete audit event from the set: SOC 2 CC7.2, FDA IND / FDA AI Credibility Framework, ECB TRIM / SR 11-7, AS9100D 8.3.5, MiFID II Art. 17, peer-review reproducibility track / NIH DMP
  4. Every CLI command in every "Three steps" block is verified against `sdk/metagenesis.py`, `scripts/mg.py`, `scripts/mg_client.py` with zero invented flags, matching the verification already performed in `.planning/research/PERSONAS.md`
**Plans**: TBD

### Phase 30: Why Not Alternatives
**Goal**: A skeptical technical reader opens `docs/WHY_NOT_ALTERNATIVES.md` expecting "MetaGenesis vs X" and instead finds "X + MetaGenesis," a concrete attack walk-through that maps to an actual test file, and three domains where rerunning simply is not an option
**Depends on**: Phase 27 (v3.0.0 complete, ALTERNATIVES.md research ready, tests/steward/test_cert02_*.py stable)
**Requirements**: ALT-01, ALT-02, ALT-03, ALT-04, ALT-05
**Success Criteria** (what must be TRUE):
  1. `docs/WHY_NOT_ALTERNATIVES.md` exists on disk and contains exactly 3 sections
  2. Section 1 includes a comparison table covering at minimum: SHA-256 alone, Docker, MLflow/DVC, Manual audit, Signed PDF, Git history — and for each tool the table states what it solves well, what it cannot solve, and a concrete failure example
  3. Section 2 walks through the CERT-02 strip-and-recompute attack step by step, and each narrated step matches an actual step in `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` (no invented steps) — attacker strips evidence, recomputes every SHA-256, resorts the manifest, recomputes root_hash, Layer 1 PASSES, Layer 2 `_verify_semantic()` FAILS
  4. Section 3 explains why rerunning is not verification using three concrete domains — ML training (GPT-3 rerun cost + GPU non-determinism), FEM/CFD (billion-cell mesh + MPI-reduction non-associativity), Monte Carlo VaR (seeded bit-equality fails by construction) — every figure traceable to a primary source
  5. Framing across the entire file is composability ("X + MetaGenesis" = verifiable X), never "MetaGenesis vs X"; 0 banned terms per `python scripts/check_stale_docs.py`
**Plans**: TBD

### Phase 31: Regulatory Gaps and README
**Goal**: A compliance officer opens `docs/REGULATORY_GAPS.md` and finds their regulation by name with the exact clause the protocol satisfies, the exact clauses it does not, and the reason; and a new reader opens the README Deep Reading table and sees the three new docs listed with one-line descriptions
**Depends on**: Phase 27 (v3.0.0 complete, REGULATIONS.md research ready); independent of Phases 28-30
**Requirements**: RG-01, RG-02, RG-03, RG-04, RM-01
**Success Criteria** (what must be TRUE):
  1. `docs/REGULATORY_GAPS.md` exists on disk and covers 24+ regulations grouped into 6 buckets: Financial / Pharma + Medical / Automotive + Aerospace / Science / AI + Cryptography / Climate + ESG
  2. Every one of the 24+ regulation entries carries an exact article, clause, or section number AND an authoritative-source link (EUR-Lex, ecfr.gov, NIST CSRC, IFRS Foundation, ISO.org, UNECE, AICPA, grants.nih.gov, cOAlition S, ALLEA)
  3. Honest [GAP] flags are preserved for boundaries MetaGenesis does not cover: training-data lineage (EU AI Act Art. 10), human oversight (EU AI Act Art. 14), organizational governance (SR 11-7 Sec V, SOC 2 CC1-CC4), design-document certification (510(k), IEC 62304, DO-178C, AS9100D), post-quantum signing (FIPS 204 migration), HARA/FMEDA (ISO 26262)
  4. The single `[CITATION UNVERIFIED]` flag on DO-178C Table A-7 objective #9 is carried forward verbatim from `.planning/research/REGULATIONS.md` §3.6
  5. `README.md` Deep Reading table has three new rows linking to `docs/USE_CASES.md`, `docs/CLIENT_JOURNEY.md`, and `docs/WHY_NOT_ALTERNATIVES.md`, each with a one-line description
**Plans**: TBD

### Phase 32: Audit and Readiness Assessment
**Goal**: All 8 verification gates pass on a clean checkout, and `reports/READINESS_ASSESSMENT.md` gives an honest 7-section verdict on whether this protocol is actually ready to face a serious technical evaluator — with Yes/No answers, not marketing language
**Depends on**: Phase 28, Phase 29, Phase 30, Phase 31 (all four docs must exist before the audit can verify them and before the readiness assessment can cite final content)
**Requirements**: AUD-01, AUD-02, AUD-03, AUD-04, AUD-05, AUD-06, AUD-07, AUD-08, RDY-01, RDY-02, RDY-03, RDY-04, RDY-05
**Success Criteria** (what must be TRUE):
  1. All 8 gates pass on a clean run: `python scripts/steward_audit.py` → STEWARD AUDIT: PASS; `python -m pytest tests/ -q` → 2407 passed; `python scripts/deep_verify.py` → ALL 13 TESTS PASSED; `python scripts/check_stale_docs.py --strict` → exit 0 (with `scripts/check_stale_docs.py` required strings updated in the SAME PR per UPDATE_PROTOCOL v1.1 if any counter changed); `python scripts/agent_evolution.py --summary` → ALL 22 CHECKS PASSED; `python demos/client_scenarios/run_all_scenarios.py` → 4/4 PASS; `python demos/open_data_demo_01/run_demo.py` → PASS PASS; `python -c "from sdk.metagenesis import MetaGenesisClient; print(MetaGenesisClient())"` → OK
  2. `reports/READINESS_ASSESSMENT.md` exists on disk and contains all 7 sections: Technical completeness / Documentation completeness / Domain coverage / Regulatory positioning / What is missing before v1.0.0 / Honest readiness verdict / The numbers tell a story
  3. Every claim in every section cites specific numbers drawn from `system_manifest.json`, `reports/scientific_claim_index.md`, and the `.planning/research/` files — no invented statistics; 0 banned terms per `python scripts/check_stale_docs.py`
  4. Section 6 gives explicit Yes/No verdicts for: (a) Is the protocol ready for first real client? (b) Is the documentation ready to present to a serious technical evaluator? (c) What is the single most important next action?
  5. Honest flags are preserved verbatim: FAULT_005, FAULT_006, SCOPE_001, and the 5 prioritised-but-unimplemented future claims (AUTO-OTA-01, CLIMATE-01, TRADING-01, EDC-01, DOC-HASH-01) listed as "planned future additions (not yet implemented in v1.0.0-rc1)" — never written up as if they exist; Section 7 uses numbers only, no adjectives, no marketing language
**Plans**: TBD

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
| 26. Counter Sync + Gates | v3.0.0 | 2/2 | Complete   | 2026-04-07 |
| 27. Polish and Debt Cleanup | v3.0.0 | 1/1 | Complete   | 2026-04-07 |
| 28. USE_CASES Deep Rewrite | v3.1.0 | 0/? | Not started | — |
| 29. Client Journeys | v3.1.0 | 0/? | Not started | — |
| 30. Why Not Alternatives | v3.1.0 | 0/? | Not started | — |
| 31. Regulatory Gaps + README | v3.1.0 | 0/? | Not started | — |
| 32. Audit + Readiness Assessment | v3.1.0 | 0/? | Not started | — |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-04-16 -- v3.1.0 Documentation Deep Pass milestone planned: Phases 28-32 mapping 31 requirements (UC-01..05, CJ-01..03, ALT-01..05, RG-01..04, RM-01, AUD-01..08, RDY-01..05)*
