# Roadmap: MetaGenesis Core

## Overview

This roadmap tracks MetaGenesis Core milestones. v0.4.0 added Ed25519 signing and temporal commitment. v0.5.0 hardened coverage with adversarial proof suites CERT-11/12. v1.0.0 made the project client-ready with pilot onboarding automation, 91.9% coverage, and academic citation infrastructure. v2.0.0 transforms the protocol into a self-verifying, client-ready standard with response infrastructure, recursive integrity, and architectural seeds for the future.

## Milestones

- **v0.4.0 Protocol Hardening** - Phases 1-4 (shipped 2026-03-18)
- **v0.5.0 Coverage Hardening** - Phases 5-8 (shipped 2026-03-18)
- **v1.0.0 First Client** - Phases 9-13 (shipped 2026-04-04)
- **v2.0.0 Autonomous Evolution** - Phases 14-22 (in progress)

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

### v2.0.0 Autonomous Evolution (Phases 14-22)

**Milestone Goal:** Transform MetaGenesis Core from a protocol into a self-verifying, client-ready standard with response infrastructure, recursive integrity, and architectural seeds for the future.

- [x] **Phase 14: Health Check and Coverage Foundation** - Verify all gates green, confirm ENV_002, update policy gate allow_globs for new output directories (completed 2026-04-04)
- [x] **Phase 15: Protocol Self-Audit** - mg_self_audit.py with Ed25519-signed baseline for 8 core scripts and Check #20 in agent_evolution.py
 (completed 2026-04-04)
- [x] **Phase 16: Verification Receipt** - mg_receipt.py generates human-readable proof for clients and auditors, integrated into mg_client.py
 (completed 2026-04-04)
- [x] **Phase 17: Response Infrastructure** - agent_responder.py with 7 domain mappings, draft generation, and queue management for 60-second reply kits (completed 2026-04-04)
- [ ] **Phase 18: Evolution Council** - agent_evolution_council.py reads 6 data sources and produces ranked improvement proposals
- [ ] **Phase 19: Agent Charter and Governance** - docs/AGENT_CHARTER.md with constitutional governance for autonomous agents
- [ ] **Phase 20: Protocol Hardening** - PROTOCOL.md deepening, mg.py inline WHY comments, CLAUDE.md updates for new scripts and counts
- [ ] **Phase 21: Hidden Potential Audit** - 8-lens investigation of untapped system capabilities, build most important finding
- [ ] **Phase 22: Vision Seeds and Counter Sync** - docs/ROADMAP_VISION.md with 4 evolution levels, final counter sync across all docs

## Phase Details

### Phase 14: Health Check and Coverage Foundation
**Goal**: All verification gates are green and infrastructure is ready for new output directories
**Depends on**: Phase 13 (v1.0.0 complete)
**Requirements**: HARD-03, HARD-05
**Success Criteria** (what must be TRUE):
  1. All 5 verification gates pass (steward_audit, pytest, deep_verify, check_stale_docs, agent_diff_review)
  2. known_faults.yaml contains ENV_002 entry documenting deep_verify.py coverage exclusion
  3. mg_policy_gate_policy.json allow_globs includes reports/receipts/**, reports/response_drafts/**, reports/response_bundles/**
**Plans**: 1 plan
Plans:
- [ ] 14-01-PLAN.md -- Verify gates, confirm ENV_002, add policy gate allow_globs, coverage baseline

### Phase 15: Protocol Self-Audit
**Goal**: The protocol can verify its own integrity by detecting tampered core scripts
**Depends on**: Phase 14
**Requirements**: SELF-01, SELF-02, SELF-03, SELF-04, SELF-05, SELF-06
**Success Criteria** (what must be TRUE):
  1. Running `mg_self_audit.py --init` creates an Ed25519-signed hash baseline of 8 core scripts
  2. Modifying any core script and running `mg_self_audit.py` produces SELF-AUDIT FAIL with the changed file identified
  3. Running `mg_self_audit.py --update` re-baselines after intentional changes with a confirmation prompt
  4. `python scripts/agent_evolution.py` reports Check #20 "self_audit" as PASS when baseline exists and scripts are unmodified
  5. 15+ tests pass covering tamper detection, signature validation, update workflow, missing baseline, missing file, and edge cases
**Plans**: TBD

### Phase 16: Verification Receipt
**Goal**: Clients and auditors receive human-readable proof after every successful verification
**Depends on**: Phase 15
**Requirements**: RCPT-01, RCPT-02, RCPT-03, RCPT-04, RCPT-05, RCPT-06
**Success Criteria** (what must be TRUE):
  1. Running `mg_receipt.py --pack bundle.zip` prints a human-readable receipt and saves it to reports/receipts/{trace_id}_receipt.txt
  2. Receipts for anchored claims (MTR, PHYS, DT-FEM, DRIFT) display the physical anchor line with the constant and its source
  3. Receipts for non-anchored claims display "Tamper-evident provenance only" with SCOPE_001 reference
  4. FAIL bundles produce a clear error message and no receipt file
  5. mg_client.py automatically generates a receipt after every PASS verification
**Plans**: TBD

### Phase 17: Response Infrastructure
**Goal**: Any outreach reply can be answered with a complete response kit (draft + bundle + queue entry) in 60 seconds
**Depends on**: Phase 16
**Requirements**: RESP-01, RESP-02, RESP-03, RESP-04, RESP-05, RESP-06, RESP-07
**Success Criteria** (what must be TRUE):
  1. Running `agent_responder.py --prepare <contact>` produces a response draft, domain-specific bundle, and queue entry in under 60 seconds
  2. All 7 domain mappings resolve correctly (Patronus, BV, Chollet, Percy Liang, IQVIA, LMArena, South Pole)
  3. Draft text reads naturally without AI markers, special unicode, or em-dashes
  4. response_queue.json tracks status flow: prepared, reviewed, bundle_sent, replied, converted
  5. Running `--status` shows all pending kits with age; `--list-domains` shows available mappings
**Plans**: TBD

### Phase 18: Evolution Council
**Goal**: The system can analyze itself and produce evidence-based improvement proposals ranked by impact
**Depends on**: Phase 17
**Requirements**: EVOL-01, EVOL-02, EVOL-03, EVOL-04
**Success Criteria** (what must be TRUE):
  1. agent_evolution_council.py reads all 6 data sources (agent_learn recall, coverage report, known_faults, agent_evolution, response_queue, git log)
  2. Running the script produces .planning/EVOLUTION_PROPOSALS.md with up to 10 proposals sorted by impact/effort ratio
  3. Running `--summary` prints the top 3 proposals to stdout
  4. 15+ tests pass covering analysis logic, proposal generation, ranking, empty sources, and edge cases
**Plans**: TBD

### Phase 19: Agent Charter and Governance
**Goal**: Autonomous agent boundaries are formally documented with clear permission/escalation rules
**Depends on**: Phase 18
**Requirements**: GOVN-01, GOVN-02, GOVN-03
**Success Criteria** (what must be TRUE):
  1. docs/AGENT_CHARTER.md exists with all 7 sections: permissions, approvals, communication, escalation, memory, prime directive, banned terms
  2. The charter draws a clear boundary between autonomous agent actions and human-approval-required actions
  3. The prime directive is documented: every agent action must make the verification protocol more trustworthy
**Plans**: TBD

### Phase 20: Protocol Hardening
**Goal**: Protocol documentation is deepened with plain-language explanations and inline code rationale
**Depends on**: Phase 19
**Requirements**: HARD-01, HARD-02, HARD-04
**Success Criteria** (what must be TRUE):
  1. PROTOCOL.md Physical Anchor section includes plain-language prose explaining kB and SI 2019 significance
  2. mg.py contains inline WHY comments for 5 key design decisions (5 layers, semantic layer, Ed25519, NIST Beacon, step chain)
  3. CLAUDE.md file map includes all new v2.0.0 scripts, check count reflects 20 (was 19), and references agent charter and vision doc
**Plans**: TBD

### Phase 21: Hidden Potential Audit
**Goal**: Untapped system capabilities are identified through systematic investigation and the most valuable finding is built
**Depends on**: Phase 20
**Requirements**: HUNT-01, HUNT-02, HUNT-03
**Success Criteria** (what must be TRUE):
  1. 8-lens investigation completed (first user, regulator, attacker, researcher 2075, client sim, pattern detective, semantic coverage, synthesis)
  2. .planning/HIDDEN_POTENTIAL.md exists with all 8 sections and findings
  3. The most important finding for a real client receiving their first bundle is implemented and tested
**Plans**: TBD

### Phase 22: Vision Seeds and Counter Sync
**Goal**: The long-term evolution path is documented and all documentation counters are consistent
**Depends on**: Phase 21
**Requirements**: VISN-01, VISN-02
**Success Criteria** (what must be TRUE):
  1. docs/ROADMAP_VISION.md documents 4 evolution levels: Protocol, Registry, Agent Economy, Self-Evolution
  2. Each level includes minimum viable pilot, first identifiable client, academic publication, and estimated duration
  3. All documentation counters (test count, claim count, check count, script references) are consistent across every file checked by check_stale_docs.py
**Plans**: TBD

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1-4 | v0.4.0 | 7/7 | Complete | 2026-03-18 |
| 5-8 | v0.5.0 | 9/9 | Complete | 2026-03-18 |
| 9-13 | v1.0.0 | 5/5 | Complete | 2026-04-04 |
| 14. Health Check and Coverage Foundation | v2.0.0 | 0/1 | Complete    | 2026-04-04 |
| 15. Protocol Self-Audit | v2.0.0 | 0/0 | Complete    | 2026-04-04 |
| 16. Verification Receipt | v2.0.0 | 0/0 | Complete    | 2026-04-04 |
| 17. Response Infrastructure | v2.0.0 | 1/1 | Complete    | 2026-04-04 |
| 18. Evolution Council | v2.0.0 | 0/0 | Not started | - |
| 19. Agent Charter and Governance | v2.0.0 | 0/0 | Not started | - |
| 20. Protocol Hardening | v2.0.0 | 0/0 | Not started | - |
| 21. Hidden Potential Audit | v2.0.0 | 0/0 | Not started | - |
| 22. Vision Seeds and Counter Sync | v2.0.0 | 0/0 | Not started | - |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-04-04 -- Phase 17 Response Infrastructure complete*
