# MetaGenesis Core

**A notary for computations.**

*The first cryptographic standard that closes the 80-year gap in digital computation: any result, provably real, anchored to physical law.*

[![Tests](https://img.shields.io/badge/Tests-2405%20passing-brightgreen.svg)](tests/)
[![Real Ratio](https://img.shields.io/badge/Real%20Verified-51.2%25-blue.svg)](proof_library/)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19521091.svg)](https://doi.org/10.5281/zenodo.19521091)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Steward Audit](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)

---

Like a notary certifies a document, MetaGenesis Core certifies that a computer produced exactly this result, at exactly this time, in exactly this way.

Without access to the computer. Without trusting anyone. In 60 seconds.

```bash
python scripts/mg.py verify --pack bundle.zip
# PASS  or  FAIL: <specific layer and reason>
```

---

## The Problem

Every day, billions of computations produce numbers that everyone must simply trust.

An ML model reports 94% accuracy. A simulation says the bridge holds. A drug calculation passes. A risk model says all clear. A carbon credit is issued. A digital twin says the turbine is calibrated.

Who checks?

**Nature 2016:** 70% of scientists cannot reproduce each other's results.
**Kapoor & Narayanan 2023:** 294 ML papers from top venues had undetected inflated results.
**FDA 2025:** Existing AI/ML validation methods declared insufficient for drug development.
**Basel III/IV:** Banks cannot independently verify risk model outputs without re-running proprietary code.

There is no standard of proof for computation. MetaGenesis Core is that standard.

---

## The Physical Anchor

This is not just a verification tool. It is a trust layer anchored to physical reality.

```
kB = 1.380649e-23 J/K    (SI 2019, exact by definition — defines the kelvin)
NA = 6.02214076e23 mol-1  (SI 2019, exact by definition — defines the mole)
```

These constants were fixed in 2019. They will never change. They are properties of the universe, not decisions of any institution.

Every verification chain that starts here outlasts every company, every government, every standard body. When we verify that a simulation of an aluminum part agrees with E = 70 GPa (measured independently in thousands of laboratories worldwide), we are not checking against a threshold someone chose. We are checking against physical reality.

```
Physical reality:  E = 70 GPa  (aluminum, measured)
        ↓
MTR-1:  Calibration    → rel_err ≤ 1%     → PASS
        ↓  anchor_hash baked in
DT-FEM-01: FEM solver  → rel_err ≤ 2%     → PASS
        ↓  anchor_hash baked in
DRIFT-01: Monitoring    → drift ≤ 5%       → PASS
```

Change any link in the chain. The cryptographic hash breaks everywhere downstream.

---

## Five Independent Layers

Each layer catches attacks that all previous layers miss. This is not a claim. It is an executable proof (CERT-11) that runs in CI on every merge.

| Layer | Catches | Proof |
|-------|---------|-------|
| **1. SHA-256 Integrity** | Any file modified after packaging | CERT-01 |
| **2. Semantic** | Evidence stripped, hashes recomputed | CERT-02 |
| **3. Step Chain** | Inputs changed, steps reordered, results fabricated | CERT-03 |
| **4. Signing** (HMAC + Ed25519) | Unauthorized bundle creator, forged signatures | CERT-07, CERT-09 |
| **5. Temporal** (NIST Beacon) | Backdated bundles | CERT-10 |

No subset of four layers catches all attacks. CERT-11 proves this with coordinated multi-vector attacks. CERT-12 adds encoding attacks: BOM injection, null bytes, homoglyphs, truncated JSON.

---

## How It Works

```
1. Compute          runner.run_job() executes the computation
                    → produces execution_trace + trace_root_hash

2. Package          mg.py pack bundles artifacts + SHA-256 manifest
                    → self-contained .zip with root_hash

3. Sign             mg_ed25519.py signs the bundle (WHO created it)
                    mg_temporal.py binds to NIST Beacon (WHEN it was created)

4. Verify           mg.py verify --pack checks all 5 layers
                    → PASS or FAIL with specific layer and reason
```

The bundle is the proof. It travels with the result. Anyone verifies it. Offline. Any machine.

---

## The Adversarial Gauntlet

Every claim is backed by adversarial tests that attempt to break it. Every test runs in CI on every merge.

| Certificate | What it proves | Attacks |
|-------------|---------------|---------|
| **CERT-02** | Semantic bypass detection | Strip evidence, recompute hashes |
| **CERT-03** | Step chain integrity | Change inputs, rebuild trace |
| **CERT-05** | 5-attack gauntlet | Strip, bit-flip, cross-domain, canary, anchor reversal |
| **CERT-06** | 5 real-world scenarios | Honest team, cherry-picker, physical chain, audit, reproducibility |
| **CERT-07** | Bundle signing | 13 attack vectors on HMAC-SHA256 |
| **CERT-08** | Reproducibility | 10 determinism proofs across all claims |
| **CERT-09** | Ed25519 attacks | Key manipulation, signature forging |
| **CERT-10** | Temporal attacks | Backdating, beacon manipulation |
| **CERT-11** | 5-layer independence | Coordinated multi-vector — proves all layers necessary |
| **CERT-12** | Encoding attacks | BOM injection, null bytes, homoglyphs, truncated JSON |

These are not unit tests. They are adversarial proofs. Each one simulates a real attacker with a specific strategy. Each one fails without the layer it tests.

---

## Try It Now

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt

# Run a domain demo with real verified bundles
python scripts/mg_demo.py --domain materials
```

Expected output: 6 materials claims verified through all 5 layers. PASS for each. Human-readable receipt saved to `demos/receipts/materials_receipt.txt`.

No GPU. No model access. No network. Works offline on any machine with Python 3.11+.

**Verify a single bundle yourself:**
```bash
python scripts/mg.py verify --pack demos/open_data_demo_01/
# PASS PASS
```

**Or use the standalone verifier — one file, zero dependencies:**
```bash
python scripts/mg_verify_standalone.py demos/open_data_demo_01/
# PASS
```

---

## Talk to the Protocol

Any person. Any language. Any domain.

Clone the repo. Bring your own Claude API key (anthropic.com/api).
Run one command:

```bash
python scripts/mg_onboard.py --api-key YOUR_KEY
```

The system detects your language. Understands what you compute.
Runs live verification. Explains the result. In your language.

A materials scientist in Tokyo.
A pharma researcher in Madrid.
A quant in London.
A student curious about cryptography.

All get the same protocol. All get the same proof.

Your API key. Your conversation. Your data stays yours.

---

## The Killer Application: Drift Detection

Compare a verification bundle from today against one from a year ago.

Same system. Same claim. Different result. Caught automatically.

```bash
python scripts/mg.py verify-chain bundle_jan2026/ bundle_jan2027/
# CHAIN FAIL: drift exceeds 5% from verified anchor
```

No existing tool does this. Experiment tracking records what happened. MetaGenesis proves whether it still agrees with physical reality.

A digital twin that was calibrated last year — is it still calibrated today? A model that passed validation — does it still pass with new data? A simulation that met regulatory thresholds — does it still meet them after the code was updated?

One command. Offline. Cryptographic proof.

---

## Eight Domains. One Protocol.

| Domain | Claims | What it verifies |
|--------|--------|-----------------|
| **Materials Science** | MTR-1 through MTR-6 | Young's modulus, thermal conductivity against NIST constants |
| **Fundamental Physics** | PHYS-01, PHYS-02 | Boltzmann constant (kB), Avogadro's number (NA) — SI 2019 exact |
| **Digital Twin** | DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01 | FEM displacement, IoT sensor integrity, calibration convergence |
| **ML / AI** | ML_BENCH-01/02/03 | Classification accuracy, regression RMSE, time-series MAPE |
| **Pharma / Biotech** | PHARMA-01 | ADMET property prediction (FDA 21 CFR Part 11) |
| **Finance / Risk** | FINRISK-01 | Value-at-Risk model validation (Basel III/IV) |
| **Data Pipelines** | DATA-PIPE-01 | Schema and range validation certificates |
| **System Identification** | SYSID-01 | ARX model calibration |

20 claims. 21 verified bundles. 51.2% verified against real external data.

---

## The Evolution

MetaGenesis Core is not a product. It is infrastructure. Four levels, each building on the last.

### Level 1 — Protocol *(shipped, v0.9.0)*

Any computation verified in 60 seconds. 5 layers. 20 claims. Physical anchors. Offline.
*Trigger to next level: first paying client.*

### Level 2 — Registry

Every verified bundle gets a persistent DOI via Zenodo. Scientists publish the proof alongside the paper. "Was this computation verified?" becomes a searchable question with a cryptographic answer.
*Trigger to next level: 5 paying clients across 2 verticals.*

### Level 3 — Agent Economy

AI agents verify each other's outputs through the protocol. Agent A produces a result. Agent B verifies it. Neither trusts the other. Both trust the physics.
*Trigger to next level: 100+ bundles verified, institutional adoption.*

### Level 4 — Self-Evolution

The protocol verifies its own development. Every code change passes through MetaGenesis before merging. The system that certifies others is itself certified — recursively.

| Level | What it proves | Who trusts it |
|-------|---------------|---------------|
| Protocol | This computation was not tampered with | One client |
| Registry | This computation has a permanent, citable record | Journals |
| Agent Economy | Autonomous systems can trust each other's outputs | AI labs |
| Self-Evolution | The verification system itself is verified | Everyone |

---

## The Deeper Vision

Every simulation is a claim about physical reality.

Molecular dynamics says this material behaves this way. FEM says this structure holds under this load. A digital twin says the turbine is still calibrated. A drug calculation says this compound has these properties.

Boeing builds in digital before metal. Rolls-Royce runs engines in simulation before they exist. Quantum chemistry calculates molecules before synthesis. The infrastructure for verified digital reality already exists.

What was missing: trust. Every simulation is an assertion that anyone must simply accept — or re-run the entire environment to check. There was no standard of proof.

MetaGenesis Core is that standard. The notary layer between digital and physical reality.

When every simulation is anchored to SI 2019 constants — when aluminum in a digital model is cryptographically proven to behave like aluminum in the physical world — we stop simulating reality and start proving it.

Verified digital laboratories. Zero-cost experiments. Digital twins that cannot lie. Science that proves itself.

kB = 1.380649e-23 J/K. Defined 2019. Will never change. Build on that, and what you build outlasts everything.

---

## Questions the Protocol Answers

**"Did this computation really produce this result?"**
→ PASS: yes, cryptographically proven.
→ FAIL: here is which layer broke and why.

**"Was this result fabricated after the fact?"**
→ NIST Beacon proves the exact moment of creation.

**"Who created this bundle?"**
→ Ed25519 signature proves the creator.

**"Is this simulation still calibrated after a year?"**
→ Drift monitoring against verified anchor answers continuously.

**"Can a regulator verify this without seeing our model?"**
→ Yes. Bundle contains proof, not the model.
→ One command. Offline. No model access needed.

**"What if MetaGenesis Core disappears tomorrow?"**
→ Nothing changes. MIT license. Zero dependencies.
→ mg_verify_standalone.py is one file that verifies forever.

---

## Honest Limitations

These make the protocol more credible, not less.

**Physical anchors apply only where physics exists.** ML accuracy, financial risk, pharma properties — these use chosen thresholds, not physical constants. For those domains, MetaGenesis provides tamper-evident provenance. It proves the computation happened as claimed. It does not anchor it to physical reality. (Documented: `reports/known_faults.yaml` :: SCOPE_001)

**Tamper-evident, not tamper-proof.** The protocol detects modification. It does not prevent it. A determined attacker who controls the entire computation environment can produce a fraudulent-but-consistent bundle. The protocol catches post-hoc tampering, not pre-hoc fraud.

**Correctness is not verified.** If your algorithm is wrong but deterministic, the bundle will PASS. That is correct behavior. The protocol certifies that this computation produced this result — not that the result is scientifically correct.

**Not a replacement for peer review.** It gives reviewers a tool they did not have before. The science still needs to be evaluated by humans.

Full limitations: `reports/known_faults.yaml` and `SECURITY.md`

---

## The Numbers

```
Tests:           2405 passing (3 skipped — platform-specific)
Real ratio:      51.2% (21 verified against real external data / 41 total)
Claims:          20 active across 8 domains
Layers:          5 independent (proven by CERT-11)
Innovations:     8 innovations (patent pending)
Agent checks:    22 agent checks (CI-enforced)
Coverage:        87.8%
Bundles:         21 signed and independently verifiable
Dependencies:    Python 3.11+ stdlib only (zero external dependencies)
```

```bash
python scripts/steward_audit.py         # STEWARD AUDIT: PASS
python -m pytest tests/ -q              # 2405 passed
python scripts/deep_verify.py           # ALL 13 TESTS PASSED
python scripts/agent_evolution.py       # ALL 22 CHECKS PASSED
```

---

## For Organizations

**Free pilot:** Send your computational result. We build a verification bundle. You decide if it's useful.
https://metagenesis-core.dev/#pilot — no obligation, 24-48 hours.

**If you're in ML/AI:** Your benchmark claims become independently verifiable without exposing models or data. EU AI Act Article 12 requires audit trails.

**If you're in pharma:** Your computational submissions become FDA 21 CFR Part 11 compatible audit artifacts. A $299 bundle vs. a $47M raise to prove credibility.

**If you're in finance:** Your VaR model outputs become independently verifiable by regulators. Basel III/IV compliance without re-running proprietary code.

**If you're in engineering:** Your FEM/CFD simulation results are anchored to physical constants. Clients verify offline. Digital twin calibration is cryptographically proven.

**Price:** $299 per verification bundle | Pipeline integration: $2,000-5,000 | Ongoing: $500-2,000/month
Full details: `COMMERCIAL.md`

**Security model:** `SECURITY.md` | **Protocol spec:** `docs/PROTOCOL.md` | **Contact:** yehor@metagenesis-core.dev

---

## 8 Patent-Pending Innovations

| # | Innovation | What it does |
|---|-----------|-------------|
| 1 | Bidirectional Claim Coverage | Every claim has an implementation. Every implementation has a claim. Enforced by static analysis. |
| 2 | Semantic Verification Layer | Catches evidence-strip attacks that bypass SHA-256 integrity. |
| 3 | Policy-Gate Immutable Anchors | CI blocks modification of locked evidence paths. No key custody. |
| 4 | Dual-Mode Canary Pipeline | One interface, two modes, identical computation. Authority isolated to metadata. |
| 5 | Step Chain + Cross-Claim Chain | 4-step cryptographic trace per claim. Upstream hashes embed in downstream claims. |
| 6 | Bundle Signing (HMAC + Ed25519) | Proves WHO created the bundle. Dual-algorithm for shared-secret and asymmetric scenarios. |
| 7 | Temporal Commitment (NIST Beacon) | Proves WHEN a bundle was signed. Pre-commitment prevents backdating. |
| 8 | 5-Layer Independence Proof | Formal proof that no subset of four layers catches all attacks. |

USPTO Provisional Patent Application #63/996,819 | Filed 2026-03-05 | Inventor: Yehor Bazhynov

---

## Built By

Yehor Bazhynov — inventor, USPTO #63/996,819.

Construction worker by day. Built this after shifts and weekends. No CS degree. No team. No funding.

2405 tests. Patent filed. 60 days.

There is a deeper paradox here.

AI systems hallucinate. They confabulate. They produce results that sound right but cannot be verified. That is a known weakness.

This project exists because one person looked at that weakness and built the solution using the very tool that has the weakness — then made the tool verify every output it produced.

AI built the verification protocol for AI. Every line generated was tested against itself. Every claim verified by the protocol it was building.

The weakness became the foundation.

If this is possible, what isn't?

Built with Claude (Anthropic). Every AI output verified by the project's own test suite.

**The protocol verifies the protocol.**
**The builder verifies the builder.**

**Site:** https://metagenesis-core.dev
**Email:** yehor@metagenesis-core.dev
**Sponsor:** https://github.com/sponsors/Lama999901

---

## License

MIT — free to use, modify, deploy.
Patent pending: protocol innovations are protected.
Commercial licensing available for organizations building on the protocol.

---

## For AI Agents

```
1. CLAUDE.md              ← mission, rules, traps
2. AGENTS.md              ← hard rules, protected files
3. CONTEXT_SNAPSHOT.md    ← current state
4. reports/known_faults.yaml ← limitations
```

---

*MetaGenesis Core v0.9.0 | 2405 tests | 51.2% real | Patent Pending #63/996,819*
