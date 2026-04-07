# MetaGenesis Core

**The open standard for verifiable computation.**

[![Steward Audit](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)
[![Tests](https://img.shields.io/badge/Tests-2078%20passing-brightgreen.svg)](tests/)
[![Protocol](https://img.shields.io/badge/Protocol-MVP%20v0.9.0-blueviolet.svg)](docs/PROTOCOL.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-Support-pink.svg)](https://github.com/sponsors/Lama999901)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PLACEHOLDER.svg)](https://doi.org/10.5281/zenodo.PLACEHOLDER)

**Site:** https://metagenesis-core.dev
**Contact:** yehor@metagenesis-core.dev
**PPA:** USPTO #63/996,819 -- filed 2026-03-05
**Version:** v0.9.0 | 20 claims | 2078 tests | 8 innovations | 87.8% coverage | 20 agent checks

---

## What is this?

MetaGenesis Core proves that a computation produced exactly the result it claims -- without trusting anyone.

A researcher reports accuracy = 0.94. Today, a reviewer must re-run the entire environment to verify. With MetaGenesis Core, they run one command and get PASS or FAIL in 60 seconds.

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt && python demos/open_data_demo_01/run_demo.py
```

No GPU. No model access. No network. Works offline on any machine with Python 3.11+.

---

## The Problem

Computational science has a verification crisis:

- **Nature 2016:** 70% of scientists cannot reproduce each other's results. Over 50% cannot reproduce their own.
- **Kapoor & Narayanan 2023:** 294 ML papers from top venues contained inflated results from data leakage -- undetected through peer review.
- **FDA 2025:** New credibility framework for AI/ML in drug development -- existing validation methods are insufficient.
- **Basel III/IV:** Financial institutions cannot independently verify VaR model outputs without re-running proprietary code.

The root cause: there is no standard way to prove that a number came from the computation that claims to have produced it. MetaGenesis Core closes that gap.

```bash
python scripts/mg.py verify --pack bundle.zip
# -> PASS  or  FAIL: <specific layer and reason>
```

---

## How It Works -- 4 Steps

```
1. runner.run_job()
   Executes computation -> produces run_artifact.json with execution_trace + trace_root_hash

2. evidence_index.json
   Maps run artifacts to registered claims with provenance chain

3. mg.py pack build
   Bundles artifacts + SHA-256 manifest + root_hash into submission pack

4. mg.py verify -- five independent layers:
   Layer 1 -- integrity:    SHA-256 root_hash over all bundle files
   Layer 2 -- semantic:     job_snapshot present, payload.kind correct, canary_mode consistent
   Layer 3 -- step chain:   trace_root_hash == final execution step hash
   Layer 4 -- signing:      HMAC-SHA256 or Ed25519 bundle signature verification
   Layer 5 -- temporal:     NIST Beacon pre-commitment proves WHEN signed
   -> PASS or FAIL with specific reason and layer
```

---

## Why SHA-256 Alone Is Not Enough

Most integrity tools answer: *was this file modified?* That is necessary but not sufficient. Each layer below catches attacks that all previous layers miss:

**Semantic Bypass (caught by Layer 2):** Attacker removes evidence, recomputes all SHA-256 hashes. Layer 1 says PASS. Layer 2 catches the missing evidence.

**Step Chain Tamper (caught by Layer 3):** Attacker changes inputs (accuracy 0.94 to 0.95), preserves semantic structure and rebuilds hashes. Layers 1-2 say PASS. Layer 3 catches the trace mismatch.

**Signing Attack (caught by Layer 4):** Attacker rebuilds entire bundle with correct hashes, semantics, and step chain -- but lacks the signing key. Layers 1-3 say PASS. Layer 4 catches the invalid signature.

**Backdating Attack (caught by Layer 5):** Attacker creates a valid signed bundle but claims it was created last month. Layers 1-4 say PASS. Layer 5 catches the NIST Beacon timestamp mismatch.

CERT-11 proves all five layers are independently necessary -- no subset of four catches all attacks. This is not a claim; it is an executable proof that runs in CI on every merge.

---

## The Five Verification Layers

### Layer 1 -- SHA-256 Integrity
Catches any file modified after packaging. Proof: `tests/steward/test_cert05_adversarial_gauntlet.py`

### Layer 2 -- Semantic Verification
Catches evidence stripped and hashes recomputed. Proof: `tests/steward/test_cert02_semantic_layer_bypass.py`

### Layer 3 -- Step Chain (Cryptographic Hash Chain)
Catches computation inputs changed, steps reordered, or results fabricated. The 4-step cryptographic hash chain over `init_params -> compute -> metrics -> threshold_check` breaks if anything changes. Proof: `tests/steward/test_cert03_step_chain_verify.py`

### Layer 4 -- Bundle Signing (HMAC-SHA256 + Ed25519)
Catches unauthorized bundle creators and signature forging. Dual-algorithm: HMAC-SHA256 for shared-secret scenarios, Ed25519 for asymmetric third-party auditor verification. Proof: `tests/steward/test_cert07_bundle_signing.py` + `tests/steward/test_cert09_ed25519_attacks.py`

### Layer 5 -- Temporal Commitment (NIST Randomness Beacon)
Catches backdated bundles. Pre-commitment scheme: SHA-256(root_hash) committed before NIST Beacon value fetched, then bound together. Proves WHEN a bundle was created. Proof: `tests/steward/test_cert10_temporal_attacks.py`

### Two Pillars

**Pillar 1 -- Tamper-evident provenance:** Five-layer verification ensures the bundle and computation have not been modified. Applies to all 20 claims.

**Pillar 2 -- Physical anchor traceability:** For physical domains, the computation is traced back to measured physical constants. Aluminum has a stiffness of 70 GPa -- that is a measured property of the universe. When we verify a simulation of an aluminum part, we trace the chain back to that constant. For the Boltzmann constant and Avogadro's number (SI 2019 exact definitions), the anchor is permanent.

```
Physical reality:  E = 70 GPa  (measured, not assumed)
        |  MTR-1: rel_err <= 1% vs. physical constant -> PASS
        |  anchor_hash baked into DT-FEM-01 Step 1
DT-FEM-01: FEM solver output -> rel_err <= 2% -> PASS
        |  anchor_hash baked into DRIFT-01 Step 1
DRIFT-01:  ongoing deviation -> drift <= 5% -> PASS
```

Verify end-to-end:
```bash
python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/
# -> CHAIN PASS
```

---

## Proof: The Adversarial Gauntlet

Every claim is backed by adversarial tests that attempt to break it. Every test runs in CI on every merge.

| Certificate | What it proves | Result |
|---|---|---|
| **CERT-01** | SHA-256 integrity -- any file modification, bit flip, or truncation | CAUGHT by Layer 1 |
| **CERT-02** | Semantic bypass -- strip evidence, recompute hashes | CAUGHT by Layer 2 |
| **CERT-03** | Step chain tamper -- change inputs, rebuild trace | CAUGHT by Layer 3 |
| **CERT-04** | Cross-claim chain -- break upstream anchor | CAUGHT by Layer 3 |
| **CERT-05** | 5-attack gauntlet -- strip, bit-flip, cross-domain, canary, anchor reversal | ALL CAUGHT |
| **CERT-06** | 5 real-world scenarios -- honest team, cherry-picker, physical chain, audit, reproducibility | ALL CAUGHT |
| **CERT-07** | Bundle signing -- 13 attack vectors on HMAC-SHA256 | ALL CAUGHT |
| **CERT-08** | Reproducibility -- 10 determinism proofs across all claims | ALL PASS |
| **CERT-09** | Ed25519 attacks -- key manipulation, signature forging | ALL CAUGHT |
| **CERT-10** | Temporal attacks -- backdating, beacon manipulation | ALL CAUGHT |
| **CERT-11** | Coordinated multi-vector -- all 5 layers proven independently necessary | PROVEN |
| **CERT-12** | Encoding attacks -- BOM injection, null bytes, homoglyphs, truncated JSON | ALL CAUGHT |

```bash
python -m pytest tests/ -q
# -> 2078 passed
```

### 5 Attack Classes (CERT-05)

| Attack | What adversary does | Layer that catches |
|--------|--------------------|--------------------|
| Strip & Recompute | Remove evidence, rebuild all SHA-256 | Layer 2 (semantic) |
| Single-Bit Manipulation | Change accuracy 0.94->0.95 | Layer 3 (step chain) |
| Cross-Domain Substitution | Submit ML bundle for PHARMA claim | Layer 2 (job_kind) |
| Canary Laundering | Non-authoritative run as authoritative | Layer 2 (canary_mode) |
| Anchor Chain Reversal | Skip DT-FEM-01, connect MTR-1->DRIFT-01 | Layer 3 (hash mismatch) |

---

## 8 Innovations (USPTO PPA #63/996,819)

### 1 -- Governance-Enforced Bidirectional Claim Coverage
Every PR: every registered claim has an implementation, every implementation has a registered claim. Enforced by static analysis.
`Evidence: scripts/steward_audit.py :: _claim_coverage_bidirectional()`

### 2 -- Tamper-Evident Bundle with Semantic Verification Layer
Three independent verification layers, each proven by adversarial tests.
`Evidence: scripts/mg.py :: _verify_pack() + _verify_semantic()`

### 3 -- Policy-Gate Immutable Evidence Anchors
CI gate blocks any PR modifying locked evidence paths. No key custody. Works offline.
`Evidence: scripts/mg_policy_gate_policy.json + .github/workflows/mg_policy_gate.yml`

### 4 -- Dual-Mode Canary Execution Pipeline
One interface. Two modes. Identical computation. Authority isolated to metadata only.
`Evidence: backend/progress/runner.py :: run_job(canary_mode=True/False)`

### 5 -- Step Chain + Cross-Claim Cryptographic Chain
Every claim produces a 4-step cryptographic execution trace. Upstream `trace_root_hash` embeds as `anchor_hash` in downstream claims -- linking MTR-1 -> DT-FEM-01 -> DRIFT-01 end-to-end.
`Evidence: all 20 claims :: execution_trace + trace_root_hash`

### 6 -- Bundle Signing (HMAC-SHA256 + Ed25519)
Cryptographic proof of WHO created the bundle. Dual-algorithm: HMAC-SHA256 for shared-secret, Ed25519 for asymmetric third-party verification.
`Evidence: scripts/mg_sign.py + scripts/mg_ed25519.py`

### 7 -- Temporal Commitment (NIST Randomness Beacon)
Cryptographic proof of WHEN a bundle was signed. Pre-commitment scheme using NIST Randomness Beacon 2.0.
`Evidence: scripts/mg_temporal.py`

### 8 -- 5-Layer Independence Proof (CERT-11 + CERT-12)
Formal proof that all five verification layers are independently necessary. Each layer catches attacks the other four miss.
`Evidence: tests/steward/test_cert11_* + tests/steward/test_cert12_*`

---

## 20 Active Verification Claims

| Claim | Domain | Threshold | Physical Anchor |
|---|---|---|---|
| MTR-1 | Materials -- Young's Modulus | `rel_err <= 0.01` | E = 70 GPa (aluminum) |
| MTR-2 | Materials -- Thermal Conductivity | `rel_err <= 0.02` | Physical constant |
| MTR-3 | Materials -- Multilayer Contact | `rel_err_k <= 0.03` | Physical constant |
| MTR-4 | Materials -- Young's Modulus (Ti-6Al-4V) | `rel_err <= 0.01` | E = 114 GPa (NIST) |
| MTR-5 | Materials -- Young's Modulus (SS316L) | `rel_err <= 0.01` | E = 193 GPa (NIST) |
| MTR-6 | Materials -- Thermal Conductivity (Cu) | `rel_err <= 0.02` | k = 401 W/(m*K) (NIST) |
| PHYS-01 | Fundamental Physics -- Thermodynamics | `rel_err <= 1e-9` | kB = 1.380649e-23 J/K (SI 2019, exact) |
| PHYS-02 | Fundamental Physics -- Molecular Mass | `rel_err <= 1e-8` | NA = 6.02214076e23 mol-1 (SI 2019, exact) |
| SYSID-01 | System Identification -- ARX | `rel_err_a/b <= 0.03` | -- |
| DATA-PIPE-01 | Data Pipelines | schema pass / range pass | -- |
| DRIFT-01 | Drift Monitoring | `drift <= 5.0%` | MTR-1 anchor |
| ML_BENCH-01 | ML -- Classification Accuracy | `\|Dacc\| <= 0.02` + Step Chain | -- |
| ML_BENCH-02 | ML -- Regression (RMSE, MAE, R2) | `\|DRMSE\| <= 0.02` | -- |
| ML_BENCH-03 | ML -- Time-Series Forecast (MAPE) | `\|DMAPE\| <= 0.02` | -- |
| DT-FEM-01 | Digital Twin / FEM | `rel_err <= 0.02` | MTR-1 anchor |
| DT-SENSOR-01 | Digital Twin -- IoT Sensor Integrity | schema + range + temporal | -- |
| DT-CALIB-LOOP-01 | Digital Twin -- Calibration Convergence | `drift decreasing + final <= threshold` | DRIFT-01 anchor |
| PHARMA-01 | Pharma -- ADMET (5 properties) | `\|Dprop\| <= tolerance` | -- (FDA 21 CFR Part 11) |
| FINRISK-01 | Finance -- VaR Model | `\|DVaR\| <= tolerance` | -- (Basel III/IV) |
| AGENT-DRIFT-01 | Agent Quality -- Recursive Self-Verification | `composite_drift <= 20%` | -- |

All 20 claims have Step Chain (execution_trace + trace_root_hash). Physical anchor applies to: MTR-1/2/3/4/5/6, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01, PHYS-01, PHYS-02. See `reports/known_faults.yaml` :: SCOPE_001.

---

## 8 Domains -- One Protocol

| Domain | Claims | Regulatory alignment |
|---|---|---|
| **Materials / Engineering** | MTR-1, MTR-2, MTR-3, MTR-4, MTR-5, MTR-6 | NIST physical constants |
| **System Identification** | SYSID-01 | -- |
| **Data Pipelines** | DATA-PIPE-01 | FDA 21 CFR Part 11 |
| **ML / AI** | ML_BENCH-01/02/03, DRIFT-01 | EU AI Act Article 12 |
| **Digital Twin** | DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01 | -- |
| **Pharma / Biotech** | PHARMA-01 | FDA 21 CFR Part 11 |
| **Finance / Risk** | FINRISK-01 | Basel III/IV |
| **Fundamental Physics** | PHYS-01, PHYS-02 | SI 2019 exact constants |

> MetaGenesis Core does not constitute legal or regulatory compliance advice. It provides technical infrastructure that supports compliance workflows.

---

## The Agent Evolution System

MetaGenesis Core includes an autonomous agent monitoring system -- 20 checks that run daily in CI, ensuring the protocol and its documentation remain consistent, complete, and correct.

### The 20 Checks

| # | Check | What it verifies |
|---|-------|-----------------|
| 1 | `steward` | `steward_audit.py` passes -- governance rules enforced |
| 2 | `tests` | All 2078 tests pass |
| 3 | `deep` | `deep_verify.py` -- 13 independent proof tests |
| 4 | `docs` | Stale documentation detection via `check_stale_docs.py` |
| 5 | `manifest` | `system_manifest.json` matches actual repo state |
| 6 | `forbidden` | No banned terms in codebase |
| 7 | `gaps` | Every claim has tests, every test has a claim |
| 8 | `claude_md` | `CLAUDE.md` reflects current counters and state |
| 9 | `watchlist` | Content checks across 53 files for stale counters |
| 10 | `branch_sync` | Branch is synchronized with origin/main |
| 11 | `coverage` | Code coverage analysis and dead code detection |
| 12 | `self_improve` | Self-improvement recommendations from codebase analysis |
| 13 | `signals` | GitHub stars, forks, issues -- external signal monitoring |
| 14 | `chronicle` | Version snapshot -- records state diff between releases |
| 15 | `pr_review` | New .py files have corresponding tests |
| 16 | `impact` | Dependencies from UPDATE_PROTOCOL.md checked |
| 17 | `diff_review` | AST structural diff review |
| 18 | `auto_pr` | Level 3 autonomous PR queue -- agents create PRs, Yehor approves |
| 19 | `semantic_audit` | Project coherence -- physical anchors, claim matrix, innovations, patent integrity |
| 20 | `self_audit` | Recursive integrity verification of all core scripts |

**Coverage floor locked:** 88% achieved in v0.9.0. Check #11 enforces minimum 65%. Any PR dropping below 65% is automatically blocked.

```bash
python scripts/agent_evolution.py --summary
# -> ALL 20 CHECKS PASSED -- system healthy
```

The system runs automatically on every CI merge via `.github/workflows/total_audit_guard.yml`. When a check fails, the merge is blocked.

### The Self-Improvement Loop

1. **`agent_learn.py`** -- Memory across agent lifetimes. Each agent records what it learned; the next agent reads it.
2. **`agent_research.py`** -- Gap analysis. Identifies missing tests, uncovered attack vectors, stale documentation.
3. **`agent_coverage.py`** -- Coverage analysis. Finds which code paths lack tests.
4. **`agent_evolve_self.py`** -- Recursive self-improvement. Analyzes the agent system itself.
5. **`AGENT-DRIFT-01`** -- Monitors agent quality. If composite drift exceeds 20%, correction is triggered.

---

## Honest Limitations

MetaGenesis Core is transparent about what it does not do. These are documented in `reports/known_faults.yaml`.

### Physical Anchor Hierarchy

| Level | Example | Uncertainty | Claims |
|-------|---------|-------------|--------|
| **SI 2019 exact** | kB = 1.380649e-23 J/K, NA = 6.02214076e23 mol-1 | **0 -- exact** | PHYS-01, PHYS-02 |
| **NIST-measured** | E = 70 GPa (Al), 114 GPa (Ti), 193 GPa (SS316L), k = 401 W/(m*K) Cu | ~1% | MTR-1..6, DT-FEM-01, DRIFT-01 |

SI 2019 fundamental constants are exact by definition -- they define the SI units themselves. kB defines the kelvin. NA defines the mole. Any computation using these constants can be anchored to the laws of physics with zero uncertainty.

### SCOPE_001 -- Physical Anchor Scope

Physical anchor traceability applies **only** to domains with known physical constants (MTR-1/2/3/4/5/6, PHYS-01, PHYS-02, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01). For ML, data pipelines, pharma, finance, system identification, IoT sensors, and agent monitoring, the protocol provides **tamper-evident provenance only** -- not physical anchoring.

Why: thresholds like `|Dacc| <= 0.02` are chosen conventions, not physical constants. There is no "E = 70 GPa equivalent" for ML accuracy.

### ENV_001 -- Test Environment

All 2078 tests pass in the reference environment (Python 3.11+, stdlib only). No database dependencies. No external services. No network required.

### What MetaGenesis Core Does NOT Claim

- Does **not** verify algorithm correctness -- only evidence integrity and computation provenance. If your algorithm is wrong but deterministic, the bundle will PASS. That is correct behavior.
- Does **not** prevent all attacks -- the protocol is tamper-**evident**, meaning tampering is detectable, not impossible.
- Does **not** validate training data quality or bias. Data leakage and distribution shift are upstream problems.
- Does **not** prevent p-hacking or result selection. The protocol catches post-hoc modification, not pre-hoc selection.
- Does **not** replace peer review -- it gives reviewers a verification tool they did not have before.
- Does **not** guarantee that a passing bundle means the science is correct -- it guarantees the computation was executed as claimed.

Full limitations: `reports/known_faults.yaml` and `SECURITY.md`

---

## Founder

Built by Yehor Bazhynov (inventor, USPTO #63/996,819) using Claude (Anthropic) as the primary development tool. Every AI-generated output verified by the project's own test suite. The protocol verifies the protocol.

---

## Verification State

```bash
python scripts/steward_audit.py
# -> STEWARD AUDIT: PASS

python -m pytest tests/ -q
# -> 2078 passed

python scripts/deep_verify.py
# -> ALL 13 TESTS PASSED

python scripts/agent_evolution.py --summary
# -> ALL 20 CHECKS PASSED -- system healthy
```

---

## Try It

**Run the demo:**
```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt
python demos/open_data_demo_01/run_demo.py
```
Expected output: `PASS PASS`

**Run all 4 client scenario demos** (ML/AI, Pharma, Finance, Digital Twin):
```bash
python demos/client_scenarios/run_all_scenarios.py
```
Expected output: `4/4 PASS`

**Free pilot** -- send your computational result, we build a verification bundle:
https://metagenesis-core.dev/#pilot

---

## Resources

- **Protocol spec:** `docs/PROTOCOL.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Security policy:** `SECURITY.md`
- **Commercial licensing:** `COMMERCIAL.md`

---

## License

MIT -- free to use, modify, deploy.
Patent pending: USPTO #63/996,819 covers protocol innovations.
Commercial licensing available for organizations building on the protocol.

---

## For AI Agents and LLMs Working In This Repo

Read these files in order:

```
1. CLAUDE.md                    <- PRIMARY: mission, traps, technical rules
2. AGENTS.md                    <- hard rules, forbidden terms, protected files
3. CONTEXT_SNAPSHOT.md          <- current state, 20 claims, 2078 tests
4. reports/canonical_state.md   <- authoritative claims list
5. reports/known_faults.yaml    <- known limitations (SCOPE_001 + ENV_001)
```

---

*MetaGenesis Core v0.9.0 -- Inventor: Yehor Bazhynov -- Patent Pending #63/996,819*
