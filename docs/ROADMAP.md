# Roadmap — From Protocol to Infrastructure

**Current version:** v1.0.0-rc1
**Protocol:** MetaGenesis Verification Protocol (MVP) v1.0
**DOI:** [10.5281/zenodo.19521091](https://doi.org/10.5281/zenodo.19521091)

MetaGenesis Core follows a four-level evolution path. Each level builds
on the previous one. The goal is not features — it is adoption. A
verification protocol that nobody uses verifies nothing.

---

## Level 1 — Protocol (NOW, v1.0.0-rc1)

The protocol works. It is complete, tested, and independently verifiable.

**What exists today:**
- 20 domain verification templates across 8 domains
- 5 independent verification layers (integrity, semantic, step chain, signing, temporal)
- 2407 adversarial tests, 22 automated evolution checks
- SDK: `from sdk.metagenesis import MetaGenesisClient` — verify in 3 lines
- GitHub Action: one-line CI integration for any repository
- Ed25519 bundle signing with temporal commitment (NIST Beacon)
- Physical anchors: SI 2019 exact constants (kB, NA) + NIST-measured properties
- Zenodo DOI for academic citation
- MIT License — anyone can verify, anyone can contribute

**What this means:** Any computational result in ML, pharma, finance,
engineering, or science can be packaged into a tamper-evident bundle
and verified offline by anyone with one command in 60 seconds.

---

## Level 2 — Standard (2026)

The protocol becomes a recognized way to document computational results.

**Milestones:**
- [ ] First paying client ($299) — proof the market exists
- [ ] First regulatory submission using MetaGenesis bundle
- [ ] JOSS paper published (target: Sep 2026, 6-month public history met)
- [ ] Integration with major ML framework (DVC, Evidently, or MLflow)
- [ ] FDA/EU AI Act compliance documentation using bundles
- [ ] 3+ organizations using protocol in pilot programs

**Regulatory context:**
- FDA guidance on AI/ML in drug development: Q2 2026
- EU AI Act enforcement: August 2, 2026
- Basel III model risk management: active now
- All three create demand for independently verifiable computational artifacts

---

## Level 3 — Infrastructure (2027)

The protocol becomes expected — like DOI for papers or git for code.

**Milestones:**
- [ ] MetaGenesis verification accepted by Basel III validators
- [ ] FDA accepts bundles as part of IND filing workflow
- [ ] 10+ organizations using protocol in production
- [ ] Non-provisional patent granted (deadline: 2027-03-05)
- [ ] Reference implementations in TypeScript and Rust
- [ ] Public bundle registry for reproducibility research

---

## Level 4 — Universal (2028+)

Any computational result in any domain has a MetaGenesis bundle as a
matter of course — like any paper has a DOI, any codebase has git.

The verification gap is closed.

---

## What We Will NOT Do

- Build a simulation platform (we verify outputs, not run computations)
- Add AI-generated code without adversarial test proof
- Add claims without the full 6-step lifecycle
- Use absolute or unverifiable security claims
- Claim to solve reproducibility (we solve verifiability — see SCOPE_001)

---

## Domain Expansion Path

**Live domains (20 claims):**
Materials (MTR-1 through MTR-6), ML/AI (ML_BENCH-01/02/03),
Digital Twin (DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01),
Pharma (PHARMA-01), Finance (FINRISK-01), System ID (SYSID-01),
Data Pipelines (DATA-PIPE-01), Drift Monitoring (DRIFT-01, AGENT-DRIFT-01),
Physics (PHYS-01, PHYS-02)

**Planned domains:**
- Carbon/ESG: sequestration estimate, deforestation rate certificates
- Additional ML: multi-class F1, LLM evaluation (BLEU/ROUGE/perplexity)
- Additional Pharma: PK/PD simulation certificates
- Additional Finance: credit scoring, stress testing
- Additional Digital Twin: CFD output verification, structural modal analysis

---

## How to Contribute

Open an issue with the label `roadmap` describing:
- Which domain or use case you need
- What the claim would verify
- Whether you can provide a reference dataset or test case

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.
