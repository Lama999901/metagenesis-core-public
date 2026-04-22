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

- [x] **DOCS-01**: All counters consistent (index.html, README, AGENTS, llms.txt, system_manifest, CONTEXT_SNAPSHOT)
- [x] **DOCS-02**: check_stale_docs.py rules updated to match final counts in same PR
- [x] **DOCS-03**: COMMERCIAL.md created (pricing, pilot flow, Stripe link)
- [x] **DOCS-04**: SECURITY.md created (threat model, 5-layer defense)
- [x] **DOCS-05**: docs/PROTOCOL.md created (protocol specification prose)

### Gate Hardening

- [x] **GATE-01**: steward_audit.py → PASS at ship
- [x] **GATE-02**: pytest ≥2063 passed at ship
- [x] **GATE-03**: deep_verify.py → ALL 13 TESTS PASSED at ship
- [x] **GATE-04**: agent_evolution.py → ALL 21 CHECKS PASSED at ship
- [x] **GATE-05**: agent_diff_review.py → PASS at ship

## v3.1.0 Requirements (Documentation Deep Pass)

**Goal:** Expand domain coverage and produce century-level client-facing documentation so a domain expert reads once and immediately understands problem/solution/next-action. Docs only — NO new claims.

**Cross-cutting rules (apply to every v3.1.0 requirement):**
- Zero banned terms: `tamper-proof`, `blockchain`, `GPT-5`, `unforgeable`, `revolutionary`, `game-changing`, `unprecedented`
- Every incident cited has a verifiable primary source (SEC/FDA/NTSB/EPA/DOJ/journal retraction/federal docket) — no invented stats
- Every regulation cited has an exact article/clause/paragraph number
- Every CLI command shown in docs is verified against `sdk/metagenesis.py`, `scripts/mg.py`, `scripts/mg_client.py` — no invented flags
- Preserve honest boundaries: SCOPE_001 (physical anchor only on 10 of 20 claims), FAULT_005, FAULT_006, governance-vs-verification distinction for Theranos/Challenger/LIBOR
- Preserve the 1 `[CITATION UNVERIFIED]` flag (DO-178C Table A-7 obj. #9) verbatim

### USE_CASES.md Rewrite

- [ ] **UC-01**: `docs/USE_CASES.md` rewritten to cover 14 domains (8 existing + 6 new: algorithmic trading, automotive simulation, quantum computing, scientific research & peer review, aerospace certification, medical devices)
- [ ] **UC-02**: Every domain section follows the 6-subsection structure: The computation / What happens when verification fails / The cost equation / Unique MetaGenesis properties / Integration — 3 steps / Regulatory requirement
- [ ] **UC-03**: Every "What happens when verification fails" subsection names a real incident with year, consequence figure, and primary source URL (from `.planning/research/INCIDENTS.md`, 22 verified incidents available)
- [ ] **UC-04**: Every "Regulatory requirement" subsection cites at least one exact article/clause (from `.planning/research/REGULATIONS.md`, 24 regulations available)
- [ ] **UC-05**: Every "Integration — 3 steps" subsection uses commands verified against the actual SDK/CLI source

### CLIENT_JOURNEY.md Creation

- [ ] **CJ-01**: `docs/CLIENT_JOURNEY.md` created with 6 complete persona journeys: ML engineer at AI startup, computational chemist at biotech, model risk manager at bank, FEM engineer at aerospace/automotive supplier, quant analyst at hedge fund, research scientist
- [ ] **CJ-02**: Every journey has 6 subsections: Who this person is / The exact trigger moment / Three steps with real commands / What verifier does / What changes after / Time and cost
- [ ] **CJ-03**: Every trigger moment is tied to a specific regulatory citation or concrete audit event (SOC 2 CC7.2, FDA IND, ECB TRIM, AS9100D 8.3.5, MiFID II Art. 17, peer-review reproducibility track)

### WHY_NOT_ALTERNATIVES.md Creation

- [ ] **ALT-01**: `docs/WHY_NOT_ALTERNATIVES.md` created with 3 sections
- [ ] **ALT-02**: Section 1 comparison table covers at minimum: SHA-256 alone, Docker, MLflow/DVC, Manual audit, Signed PDF, Git history — for each: what it solves well, what it cannot, concrete failure
- [ ] **ALT-03**: Section 2 walks through CERT-02 strip-and-recompute attack step by step, matching what `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` actually does (do not invent steps)
- [ ] **ALT-04**: Section 3 explains why rerunning is not verification using 3 concrete domains (ML training, FEM/CFD, Monte Carlo VaR) with real compute-cost figures citing primary sources
- [ ] **ALT-05**: Framing is composability ("X + MetaGenesis"), never "MetaGenesis vs X"

### REGULATORY_GAPS.md Update

- [ ] **RG-01**: `docs/REGULATORY_GAPS.md` expanded from current 3 regulations to 24+ regulations grouped by domain (Financial / Pharma+Medical / Auto+Aero / Science / AI+Crypto / Climate)
- [ ] **RG-02**: Every citation has the exact article/clause/section number with an authoritative-source link (EUR-Lex, ecfr.gov, NIST CSRC, etc.)
- [ ] **RG-03**: Honest [GAP] flags preserved for boundaries MetaGenesis does not cover (training-data lineage, human oversight, org governance, design-document certification, post-quantum signing, HARA/FMEDA)
- [ ] **RG-04**: The single `[CITATION UNVERIFIED]` flag on DO-178C Table A-7 obj. #9 is carried forward verbatim

### README.md Deep Reading Update

- [ ] **RM-01**: `README.md` Deep Reading table updated with new entries for `docs/USE_CASES.md`, `docs/CLIENT_JOURNEY.md`, `docs/WHY_NOT_ALTERNATIVES.md`

### Full Audit (8 Gates)

- [ ] **AUD-01**: `python scripts/steward_audit.py` → STEWARD AUDIT: PASS
- [ ] **AUD-02**: `python -m pytest tests/ -q` → 2407 passed
- [ ] **AUD-03**: `python scripts/deep_verify.py` → ALL 13 TESTS PASSED (TEST 6 clean post quick task 260416-i4y)
- [ ] **AUD-04**: `python scripts/check_stale_docs.py --strict` → exit 0 (if any count changes in any doc, `scripts/check_stale_docs.py` required strings updated in SAME PR per UPDATE_PROTOCOL v1.1)
- [ ] **AUD-05**: `python scripts/agent_evolution.py --summary` → ALL 22 CHECKS PASSED
- [ ] **AUD-06**: `python demos/client_scenarios/run_all_scenarios.py` → 4/4 scenarios PASS
- [ ] **AUD-07**: `python demos/open_data_demo_01/run_demo.py` → PASS PASS
- [ ] **AUD-08**: `python -c "from sdk.metagenesis import MetaGenesisClient; print(MetaGenesisClient())"` → OK

### READINESS_ASSESSMENT.md Creation

- [ ] **RDY-01**: `reports/READINESS_ASSESSMENT.md` created with all 7 sections: Technical completeness / Documentation completeness / Domain coverage / Regulatory positioning / What is missing before v1.0.0 / Honest readiness verdict / The numbers tell a story
- [ ] **RDY-02**: Every section uses specific numbers from `system_manifest.json`, `reports/scientific_claim_index.md`, and research files — no invented statistics
- [ ] **RDY-03**: Section 6 provides explicit Yes/No verdicts for: (a) Is the protocol ready for first real client? (b) Is the documentation ready to present to a serious technical evaluator? (c) What is the single most important next action?
- [ ] **RDY-04**: Section 7 ("The numbers tell a story") uses numbers only — no adjectives, no marketing language
- [ ] **RDY-05**: Honest flags preserved: FAULT_005, FAULT_006, SCOPE_001, the 5 prioritised-but-unimplemented future claims (AUTO-OTA-01, CLIMATE-01, TRADING-01, EDC-01, DOC-HASH-01)

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
| v3.1.0 new claims (AUTO-OTA-01, CLIMATE-01, TRADING-01, EDC-01, DOC-HASH-01) | Docs-only milestone — these 5 future claims are informational only per research/SUMMARY.md §10 |

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
| DOCS-01 | Phase 26 | Complete |
| DOCS-02 | Phase 26 | Complete |
| DOCS-03 | Phase 25 | Complete |
| DOCS-04 | Phase 25 | Complete |
| DOCS-05 | Phase 25 | Complete |
| GATE-01 | Phase 26 | Complete |
| GATE-02 | Phase 26 | Complete |
| GATE-03 | Phase 26 | Complete |
| GATE-04 | Phase 26 | Complete |
| GATE-05 | Phase 26 | Complete |
| UC-01 | Phase 28 | Pending |
| UC-02 | Phase 28 | Pending |
| UC-03 | Phase 28 | Pending |
| UC-04 | Phase 28 | Pending |
| UC-05 | Phase 28 | Pending |
| CJ-01 | Phase 29 | Pending |
| CJ-02 | Phase 29 | Pending |
| CJ-03 | Phase 29 | Pending |
| ALT-01 | Phase 30 | Pending |
| ALT-02 | Phase 30 | Pending |
| ALT-03 | Phase 30 | Pending |
| ALT-04 | Phase 30 | Pending |
| ALT-05 | Phase 30 | Pending |
| RG-01 | Phase 31 | Pending |
| RG-02 | Phase 31 | Pending |
| RG-03 | Phase 31 | Pending |
| RG-04 | Phase 31 | Pending |
| RM-01 | Phase 31 | Pending |
| AUD-01 | Phase 32 | Pending |
| AUD-02 | Phase 32 | Pending |
| AUD-03 | Phase 32 | Pending |
| AUD-04 | Phase 32 | Pending |
| AUD-05 | Phase 32 | Pending |
| AUD-06 | Phase 32 | Pending |
| AUD-07 | Phase 32 | Pending |
| AUD-08 | Phase 32 | Pending |
| RDY-01 | Phase 32 | Pending |
| RDY-02 | Phase 32 | Pending |
| RDY-03 | Phase 32 | Pending |
| RDY-04 | Phase 32 | Pending |
| RDY-05 | Phase 32 | Pending |

**Coverage:**
- v1.0.0 requirements: 19 total -- 19 complete
- v3.0.0 requirements: 18 total -- 18 complete
- v3.1.0 requirements: 31 total -- 0 complete, 31 pending
- Mapped to phases: 68/68
- Unmapped: 0

---
*Requirements defined: 2026-04-03*
*Last updated: 2026-04-16 after v3.1.0 roadmap created -- 31 new requirements (UC-01..05, CJ-01..03, ALT-01..05, RG-01..04, RM-01, AUD-01..08, RDY-01..05) mapped to Phases 28-32*
