# MetaGenesis Core

**A notary for computations.**

*The first cryptographic standard that closes the 80-year gap in digital computation: any result, provably real, anchored to physical law.*

[![Tests](https://img.shields.io/badge/Tests-2407%20passing-brightgreen.svg)](tests/)
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

## A Protocol That Verifies Itself

A verification protocol that cannot verify its own evolution is incomplete. MetaGenesis Core applies its own discipline inward: every commit, every CI run, every documentation update passes through the same gates that external bundles pass through.

The self-verification operates at four levels:

```
Level 1 — CI (every push)     22 automated checks block merge on failure
Level 2 — Memory (post-merge)  agent_learn.py records what changed, what broke, what was fixed
Level 3 — Synthesis (periodic) Patterns promoted to governance rules — human approves
Level 4 — Intentionally absent A system that can rewrite its own rules provides no guarantees
```

Level 4 is missing on purpose. A notary cannot notarize their own documents. A verification system that autonomously adjusts its own success criteria would be circular: it passes because it decided it should pass. The human gate at Level 3 is not a weakness — it is the mechanism that makes everything below it trustworthy.

The numbers are real: 122 agent learning sessions. 11 recurring failure patterns detected, root-caused, and structurally eliminated. Zero ghost patterns remaining. The system reads its own coverage reports and decides what to build next — but a human decides whether to change the rules.

Full architecture: [docs/EVOLUTIONARY_ARCHITECTURE.md](docs/EVOLUTIONARY_ARCHITECTURE.md)

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

## Integration: Not a Standalone Tool

MetaGenesis Core is not a tool you run separately. It is infrastructure that embeds into existing workflows — MLflow, DVC, Evidently, GitHub Actions, or any CI pipeline.

**GitHub Action — zero friction entry point:**

```yaml
# Add one step to any CI pipeline. That's it.
- uses: Lama999901/metagenesis-core-public/.github/actions/verify-bundle@main
  with:
    bundle_path: ./results/bundle.zip
```

Every PR that touches computational results now produces a cryptographic proof. No configuration. No dependencies. No accounts.

**SDK — programmatic verification:**

```python
from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
result = client.verify("bundle/")

result.passed          # True
result.layers          # {"integrity": True, "semantic": True, ...}
result.reason          # "PASS"
result.trace_root_hash # SHA-256 of computation chain
result.claim_id        # "MTR-1"
```

**Standalone verifier — one file, zero dependencies, works forever:**

```bash
python scripts/mg_verify_standalone.py bundle/
# PASS
```

This single file (~580 lines, stdlib only) is the ultimate insurance policy. If MetaGenesis Core disappears tomorrow, this file still verifies every bundle ever created.

Full API reference: [docs/SDK.md](docs/SDK.md)

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

## Drift Calibration: The Category Shift

Most verification asks: *was this file changed?* MetaGenesis asks a different question: *is this computation still anchored to physical reality?*

This is a qualitatively different capability. Without a verified anchor, you cannot know what your simulation is drifting *from*. Drift detection without an anchor is just noise monitoring.

```
January 2026:
  MTR-1 verified:  E = 70 GPa  →  rel_err = 0.3%  →  PASS  →  trusted anchor
  anchor_hash: 8a3f...c7d1

July 2026:
  Same system, same claim, new data:
  E = 76 GPa  →  drift = 8.6%  →  correction_required: True
  anchor_hash: 8a3f...c7d1 (unchanged — drift measured FROM this anchor)
```

The anchor hash from January is baked into July's verification. The protocol does not just detect that a number changed. It proves *how far* the number has moved from a physically anchored reference point. A digital twin that was calibrated last year — is it still calibrated today? A model that passed validation — does it still pass with the updated code? A simulation that met regulatory thresholds — does it still meet them?

```bash
python scripts/mg.py verify-chain bundle_jan2026/ bundle_jul2026/
# CHAIN FAIL: drift exceeds 5% from verified anchor
```

No existing tool does this. Experiment trackers record what happened. Docker reproduces an environment. MetaGenesis proves whether the result still agrees with physical reality. One command. Offline. Cryptographic proof.

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

This is not a prototype.

```
Tests:           2407 passing (3 skipped — platform-specific)
Real ratio:      51.2% (21 verified against real external data / 41 total)
Claims:          20 active across 8 domains
Layers:          5 independent (proven by CERT-11)
Innovations:     8 innovations (patent pending)
Agent checks:    22 agent checks (CI-enforced)
Agent sessions:  122 learning sessions (institutional memory)
Coverage:        87.8%
Bundles:         21 signed and independently verifiable
Dependencies:    Python 3.11+ stdlib only (zero external dependencies)
```

```bash
python scripts/steward_audit.py         # STEWARD AUDIT: PASS
python -m pytest tests/ -q              # 2407 passed
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

2407 tests. Patent filed. 60 days.

There is a deeper paradox here.

AI systems hallucinate. They confabulate. They produce results that sound right but cannot be verified. That is a known weakness.

This project exists because one person looked at that weakness and built the solution using the very tool that has the weakness — then made the tool verify every output it produced.

AI built the verification protocol for AI. Every line generated was tested against itself. Every claim verified by the protocol it was building.

The weakness became the foundation.

Today: 125 agent sessions. 11 failure patterns learned from the system's own mistakes, root-caused, and structurally eliminated. An evolution engine that watches itself build. Level 3 autonomous: the system reads its own coverage reports and decides what to build next. A human decides whether to change the rules.

If this is possible, what isn't?

Built with Claude (Anthropic). Every AI output verified by the project's own test suite.

**The protocol verifies the protocol.**
**The builder verifies the builder.**

**Site:** https://metagenesis-core.dev
**Email:** yehor@metagenesis-core.dev
**Sponsor:** https://github.com/sponsors/Lama999901

---

## The World That Awaits

Standards do not emerge because someone decides the world needs one. They emerge when three conditions coincide: a universal problem, a simple solution, and a moment of urgency.

git became the standard for code. Before git — zip archives and trust. DOI became the standard for publications. Before DOI — URLs that break. HTTPS became the default for the web. Before Let's Encrypt — certificates were expensive and optional.

The pattern is the same. The standard succeeds not because it is technically superior but because it introduces a primitive simple enough to be universal. `git commit` is one command. A DOI is one string. HTTPS is one protocol.

`python scripts/mg.py verify --pack bundle.zip` is one command.

The verification gap is universal: every domain produces computational claims that everyone must trust. The solution is simple: stdlib Python, 60 seconds, offline, zero dependencies. The urgency is real: FDA Q2 2026, EU AI Act August 2026, Basel III active now, reproducibility crisis measured and documented for a decade.

All three conditions have coincided. The trajectory is not aspirational — it is structural:

```
Level 1 — Protocol (now)         Any result verified in 60 seconds
Level 2 — Standard (2026)        Regulatory submissions include bundles
Level 3 — Infrastructure (2027)  Expected, like DOI for papers
Level 4 — Universal (2028+)      Default, like HTTPS for the web
```

The question will shift from "should we verify this result?" to "why wasn't this result verified?"

Full roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## License

MIT — free to use, modify, deploy.
Patent pending: protocol innovations are protected.
Commercial licensing available for organizations building on the protocol.

---

## Deep Reading

| Document | What it answers |
|----------|----------------|
| [The Verification Gap](docs/VISION.md) | Why every computational result needs a tamper-evident artifact |
| [Proof, Not Trust](docs/PHILOSOPHICAL_FOUNDATION.md) | The epistemological foundation — why cryptographic proof is categorically different from trust |
| [Evolutionary Architecture](docs/EVOLUTIONARY_ARCHITECTURE.md) | How the protocol verifies its own evolution |
| [Client Journey](docs/CLIENT_JOURNEY.md) | 6 persona journeys from trigger moment to integrated workflow |
| [Roadmap](docs/ROADMAP.md) | Protocol → Standard → Infrastructure → Universal |
| [Regulatory Gaps](docs/REGULATORY_GAPS.md) | FDA, EU AI Act, Basel III coverage assessment |
| [SDK Reference](docs/SDK.md) | Full API, GitHub Action, real-world examples |
| [Use Cases](docs/USE_CASES.md) | 14 domains × real incidents × exact regulatory citations × verified 3-step integration |
| [Why Not Alternatives](docs/WHY_NOT_ALTERNATIVES.md) | Composability matrix (10 tools), CERT-02 walk-through, rerun-cost math |

## For AI Agents

```
1. CLAUDE.md              ← mission, rules, traps
2. AGENTS.md              ← hard rules, protected files
3. CONTEXT_SNAPSHOT.md    ← current state
4. reports/known_faults.yaml ← limitations
```

---

*MetaGenesis Core v1.0.0-rc1 | 2407 tests | 51.2% real | Patent Pending #63/996,819*
