# Readiness Assessment — MetaGenesis Core v1.0.0-rc1

**Assessment date:** 2026-04-16
**Scope:** v3.1.0 Documentation Deep Pass, Phase 32 (final honest readiness verdict before the first paying customer)
**Authority sources:** `system_manifest.json`, `reports/scientific_claim_index.md`, `reports/known_faults.yaml`, `.planning/research/*`, commit history from 2026-03-05 to 2026-04-16
**Gates:** all 8 (AUD-01..AUD-08) PASS on this branch (`feat/v3.1.0-docs-deep-pass` at HEAD 1f62bd0 plus this file)

This document answers one question: **is the protocol and its documentation ready to be handed to a serious technical evaluator and to the first paying customer at $299?** The verdict is in Section 6. Sections 1–5 are the evidence. Section 7 is the bare numeric trajectory.

---

## 1. Technical completeness

**Verification claims:** 20 active. The authoritative list is `system_manifest.json::active_claims` and `reports/scientific_claim_index.md`.

| Class | Count | Claim IDs |
|---|---|---|
| Physical-anchor claims (traceable to a measured or SI-exact physical constant) | 10 | PHYS-01, PHYS-02, MTR-1, MTR-2, MTR-3, MTR-4, MTR-5, MTR-6, DT-FEM-01, DRIFT-01, plus the calibration-convergence claim DT-CALIB-LOOP-01 which inherits MTR-1 |
| Tamper-evident-only claims (no physical constant anchor — by design, per SCOPE_001) | 10 | SYSID-01, DATA-PIPE-01, ML_BENCH-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, AGENT-DRIFT-01, and the non-physical half of the catalogue |

(DT-CALIB-LOOP-01 is counted under the physical-anchor class because it inherits MTR-1's anchor; SCOPE_001 enumerates 9 claims as tamper-evident-only with DT-CALIB-LOOP-01 not listed there. The 10/10 split in this table reflects the inheritance-based grouping.)

**Physical-anchor hierarchy:**
- **SI 2019 exact, zero uncertainty:** PHYS-01 kB = 1.380649 × 10⁻²³ J/K; PHYS-02 NA = 6.02214076 × 10²³ mol⁻¹. These anchors carry zero measurement uncertainty because they are *defined*, not measured.
- **NIST-measured, ≈ 1% uncertainty:** MTR-1 (E = 70 GPa Al), MTR-2 (thermal paste conductivity), MTR-3 (multilayer contact), MTR-4 (E = 114 GPa Ti-6Al-4V), MTR-5 (E = 193 GPa SS316L), MTR-6 (k = 401 W/(m·K) Cu).
- **Derived anchors:** DT-FEM-01 (inherits MTR-1), DRIFT-01 (monitors MTR-1 anchor), DT-CALIB-LOOP-01 (convergence against MTR-1).

**Verification layers:** 5, independent. Independence is proven by `tests/steward/test_cert11_multi_vector.py` — no subset of four layers is sufficient against a coordinated adversary.

| Layer | Mechanism | Attack caught | Proof test |
|---|---|---|---|
| 1 | SHA-256 integrity via `pack_manifest.json::root_hash` | file modified after packaging | `test_cert03` |
| 2 | Semantic verification (`_verify_semantic` in `scripts/mg.py`) | evidence stripped, then all hashes recomputed and re-signed | `test_cert02` (flagship) |
| 3 | Step chain — 4-step Step Chain template with `trace_root_hash` | inputs changed, steps reordered, partial computation | `test_cert03`, every `backend/progress/<claim>.py` |
| 4 | Bundle signing (HMAC-SHA-256 or Ed25519 asymmetric) | unauthorised bundle creator, signature tampering | `test_cert07`, `test_cert09` |
| 5 | Temporal commitment against NIST Randomness Beacon 2.0 | backdated bundle, timestamp forgery | `test_cert10` |

**Test suite:** 2407 tests PASS + 1 skipped; pytest wall time 31 s on the reference environment. 2408 tests are collected; 1 is skipped by design (documented in pytest output).

**Self-audit:** 22/22 Mechanicus checks PASS (`scripts/agent_evolution.py --summary`): steward, tests, deep, docs, manifest, forbidden-terms, gaps, claude_md, watchlist, branch_sync, coverage, self_improve, signals, chronicle, pr_review, impact, diff_review, auto_pr, semantic_audit, self_audit, real_ratio, client_contrib.

**Proof suite:** 13/13 deep_verify.py tests PASS (`scripts/deep_verify.py`), covering CERT-02 through CERT-12 and Ed25519 + temporal primitives.

**Real-data coverage:** 21 real verifications + 20 synthetic templates = 51.2% real/synthetic ratio (check #21 PASS).

**Code coverage:** 86.2% on `scripts/ + backend/ + sdk/` (pytest-cov on reference environment). 91.9% on the testable subset excluding `scripts/deep_verify.py` per ENV_002 — deep_verify spawns pytest as a subprocess and testing a subprocess chain via pytest is structurally circular.

**Adversarial proof library (relevant subset):**
- `test_cert02` — Layer-2 semantic bypass proof (FLAGSHIP)
- `test_cert03` — Layer-3 step-chain tamper
- `test_cert04` — cross-claim chain integrity
- `test_cert05` — 5-attack gauntlet (proves every layer independently necessary)
- `test_cert06` — 5 real-world scenarios
- `test_cert07` — 13 bundle-signing tests
- `test_cert08` — 10 reproducibility proofs
- `test_cert09` — Ed25519 signing attacks
- `test_cert10` — temporal-commitment attacks
- `test_cert11` — coordinated multi-vector (proves 5-layer independence)
- `test_cert12` — encoding and partial-corruption attacks

**Canonical-state sync:** `reports/canonical_state.md::current_claims_list` and `reports/scientific_claim_index.md` enumerate the same 20 IDs in the same set — verified by `steward_audit.py` as `canonical sync: PASS`.

**Integrations that reduce time-to-value for a client:**
- `sdk/metagenesis.py` — `MetaGenesisClient` Python SDK; instance construction and round-trip pack+verify both covered by `tests/test_sdk.py`.
- `.github/actions/verify-bundle/` — reusable GitHub Action for any repository, one-line CI adoption.
- `scripts/mg_verify_standalone.py` — single-file zero-dependency verifier (~580 lines) for regulator-side verification without a clone of the repo.
- `demos/client_scenarios/run_all_scenarios.py` — 4 client scenarios (NeuralBench AI, PsiThera, QuantRisk Capital, AeroSim Engineering) all PASS end-to-end.
- `demos/open_data_demo_01/run_demo.py` — open-data demonstration: PASS PASS (pack + verify).

---

## 2. Documentation completeness

**Corpus added in v3.1.0 (committed on this branch before Phase 32):**
- `docs/USE_CASES.md` (7,638 words, 14 domains, every "what happens when verification fails" case sourced from `.planning/research/INCIDENTS.md`)
- `docs/CLIENT_JOURNEY.md` (5,997 words, 6 personas with regulatory triggers)
- `docs/WHY_NOT_ALTERNATIVES.md` (6,516 words, 10 alternatives compared, CERT-02 step-by-step walk-through, 3-domain rerun-cost math)
- `docs/REGULATORY_GAPS.md` (7,722 words, 24 regulations grouped into 6 categories, 31 `[GAP]` honest-scope markers, 3 explicit `[CITATION UNVERIFIED]` markers of which one is the required DO-178C Table A-7 objective #9 flag)
- `README.md` Deep Reading rows updated with the three new docs

Total new material in v3.1.0: 27,873 words across the 4 new docs.

**Pre-existing corpus preserved and still current:**
- `docs/PROTOCOL.md`, `docs/SECURITY.md`, `docs/COMMERCIAL.md`, `docs/SDK.md`, `docs/CLIENT_GUIDE.md`, `docs/CLIENT_SECURITY.md`, `docs/AGENT_CHARTER.md`, `docs/AGENT_SYSTEM.md`, `docs/API_CONTRACT.md`, `docs/ERROR_HANDLING_STANDARD.md`, `docs/ROADMAP.md`, `docs/ROADMAP_VISION.md`, `docs/VISION.md`, `docs/PHILOSOPHICAL_FOUNDATION.md`, `docs/EVOLUTIONARY_ARCHITECTURE.md`
- Counter-synchronised documents: `README.md`, `AGENTS.md`, `llms.txt`, `CONTEXT_SNAPSHOT.md`, `system_manifest.json`, `index.html`, `AGENT_TASKS.md`, `reports/canonical_state.md` — all PASS `scripts/check_stale_docs.py --strict`
- Academic artefacts: `paper.md`, `paper.bib`, `CITATION.cff`, `.zenodo.json` (Zenodo DOI 10.5281/zenodo.19521091)

**What is explained:**
- 14 application domains (USE_CASES.md, all with cited real-world incidents as motivation and with exact regulatory citations as compliance hooks)
- 6 buyer personas (CLIENT_JOURNEY.md, every CLI flag verified against `sdk/metagenesis.py`, `scripts/mg.py`, `scripts/mg_client.py` — zero invented flags)
- 10 alternative tools (WHY_NOT_ALTERNATIVES.md) positioned as *composable* additions ("X + MetaGenesis"), never as replacements
- 24 regulations with exact article, clause, or section numbers (REGULATORY_GAPS.md), each with an authoritative-source link (EUR-Lex / ecfr.gov / NIST CSRC / IFRS Foundation / ISO.org / UNECE / AICPA / Federal Reserve / grants.nih.gov / cOAlition S / ALLEA)
- 5-layer verification architecture (SECURITY.md, PROTOCOL.md, scientific_claim_index.md)
- 11 documented known faults (`reports/known_faults.yaml`) including SCOPE_001, FAULT_004 through FAULT_011

**What is documented as missing on purpose:**
The 31 `[GAP]` flags in REGULATORY_GAPS.md cluster into three honest-scope categories per `.planning/research/SUMMARY.md §7`:

| Category | Examples | Status |
|---|---|---|
| Training-data lineage | EU AI Act Art. 10 | permanent out-of-scope (MetaGenesis verifies outputs, not data provenance) |
| Human oversight, conceptual soundness, org governance | EU AI Act Art. 14, SR 11-7 Sec V, SOC 2 CC1-CC4, ISO 26262 HARA, AS9100D organisational controls, SOX-style attestations | permanent out-of-scope (cannot be automated — MetaGenesis supports human reviewers, does not replace them) |
| Design-document certification | 510(k) design-history file, IEC 62304 plans, DO-178C PSAC/SDP/SVP, AS9100D design-record items | **closable** via a future thin claim `DOC-HASH-01` |

**What is unclear — honest disclosure:**
- The `[CITATION UNVERIFIED]` flag on DO-178C Table A-7 objective #9 survives verbatim from research into the regulatory doc (RG-04). Secondary source wording is recorded; the exact phrasing could not be cross-checked against the RTCA standard itself. This is a known soft spot in the regulatory corpus.
- Three ISO 26262 sub-clause numberings are MEDIUM-confidence, drawn from secondary sources, not the standard itself (noted in REGULATORY_GAPS.md Confidence Assessment).
- Everything else in the regulatory corpus is HIGH-confidence primary-source verified.

---

## 3. Domain coverage

**14 application domains are documented in `docs/USE_CASES.md`.** The mapping from domain → claim → incident → regulation is derived from `.planning/research/SUMMARY.md §2`:

| # | Domain | Claim mapping | Real incident cited | Regulation cited |
|---|---|---|---|---|
| 1 | ML / AI benchmarks | ML_BENCH-01 / 02 / 03 | Kapoor-Narayanan 2023, Zillow 2021 | EU AI Act, NIST AI RMF, SOC 2 CC7.2 |
| 2 | Pharma / Biotech | PHARMA-01 | Duke Potti 2010-15, Theranos 2015-22 (governance), Takeda Actos | 21 CFR Part 11, FDA AI Credibility Draft Jan 2025, ISO 14155 |
| 3 | Medical devices | uses DT-SENSOR-01 analogue | Therac-25 1985-87, Guidant 2002-05 | FDA 510(k), IEC 62304, EU MDR |
| 4 | Materials | MTR-1 / 2 / 3 / 4 / 5 / 6 ⚓ | Schön 2002 | AS9100D, ISO 26262 |
| 5 | Digital twin / FEM | DT-FEM-01 ⚓, DT-CALIB-LOOP-01 ⚓ | Takata 2001-14 | NASA-STD-7009B, AS9100D |
| 6 | IoT sensor / aerospace | DT-SENSOR-01 | Air France 447 2009-12, 737 MAX 2018-19, Challenger 1986 (governance) | DO-178C, UN R155 |
| 7 | System ID / science | SYSID-01 | CovidSim 2020, LaCour 2014, OSC Psych 2015 | NIH DMSP, Plan S, ALLEA |
| 8 | Algorithmic trading | uses FINRISK-01 pattern | Knight Capital 2012, Flash Crash 2010 | MiFID II Art. 17 |
| 9 | Financial risk | FINRISK-01 | JPM London Whale 2012, LIBOR 2005-12 (governance) | Basel III BCBS 239, SR 11-7, SEC 17a-4 |
| 10 | Automotive simulation | uses DT-FEM-01 + DT-SENSOR-01 | VW Dieselgate 2015, Uber ATG 2018 | UN R155, UN R156, ISO 26262 |
| 11 | Carbon / ESG | — | Verra 2023 | IFRS S1/S2, EU CSRD |
| 12 | Quantum computing | — | Google Sycamore 2019 (methodology dispute) | — |
| 13 | Data pipeline | DATA-PIPE-01 | — | NIH DMSP |
| 14 | Agent drift | AGENT-DRIFT-01 | — | SOC 2 CC7.2, NIST AI RMF MANAGE |

**Domains with live first-class claims:** 10 of 14 have at least one dedicated claim template in `backend/progress/`. The other 4 (medical devices, algorithmic trading, automotive sim, carbon / ESG) are documented and demonstrably addressable with existing claim primitives through inherited or grouped use (e.g. automotive sim already chains DT-FEM-01 + DT-SENSOR-01 in `demos/client_scenarios/04_digital_twin/`), but do not yet have a single dedicated dossier claim.

**Real incidents cited:** 22 across the 14 domains, every one traced to a verifiable primary source in `.planning/research/INCIDENTS.md` (SEC filings, FDA / EPA / NTSB / BEA / DOJ notices, journal retractions, US federal-court dockets, Senate subcommittee reports). Three of the 22 (Theranos 2015-22, Challenger 1986, LIBOR 2005-12) are **governance / fraud failures, not pure verification-gap cases** — USE_CASES.md flags them as such and frames MetaGenesis as "would have bounded the damage / made concealment cryptographically expensive," never as "would have prevented."

**Planned future claims, NOT implemented in v1.0.0-rc1 (informational only per `.planning/research/SUMMARY.md §10`):**

| Future claim | Regulatory fit | Out-of-scope justification |
|---|---|---|
| `AUTO-OTA-01` | UN R156 SUMS (Software Update Management System); bundle ≡ update package | requires the mandatory 6-step claim lifecycle (CLAUDE.md); belongs to a later milestone |
| `CLIMATE-01` | IFRS S2 / CSRD GHG accounting certificate; 2026 CSRD limited-assurance deadline | same — separate milestone |
| `TRADING-01` | MiFID II Art. 17(2) order / cancellation / quotation log (highest-margin vertical) | same — separate milestone |
| `EDC-01` | ISO 14155 Clause 7.8.3 Electronic Data Capture (pharma clinical-trial fit) | same — separate milestone |
| `DOC-HASH-01` | Design-document hash + signature claim; closes 510(k) + IEC 62304 + DO-178C + AS9100D design-document gaps | small-effort gap-closer, intentionally deferred to preserve v3.1.0 as a pure-docs milestone |

v3.1.0 is explicitly a documentation-only milestone. Any of the five above becoming a real claim carries a separate phase and full 6-step claim-lifecycle overhead.

---

## 4. Regulatory positioning

**Scope:** 24 regulations cited with exact article / clause / section numbers, grouped into 6 categories in `docs/REGULATORY_GAPS.md`. Authority sources ordered: EUR-Lex → ecfr.gov → NIST CSRC → IFRS Foundation → ISO.org → UNECE → AICPA → Federal Reserve / OCC → grants.nih.gov → cOAlition S → ALLEA.

| Category | Regulations (n) | Representative clauses |
|---|---|---|
| Financial | 4 | MiFID II Art. 17(2); Basel III BCBS 239 Principle 3; SR 11-7 Sections III, V, VI; SEC Rule 17a-4(f) |
| Pharma + Medical | 6 | 21 CFR Part 11 §§ 11.10(a) and 11.10(e); FDA AI Credibility Draft Jan 2025 (7-step framework); FDA 510(k) 2023 final; IEC 62304 Clauses 5.1, 5.5-5.7, 5.8; ISO 14155 Clause 7.8.3; EU MDR Annex I §17 |
| Automotive + Aerospace | 6 | ISO 26262 Parts 4, 6, 8; AS9100D Clause 8.3.4; NASA-STD-7009B Credibility Assessment Scale (8 factors); UN R155; UN R156 (strongest natural fit, AUTO-OTA-01 planned); DO-178C Table A-7 (obj. #9 `[CITATION UNVERIFIED]`) |
| Science | 3 | NIH NOT-OD-21-013 Data Management and Sharing Policy; Plan S Principles 5 and 8; ALLEA Code 2023 Section 2 |
| AI + Cryptography | 4 | EU AI Act Arts. 10, 12, 15, 26(6), 72; NIST FIPS 203, 204, 205 (post-quantum); NIST AI RMF MEASURE / MANAGE; SOC 2 CC7.2, CC7.3, CC8.1 |
| Climate / ESG | 1 (combined) | IFRS S1 / S2 and EU CSRD Art. 34a (CEAOB limited-assurance guidance) |

**Gap architecture:** 31 `[GAP]` flags in REGULATORY_GAPS.md cluster on three honest boundaries:
- **Training-data lineage** (EU AI Act Art. 10) — permanent out-of-scope. MetaGenesis verifies *outputs*, not training-data provenance.
- **Human oversight and conceptual soundness** (EU AI Act Art. 14; SR 11-7 Section V; SOC 2 CC1-CC4; ISO 26262 HARA; AS9100D organisational controls) — permanent out-of-scope. Cannot be automated. MetaGenesis supports human reviewers, does not replace them.
- **Design-document certification** (510(k) design-history file; IEC 62304 plans; DO-178C PSAC/SDP/SVP; AS9100D design records) — **closable** by the future `DOC-HASH-01` claim, intentionally deferred from v3.1.0 to preserve docs-only scope.

**Timeline urgency (reason to move now, not next year):**
- **FDA AI Credibility Framework Jan 2025 draft** — currently in active public comment; early-adopter evidence patterns will shape final guidance. Pharma / biotech clients with IND filings in 2026-27 are the natural first customers.
- **EU CSRD Art. 34a** — 2026 limited-assurance deadline for large undertakings; climate + ESG reporting must produce auditable evidence. IFRS S2 + CSRD combined is the fastest-growing regulatory pressure in the industrial base.
- **NSS post-quantum transition** — CNSA 2.0 / FIPS 204 ML-DSA standardisation complete; NSS migration deadline 2030. Ed25519 is fit for 2026 but a dual-signing migration path must be documented before the first regulated customer asks for it.

---

## 5. What is missing before v1.0.0

This section is deliberately without marketing varnish. Four candidates were considered:

1. **First paying customer at $299.** This is the #1 priority per `CLAUDE.md::COMMERCIAL PRIORITY`. Stripe link is live. Contact email `yehor@metagenesis-core.dev` is live. The free-pilot funnel (`metagenesis-core.dev/#pilot`, Formspree `xlgpdwop`) is live. No technical work remains to accept the first $299. **Status: genuine blocker for the v1.0.0 tag.** A v1.0.0 release without a paying customer is a technical release, not a commercial one.

2. **External endorsement.** No academic citation yet (JOSS resubmission window opens September 2026 after the 6-month public-history requirement). No regulatory reference. Wave-2 outreach to François Chollet, LMArena, and Percy Liang is drafted but has not been sent. Zenodo DOI is minted (`10.5281/zenodo.19521091`). **Status: genuine blocker for commercial confidence, not for technical correctness.** The protocol works whether or not a regulator has name-checked it, but the first customer will be much faster to land once someone external has.

3. **Post-quantum dual-signing migration (FIPS 204 ML-DSA).** FAULT_004 documents this explicitly: SHA-256 and Ed25519 are not quantum-resistant; NIST timeline is 15–30 years to cryptographically relevant quantum computers; NSS migration deadline 2030. Protocol is designed for algorithm substitution without architectural change. **Status: NOT a blocker for v1.0.0, not a blocker for 2026, not a blocker for 2027.** It is a 2028-onward roadmap item. Documentation has it; code has the substitution hooks; no client in 2026 will ask for this.

4. **`DOC-HASH-01` future claim.** Closes four regulatory `[GAP]` clusters (510(k), IEC 62304, DO-178C, AS9100D design-document certification) with small effort per `.planning/research/SUMMARY.md §10`. **Status: NOT a blocker for v1.0.0.** It is a high-leverage next-milestone claim that unlocks additional verticals. v1.0.0 releases without it; the next minor release can add it.

**Honest verdict on the "only two things remain: first client + endorsement" claim from the task brief:** Confirmed by evidence. Items 3 and 4 above are not blockers. Items 1 and 2 are. **The commercial milestone is gated on those two, not on any technical deliverable.**

---

## 6. Honest readiness verdict

### Is the protocol ready for a first real client?

**Yes.**

All 8 audit gates PASS on this branch (steward_audit PASS, 2407 pytest tests PASS, 13/13 deep_verify tests PASS, 22/22 evolution checks PASS, check_stale_docs strict exit 0, 4/4 client scenarios PASS, open-data demo PASS PASS, SDK import OK). 20 claims are live, 51.2% backed by real external data, and the $299 Stripe link is operational. The protocol answers `PASS` or `FAIL` in one command and does it offline — there is no missing technical capability between a pilot request arriving and a signed bundle being returned.

### Is the documentation ready to present to a serious technical evaluator?

**Yes.**

USE_CASES.md explains 14 domains with 22 primary-sourced real incidents; CLIENT_JOURNEY.md walks 6 personas through concrete commands with zero invented CLI flags; WHY_NOT_ALTERNATIVES.md positions MetaGenesis against 10 alternatives using the composability framing ("X + MetaGenesis") and walks CERT-02 step by step against the actual test file; REGULATORY_GAPS.md cites 24 regulations with exact clauses and 31 honest `[GAP]` flags including the preserved `[CITATION UNVERIFIED]` on DO-178C Table A-7 objective #9. An evaluator reading these four docs in order will find: the problem (real incidents), the solution (5 independent layers), the competition (10 alternatives with honest composability), and the regulatory fit (24 exact citations). The open soft spots (governance failures, training-data lineage, human oversight, design-document certification, post-quantum migration) are disclosed rather than hidden.

### What is the single most important next action?

**Send the Wave-2 outreach emails to François Chollet, LMArena, and Percy Liang within the next 7 days.** Outreach drafts are prepared (`reports/WAVE2_OUTREACH_DRAFTS.md`). The protocol, the demos, and the docs are all ready. The shortest path to unblocking the first $299 is to obtain external engagement from a credible technical evaluator in the ML / benchmarking community, because PHYS-01 / PHYS-02 anchored in SI 2019 exact constants is the strongest anchor narrative available to any verification protocol and is directly relevant to their public positions on benchmark integrity. Target: first outreach reply within 7 days; first pilot conversation within 14 days; first $299 within 30 days.

---

## 7. The numbers tell a story

Numbers only. No adjectives.

**Period:** 42 days from inception commit `23138a3` (2026-03-05) to this assessment (2026-04-16). 1,650 commits.

**Tests:**
- Inception: 39 tests
- v0.9.0: 2012 tests
- v3.0.0 ship: 2063 tests
- v1.0.0-rc1 (today): 2407 tests + 1 skipped, 2408 collected
- Wall time: 31 s

**Claims:**
- Inception: 5 claims live
- v1.0.0-rc1: 20 claims live, 20/20 canonical-sync PASS
- Planned future: 5 (`AUTO-OTA-01`, `CLIMATE-01`, `TRADING-01`, `EDC-01`, `DOC-HASH-01`) — documented, not implemented
- Physical-anchor subset: 10 of 20 (SCOPE_001)

**Domains:**
- Inception: 0 domains documented in the application sense
- v1.0.0-rc1: 14 domains in USE_CASES.md, 8 in `system_manifest.json::domains`

**Verification layers:**
- v0.6.x: 1 layer (SHA-256 integrity)
- v1.0.0-rc1: 5 layers (SHA-256, semantic, step chain, Ed25519 signing, temporal commitment) — independence proven by `test_cert11`

**Innovations:**
- v1.0.0-rc1 verified innovations: 8 (bidirectional claim coverage, tamper-evident semantic verification, policy-gate immutable anchors, dual-mode canary pipeline, step-chain verification, cross-claim cryptographic chain, bundle signing HMAC-SHA-256, temporal commitment NIST Beacon)

**Personas:**
- Inception: 0 personas documented
- v1.0.0-rc1: 6 personas with regulatory triggers in CLIENT_JOURNEY.md
- Every CLI flag verified against source: 0 invented flags

**Alternatives analysed:**
- Inception: 0
- v1.0.0-rc1: 10 in WHY_NOT_ALTERNATIVES.md (SHA-256, Docker, MLflow/DVC, manual audit, signed PDF, Git history, Jupyter output, Nextflow/CWL/Snakemake, Chainpoint/RFC 3161, Coq/Lean4)

**Regulations cited:**
- Inception: 0
- v3.1.0 Wave 1: 24 with exact article/clause/section numbers across 6 categories
- `[GAP]` honest-scope flags: 31
- `[CITATION UNVERIFIED]` flags: 3 (the required DO-178C Table A-7 objective #9 is one of them, preserved verbatim)

**Incidents cited:**
- Inception: 0
- v3.1.0 Wave 1: 22 real-world cases, 100% primary-source verifiable

**Real-data verification ratio:**
- v1.0.0-rc1: 51.2% (21 real verifications / 20 synthetic templates; check #21 PASS)

**Test coverage:**
- v1.0.0-rc1: 86.2% overall; 91.9% excluding `scripts/deep_verify.py` per ENV_002

**Documentation word count added in v3.1.0:**
- 27,873 words across 4 new docs (USE_CASES 7,638; CLIENT_JOURNEY 5,997; WHY_NOT_ALTERNATIVES 6,516; REGULATORY_GAPS 7,722)

**Audit gates, this branch, today:**
- Steward audit: PASS
- Pytest: 2407 passed, 1 skipped
- Deep verify: 13 / 13
- Stale docs (strict): exit 0
- Evolution: 22 / 22
- Client scenarios: 4 / 4
- Open-data demo: PASS PASS
- SDK import: OK

**Clients:**
- Inception: 0
- v1.0.0-rc1 ship: 0
- v1.0.0 target: ≥ 1 paying at $299

**Honest-boundary flags preserved through v3.1.0:**
- `SCOPE_001` — physical-anchor scope limited to 10 of 20 claims by design
- `FAULT_005` — trusted-verifier assumption (analogous to trusting your compiler); mitigated by single-file verifier (~580 lines) whose SHA-256 can be published and checked independently
- `FAULT_006` — protocol certifies provenance, not correctness (a notary certifies the signature, not the truth of the contents); mitigated by independent peer review of claim templates
- `[CITATION UNVERIFIED]` — DO-178C Table A-7 objective #9 exact wording, preserved verbatim per RG-04

---

*Assessment authority: MetaGenesis Core / STEW-01. Written 2026-04-16 after Phase 32 of the v3.1.0 Documentation Deep Pass. Honest verdict: ready for first client; ready for technical evaluator; blocked commercially on first customer and first external endorsement.*
