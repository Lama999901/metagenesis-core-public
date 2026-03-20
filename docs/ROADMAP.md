# Roadmap

This roadmap reflects planned development directions.
All items are subject to change based on community feedback and priorities.

**Current version:** 0.5.0
**Protocol:** MetaGenesis Verification Protocol (MVP) v0.5

**Core principle:** MetaGenesis Core verifies that computational results
agree with physical reality — not just that numbers weren't changed.
Where physical constants exist (E = 70 GPa, thermal conductivity values,
measured reference data), the verification chain is anchored to them.
This is traceability to physical measurement, not threshold compliance.

---

## Done (v0.1 → v0.3)

- [x] Core verification protocol (integrity + semantic layers)
- [x] Adversarial tamper detection test (test_cert02)
- [x] Bidirectional claim coverage governance
- [x] Dual-mode canary pipeline
- [x] 8 active claims: MTR-1/2/3, SYSID-01, DATA-PIPE-01, DRIFT-01,
      ML_BENCH-01, DT-FEM-01
- [x] Protocol specification (docs/PROTOCOL.md v0.2)
- [x] Architecture documentation (docs/ARCHITECTURE.md v0.2)
- [x] Step Chain Verification in ALL 14 claims (4-step execution trace)
- [x] Cross-Claim Cryptographic Chain (MTR-1 → DT-FEM-01 → DRIFT-01)
- [x] anchor_hash validation in mg.py verify
- [x] verify-chain CLI command
- [x] ML_BENCH-02 — regression certificate (RMSE, MAE, R²)
- [x] ML_BENCH-03 — time-series forecast certificate (MAPE)
- [x] PHARMA-01 — ADMET prediction certificate (FDA 21 CFR Part 11)
- [x] FINRISK-01 — VaR model certificate (Basel III/IV)
- [x] DT-SENSOR-01 — IoT sensor data integrity certificate
- [x] DT-CALIB-LOOP-01 — calibration convergence certificate
- [x] 526 adversarial tests, steward_audit PASS
- [x] CERT-07 Bundle Signing (HMAC + Ed25519)
- [x] CERT-08 Reproducibility as cryptographic property
- [x] CERT-09 Ed25519 attacks
- [x] CERT-10 Temporal attacks
- [x] CERT-11 5-layer independence proof (coordinated multi-vector)
- [x] CERT-12 Encoding attacks (BOM, null bytes, homoglyphs)
- [x] Agent Evolution System (agent_learn.py + agent_evolution.py)
- [x] JOSS paper (paper.md ready for submission)
- [x] CERT-05 Adversarial Gauntlet (5 attack scenarios documented and caught)
- [x] CERT-06 Real-World Scenarios (5 proof stories end-to-end)
- [x] GitHub Sponsors configured

---

## Near-term (v0.3)

**ML domain expansion**

- [ ] ML_BENCH-04 — multi-class classification (F1 macro, per-class precision/recall)
- [ ] ML_BENCH-05 — LLM evaluation certificate (BLEU, ROUGE, perplexity)

**CLI and tooling**

- [ ] `mg.py pack build --auto` — auto-detect claim type from result structure
- [ ] Bundle signing with asymmetric keys (verifier can confirm bundle origin)
- [ ] `mg init` — scaffold new claim in 60 seconds

**Developer experience**

- [ ] GitHub Action for automatic bundle generation on release

---

## Medium-term (v0.4 – v0.5)

**Pharma / regulatory domain**

- [x] PHARMA-01 — ADMET prediction certificate (✅ live)
- [ ] PHARMA-02 — PK/PD simulation output certificate
- [ ] FDA 21 CFR Part 11 alignment documentation

**Carbon / ESG domain**

- [ ] CARBON-01 — carbon sequestration estimate certificate
- [ ] CARBON-02 — deforestation rate model certificate
- [ ] Integration with existing carbon registry data formats

**Financial domain**

- [x] FINRISK-01 — VaR model output certificate (✅ live)
- [ ] FINRISK-02 — credit scoring model certificate
- [ ] Basel model risk management documentation

---

## Digital Twin Verification Path (v0.6+)

MetaGenesis Core is the universal verification layer for computational
scientific claims. Digital twin calibration is the highest-value
application: every step from physical measurement to simulation output
to drift monitoring becomes independently verifiable.

**DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01** are live (526 tests PASS).

Next claims in the digital twin path:

- [ ] DT-CFD-01 — CFD output vs. physical measurement
      (pressure, velocity, temperature fields — rel_err per quantity)
- [ ] DT-MODAL-01 — structural modal analysis vs. experimental FRF
      (natural frequency match within threshold)

**Architecture note:** MetaGenesis Core does NOT implement FEM solvers,
CFD engines, or any simulation platform. It verifies the OUTPUT of any
external simulator against physical reference measurements.
The verified result becomes a trusted anchor for DRIFT-01 monitoring.

---

## Long-term (v1.0)

**Protocol standardization**

- [ ] MVP v1.0 spec with formal schema validation
- [ ] Reference implementations in Python, TypeScript, Rust
- [ ] Protocol adoption by at least one external organization

**Interoperability**

- [ ] Bundle import/export compatibility with DVC, MLflow, W&B
- [ ] ONNX model prediction certificate integration
- [ ] CML (Continuous Machine Learning) GitHub Action integration

**Infrastructure**

- [ ] Public bundle registry (opt-in, for reproducibility research)
- [ ] Bundle verification as a service API

---

## What we will NOT do

- Build a simulation platform
- Add AI-generated code without adversarial test proof
- Add claims without the full lifecycle: implementation + test + governance
- Use absolute or unverifiable security claims (see PROTOCOL.md)

---

## How to contribute to the roadmap

Open an issue with the label `roadmap` describing:
- Which domain or use case you need
- What the claim would verify
- Whether you can provide a reference dataset or test case

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.
