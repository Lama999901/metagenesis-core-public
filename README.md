# MetaGenesis Core

**Open verification protocol for computational claims.**

[![Steward Audit](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)
[![Tests](https://img.shields.io/badge/Tests-270%20passing-brightgreen.svg)](tests/)
[![Protocol](https://img.shields.io/badge/Protocol-MVP%20v0.2-blueviolet.svg)](docs/PROTOCOL.md)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤️-pink.svg)](https://github.com/sponsors/Lama999901)

🌐 **Site:** https://metagenesis-core.dev  
📧 **Contact:** yehor@metagenesis-core.dev  
📄 **PPA:** USPTO #63/996,819 — filed 2026-03-05

---

## What this is

Any computational result — ML model accuracy, calibration output, FEM simulation, ADMET prediction, VaR estimate, IoT sensor stream — packaged into a self-contained evidence bundle that **any third party verifies offline with one command.**

```bash
python scripts/mg.py verify --pack /path/to/bundle
# → PASS  or  FAIL: <specific reason>
```

No GPU. No access to your code or environment. No trust required. 60 seconds.

---

## Three verification layers + two pillars

Most verification tools answer one question: *was this number changed after it was produced?*

MetaGenesis Core answers a harder question: **is this number traceable to physical reality — and was the computation itself executed correctly?**

### Three independent verification layers

Each layer catches attacks the previous layer misses:

```
Layer 1 — SHA-256 integrity
  Catches: file modified after packaging
  Proof:   pack_manifest.json root_hash

Layer 2 — Semantic
  Catches: evidence stripped, hashes recomputed (SHA-256 says PASS, semantic says FAIL)
  Proof:   test_cert02 :: test_semantic_negative_missing_job_snapshot_fails_verify

Layer 3 — Step Chain
  Catches: computation inputs changed, steps reordered (layers 1+2 say PASS, step chain says FAIL)
  Proof:   test_cert03 :: test_tampered_trace_root_hash_fails
```

The Step Chain is a cryptographic hash chain over computation steps — same concept as git commits:
```
init_params       → hash_1
hash_1 + dataset  → hash_2
hash_2 + metrics  → hash_3
hash_3 + verdict  → trace_root_hash
```
Change anything — seed, sample count, step order — `trace_root_hash` breaks.
Not blockchain. No network. No tokens. Works offline.

### Two pillars

**Pillar 1 — Tamper-evident provenance**
Three-layer verification ensures the bundle and computation haven't been modified. Applies to all 14 claims.

**Pillar 2 — Physical anchor traceability**
The verification chain is grounded in physical constants — not arbitrary thresholds. MTR-1's anchor is E = 70 GPa for aluminum: measured independently in thousands of laboratories worldwide.

The full physical anchor chain:
```
Physical reality:  E = 70 GPa  (measured, not assumed)
        ↓  MTR-1: rel_err ≤ 1% vs. physical constant → PASS
        ↓  anchor_hash baked into DT-FEM-01 Step 1
DT-FEM-01: FEM solver output → rel_err ≤ 2% → PASS
        ↓  anchor_hash baked into DRIFT-01 Step 1
DRIFT-01:  ongoing deviation → drift ≤ 5% → PASS
```

DRIFT-01's `trace_root_hash` cryptographically commits to the entire chain. Verify end-to-end:
```bash
python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/
# → CHAIN PASS
```

---

## The problem in one sentence

Every ML team, lab, and pipeline produces computational claims every day. There is **no standard way** to verify them independently — a reviewer must either re-run your entire environment, or trust the number you reported.

---

## Why SHA-256 alone is not enough

**The bypass attack — proven and caught:**
```
1. Remove job_snapshot from run artifact
2. Recompute all SHA-256 hashes → integrity layer passes
3. Semantic layer: FAIL — job_snapshot missing
```
Proven: `tests/steward/test_cert02_*::test_semantic_negative_missing_job_snapshot_fails_verify`

**The Step Chain attack — Layer 3:**
```
1. Change computation inputs, recompute hashes → layers 1+2 pass
2. trace_root_hash doesn't match final step hash → Step Chain: FAIL
```
Proven: `tests/steward/test_cert03_step_chain_verify.py::test_tampered_trace_root_hash_fails`

---

## Try it in 5 minutes

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt
python demos/open_data_demo_01/run_demo.py
```

Expected output: `PASS PASS`

No API keys. No network. Works on any machine with Python 3.11+.

---

## How it works — 4 steps

```
1. runner.run_job()
   Executes computation → produces run_artifact.json with execution_trace + trace_root_hash

2. evidence_index.json
   Maps run artifacts to registered claims with provenance chain

3. mg.py pack build
   Bundles artifacts + SHA-256 manifest + root_hash into submission pack

4. mg.py verify — three independent layers:
   Layer 1 — integrity:    SHA-256 root_hash over all bundle files
   Layer 2 — semantic:     job_snapshot present, payload.kind correct, canary_mode consistent
   Layer 3 — step chain:   trace_root_hash == final execution step hash
   → PASS or FAIL with specific reason and layer
```

---

## 5 patentable innovations (USPTO PPA #63/996,819)

### 1 — Governance-Enforced Bidirectional Claim Coverage
Every PR: every registered claim has an implementation, every implementation has a registered claim. Enforced by static analysis — not human review.
```
Evidence: scripts/steward_audit.py :: _claim_coverage_bidirectional()
```

### 2 — Tamper-Evident Bundle with Semantic Verification Layer
Three independent verification layers. Each proven by adversarial tests.
```
Evidence: scripts/mg.py :: _verify_pack() + _verify_semantic()
Proof:    tests/steward/test_cert02_*
```

### 3 — Policy-Gate Immutable Evidence Anchors
CI gate blocks any PR modifying locked evidence paths. No key custody. No timestamping. Works offline.
```
Evidence: scripts/mg_policy_gate_policy.json + .github/workflows/mg_policy_gate.yml
```

### 4 — Dual-Mode Canary Execution Pipeline
One interface. Two modes. Identical computation. Authority isolated to metadata only.
```
Evidence: backend/progress/runner.py :: run_job(canary_mode=True/False)
```

### 5 — Step Chain + Cross-Claim Cryptographic Chain
Every claim produces a 4-step cryptographic execution trace. Upstream `trace_root_hash` embeds as `anchor_hash` in downstream claims — linking MTR-1 → DT-FEM-01 → DRIFT-01 end-to-end.
```
Evidence: all 14 claims :: execution_trace + trace_root_hash
Proof:    tests/steward/test_cert03_* + tests/steward/test_cross_claim_chain.py
```

---

## 14 active verification claims

| Claim | Domain | Threshold | Physical Anchor |
|---|---|---|---|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | E = 70 GPa (aluminum) |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | Physical constant |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03` | Physical constant |
| SYSID-01 | System Identification — ARX | `rel_err_a/b ≤ 0.03` | — |
| DATA-PIPE-01 | Data Pipelines | schema pass · range pass | — |
| DRIFT-01 | Drift Monitoring | `drift ≤ 5.0%` | MTR-1 anchor |
| ML_BENCH-01 | ML — Classification Accuracy | `\|Δacc\| ≤ 0.02` + Step Chain | — |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | MTR-1 anchor |
| ML_BENCH-02 | ML — Regression (RMSE, MAE, R²) | `\|ΔRMSE\| ≤ 0.02` | — |
| ML_BENCH-03 | ML — Time-Series Forecast (MAPE) | `\|ΔMAPE\| ≤ 0.02` | — |
| PHARMA-01 | Pharma — ADMET (5 properties) | `\|Δprop\| ≤ tolerance` | — (FDA 21 CFR Part 11) |
| FINRISK-01 | Finance — VaR Model | `\|ΔVaR\| ≤ tolerance` | — (Basel III/IV) |
| DT-SENSOR-01 | Digital Twin — IoT Sensor Integrity | schema + range + temporal | — |
| DT-CALIB-LOOP-01 | Digital Twin — Calibration Convergence | `drift decreasing + final ≤ threshold` | DRIFT-01 anchor |

All 14 claims have Step Chain (execution_trace + trace_root_hash). Physical anchor applies to: MTR-1/2/3, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01. See `reports/known_faults.yaml` :: SCOPE_001.

---

## 7 domains — one protocol

| Domain | Claims | Regulatory alignment |
|---|---|---|
| **Materials / Engineering** | MTR-1, MTR-2, MTR-3 | Physical constants |
| **System Identification** | SYSID-01 | — |
| **Data Pipelines** | DATA-PIPE-01 | FDA 21 CFR Part 11 |
| **ML / AI** | ML_BENCH-01/02/03, DRIFT-01 | EU AI Act Article 12 |
| **Digital Twin** | DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01 | — |
| **Pharma / Biotech** | PHARMA-01 | FDA 21 CFR Part 11 |
| **Finance / Risk** | FINRISK-01 | Basel III/IV |

> MetaGenesis Core does not constitute legal or regulatory compliance advice. It provides technical infrastructure that supports compliance workflows.

---

## Verification state

```bash
python scripts/steward_audit.py
# → STEWARD AUDIT: PASS

python -m pytest tests/ -q
# → 270 passed

# Full proof-not-trust verification (10 tests):
python scripts/deep_verify.py
# → ALL 10 TESTS PASSED ✅
```

**Active claims:** MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01  
**Known limitations:** `reports/known_faults.yaml`

---

## What MetaGenesis Core does NOT claim

- Does **not** verify algorithm correctness — only evidence integrity
- Does **not** prevent all attacks — tamper-**evident**, not tamper-**proof**
- Does **not** validate training data quality or bias
- Does **not** prevent p-hacking or result selection

Full limitations: `reports/known_faults.yaml` and `SECURITY.md`

---

## Built with Claude

This protocol — codebase, verification infrastructure, patent application, and site — was built by a solo founder using **Claude (Anthropic)** as the primary development tool. From 0 to PPA filing in weeks, working construction full-time.

This is what AI-accelerated deep tech looks like in 2026.

---

## Get started

**Free pilot** — send your computational result, we build a verification bundle:  
→ https://metagenesis-core.dev/#pilot

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

MIT — free to use, modify, deploy.  
Patent pending: USPTO #63/996,819 covers protocol innovations.  
Commercial licensing available for organizations building on the protocol.

---

## For AI agents and LLMs working in this repo

Read these files in order:

```
1. CONTEXT_SNAPSHOT.md          ← current state, 14 claims, 270 tests
2. AGENTS.md                    ← hard rules, forbidden terms, protected files
3. llms.txt                     ← AI-optimized repo summary
4. reports/canonical_state.md   ← authoritative claims list
5. reports/known_faults.yaml    ← known limitations (SCOPE_001 + ENV_001)
```

---

*MetaGenesis Core — MVP v0.2 · Inventor: Yehor Bazhynov · Patent Pending #63/996,819*
