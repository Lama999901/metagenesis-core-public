# Requirements: MetaGenesis Core

**Defined:** 2026-04-03
**Core Value:** Every verification claim must be independently auditable offline with cryptographic proof of integrity, provenance, and temporal commitment.

## v1.0.0 Requirements (SHIPPED 2026-04-04)

### Client Onboarding (Phase 11)

- [x] **PILOT-01**: agent_pilot.py reads pilot form submissions (CSV or JSON) and auto-detects domain from description
- [x] **PILOT-02**: agent_pilot.py runs mg_client.py for detected domain and generates verified bundle
- [x] **PILOT-03**: agent_pilot.py generates response email draft with PASS result and bundle summary
- [x] **PILOT-04**: agent_pilot.py saves processing state to reports/pilot_queue.json with status tracking
- [x] **PILOT-05**: agent_pilot.py provides --help showing usage and --process for batch processing

### Coverage Hardening (Phase 10)

- [x] **COV-01**: Dedicated tests for check_stale_docs.py
- [x] **COV-02**: Tests for agent_evolve_self.py analyze() and report generation paths
- [x] **COV-03**: Tests for agent_research.py write_report() and uncovered branches
- [x] **COV-04**: Tests for agent_coverage.py run() function
- [x] **COV-05**: Overall coverage reaches 90%+ (91.9% excluding deep_verify.py per ENV_002)

### Academic Infrastructure (Phase 9)

- [x] **DOI-01**: .zenodo.json updated with correct test count (2012) and current state
- [x] **DOI-02**: CITATION.cff verified complete and current (v0.9.0, 2012 tests)
- [x] **DOI-03**: README.md updated with DOI badge placeholder for Zenodo
- [x] **DOI-04**: paper.md cross-references updated

### Agent Evolution (Phase 12)

- [x] **AGENT-01**: agent_pr_creator.py detector #5: detect_pilot_queue_stale() -- flags pending entries older than 24h
- [x] **AGENT-02**: agent_pr_creator.py tests updated for new detector

### System Hardening (Phase 13)

- [x] **HARD-01**: Full gap analysis run -- missing tests, stale counters, broken paths identified and fixed
- [x] **HARD-02**: All counters consistent across docs (test count, version, claim count, innovation count)
- [x] **HARD-03**: All verification gates pass: steward_audit, pytest, deep_verify, check_stale_docs, agent_diff_review

## v3.0.0 Requirements (Client-Ready Protocol)

### Real Verification

- [x] **REAL-01**: All 20 active claims verified with real external data via mg_claim_builder.py
- [x] **REAL-02**: Each verified claim produces a signed bundle in proof_library/bundles/
- [x] **REAL-03**: Bundles grouped by domain (ML, pharma, finance, digital_twin, materials, physics)
- [x] **REAL-04**: real_ratio reaches 50% (20 real / 40 total) — check #21 shows PASS
- [x] **REAL-05**: All 20 bundles pass `mg.py verify --pack` independently

### Client Demo

- [x] **DEMO-01**: Single-command demo script: pick domain → run claims → bundle → verify → receipt
- [x] **DEMO-02**: Demo produces human-readable receipt (mg_receipt.py) for each domain bundle
- [x] **DEMO-03**: Demo works offline (no network dependency except optional temporal layer)

### Documentation

- [ ] **DOCS-01**: All counters consistent (index.html, README, AGENTS, llms.txt, system_manifest, CONTEXT_SNAPSHOT)
- [ ] **DOCS-02**: check_stale_docs.py rules updated to match final counts in same PR
- [x] **DOCS-03**: COMMERCIAL.md created (pricing, pilot flow, Stripe link)
- [x] **DOCS-04**: SECURITY.md created (threat model, 5-layer defense)
- [x] **DOCS-05**: docs/PROTOCOL.md created (protocol specification prose)

### Gate Hardening

- [ ] **GATE-01**: steward_audit.py → PASS at ship
- [ ] **GATE-02**: pytest ≥2063 passed at ship
- [ ] **GATE-03**: deep_verify.py → ALL 13 TESTS PASSED at ship
- [ ] **GATE-04**: agent_evolution.py → ALL 21 CHECKS PASSED at ship
- [ ] **GATE-05**: agent_diff_review.py → PASS at ship

## Future Requirements (deferred)

### v4.0.0

- **FUTURE-01**: Web dashboard for bundle verification (CLI-first for now)
- **FUTURE-02**: Real-time Zoho Mail API integration (file-based drafts for now)
- **FUTURE-03**: New claim domains beyond existing 20
- **FUTURE-04**: Mobile verification app
- **CLIENT-V2-01**: Zoho Mail API integration for automated email sending
- **CLIENT-V2-02**: Web dashboard for pilot queue management
- **CLIENT-V2-03**: Automatic Stripe invoice generation per pilot conversion

## Out of Scope

| Feature | Reason |
|---------|--------|
| New verification layers or innovations | v3.0.0 validates what exists, not new architecture |
| New claim domains beyond 20 | Proving existing 20 with real data is the priority |
| Modifying steward_audit.py | Sealed, CI-locked |
| Pricing changes | $299 fixed, Stripe link live |
| Mobile/web dashboard | CLI-first, deferred to v4.0.0 |
| deep_verify.py coverage refactor | load_module uses subprocess, untestable without refactor |
| REST API wrapper | Deferred — CLI-first for v3.0.0 |
| Guided onboarding wizard | Deferred — demo script covers v3.0.0 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DOI-01 | Phase 9 | Complete |
| DOI-02 | Phase 9 | Complete |
| DOI-03 | Phase 9 | Complete |
| DOI-04 | Phase 9 | Complete |
| COV-01 | Phase 10 | Complete |
| COV-02 | Phase 10 | Complete |
| COV-03 | Phase 10 | Complete |
| COV-04 | Phase 10 | Complete |
| COV-05 | Phase 10 | Complete |
| PILOT-01 | Phase 11 | Complete |
| PILOT-02 | Phase 11 | Complete |
| PILOT-03 | Phase 11 | Complete |
| PILOT-04 | Phase 11 | Complete |
| PILOT-05 | Phase 11 | Complete |
| AGENT-01 | Phase 12 | Complete |
| AGENT-02 | Phase 12 | Complete |
| HARD-01 | Phase 13 | Complete |
| HARD-02 | Phase 13 | Complete |
| HARD-03 | Phase 13 | Complete |
| REAL-01 | Phase 23 | Complete |
| REAL-02 | Phase 23 | Complete |
| REAL-03 | Phase 23 | Complete |
| REAL-04 | Phase 23 | Complete |
| REAL-05 | Phase 23 | Complete |
| DEMO-01 | Phase 24 | Complete |
| DEMO-02 | Phase 24 | Complete |
| DEMO-03 | Phase 24 | Complete |
| DOCS-01 | Phase 26 | Pending |
| DOCS-02 | Phase 26 | Pending |
| DOCS-03 | Phase 25 | Complete |
| DOCS-04 | Phase 25 | Complete |
| DOCS-05 | Phase 25 | Complete |
| GATE-01 | Phase 26 | Pending |
| GATE-02 | Phase 26 | Pending |
| GATE-03 | Phase 26 | Pending |
| GATE-04 | Phase 26 | Pending |
| GATE-05 | Phase 26 | Pending |

**Coverage:**
- v1.0.0 requirements: 19 total -- 19 complete
- v3.0.0 requirements: 18 total
- Mapped to phases: 18/18
- Unmapped: 0

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-06 after v3.0.0 roadmap created -- all 18 requirements mapped to phases 23-26*
