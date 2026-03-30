# Use Cases

MetaGenesis Core applies to any domain where a computational result
must be verified independently, without access to the original environment.

---

## 1. ML benchmark and AI accuracy claims

**The problem:** Every ML team claims state-of-the-art results. Reviewers
cannot check without re-running training — which requires the original
compute, data, and environment. Published accuracy numbers are routinely
inflated, cherry-picked, or evaluated on leaked test sets.

**What MetaGenesis Core does:** Package the model's predictions
(y_true / y_pred CSV) into a tamper-evident bundle. SHA-256 fingerprint
the dataset. Any reviewer runs one command and gets PASS or FAIL.

```bash
# Claim: model achieves 94.3% accuracy on this test set
result = run_certificate(
    dataset_relpath="predictions/model_v3_test.csv",
    claimed_accuracy=0.943
)
# Bundle includes: dataset fingerprint, predictions, metrics, provenance
# Verifier runs: mg.py verify --pack bundle.zip → PASS or FAIL
```

**Who needs this:** ML research teams, AI product companies, benchmark
organizers, regulators reviewing AI system submissions (EU AI Act,
FDA AI/ML guidance for Software as a Medical Device).

---

## 2. Pharmaceutical and clinical computational submissions

**The problem:** Drug discovery and clinical trials increasingly rely on
computational models — ADMET predictions, pharmacokinetic simulations,
biomarker analysis. Regulators (FDA 21 CFR Part 11, EMA) require
audit trails but existing infrastructure is expensive and proprietary.

**What MetaGenesis Core does:** Package any computational model output
into a verifiable bundle. The bundle contains the full provenance chain —
inputs, algorithm version, result — in a form any regulator can verify
offline. No proprietary tools required.

**Target claim types:**
- IC50 / binding affinity predictions
- PK/PD simulation outputs
- Clinical trial outcome model validation
- Safety signal detection algorithm outputs

**Who needs this:** Biotech and pharma computational chemistry teams,
CROs submitting computational evidence to regulators, clinical trial
data management organizations.

---

## 3. Carbon credit and ESG model verification

**The problem:** Carbon credits are issued based on computational models
— satellite imagery analysis, deforestation algorithms, carbon
sequestration estimates. These models are opaque. Auditors cannot verify
the outputs without the original proprietary software.

The market for voluntary carbon credits is in crisis precisely because
there is no credible independent verification standard for the underlying
computations.

**What MetaGenesis Core does:** Any carbon model output becomes a
verifiable bundle. Third-party auditors — corporate ESG teams, rating
agencies, regulators — verify offline without access to the proprietary
model. The bundle is tamper-evident.

**Target claim types:**
- Deforestation rate estimates (hectares / year)
- Carbon sequestration model outputs (tonnes CO₂e)
- Satellite-derived land-use change metrics

**Who needs this:** Carbon project developers, voluntary carbon market
registries (Verra, Gold Standard), ESG rating agencies, corporate buyers
requiring credible offset documentation.

---

## 4. Financial risk model validation

**The problem:** Banks and asset managers run risk models (VaR, credit
scoring, stress testing) that regulators must validate. Basel III/IV
requires model risk management. Current validation is expensive,
proprietary, and manual.

**What MetaGenesis Core does:** Financial model outputs are packaged
into verifiable bundles. Regulators and internal model risk teams
verify specific claim outputs — VaR estimates, loss given default,
scenario analysis results — without re-running the full model.

**Target claim types:**
- Value at Risk (VaR) computation outputs
- Credit model PD/LGD/EAD estimates
- Stress test scenario results
- Algorithmic trading strategy backtests

**Who needs this:** Bank model risk management teams, regulatory
technology (regtech) vendors, internal audit functions, central bank
supervisory teams.

---

## 5. Materials science and engineering calibration

**The original domain.** Simulation-based design — finite element
analysis, molecular dynamics, thermal simulation — produces calibrated
material property claims that other teams depend on.

**What MetaGenesis Core does:** Calibration results (Young's modulus,
thermal conductivity, contact resistance) are packaged into verifiable
bundles. Engineering teams hand off simulation results to clients and
regulators with independent verification proof.

**The physical anchor principle.** MTR-1's anchor — E = 70 GPa for
aluminum — is not a threshold invented by the protocol. It is a physical
constant measured independently in thousands of laboratories worldwide.
When MetaGenesis Core verifies rel_err ≤ 1% against this anchor, it is
verifying that the computation agrees with physical reality, not merely
that a number falls within an arbitrary range.

This is the key distinction: traceability to physical measurement,
not threshold compliance.

The full chain is independently verifiable:
```
Physical reality:  E = 70 GPa  (measured, not assumed)
        ↓
MTR-1:   computational model → rel_err ≤ 1% vs. physical constant → PASS
        ↓
DT-FEM-01: FEM solver output verified against MTR-1 anchor → rel_err ≤ 2% → PASS
        ↓
DRIFT-01:  ongoing deviation from anchor → drift ≤ 5% → PASS
```

Any third party verifies the entire chain with one command:
```
mg.py verify --pack mtr1_bundle.zip → PASS
```

Active claims: MTR-1 (Young's modulus), MTR-2 (thermal paste conductivity),
MTR-3 (multilayer thermal contact), DT-FEM-01 (FEM displacement vs. anchor),
DRIFT-01 (drift monitoring).

**Who needs this:** Materials science labs, aerospace and automotive
simulation teams, AI materials prediction companies needing manufacturing
partner trust, component qualification for safety-critical applications.

---

## 6. Digital twin calibration verification

**The problem:** Digital twins — simulation models that mirror physical
systems in real time — require continuous calibration against physical
measurements. A twin claiming 1% accuracy from a structural FEM solver,
a thermal CFD model, or a materials simulation has no standard way to
prove that claim to clients, regulators, or partner teams. The calibration
result exists as a number in a report. Nothing ties it to the computation
that produced it.

**What MetaGenesis Core does:** Every calibration step becomes a
tamper-evident evidence bundle. The physical reference measurement and
the simulation output are packaged together with SHA-256 fingerprints,
provenance metadata, and a verified threshold. A third party verifies
the entire calibration chain offline with one command.

The protocol supports the full digital twin lifecycle:
Physical measurement → MTR-1 (anchor: E = 70 GPa, rel_err ≤ 1%) → PASS
FEM solver output   → DT-FEM-01 (vs. reference, rel_err ≤ 2%) → PASS
Drift monitoring    → DRIFT-01 (current vs. anchor, drift ≤ 5%) → OK
↓ drift > 5% → correction_required = True
Iteration           → new calibration → rel_err decreasing → provably closer to reality

Each step in the chain is independently verifiable. The chain is
tamper-evident. Any reviewer — client, regulator, partner — runs:
```bash
mg.py verify --pack calibration_bundle.zip → PASS or FAIL
```

No FEM solver access required. No simulation environment. No trust.

**Target claim types:**
- Structural displacement vs. lab measurement (DT-FEM-01)
- Material property calibration vs. physical constants (MTR-1/2/3)
- Thermal field vs. thermocouple readings
- System identification vs. measured impulse response (SYSID-01)
- Calibration drift against verified anchor (DRIFT-01)

**Who needs this:** Aerospace and automotive simulation teams handing
off FEM results to clients, materials science labs with ongoing calibration
workflows, medical device manufacturers requiring simulation evidence for
regulatory submissions (FDA, CE), engineering firms building digital twins
of industrial equipment, research groups publishing simulation-backed
physical claims.

---

## 6. Pharma / Biotech — ADMET prediction and regulatory submissions

**The problem:** Computational ADMET predictions (solubility, permeability, toxicity, binding affinity, bioavailability) are central to drug discovery but have no standard verifiable format. FDA's 2025 AI/ML guidance and EU AI Act require documented, auditable computational evidence.

**What MetaGenesis Core does:** Package any ADMET prediction as a tamper-evident evidence bundle with FDA 21 CFR Part 11 alignment note. Any reviewer — internal auditor, FDA inspector, partner lab — verifies offline.

**Relevant claim:** PHARMA-01 — 5 properties: solubility (logS), permeability (logP), toxicity_score, binding_affinity (pIC50), bioavailability_score.

**Price:** $299 per bundle. Trivial against nine-figure drug development budgets.

---

## 7. Finance / Risk — Model validation and Basel compliance

**The problem:** VaR models and credit scoring models require independent validation under Basel III/IV. Model Risk Management (SR 11-7) mandates documented, reproducible validation evidence. Existing tools produce reports — not machine-verifiable evidence.

**What MetaGenesis Core does:** Package VaR model output with confidence level, observation count, and portfolio ID into a tamper-evident bundle. Any validator verifies the claim offline without accessing the model.

**Relevant claim:** FINRISK-01 — historical VaR at specified confidence level (default 99%).

---

## 8. IoT / Digital Twin — Sensor data integrity

**The problem:** IoT sensor streams feeding digital twins are vulnerable to data corruption, out-of-range values, and timestamp anomalies. There is no standard way to certify that a sensor data stream was valid at the time of ingestion.

**What MetaGenesis Core does:** Package sensor stream validation (schema + range + temporal consistency) with SHA-256 fingerprint into an evidence bundle. Downstream consumers verify data integrity without re-running the pipeline.

**Relevant claim:** DT-SENSOR-01 — 5 sensor types: temperature, pressure, displacement, strain, voltage.

---

## Common pattern across all domains

The verification workflow is identical regardless of domain:

```
1. Computation runs → produces result
2. result + provenance → evidence bundle (mg.py pack build)
3. Bundle sent to third party
4. Third party: mg.py verify --pack bundle.zip → PASS or FAIL
```

No GPU. No environment access. No trust.

The only thing that changes per domain is the claim type and V&V thresholds.

---

*Use Cases v0.8 — 2026-03-30 — MetaGenesis Core — 20 claims, 601 tests*
