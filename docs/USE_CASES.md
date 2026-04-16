# Use Cases — MetaGenesis Core

**Version:** v1.0.0-rc1 | **Claims:** 20 | **Tests:** 2407 | **Layers:** 5 | **Mode:** offline

---

## What this document is

MetaGenesis Core is a verification protocol layer for computational claims. This document maps the protocol onto 14 domains where a numerical result must survive scrutiny from a party who does not have access to the original compute environment, data, or model. The protocol ships 20 active claim templates in v1.0.0-rc1 — 10 anchored to a physical constant (SI 2019 exact or NIST measured) and 10 tamper-evident only — and five independent verification layers (SHA-256 integrity, semantic verification, 4-step cryptographic chain, Ed25519/HMAC signing, NIST Beacon temporal commitment). Every bundle is verified offline with `python scripts/mg.py verify --pack bundle/` → PASS or FAIL in under 60 seconds.

Each domain section below follows the same structure: the computation, a real named incident showing what happens when verification fails, the cost equation, the specific claim IDs and layers that apply, the 3-step integration path, and at least one exact regulatory citation.

---

> **Honest-scope callout**
>
> - **SCOPE_001 — physical anchors apply to 10 of 20 claims only.** PHYS-01/02 (SI 2019 exact), MTR-1/2/3/4/5/6 (NIST measured), DT-FEM-01, DRIFT-01, and DT-CALIB-LOOP-01 (derived from MTR-1) are the only claims that claim traceability to a physical constant. ML, pharma, finance, system ID, IoT sensor, data pipeline, and agent-drift claims are **tamper-evident only** — they prove that the number produced was the number submitted, not that the number agrees with a physical reality.
> - **Governance vs verification.** Three of the 22 cited incidents (Theranos, Challenger, LIBOR) are governance or fraud failures at root. MetaGenesis would have **bounded the damage** — by making concealment cryptographically expensive, binding test results to specific individuals or devices, and making override trails signable — but would **not have prevented** criminal intent. This distinction is preserved throughout.
> - **Composability — addition, not replacement.** MetaGenesis sits on top of Docker, MLflow, DVC, git, Nextflow, MATLAB, ANSYS, Coq, Lean, and every other tool you already use. The frame is always "X + MetaGenesis = verifiable X," never "MetaGenesis vs X."
> - **One `[CITATION UNVERIFIED]` flag** is preserved in this document: DO-178C Table A-7 objective #9 exact wording was taken from a secondary source. Carried forward verbatim from `.planning/research/REGULATIONS.md`.

---

## 1. ML / AI benchmarks

**The computation.** A model produces predictions on a held-out test set and a paper, a product-launch deck, or a leaderboard entry reports an accuracy, RMSE, MAPE, or F1 number. Downstream consumers — reviewers, product managers, regulators, users — depend on that number being an honest characterization of the model's behavior on data it has not seen. Reproducing it requires the original weights, the original test split, and often the original hardware.

**What happens when verification fails.** Kapoor and Narayanan (Princeton, 2023) surveyed ML-based scientific claims across 17 fields and documented 294 peer-reviewed papers affected by data-leakage pitfalls, including 8 distinct leakage types such as temporal leakage and train/test contamination. Once leakage was corrected in their deeper civil-war-prediction study, the apparent ML advantage over classical statistics disappeared entirely. Primary source: Kapoor S., Narayanan A., "Leakage and the reproducibility crisis in machine-learning-based science," *Patterns* 4(9), August 2023, DOI 10.1016/j.patter.2023.100804 (PMID 37720327). A second named incident in the same domain is Zillow Offers (2021), where an algorithmic home-pricing model drove approximately USD 569 million in inventory write-downs and a 25% workforce reduction before the iBuying line was shut down. Primary source: Zillow Group Q3 2021 shareholder letter and 10-Q — https://www.gsb.stanford.edu/insights/flip-flop-why-zillows-algorithmic-home-buying-venture-imploded.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Re-run training: compute access + GPU time + data access + environment rebuild | $299 per bundle |
| Weeks to months of reviewer effort | ~60 seconds offline verification |
| Residual risk: inflated SOTA claims go uncaught at submission | Residual risk: bundle proves output provenance only, not training-data lineage (EU AI Act Art. 10 — out of scope) |

**Unique MetaGenesis properties for this domain.** ML_BENCH-01 (accuracy certificate, Δacc ≤ 0.02), ML_BENCH-02 (regression RMSE certificate), and ML_BENCH-03 (time-series MAPE certificate) cover the three most common metric families. DRIFT-01 tracks divergence of a live model from a verified baseline. AGENT-DRIFT-01 monitors the evaluator's own quality. All four are **tamper-evident only** — no physical anchor applies (per SCOPE_001). The relevant layers are Layer 1 (the test-set file is SHA-256 fingerprinted), Layer 2 (semantic verification catches an attacker who strips the predictions file and recomputes hashes — proven by `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`), Layer 3 (the 4-step execution trace records seed → dataset hash → metric computation → threshold check), Layer 4 (Ed25519 proves which team produced the bundle), and Layer 5 (NIST Beacon commitment prevents backdating a bundle to pre-date a contest cutoff).

**Integration — 3 steps.**
1. Prepare a CSV with `y_true` / `y_pred` columns (predictions from the frozen model on the frozen test set).
2. `python scripts/mg_client.py --domain ml --data params.json --output my_bundle/` where `params.json` sets `claimed_accuracy`, `accuracy_tolerance`, and points to the predictions path.
3. Verifier runs `python scripts/mg.py verify --pack my_bundle/` → PASS or FAIL in under 60 seconds, no model or data access required.

**Regulatory requirement.** EU AI Act, Regulation (EU) 2024/1689, **Article 15(1)** (accuracy, robustness, cybersecurity maintained throughout lifecycle) and **Article 15(5)** (resilience "against attempts by unauthorised third parties to alter their use, outputs or performance"). Full application for high-risk systems on 2 August 2026. Source: https://artificialintelligenceact.eu/article/15/. Also applicable: NIST AI RMF 1.0 MEASURE 2.5 / 2.7 — https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf.

---

## 2. Pharma and biotech — ADMET and computational submissions

**The computation.** A cheminformatics or ADMET model predicts properties of a drug candidate — solubility (logS), permeability (logP), binding affinity (pIC50), bioavailability, toxicity — and those predictions feed IND filings, go / no-go decisions on compound series, and ultimately clinical-trial enrollment. Regulators rely on the numerical submissions; peer companies and CROs rely on handoff bundles.

**What happens when verification fails.** The Duke University Potti/Nevins genomic-signatures case (2010–2015) enrolled more than 100 advanced-cancer patients in three clinical trials on the basis of gene-expression predictors of chemotherapy response. Independent biostatisticians Keith Baggerly and Kevin Coombes traced the underlying data manipulations (row/column swaps, label reversals). Trials were halted in 2010; the US Office of Research Integrity formally found misconduct on 9 November 2015. As of 2024, 11 publications have been retracted. Primary source: ORI Case Summary, *Federal Register* Vol. 80 No. 218 — https://retractionwatch.com/2015/11/07/its-official-anil-potti-faked-data-say-feds/. Also in this domain: Takeda Actos pioglitazone (2010–2015) — ~10,000 product-liability suits consolidated into MDL; USD 2.4 billion settlement in 2015; internal safety-signal timelines became the central litigation question. Primary source: FDA Drug Safety Communication, 15 June 2011 — https://www.fda.gov/drugs/drug-safety-and-availability.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Proprietary audit-trail infrastructure; nine-figure IND preparation budgets | $299 per bundle |
| Months of data-management reconstruction under litigation | ~60 seconds offline verification |

**Unique MetaGenesis properties for this domain.** PHARMA-01 (ADMET prediction certificate, `abs(predicted_value − claimed_value) ≤ tolerance`) is the primary claim. This is **tamper-evident only** — no physical anchor applies (per SCOPE_001); the property being certified is "the submitted prediction and its inputs survived the packaging process intact," not "the prediction agrees with measured wet-lab values." Layer 3 (step chain) hashes every per-sample input so silent label reversals — the exact Potti/Nevins failure mode — cannot occur without invalidating `trace_root_hash`. Layer 4 (Ed25519) binds each artifact to a specific signer. Layer 5 (temporal commitment) makes "when did the sponsor know" a cryptographic question rather than a discovery-litigation question.

**Integration — 3 steps.**
1. Prepare a JSON input with `property_name` (e.g. `"solubility"`), `claimed_value`, and `tolerance`.
2. `python scripts/mg_client.py --domain pharma --data inputs.json --output pharma_bundle/`.
3. FDA inspector or partner CRO runs `python scripts/mg.py verify --pack pharma_bundle/` → PASS or FAIL, offline, no model access required.

**Regulatory requirement.** FDA 21 CFR § 11.10(e): "secure, computer-generated, time-stamped audit trails to independently record the date and time of operator entries and actions that create, modify, or delete electronic records. Record changes shall not obscure previously recorded information." Source: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11/subpart-B/section-11.10. Also applicable: FDA Draft Guidance January 2025, 7-step Credibility Assessment Framework for AI models in drug submissions — https://www.fda.gov/news-events/press-announcements/fda-proposes-framework-advance-credibility-ai-models-used-drug-and-biological-product-submissions.

---

## 3. Medical devices — software and diagnostic results

**The computation.** A medical-device software function computes a radiation dose, a defibrillator-therapy decision, a blood-test result, or a diagnostic classification. The number or decision drives clinical action within seconds to minutes. Device firmware, hardware state, patient identifier, and procedure parameters are all load-bearing inputs.

**What happens when verification fails.** The Therac-25 radiation-therapy machine (1985–1987) overdosed patients on at least six occasions due to a race-condition software bug combined with removal of hardware interlocks present in the Therac-20. At least three patient deaths are attributed to the overdoses. FDA issued a Class I recall on 6 February 1987. Post-incident reconstruction at East Texas Cancer Center took weeks because machine logs were ambiguous. Primary source: Leveson N., Turner C., "An Investigation of the Therac-25 Accidents," *IEEE Computer* 26(7):18–41, July 1993 — https://www.cse.msu.edu/~cse470/Public/Handouts/Therac/Therac_1.html. Also in this domain: Guidant implantable cardioverter-defibrillators (2002–2005) — six confirmed failure-related deaths, USD 296 million criminal settlement in November 2009. Primary source: DOJ press release, US v. Guidant LLC, USDC D. Minnesota, 5 February 2010 — https://www.justice.gov/archives/opa/pr/medical-device-manufacturer-guidant-charged-failure-report-defibrillator-safety-problems-fda. The Theranos case (2015–2022, Elizabeth Holmes sentenced to 135 months federal prison, restitution USD 452 million) cross-cuts this domain; **it is primarily a fraud case, not a pure verification-gap case — MetaGenesis would have bounded the damage by binding each patient result to a specific device and method, not prevented criminal intent** (primary source: US v. Holmes, 5:18-cr-00258-EJD — https://www.justice.gov/usao-ndca/us-v-elizabeth-holmes-et-al).

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Post-incident log reconstruction: weeks | ~60 seconds offline verification |
| 510(k) or CE-mark V&V evidence: bespoke audit artifacts | $299 per bundle |

**Unique MetaGenesis properties for this domain.** DT-SENSOR-01 (schema + range + temporal integrity for device telemetry) is the nearest existing claim; it is **tamper-evident only** (per SCOPE_001). Device firmware bundles can be signed through the same Layer 4 pathway that signs any other bundle. Layer 1 (SHA-256) plus Layer 4 (Ed25519) cryptographically binds each delivered dose or decision to (a) the firmware version, (b) the configured mode, (c) the patient/plan identifier. Layer 5 (temporal commitment) makes concealment — the Guidant failure mode — cryptographically expensive.

**Integration — 3 steps.**
1. Log the sensor / telemetry stream alongside firmware identifiers and patient/procedure metadata into a JSON artifact.
2. `python scripts/mg_client.py --domain digital_twin --data telemetry.json --output device_bundle/` (the `digital_twin` flag packages sensor-style claims; a dedicated medical-device template is a future addition per SUMMARY §10).
3. FDA inspector or notified body runs `python scripts/mg.py verify --pack device_bundle/` → PASS or FAIL.

**Regulatory requirement.** FDA Guidance "Content of Premarket Submissions for Device Software Functions" (final 2023-06-14) — requires V&V testing evidence, version history, and unresolved-anomalies documentation as part of Enhanced Documentation for devices where failure could cause a hazardous situation. Source: https://www.fda.gov/regulatory-information/search-fda-guidance-documents/content-premarket-submissions-device-software-functions. Also: **IEC 62304:2006+A1:2015, Clause 5.8** (verified, versioned, anomaly-tracked releases with reliable delivery) — https://www.iso.org/standard/38421.html. Also: **EU MDR Regulation (EU) 2017/745, Annex I Chapter II §17.1** (software developed in accordance with the state of the art, including verification and validation and information security) — https://eur-lex.europa.eu/eli/reg/2017/745/oj/eng.

---

## 4. Materials science — calibration and qualification

**The computation.** A materials laboratory or simulation team calibrates a property (Young's modulus, thermal conductivity, contact resistance) against a reference specimen or a physical constant. The calibrated value flows downstream into FEM models, component qualifications, and supplier acceptance criteria. A simulation run that declares E = 70 GPa for aluminum is building on a number that can be checked, in principle, against any of thousands of independent laboratory measurements worldwide.

**What happens when verification fails.** Jan Hendrik Schön (Bell Labs, 1998–2002) published approximately 90 papers in *Science*, *Nature*, and *Physical Review* on superconductivity in organic materials and molecular transistors. Independent physicists noticed that measurement curves from ostensibly different samples and different experiments were identical down to random-noise bumps. The Beasley Committee inquiry report (26 September 2002) found misconduct in at least 16 of 24 investigated cases. More than 21 papers were retracted across *Science* (8), *PRL/PRB* (6), *Applied Physics Letters* (4), and *Nature* (7); the subfield of organic/molecular electronics was set back by years of wasted follow-on research. Primary source: Lucent/Bell Labs Beasley Committee Report, Sep 2002 — https://www.aps.org/apsnews/2022/08/september-2002-schon-scandal-report.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Peer replication: months, new specimens, new apparatus | ~60 seconds offline verification |
| Supplier-partner qualification disputes resolved in email | $299 per bundle, one-line PASS/FAIL |

**Unique MetaGenesis properties for this domain.** MTR-1 through MTR-6 are the reference anchored claims — MTR-1 (E = 70 GPa Al), MTR-2 (thermal paste k), MTR-3 (multilayer thermal contact), MTR-4 (E = 114 GPa Ti-6Al-4V), MTR-5 (E = 193 GPa SS316L), MTR-6 (k = 401 W/(m·K) Cu). **All six carry a physical anchor** (NIST measured, ~1% uncertainty), which means the pass/fail threshold is tied to a value independently measured in laboratories outside the protocol — not an arbitrary constant chosen by the submitter. This is the strongest form of verification the protocol supports. PHYS-01 (kB = 1.380649 × 10⁻²³ J/K, SI 2019 exact) and PHYS-02 (NA = 6.02214076 × 10²³ mol⁻¹, SI 2019 exact) provide zero-uncertainty anchors at the foundation of the anchor hierarchy. Layer 3 (step chain) records per-sample raw-data fingerprints; the Schön failure mode — reuse of identical noise across nominally independent measurements — would produce identical per-sample hashes and be trivially flagged.

**Integration — 3 steps.**
1. Supply experimental or simulation data (seed + target constant, or a CSV of measurements).
2. `python scripts/mg_client.py --domain materials --output mtr1_bundle/` (defaults to E = 70 GPa Al; override via `--data`).
3. Downstream engineer, auditor, or partner runs `python scripts/mg.py verify --pack mtr1_bundle/` → PASS if `relative_error ≤ 0.01` against the anchor.

**Regulatory requirement.** AS9100 Rev D:2016, **Clause 8.3.4** (Design and development controls — requires reviews, verification that design outputs correspond to design inputs, and retention of documented information as objective evidence). Source: https://www.sae.org/standards/content/as9100d/. Also applicable: **ISO 26262-6:2018, Clause 9** (Software unit verification) and **ISO 26262-8:2018, Clause 11** (Confidence in the use of software tools) — https://www.iso.org/standard/68388.html.

---

## 5. Digital twin and FEM verification

**The computation.** A finite-element or multi-physics solver (ANSYS, FEniCS, OpenFOAM, COMSOL, Simcenter, or a custom code) produces a computed physical quantity — structural displacement, thermal field, stress concentration, modal frequency. A digital twin claims to mirror a physical asset in real time, with periodic calibration against instrumented ground truth. The twin's utility depends on the calibration chain staying tight: physical constant → material calibration → solver output → in-service drift.

**What happens when verification fails.** Takata ammonium-nitrate airbag inflators (2001–2014): 28 US deaths and 35 deaths globally (as of September 2024), approximately 67 million US inflators recalled (largest auto recall in US history), Takata Corporation bankruptcy in June 2017, USD 1 billion DOJ criminal settlement in January 2017 including an USD 850 million victim restitution fund. *The New York Times* reported in November 2014 that Takata had ordered technicians to destroy test results showing inflator cracks. Primary source: US Senate Commerce Committee Report, 2015 — https://www.commerce.senate.gov/public/_cache/files/998a3b71-e717-4a25-904c-5882b2dc23d0/DAAF1DD26E6E1F3403AED6F548F9484C.takata-report-final.pdf.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Industrial CFD rerun: billion-cell mesh, 200k cores, days of wall time; MPI-reduction non-associativity breaks bit-equality | ~60 seconds offline verification |
| Handoff dispute resolution across OEM / supplier / customer: weeks | $299 per bundle |

**Unique MetaGenesis properties for this domain.** DT-FEM-01 (displacement verification, `rel_err ≤ 0.02` vs. physical reference) is the primary claim; **it carries a physical anchor derived from MTR-1** (per SCOPE_001, anchor inheritance). DT-CALIB-LOOP-01 (calibration convergence certificate) monitors whether iterative re-calibration is actually converging; **it inherits the anchor through DRIFT-01 and MTR-1**. DRIFT-01 (drift ≤ 5% against verified anchor) completes the chain. The anchor hierarchy — PHYS-01/02 (SI 2019 exact, zero uncertainty) → MTR-* (NIST measured, ~1%) → DT-FEM-01 (derived) → DRIFT-01 (derived) — means that a single change upstream invalidates every downstream hash. This is the strongest use case for the 5-layer architecture because each layer protects against a different failure pattern: Layer 1 against file substitution, Layer 3 against step-reordering, Layer 5 against post-hoc destruction of inconvenient results (the Takata failure mode).

**Integration — 3 steps.**
1. Export FEM or CFD results alongside the physical reference measurement into a CSV (`fem_value`, `measured_value`, `quantity` columns) or a JSON parameter set.
2. `python scripts/mg_client.py --domain digital_twin --data fem.json --output dt_bundle/`.
3. Customer, OEM, or certifying body runs `python scripts/mg.py verify --pack dt_bundle/` → PASS or FAIL. For cross-claim chains (MTR-1 → DT-FEM-01), use `python scripts/mg.py verify-chain mtr1_bundle/ dt_bundle/`.

**Regulatory requirement.** NASA-STD-7009B (March 2024), Credibility Assessment Scale — 8 factors across 3 categories (M&S Development: Verification, Validation; M&S Operations: Input Pedigree, Results Uncertainty, Results Robustness; Supporting Evidence: Use History, M&S Management, People Qualifications). Any M&S output presented to a decision-maker must include (1) best estimate, (2) uncertainty statement, (3) CAS evaluation, (4) explicit caveats. Source: https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf.

---

## 6. IoT sensor integrity

**The computation.** A telemetry stream from a sensor (temperature, pressure, displacement, strain, voltage, airspeed, pitot pressure) feeds a digital twin, a monitoring dashboard, a control loop, or an operational-safety decision. The stream is high-volume, continuous, and often summarized into aggregate values that drive downstream computations.

**What happens when verification fails.** Air France Flight 447 (1 June 2009): an Airbus A330 crashed into the Atlantic en route from Rio de Janeiro to Paris; 228 deaths (all aboard). The BEA final report (5 July 2012) concluded Thales AA-series pitot tubes iced over, producing inconsistent airspeed readings. European aviation regulators had documented a "significant number of events" with that pitot model for at least two years prior. Primary source: Bureau d'Enquêtes et d'Analyses, "Final Report on the Accident on 1st June 2009 to the Airbus A330-203 registered F-GZCP operated by Air France, flight AF 447 Rio de Janeiro – Paris," 5 July 2012 — https://bea.aero/en/investigation-reports/notified-events/detail/accident-to-the-airbus-a330-203-registered-f-gzcp-and-operated-by-air-france-on-01-06-2009/.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Fleet-wide sensor-incident trend analysis: bespoke telemetry forensics team | Continuous drift monitoring against a verified anchor |
| Post-incident telemetry-log integrity disputes | $299 per bundle, offline verification |

**Unique MetaGenesis properties for this domain.** DT-SENSOR-01 (IoT sensor certificate: schema + range + temporal consistency) is the primary claim; it is **tamper-evident only** (per SCOPE_001). DRIFT-01 bound against a sensor-family baseline can surface a systematically misbehaving component before it aggregates into a fleet-wide safety event — the failure mode that preceded AF447 by at least two years. Layer 3 (step chain) binds each sensor reading to the previous one cryptographically, which makes post-incident ACARS or CVDR forensics a matter of hash-equality arithmetic rather than log-interpretation argument.

**Integration — 3 steps.**
1. Export the sensor stream to a JSON file with schema metadata (expected range, sample cadence, quantity).
2. `python scripts/mg_client.py --domain digital_twin --data sensor.json --output sensor_bundle/` (DT-SENSOR-01 is invoked via the `digital_twin` flag variant; see `scripts/mg_client.py` DOMAIN_CONFIG).
3. Airframe, component, or fleet operator runs `python scripts/mg.py verify --pack sensor_bundle/` → PASS or FAIL.

**Regulatory requirement.** UN Regulation No. 155 (E/ECE/TRANS/505/Rev.3/Add.154) — Cybersecurity Management System (Vehicles), Annex 5 (69 attack vectors); applies to all vehicles manufactured on or after 1 July 2024 in UNECE contracting parties. Source: https://unece.org/transport/documents/2021/03/standards/un-regulation-no-155-cyber-security-and-cyber-security. Also applicable to telemetry integrity in aerospace: DO-178C Design Assurance Levels A–E (see aerospace section below for citation with the `[CITATION UNVERIFIED]` flag on Table A-7 obj. #9).

---

## 7. System identification, scientific research, and peer review

**The computation.** A researcher fits parameters of a model from observed data — an ARX or state-space model from an input/output time series, an epidemiological microsimulation from case counts, a social-science regression from a survey. The fitted parameters, the seed, the exact input data, and the code version together determine whether the reported finding is reproducible.

**What happens when verification fails.** Neil Ferguson's CovidSim (Imperial College, March 2020) produced Report 9, which projected 510,000 UK and 2.2 million US deaths absent intervention. The underlying C code — 13 years old, undocumented — was released to GitHub only after substantial clean-up by Microsoft engineers. Independent reviewers documented non-determinism across runs on the same hardware. Codecheck (Eglen 2020) ultimately confirmed the key findings reproduce within approximately 5% — but only with the cleaned-up code version. Direct policy impact on UK and US lockdown decisions implicates trillions of USD in cumulative economic effect. Primary source: Eglen S., "CODECHECK confirms reproducibility of COVID-19 model results," 2020 — https://www.nature.com/articles/d41586-020-01685-y. Also in this domain: LaCour–Green *Science* retraction (December 2014 / 28 May 2015) — Broockman, Kalla, Aronow attempted to replicate, contacted the alleged survey firm, learned no such survey had been conducted; paper retracted over lead author's objection. Primary source: *Science* retraction notice — https://www.science.org/doi/10.1126/science.aac6638. Also: Open Science Collaboration 2015 — 100 psychology studies replicated, 97% of originals had significant results, 36% of replications did; primary source: *Science* 349:aac4716 — https://www.science.org/doi/10.1126/science.aac4716.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Post-publication replication: months, new teams, new funding | ~60 seconds offline verification |
| Pre-registration enforced by editorial process alone | Layer 5 temporal commitment proves the analysis plan predates the data |

**Unique MetaGenesis properties for this domain.** SYSID-01 (ARX calibration, rel_err ≤ 0.03) is the primary parameter-identification claim; **it is tamper-evident only** (per SCOPE_001). For research reproducibility more broadly, any claim template applies — the load-bearing property is Layer 5 temporal commitment: the NIST Beacon commits the analysis plan to a specific published random value, which cannot be backdated because the beacon value for a future pulse does not exist until that pulse is published. This addresses researcher degrees of freedom at a cryptographic level. DATA-PIPE-01 (schema + range certificate) applies to the dataset-quality half of the pipeline.

**Integration — 3 steps.**
1. Prepare an input JSON with `seed`, `a_true`, `b_true`, `n_steps`, `u_max` for SYSID-01 — or, for a general research artifact, a claim-specific parameter file.
2. `python scripts/mg_client.py --domain systems --data arx.json --output sysid_bundle/`.
3. Peer reviewer, journal editor, or funder runs `python scripts/mg.py verify --pack sysid_bundle/` → PASS or FAIL.

**Regulatory requirement.** NIH Data Management and Sharing Policy, **NOT-OD-21-013** (effective 2023-01-25) — all NIH grant applications resulting in scientific-data generation must include a Data Management and Sharing Plan covering data types, access tools, standards, preservation, access control, and compliance oversight. Approved DMSP becomes a term of the award. Source: https://grants.nih.gov/grants/guide/notice-files/NOT-OD-21-013.html. Also: cOAlition S Plan S Principles 5 and 8 (open-access compliance and FAIR infrastructure) — https://www.coalition-s.org/addendum-to-the-coalition-s-guidance-on-the-implementation-of-plan-s/principles-and-implementation/. Also: ALLEA European Code of Conduct for Research Integrity (Revised 2023), Section 2 — https://allea.org/code-of-conduct/.

---

## 8. Algorithmic trading

**The computation.** An algorithmic trading system decides, places, cancels, and confirms thousands of orders per second across multiple venues. Each order carries a client ID, a strategy identifier, a source code version, and a timestamp. Regulators require the firm to reconstruct the full order lifecycle on demand.

**What happens when verification fails.** Knight Capital Americas LLC (1 August 2012) deployed new code to its Smart Market Access Routing System (SMARS) to support the NYSE Retail Liquidity Program. The deployment reached only 7 of 8 servers; the 8th ran a code path repurposed in 2005 ("Power Peg"), reactivated by a flag that had been reused for the new feature. In 45 minutes of market open, the 8th server generated millions of erroneous child orders. Consequence: USD 440 million realized pre-tax loss; emergency capital infusion; acquisition by Getco to form KCG Holdings; USD 12 million SEC penalty under Rule 15c3-5 (first enforcement under the Market Access Rule). Primary source: SEC Order in *In the Matter of Knight Capital Americas LLC*, Release No. 34-70694, 16 October 2013 — https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf. Also: the 6 May 2010 Flash Crash — approximately USD 1 trillion in market value evaporated intraday; primary source: SEC-CFTC Joint Advisory Committee, 30 September 2010 — https://www.sec.gov/news/studies/2010/marketevents-report.pdf.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Partial-deployment failures caught at market open by loss magnitude | Hash-mismatch across deployed servers caught immediately |
| Post-incident multi-venue order-book reconstruction: months | Step-chain + NIST-Beacon timestamp = microsecond-accurate independent replay |

**Unique MetaGenesis properties for this domain.** No dedicated `TRADING-01` claim exists in v1.0.0-rc1 — this is documented as a future addition in `.planning/research/SUMMARY.md` §10. The bundle format itself is order-record agnostic, and the pattern that FINRISK-01 establishes for risk-model outputs transfers directly. The relevant layers for trading are Layer 1 (byte-exact order-log integrity), Layer 3 (step chain enforces ordering — reordering orders or cancellations invalidates `trace_root_hash`), Layer 4 (Ed25519 proves the firm identity per record), and Layer 5 (NIST Beacon commitment prevents backdating to shift the apparent pre-trade state). All four are **tamper-evident only**; no physical anchor applies to order records (per SCOPE_001).

**Integration — 3 steps.**
1. Export the trading system's order-and-cancellation log for the relevant window as a JSON artifact (one record per order event).
2. `python scripts/mg_client.py --domain finance --data orders.json --output trading_bundle/` (using the `finance` domain template as the closest existing fit; a dedicated trading template is a documented future addition).
3. Competent authority runs `python scripts/mg.py verify --pack trading_bundle/` → PASS or FAIL.

**Regulatory requirement.** MiFID II, Directive 2014/65/EU, **Article 17(2) second subparagraph**: "An investment firm that engages in a high-frequency algorithmic trading technique shall store in an approved form accurate and time sequenced records of all its placed orders, including cancellations of orders, executed orders and quotations on trading venues and shall make them available to the competent authority upon request." Source: https://eur-lex.europa.eu/eli/dir/2014/65/oj/eng. ESMA Interactive Single Rulebook for Article 17: https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mifid-ii/article-17-algorithmic-trading.

---

## 9. Financial risk — VaR, credit, stress testing

**The computation.** A bank or asset manager runs a Value-at-Risk model, a credit-scoring model, a stress-test scenario, or a Monte Carlo simulation whose output drives regulatory capital, internal risk limits, or public disclosure. Validation by an independent team is the regulatory expectation under SR 11-7, Basel III, and equivalent frameworks. The validator frequently does not have access to the production model runtime.

**What happens when verification fails.** JPMorgan Chase London Whale (2012): the Chief Investment Office hurriedly adopted a new VaR model in late January 2012 that immediately lowered reported Synthetic Credit Portfolio VaR by approximately 50%, enabling continued risk-taking despite limit breaches. The US Senate Permanent Subcommittee on Investigations later concluded the new model contained formula and calculation errors and relied on error-prone manual Excel data entry. Consequence: approximately USD 6.2 billion trading loss; USD 920 million in combined SEC / OCC / FRB / UK FCA fines; two trader indictments. Primary source: US Senate PSI, "JPMorgan Chase Whale Trades: A Case History of Derivatives Risks and Abuses," 15 March 2013 — https://www.hsgac.senate.gov/wp-content/uploads/imo/media/doc/REPORT%20-%20JPMorgan%20Chase%20Whale%20Trades%20(4-12-13).pdf. Also: LIBOR manipulation (Barclays 2005–2009 and peers) — **this is primarily a governance and fraud case; MetaGenesis would have bounded the damage by cryptographically binding each rate submission to a specific individual and their contemporaneous book evidence, not prevented collusion** (Barclays CFTC order 27 June 2012 — USD 453 million; industry-wide fines exceeded USD 9 billion across 2012–2015). Primary source: CFTC Order against Barclays — https://www.cftc.gov/PressRoom/PressReleases/6289-12.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Monte Carlo VaR: 50k–100k paths nightly, seeded — bit-equality fails by construction | Verifier operates on the artifact, not on a rerun |
| Independent validation: model access, data access, bespoke infrastructure | $299 per bundle, offline |

**Unique MetaGenesis properties for this domain.** FINRISK-01 (VaR model certificate, `abs(actual_var − claimed_var) ≤ var_tolerance`) is the primary claim; **it is tamper-evident only** (per SCOPE_001). DRIFT-01 monitors deviation of the live model from a verified baseline, addressing SR 11-7 Section V's ongoing-monitoring requirement at a cryptographic level. AGENT-DRIFT-01 is a meta-claim: the agent that monitors model drift can itself be monitored. Layer 4 (Ed25519) identifies which model version produced which daily number — the exact signal missing from the London Whale's silent model swap.

**Integration — 3 steps.**
1. Prepare a JSON input with `claimed_var`, `var_tolerance`, `confidence_level`, and the portfolio identifier.
2. `python scripts/mg_client.py --domain finance --data var.json --output finrisk_bundle/`.
3. Regulator or internal model-risk team runs `python scripts/mg.py verify --pack finrisk_bundle/` → PASS or FAIL.

**Regulatory requirement.** Federal Reserve SR 11-7 / OCC 2011-12, **Section V "Validation" — Ongoing Monitoring**: validation must include "an evaluation of conceptual soundness, ongoing monitoring, and outcomes analysis" and must be performed by parties independent of model development. Source: https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm. Also: Basel III / BCBS 239, **Principle 3 — Accuracy and Integrity** — https://www.bis.org/publ/bcbs239.pdf. Also: **SEC Rule 17 CFR § 240.17a-4(f)** — audit-trail alternative for electronic recordkeeping systems — https://www.law.cornell.edu/cfr/text/17/240.17a-4.

---

## 10. Automotive simulation

**The computation.** An automotive OEM or Tier-1 supplier runs structural, crash, thermal, EMI, or ECU-calibration simulations that feed type-approval, safety certification, and on-vehicle deployment. Autonomous-driving stacks additionally consume perception, prediction, and planning outputs whose correctness feeds real-time safety decisions.

**What happens when verification fails.** Volkswagen Dieselgate (2015): the EPA issued a Notice of Violation of the Clean Air Act on 18 September 2015 against Volkswagen AG, Audi AG, and VW Group of America. ECU software on model-year 2009–2015 2.0L TDI diesels detected official EPA test conditions and enabled full emissions controls only during testing; on-road NOx emissions were up to 40× the standard. Consequence: USD 25+ billion in US civil/criminal penalties (global total exceeding USD 33 billion); approximately 11 million affected vehicles worldwide, 500,000 in the US; multiple criminal convictions; Winterkorn indicted; ~€30 billion market-cap loss within weeks. Primary source: EPA Notice of Violation to Volkswagen, 18 September 2015 — https://www.epa.gov/sites/default/files/2015-10/documents/vw-nov-caa-09-18-15.pdf. Also: Uber ATG Tempe pedestrian fatality (18 March 2018) — the first pedestrian fatality by a Level-4 autonomous test vehicle. Primary source: NTSB Highway Accident Report HAR-19/03, adopted 19 November 2019 — https://www.ntsb.gov/investigations/accidentreports/reports/har1903.pdf.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Type-approval submission vs. on-vehicle behavior: no cryptographic equality | Signed ECU calibration bundle = type-approval artifact; hash mismatch flags defeat behavior |
| NTSB log-integrity disputes: months | Signed telemetry bundle = offline-verifiable chain of every sensor frame |

**Unique MetaGenesis properties for this domain.** No dedicated automotive-simulation claim exists in v1.0.0-rc1 — the nearest existing claims are DT-FEM-01 (**physical anchor via MTR-1**), DT-SENSOR-01 (tamper-evident only), and DRIFT-01 (**derived anchor**). The pattern is identical to the digital-twin and IoT-sensor use cases. For ECU-software OTA updates, UN R156 is an almost one-to-one mapping onto the MetaGenesis bundle lifecycle; a dedicated `AUTO-OTA-01` claim is a documented future addition (see `.planning/research/SUMMARY.md` §10). Layer 4 (Ed25519 signature) + Layer 5 (NIST Beacon commitment) make "the calibration on this vehicle today" cryptographically equal to "the calibration submitted for type-approval" — any branch or conditional behavior absent from the approved bundle breaks verification.

**Integration — 3 steps.**
1. Export the simulation or telemetry payload alongside the reference configuration into a JSON or CSV file.
2. `python scripts/mg_client.py --domain digital_twin --data sim.json --output auto_bundle/`.
3. Type-approval authority, NHTSA, or KBA runs `python scripts/mg.py verify --pack auto_bundle/` → PASS or FAIL.

**Regulatory requirement.** UN Regulation No. 156 — Software Update Management System — in force since July 2022, mandatory for new vehicles from 1 July 2024; harmonised with ISO 24089:2023. The manufacturer must operate a certified SUMS that can "plan, package, approve, deliver, verify, and record software updates securely across a vehicle's service life." Source: https://unece.org/transport/vehicle-regulations/working-party-automated-autonomous-and-connected-vehicles-introduction. Also: UN Regulation No. 155 (CSMS) Annex 5 — 69 attack vectors — https://unece.org/transport/documents/2021/03/standards/un-regulation-no-155-cyber-security-and-cyber-security. Also: **ISO 26262-4:2018 Clause 9** (system-level integration and verification) — https://www.iso.org/standard/68388.html.

---

## 11. Carbon, climate, and ESG model verification

**The computation.** Carbon-credit issuance, climate-model forecasts, and ESG disclosure rest on computational outputs — deforestation-baseline models, satellite-derived land-use change metrics, scope 1/2/3 greenhouse-gas accounting, physical-risk scenario runs. The outputs drive financial flows, regulatory disclosure, and corporate reputational exposure. The underlying models are proprietary in most cases; auditors are asked to validate outputs without access to the model.

**What happens when verification fails.** The Verra rainforest carbon-credit investigation (18 January 2023) — a nine-month joint investigation by *The Guardian*, *Die Zeit*, and SourceMaterial applied peer-reviewed deforestation-baseline models to two-thirds of Verra's 87 active REDD+ offsetting projects. Journalists concluded roughly 94% of rainforest credits (about 40% of all Verra-approved credits) did not represent a tonne of avoided CO2e; deforestation threat was overstated by approximately 400% on average. Consequence: Verra CEO David Antonioli resigned May 2023; major corporate buyers (Gucci, Shell, Disney) faced reputational exposure; voluntary carbon market price collapse in 2023; Verra revised REDD+ methodology (VM0048) in direct response. Primary source: Greenfield P., *The Guardian*, 18 Jan 2023, with underlying science in West et al., *Science* 2023 — https://www.science.org/doi/10.1126/science.ade3535.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Limited-assurance audit: manual recomputation of every number | Auditor runs `mg verify --pack esg_bundle/` per disclosure |
| Methodology defensibility disputes resolved in court | $299 per bundle; bundle proves the model produced exactly this number on exactly this data |

**Unique MetaGenesis properties for this domain.** No dedicated `CLIMATE-01` claim exists in v1.0.0-rc1 — documented future addition (see `.planning/research/SUMMARY.md` §10). Every ESG computation can be packaged through FINRISK-01's pattern with domain-specific parameters. The claim would be **tamper-evident only** per SCOPE_001 (MetaGenesis does not endorse the scientific defensibility of a carbon model — it proves that the model produced exactly this number on exactly this data). Layer 4 (Ed25519) binds each disclosure to the issuing entity; Layer 5 (NIST Beacon) locks the disclosure to a specific publication time.

**Integration — 3 steps.**
1. Export the carbon-accounting or ESG-metric computation payload (inputs, intermediate values, claimed output, tolerance) as JSON.
2. `python scripts/mg_client.py --domain finance --data esg.json --output esg_bundle/` (using FINRISK-01 pattern; dedicated template planned).
3. Statutory auditor or Independent Assurance Services Provider runs `python scripts/mg.py verify --pack esg_bundle/` → PASS or FAIL.

**Regulatory requirement.** **IFRS S2 — Climate-related Disclosures** (ISSB, June 2023; effective for annual reporting periods on or after 2024-01-01); requires "consistent, complete, comparable and verifiable" sustainability-related financial information. Source: https://www.ifrs.org/issued-standards/ifrs-sustainability-standards-navigator/ifrs-s2-climate-related-disclosures/. Also: EU CSRD, **Directive (EU) 2022/2464, Article 34a** — limited assurance from a statutory auditor covering compliance with ESRS, materiality-assessment process, EU Taxonomy alignment, and digital tagging. Source: https://eur-lex.europa.eu/eli/dir/2022/2464/oj. Commission adopts limited-assurance standards before 1 October 2026.

---

## 12. Quantum computing

**The computation.** A quantum processor samples outputs from a specific random circuit (random-circuit sampling, boson sampling, Gaussian boson sampling). A "quantum advantage" claim compares the measured runtime against the best-known classical simulation of the same circuit. The claim is sensitive to the exact circuit, shot count, measurement outcomes, and classical baseline assumptions.

**What happens when verification fails.** Google Sycamore (23 October 2019, Arute et al., *Nature* 574:505–510) claimed the processor sampled a specific random-circuit instance in 200 seconds versus an estimated 10,000 years classical. Within days, IBM (Pednault, Gunnels, Gambetta) argued the classical estimate was wrong — their secondary-storage-augmented approach could do it in 2.5 days. Subsequent classical-simulation work by Pan & Zhang (2021), Kalachev et al. (2022), and Gao et al. (2024) further reduced the classical cost, with some tensor-network approaches matching Sycamore's runtime on commodity GPU clusters. Consequence: no financial loss, but erosion of "quantum supremacy" as a meaningful milestone; subsequent claims (Jiuzhang, Zuchongzhi) face similar classical-simulation pushback cycles. **This is primarily a scientific-methodology dispute rather than a verification failure** — MetaGenesis would have frozen the sealed circuit so both sides are arguing about the same artifact. Primary sources: Arute F. et al., *Nature* 574:505–510 (2019), DOI 10.1038/s41586-019-1666-5; IBM response Pednault E. et al., arXiv:1910.09534; refutation Pan F., Zhang P., *Phys. Rev. Lett.* 128, 030501 (2022).

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Moving-goalpost arguments over what was actually claimed | Sealed bundle with fixed circuit + shots + outcomes |
| Reproducing shots: access to the quantum processor | Classical simulator or competing platform verifies offline |

**Unique MetaGenesis properties for this domain.** No dedicated quantum-computing claim exists in v1.0.0-rc1 — the claim pattern is identical to ML_BENCH-01 with domain-specific parameters (circuit hash, shot count, measurement histogram). The claim would be **tamper-evident only** per SCOPE_001. Layer 3 (step chain) records the exact circuit and shot count; Layer 5 (NIST Beacon) proves when each side's claim was fixed — independently of either side's infrastructure.

**Integration — 3 steps.**
1. Export the circuit description, shot count, and measured histogram as JSON.
2. `python scripts/mg_client.py --domain ml --data quantum.json --output quantum_bundle/` (using ML_BENCH-01 pattern as closest template).
3. Competing platform team, classical-simulation team, or journal reviewer runs `python scripts/mg.py verify --pack quantum_bundle/` → PASS or FAIL.

**Regulatory requirement.** No domain-specific regulation in force. Cross-cutting: NIST AI RMF 1.0 MEASURE framework applies to any computational claim used in a decision-making context — https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf.

---

## 13. Aerospace certification

**The computation.** Certification of an airborne system — a flight-control law, a MCAS-style flight-envelope protection, a propulsion-system FADEC, an avionics sensor-fusion output — depends on verified simulation, verified software, and verified test evidence. Design Assurance Levels A through E (catastrophic → no-effect) prescribe objective counts (DAL A: 66; DAL B: 65; DAL C: 57; DAL D: 28; DAL E: 0) against Annex A objective tables in DO-178C.

**What happens when verification fails.** Boeing 737 MAX MCAS (2018–2019): 346 deaths across Lion Air 610 (29 October 2018, 189 aboard) and Ethiopian Airlines 302 (10 March 2019, 157 aboard); worldwide 737 MAX fleet grounding March 2019 – December 2020; DOJ Deferred Prosecution Agreement January 2021 (USD 2.5 billion); CEO Dennis Muilenburg fired December 2019; Boeing financial impact exceeding USD 20 billion. MCAS was designed to take input from only one of two angle-of-attack sensors; the hazard classification of AoA-sensor failure was a simulation-based claim that was not independently verified against worst-case assumption-set bundles. Primary source: US House Committee on Transportation Final Report, September 2020; Ethiopian CAA Final Report ET-AVJ, December 2022 — https://www.ntsb.gov/investigations/Documents/Response%20to%20EAIB%20final%20report.pdf. Also: Space Shuttle Challenger STS-51-L (28 January 1986) — 7 crew deaths, 32-month fleet grounding, USD 8+ billion (1986 dollars) program impact. **Challenger is primarily a management and governance failure, not a verification-gap case — MetaGenesis would have made the override decision a cryptographic act requiring explicit sign-off, not prevented the decision.** Primary source: Rogers Commission Report, 6 June 1986 — https://www.nasa.gov/history/rogersrep/genindex.htm.

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Independent auditor (DER, authorized representative) verification flow: manual | Offline verification of simulation and test bundles, one command each |
| Post-incident design-assumption reconstruction: years | Step chain records the exact assumption set |

**Unique MetaGenesis properties for this domain.** DT-FEM-01 (**physical anchor through MTR-1**) and MTR-4 / MTR-5 (**aerospace-grade Ti-6Al-4V and SS316L anchors, NIST measured**) are the relevant anchored claims. Layer 4 (Ed25519) supports per-authority signing — DER, TCCA, FAA AEG — without key sharing. Layer 5 (NIST Beacon commitment) addresses the "when did we know" question for safety-of-flight simulations. Objectives on Annex A Table A-7 map naturally onto bundle artifacts: verification-of-verification results are packaged as claim bundles with explicit PASS/FAIL on the threshold.

**Integration — 3 steps.**
1. Export the simulation or V&V test payload with explicit threshold, reference value, and tolerance as JSON or CSV.
2. `python scripts/mg_client.py --domain digital_twin --data dt.json --output aero_bundle/` (DT-FEM-01 template).
3. Authority or DER runs `python scripts/mg.py verify --pack aero_bundle/` → PASS or FAIL. For anchor-chained evidence (MTR-4 → DT-FEM-01 → DRIFT-01), use `python scripts/mg.py verify-chain bundle_a/ bundle_b/`.

**Regulatory requirement.** DO-178C (RTCA / EUROCAE ED-12C, December 2011), Design Assurance Levels A–E, **Annex A Table A-7 — Verification of Verification Process Results** (9 objectives). DAL A requires 66 objectives; DAL D requires 28. Source: https://www.rtca.org/wp-content/uploads/2020/08/do-178c.pdf. **`[CITATION UNVERIFIED]` — exact wording of Table A-7 objective #9 was taken from a secondary source, not from the standard itself.** Also applicable: NASA-STD-7009B (see digital-twin section above for full citation) — https://standards.nasa.gov/sites/default/files/standards/NASA/B/1/NASA-STD-7009B-Final-3-5-2024.pdf. Also: AS9100 Rev D Clause 8.3.4 (design and development controls).

---

## 14. Data pipelines and agent drift

**The computation.** (a) An ingestion pipeline produces a dataset that downstream models consume — schema correctness, range correctness, and absence of temporal anomalies are necessary conditions for every downstream claim. (b) An autonomous agent produces artifacts continuously over time; its own quality metrics (tests per phase, pass rate, regressions, iterations to pass the verifier) must themselves be monitored lest the evaluator drift.

**What happens when verification fails.** Both subdomains are cross-cutting; concrete named incidents appear in the other domains above (Zillow iBuying 2021 for data-pipeline-driven ML failure; the Duke Potti data-manipulation case for a scientific data-pipeline failure). The distinct value of packaging them as first-class claims is that the upstream failure is caught at the pipeline layer before it cascades. Kapoor and Narayanan (2023) documented data-leakage pitfalls across 294 papers — an elementary DATA-PIPE-01 check (schema + range + absence of train/test overlap) would have caught the majority of the 8 documented leakage types. Primary source: Kapoor S., Narayanan A., "Leakage and the reproducibility crisis in machine-learning-based science," *Patterns* 4(9), August 2023, DOI 10.1016/j.patter.2023.100804 (PMID 37720327).

**The cost equation.**

| Without MetaGenesis | With MetaGenesis |
|---|---|
| Downstream failure localization: debug forwards from a wrong model output | Upstream PASS/FAIL per pipeline run catches the failure at the source |
| Agent-quality monitoring: bespoke dashboards | AGENT-DRIFT-01 = the evaluator applies the same protocol to itself |

**Unique MetaGenesis properties for this domain.** DATA-PIPE-01 (quality certificate — schema + range; no absolute paths in output) is the pipeline claim. AGENT-DRIFT-01 (composite drift ≤ 20% across tests_per_phase, pass_rate, regressions, verifier_iterations) is the agent-drift claim. **Both are tamper-evident only** (per SCOPE_001). AGENT-DRIFT-01 is notable architecturally: it is the first claim where agents monitor their own quality through the same verification protocol they extend — recursive self-verification. DRIFT-01, which is anchored, composes with both: a drift > 5% triggers `correction_required = True` signal downstream.

**Integration — 3 steps.**
1. Export the dataset summary (schema, per-column range, SHA-256 of the dataset file) for DATA-PIPE-01, or the agent baseline / current metrics (tests_per_phase, pass_rate, regressions, verifier_iterations) for AGENT-DRIFT-01.
2. `python scripts/mg_client.py --domain agent --data agent.json --output agent_bundle/` (for AGENT-DRIFT-01); the DATA-PIPE-01 template runs via `python -m pytest tests/data/test_datapipe01_quality_certificate.py -v` in v1.0.0-rc1 and is packageable via the same bundle flow.
3. Internal audit, SOC 2 assessor, or NIST AI RMF MANAGE-function reviewer runs `python scripts/mg.py verify --pack agent_bundle/` → PASS or FAIL.

**Regulatory requirement.** SOC 2 AICPA Trust Services Criteria (2017 framework, 2022 revision), **CC7.2** (monitor system components for anomalies) and **CC8.1** (authorize, design, develop, and implement changes with documented approval and rollback). Source: https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022. Also applicable: NIST AI RMF 1.0 MANAGE 4 (incident detection / drift) — https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf.

---

## Summary — 14 domains at a glance

| # | Domain | Primary claim(s) | Incident cited | Regulation cited |
|---|---|---|---|---|
| 1 | ML / AI benchmarks | ML_BENCH-01/02/03, DRIFT-01, AGENT-DRIFT-01 | Kapoor-Narayanan 2023; Zillow 2021 | EU AI Act Art. 15; NIST AI RMF |
| 2 | Pharma / biotech | PHARMA-01 | Duke Potti 2010–15; Takeda Actos 2010–15 | 21 CFR §11.10(e); FDA AI Draft Jan 2025 |
| 3 | Medical devices | DT-SENSOR-01 analogue | Therac-25 1985–87; Guidant 2002–05; Theranos 2015–22 (governance) | FDA 510(k) 2023; IEC 62304 §5.8; EU MDR Annex I §17 |
| 4 | Materials science | MTR-1/2/3/4/5/6 ⚓; PHYS-01/02 ⚓ | Schön 2002 | AS9100D §8.3.4; ISO 26262-6 §9 |
| 5 | Digital twin / FEM | DT-FEM-01 ⚓; DT-CALIB-LOOP-01 ⚓; DRIFT-01 ⚓ | Takata 2001–14 | NASA-STD-7009B CAS |
| 6 | IoT sensor | DT-SENSOR-01 | Air France 447 2009–12 | UN R155 Annex 5 |
| 7 | System ID / science / peer review | SYSID-01; DATA-PIPE-01 | CovidSim 2020; LaCour 2014; OSC 2015 | NIH NOT-OD-21-013; Plan S; ALLEA |
| 8 | Algorithmic trading | TRADING-01 (planned); FINRISK-01 pattern | Knight Capital 2012; Flash Crash 2010 | MiFID II Art. 17(2) |
| 9 | Financial risk | FINRISK-01; DRIFT-01 | JPM London Whale 2012; LIBOR 2005–12 (governance) | SR 11-7 §V; BCBS 239 Principle 3; SEC 17a-4(f) |
| 10 | Automotive simulation | AUTO-OTA-01 (planned); DT-FEM-01 ⚓; DT-SENSOR-01 | VW Dieselgate 2015; Uber ATG 2018 | UN R156; UN R155; ISO 26262-4 §9 |
| 11 | Carbon / ESG | CLIMATE-01 (planned); FINRISK-01 pattern | Verra 2023 | IFRS S2; CSRD Art. 34a |
| 12 | Quantum computing | ML_BENCH-01 pattern | Google Sycamore 2019 (methodology) | — |
| 13 | Aerospace certification | DT-FEM-01 ⚓; MTR-4 ⚓; MTR-5 ⚓ | 737 MAX 2018–19; Challenger 1986 (governance) | DO-178C Table A-7 `[CITATION UNVERIFIED obj. #9]`; NASA-STD-7009B |
| 14 | Data pipeline / agent drift | DATA-PIPE-01; AGENT-DRIFT-01; DRIFT-01 ⚓ | Kapoor-Narayanan 2023 (cross-cut) | SOC 2 CC7.2, CC8.1; NIST AI RMF MANAGE 4 |

**Legend:** ⚓ = physical anchor per SCOPE_001. Planned claims (AUTO-OTA-01, CLIMATE-01, TRADING-01, EDC-01, DOC-HASH-01) are informational only — documented as future additions in `.planning/research/SUMMARY.md` §10 and NOT implemented in v1.0.0-rc1.

---

## Next steps — where to go from here

- **`docs/CLIENT_JOURNEY.md`** — 6 persona journeys (ML engineer at an AI startup, computational chemist at a biotech, model-risk manager at a bank, FEM engineer at an aerospace / automotive supplier, quant analyst at a hedge fund, research scientist) with exact trigger moments, three-step integration paths, and commands verified against the actual SDK and CLI source.
- **`docs/WHY_NOT_ALTERNATIVES.md`** — composability stance ("X + MetaGenesis") vs. 10 specific alternatives (SHA-256 alone, Docker image hash, MLflow / DVC, manual audit, signed PDF, git history, Jupyter output, Nextflow / CWL / Snakemake, Chainpoint / RFC 3161, Coq / Lean formal); a step-by-step walk-through of the CERT-02 strip-and-recompute attack; rerun-cost math across three domains (GPT-3 training, industrial CFD, Basel Monte Carlo VaR).
- **`docs/REGULATORY_GAPS.md`** — all 24 regulations grouped by domain, with honest `[GAP]` flags preserved for training-data lineage (EU AI Act Art. 10), human oversight (EU AI Act Art. 14), organizational governance (SOC 2 CC1–CC4), design-document certification (510(k) / IEC 62304 / DO-178C / AS9100D), and post-quantum signing migration (FIPS 204 ML-DSA, 2030 NSS deadline).
- **`reports/READINESS_ASSESSMENT.md`** — 7-section honest verdict on v1.0.0-rc1 readiness for first paying customer at $299.

---

*USE_CASES v2.0 — 2026-04-16 — MetaGenesis Core v1.0.0-rc1 — 14 domains, 20 active claims, 5-layer verification, 2407 tests PASS.*
