# CONTEXT_SNAPSHOT.md — Live State for AI Agents

> Read this file first if you are an AI agent starting a new session.
> This is the authoritative snapshot of what has been done and what is next.
> Updated: 2026-04-08

---

## Project identity

- **What:** Open verification protocol for computational claims (NOT a simulation platform)
- **Inventor:** Yehor Bazhynov
- **PPA:** USPTO #63/996,819 — filed 2026-03-05 — non-provisional deadline 2027-03-05
- **Repo:** https://github.com/Lama999901/metagenesis-core-public
- **Site:** https://metagenesis-core.dev (Vercel, auto-deploys from main)
- **Email:** yehor@metagenesis-core.dev
- **Payment:** $299/bundle — bank transfer / crypto (BTC/ETH/USDC) / invoice

---

## Verified state (2026-04-08)

| Parameter | Value |
|---|---|
| Tests | **2078 passing** |
| steward_audit | PASS |
| CI | GREEN |
| Active claims | **20** |
| Verification layers | 5 (integrity + semantic + step chain + bundle signing + temporal commitment) |
| Innovations | 8 (5 PPA + HMAC signing + Ed25519 signing + temporal commitment) |
| Domains | 8 |
| Agent checks | 21 (agent_evolution.py) |
| Real ratio | 51.2% (21 real / 20 synthetic) |
| Coverage | 87.8% |
| GitHub Release | v0.9.0 |
| Adversarial tests | CERT-05 (5 attacks) + CERT-06 (5 scenarios) + CERT-07 (signing) + CERT-08 (reproducibility) + CERT-09 (Ed25519 attacks) + CERT-10 (temporal attacks) + CERT-11 (coordinated multi-vector) + CERT-12 (encoding attacks) |

---

## 20 domain verification templates

| Claim | Domain | Threshold | Physical Anchor |
|-------|--------|-----------|-----------------|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | E = 70 GPa ⚓ |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | Physical constant ⚓ |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03` | Physical constant ⚓ |
| SYSID-01 | System Identification | `rel_err_a/b ≤ 0.03` | — |
| DATA-PIPE-01 | Data Pipelines | schema + range pass | — |
| DRIFT-01 | Drift Monitoring | `drift ≤ 5.0%` | MTR-1 anchor ⚓ |
| ML_BENCH-01 | ML — Classification | `\|Δacc\| ≤ 0.02` + Step Chain | — |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | MTR-1 anchor ⚓ |
| ML_BENCH-02 | ML — Regression | `\|ΔRMSE\| ≤ 0.02` | — |
| ML_BENCH-03 | ML — Time-Series | `\|ΔMAPE\| ≤ 0.02` | — |
| PHARMA-01 | Pharma — ADMET | `\|Δprop\| ≤ tolerance` | — |
| FINRISK-01 | Finance — VaR | `\|ΔVaR\| ≤ tolerance` | — |
| DT-SENSOR-01 | IoT — Sensor Integrity | schema + range + temporal | — |
| DT-CALIB-LOOP-01 | Digital Twin — Convergence | `drift_pct decreasing` | DRIFT-01 anchor ⚓ |
| AGENT-DRIFT-01 | Agent Quality — Self-Verification | `composite_drift <= 20%` | — |
| MTR-4 | Materials — Titanium Ti-6Al-4V | `rel_err ≤ 0.01` | E = 114 GPa ⚓ |
| MTR-5 | Materials — Stainless Steel SS316L | `rel_err ≤ 0.01` | E = 193 GPa ⚓ |
| MTR-6 | Materials — Copper Conductivity | `rel_err ≤ 0.02` | k = 401 W/(m·K) ⚓ |
| PHYS-01 | Fundamental Physics — Boltzmann | `rel_err ≤ 1e-9` | kB = 1.380649e-23 J/K ⚓ SI2019 |
| PHYS-02 | Fundamental Physics — Avogadro | `rel_err ≤ 1e-8` | NA = 6.02214076e23 mol^-1 ⚓ SI2019 |

Physical anchor scope (SCOPE_001): MTR-1/2/3/4/5/6, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01, PHYS-01, PHYS-02 only.

---

## Adversarial proof suite (new 2026-03-17)

**CERT-05 — Adversarial Gauntlet** (`tests/steward/test_cert05_adversarial_gauntlet.py`)

| Attack | What adversary does | Layer that catches |
|--------|--------------------|--------------------|
| Strip & Recompute | Remove evidence, rebuild all SHA-256 hashes | Layer 2 (semantic) |
| Single-Bit Manipulation | Change accuracy 0.94→0.95 (1%) | Layer 3 (step chain) |
| Cross-Domain Substitution | Submit ML bundle for PHARMA claim | Layer 2 (job_kind) |
| Canary Laundering | Submit non-authoritative run as authoritative | Layer 2 (canary_mode) |
| Anchor Chain Reversal | Skip DT-FEM-01, connect MTR-1→DRIFT-01 | Layer 3 (hash mismatch) |

**CERT-06 — Real-World Scenarios** (`tests/steward/test_cert06_real_world_scenarios.py`)
- Honest Team Verification, Cherry-Picker Caught, Physical Anchor Chain,
  Real Client Data Audit, Reproducibility Crisis Resolution

---

## 8 innovations

1. **Bidirectional Claim Coverage** → `steward_audit.py :: _claim_coverage_bidirectional()`
2. **Tamper-Evident Bundle + Semantic Layer** → `mg.py :: _verify_pack() + _verify_semantic()`
3. **Policy-Gate Immutable Anchors** → `mg_policy_gate_policy.json`
4. **Dual-Mode Canary Pipeline** → `runner.py :: run_job(canary_mode=True/False)`
5. **Step Chain + Cross-Claim Chain** → all 20 claims + anchor_hash MTR-1→DT-FEM-01→DRIFT-01
6. **Bundle Signing (HMAC-SHA256 + Ed25519)** → `mg_sign.py` + `mg_ed25519.py` [test_cert07 + test_cert09]
7. **Temporal Commitment (NIST Beacon)** → `mg_temporal.py` [test_temporal + test_cert10]
8. **5-Layer Independence (CERT-11 coordinated + CERT-12 encoding)** → test_cert11 + test_cert12 [proves each layer catches attacks others miss]

---

## How to verify

```bash
python scripts/steward_audit.py          # → STEWARD AUDIT: PASS
python -m pytest tests/ -q               # → 2078 passed
python scripts/deep_verify.py            # → ALL 13 TESTS PASSED
python demos/open_data_demo_01/run_demo.py  # → PASS PASS

# Run adversarial gauntlet
python -m pytest tests/steward/test_cert05_adversarial_gauntlet.py -v
python -m pytest tests/steward/test_cert06_real_world_scenarios.py -v
```

---

## What is next

- [ ] First paying customer ($299 via email) -- TOP PRIORITY
- [ ] Wave-2 outreach: Chollet, LMArena, Percy Liang (drafts ready)
- [ ] Non-provisional patent attorney (deadline 2027-03-05)
- [ ] Zenodo DOI (metadata ready in .zenodo.json)
- [ ] JOSS resubmission (Sep 2026, 6 months public history required)
- [ ] YC S26 (deadline 2026-05-04)
- [ ] r/MachineLearning post, MLOps Community Slack

---

## Outreach tracker (21 sent + 8 new wave-2 drafts)

| Name | Email | Status |
|------|-------|--------|
| Tongqi Wen | tongqwen@gmail.com | Sent 2026-03-05 |
| Giovanni Pizzi | giovanni.pizzi@psi.ch | Sent 2026-03-07 |
| Brian Nosek | ban2b@virginia.edu | Sent + follow-up |
| Peter Coveney | p.v.coveney@ucl.ac.uk | Sent + follow-up |
| Arvind Narayanan | arvindn@cs.princeton.edu | Sent + follow-up |
| Jeffrey Ip (Confident AI) | jeffreyip@confident-ai.com | Sent 2026-03-11 |
| Elena Samuylova | founders@evidentlyai.com | Sent 2026-03-16 |
| Jonah Cool (Anthropic) | jonah@anthropic.com | Sent + follow-up |
| Anand Kannappan (Patronus AI) | anand@patronus.ai | Sent 2026-03-16 |
| Vikram Chatterji (Galileo AI) | vikram@galileo.ai | Sent 2026-03-16 |
| Woody Sherman (PsiThera) | woody.sherman@psithera.com | Sent 2026-03-16 |
| Jonathan Godwin (Orbital) | jonathan@orbitalmaterials.com | Sent 2026-03-16 |
| Joelle Pineau (McGill) | jpineau@cs.mcgill.ca | Sent 2026-03-16 |
| Stella Biderman (EleutherAI) | stella@eleuther.ai | Sent 2026-03-16 |
| Koustuv Sinha (Meta FAIR) | koustuv.sinha@gmail.com | Sent 2026-03-16 |
| Victoria Stodden (USC) | stodden@usc.edu | Sent 2026-03-16 |
| Sayash Kapoor (Princeton) | sayashk@princeton.edu | Sent 2026-03-16 |
| MLRC Princeton | ailab@princeton.edu | Sent 2026-03-16 |
| Papers With Code | hello@paperswithcode.com | Sent 2026-03-16 |
| Anthropic OSS Program | form | Submitted 2026-03-16 |
| Anthropic Partner Network | contact sales | Submitted 2026-03-16 |
| François Chollet | chollet@google.com | Draft (wave-2) |
| LMArena | support@lmarena.ai | Draft (wave-2) |
| Percy Liang (HELM) | pliang@cs.stanford.edu | Draft (wave-2) |
| Colin White (LiveBench) | colinarwhite@gmail.com | Draft (wave-2) |
| EU AI Office | ai-office@ec.europa.eu | Draft (wave-2) |
| FDA Digital Health | digital.health@fda.hhs.gov | Draft (wave-2) |
| Sebastian Raschka | mail@sebastianraschka.com | Draft (wave-2) |
| Weights & Biases | support@wandb.com | Draft (wave-2) |

*All outreach from yehor@metagenesis-core.dev (Zoho), NOT Gmail.*

---

*Updated: 2026-04-08 | Next update: first response or first client*
