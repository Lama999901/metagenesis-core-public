# Regulatory Gap Analysis

**Date:** 2026-04-16
**Protocol version:** v1.0.0-rc1 (2407 tests, 20 claims, 5 verification layers, 8 innovations)
**Purpose:** Map MetaGenesis Core's 5-layer verification architecture and 20 scientific claims against 24 regulations a compliance officer, auditor, or regulator is likely to cite — with exact article / clause / section numbers, authoritative source links, and explicit `[GAP]` flags where MetaGenesis does not cover the requirement.

---

## Overview

MetaGenesis Core v1.0.0-rc1 ships five independent verification layers and 20 domain claims:

- **Layer 1** — SHA-256 integrity (`pack_manifest.json` root_hash).
- **Layer 2** — Semantic verification (`_verify_semantic()` in `scripts/mg.py`).
- **Layer 3** — Step Chain (`execution_trace` + `trace_root_hash`).
- **Layer 4** — Bundle Signing (HMAC-SHA-256 plus Ed25519, `scripts/mg_sign.py` + `scripts/mg_ed25519.py`).
- **Layer 5** — Temporal Commitment (NIST Randomness Beacon, `scripts/mg_temporal.py`).

Ten of the 20 claims carry a physical anchor (PHYS-01 `kB` and PHYS-02 `NA` are SI 2019 exact constants with zero declared uncertainty; MTR-1 through MTR-6 are NIST-measured material properties; DT-FEM-01, DRIFT-01, and DT-CALIB-LOOP-01 inherit the MTR-1 anchor). The remaining ten claims are **tamper-evident only** — they cryptographically prove "this exact number was produced on this exact input by this exact code at this exact time" but do not assert traceability to a physical constant. This distinction is documented as `SCOPE_001` in `reports/known_faults.yaml` and survives into every regulatory row below.

This document groups 24 regulations into six domain buckets (Financial, Pharma + Medical, Automotive + Aerospace, Science, AI + Cryptography, Climate / ESG), records the exact article or clause cited by each regulation, names the MetaGenesis layer(s) and claim(s) that address it, and attaches an explicit `[GAP]` flag wherever MetaGenesis falls short. The honest-boundaries section (§9) clusters the `[GAP]` flags into the three scope categories that cannot be closed without a protocol extension. The future-roadmap section (§10) lists the five planned claim additions that would close specific gaps — none are implemented in v1.0.0-rc1 and none are in scope for v3.1.0.

The single `[CITATION UNVERIFIED]` flag on DO-178C Table A-7 objective #9 is preserved verbatim per RG-04; we record the exact wording from a secondary source and flag that the exact text could not be cross-checked against the standard itself.

**Authoritative source hierarchy for the citations below:** EUR-Lex → ecfr.gov → NIST CSRC → IFRS Foundation → ISO.org → UNECE → AICPA → Federal Reserve / OCC → grants.nih.gov → cOAlition S → ALLEA.

### Coverage assessment matrix (24 regulations × 5 layers)

| # | Regulation | Citation | L1 integrity | L2 semantic | L3 step chain | L4 signing | L5 temporal | Nearest claim | Overall |
|---|---|---|---|---|---|---|---|---|---|
| 1 | MiFID II | Art. 17(2) 2nd subpara | Yes | — | Yes | Yes | Yes | FINRISK-01 (pattern) | Partial (TRADING-01 planned) |
| 2 | Basel III / BCBS 239 | Principle 3 | Yes | Yes | Yes | — | — | FINRISK-01, DRIFT-01 | Partial (pipeline process) |
| 3 | SR 11-7 | Sections III, V, VI | Yes | Yes | Yes | Yes | Yes | FINRISK-01, DRIFT-01, AGENT-DRIFT-01 | Partial (conceptual soundness) |
| 4 | SEC Rule 17a-4 | 17 CFR 240.17a-4(f) | Yes | — | — | Yes | Yes | — | Partial (D3P legal) |
| 5 | 21 CFR Part 11 | §11.10(a), §11.10(e) | Yes | Yes | Yes | — | Yes | PHARMA-01 | Partial (access controls) |
| 6 | FDA AI Credibility | Jan 2025 draft, 7-step | Yes | Yes | Yes | Yes | Yes | PHARMA-01, ML_BENCH-01..03 | Partial (plan authoring) |
| 7 | FDA 510(k) software | June 2023 final | Yes | — | Yes | Yes | Yes | DT-FEM-01, ML_BENCH-01..03 | Partial (design docs) |
| 8 | IEC 62304 | Cl. 5.1, 5.5-5.7, 5.8 | Yes | — | Yes | Yes | Yes | DT-FEM-01 | Partial (design docs) |
| 9 | ISO 14155 | Cl. 7.8.3 | Yes | — | Yes | — | Yes | DT-SENSOR-01 (pattern) | Partial (EDC-01 planned) |
| 10 | EU MDR | Annex I §17 | Yes | Yes | Yes | Yes | Yes | DT-FEM-01 | Partial (clinical eval) |
| 11 | ISO 26262 | Parts 4, 6, 8 | Yes | — | Yes | Yes | — | DT-FEM-01, MTR-4/5 | Partial (HARA/FMEDA) |
| 12 | AS9100D | Cl. 8.3.4 | Yes | — | Yes | Yes | — | DT-FEM-01, MTR-4 | Partial (design-review minutes) |
| 13 | NASA-STD-7009B | CAS 8 factors | Yes ⚓ | Yes | Yes | Yes | Yes | DT-FEM-01, PHYS-01/02 ⚓, MTR-* ⚓ | Partial (CAS 6-8 organisational) |
| 14 | UN R155 | Annex 5 | Yes | — | — | Yes | Yes | — | Partial (AUTO-CSMS claim absent) |
| 15 | UN R156 | R156 + ISO 24089 | Yes | — | — | Yes | Yes | — | Strongest natural fit (AUTO-OTA-01 planned) |
| 16 | DO-178C | Table A-7 (obj. #9 `[CITATION UNVERIFIED]`) | Yes | — | Yes | Yes | Yes | DT-FEM-01, ML_BENCH-01..03 | Partial (design data items) |
| 17 | NIH DMSP | NOT-OD-21-013 | Yes | — | — | Yes | Yes | DATA-PIPE-01 | Partial (repository function) |
| 18 | Plan S | Principles 5, 8 | Yes | — | — | Yes | — | DATA-PIPE-01 | Good (licensing editorial) |
| 19 | ALLEA Code 2023 | Section 2 | Yes | Yes | Yes | Yes | Yes | All 20 claims | Good (authorship editorial) |
| 20 | EU AI Act | Arts. 10, 12, 15, 26(6), 72 | Yes | — | Yes | Yes | Yes | ML_BENCH-01..03, DRIFT-01 | Partial (Art. 10 data lineage) |
| 21 | NIST FIPS 203/204/205 | Aug 2024 finalised | — | — | — | Ed25519 only | — | — | `[GAP]` PQC migration pending |
| 22 | NIST AI RMF 1.0 | MEASURE, MANAGE | Yes | Yes | Yes | Yes | Yes | ML_BENCH-01..03, DRIFT-01, AGENT-DRIFT-01 | Partial (GOVERN / MAP organisational) |
| 23 | SOC 2 TSC | CC7.2, CC7.3, CC8.1 | Yes | — | — | Yes | Yes | DRIFT-01, AGENT-DRIFT-01 | Partial (CC1-CC4 organisational) |
| 24 | IFRS S1/S2 + EU CSRD | CSRD Art. 34a | Yes | Yes | Yes | Yes | Yes | — | Partial (CLIMATE-01 planned) |

`⚓` = claim carries a physical anchor and therefore strengthens the relevant factor (notably NASA-STD-7009B CAS Input Pedigree / Results Uncertainty).

---

## 1. Financial

### 1.1 MiFID II — Directive 2014/65/EU, Article 17 (Algorithmic Trading)

- **Citation:** `Directive 2014/65/EU, Article 17(1)` (general algorithmic trading) and **`Article 17(2) second subparagraph`** (record-keeping obligation for firms engaging in a high-frequency algorithmic trading technique).
- **Mandates:** Article 17(2) 2nd subpara — "An investment firm that engages in a high-frequency algorithmic trading technique shall store in an approved form accurate and time sequenced records of all its placed orders, including cancellations of orders, executed orders and quotations on trading venues and shall make them available to the competent authority upon request." Article 17(1) adds effective systems and controls, orderly-operation arrangements, business-continuity arrangements, and records of compliance.
- **MetaGenesis coverage:**
  - Layer 1 (SHA-256) + Layer 3 (step chain) deliver "accurate" and cryptographically-ordered records.
  - Layer 5 (NIST Beacon temporal commitment) delivers "time sequenced" with a property that exceeds the clause — the bundle temporal binding `SHA-256(pre_commitment ‖ beacon_value)` cannot be computed before the beacon value is published, so a bundle cannot be backdated even by the firm that signs it.
  - Layer 4 (Ed25519) attaches non-repudiable signer identity — which investment firm produced this record.
  - FINRISK-01 (VaR certificate) demonstrates the pattern for risk-model outputs. The bundle format is order-record agnostic.
- **[GAP]** No existing MetaGenesis claim packages order, cancellation, and quotation logs specifically. A new `TRADING-01` claim following the mandatory 6-step lifecycle (see `CLAUDE.md`) would close this gap. The current bundle format can carry the data; only the claim template is missing.
- **Source:** [EUR-Lex — Directive 2014/65/EU consolidated](https://eur-lex.europa.eu/eli/dir/2014/65/oj/eng) · [ESMA Interactive Single Rulebook — Article 17](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mifid-ii/article-17-algorithmic-trading)

### 1.2 Basel III — BCBS 239 (Principles for Effective Risk Data Aggregation and Risk Reporting)

- **Citation:** `BCBS 239, Principle 3 — Accuracy and Integrity` (Bank for International Settlements, January 2013). Related: `Principle 2 — Data Architecture and IT Infrastructure`; `Principle 6 — Adaptability`.
- **Mandates:** Principle 3 — "A bank should be able to generate accurate and reliable risk data to meet normal and stress/crisis reporting accuracy requirements. Data should be aggregated on a largely automated basis so as to minimise the probability of errors." Data must be reconciled with accounting data; differences must be explained.
- **MetaGenesis coverage:**
  - Layer 1 (SHA-256) provides byte-exact data integrity.
  - Layer 3 (step chain) proves the *aggregation computation* was not tampered with — each aggregation step hashes the previous step's output, so reordering or altering any intermediate step invalidates `trace_root_hash`.
  - FINRISK-01 plus DRIFT-01 together satisfy reconciliation with a trusted anchor (anchor = baseline model output; drift > 5% triggers correction).
- **[GAP]** Principle 3 specifies "largely automated" aggregation — MetaGenesis verifies *outputs*, not the *automation pipeline itself*. A compliance officer still needs separate controls evidence for the aggregation pipeline.
- **Source:** [BCBS 239 — Principles for effective risk data aggregation and risk reporting (PDF)](https://www.bis.org/publ/bcbs239.pdf)

### 1.3 SR 11-7 — Federal Reserve / OCC Supervisory Guidance on Model Risk Management (2011-04-04)

- **Citation:** `SR 11-7 / OCC 2011-12, Section III — Model Development, Implementation, and Use`; **`Section V — Validation` (subsection on Ongoing Monitoring)**; `Section VI — Governance, Policies, and Controls`.
- **Mandates:** Banks must maintain "robust model development, implementation, and use; effective validation; and sound governance, policies, and controls." Validation must include "an evaluation of conceptual soundness, ongoing monitoring, and outcomes analysis" and must be performed by parties independent of model development.
- **MetaGenesis coverage:**
  - FINRISK-01 (VaR certificate), ML_BENCH-01/02/03 (accuracy / RMSE / MAPE certificates), and DRIFT-01 (anchor drift monitor) together cover the outcomes-analysis and ongoing-monitoring requirements.
  - Layers 1–5 deliver "effective validation" because an independent party can verify the bundle offline without access to the model, data, or compute environment — which is the gold standard for "independent validation" in SR 11-7 Section V.
  - AGENT-DRIFT-01 is a meta-claim: the agent that monitors model drift can itself be monitored cryptographically.
- **[GAP]** SR 11-7 also requires "conceptual soundness" review — a judgemental activity that MetaGenesis does not and cannot automate. Bundles support the human reviewer's work; they do not replace it.
- **Source:** [Federal Reserve SR 11-7](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) · [SR 11-7 PDF](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.pdf)

### 1.4 SEC Rule 17a-4 — Broker-Dealer Records Retention (17 CFR 240.17a-4)

- **Citation:** `17 CFR § 240.17a-4(f)` (electronic recordkeeping). The October 2022 amendment adds the "audit-trail alternative" alongside the legacy WORM (write-once-read-many) requirement.
- **Mandates:** A broker-dealer electing an electronic recordkeeping system must meet either (i) the WORM requirement, or (ii) the audit-trail requirement that "maintains and preserves electronic records in a manner that permits the recreation of an original record if it is modified or deleted." Retention periods are specified per-category in 17a-4(b) (3 or 6 years) and 17a-4(e) (lifetime for corporate-governance records).
- **MetaGenesis coverage:**
  - Layer 1 (SHA-256) plus Layer 4 (Ed25519 signing) satisfy the audit-trail alternative: a tampered or deleted record is detectable because the signature breaks and the manifest hash no longer validates.
  - Layer 5 (temporal commitment) provides an authoritative "time of record" value no party — including the broker-dealer — can backdate.
- **[GAP]** `17a-4(f)(3)(ii)` also requires a Designated Third Party (D3P) that can access records at SEC request if the broker-dealer is unavailable. MetaGenesis bundles are self-contained and offline-verifiable, but the D3P designation and agreement are operational and legal artefacts outside the protocol.
- **Source:** [eCFR — 17 CFR 240.17a-4](https://www.law.cornell.edu/cfr/text/17/240.17a-4) · [SEC — Amendments to Electronic Recordkeeping Requirements for Broker-Dealers (Oct 2022)](https://www.sec.gov/investment/amendments-electronic-recordkeeping-requirements-broker-dealers)

---

## 2. Pharma + Medical

### 2.1 FDA 21 CFR Part 11 — Electronic Records and Electronic Signatures

- **Citation:** `21 CFR § 11.10` (Controls for closed systems), Subpart B. Subsection **`11.10(e)`** is the audit-trail clause; subsection `11.10(a)` is the validation clause.
- **Mandates:**
  - `11.10(a)` — "validation of systems to ensure accuracy, reliability, consistent intended performance, and the ability to discern invalid or altered records."
  - `11.10(e)` — "secure, computer-generated, time-stamped audit trails to independently record the date and time of operator entries and actions that create, modify, or delete electronic records. Record changes shall not obscure previously recorded information."
- **MetaGenesis coverage:**
  - Layer 3 (step chain) directly fulfils `11.10(e)` — every step is hashed with the previous hash, so changes cannot obscure prior records; any change invalidates downstream hashes.
  - Layer 5 (temporal commitment) delivers the "time-stamped" requirement with a property that exceeds `11.10(e)` — even the signer cannot backdate because the beacon value used in the temporal binding is only published after the commitment is made.
  - PHARMA-01 (ADMET prediction certificate) is the reference claim for computational pharmaceutical outputs.
- **[GAP]** `11.10(d)` (limiting system access) and `11.10(g)` (authority checks) are operational controls on the signer's environment. MetaGenesis verifies the *output*, not the *system that produced it*. FDA expects SOPs and access logs *in addition to* MetaGenesis bundles.
- **Source:** [eCFR — 21 CFR 11.10](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/subpart-B/section-11.10)

### 2.2 FDA Draft Guidance (January 2025) — AI Credibility Assessment for Drug and Biological Products

- **Citation:** FDA draft guidance "Considerations for the Use of Artificial Intelligence to Support Regulatory Decision-Making for Drug and Biological Products" (issued 2025-01-06; public comment closed 2025-04-07). Structure: 7-step Credibility Assessment Framework.
- **Mandates:** Seven steps — (1) define the question of interest; (2) define the Context of Use (COU) for the AI model; (3) assess AI model risk (model influence × decision consequence); (4) develop a credibility assessment plan aligned with that risk; (5) execute the plan; (6) document the results (including deviations); (7) monitor lifecycle.
- **MetaGenesis coverage:**
  - Step 5 (execute plan) + Step 6 (document results): Layers 1–5 deliver cryptographic documentation that outputs match the declared plan. ML_BENCH-01/02/03 and PHARMA-01 are the applicable claim templates.
  - Step 7 (monitor lifecycle): DRIFT-01 and AGENT-DRIFT-01 deliver calibration-chain and agent-quality drift monitoring.
  - Physical anchors ⚓ (PHYS-01 `kB`, PHYS-02 `NA` — both SI 2019 exact) strengthen Step 3 risk assessment where physical-reality traceability is needed.
- **[GAP]** Steps 1–4 are sponsor-authored design documents — MetaGenesis does not produce them. A bundle can *refer to* the plan document (by hash), but the plan itself is a human-authored artefact and MetaGenesis does not certify the plan's content.
- **Source:** [FDA — Framework to Advance Credibility of AI Models (Jan 2025)](https://www.fda.gov/news-events/press-announcements/fda-proposes-framework-advance-credibility-ai-models-used-drug-and-biological-product-submissions) · [FDA CDER — AI for Drug Development](https://www.fda.gov/about-fda/center-drug-evaluation-and-research-cder/artificial-intelligence-drug-development)

### 2.3 FDA 510(k) — Content of Premarket Submissions for Device Software Functions (June 2023 final guidance)

- **Citation:** FDA Guidance "Content of Premarket Submissions for Device Software Functions" (final 2023-06-14; replaces the 2005 "Software Contained in Medical Devices" guidance). Two documentation levels: `Basic Documentation` and `Enhanced Documentation`.
- **Mandates:** Enhanced Documentation applies where a software failure could cause a hazardous situation with probable risk of death or serious injury. Required artefacts: software description, software requirements specification (SRS), architecture, software design specification (SDS), V&V testing, version history, unresolved anomalies, SDLC processes, configuration management, maintenance practices, risk-management file.
- **MetaGenesis coverage:**
  - "V&V testing" and "unresolved anomalies" evidence can be packaged as DT-FEM-01 (engineering V&V) or ML_BENCH-01/02/03 (model V&V) bundles, each cryptographically signed and temporally committed.
  - Layer 4 plus Layer 5 deliver non-repudiation of the test results to the FDA reviewer.
- **[GAP]** SRS, SDS, architecture, and risk-management file are *design documents*, not computational outputs. MetaGenesis does not currently certify design documents — they are markdown or PDF, not execution traces. A planned `DOC-HASH-01` claim (file-level integrity plus signature) would close this gap with small effort. See §10.
- **Source:** [FDA — Premarket Notification 510(k)](https://www.fda.gov/medical-devices/premarket-submissions-selecting-and-preparing-correct-submission/premarket-notification-510k) · [FDA Guidance on Device Software Functions (2023)](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/content-premarket-submissions-device-software-functions)

### 2.4 IEC 62304 — Medical Device Software Lifecycle Processes

- **Citation:** `IEC 62304:2006+A1:2015, Clause 5` (Software development process). In particular `Clause 5.1` (Software development planning); `Clauses 5.5–5.7` (Software verification); `Clause 5.8` (Software release). Sub-clause `5.1.4` applies only to Class C; `5.1.5, 5.1.10, 5.1.11` apply to Class B and C. Sub-clauses `5.8.1, 5.8.2, 5.8.3, 5.8.5, 5.8.6, 5.8.7, 5.8.8` apply to Class B and C.
- **Mandates:** Class A = software requirements plus software release documented; Class B = architecture plus verification added; Class C = detailed design added. Clause 5.8 requires verified, versioned, anomaly-tracked releases with reliable delivery.
- **MetaGenesis coverage:**
  - `5.8.1`–`5.8.8` (verified, versioned release) is directly satisfied by Layers 1–5: the bundle is a versioned, hashed, signed, temporally-committed artefact. "Reliable delivery" — the bundle itself is the deliverable.
  - `5.5`–`5.7` (verification) satisfied where outputs can be expressed as computational claims (DT-FEM-01, ML_BENCH-01, DT-SENSOR-01).
- **[GAP]** `5.1` (planning), `5.3`/`5.4` (architecture and detailed design) are design documents — the same scope gap as 510(k) above. Closable by `DOC-HASH-01` (§10).
- **Source:** [ISO — ISO/IEC 62304:2006](https://www.iso.org/standard/38421.html) · [IEC 62304 overview — Johner Institute](https://blog.johner-institute.com/iec-62304-medical-software/safety-class-iec-62304/)

### 2.5 ISO 14155:2020 — Clinical Investigation of Medical Devices (GCP)

- **Citation:** `ISO 14155:2020, Clause 7.8` (Document and data control), in particular **`Clause 7.8.3`** (Electronic clinical data systems). Related: `Clause 8` (Responsibilities of the sponsor); `Clause 9` (Responsibilities of the principal investigator).
- **Mandates:** `7.8.3` requires that electronic data capture (EDC) systems be validated for "authenticity, accuracy, reliability, and consistent performance." Source data must be contemporaneous. Retention is per regulatory requirement.
- **MetaGenesis coverage:**
  - Layer 1 (integrity) + Layer 3 (chain) directly address "authenticity, accuracy, reliability."
  - "Contemporaneous" is the exact property Layer 5 delivers via NIST Beacon temporal commitment.
  - DT-SENSOR-01 (IoT sensor schema+range+temporal validation) is the nearest existing claim. A PHARMA-specific `EDC-01` claim would follow the same 6-step lifecycle.
- **[GAP]** ISO 14155 also requires signed informed consent and protocol-deviation logs — outside MetaGenesis scope. The `EDC-01` future claim (§10) would cover the computational-record path; consent artefacts remain out of scope.
- **Source:** [ISO 14155:2020](https://www.iso.org/standard/71690.html)

### 2.6 EU MDR — Regulation (EU) 2017/745, Annex I (GSPR for Software)

- **Citation:** `Regulation (EU) 2017/745, Annex I, Chapter II, Section 17` (software requirements in the General Safety and Performance Requirements). Qualification guidance is in `MDCG 2019-11 Rev.1` (June 2025).
- **Mandates:** `Annex I §17.1` — software shall be developed and manufactured "in accordance with the state of the art taking into account the principles of development life cycle, risk management, including information security, verification and validation." `§17.2` requires repeatability, reliability, and performance in line with intended use.
- **MetaGenesis coverage:**
  - "Verification and validation" for computational outputs is exactly the MetaGenesis protocol. DT-FEM-01 is the reference claim for simulation V&V.
  - "Information security" — Ed25519 (Layer 4) plus NIST-Beacon temporal commitment (Layer 5) are state-of-the-art cryptographic primitives.
  - Layers 1–5 together align with the "state of the art" requirement in `§17.1`.
- **[GAP]** MDR requires clinical evaluation (Annex XIV) and post-market surveillance (Articles 83–86) — these are regulatory processes, not computational outputs. MetaGenesis bundles *support* the evidence package but do not replace it.
- **Source:** [EUR-Lex — Regulation (EU) 2017/745](https://eur-lex.europa.eu/eli/reg/2017/745/oj/eng) · [MDCG 2019-11 Rev.1 — Qualification of MDSW](https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en)

---

## 3. Automotive + Aerospace

### 3.1 ISO 26262 — Road Vehicles Functional Safety

- **Citation:** `ISO 26262-6:2018, Clause 9` (Software unit verification); `ISO 26262-6:2018, Clause 10` (Software integration and verification); `ISO 26262-8:2018, Clause 10` (Documentation management); `ISO 26262-8:2018, Clause 11` (Confidence in the use of software tools); `ISO 26262-4:2018, Clause 9` (System-level integration and verification).
- **Mandates:** Verification coverage and traceability scale with ASIL level (A → D, D highest). ASIL D requires MC/DC coverage, full requirements traceability, and comprehensive documentation. Tool qualification under Part 8 Clause 11 requires evidence that tools used in the safety lifecycle produce trustworthy output.
- **MetaGenesis coverage:**
  - MetaGenesis itself is a candidate `T2`-classified tool under ISO 26262-8 §11. The 5-layer architecture plus CERT-11 proof of layer independence plus RFC 8032 validation of Ed25519 plus the adversarial proof suite (CERT-02 through CERT-12) constitute substantive tool-qualification evidence.
  - Verification *output* evidence (Clause 9 / 10) is directly packagable as DT-FEM-01 (physics), MTR-4 / MTR-5 / MTR-6 (material calibration for aerospace- and nuclear-grade metals), or ML_BENCH-01 (if ADAS ML models are in scope).
- **[GAP]** ISO 26262 is fundamentally a *process* standard — MetaGenesis verifies artefacts, not the HARA, safety case, or FMEDA processes. HARA and FMEDA are out of scope; this is documented in the honest-boundaries section §9.2.
- **Source:** [ISO 26262-6:2018](https://www.iso.org/standard/68388.html) · [ISO 26262-8:2018](https://www.iso.org/standard/68390.html)

### 3.2 AS9100 Rev D — Aerospace Quality Management, Clause 8.3

- **Citation:** `AS9100 Rev D:2016, Clause 8.3` (Design and development of products and services). Sub-clauses: `8.3.2` (planning); `8.3.3` (inputs); **`8.3.4`** (design and development controls — merged verification and validation); `8.3.5` (outputs); `8.3.6` (changes).
- **Mandates:** `8.3.4` requires reviews, verification ("design outputs correspond to design inputs"), and validation ("resulting products and services are capable of meeting requirements for the specified application or intended use"). The `8.3.4 Note` requires retention of documented information as objective evidence.
- **MetaGenesis coverage:**
  - `8.3.4` objective evidence for any *computational* design output is exactly what MetaGenesis produces. A DT-FEM-01 bundle is "design verification evidence" for FEM-based analyses.
  - MTR-4 (Ti-6Al-4V `E ≈ 114 GPa`) and MTR-5 (SS316L `E ≈ 193 GPa`) are the aerospace and nuclear-grade material calibration anchors.
  - Layer 4 (Ed25519) enables third-party certifying-body (Nadcap and similar) verification without access to proprietary models.
- **[GAP]** Design-review minutes and the design-changes log are human-maintained records — MetaGenesis can hash them (a `DOC-HASH-01`-style claim, not yet implemented — see §10) but does not author them.
- **Source:** [ISO-Registrar — AS9100D 8.3.4 overview](https://www.isaregistrar.com/design-and-development-control-clause-8-3-4-of-iso-9001-as9100d-standard/) · [SAE AS9100D standard](https://www.sae.org/standards/content/as9100d/)

### 3.3 NASA-STD-7009B — Standard for Models and Simulations (March 2024)

- **Citation:** `NASA-STD-7009B, Section 4` (Requirements) and the **Credibility Assessment Scale (CAS)** with 8 factors across 3 categories:
  - *M&S Development:* (1) Verification, (2) Validation.
  - *M&S Operations:* (3) Input Pedigree, (4) Results Uncertainty, (5) Results Robustness.
  - *Supporting Evidence:* (6) Use History, (7) M&S Management, (8) People Qualifications.
  Each factor is scored on a 0–4 scale.
- **Mandates:** Any M&S output presented to a decision-maker must include (a) best estimate, (b) uncertainty statement, (c) CAS evaluation, (d) explicit caveats.
- **MetaGenesis coverage:**
  - Factors (1) Verification and (2) Validation are directly delivered by DT-FEM-01 plus MTR-1 through MTR-6 plus DRIFT-01.
  - Factor (3) Input Pedigree is delivered by dataset SHA-256 fingerprinting inside the bundle (`pack_manifest.json` carries input hashes).
  - Factors (4) Results Uncertainty and (5) Results Robustness are partially covered — claims carry a tolerance (e.g. `rel_err ≤ 0.02`) but do not auto-propagate full uncertainty budgets.
  - PHYS-01 ⚓ and PHYS-02 ⚓ (SI 2019 exact, zero declared uncertainty) are ideal "Input Pedigree level 4" anchors.
- **[GAP]** CAS factors (6) Use History, (7) M&S Management, and (8) People Qualifications are organisational and operational evidence — MetaGenesis does not touch them.
- **Source:** [NASA-STD-7009B (March 2024) PDF](https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf) · [NASA Standards — NASA-STD-7009 page](https://standards.nasa.gov/standard/NASA/NASA-STD-7009)

### 3.4 UN R155 — Cybersecurity Management System (Vehicles)

- **Citation:** `UN Regulation No. 155 (E/ECE/TRANS/505/Rev.3/Add.154)`, Annex 5 (69 attack vectors / risk categories). Type-approval in force since July 2022 for new types; applies to all vehicles manufactured on or after 1 July 2024 in the UNECE contracting parties.
- **Mandates:** The vehicle manufacturer must operate a certified Cybersecurity Management System (CSMS) covering development, production, and post-production. Risk assessment must address all 69 threat categories, with evidence maintained throughout vehicle lifecycle.
- **MetaGenesis coverage:**
  - UN R155 risk-assessment *outputs* (per-threat mitigation verification) can be packaged as bundles — each threat's test result becomes a claim.
  - Layer 4 (Ed25519 per-OEM) gives approval authorities per-signer provenance.
  - Layer 5 (temporal) proves *when* a mitigation test was run — critical if post-market surveillance reveals that the mitigation was never actually tested on this vehicle generation.
- **[GAP]** No existing MetaGenesis claim targets UN R155 specifically. An `AUTO-CSMS-01` claim would need to be authored. Also, the CSMS itself is a *management system* (process), not a computational output — so only the risk-assessment outputs are in scope.
- **Source:** [UNECE — UN Regulation No. 155](https://unece.org/transport/documents/2021/03/standards/un-regulation-no-155-cyber-security-and-cyber-security) · [EUR-Lex — UN R155 (OJ L 2025/5)](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202500005)

### 3.5 UN R156 — Software Update Management System (Vehicles)

- **Citation:** `UN Regulation No. 156`, in force since July 2022; mandatory for new vehicles from 1 July 2024. Harmonised with `ISO 24089:2023` (Road vehicles — Software update engineering).
- **Mandates:** The manufacturer operates a certified SUMS that can "plan, package, approve, deliver, verify, and record software updates securely across a vehicle's service life." Software integrity must be validated on delivery; update logs must be auditable.
- **MetaGenesis coverage (strongest natural fit in the regulatory landscape):**
  - The verbs "package, approve, deliver, verify, record" map almost one-to-one onto the MetaGenesis bundle lifecycle:
    - **Package** → `mg pack`
    - **Approve** → Layer 4 Ed25519 signature by OEM
    - **Verify** → `mg verify --pack`
    - **Record** → Layer 5 temporal commitment in `temporal_commitment.json`
  - A planned `AUTO-OTA-01` claim (§10) would formalise this — the mapping is so direct that the bundle effectively *is* the update package.
- **[GAP]** Delivery-channel security (TLS, PKI for the over-the-air pipe) is transport-layer security — MetaGenesis secures the *payload* end-to-end but does not prescribe the transport.
- **Source:** [UNECE — UN R156 page](https://unece.org/transport/vehicle-regulations/working-party-automated-autonomous-and-connected-vehicles-introduction) · [ISO 24089:2023](https://www.iso.org/standard/77796.html)

### 3.6 DO-178C — Software Considerations in Airborne Systems (RTCA / EUROCAE ED-12C)

- **Citation:** `DO-178C (December 2011)`, Design Assurance Levels A–E, with Annex A objective tables. **`Table A-7` — Verification of Verification Process Results** contains 9 objectives. Object #5 (MC/DC), #6 (decision coverage), #7 (statement coverage) apply to DAL A; objectives 5, 6, 7, 8 do not apply to DAL D or E.
- **Mandates:** DAL A (catastrophic failure) = 66 objectives; DAL B = 65; DAL C = 57; DAL D = 28; DAL E = 0. Each requires documented verification evidence retained as `Software Life Cycle Data` artefacts (per DO-178C §11).
- **MetaGenesis coverage:**
  - Verification-artefact *integrity* and *provenance* (Table A-9 objectives) are directly delivered by Layers 1 + 4 + 5.
  - Test-result bundles (DT-FEM-01, or ML_BENCH-01 for any ML component on DAL-C or lower) provide cryptographic Software Verification Results.
- **[GAP]** DO-178C requires specific data items (`Plan for Software Aspects of Certification`, `Software Development Plan`, and similar) — design documents, not computational outputs. Same gap pattern as 510(k) / IEC 62304. Closable by `DOC-HASH-01` (§10).
- **Source:** [RTCA DO-178C overview](https://www.rtca.org/wp-content/uploads/2020/08/do-178c.pdf) **[CITATION UNVERIFIED — exact wording of Table A-7 objective #9 taken from secondary source, not from the standard itself]**

---

## 4. Science

### 4.1 NIH Data Management and Sharing Policy — NOT-OD-21-013 (effective 2023-01-25)

- **Citation:** `NOT-OD-21-013` (Final Policy); supplemental `NOT-OD-21-014` (Elements of a DMS Plan); `NOT-OD-21-015` (Allowable Costs); `NOT-OD-22-213` (Protecting Privacy). Updated elements: `NOT-OD-26-046`.
- **Mandates:** All NIH grant applications resulting in scientific data generation must include a Data Management and Sharing Plan (DMSP) covering data types, tools for accessing data, standards used, preservation and access, access-control considerations, and oversight of compliance. The approved DMSP becomes a term of the award.
- **MetaGenesis coverage:**
  - "Data types" and "standards used" — bundle metadata carries both.
  - "Preservation" — SHA-256 integrity plus Ed25519 signature plus NIST Beacon temporal commitment provide long-term tamper-evidence.
  - `DATA-PIPE-01` (data quality certificate) is the closest existing claim.
- **[GAP]** NIH policy requires ongoing *sharing* via approved repositories (dbGaP, NIH-supported generalist repositories) — MetaGenesis bundles are portable but not a repository.
- **Source:** [NOT-OD-21-013](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-21-013.html) · [NOT-OD-23-053 reminder](https://grants.nih.gov/grants/guide/notice-files/NOT-OD-23-053.html)

### 4.2 Plan S — cOAlition S Open Access Principles

- **Citation:** cOAlition S "Principles and Implementation" (2018, revised guidance 2019 and after); 10 Principles. Most relevant: **`Principle 5`** (funders monitor compliance and sanction non-compliance) and **`Principle 8`** (funders support open-access infrastructure including FAIR data).
- **Mandates:** All publications resulting from cOAlition-S-funded research must be immediately open access (CC BY), deposited in a compliant repository, with FAIR metadata and persistent identifiers.
- **MetaGenesis coverage:**
  - A MetaGenesis bundle is a FAIR-ready data artefact: Findable (hash = persistent identifier), Accessible (offline), Interoperable (JSON plus SHA-256), Reusable (reproduction command recorded in the claim).
  - Zenodo DOI infrastructure (minted: `10.5281/zenodo.19521091`) plus `CITATION.cff` align directly with Plan S repository criteria.
- **[GAP]** Plan S requires CC BY licensing — this is an editorial choice, not a protocol constraint. Out of scope.
- **Source:** [Plan S — Principles and Implementation](https://www.coalition-s.org/addendum-to-the-coalition-s-guidance-on-the-implementation-of-plan-s/principles-and-implementation/)

### 4.3 ALLEA European Code of Conduct for Research Integrity (Revised 2023)

- **Citation:** ALLEA European Code of Conduct, 2023 Revised Edition, **Section 2 — Good Research Practices** (sub-items on data management, reproducibility, transparency). Section 3 addresses violations.
- **Mandates:** Researchers must "handle research data and samples appropriately, including secure storage, safe retrieval, and clear referencing, in accordance with the FAIR principles" and support reproducibility through transparency of methods and data.
- **MetaGenesis coverage:**
  - "Secure storage, safe retrieval, clear referencing" — Layers 1 + 4 + 5.
  - "Reproducibility through transparency" — every claim has a one-line `reproduction` command recorded in `reports/scientific_claim_index.md`.
  - 21 of 41 claims use real data (51.2% real ratio per `system_manifest.json`).
- **[GAP]** ALLEA also addresses authorship, peer review, and conflicts of interest — purely human-editorial concerns. Out of scope.
- **Source:** [ALLEA European Code of Conduct 2023](https://allea.org/code-of-conduct/) · [Horizon Europe — Code PDF](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/horizon/guidance/european-code-of-conduct-for-research-integrity_horizon_en.pdf)

---

## 5. AI + Cryptography

### 5.1 EU AI Act — Regulation (EU) 2024/1689

- **Citation:** Key articles for high-risk systems:
  - **`Article 10`** — Data and data governance.
  - **`Article 12`** — Record-keeping (automated logging).
  - `Article 14` — Human oversight.
  - **`Article 15`** — Accuracy, robustness, cybersecurity.
  - **`Article 26(6)`** — 6-month minimum log retention.
  - **`Article 72`** — Post-market monitoring.
  - `Article 79(1)` — Risk-presenting situations (triggering log relevance under Art. 12).
- **Mandates:**
  - `Art. 12(1)` — "High-risk AI systems shall technically allow for the automatic recording of events (logs) over the lifetime of the system." Manual logging does not satisfy the clause.
  - `Art. 12(2)` — Logging must enable identification of risk situations, facilitate post-market monitoring, and support operation monitoring.
  - `Art. 15(1)` — Accuracy, robustness, and cybersecurity maintained throughout lifecycle.
  - `Art. 15(5)` — Resilience "against attempts by unauthorised third parties to alter their use, outputs or performance by exploiting system vulnerabilities."
- **MetaGenesis coverage:**
  - `Art. 12` — the MetaGenesis bundle is an automated record. Layer 3 step chain is automatic (hashes computed in-code); Layer 5 temporal commitment fetches the NIST Beacon automatically. No manual logging required.
  - `Art. 15(5)` — Layers 1 + 4 + 5 are the cryptographic answer to "resilience against output alteration." ML_BENCH-01/02/03 certify accuracy; drift detection (DRIFT-01, AGENT-DRIFT-01) certifies lifecycle stability.
  - `Art. 26(6)` 6-month retention is trivial — bundles are file artefacts that can be stored indefinitely.
- **[GAP]** `Art. 10` — data governance. MetaGenesis verifies *outputs*, not *training-data lineage*. We cannot prove "training data is free of errors" or "bias was detected and mitigated." This is documented as `SCOPE_001`.
- **[GAP]** `Art. 14` — human oversight. Out of scope entirely; human oversight cannot be automated. MetaGenesis supports human reviewers; it does not replace them.
- **Enforcement:** Full application for high-risk systems on **2 August 2026**.
- **Source:** [EU AI Act Article 12 Record-keeping](https://artificialintelligenceact.eu/article/12/) · [Article 15 Accuracy/Robustness/Cybersecurity](https://artificialintelligenceact.eu/article/15/) · [Article 10 Data Governance](https://artificialintelligenceact.eu/article/10/) · [EUR-Lex — Regulation 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)

### 5.2 NIST FIPS 203 / 204 / 205 — Post-Quantum Cryptography (effective 2024-08-14)

- **Citation:**
  - `FIPS 203` — Module-Lattice-Based Key-Encapsulation Mechanism Standard (**ML-KEM**, based on CRYSTALS-Kyber). Parameter sets: ML-KEM-512, ML-KEM-768, ML-KEM-1024.
  - `FIPS 204` — Module-Lattice-Based Digital Signature Standard (**ML-DSA**, based on CRYSTALS-Dilithium).
  - `FIPS 205` — Stateless Hash-Based Digital Signature Standard (**SLH-DSA**, based on SPHINCS+). Primary backup if ML-DSA is broken.
- **Mandates:** These are approved FIPS for federal use against quantum-era adversaries. NIST CNSA 2.0 target: transition cryptographic algorithms to quantum-safe by 2030 for National Security Systems, with broader federal transition before the end of the decade.
- **MetaGenesis coverage:**
  - Current signing layer (Layer 4) uses **Ed25519** — classical EdDSA, **not quantum-safe**. Ed25519 is fit for 2026 but will need to migrate.
- **[GAP]** **Post-quantum migration path is not yet implemented.** Adding `scripts/mg_mldsa.py` (FIPS 204 ML-DSA) as a dual-signature option alongside Ed25519 would close this gap. Pure-Python reference implementations exist; the precedent set by `scripts/mg_ed25519.py` (RFC 8032 validation via test vectors) can be replicated for ML-DSA using NIST ACVP test vectors.

  **Honest positioning.** This is a **multi-year migration item**, not a pending v1.0.0-rc1 deliverable. Ed25519 remains a responsible choice for 2026 computational-claim signatures because the NSS transition deadline is 2030 and broader federal transition runs to the end of the decade. MetaGenesis should ship dual-signing (Ed25519 ‖ ML-DSA) well before 2030; a target of 2027–2028 is appropriate and is documented here as a roadmap item, not a commitment.
- **Source:** [NIST — FIPS 203/204/205 Finalized (Aug 2024)](https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards) · [FIPS 203 final PDF](https://csrc.nist.gov/pubs/fips/203/final) · [FIPS 204 final PDF](https://csrc.nist.gov/pubs/fips/204/final) · [FIPS 205 final PDF](https://csrc.nist.gov/pubs/fips/205/final)

### 5.3 NIST AI RMF 1.0 — Artificial Intelligence Risk Management Framework

- **Citation:** `NIST AI 100-1, AI Risk Management Framework 1.0` (released 2023-01-26). Four functions: Govern, Map, Measure, Manage. Companion Playbook with sub-category actions.
- **Mandates:**
  - **MEASURE** — "quantitative, qualitative, or mixed-method tools, techniques, and methodologies to analyze, assess, benchmark, and monitor AI risk and related impacts."
  - **MANAGE** — risk prioritisation, response, incident detection.
- **MetaGenesis coverage:**
  - MEASURE 2.5 (accuracy) — ML_BENCH-01/02/03.
  - MEASURE 2.7 (security and resilience) — Layers 4 + 5 deliver cryptographic integrity under tampering attacks, proved by CERT-07 through CERT-12.
  - MEASURE 2.9 (model explainability) — out of scope.
  - MANAGE 4 (incident detection / drift) — DRIFT-01, AGENT-DRIFT-01.
- **[GAP]** NIST AI RMF is voluntary and principles-based; not a hard requirement. GOVERN and MAP functions are primarily organisational — out of scope.
- **Source:** [NIST AI RMF 1.0 PDF](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) · [NIST AI RMF Playbook](https://airc.nist.gov/airmf-resources/playbook/)

### 5.4 SOC 2 — AICPA Trust Services Criteria

- **Citation:** AICPA SOC 2 Common Criteria (2017 TSC framework, 2022 revision):
  - **`CC7.2`** — Monitor system components for anomalies.
  - **`CC7.3`** — Evaluate security events.
  - **`CC8.1`** — Authorize, design, develop, and implement changes.
- **Mandates:**
  - `CC7.2` — infrastructure monitoring for performance degradation, capacity thresholds, configuration drift, and unauthorized changes.
  - `CC7.3` — evaluation and response to security events.
  - `CC8.1` — formal change management (documentation, risk assessment, testing, approval, rollback).
- **MetaGenesis coverage:**
  - `CC7.2` — "configuration drift" and "unauthorized changes" → DRIFT-01, AGENT-DRIFT-01, Layer 1 integrity.
  - `CC8.1` — "documentation, approval, testing" for changes → Layer 4 Ed25519 signature is cryptographic approval; Layer 5 temporal commitment is the immutable change log.
- **[GAP]** Criteria CC1–CC4 (control environment, communication, governance) are organisational — out of scope.
- **Source:** [AICPA Trust Services Criteria](https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022)

---

## 6. Climate / ESG

### 6.1 IFRS S1 / S2 + EU CSRD — Combined Sustainability Disclosure

- **Citation (IFRS):** `IFRS S1` (General Requirements for Disclosure of Sustainability-related Financial Information) plus `IFRS S2` (Climate-related Disclosures), both issued by ISSB June 2023; effective for annual reporting periods beginning on or after 2024-01-01. S2 requires Scope 1 + 2 greenhouse-gas emissions disclosure from day one; Scope 3 has a one-year transition relief.
- **Citation (CSRD):** `Directive (EU) 2022/2464` amending the Accounting Directive. Assurance requirements in **`Article 34a`** (audit of sustainability reporting). European Sustainability Reporting Standards (**ESRS**) are the companion technical standard. CEAOB guidelines on limited assurance (September 2024) set auditor expectations.
- **Mandates:**
  - IFRS S1 / S2 — "consistent, complete, comparable and verifiable" sustainability-related financial information. Climate metrics must be disclosed on the same reporting basis as financial statements.
  - CSRD Art. 34a — in-scope companies must obtain **limited assurance** from a statutory auditor (or, where member states permit, an Independent Assurance Services Provider) covering compliance with ESRS, the materiality-assessment process, EU Taxonomy Regulation alignment, and digital tagging. The Commission adopts limited-assurance standards before 1 October 2026; reasonable-assurance standards by 1 October 2028 contingent on feasibility.
- **MetaGenesis coverage:**
  - "Verifiable" is the exact property Layers 1–5 deliver. A carbon-accounting model's output is packaged as a bundle; an external assurer verifies offline.
  - "Digital tagging" integrity — Layers 1 + 4.
  - "Consistent" data values — Layers 1 + 3.
  - Auditor work is made dramatically cheaper: instead of recomputing every ESG number, the auditor runs `mg verify --pack esg_bundle.zip` per disclosure and gets PASS / FAIL.
- **[GAP]** No existing dedicated claim. A planned `CLIMATE-01` (GHG accounting model certificate) or `ESG-01` claim would follow the same 6-step lifecycle as FINRISK-01. See §10.
- **[GAP]** Methodology appropriateness — is the carbon model defensible? — is judgemental. MetaGenesis proves the model produced exactly this number on exactly this data; it does not endorse the model.
- **[GAP]** Materiality-assessment process is inherently judgemental; CSRD requires documentation of the *process*, not just the *outputs*.
- **Source:** [IFRS S2 — Climate-related Disclosures](https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/) · [IFRS S1](https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s1-general-requirements/) · [EUR-Lex — Directive (EU) 2022/2464 (CSRD)](https://eur-lex.europa.eu/eli/dir/2022/2464/oj) · [CEAOB Limited Assurance Guidelines (Sep 2024)](https://finance.ec.europa.eu/document/download/8ac2df18-2ae1-4bc7-9d87-a4a740e48f5e_en?filename=240930-ceaob-guidelines-limited-assurance-sustainability-reporting_en.pdf)

---

## 7. Physical Anchor Principle — Scope Reminder (SCOPE_001)

Regulatory citations frequently conflate two distinct properties. MetaGenesis keeps them separate:

- **Tamper-evident provenance** — "was this bundle modified after production?" — is delivered by ALL 20 claims via Layers 1–5.
- **Physical anchor traceability** — "does this number agree with physical reality?" — is delivered ONLY by the 10 anchored claims (PHYS-01, PHYS-02, MTR-1..MTR-6, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01).

Scope is documented in `reports/known_faults.yaml :: SCOPE_001`. Agents, regulators, and writers MUST NOT claim physical-anchor traceability for ML_BENCH-01/02/03, FINRISK-01, PHARMA-01, SYSID-01, DT-SENSOR-01, DATA-PIPE-01, or AGENT-DRIFT-01. These seven claims are tamper-evident only.

This matters for regulations that require uncertainty budgets (NASA-STD-7009B CAS factors 3–5, EU MDR `§17.1` "state of the art"): anchored claims strengthen those factors; unanchored claims do not.

---

## 8. SI 2019 Exact Constants — Expansion Opportunity

MetaGenesis currently anchors to two SI 2019 exact constants:

- `kB = 1.380649 × 10⁻²³ J/K` (Boltzmann constant, PHYS-01 — rel_err ≤ 1e-9)
- `NA = 6.02214076 × 10²³ mol⁻¹` (Avogadro constant, PHYS-02 — rel_err ≤ 1e-8)

Five additional SI 2019 exact constants could anchor future claims:

- `h = 6.62607015 × 10⁻³⁴ J·s` (Planck constant) — quantum computing output verification.
- `e = 1.602176634 × 10⁻¹⁹ C` (elementary charge) — semiconductor device simulation.
- `c = 299 792 458 m/s` (speed of light) — electromagnetic simulation, GPS timing.
- `Kcd = 683 lm/W` (luminous efficacy) — photometric calibration.
- `Δν_Cs = 9 192 631 770 Hz` (cesium hyperfine frequency) — precision timing, atomic-clock calibration.

These are opportunities for future milestones. Any new claim requires the mandatory 6-step lifecycle (see `docs/HOW_TO_ADD_CLAIM.md`) and is not in scope for v3.1.0.

---

## 9. Honest Boundaries — What MetaGenesis Cannot Do (Today)

The 24 `[GAP]` flags above cluster into three honest-scope categories. These are structural limits of a verification protocol, not engineering debt.

### 9.1 Training-data lineage

**In scope for:** EU AI Act Art. 10 (data governance); portions of NIH DMSP; portions of FDA AI Credibility Framework Step 1 (define the question of interest).

MetaGenesis verifies *outputs* — "this exact model, on this exact dataset, at this exact time, produced this exact number." It does not trace each training-data row back to its raw source, does not verify that data collection was consent-compliant, and does not prove that biases in the training data were detected or mitigated. A bundle can carry dataset hashes (via `DATA-PIPE-01`), which proves the exact dataset was used; it cannot prove where each row originated, or that the dataset is ethically sound.

This is a structural limit of an output-verification protocol. Closing it requires a data-provenance system (e.g. C2PA-style lineage tracing, permissioned data registries, or formal data-sheet documentation). MetaGenesis composes with these systems; it does not replace them.

**Status:** Out of scope for v1.0.0-rc1 and v3.1.0. Not on the roadmap.

### 9.2 Human oversight, conceptual soundness, and organisational governance

**In scope for:** EU AI Act Art. 14 (human oversight); SR 11-7 Section V (conceptual soundness review); SOC 2 CC1–CC4 (control environment, communication, governance); ISO 26262 HARA and FMEDA; NASA-STD-7009B CAS factors 6–8 (Use History, M&S Management, People Qualifications); AS9100D design-review minutes; CSRD materiality-assessment process; NIST AI RMF GOVERN and MAP functions.

These are process frameworks, not automatable controls. A model risk manager reading a MetaGenesis bundle still needs to exercise judgement about whether the model's conceptual approach is defensible for the use case. An ISO 26262 HARA analyst still needs to reason about hazard scenarios that the code does not know about. A NASA M&S decision review still needs people with relevant qualifications. These cannot be automated; no verification protocol would change this.

MetaGenesis reduces the blast radius of human error (a signed bundle cannot be altered after review) and enables cheap independent second-opinion review (anyone can run `mg verify` offline). It does not — and should not — automate the judgement itself.

**Status:** Out of scope permanently. Documented honestly as process-framework coverage.

### 9.3 Design-document certification

**In scope for:** FDA 510(k) (SRS, SDS, architecture, risk-management file); IEC 62304 Clauses 5.1 / 5.3 / 5.4 (planning, architecture, detailed design); DO-178C Software Life Cycle Data (Plan for Software Aspects of Certification, Software Development Plan, and similar); AS9100D design-review minutes and design-changes log.

Design documents are markdown, PDF, or Word files — not execution traces. MetaGenesis currently certifies computational outputs (numbers produced by running code); it does not certify text documents authored by humans.

This gap is **close-able** by a thin `DOC-HASH-01` claim that packages any file with SHA-256 integrity plus Ed25519 signature plus NIST Beacon temporal commitment — the same Layer 1 + 4 + 5 stack, adapted to arbitrary file payloads. A single claim template would unlock design-document provenance for 510(k), IEC 62304, DO-178C, and AS9100D simultaneously. This is one of the five planned future claims (§10).

**Status:** Out of scope for v1.0.0-rc1 and v3.1.0 (docs-only milestone). Planned but not committed.

---

## 10. Future Roadmap — Planned Claim Additions (Informational Only)

The five future claims below were surfaced by the REGULATIONS research as high-leverage additions. **None are implemented in v1.0.0-rc1, and none are in scope for v3.1.0.** This section is informational; it does not commit to delivery dates. Each future claim requires the mandatory 6-step lifecycle documented in `CLAUDE.md`.

| Planned claim ID | Maps to regulation | What it would add | Close date (planning only) |
|---|---|---|---|
| **`AUTO-OTA-01`** | UN R156 SUMS (Software Update Management System) | Bundle ≡ update package. Strongest natural fit in the regulatory landscape; the "package / approve / deliver / verify / record" verbs in UN R156 map one-to-one onto the MetaGenesis bundle lifecycle. | Not committed |
| **`CLIMATE-01`** | IFRS S2 / CSRD Art. 34a | GHG accounting model certificate. Unlocks the sustainability-assurance market ahead of the CSRD limited-assurance deadline (1 October 2026 Commission adoption; reasonable assurance by 1 October 2028). | Not committed |
| **`TRADING-01`** | MiFID II Art. 17(2) 2nd subpara | Order, cancellation, and quotation log certificate. Financial services is the highest-margin vertical. | Not committed |
| **`EDC-01`** | ISO 14155 Clause 7.8.3 | Electronic Data Capture validation certificate for clinical trials. Pharma GCP fit; complements PHARMA-01. | Not committed |
| **`DOC-HASH-01`** | FDA 510(k) + IEC 62304 + DO-178C + AS9100D | Design-document hash-plus-signature claim. Small effort; unlocks design-document provenance across four regulations simultaneously. See §9.3. | Not committed |

**Agent / writer note:** Do not describe these as if they exist. "Planned," "would add," "if implemented," "future roadmap" — these are the correct framings. Anyone reading this document is reading the state of v1.0.0-rc1; the five future claims are NOT part of v1.0.0-rc1.

---

## 11. Recommendations

These recommendations are prioritised by regulatory leverage per unit engineering effort.

1. **Immediate (Level 2 agent work):** Document how existing bundles already satisfy specific article requirements (EU AI Act Art. 12, 21 CFR Part 11 §11.10(e), NASA-STD-7009B CAS 1–5, UN R156 SUMS lifecycle). This is evidence, not code — the bundles already demonstrate the properties the regulations require. The only work is explanatory.
2. **Near-term (v3.1.1 or v3.2.0 candidate):** `DOC-HASH-01` design-document claim (§10). Smallest engineering footprint, largest regulatory surface — closes gaps in 510(k), IEC 62304, DO-178C, and AS9100D in one template.
3. **Near-term:** `AUTO-OTA-01` (§10). The regulatory fit to UN R156 is direct enough that the claim template is close to trivial; the business value — entry into the automotive OTA compliance market — is substantial.
4. **Medium-term:** `CLIMATE-01` (§10) ahead of the CSRD limited-assurance adoption deadline (1 October 2026). The sustainability-assurance market is opening; a verifiable carbon-accounting bundle is a distinctive offering.
5. **Medium-term:** `TRADING-01` (§10). Financial services is the highest-margin vertical per the commercial plan. MiFID II Art. 17(2) 2nd subpara is already a direct fit.
6. **Long-term (by 2028):** Post-quantum migration — add `scripts/mg_mldsa.py` (FIPS 204 ML-DSA) as a dual-signature option alongside Ed25519. NSS transition deadline is 2030; MetaGenesis should ship dual-signing well before that, with a reasonable target of 2027–2028. Pure-Python reference ML-DSA implementations plus NIST ACVP test vectors make this tractable.
7. **Long-term:** `EDC-01` (§10) — pharma GCP fit; complements PHARMA-01 once there is a pilot sponsor.
8. **Exploratory (future milestones):** Planck, elementary-charge, speed-of-light anchors (§8) for quantum-computing, semiconductor, and electromagnetic-simulation verification domains.

---

## 12. Confidence Assessment

| Section | Confidence | Notes |
|---|---|---|
| §1 Financial | HIGH | All primary sources from EUR-Lex, Federal Reserve, eCFR, BIS |
| §2 Pharma + Medical | HIGH | eCFR plus FDA plus ISO authoritative; MDCG 2019-11 Rev.1 confirmed current |
| §3 Automotive + Aerospace | MEDIUM | ISO 26262 sub-clause numbering verified via secondary sources; NASA-STD-7009B primary-source verified; DO-178C Table A-7 objective #9 carries the `[CITATION UNVERIFIED]` flag verbatim |
| §4 Science | HIGH | NIH grants.nih.gov, cOAlition S, ALLEA primary sources |
| §5 AI + Cryptography | HIGH | NIST CSRC plus NVL PUBS plus official AI Act text |
| §6 Climate / ESG | HIGH | IFRS Foundation plus EUR-Lex plus CEAOB primary sources |
| §9 Honest boundaries | HIGH | Explicitly scoped; not aspirational |
| §10 Future roadmap | HIGH | Planning only; no implementation claims |

---

*Gap analysis assembled 2026-04-16 for MetaGenesis Core v3.1.0 Documentation Deep Pass (Phase 31 — RG-01..04). Primary citations prioritised in this order: EUR-Lex → ecfr.gov → NIST CSRC → IFRS Foundation → ISO.org → UNECE → AICPA → Federal Reserve → grants.nih.gov → cOAlition S → ALLEA. This document assesses gaps, not plans; new claims require the full 6-step lifecycle documented in `docs/HOW_TO_ADD_CLAIM.md` and must go through GSD.*
