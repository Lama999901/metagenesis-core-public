# Roadmap: MetaGenesis Core

## Overview

This roadmap covers two milestones. v0.5.0 hardened coverage from 391 to 526+ tests with adversarial proof suites CERT-11 and CERT-12. v1.0.0 makes MetaGenesis Core client-ready by adding academic citation infrastructure, boosting coverage to 90%+, automating pilot onboarding end-to-end, upgrading autonomous agents with a pilot queue staleness detector, and running a final hardening pass to ensure zero gaps before the first $299 client.

## Milestones

- **v0.4.0 Protocol Hardening** - Phases 1-4 (shipped 2026-03-18)
- **v0.5.0 Coverage Hardening** - Phases 5-8 (shipped 2026-03-18)
- **v1.0.0 First Client** - Phases 9-13 (in progress)

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

### v1.0.0 First Client

- [ ] **Phase 9: Academic Infrastructure** - Zenodo DOI metadata, CITATION.cff currency, README badge, paper.md cross-references
- [x] **Phase 10: Coverage Hardening** - Dedicated tests for check_stale_docs, agent_evolve_self, agent_research, agent_coverage to reach 90%+ (completed 2026-04-03)
- [x] **Phase 11: Client Onboarding Automation** - agent_pilot.py end-to-end: form ingestion, domain detection, bundle generation, email draft, queue tracking (completed 2026-04-03)
- [x] **Phase 12: Agent Evolution** - Pilot queue staleness detector (#5) in agent_pr_creator.py with tests (completed 2026-04-03)
- [ ] **Phase 13: System Hardening** - Gap analysis, counter consistency, all verification gates green

## Phase Details

### Phase 9: Academic Infrastructure
**Goal**: MetaGenesis Core has complete academic citation infrastructure ready for Zenodo DOI minting and JOSS resubmission
**Depends on**: Phase 8 (v0.5.0 complete, 1634 tests baseline)
**Requirements**: DOI-01, DOI-02, DOI-03, DOI-04
**Success Criteria** (what must be TRUE):
  1. .zenodo.json contains correct metadata including test count 1634, version v0.9.0, and all author/license fields required by Zenodo
  2. CITATION.cff passes validation (cffconvert or manual review) with current version and date
  3. README.md contains a DOI badge placeholder that will resolve once the Zenodo deposit is created
  4. paper.md cross-references (test count, claim count, layer count, innovation count) match current project state
**Plans:** 1 plan
Plans:
- [x] 09-01-PLAN.md -- Fix .zenodo.json stale count, add DOI badge to README, verify CITATION.cff and paper.md

### Phase 10: Coverage Hardening
**Goal**: Test coverage reaches 90%+ by filling gaps in the four least-covered agent scripts
**Depends on**: Phase 9
**Requirements**: COV-01, COV-02, COV-03, COV-04, COV-05
**Success Criteria** (what must be TRUE):
  1. tests/test_check_stale_docs.py exists and exercises both PASS and FAIL paths of check_stale_docs.py
  2. tests/test_agent_evolve_self.py exercises analyze() and report generation, covering previously untested branches
  3. tests/test_agent_research.py exercises write_report() and uncovered decision branches
  4. tests/test_agent_coverage.py exercises the run() function end-to-end, raising coverage from 20% to 80%+
  5. Running `python -m pytest tests/ -q` reports 90%+ overall coverage (excluding deep_verify.py load_module)
**Plans:** 1/2 plans complete
Plans:
- [ ] 10-01-PLAN.md -- High-impact coverage: check_stale_docs main flow, agent_coverage analyze(), agent_evolve_self analyze()
- [ ] 10-02-PLAN.md -- Remaining coverage: agent_research write_report, agent_diff_review main, agent_pr_creator detectors, agent_learn commands

### Phase 11: Client Onboarding Automation
**Goal**: A pilot form submission is automatically processed into a verified bundle with email draft, requiring only human review before sending
**Depends on**: Phase 10
**Requirements**: PILOT-01, PILOT-02, PILOT-03, PILOT-04, PILOT-05
**Success Criteria** (what must be TRUE):
  1. Running `python scripts/agent_pilot.py --process submissions.csv` reads form data and auto-detects the domain (e.g., ML, pharma, materials) from the description text
  2. For each submission, agent_pilot.py calls mg_client.py for the detected domain and produces a verified bundle that passes `python scripts/mg.py verify --pack`
  3. agent_pilot.py generates a response email draft file containing the PASS result, bundle summary, and next-steps language pointing to the $299 Stripe link
  4. reports/pilot_queue.json tracks every submission with status (pending/processed/sent), timestamps, and domain detected
  5. Running `python scripts/agent_pilot.py --help` displays usage information including all flags
**Plans:** 1/2 plans complete
Plans:
- [ ] 11-01-PLAN.md -- Core agent_pilot.py: CSV ingestion, domain detection, bundle generation, email drafts, queue state
- [ ] 11-02-PLAN.md -- Test suite for agent_pilot.py: domain detection, CSV parsing, bundle gen, drafts, queue, CLI

### Phase 12: Agent Evolution
**Goal**: agent_pr_creator.py autonomously detects stale pilot queue entries and flags them for action
**Depends on**: Phase 11 (pilot_queue.json must exist)
**Requirements**: AGENT-01, AGENT-02
**Success Criteria** (what must be TRUE):
  1. Running agent_pr_creator.py with a pilot_queue.json containing an entry older than 24 hours produces a warning or PR recommendation flagging the stale entry
  2. Running agent_pr_creator.py with all entries processed within 24 hours produces no pilot-queue-related warnings
  3. Tests for detect_pilot_queue_stale() cover both stale and fresh scenarios
**Plans**: TBD

### Phase 13: System Hardening
**Goal**: Every counter, path, and verification gate is consistent and green -- the project is release-ready for v1.0.0
**Depends on**: Phase 12
**Requirements**: HARD-01, HARD-02, HARD-03
**Success Criteria** (what must be TRUE):
  1. A full gap analysis finds zero missing tests, zero stale counters, and zero broken file paths across the project
  2. Test count, version (v1.0.0), claim count (20), and innovation count (8) are consistent in index.html, README.md, AGENTS.md, llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md, and CLAUDE.md
  3. All five verification gates pass in sequence: steward_audit, pytest, deep_verify, check_stale_docs, agent_diff_review
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 9 -> 10 -> 11 -> 12 -> 13

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 5. Foundation | 3/3 | Complete | 2026-03-18 |
| 6. Layer Hardening | 2/2 | Complete | 2026-03-18 |
| 7. Flagship Proofs | 2/2 | Complete | 2026-03-18 |
| 8. Counter Updates | 2/2 | Complete | 2026-03-18 |
| 9. Academic Infrastructure | 0/1 | Planned | - |
| 10. Coverage Hardening | 0/2 | Complete    | 2026-04-03 |
| 11. Client Onboarding Automation | 0/2 | Complete    | 2026-04-03 |
| 12. Agent Evolution | 0/TBD | Complete    | 2026-04-03 |
| 13. System Hardening | 0/TBD | Not started | - |

---
*Roadmap created: 2026-03-17*
*Last updated: 2026-04-03 -- Phase 11 planned (2 plans)*
