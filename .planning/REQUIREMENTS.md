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

## v2 Requirements

### Advanced Client Features

- **CLIENT-V2-01**: Zoho Mail API integration for automated email sending (currently file-based drafts)
- **CLIENT-V2-02**: Web dashboard for pilot queue management
- **CLIENT-V2-03**: Automatic Stripe invoice generation per pilot conversion

## Out of Scope

| Feature | Reason |
|---------|--------|
| New verification layers | Testing and automating what exists |
| New claim domains (21+) | Client onboarding uses existing 20 claims |
| Modifying steward_audit.py | Sealed, CI-locked |
| Real-time Zoho Mail API | File-based drafts sufficient for v1.0.0 |
| Pricing changes | $299 fixed, Stripe link live |
| Mobile/web dashboard | CLI-first, deferred to v2 |
| deep_verify.py coverage | load_module uses subprocess, untestable without refactor |

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

**Coverage:**
- v1.0.0 requirements: 19 total
- Complete: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-04 after v2.0.0 close — synced with ROADMAP.md reality*
