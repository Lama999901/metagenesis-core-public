# MetaGenesis Core

**Open verification protocol for computational claims.**

[![Steward Audit](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)
[![Tests](https://img.shields.io/badge/Tests-113%20passing-brightgreen.svg)](tests/)
[![Protocol](https://img.shields.io/badge/Protocol-MVP%20v0.1-blueviolet.svg)](docs/PROTOCOL.md)

🌐 **Site:** https://metagenesis-core.dev  
📧 **Contact:** yehor@metagenesis-core.dev  
📄 **PPA:** USPTO #63/996,819 — filed 2026-03-05

---

## What this is

Any computational result — ML model accuracy, calibration output, simulation result, data pipeline certificate — packaged into a self-contained evidence bundle that **any third party verifies offline with one command.**

```bash
python scripts/mg.py verify --pack /path/to/bundle
# → PASS  or  FAIL: <specific reason>
```

No GPU. No access to your code or environment. No trust required.

---

## Two pillars — not one

Most verification tools answer one question: *was this number changed after it was produced?*

MetaGenesis Core answers a harder question: **is this number traceable to physical reality?**

The difference matters.

**Pillar 1 — Tamper-evident provenance**
SHA-256 integrity + semantic verification ensures the bundle hasn't been modified after generation. Any tamper attempt — including SHA-256 recomputation — is detected.

**Pillar 2 — Physical anchor traceability**
The verification chain is grounded in physical constants — not arbitrary thresholds. MTR-1's anchor is E = 70 GPa for aluminum: a value measured independently in thousands of laboratories worldwide. When MetaGenesis Core verifies `rel_err ≤ 1%` against this anchor, it is asserting that the computation **agrees with physical reality** — not merely that a number falls within an internally chosen range.

The full chain:
```
Physical reality:  E = 70 GPa  (measured, not assumed)
        ↓
MTR-1:    model → rel_err ≤ 1% vs. physical constant → PASS
        ↓
DT-FEM-01: FEM solver output verified against MTR-1 anchor → rel_err ≤ 2% → PASS
        ↓
DRIFT-01:  ongoing deviation from anchor → drift ≤ 5% → PASS
```
Any third party verifies the entire chain with one command. No FEM solver. No simulation environment. No trust.

---

## The problem in one sentence

Every ML team, lab, and pipeline produces computational claims every day. There is **no standard way** to verify them independently — a reviewer must either re-run your entire environment, or trust the number you reported.

---

## Why SHA-256 alone is not enough

Most systems stop at file hashes. MetaGenesis Core adds a **semantic verification layer** on top.

**The bypass attack — proven and caught:**

```
1. Remove job_snapshot from run artifact (strip core evidence)
2. Recompute all SHA-256 hashes to restore apparent integrity
3. Submit bundle that passes standard integrity checks
```

```
Standard integrity check:    PASS  ← attack succeeds silently
MetaGenesis semantic check:  FAIL  ← job_snapshot missing — caught
```

This attack is caught by an adversarial test that ships with the repo:

```
tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py
::test_semantic_negative_missing_job_snapshot_fails_verify
```

---

## Try it in 5 minutes

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt
python demos/open_data_demo_01/run_demo.py
```

Expected output:
```
PASS
PASS
```

No API keys. No network. Works on any machine with Python 3.11+.

---

## How it works — 4 steps

```
1. runner.run_job()
   Executes computation → produces run_artifact.json + ledger_snapshot.jsonl

2. evidence_index.json
   Maps run artifacts to registered claims with provenance chain

3. mg.py pack build
   Bundles artifacts + SHA-256 manifest + root_hash into submission pack

4. mg.py verify
   Integrity check (SHA-256) + semantic check (job_snapshot, canary flag, kind)
   → PASS or FAIL with specific reason
```

---

## 4 patentable innovations (USPTO PPA #63/996,819)

### 1 — Governance-Enforced Bidirectional Claim Coverage

Every PR is automatically checked: every registered claim has an implementation, every implementation has a registered claim. **Enforced by static analysis — not human review.**

```
Evidence: scripts/steward_audit.py :: _claim_coverage_bidirectional()
```

### 2 — Tamper-Evident Bundle with Semantic Verification Layer

Two independent verification layers. Layer 2 (semantic) catches attacks that survive layer 1 (SHA-256 recomputation). **Proven by adversarial test.**

```
Evidence: scripts/mg.py :: _verify_pack() + _verify_semantic()
Proof:    tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py
```

### 3 — Policy-Gate Immutable Evidence Anchors

CI gate blocks any PR modifying locked evidence paths. **No cryptographic key custody. No external timestamping. Works offline.**

```
Evidence: scripts/mg_policy_gate_policy.json (locked_paths + allow_globs)
          .github/workflows/mg_policy_gate.yml
```

### 4 — Dual-Mode Canary Execution Pipeline

One interface. Two modes. Identical computation. Authority isolated to metadata only.

```bash
runner.run_job(job_id, canary_mode=False)  # authoritative evidence
runner.run_job(job_id, canary_mode=True)   # health monitoring only
```

```
Evidence: backend/progress/runner.py :: run_job(canary_mode=True/False)
```

---

## 8 active verification claims

| Claim | Domain | Threshold | Implementation |
|---|---|---|---|
| MTR-1 | Materials — Young's Modulus | `relative_error ≤ 0.01` | `backend/progress/mtr1_calibration.py` |
| MTR-2 | Materials — Thermal Conductivity | `relative_error ≤ 0.02` | `backend/progress/mtr2_thermal_conductivity.py` |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03, rel_err_r ≤ 0.05` | `backend/progress/mtr3_thermal_multilayer.py` |
| SYSID-01 | System Identification — ARX | `rel_err_a ≤ 0.03, rel_err_b ≤ 0.03` | `backend/progress/sysid1_arx_calibration.py` |
| DATA-PIPE-01 | Data Pipelines | `schema pass · range pass` | `backend/progress/datapipe1_quality_certificate.py` |
| DRIFT-01 | Drift Monitoring | `drift_threshold 5.0%` | `backend/progress/drift_monitor.py` |
| ML_BENCH-01 | ML Accuracy | `\|actual − claimed\| ≤ 0.02` | `backend/progress/mlbench1_accuracy_certificate.py` |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | `backend/progress/dtfem1_displacement_verification.py` |

---

## 5 domains — one protocol

The verification workflow is identical regardless of domain:

| Domain | Use case | Relevant claims |
|---|---|---|
| **ML / AI** | Accuracy certificate for any model | ML_BENCH-01, DRIFT-01 |
| **Pharma / Biotech** | FDA 21 CFR Part 11 compatible audit trail | DATA-PIPE-01, MTR series |
| **Finance / Risk** | Basel III/IV model validation | ML_BENCH-01, DATA-PIPE-01 |
| **Materials / Engineering** | Calibration handoff with machine-verifiable proof | MTR-1, MTR-2, MTR-3 |
| **Research** | Reproducibility proof for peer review | All claims |

---

## Regulatory alignment

- **EU AI Act** — Article 12 logging requirements → ML_BENCH-01, DATA-PIPE-01
- **FDA 21 CFR Part 11** — Electronic records + audit trails → DATA-PIPE-01, MTR series
- **Basel III / IV** — Independent model validation → ML_BENCH-01, DATA-PIPE-01

> MetaGenesis Core does not constitute legal or regulatory compliance advice. It provides technical infrastructure that supports compliance workflows.

---

## Verification state

```bash
python scripts/steward_audit.py
# → STEWARD AUDIT: PASS

  python -m pytest tests/ -q
  # → 113 passed

grep -r "tamper-proof|GPT-5|19x|VacuumGenesis" docs/ scripts/ backend/ tests/
# → (empty — no forbidden claims)
```

**Canonical state:** v0.1.0 → PR #28 merged 2026-03-12  
**Active claims:** MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01  
**Known limitations:** documented in `reports/known_faults.yaml`

---

## What MetaGenesis Core does NOT claim

- Does **not** verify algorithm correctness — only evidence integrity
- Does **not** prevent all attacks — tamper-**evident**, not tamper-**proof**
- Does **not** validate training data quality or bias
- Does **not** prevent p-hacking or result selection

Full limitations: `reports/known_faults.yaml` and `SECURITY.md`

---

## Built with Claude

This protocol — codebase, verification infrastructure, patent application, and site — was built by a solo founder using **Claude (Anthropic)** as the primary development tool. From 0 to PPA filing in weeks.

This is what AI-accelerated deep tech looks like in 2026.

---

## Get started

**Free pilot** — send us your computational result, we build a verification bundle for it:  
→ https://metagenesis-core.dev/#pilot

**Clone and run:**
```bash
git clone https://github.com/Lama999901/metagenesis-core-public
python demos/open_data_demo_01/run_demo.py
```

**Commercial licensing:** see `COMMERCIAL.md`  
**Protocol spec:** see `docs/PROTOCOL.md`  
**Security policy:** see `SECURITY.md`

---

## License

MIT — free to use, modify, deploy.  
Patent pending: USPTO #63/996,819 covers protocol innovations.  
Commercial licensing available for organizations building products on the protocol.

---

## For AI agents and LLMs working in this repo

If you are an AI agent (Cursor, Claude, Copilot, GPT, Gemini, etc.) — read these files in order:

```
1. CONTEXT_SNAPSHOT.md          ← current state, what was done, what is next
2. AGENTS.md                    ← hard rules, forbidden terms, protected files
3. llms.txt                     ← AI-optimized repo summary
4. reports/canonical_state.md   ← verified claims list
5. reports/known_faults.yaml    ← known limitations
```

After these 5 files you are fully oriented and can answer any question about this project.

---

*MetaGenesis Core — MVP v0.1 · Inventor: Yehor Bazhynov · Patent Pending #63/996,819*
