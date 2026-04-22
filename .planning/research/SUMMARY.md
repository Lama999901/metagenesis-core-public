# Research Synthesis — v3.1.0 Documentation Deep Pass

**Milestone:** MetaGenesis Core v1.0.0-rc1 → v3.1.0 (documentation-only, NO new claims)
**Synthesis date:** 2026-04-16
**Deliverables:** 5 docs + README Deep Reading update + full audit. This is a DOC milestone — the 5 prioritised future claim additions surfaced by REGULATIONS research are kept in Section 10 as informational only.

---

## 1. Scope at a glance (counts + file map)

| Research file | Count delivered | Confidence | Feeds |
|---|---|---|---|
| `INCIDENTS.md` | 22 verified incidents, 14 domains, 100% primary-source cited | HIGH | `USE_CASES.md`, `CLIENT_JOURNEY.md` trigger moments, `READINESS_ASSESSMENT.md` §3 |
| `REGULATIONS.md` | 24 regulations with exact clause citations; 24 [GAP] flags; 1 [CITATION UNVERIFIED] (DO-178C A-7 obj. #9) | HIGH (primary), MEDIUM (3 sub-clause lookups) | `REGULATORY_GAPS.md`, `READINESS_ASSESSMENT.md` §4 |
| `ALTERNATIVES.md` | 10 alternatives analyzed, CERT-02 walk-through (lines 108-148), 3-domain rerun-cost math (GPT-3, CFD, Basel VaR) | HIGH | `WHY_NOT_ALTERNATIVES.md` |
| `PERSONAS.md` | 6 personas, every CLI flag verified against `sdk/metagenesis.py` + `scripts/mg.py` + `scripts/mg_client.py`, regulatory triggers cited | HIGH | `CLIENT_JOURNEY.md` |

---

## 2. Domain coverage matrix (14 domains)

| Domain | Existing claim | Incident cited | Regulation cited |
|---|---|---|---|
| ML/AI benchmarks | ML_BENCH-01/02/03 | Kapoor-Narayanan 2023, Zillow 2021 | EU AI Act, NIST AI RMF, SOC 2 |
| Pharma/Biotech | PHARMA-01 | Duke Potti 2010-15, Theranos 2015-22 (fraud), Takeda Actos | 21 CFR Part 11, FDA AI Draft Jan 2025, ISO 14155 |
| Medical devices | — (uses DT-SENSOR-01 analogue) | Therac-25 1985-87, Guidant 2002-05 | FDA 510(k), IEC 62304, EU MDR |
| Materials | MTR-1/2/3/4/5/6 ⚓ | Schön 2002 | AS9100D, ISO 26262 |
| Digital twin / FEM | DT-FEM-01 ⚓, DT-CALIB-LOOP-01 ⚓ | Takata 2001-14 | NASA-STD-7009B, AS9100D |
| IoT sensor / Aerospace | DT-SENSOR-01 | Air France 447 2009-12, 737 MAX 2018-19, Challenger 1986 (governance) | DO-178C, UN R155 |
| System ID / Science | SYSID-01 | CovidSim 2020, LaCour 2014, OSC Psych 2015 | NIH DMSP, Plan S, ALLEA |
| Algorithmic trading | — (FINRISK-01 pattern) | Knight Capital 2012, Flash Crash 2010 | MiFID II Art. 17 |
| Financial risk | FINRISK-01 | JPM London Whale 2012, LIBOR 2005-12 (governance) | Basel III BCBS 239, SR 11-7, SEC 17a-4 |
| Automotive sim | — (uses DT-FEM-01 + DT-SENSOR-01) | VW Dieselgate 2015, Uber ATG 2018 | UN R155, UN R156, ISO 26262 |
| Carbon / ESG | — | Verra 2023 | IFRS S1/S2, EU CSRD |
| Quantum computing | — | Google Sycamore 2019 (methodology dispute) | — |
| Data pipeline | DATA-PIPE-01 | — | NIH DMSP |
| Agent drift | AGENT-DRIFT-01 | — | SOC 2 CC7.2, NIST AI RMF MANAGE |

**Physical anchor present:** 10 claims (PHYS-01/02 SI 2019 exact; MTR-1/2/3/4/5/6 NIST measured; DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01 inherit).

---

## 3. Regulatory coverage summary (24 regulations, grouped)

- **Financial (4):** MiFID II Art. 17(2), Basel III BCBS 239 Principle 3, SR 11-7 Sections III/V/VI, SEC Rule 17a-4(f).
- **Pharma + Medical (6):** 21 CFR Part 11 §11.10(a)(e), FDA AI Credibility Draft Jan 2025 (7-step framework), FDA 510(k) 2023 final, IEC 62304 Clauses 5.1/5.5-5.7/5.8, ISO 14155 Clause 7.8.3, EU MDR Annex I §17.
- **Automotive + Aerospace (6):** ISO 26262 Parts 4/6/8, AS9100D Clause 8.3.4, NASA-STD-7009B CAS 8 factors, UN R155, UN R156 (strongest natural fit), DO-178C Table A-7 `[CITATION UNVERIFIED for obj. #9]`.
- **Science (3):** NIH NOT-OD-21-013 DMSP, Plan S Principles 5 + 8, ALLEA Code 2023 Section 2.
- **AI + Cryptography (4):** EU AI Act Arts. 10/12/15/26(6)/72, NIST FIPS 203/204/205 PQC, NIST AI RMF MEASURE/MANAGE, SOC 2 CC7.2/CC7.3/CC8.1.
- **Climate / ESG (1 combined):** IFRS S1/S2 + EU CSRD Art. 34a (CEAOB limited-assurance guidance).

**Bottom line:** Layers 1–5 hit all 24 regulations at least partially. 24 [GAP] flags cluster on three honest-scope categories: (a) training-data lineage (EU AI Act Art. 10), (b) human oversight / conceptual soundness / org governance (EU AI Act Art. 14, SR 11-7 Sec V, SOC 2 CC1-CC4, ISO 26262 HARA), (c) design-document certification (510(k), IEC 62304, DO-178C, AS9100D — all close-able by a thin `DOC-HASH-01` claim, but out of v3.1.0 scope).

---

## 4. Alternatives positioning (one-line matrix)

| Tool | Where it wins | Why MetaGenesis is additive, not replacement |
|---|---|---|
| SHA-256 of output | Single-file byte integrity | Cannot bind inputs/time/who/what-computation |
| Docker image hash | Environment reproducibility | Hash is build-time; outputs are runtime |
| MLflow / DVC | Team experiment hygiene | Server-of-record, not offline-verifiable |
| Manual audit | Semantic context / judgement | Not scalable, not repeatable |
| Signed PDF | Document authorship | Signs bytes, not the numbers' provenance |
| Git history | Code versioning | Code ≠ result |
| Jupyter output | Readable narrative | Output cells are editable JSON strings |
| Nextflow / CWL / Snakemake | Pipeline orchestration | Traces are plaintext; no external anchor |
| Chainpoint / RFC 3161 timestamp | Existence-at-time | Opaque hash; no semantic content |
| Coq / Lean4 formal | Algorithmic correctness | Does not prove execution on declared inputs |

**CERT-02 highlight (flagship):** `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` lines 108-148 proves an attacker with full byte-level write access can strip `job_snapshot` from `run_artifact.json`, recompute every SHA-256, resort the manifest, and recompute `root_hash`. Layer 1 PASSES. Layer 2 `_verify_semantic()` FAILS because the semantic structure is missing. This is the load-bearing example for "hashes alone are not enough."

**Rerun-cost math (3 domains):** GPT-3 ≈ $4.6M / 355 V100-years + GPU non-determinism; industrial CFD ≈ billion-cell mesh at 200,000 cores, days of wall time + MPI-reduction non-associativity; Basel Monte Carlo VaR ≈ 50k–100k paths nightly, seeded (bit-equality fails by construction). In all three, verification MUST operate on the artefact.

**Composability stance (must preserve):** MetaGenesis is **addition-on-top** of Docker, MLflow, git, Nextflow, Coq, etc. — never a replacement. Writer MUST NOT frame this as "MetaGenesis vs X"; frame as "X + MetaGenesis = verifiable X."

---

## 5. Persona → domain → regulatory trigger map

| # | Persona | Domain | Regulatory trigger | Primary claim | Integration |
|---|---|---|---|---|---|
| 1 | ML Engineer @ AI startup | ML/AI | SOC 2 Type II CC7.2 + CC8.1 | ML_BENCH-01 | 3 hours |
| 2 | Comp. Chemist @ biotech | Pharma | FDA AI Credibility Framework (Jan 2025) + 21 CFR Part 11 | PHARMA-01 | 4 hours |
| 3 | Model Risk Manager @ G-SIB | Finance | ECB TRIM + CRR Arts. 365-366 + SR 11-7 + PRA SS1/23 | FINRISK-01 | 5-8 days |
| 4 | FEM Engineer @ aerospace supplier | Materials + DT | AS9100D Clause 8.3.4/8.3.5 + NASA-STD-7009B | MTR-1 → DT-FEM-01 chain | 2-3 days |
| 5 | Quant Analyst @ hedge fund | Finance / trading | MiFID II Art. 17(2) + EU Del. Reg 2017/589 | ML_BENCH-02 (custom) | 1-2 weeks |
| 6 | Research Scientist @ lab | Science | Nature/Science reproducibility + NeurIPS Reproducibility Track + NIH DMP | ML_BENCH-01 | 1-2 days |

Every command in PERSONAS.md was verified against `sdk/metagenesis.py`, `scripts/mg.py`, `scripts/mg_client.py` — zero invented flags.

---

## 6. Deliverable → research-file dependency map

| Deliverable | Pulls primarily from | Secondary |
|---|---|---|
| `docs/USE_CASES.md` (12+ domains) | INCIDENTS (22 × "What happens when verification fails") | REGULATIONS (regulatory triggers per domain) |
| `docs/CLIENT_JOURNEY.md` (6 journeys) | PERSONAS (6 fully drafted) | INCIDENTS (trigger moments), REGULATIONS (compliance hooks) |
| `docs/WHY_NOT_ALTERNATIVES.md` (3 sections) | ALTERNATIVES (full 10-tool table + CERT-02 walk-through + 3-domain rerun-cost) | — |
| `docs/REGULATORY_GAPS.md` (3 → 24+ regs) | REGULATIONS (24 grouped in 6 buckets + summary matrix + gap list) | ALTERNATIVES (composability language) |
| `reports/READINESS_ASSESSMENT.md` (7-section honest verdict) | All 4 files | — |
| `README.md` Deep Reading row updates | All 4 files (cross-link targets) | — |

---

## 7. Honest boundaries (critical — must survive into every doc)

1. **SCOPE_001 physical-anchor scope reminder.** Only 10 of 20 claims have a physical anchor. ML, finance, pharma, sysid, sensor, and agent claims are **tamper-evident only** — they do NOT claim traceability to a physical constant. Documented in `reports/known_faults.yaml`. Writer MUST preserve this distinction.
2. **[CITATION UNVERIFIED] — DO-178C Table A-7 obj. #9.** REGULATIONS.md §3.6 explicitly flags this. `docs/REGULATORY_GAPS.md` MUST carry the flag forward with the exact phrasing.
3. **Governance-vs-verification distinction.** Three of the 22 incidents (Theranos, Challenger, LIBOR) are fundamentally governance/fraud failures, not pure verification-gap cases. INCIDENTS.md says so; `docs/USE_CASES.md` MUST say so. MetaGenesis would have reduced blast radius (signed test certs, cryptographic override trails, bound rate submissions to specific individuals) but would not have prevented criminal intent.
4. **EU AI Act Art. 10 training-data lineage — out of scope.** MetaGenesis verifies *outputs*, not training-data provenance. Documented; writer MUST NOT imply otherwise.
5. **EU AI Act Art. 14 human oversight — out of scope.** Cannot be automated; MetaGenesis supports human reviewers, does not replace them.
6. **Design-document certification — partial gap.** Possible via a future `DOC-HASH-01` claim but NOT IN SCOPE for v3.1.0.
7. **Post-quantum signatures — migration pending.** Ed25519 is fit for 2026. FIPS 204 ML-DSA dual-signing is a multi-year roadmap item. NSS transition deadline 2030.

---

## 8. Watch Out For (top 5 risks for the docs writer)

1. **Banned-term regression.** CLAUDE.md prohibits `tamper-proof`, `blockchain`, `unforgeable`, `GPT-5`, `100% test success`, any stale test count, any stale version. Also marketing language `revolutionary / game-changing / unprecedented`. Use `tamper-evident`, `cryptographic hash chain`, `2407 tests PASS`, `v1.0.0-rc1`. Run `python scripts/check_stale_docs.py` before commit.
2. **Over-claiming on governance-failure incidents.** Theranos, Challenger, LIBOR — write these as "MetaGenesis would have bounded the damage / made concealment cryptographically expensive" NOT "would have prevented."
3. **Replace-vs-add framing on ALTERNATIVES.** Compose, never replace. Docker + MetaGenesis. MLflow + MetaGenesis. Formal verification + MetaGenesis.
4. **Stale-rule trap (UPDATE_PROTOCOL v1.1).** If any count changes (test count, claim count, domain count), update `scripts/check_stale_docs.py` required strings in the SAME PR. Otherwise 13 files report false PASS for up to a week.
5. **Scope creep into new claims.** The 5 prioritised future claims (§10) are DOCUMENTED, NOT IMPLEMENTED, in v3.1.0. The milestone is docs only. If the writer gets tempted to "just add AUTO-OTA-01 quickly," STOP — that's a separate milestone with the mandatory 6-step claim lifecycle.

---

## 9. Confidence assessment

| Area | Confidence | Notes |
|---|---|---|
| Incidents (22) | HIGH | Every figure traceable to SEC / FDA / EPA / NTSB / BEA / retraction notice / federal docket |
| Regulations (24) | HIGH for primaries, MEDIUM for 3 sub-clause numberings | 1 [CITATION UNVERIFIED] flagged (DO-178C A-7 #9); ISO 26262 sub-clauses via secondary source |
| Alternatives (10) | HIGH | CERT-02 walked directly from test file; GPT-3 / CFD / VaR figures from peer-reviewed or vendor primaries |
| Personas (6) | HIGH | Every CLI flag verified against `sdk/metagenesis.py` + `scripts/mg.py` + `scripts/mg_client.py`; every regulatory citation has clause reference |
| **Overall** | **HIGH** | Docs writer can quote figures and citations with confidence; carry forward the single [CITATION UNVERIFIED] flag verbatim |

**Remaining gaps (for READINESS_ASSESSMENT.md to address honestly):** (a) training-data lineage, (b) human-oversight automation, (c) org-governance controls, (d) design-document certification, (e) post-quantum signing migration, (f) process-framework coverage (HARA, FMEDA, conceptual soundness review).

---

## 10. Prioritised future claim additions — **OUT OF SCOPE for v3.1.0, informational only**

Surfaced by REGULATIONS.md §8 as high-leverage future additions. Each requires the mandatory 6-step claim lifecycle (CLAUDE.md) and belongs to a **later** milestone, not this docs pass.

1. **`AUTO-OTA-01`** — UN R156 SUMS (Software Update Management System). Strongest natural fit; bundle ≡ update package.
2. **`CLIMATE-01`** — IFRS S2 / CSRD GHG accounting certificate. 2026 CSRD limited-assurance deadline opens market.
3. **`TRADING-01`** — MiFID II Art. 17(2) order / cancellation / quotation log. Highest-margin vertical.
4. **`EDC-01`** — ISO 14155 Clause 7.8.3 Electronic Data Capture. Pharma clinical-trial fit.
5. **`DOC-HASH-01`** — Design-document hash+signature claim. Small effort, unlocks 510(k) + IEC 62304 + DO-178C + AS9100D design-document provenance.

**For docs writer:** You may REFERENCE these in `docs/REGULATORY_GAPS.md` and `reports/READINESS_ASSESSMENT.md` as "planned future additions (not yet implemented in v1.0.0-rc1)." You may NOT write them up as if they exist.

---

## Sources (aggregated)

- **INCIDENTS.md** — SEC filings, FDA/EPA notices, NTSB/BEA reports, journal retractions, US federal-court dockets, US Senate subcommittee reports (22 incidents).
- **REGULATIONS.md** — EUR-Lex, ecfr.gov, NIST CSRC, IFRS Foundation, ISO.org, UNECE, AICPA, Federal Reserve, grants.nih.gov, cOAlition S, ALLEA (24 regulations).
- **ALTERNATIVES.md** — CERT-02 test file (direct read), `SECURITY.md`, `scripts/mg.py`, Lambda Labs via TechTalks, Stanford AI Index via Statista, Siemens Simcenter, AIAA SciTech 2025, MDPI Risks 2025 (10 alternatives + 3-domain rerun math).
- **PERSONAS.md** — Direct read of `sdk/metagenesis.py`, `scripts/mg.py`, `scripts/mg_client.py`; SOC 2 TSC, FDA AI Draft Jan 2025, ECB TRIM, MiFID II, AS9100D, NASA-STD-7009B, NIH DMP, NeurIPS Reproducibility Track.
