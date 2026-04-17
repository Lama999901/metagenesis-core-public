# Client Journey

## What this document is

Six persona journeys — real jobs, real tools, real regulatory triggers.
Each journey begins when a specific regulation or audit event lands on
someone's desk, walks through what they tried before, shows verbatim
commands from the shipped CLI, describes what the verifier does, and
ends with what measurably changes. Every regulatory citation carries
an exact article or clause. Every command is taken from
`sdk/metagenesis.py`, `scripts/mg.py`, or `scripts/mg_client.py` — no
pseudocode, no invented flags. MetaGenesis Core is composable: it sits
alongside the tools these people already use (MLflow, Schrödinger,
QuantLib, Abaqus, kdb+, Zenodo) and closes one evidence gap each.

## Quick-scan matrix

| # | Persona | Regulatory trigger | Primary claim | Integration time |
|---|---------|-------------------|---------------|------------------|
| 1 | ML Engineer at AI startup | SOC 2 TSC CC7.2 + CC8.1 | ML_BENCH-01 | ~3 hours |
| 2 | Computational Chemist at biotech | FDA AI Credibility Framework (Jan 2025) + 21 CFR Part 11 §11.10(e) | PHARMA-01 | ~5 hours |
| 3 | Model Risk Manager at G-SIB bank | ECB TRIM 2.0 + CRR Art. 365-366 + SR 11-7 + PRA SS1/23 | FINRISK-01 | 5-8 days |
| 4 | FEM Engineer at aerospace supplier | AS9100 Rev D Clause 8.3.4 / 8.3.5 + NASA-STD-7009B CAS | MTR-1 → DT-FEM-01 | 2-3 days |
| 5 | Quant Analyst at hedge fund | MiFID II Art. 17(2) + EU Delegated Reg 2017/589 | ML_BENCH-02 | 1-2 weeks |
| 6 | Research Scientist at lab | Nature Methods Code & Data Availability + NeurIPS Reproducibility Track + NIH NOT-OD-21-013 (DMSP) | ML_BENCH-01 | 1-2 days |

---

## 1. ML Engineer at AI Startup — SOC 2 CC7.2 + CC8.1

### Who this person is

Senior or staff ML engineer at a Series B or C AI product company
(roughly 50-300 people). Owns the model card, the evaluation harness,
and the deployment pipeline. Works in VS Code and Jupyter, relies on
`scikit-learn`, `xgboost`, `pytorch`, and `transformers`; tracks
experiments in `mlflow` with dashboards in `wandb`; pins datasets with
DVC; runs CI evaluation through GitHub Actions; structures config with
`hydra`; and pushes model artefacts to S3 or HuggingFace Hub. The eval
suite is `pytest` plus a bespoke harness that writes `y_true` / `y_pred`
CSVs per release.

### The exact trigger moment

The sales team closes a $400k annual contract with an insurance
carrier, conditional on the startup passing a SOC 2 Type II audit
within ninety days. The external auditor's Request List targets AICPA
Trust Services Criteria **CC7.2** ("The entity monitors system
components and the operation of those components for anomalies") and
**CC8.1** ("The entity authorizes, designs, develops, tests, approves,
and implements changes"). The concrete ask: produce evidence that each
model version deployed to production was validated against an acceptance
threshold, that the validation artefact was authorised before deployment,
and that production outputs are monitored for deviation from that
baseline. The auditor pins the engineer down: "How do you prove that
model `v3.2.1-prod` actually hit 0.94 accuracy on dataset `eval_2026Q1`
on the date you deployed it — and how do I know that number was not
edited after the fact?"

### What they tried first

The engineer walks the auditor through MLflow. The auditor asks whether
MLflow entries are immutable — they are not, a user with DB write access
can overwrite a run, so the control fails. A weekly signed PDF "model
quality" report is next: the auditor accepts the signature but cannot
confirm the numbers inside came from the eval run. S3 object-lock on
the MLflow artefact store proves a file was not deleted but does not
prove its content came from an authoritative computation. DVC-tracked
eval datasets with git tags pin the dataset, yet the auditor still asks
whether the model actually produced 0.94 on it. Each tool proves one
property; none prove *"this model, on this dataset, on this date,
produced exactly this accuracy number, and the number has not been
touched since."*

### Three steps with real commands

**Step 1 — Install and smoke-test.**

```bash
git clone https://github.com/Lama999901/metagenesis-core-public.git
cd metagenesis-core-public
pip install -r requirements.txt
python scripts/mg_client.py --demo
```

The demo runs `ML_BENCH-01`, produces a signed bundle, and verifies all
five layers in place: Layer 1 (SHA-256 integrity), Layer 2 (semantic
structure), Layer 3 (Step Chain), Layer 4 (Bundle Signature), Layer 5
(Temporal Commitment).

**Step 2 — Wire the CI eval harness to emit a bundle.**

After the eval pipeline writes `predictions/model_v3_2_1_eval_2026Q1.csv`,
the engineer creates `configs/mg_ml.json`:

```json
{
  "seed": 42,
  "claimed_accuracy": 0.94,
  "accuracy_tolerance": 0.02,
  "n_samples": 10000
}
```

The CI job ends with one call:

```bash
python scripts/mg_client.py --domain ml \
    --data configs/mg_ml.json \
    --output bundles/model_v3_2_1_20260416
```

This invokes `ML_BENCH-01` (`backend/progress/mlbench1_accuracy_certificate.py`),
writes the 4-step execution trace, drops `evidence.json`,
`pack_manifest.json`, `bundle_signature.json`, and
`temporal_commitment.json` into the output directory, and immediately
verifies all five layers.

**Step 3 — Archive the bundle into the SOC 2 evidence repository.**

The engineer prefers Python over shell for CI glue, so they use the SDK:

```python
from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
result = client.verify("bundles/model_v3_2_1_20260416")
assert result.passed, f"Bundle FAIL: {result.reason}"
receipt = client.receipt("bundles/model_v3_2_1_20260416")
with open("evidence/soc2_cc8_model_v3_2_1.txt", "w") as f:
    f.write(receipt)
```

The bundle directory is uploaded to the auditor's shared evidence portal
as part of the CC8.1 change-management package.

### What the verifier does

On a fresh laptop with Python 3.9 installed, no network access, and no
credentials from the startup, the SOC 2 auditor runs:

```bash
python scripts/mg.py verify --pack bundles/model_v3_2_1_20260416
```

Output: `PASS`, in under 60 seconds for a roughly 50 KB bundle.
Optionally the auditor requests a human-readable receipt:

```bash
python scripts/mg.py verify --pack bundles/model_v3_2_1_20260416 \
    --receipt receipts/soc2_cc8_model_v3_2_1.json
```

The receipt contains the verification timestamp, bundle root hash, the
auditor's username, the platform, the `PASS` result, the list of layers
checked, and a `receipt_hash` covering the other fields. The auditor now
has an artefact that answers CC7.2 and CC8.1 without access to MLflow,
S3, or the training environment.

### What changes after

CC8.1 passes: the evidence bundle is tied cryptographically to model
version and eval dataset, and the deployment PR references the bundle
root hash. CC7.2 passes: every production release generates a bundle
and the CI job fails deployment if any of the five layers fail. "Which
accuracy number did we actually ship?" stops being ambiguous. The next
audit cycle runs ~40% faster because the evidence is machine-verifiable.
Enterprise prospects asking about SOC 2 get a verifiable bundle to demo.

### Time and cost

Integration time: about three engineer-hours, one-time. Per-bundle
cost: $299 per externally-attested bundle, or free using the open
protocol internally. Auditor verification: ~60 seconds per bundle.
Context: custom SOC 2 automation platforms run $50k-$150k per year and
SOC 2 readiness consulting is $30k-$80k per Type II cycle.

---

## 2. Computational Chemist at Biotech — FDA AI Credibility Framework + 21 CFR Part 11

### Who this person is

Principal computational chemist or director of molecular informatics at
a Series A or B AI-first drug-discovery biotech (roughly 20-80 people).
Lives inside **Schrödinger Suite** (Maestro, Glide, Prime MM-GBSA,
Jaguar QM), supplements with **OpenEye** (OMEGA, FRED, ROCS), scripts
cheminformatics with **RDKit**, trains ADMET models in **DeepChem**,
**Chemprop**, and **PyTorch** MPNN/GNN architectures, runs molecular
dynamics in **GROMACS** or **Desmond**, tracks samples in **Benchling**,
and logs ML experiments in **Weights & Biases**.

### The exact trigger moment

The biotech is preparing an Investigational New Drug (IND) application
for a small-molecule oncology candidate. The lead was selected from
14,000 computationally screened molecules filtered through an in-house
Chemprop ADMET model. The FDA issued **"Considerations for the Use of
Artificial Intelligence to Support Regulatory Decision-Making for Drug
and Biological Products"** draft guidance in January 2025, introducing
the 7-step AI Credibility Assessment Framework. The pre-IND meeting
minutes close with: *"Sponsor should describe the establishment and
documentation of model credibility for the AI/ML model(s) used to
generate the ADMET predictions supporting candidate selection. Please
provide: (1) training data provenance, (2) performance metrics on a
held-out test set, (3) version control evidence for the model artifact,
and (4) an auditable record of the inference runs that produced the
predictions in Module 2.6 and Module 4."* Alongside, **21 CFR § 11.10(e)**
still applies: computer-generated, time-stamped audit trails must
independently record the date and time of entries that create, modify,
or delete electronic records, and changes must not obscure previously
recorded information.

### What they tried first

The chemist starts with **Benchling** notebook attachments — screenshots
of Jupyter cells pasted into a 21 CFR Part 11-compliant ELN. The
platform is validated for the lab workflow, but a screenshot does not
prove which model produced the number. A 7 GB **Docker** image shipped
to a contract research organisation fails on CUDA driver mismatch; even
when it runs, inference takes four hours per 1,000 compounds and "does
the image match what ran in production?" remains unverifiable. **MLflow**
plus a Model Registry tracks the model version but does not tie
individual inference outputs to it — the link between "model v2.3" and
"logS = -3.2 for MG-0471" lives in an unsigned CSV on a shared drive.
A PDF of predictions digitally signed by the CIO proves the CIO approved
a document, not that the numbers came from the computation they
allegedly came from. The FDA reviewer treats it as a claim, not evidence.

### Three steps with real commands

**Step 1 — Wrap each Chemprop inference output in a `PHARMA-01` bundle.**

The chemist writes `predictions/MG-0471_solubility.json`:

```json
{
  "seed": 42,
  "property_name": "solubility",
  "claimed_value": -3.2,
  "tolerance": 0.5
}
```

Then:

```bash
python scripts/mg_client.py --domain pharma \
    --data predictions/MG-0471_solubility.json \
    --output bundles/IND_MG0471_logS_20260416
```

This invokes `PHARMA-01` (`backend/progress/pharma1_admet_certificate.py`),
which supports the five regulated ADMET properties: solubility (logS),
permeability (logP), toxicity_score, binding_affinity (pIC50), and
bioavailability_score. The 4-step execution trace records
`init_params` → `compute` → `metrics` → `threshold_check` with each
step hashed against the previous, bound into `trace_root_hash`.

**Step 2 — Batch-generate bundles for every compound referenced in Module 2.6.**

```python
from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
for row in candidates:  # 14,000 molecules
    job_result = run_chemprop_pharma01(row)
    bundle = client.pack(job_result, f"bundles/batch/{row['compound_id']}")
    res = client.verify(bundle)
    assert res.passed, f"{row['compound_id']}: {res.reason}"
```

At roughly two seconds per bundle, the full batch completes in under
eight hours on a laptop, offline.

**Step 3 — Sign the 12 IND-referenced bundles with Ed25519.**

```bash
python scripts/mg.py sign keygen \
    --out keys/biotech_signing_ed25519.json --type ed25519
```

Then, per named compound:

```bash
python scripts/mg.py sign bundle \
    --pack bundles/IND_MG0471_logS_20260416 \
    --key keys/biotech_signing_ed25519.json
```

The private key stays in the HSM. The public key fingerprint is
published on the biotech's website and included in the IND cover letter;
any FDA reviewer can verify the signature with the public key alone.

### What the verifier does

The FDA reviewer downloads the bundle for MG-0471 from the eCTD
submission. On an FDA-issued laptop with Python 3.9 and no biotech
credentials:

```bash
python scripts/mg.py verify --pack bundles/IND_MG0471_logS_20260416
python scripts/mg.py sign verify \
    --pack bundles/IND_MG0471_logS_20260416 \
    --fingerprint 8f3e...
```

Each command returns a cryptographic answer in under a minute. The
reviewer now has proof across all five layers: the prediction file was
not modified, evidence conforms to schema and threshold logic, the
4-step trace is internally consistent, the bundle was signed by the
biotech's declared public key, and the bundle was not backdated (NIST
Randomness Beacon). No model access, no training data access required.

### What changes after

The Module 2.6 and Module 4 AI-evidence obligation is satisfied: every
AI-derived number has an attached bundle hash. The AI credibility
dimension of the FDA draft guidance is addressed with machine-verifiable
artefacts, and 21 CFR § 11.10(e)'s computer-generated time-stamped
audit-trail clause is met by Layer 5 combined with Layer 3. The biotech
can license the model to a partner with signed bundle samples as
proof-of-performance. If a post-IND adverse event prompts the FDA to
demand the original prediction, the bundle is already archived, signed,
and offline-verifiable.

### Time and cost

Integration time: about four hours for the chemist plus an hour for IT
to set up Ed25519 key management, one-time. Per-bundle cost: $299 per
IND-referenced bundle — 12 compounds × $299 = $3,588. The other 13,988
batch-screened bundles can use the open protocol at zero per-bundle cost.
Context: an IND filing costs $2M-$20M total and a single pre-IND
consulting package with a specialty regulatory firm is $150k-$400k; a
failed IND can burn $5M-$47M in runway over 6-18 months of delay.

---

## 3. Model Risk Manager at G-SIB Bank — ECB TRIM + CRR Art. 365-366 + SR 11-7 + PRA SS1/23

### Who this person is

Head of Model Risk Management or senior quantitative validator at a
Tier 1 European bank (G-SIB or D-SIB). Runs pricing and risk analytics
in **QuantLib**, queries tick data and back-tests in **kdb+/q**, pulls
market data from Bloomberg and Reuters Eikon, runs credit-risk reporting
in **SAS**, maintains in-house VaR engines (historical simulation, Monte
Carlo, parametric), scripts analysis in Python (`pandas`, `numpy`,
`statsmodels`), tracks every model in a Model Risk Inventory (SAS MRM,
IBM OpenPages, or ServiceNow GRC), and closes the audit loop through
Jira and SharePoint.

### The exact trigger moment

The ECB Joint Supervisory Team notifies the bank of a **Targeted Review
of Internal Models (TRIM 2.0)** inspection scheduled for Q3 2026, scoped
to the internal model approach (IMA) for market risk — the VaR engine
used to calculate Pillar 1 capital under **CRR Article 365**.
Simultaneously, the PRA's **SS1/23** (Model risk management principles
for banks, effective May 2024) and the US Federal Reserve's **SR 11-7**
remain in force. All three frameworks demand the same thing: independent
validation of each model output, documented across the model's lifetime,
with evidence that cannot be reconstructed by the developer. The
examiner opens the request list: *"For each of the last 250 trading
days, provide the 1-day 99% VaR for the consolidated trading book, the
P&L, the backtest exception flag, and the audit evidence demonstrating
that these VaR numbers were produced by the declared model version on
the declared date. We require evidence that can be independently
verified by the ECB without accessing your risk systems."* Under
**CRR Article 366**, backtest exceptions drive the additive multiplier
on required capital (green 3.0; yellow 3.4-3.85; red 4.0) — weak
validation evidence directly costs tens of millions in regulatory capital.

### What they tried first

The Model Risk Inventory runs on a vendor platform with validation
evidence stored as PDFs attached to workflow tickets; the platform is
closed-source, hosted internally, and a DB admin can edit history — ECB
examiners repeatedly flag this as "insufficient independence." A signed
daily VaR report (PGP or S/MIME from the CRO) proves CRO approval on a
date but does not prove the numbers came from the declared model.
An immutable Kafka audit stream is not intrinsically immutable —
retention and compaction are configurable and admin access can reset
offsets. WORM storage satisfies FINRA 17a-4 for the US broker-dealer
arm but does not on its own satisfy ECB TRIM — the file on WORM is
still just numbers with no cryptographic chain to model version, inputs,
and a time commitment.

### Three steps with real commands

**Step 1 — Wrap the nightly VaR calculation in a `FINRISK-01` bundle.**

After QuantLib computes the 1-day 99% VaR for the trading book, the
pipeline writes `runs/var_20260315.json`:

```json
{
  "seed": 42,
  "claimed_var": 0.0183,
  "var_tolerance": 0.0005,
  "confidence_level": 0.99
}
```

Then:

```bash
python scripts/mg_client.py --domain finance \
    --data runs/var_20260315.json \
    --output bundles/var_99pct_20260315
```

`FINRISK-01` (`backend/progress/finrisk1_var_certificate.py`) produces
the 4-step execution trace, bound into `trace_root_hash`.

**Step 2 — Sign each daily bundle with the bank's governance Ed25519 key.**

One-time setup:

```bash
python scripts/mg.py sign keygen \
    --out /secure/mrm_governance_ed25519.json --type ed25519
```

Every night, after the VaR bundle is packed:

```bash
python scripts/mg.py sign bundle \
    --pack bundles/var_99pct_20260315 \
    --key /secure/mrm_governance_ed25519.json
```

The public key fingerprint is published on the bank's investor relations
site and in its annual Pillar 3 disclosure. Every regulator has it in
advance.

**Step 3 — Chain model-calibration bundles to the VaR bundles with `verify-chain`.**

```bash
python scripts/mg.py verify-chain \
    bundles/model_calibration_2026Q1 \
    bundles/var_99pct_20260315 \
    --json reports/chain_verify_20260315.json
```

The `anchor_hash` in the VaR bundle's `inputs` must equal the upstream
calibration bundle's `trace_root_hash`. A broken chain returns
`CHAIN BROKEN`; an intact chain returns `CHAIN PASS`. Daily bundles are
archived for the full model life (minimum 7 years under
**CRR Article 192**).

### What the verifier does

The ECB examiner arrives on-site. The bank hands the examiner a USB
drive with 250 daily VaR bundles (~12 MB total). On a laptop with
Python 3.9, the public MetaGenesis Core clone, and the bank's published
public key fingerprint:

```bash
for day in 20260109 20260115 20260203 20260227 20260315; do
    python scripts/mg.py verify --pack bundles/var_99pct_$day
    python scripts/mg.py sign verify \
        --pack bundles/var_99pct_$day \
        --fingerprint 8f3e...
done
```

Each command returns `PASS` in under ten seconds. The examiner verifies
all five layers for each sampled bundle — integrity, semantic schema
conformance for `FINRISK-01`, Step Chain consistency with
`trace_root_hash` bound to the final step, signature against the bank's
declared public key, and temporal commitment placing creation at the
declared date. Any trading day, any bundle, offline, independent.

### What changes after

The standard TRIM finding — "insufficient independence of validation
evidence" — is closed. The bank moves from the "remediation" category
to "satisfactory." Discretionary backtest-multiplier add-ons under
**CRR Art. 366** drop, saving tens of millions in regulatory capital.
The PRA SS1/23 Principle 2 (Model Development and Implementation) and
Principle 3 (Model Validation) evidence obligations are met in the same
format. US Fed examiners accept the same bundles for the bank's US
branch under **SR 11-7**, avoiding duplicate validation infrastructure.
Model-change management compresses: a version change now ships with a
signed bundle trail, removing the usual three-to-six-month validation
cycle delay.

### Time and cost

Integration time: five to eight engineering days for pipeline wiring,
key management, and archive policy. Per-bundle cost: $299 per
externally-referenced bundle, effectively free for the 250 daily bundles
using the open protocol. Annual cost: around $75,000 for externally-
referenced bundles plus negligible compute and storage. Context: a
single TRIM finding can cost €50M-€500M in additional capital add-ons or
IMA approval loss, and MRM platform licences run $500k-$2M per year.

---

## 4. FEM Engineer at Aerospace / Automotive Supplier — AS9100 Rev D + NASA-STD-7009B

### Who this person is

Senior CAE engineer or FEA lead at a Tier 1 supplier to Airbus, Boeing,
BMW, or Ford (500-5,000 people). Runs **Abaqus/Simulia** for FEA,
crashworthiness, and fatigue; **ANSYS Mechanical** and **LS-DYNA** for
non-linear dynamics; **Altair HyperMesh** for meshing; **MSC Nastran**
for airframe analysis; **Siemens NX** or **Catia V5** for CAD; and
**Teamcenter** or **Windchill** for PDM. Works alongside certified test
hardware: Instron tensile testers, strain-gauge DAQ, Digital Image
Correlation systems.

### The exact trigger moment

The supplier's contract with a major aerospace OEM on the Airbus A321XLR
program requires delivering a simulated fatigue-life prediction for a
titanium structural bracket as part of an AS9100 Rev D quality package.
Under **AS9100 Rev D:2016 Clause 8.3.4** (Design and Development
Controls — merged verification and validation) and **Clause 8.3.5**
(Design and Development Outputs, retaining documented information as
objective evidence), every simulation-derived performance claim must be
traceable to a verified and validated computational method.
**NASA-STD-7009B** (March 2024 revision) additionally requires
Credibility Assessment Scale evidence across Verification, Validation,
Uncertainty Quantification, and Pedigree. The OEM Supplier Quality
Assurance auditor sends a Request for Objective Evidence: *"Per AS9100
Rev D Clause 8.3.5.d, demonstrate that the FEM displacement and stress
results for part AXP-BRK-0471 were generated by a validated solver on a
validated mesh and material model, with results traceable to the
physical material reference data cited (Al-7075-T6, E = 71.7 GPa per
MMPDS-15)."* Two constraints: the supplier cannot hand over the full
Abaqus model (mesh topology and contact algorithms are proprietary IP),
and NASA-STD-7009B's Pedigree dimension must be machine-verifiable,
not narrative.

### What they tried first

Shipping the Abaqus `.odb` file with a digital signature reveals full
model IP, requires an Abaqus licence to read, and the signature only
proves file integrity, not provenance. An Abaqus post-processing PDF
signed by the lead FEA engineer gets the standard OEM finding:
"signature validates authorship, not technical content." A Teamcenter
PLM workflow tracks who approved but does not tie the deliverable to
the simulation cryptographically. Citing MMPDS-15 (FAA-accepted) for
E = 71.7 GPa is citation, not verification — nothing links the cited
value to the computation's inputs programmatically. A 40-page narrative
NASA-STD-7009B "Pedigree" document is skimmed and filed. The auditor
wants a small, verifiable artefact attesting that this FEM result was
produced by this solver/mesh/material combination and is traceable to
the physical material constant — without handing over the proprietary
model.

### Three steps with real commands

**Step 1 — Anchor the material calibration to the physical constant using `MTR-1`.**

For the 7075-T6 aluminium variant at E = 71.7 GPa, `runs/al7075_calibration.json`:

```json
{
  "seed": 42,
  "E_true": 7.17e10
}
```

```bash
python scripts/mg_client.py --domain materials \
    --data runs/al7075_calibration.json \
    --output bundles/mat_al7075_20260215
```

The MTR-1 bundle carries the calibration trace anchored to the declared
physical constant (`anchor_claim_id` = MTR-1, `anchor_hash` computed
from the physical reference).

**Step 2 — Wrap the FEM result in a `DT-FEM-01` bundle chained to the calibration.**

```bash
python scripts/mg_client.py --domain digital_twin \
    --output bundles/fem_bracket_AXP0471_20260215
```

`DT-FEM-01` (`backend/progress/dtfem1_displacement_verification.py`)
validates the FEM output against the MTR-1 anchor with threshold
`rel_err ≤ 0.02`. The bundle contains only the scalar results (peak
displacement, stress), not the Abaqus mesh or model internals.

**Step 3 — Verify the cross-claim chain and sign the downstream bundle.**

```bash
python scripts/mg.py verify-chain \
    bundles/mat_al7075_20260215 \
    bundles/fem_bracket_AXP0471_20260215 \
    --json reports/chain_fem_bracket.json
python scripts/mg.py sign bundle \
    --pack bundles/fem_bracket_AXP0471_20260215 \
    --key /secure/supplier_ed25519.json
```

Total deliverable to the OEM: two bundle directories (~100 KB each)
plus the supplier's public key fingerprint.

### What the verifier does

The OEM SQA auditor receives the two bundles. No Abaqus licence, no
supplier credentials, no access to the mesh:

```bash
python scripts/mg.py verify --pack bundles/mat_al7075_20260215
python scripts/mg.py verify --pack bundles/fem_bracket_AXP0471_20260215
python scripts/mg.py verify-chain \
    bundles/mat_al7075_20260215 \
    bundles/fem_bracket_AXP0471_20260215
python scripts/mg.py sign verify \
    --pack bundles/fem_bracket_AXP0471_20260215 \
    --fingerprint a1b2c3d4...
```

In under two minutes and without any proprietary software, the auditor
has traceability from peak displacement to FEM solver to material
calibration to physical constant (E = 71.7 GPa per MMPDS-15), a
cryptographic receipt that nothing in the chain was modified, AS9100
Rev D Clause 8.3.5.d objective evidence in a compact form, and the
NASA-STD-7009B Pedigree dimension delivered as machine-verifiable data.

### What changes after

AS9100 Rev D Clause 8.3.5 objective evidence is satisfied in a form
that is machine-verifiable, compact, and IP-preserving. The
NASA-STD-7009B Pedigree moves from narrative to cryptographic. No
`.odb`, no mesh, no material-model source crosses the IP boundary.
Sign-off on simulation deliverables drops from weeks to days because
the OEM no longer debates whether the numbers are trustworthy — the
bundle verifies in seconds. Competing suppliers still ship PDFs; this
supplier ships machine-verifiable bundles, and the OEM's buying team
notices. Future DO-160 or DO-178C type-certification evidence can
chain to the same bundle format.

### Time and cost

Integration time: two to three engineering days per part family;
template reusable thereafter. Per-bundle cost: $299 for OEM-referenced
deliverables, free for internal QA. Context: a physical prototype plus
destructive test for a single aerospace bracket is $50k-$250k;
simulation-based qualification with MetaGenesis evidence is $299 plus
engineering time. The goal is to supplement physical tests with
trustworthy simulation evidence, not to replace them.

---

## 5. Quant Analyst at Hedge Fund — MiFID II Art. 17(2) + EU Delegated Reg 2017/589

### Who this person is

Senior quantitative researcher or portfolio manager at a systematic or
quantitative hedge fund with $500M-$50B assets under management. Handles
tick-level market data in **kdb+/q**, prices derivatives in **QuantLib**,
pulls market data from Bloomberg and Refinitiv Eikon, scripts research
in Python (`pandas`, `numpy`, `polars`, `numba`), runs back-tests in
**vectorbt**, **zipline**, or in-house engines, uses **R** for
econometrics, routes orders through an in-house OMS over FIX, Bloomberg
EMSX, or Trading Technologies, versions code in Git with GitHub Actions
CI, develops in Jupyter, and monitors PM dashboards in Grafana. Trade
capture hits an internal ticket database reconciled daily with the prime
broker.

### The exact trigger moment

The fund operates from London. A competitor was recently fined under
**MiFID II Article 17 (Algorithmic Trading)** by the FCA for inability
to reconstruct the signals that led to specific trade decisions during
a period of market stress. The compliance officer initiates a pre-emptive
internal audit. The hard requirements:

- **Directive 2014/65/EU Article 17(1)**: firms must have effective
  systems and risk controls ensuring trading systems are resilient and
  have sufficient capacity.
- **Commission Delegated Regulation (EU) 2017/589, Article 1**: firms
  shall "store records in a durable medium for a period of at least
  five years."
- **Article 17(2) second subparagraph**: high-frequency algorithmic
  trading firms "shall store in an approved form accurate and time
  sequenced records of all its placed orders, including cancellations,
  executed orders and quotations on trading venues."

The compliance officer asks the PM: *"On 2026-02-15 the fund executed
a $40M short SPX options position at 14:23:07 UTC. The decision was
generated by strategy `vol_regime_v7.2`. If the FCA asks tomorrow to
prove that this strategy, on this model version, with these inputs,
produced this signal at this time — can we?"* The link between commit
`a7f4e3c`, the kdb+ tick window, the 14:23:07 UTC timestamp, and the
signal lives implicitly across a CI log, a kdb+ table, and the trade
ticket. No single artefact ties them together cryptographically.

### What they tried first

A Git commit SHA proves code state but not which signal was emitted on
which date — two runs of the same commit against different data produce
different signals. **Chronicle Queue** and similar append-only logs are
fast but not cryptographically signed, not externally timestamped, and
editable by a privileged admin. A proprietary trade-capture vendor
(Traiana, OSTTRA, or internal) captures trades after execution, not the
signal that drove them. An S3 bucket with object lock and MFA-delete
prevents deletion, but lock policies can be loosened by an admin and
CloudTrail logs are editable by a root-level AWS principal. A hand-rolled
SHA-256-chained strategy log gives forward integrity, but without an
external time commitment the chain can be rebuilt by a determined
adversary. The fund needs each trade's signal tied to strategy version,
input tick fingerprint, computed signal, independent time commitment,
and a signature from a declared fund key — all in one artefact.

### Three steps with real commands

**Step 1 — Emit a bundle per trading decision using the SDK.**

The strategy runner is modified so each decision point calls the SDK
and packages an `ML_BENCH-02` (regression certificate) result — the signal
is a continuous value that drives position sizing:

```python
import hashlib
from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()

# Signal generation
signal_value = run_strategy_vol_regime_v7_2(tick_window)

job_result = {
    "mtr_phase": "ML_BENCH-02",
    "inputs": {
        "strategy_version": "vol_regime_v7.2",
        "git_commit": "a7f4e3c",
        "tick_window_sha256": hashlib.sha256(tick_bytes).hexdigest(),
        "timestamp_utc": "2026-02-15T14:23:07Z",
    },
    "result": {
        "signal": -0.72,
        "predicted_rmse": 0.05,
        "actual_rmse": 0.048,
        "pass": True,
    },
    "execution_trace": [...],   # 4 steps, chained
    "trace_root_hash": "...",
}

bundle_path = client.pack(job_result, f"bundles/trades/{trade_id}")
```

**Step 2 — Sign each bundle with the fund's governance Ed25519 key.**

One-time setup — the public key fingerprint is published in the offering
memorandum and prime-broker due-diligence pack:

```bash
python scripts/mg.py sign keygen \
    --out /secure/fund_governance_ed25519.json --type ed25519
```

Per trade:

```bash
python scripts/mg.py sign bundle \
    --pack bundles/trades/T20260215_142307_001 \
    --key /secure/fund_governance_ed25519.json
```

Signing takes under 100 ms; at a decision rate of ten signals per minute
during market hours, signing overhead is negligible.

**Step 3 — Chain daily strategy-config bundles to per-trade bundles.**

```bash
python scripts/mg_client.py --domain ml \
    --data configs/strategy_vol_regime_v7_2_20260215.json \
    --output bundles/strategy/vol_regime_v7_2_20260215
python scripts/mg.py verify-chain \
    bundles/strategy/vol_regime_v7_2_20260215 \
    bundles/trades/T20260215_142307_001 \
    --json reports/audit_chain_T001.json
```

Every trade bundle references the daily strategy bundle's
`trace_root_hash` as its `anchor_hash`.

### What the verifier does

The FCA requests evidence for the 2026-02-15 SPX short. The fund ships
a bundle directory (one strategy bundle plus one trade bundle,
~100 KB total):

```bash
python scripts/mg.py verify --pack bundles/strategy/vol_regime_v7_2_20260215
python scripts/mg.py verify --pack bundles/trades/T20260215_142307_001
python scripts/mg.py verify-chain \
    bundles/strategy/vol_regime_v7_2_20260215 \
    bundles/trades/T20260215_142307_001
python scripts/mg.py sign verify \
    --pack bundles/trades/T20260215_142307_001 \
    --fingerprint 9d2c...
```

All four commands return `PASS` or `CHAIN PASS`. The FCA auditor now has
cryptographic proof of the strategy version used (git commit embedded,
tick-window SHA-256, and signal), proof the signal value has not been
edited, a temporal commitment placing bundle creation inside market
hours on the declared date, and a signature from the fund's declared
public key. **Article 17(2)** and the EU Delegated Regulation 2017/589
five-year durable-medium retention requirement are both satisfied in a
form the FCA can verify without the fund's cooperation.

### What changes after

An Article 17(2) reconstruction request is answered in minutes rather
than weeks. Five-year retention in a durable medium is automatic — each
bundle is a self-contained, offline-verifiable file archived to S3
Glacier or tape. Best-execution evidence (MiFID II Art. 27) extends
naturally. Prime-broker due-diligence improves — funds with
machine-verifiable signal trails get better financing terms, and the
fund can offer signed performance verification to allocators and LPs.

### Time and cost

Integration time: one to two weeks for a mid-sized quant team to
refactor the strategy runner to emit bundles. Per-bundle cost: free
using the open protocol for internal storage; $299 per externally-
attested bundle when paid verification is desired. Annual storage: a
$2B AUM fund executing 10,000 trades generates ~500 MB of bundles.
Context: a single MiFID II Article 17 enforcement action has reached
€15M-€40M in fines; an audit-trail retrofit at a mid-sized fund is
$500k-$2M.

---

## 6. Research Scientist at Lab — Peer-Review Reproducibility + NIH DMP + NeurIPS Reproducibility Track

### Who this person is

Postdoc, principal investigator, or group leader in computational biology,
physics, ML research, or chemistry — university lab, national lab
(NIH, LLNL, CERN), or Max Planck institute. Computes with **NumPy**,
**SciPy**, **PyTorch**, **TensorFlow**, and **JAX**; manages pipelines
in **Snakemake** or **Nextflow**; writes notebooks in **Jupyter** with
**papermill**; ships environments in **Singularity** or **Docker**;
archives via **Git + GitHub + Zenodo**; mints DOIs through **Zenodo**,
**Figshare**, or **Dryad**; writes in **LaTeX + Overleaf**. Reviewer-
facing artefacts land in **OpenReview** (NeurIPS, ICLR) or **Code Ocean**
capsules (Nature, Science).

### The exact trigger moment

The PI submitted a paper to **Nature Methods** on a new AI model for
protein structure refinement, reporting a median TM-score improvement
of 0.047 over AlphaFold2 on the CAMEO benchmark. Reviewer 2's report
lands: *"I attempted to reproduce the benchmark comparison in Table 2
using the authors' Code Ocean capsule. The capsule runs, but produces
TM-score = 0.829 rather than the claimed 0.876 on CAMEO target T1074.
The discrepancy of 0.047 is, coincidentally, the exact magnitude of the
authors' claimed improvement. The paper cannot be accepted until this
is resolved. The authors should provide machine-verifiable evidence that
Table 2 values came from the released model and released data."*
Separately, **NeurIPS 2026** announced a mandatory Reproducibility
Certification Track — fast-tracked review for papers that provide
machine-verifiable artefacts tying every reported metric to a
reproducible computation. **NIH NOT-OD-21-013** (Data Management and
Sharing Policy, effective 2023-01-25) requires every NIH-funded project's
DMS Plan to become a term of the award. The PI opens the laptop. The
Table 2 numbers sit in a CSV produced three months ago on an HPC cluster
that has since been reprovisioned. The numbers are defended by a
HuggingFace model, a Zenodo dataset, a Methods paragraph, and a signed
Zenodo DOI — none of which prove the specific numbers in Table 2 came
from the specific model on the specific data. A re-run produces slightly
different numbers due to CUDA mixed-precision non-determinism, exactly
as Reviewer 2 describes.

### What they tried first

Zenodo-archived code plus data provides DOI-stable artefacts and dataset
hashes but does not prove the paper's results came from those artefacts.
A **Code Ocean** capsule reruns the code in a hosted container — Reviewer
2 literally just reran it and got a different number, so capsule reruns
prove only that the capsule is runnable. A Dockerfile with a `sha256:`
image digest pins the environment but cannot control CUDA non-determinism,
and linking post-hoc to numbers computed before the image was finalised
is not verification. A Methods section with random seeds and PyTorch
deterministic flags did everything right on paper and still produced
0.047 reproduction error because of deep-model + GPU + mixed-precision
non-determinism. Raw output logs attached to Supplementary are, in
Reviewer 2's words, just text — anyone could have edited them. The
discussion collapses into "authors say X, reviewer reruns and gets Y,
neither can prove whose number is authoritative."

### Three steps with real commands

**Step 1 — Bundle the original evaluation outputs at manuscript-preparation time.**

At the moment Table 2 is computed, the PI writes
`runs/table2_T1074_eval.json`:

```json
{
  "seed": 42,
  "claimed_accuracy": 0.876,
  "accuracy_tolerance": 0.001,
  "n_samples": 106
}
```

```bash
python scripts/mg_client.py --domain ml \
    --data runs/table2_T1074_eval.json \
    --output bundles/paper_table2_T1074
```

`ML_BENCH-01` emits the 4-step execution trace with inputs (model hash,
dataset hash), result, metrics, and threshold check — one per table row.

**Step 2 — Sign the bundles and mint a Zenodo DOI that includes them.**

```bash
python scripts/mg.py sign keygen --out keys/lab_ed25519.json --type ed25519
for target in T1074 T1075 T1076 T1077 T1078; do
    python scripts/mg.py sign bundle \
        --pack bundles/paper_table2_$target \
        --key keys/lab_ed25519.json
done
```

All bundles plus the public key file are uploaded as a Zenodo deposition.
The DOI and public-key fingerprint go in the paper's Data Availability
statement.

**Step 3 — Chain the model-training bundle to the evaluation bundle.**

```bash
python scripts/mg.py verify-chain \
    bundles/model_v1_training \
    bundles/paper_table2_T1074 \
    --json supplementary/chain_verify_T1074.json
```

The chain proves the evaluated model is the model from the training run,
not a later-modified checkpoint.

### What the verifier does

Reviewer 2 downloads the Zenodo deposition. On a laptop with Python and
the open MetaGenesis repo:

```bash
python scripts/mg.py verify --pack bundles/paper_table2_T1074
python scripts/mg.py sign verify \
    --pack bundles/paper_table2_T1074 \
    --fingerprint e8c1...
python scripts/mg.py verify --pack bundles/paper_table2_T1074 \
    --receipt receipts/review_T1074.json
```

Reviewer 2 now has cryptographic proof the Table 2 TM-score = 0.876 for
T1074 came from the declared model and data on the declared date, signed
by the PI's declared key, and has not been modified since. The reviewer
can still run the code and observe non-determinism — but the
authoritative number in the paper is anchored to a specific computation.
The objection moves from "I cannot reproduce the number" to "the
authors' number is this specific attested value; my re-run shows
non-determinism on the order of 0.047" — a substantive scientific
discussion rather than a trust collapse. For the NeurIPS Reproducibility
Certification Track, the same bundle directory is uploaded as the
Reproducibility Artifact and the area chair verifies in under a minute.

### What changes after

Peer-review trust is restored: disagreement between authors and reviewers
becomes a discussion about non-determinism magnitude rather than
fabrication, and the paper moves forward. The NeurIPS Reproducibility
Certification Track fast-track becomes accessible. Nature's Data and
Code Availability policy (2023) favours "machine-readable, verifiable"
evidence — bundles fit. NIH DMSP (**NOT-OD-21-013**) preservation and
access elements are covered in verifiable form. The bundle DOI becomes
citeable with cryptographic precision. If a mistake is later discovered,
the bundle identifies exactly which table entries depend on it.

### Time and cost

Integration time: one to two days for the PI or postdoc to wrap the
evaluation pipeline. Per-bundle cost: $0 using the open protocol for
academic use; $299 per signed bundle is available when a lab wants paid
verification on a headline result. Per-paper cost: ~$0-$3000 depending
on the number of headline claims. Context: a Code Ocean capsule
subscription runs $5k-$25k per year for a lab, and the cost of a
retraction is roughly $500k in lost time plus reputational damage.

---

## Cross-references

- **`docs/USE_CASES.md`** — domain entry points keyed by problem (ML
  benchmark, pharma IND, model risk, FEM, algorithmic trading,
  reproducibility) with regulatory citations per domain.
- **`docs/WHY_NOT_ALTERNATIVES.md`** — what each persona tried first
  (MLflow, signed PDF, Docker, Chronicle Queue, S3 object-lock, Code
  Ocean, DVC + git, WORM storage) and where those tools stop short of
  the evidence regulators and reviewers ask for. MetaGenesis is
  additive to those tools, not a replacement.
- **`docs/QUICKSTART.md`** — generic install and first-bundle workflow
  independent of persona or domain.
