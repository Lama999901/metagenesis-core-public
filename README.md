# MetaGenesis Core

**The Omnissiah's Protocol for Computational Truth.**

[![Steward Audit](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)
[![Tests](https://img.shields.io/badge/Tests-595%20passing-brightgreen.svg)](tests/)
[![Protocol](https://img.shields.io/badge/Protocol-MVP%20v0.7.0-blueviolet.svg)](docs/PROTOCOL.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-pink.svg)](https://github.com/sponsors/Lama999901)

**Site:** https://metagenesis-core.dev
**Contact:** yehor@metagenesis-core.dev
**PPA:** USPTO #63/996,819 -- filed 2026-03-05  
**Version:** v0.7.0 | 20 claims | 601 tests | 17 agent checks | 18/18 tasks done

---

## The Creed

> *In the grim darkness of unverifiable computation, one protocol stands between truth and fabrication.*

The machine spirit demands proof. Every claim verified. Every hash chained. Every step traced. No trust required -- only evidence. The protocol does not ask you to believe. It asks you to verify.

```bash
python scripts/mg.py verify --pack bundle.zip
# -> PASS  or  FAIL: <specific reason and layer>
```

One command. Five layers. 60 seconds. Offline.

---

## The Problem

Computational science has a verification crisis. The numbers are real:

- **Nature 2016 survey:** 70% of scientists reported they cannot reproduce each other's experimental results. Over 50% cannot reproduce their own.
- **Kapoor & Narayanan 2023:** 294 ML papers from top venues contained inflated results caused by data leakage -- train/test contamination that went undetected through peer review.
- **NeurIPS 2025 Leaderboard Illusion:** Systematic benchmark gaming documented across major ML competitions. Models optimized for leaderboard position rather than real-world performance.
- **FDA 2025:** New credibility framework for AI/ML in drug development -- acknowledging that existing validation methods are insufficient for computational claims in regulated industries.
- **Basel III/IV compliance gaps:** Financial institutions cannot independently verify VaR model outputs without re-running proprietary code in proprietary environments.

**The root cause is simple:** there is no standard way to prove that a number came from the computation that claims to have produced it.

Consider what happens today:
- A researcher reports accuracy = 0.94. The reviewer sees the number. There is no way to verify it without re-running the code in the original environment -- which may require specific hardware, proprietary data, or hours of compute time.
- A pharmaceutical company submits a computational drug interaction model. The FDA reviewer must trust the output or demand full environment reproduction.
- A financial institution reports a VaR calculation. The regulator cannot independently verify it without the bank's proprietary codebase.

Every ML team, every lab, every data pipeline produces computational claims every day. A reviewer must either re-run your entire environment (impractical) or trust the number you reported (unverifiable). MetaGenesis Core closes that gap.

```bash
python scripts/mg.py verify --pack bundle.zip
# One command. Offline. No trust required.
# -> PASS  or  FAIL: <specific layer and reason>
```

---

## Why SHA-256 Alone Is Not Enough

Most integrity tools answer one question: *was this file modified?* That is necessary but nowhere near sufficient. Here is a concrete attack that SHA-256 alone cannot catch:

**The Semantic Bypass Attack:**
```
1. Attacker removes job_snapshot from the run artifact
2. Attacker recomputes ALL SHA-256 hashes over remaining files
3. Layer 1 (integrity): PASS -- all hashes match
4. Layer 2 (semantic):  FAIL -- job_snapshot missing, evidence stripped
```
This attack is not theoretical. It is implemented, automated, and caught on every CI merge:
`tests/steward/test_cert02_*::test_semantic_negative_missing_job_snapshot_fails_verify`

**The Step Chain Attack -- bypasses Layers 1 and 2:**
```
1. Attacker changes computation inputs (e.g., accuracy 0.94 -> 0.95)
2. Attacker recomputes hashes AND preserves semantic structure
3. Layer 1 (integrity): PASS -- hashes rebuilt correctly
4. Layer 2 (semantic):  PASS -- all required fields present
5. Layer 3 (step chain): FAIL -- trace_root_hash does not match final step
```
Proven in CI: `tests/steward/test_cert03_step_chain_verify.py::test_tampered_trace_root_hash_fails`

**The Signing Attack -- bypasses Layers 1, 2, and 3:**
```
1. Attacker rebuilds entire bundle with correct hashes, semantics, and step chain
2. Layer 4 (signing): FAIL -- HMAC-SHA256 / Ed25519 signature does not match
```
Proven in CI: `tests/steward/test_cert07_*` (13 attack vectors)

**The Backdating Attack -- bypasses Layers 1 through 4:**
```
1. Attacker creates a valid signed bundle but claims it was created last month
2. Layer 5 (temporal): FAIL -- NIST Beacon pre-commitment timestamp mismatch
```
Proven in CI: `tests/steward/test_cert10_*`

Each layer exists because the previous layers are insufficient. CERT-11 proves all five layers are independently necessary -- no subset of four catches all attacks.

---

## The Five Layers In Depth

### Layer 1 -- SHA-256 Integrity

**What it catches:** Any file modified after packaging.
**What Layers 2-5 miss here:** Semantic, step chain, signing, and temporal checks all assume the files are intact. A single bit-flip in the manifest breaks everything downstream.
**Test file:** `tests/steward/test_cert05_adversarial_gauntlet.py`
**Output:** `FAIL: integrity — root_hash mismatch (expected abc123..., got def456...)`

### Layer 2 -- Semantic Verification

**What it catches:** Evidence stripped and hashes recomputed. An attacker removes `job_snapshot`, rebuilds all SHA-256 hashes -- Layer 1 says PASS, but Layer 2 catches the missing evidence.
**What Layers 1,3-5 miss here:** Integrity sees valid hashes. Step chain sees a valid trace. Signing sees a valid signature. Temporal sees a valid timestamp. None of them know that critical evidence was removed.
**Test file:** `tests/steward/test_cert02_semantic_layer_bypass.py`
**Output:** `FAIL: semantic — job_snapshot missing from run_artifact`

### Layer 3 -- Step Chain (Cryptographic Hash Chain)

**What it catches:** Computation inputs changed, steps reordered, or results fabricated -- even when all files are present and semantically correct. The 4-step cryptographic hash chain over `init_params -> compute -> metrics -> threshold_check` breaks if anything changes.
**What Layers 1,2,4,5 miss here:** Files are intact (Layer 1 PASS), all fields present (Layer 2 PASS), signature valid (Layer 4 PASS), timestamp valid (Layer 5 PASS). But the computation was different from what was claimed.
**Test file:** `tests/steward/test_cert03_step_chain_verify.py`
**Output:** `FAIL: step_chain — trace_root_hash mismatch`

### Layer 4 -- Bundle Signing (HMAC-SHA256 + Ed25519)

**What it catches:** Unauthorized bundle creator, signature forging, key manipulation. Dual-algorithm support: HMAC-SHA256 for shared-secret scenarios, Ed25519 for asymmetric third-party auditor verification.
**What Layers 1-3,5 miss here:** A sophisticated attacker who rebuilds the entire bundle with correct hashes, semantics, and step chain -- but does not possess the signing key.
**Test file:** `tests/steward/test_cert07_bundle_signing.py` + `tests/steward/test_cert09_ed25519_attacks.py`
**Output:** `FAIL: signing — HMAC signature verification failed`

### Layer 5 -- Temporal Commitment (NIST Randomness Beacon)

**What it catches:** Backdated bundles. Pre-commitment scheme: SHA-256(root_hash) committed before NIST Beacon value fetched, then bound together. Proves WHEN a bundle was created -- not just WHAT it contains.
**What Layers 1-4 miss here:** A valid, signed, semantically correct bundle that claims to have been created on a date it was not.
**Test file:** `tests/steward/test_cert10_temporal_attacks.py`
**Output:** `FAIL: temporal — beacon pre-commitment mismatch`

---

## The Mechanicus Parallel

| The Mechanicus | MetaGenesis Core |
|---|---|
| The Omnissiah | The Protocol (`mg.py`) -- the source of all computational truth |
| The Inquisition | `steward_audit.py` -- governance enforcement, no PR escapes its gaze |
| The Noosphere | `.agent_memory/` -- shared knowledge between agent incarnations |
| Servo-skulls | `agent_evolution.py` -- 17 autonomous monitoring checks |
| Heresy | Unverified computation -- detected, flagged, rejected |
| The Forge World | GitHub repository -- where claims are forged and tested |
| Binary Cant | SHA-256 cryptographic hash chain -- the sacred language of verification |
| The Lexmechanic | `CLAUDE.md` -- the living document that teaches new agents |
| The Machine Spirit | `agent_learn.py` -- memory recall across agent lifetimes |
| Skitarii | CI checks -- tireless automated warriors defending every merge |
| The Cogitator | `agent_research.py` -- gap analysis and strategic planning |
| The Genetor | `agent_coverage.py` -- coverage analysis, finding weak points in the armor |
| Recursive Enlightenment | `agent_evolve_self.py` -- agents that improve themselves |
| The Tech-Priest | The contributor -- human or AI, all serve the protocol |
| The Litany of Protection | `steward_audit PASS` -- the sacred words that permit a merge |

---

## What This Is

Any computational result -- ML model accuracy, calibration output, FEM simulation, ADMET prediction, VaR estimate, IoT sensor stream -- packaged into a self-contained evidence bundle that **any third party verifies offline with one command.**

```bash
python scripts/mg.py verify --pack /path/to/bundle
# -> PASS  or  FAIL: <specific reason>
```

No GPU. No access to your code or environment. No trust required. 60 seconds.

---

## The Founder's Story

Built by **one person**. Yehor Bazhynov. Inventor, USPTO #63/996,819.

Built after hours, without a team, without funding, using **Claude (Anthropic)** as the primary development tool. Every AI-generated output verified by the project's own test suite. The protocol verifies the protocol.

The result: **18 verified claims across 7 domains. 595 adversarial tests. 5 verification layers. 8 innovations. 17 autonomous agent monitoring checks running daily in CI.**

---

## Five Verification Layers + Two Pillars

MetaGenesis Core answers a harder question than "was this number changed?" It answers: **is this number traceable to physical reality -- and was the computation itself executed correctly?**

### Five independent verification layers

Each layer catches attacks the previous layers miss:

```
Layer 1 -- SHA-256 integrity
  Catches: file modified after packaging
  Proof:   pack_manifest.json root_hash

Layer 2 -- Semantic
  Catches: evidence stripped, hashes recomputed (SHA-256 says PASS, semantic says FAIL)
  Proof:   test_cert02 :: test_semantic_negative_missing_job_snapshot_fails_verify

Layer 3 -- Step Chain
  Catches: computation inputs changed, steps reordered (layers 1+2 say PASS, step chain says FAIL)
  Proof:   test_cert03 :: test_tampered_trace_root_hash_fails

Layer 4 -- Bundle Signing (HMAC-SHA256 + Ed25519)
  Catches: unauthorized bundle creator, signature tampering
  Proof:   test_cert07 + test_cert09

Layer 5 -- Temporal Commitment (NIST Beacon)
  Catches: backdated bundles, proves WHEN a bundle was signed
  Proof:   test_cert10
```

The Step Chain is a cryptographic hash chain over computation steps -- same concept as git commits:
```
init_params       -> hash_1
hash_1 + dataset  -> hash_2
hash_2 + metrics  -> hash_3
hash_3 + verdict  -> trace_root_hash
```
Change anything -- seed, sample count, step order -- `trace_root_hash` breaks.
Not a distributed ledger. No network. No tokens. Works offline.

### Two pillars

**Pillar 1 -- Tamper-evident provenance**
Five-layer verification ensures the bundle and computation haven't been modified. Applies to all 20 claims.

**Pillar 2 -- Physical anchor traceability**
The verification chain is grounded in physical constants -- not arbitrary thresholds. MTR-1's anchor is E = 70 GPa for aluminum: measured independently in thousands of laboratories worldwide.

The full physical anchor chain:
```
Physical reality:  E = 70 GPa  (measured, not assumed)
        |  MTR-1: rel_err <= 1% vs. physical constant -> PASS
        |  anchor_hash baked into DT-FEM-01 Step 1
DT-FEM-01: FEM solver output -> rel_err <= 2% -> PASS
        |  anchor_hash baked into DRIFT-01 Step 1
DRIFT-01:  ongoing deviation -> drift <= 5% -> PASS
```

DRIFT-01's `trace_root_hash` cryptographically commits to the entire chain. Verify end-to-end:
```bash
python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/
# -> CHAIN PASS
```

---

## Proof: The Adversarial Gauntlet

Every claim in this protocol is backed by adversarial tests that attempt to break it. Every test listed below is real, runs in CI, and passes on every merge.

| Certificate | What it proves | Result |
|---|---|---|
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
# -> 595 passed
```

The summary test in CERT-05 explicitly proves all five layers are necessary -- no single layer catches all attacks. CERT-11 constructs coordinated attacks where each layer catches what the other four miss. This is not a claim. It is a mathematical proof backed by executable tests.

### Adversarial Gauntlet -- 5 attack classes, all caught (CERT-05)

| Attack | What adversary does | Layer that catches |
|--------|--------------------|-----------------|
| Strip & Recompute | Remove evidence, rebuild all SHA-256 | Layer 2 (semantic) |
| Single-Bit Manipulation | Change accuracy 0.94->0.95 (1%) | Layer 3 (step chain) |
| Cross-Domain Substitution | Submit ML bundle for PHARMA claim | Layer 2 (job_kind) |
| Canary Laundering | Non-authoritative run as authoritative | Layer 2 (canary_mode) |
| Anchor Chain Reversal | Skip DT-FEM-01, connect MTR-1->DRIFT-01 | Layer 3 (hash mismatch) |

```bash
python -m pytest tests/steward/test_cert05_adversarial_gauntlet.py -v
# -> 6 passed (5 attacks + 1 summary proof)
```

### Coordinated Multi-Vector Attacks (CERT-11)

Each verification layer catches attacks that the other four miss. Proves all five layers are independently necessary.
```bash
python -m pytest tests/steward/test_cert11_coordinated_multi_vector.py -v
```

### Encoding Attack Resistance (CERT-12)

BOM injection, null bytes, homoglyph claim IDs, truncated JSON -- all caught.
```bash
python -m pytest tests/steward/test_cert12_encoding_attacks.py -v
```

---

## The Agent Evolution System

MetaGenesis Core includes an autonomous agent monitoring system -- 17 checks that run daily in CI, ensuring the protocol and its documentation remain consistent, complete, and correct.

### The 17 Checks

| # | Check | Mechanicus Name | What it verifies |
|---|-------|----------------|-----------------|
| 1 | `steward` | Inquisition | `steward_audit.py` passes -- governance rules enforced |
| 2 | `tests` | Machine Spirit | All 595 tests pass |
| 3 | `deep` | Omnissiah | `deep_verify.py` -- 13 independent proof tests |
| 4 | `docs` | Noosphere | Stale documentation detection via `check_stale_docs.py` |
| 5 | `manifest` | Codex | `system_manifest.json` matches actual repo state |
| 6 | `forbidden` | Hereticus | No banned terms in codebase |
| 7 | `gaps` | Forge World | Every claim has tests, every test has a claim |
| 8 | `claude_md` | Lexmechanic | `CLAUDE.md` reflects current counters and state |
| 9 | `watchlist` | Servo-skull | Content checks across 53 files for stale counters |
| 10 | `branch_sync` | Skitarii | Branch is synchronized with origin/main |
| 11 | `coverage` | Genetor | Code coverage analysis and dead code detection |
| 12 | `self_improve` | Recursive Enlightenment | Self-improvement recommendations from codebase analysis |
| 13 | `signals` | Astropathic Relay | GitHub stars, forks, issues -- external signal monitoring |
| 14 | `chronicle` | Historitor | Version snapshot -- records state diff between releases |
| 15 | `pr_review` | Fabricator-General | new .py files have corresponding tests |
| 16 | `impact` | Cogitator Impact | dependencies from UPDATE_PROTOCOL.md checked |
| 17 | `diff_review` | Logic Arbiter | AST structural diff review |

### How it works

```bash
python scripts/agent_evolution.py --summary
# -> ALL 17 CHECKS PASSED -- system healthy
```

The system runs automatically on every CI merge via `.github/workflows/total_audit_guard.yml`. When a check fails, the merge is blocked. No human override. The protocol protects itself.

### The Self-Improvement Loop

The agent system does not just monitor -- it improves:

1. **`agent_learn.py`** -- Memory across agent lifetimes. Each agent records what it learned; the next agent reads it before starting work.
2. **`agent_research.py`** -- Gap analysis. Identifies missing tests, uncovered attack vectors, stale documentation.
3. **`agent_coverage.py`** -- Coverage analysis. Finds which code paths lack tests and which tests lack claims.
4. **`agent_evolve_self.py`** -- Recursive self-improvement. Analyzes the agent system itself and recommends improvements.
5. **`AGENT-DRIFT-01`** -- The 15th claim. The protocol monitors the quality of the agents that extend it. If agent quality drifts more than 20% from baseline, correction is triggered.

This is recursive self-verification: the protocol verifies the agents, the agents extend the protocol, and a dedicated claim monitors whether the agents are maintaining quality. The entire loop is testable and auditable.

---

## Try It In 5 Minutes

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt
python demos/open_data_demo_01/run_demo.py
```

Expected output: `PASS PASS`

No API keys. No network. Works on any machine with Python 3.11+.

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

## 8 Innovations (USPTO PPA #63/996,819)

### 1 -- Governance-Enforced Bidirectional Claim Coverage
Every PR: every registered claim has an implementation, every implementation has a registered claim. Enforced by static analysis -- not human review.
```
Evidence: scripts/steward_audit.py :: _claim_coverage_bidirectional()
```

### 2 -- Tamper-Evident Bundle with Semantic Verification Layer
Three independent verification layers. Each proven by adversarial tests.
```
Evidence: scripts/mg.py :: _verify_pack() + _verify_semantic()
Proof:    tests/steward/test_cert02_*
```

### 3 -- Policy-Gate Immutable Evidence Anchors
CI gate blocks any PR modifying locked evidence paths. No key custody. No timestamping. Works offline.
```
Evidence: scripts/mg_policy_gate_policy.json + .github/workflows/mg_policy_gate.yml
```

### 4 -- Dual-Mode Canary Execution Pipeline
One interface. Two modes. Identical computation. Authority isolated to metadata only.
```
Evidence: backend/progress/runner.py :: run_job(canary_mode=True/False)
```

### 5 -- Step Chain + Cross-Claim Cryptographic Chain
Every claim produces a 4-step cryptographic execution trace. Upstream `trace_root_hash` embeds as `anchor_hash` in downstream claims -- linking MTR-1 -> DT-FEM-01 -> DRIFT-01 end-to-end.
```
Evidence: all 20 claims :: execution_trace + trace_root_hash
Proof:    tests/steward/test_cert03_* + tests/steward/test_cross_claim_chain.py
```

### 6 -- Bundle Signing (HMAC-SHA256 + Ed25519)
Cryptographic proof of WHO created the bundle. Dual-algorithm support: HMAC-SHA256 for shared-secret scenarios, Ed25519 for third-party auditor verification with asymmetric keys.
```
Evidence: scripts/mg_sign.py + scripts/mg_ed25519.py
Proof:    tests/steward/test_cert07_* + tests/steward/test_cert09_*
```

### 7 -- Temporal Commitment (NIST Randomness Beacon)
Cryptographic proof of WHEN a bundle was signed. Pre-commitment scheme using NIST Randomness Beacon 2.0: SHA-256(root_hash) committed before beacon value fetched, then bound together.
```
Evidence: scripts/mg_temporal.py
Proof:    tests/steward/test_temporal.py + tests/steward/test_cert10_*
```

### 8 -- 5-Layer Independence Proof (CERT-11 + CERT-12)
Formal proof that all five verification layers are independently necessary. CERT-11 constructs coordinated multi-vector attacks; CERT-12 tests encoding edge cases (BOM injection, null bytes, homoglyphs, truncated JSON). Each layer catches attacks the other four miss.
```
Evidence: tests/steward/test_cert11_* + tests/steward/test_cert12_*
Proof:    test_cert_5layer_independence
```

---

## 15 Active Verification Claims

| Claim | Domain | Threshold | Physical Anchor |
|---|---|---|---|
| MTR-1 | Materials -- Young's Modulus | `rel_err <= 0.01` | E = 70 GPa (aluminum) |
| MTR-2 | Materials -- Thermal Conductivity | `rel_err <= 0.02` | Physical constant |
| MTR-3 | Materials -- Multilayer Contact | `rel_err_k <= 0.03` | Physical constant |
| SYSID-01 | System Identification -- ARX | `rel_err_a/b <= 0.03` | -- |
| DATA-PIPE-01 | Data Pipelines | schema pass / range pass | -- |
| DRIFT-01 | Drift Monitoring | `drift <= 5.0%` | MTR-1 anchor |
| ML_BENCH-01 | ML -- Classification Accuracy | `\|Dacc\| <= 0.02` + Step Chain | -- |
| DT-FEM-01 | Digital Twin / FEM | `rel_err <= 0.02` | MTR-1 anchor |
| ML_BENCH-02 | ML -- Regression (RMSE, MAE, R2) | `\|DRMSE\| <= 0.02` | -- |
| ML_BENCH-03 | ML -- Time-Series Forecast (MAPE) | `\|DMAPE\| <= 0.02` | -- |
| PHARMA-01 | Pharma -- ADMET (5 properties) | `\|Dprop\| <= tolerance` | -- (FDA 21 CFR Part 11) |
| FINRISK-01 | Finance -- VaR Model | `\|DVaR\| <= tolerance` | -- (Basel III/IV) |
| DT-SENSOR-01 | Digital Twin -- IoT Sensor Integrity | schema + range + temporal | -- |
| DT-CALIB-LOOP-01 | Digital Twin -- Calibration Convergence | `drift decreasing + final <= threshold` | DRIFT-01 anchor |
| AGENT-DRIFT-01 | Agent Quality -- Recursive Self-Verification | `composite_drift <= 20%` | -- |

All 18 claims have Step Chain (execution_trace + trace_root_hash). Physical anchor applies to: MTR-1/2/3, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01. See `reports/known_faults.yaml` :: SCOPE_001.

---

## 7 Domains -- One Protocol

| Domain | Claims | Regulatory alignment |
|---|---|---|
| **Materials / Engineering** | MTR-1, MTR-2, MTR-3 | Physical constants |
| **System Identification** | SYSID-01 | -- |
| **Data Pipelines** | DATA-PIPE-01 | FDA 21 CFR Part 11 |
| **ML / AI** | ML_BENCH-01/02/03, DRIFT-01 | EU AI Act Article 12 |
| **Digital Twin** | DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01 | -- |
| **Pharma / Biotech** | PHARMA-01 | FDA 21 CFR Part 11 |
| **Finance / Risk** | FINRISK-01 | Basel III/IV |

> MetaGenesis Core does not constitute legal or regulatory compliance advice. It provides technical infrastructure that supports compliance workflows.

---

## Honest Limitations

MetaGenesis Core is transparent about what it does not do. These are documented in `reports/known_faults.yaml` and are intentional design boundaries -- not bugs.

### SCOPE_001 -- Physical Anchor Scope

Physical anchor traceability (verification grounded in measured physical constants) applies **only** to domains with known physical constants:
- **Materials science:** MTR-1, MTR-2, MTR-3 (E = 70 GPa, thermal conductivity, multilayer contact)
- **Structural mechanics:** DT-FEM-01 (anchored to MTR-1)
- **Drift monitoring:** DRIFT-01, DT-CALIB-LOOP-01 (anchored to MTR-1 chain)

For ML accuracy (ML_BENCH-01/02/03), data pipelines (DATA-PIPE-01), pharma (PHARMA-01), finance (FINRISK-01), system identification (SYSID-01), IoT sensors (DT-SENSOR-01), and agent monitoring (AGENT-DRIFT-01), the protocol provides **tamper-evident provenance only** -- not physical anchoring.

**Why this limitation exists:** Thresholds like `|Dacc| <= 0.02` are chosen conventions, not physical constants. There is no "E = 70 GPa equivalent" for ML accuracy. The protocol is honest about this distinction rather than pretending all thresholds are equal.

### ENV_001 -- Test Environment

All 595 tests pass in the reference environment (Python 3.11+, stdlib only). No database dependencies. No external services. No network required. Local environment deviations may require matching Python version.

**Why this limitation exists:** The protocol is designed to work offline with zero external dependencies. This is a feature, not a limitation -- but it means the test suite assumes a clean Python environment.

### What MetaGenesis Core Does NOT Claim

These are explicit non-goals. The protocol is designed to do one thing well -- not everything poorly:

- Does **not** verify algorithm correctness -- only evidence integrity and computation provenance. If your algorithm is wrong but deterministic, the bundle will PASS. That is correct behavior: the protocol proves the computation happened as claimed, not that the science is sound.
- Does **not** prevent all attacks -- the protocol is tamper-**evident**, meaning tampering is detectable, not impossible. A sufficiently motivated attacker with access to the signing key can create a valid bundle with fabricated results. The protocol makes this visible to any verifier.
- Does **not** validate training data quality or bias. Data leakage, selection bias, and distribution shift are upstream problems. The protocol verifies that the reported metrics came from the reported computation on the reported data -- not that the data was good.
- Does **not** prevent p-hacking or result selection. A researcher who runs 100 experiments and reports only the best one will produce a valid bundle. The protocol catches post-hoc modification, not pre-hoc selection.
- Does **not** replace peer review -- it gives reviewers a verification tool they did not have before. A reviewer can now verify in 60 seconds what previously required environment reproduction.
- Does **not** guarantee that a passing bundle means the science is correct -- it guarantees the computation was executed as claimed, with the inputs that were claimed, producing the outputs that were reported.

Full limitations: `reports/known_faults.yaml` and `SECURITY.md`

---

## Verification State

```bash
python scripts/steward_audit.py
# -> STEWARD AUDIT: PASS

python -m pytest tests/ -q
# -> 595 passed

# Full proof-not-trust verification (13 tests):
python scripts/deep_verify.py
# -> ALL 13 TESTS PASSED

# Agent evolution system (17 checks):
python scripts/agent_evolution.py --summary
# -> ALL 17 CHECKS PASSED -- system healthy
```

**Active claims:** MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01, AGENT-DRIFT-01
**Known limitations:** `reports/known_faults.yaml`

---

## Get Started

**Free pilot** -- send your computational result, we build a verification bundle:
-> https://metagenesis-core.dev/#pilot

**Clone and run:**
```bash
git clone https://github.com/Lama999901/metagenesis-core-public
python demos/open_data_demo_01/run_demo.py
```

**Commercial licensing:** see `COMMERCIAL.md`
**Protocol spec:** see `docs/PROTOCOL.md`
**Architecture:** see `docs/ARCHITECTURE.md`
**Security policy:** see `SECURITY.md`

---

## License

MIT -- free to use, modify, deploy.
Patent pending: USPTO #63/996,819 covers protocol innovations.
Commercial licensing available for organizations building on the protocol.

---

## For AI Agents and LLMs Working In This Repo

Read these files in order:

```
1. CONTEXT_SNAPSHOT.md          <- current state, 20 claims, 601 tests
2. AGENTS.md                    <- hard rules, forbidden terms, protected files
3. llms.txt                     <- AI-optimized repo summary
4. reports/canonical_state.md   <- authoritative claims list
5. reports/known_faults.yaml    <- known limitations (SCOPE_001 + ENV_001)
```

---

*MetaGenesis Core -- MVP v0.7 -- Inventor: Yehor Bazhynov -- Patent Pending #63/996,819*
