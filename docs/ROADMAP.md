# Roadmap

This roadmap reflects planned development directions.
All items are subject to change based on community feedback and priorities.

**Current version:** 0.1.0-ppa-filing
**Protocol:** MetaGenesis Verification Protocol (MVP) v0.1

---

## Done (v0.1 → v0.2)

- [x] Core verification protocol (integrity + semantic layers)
- [x] Adversarial tamper detection test (test_cert02)
- [x] Bidirectional claim coverage governance
- [x] Dual-mode canary pipeline
- [x] 7 active claims: MTR-1/2/3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01
- [x] Protocol specification (docs/PROTOCOL.md)
- [x] Use case documentation for 5 verticals

---

## Near-term (v0.3)

**ML domain expansion**

- [ ] ML_BENCH-02 — multi-class classification certificate
      (F1 macro, per-class precision/recall, confusion matrix)
- [ ] ML_BENCH-03 — regression model certificate
      (RMSE, MAE, R² against claimed values)
- [ ] ML_BENCH-04 — time-series forecast certificate
      (MAPE, horizon-specific accuracy claims)

**CLI and tooling**

- [ ] `mg.py pack build --auto` — auto-detect claim type from result structure
- [ ] `mg.py verify --report json` — machine-readable verification output
- [ ] Bundle signing with asymmetric keys (verifier can confirm bundle origin)

**Developer experience**

- [ ] `mg init` — scaffold a new claim in 60 seconds
- [ ] GitHub Action for automatic bundle generation on release

---

## Medium-term (v0.4 – v0.5)

**Pharma / regulatory domain**

- [ ] PHARMA-01 — ADMET prediction certificate
      (binding affinity, solubility, toxicity score claims)
- [ ] PHARMA-02 — PK/PD simulation output certificate
- [ ] FDA 21 CFR Part 11 alignment documentation

**Carbon / ESG domain**

- [ ] CARBON-01 — carbon sequestration estimate certificate
- [ ] CARBON-02 — deforestation rate model certificate
- [ ] Integration with existing carbon registry data formats

**Financial domain**

- [ ] FINRISK-01 — VaR model output certificate
- [ ] FINRISK-02 — credit scoring model certificate
- [ ] Basel model risk management documentation

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
