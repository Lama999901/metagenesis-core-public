# Requirements: MetaGenesis Core v1.0.0

**Defined:** 2026-04-03
**Core Value:** Every verification claim must be independently auditable offline with cryptographic proof of integrity, provenance, and temporal commitment.

## v1.0.0 Requirements

### Client Onboarding

- [ ] **PILOT-01**: agent_pilot.py reads pilot form submissions (CSV or JSON) and auto-detects domain from description
- [ ] **PILOT-02**: agent_pilot.py runs mg_client.py for detected domain and generates verified bundle
- [ ] **PILOT-03**: agent_pilot.py generates response email draft with PASS result and bundle summary
- [ ] **PILOT-04**: agent_pilot.py saves processing state to reports/pilot_queue.json with status tracking
- [ ] **PILOT-05**: agent_pilot.py provides --help showing usage and --process for batch processing

### Coverage Hardening

- [ ] **COV-01**: Dedicated tests for check_stale_docs.py (currently no dedicated test file)
- [ ] **COV-02**: Tests for agent_evolve_self.py analyze() and report generation paths
- [ ] **COV-03**: Tests for agent_research.py write_report() and uncovered branches
- [ ] **COV-04**: Tests for agent_coverage.py run() function (20% covered)
- [ ] **COV-05**: Overall coverage reaches 90%+ (excluding deep_verify.py load_module)

### Academic Infrastructure

- [ ] **DOI-01**: .zenodo.json updated with correct test count (1634) and current state
- [ ] **DOI-02**: CITATION.cff verified complete and current (v0.9.0, 1634 tests)
- [ ] **DOI-03**: README.md updated with DOI badge placeholder for Zenodo
- [ ] **DOI-04**: paper.md cross-references updated if stale

### Agent Evolution

- [ ] **AGENT-01**: agent_pr_creator.py detector #5: detect_pilot_queue_stale() -- flags pending entries older than 24h
- [ ] **AGENT-02**: agent_pr_creator.py tests updated for new detector

### System Hardening

- [ ] **HARD-01**: Full gap analysis run -- any missing tests, stale counters, or broken paths identified and fixed
- [ ] **HARD-02**: All counters consistent across docs (test count, version, claim count, innovation count)
- [ ] **HARD-03**: All verification gates pass: steward_audit, pytest, deep_verify, check_stale_docs, agent_diff_review

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
| DOI-01 | Phase 9 | Pending |
| DOI-02 | Phase 9 | Pending |
| DOI-03 | Phase 9 | Pending |
| DOI-04 | Phase 9 | Pending |
| COV-01 | Phase 10 | Pending |
| COV-02 | Phase 10 | Pending |
| COV-03 | Phase 10 | Pending |
| COV-04 | Phase 10 | Pending |
| COV-05 | Phase 10 | Pending |
| PILOT-01 | Phase 11 | Pending |
| PILOT-02 | Phase 11 | Pending |
| PILOT-03 | Phase 11 | Pending |
| PILOT-04 | Phase 11 | Pending |
| PILOT-05 | Phase 11 | Pending |
| AGENT-01 | Phase 12 | Pending |
| AGENT-02 | Phase 12 | Pending |
| HARD-01 | Phase 13 | Pending |
| HARD-02 | Phase 13 | Pending |
| HARD-03 | Phase 13 | Pending |

**Coverage:**
- v1.0.0 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-03 after roadmap creation*
