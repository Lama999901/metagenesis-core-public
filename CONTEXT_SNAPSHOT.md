# CONTEXT_SNAPSHOT.md — Live State for AI Agents

> Read this file first if you are an AI agent starting a new session.
> This is the authoritative snapshot of what has been done and what is next.
> Updated: 2026-03-15

---

## Project identity

- **What:** Open verification protocol for computational claims (NOT a simulation platform)
- **Inventor:** Yehor Bazhynov
- **PPA:** USPTO #63/996,819 — filed 2026-03-05 — non-provisional deadline 2027-03-05
- **Repo:** https://github.com/Lama999901/metagenesis-core-public
- **Site:** https://metagenesis-core.dev (Vercel, auto-deploys from main)
- **Email:** yehor@metagenesis-core.dev
- **Stripe:** https://buy.stripe.com/14AcN57qH19R1qN3QQ6Na00 — $299/license

---

## Verified state (2026-03-15)

| Parameter | Value |
|---|---|
| Tests | **223 passing** |
| steward_audit | PASS |
| CI | GREEN |
| Active claims | **14**: MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01 |
| Verification layers | 3 (integrity + semantic + step chain) |
| Innovations | 5 + Cross-Claim Chain |
| Domains | 7: materials, sysid, data, ml, digital_twin, pharma_biotech, financial_risk |
| Last PR merged | Summit 5-8: PHARMA-01 + FINRISK-01 + DT-SENSOR-01 + DT-CALIB-LOOP-01 — **14 claims, 223 tests** |
| Site counters | 14 claims / 223 tests / 3 layers |
| known_faults entries | 2: ENV_001 (test env) + SCOPE_001 (physical anchor scope) |
| HN post | https://news.ycombinator.com/item?id=47335416 — active |
| GitHub Release | v0.1.0 — published at /releases/tag/v0.1.0 |

---

## 14 active claims

| Claim | Domain | Threshold | Physical Anchor |
|-------|--------|-----------|-----------------|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | E = 70 GPa (aluminum) |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | Physical constant |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03` | Physical constant |
| SYSID-01 | System Identification | `rel_err_a/b ≤ 0.03` | — |
| DATA-PIPE-01 | Data Pipelines | schema + range pass | — |
| DRIFT-01 | Drift Monitoring | `drift ≤ 5.0%` | MTR-1 anchor |
| ML_BENCH-01 | ML — Classification Accuracy | `\|Δacc\| ≤ 0.02` + Step Chain | — |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | MTR-1 anchor |
| ML_BENCH-02 | ML — Regression (RMSE, MAE, R²) | `\|ΔRMSE\| ≤ 0.02` | — |
| ML_BENCH-03 | ML — Time-Series (MAPE) | `\|ΔMAPE\| ≤ 0.02` | — |
| PHARMA-01 | Pharma — ADMET (5 properties) | `\|Δprop\| ≤ tolerance` | — (FDA 21 CFR Part 11) |
| FINRISK-01 | Finance — VaR (Basel III/IV) | `\|ΔVaR\| ≤ tolerance` | — |
| DT-SENSOR-01 | IoT — Sensor Integrity | schema + range + temporal | — |
| DT-CALIB-LOOP-01 | Digital Twin — Convergence | `drift_pct decreasing + final ≤ threshold` | DRIFT-01 anchor |

Physical anchor applies to: MTR-1/2/3, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01.
Documented in `reports/known_faults.yaml` :: SCOPE_001.

---

## 5 patentable innovations

1. **Governance-Enforced Bidirectional Claim Coverage** → `steward_audit.py :: _claim_coverage_bidirectional()`
2. **Tamper-Evident Bundle + Semantic Verification** → `mg.py :: _verify_pack() + _verify_semantic()`
3. **Policy-Gate Immutable Evidence Anchors** → `mg_policy_gate_policy.json` (locked_paths)
4. **Dual-Mode Canary Execution Pipeline** → `runner.py :: run_job(canary_mode=True/False)`
5. **Step Chain + Cross-Claim Cryptographic Chain** → all 14 claims + anchor_hash MTR-1→DT-FEM-01→DRIFT-01

---

## Cross-Claim Chain (Physical Anchor Chain)

```
E = 70 GPa (physical reality — measured in thousands of labs)
    ↓  MTR-1 calibrates against this
MTR-1  trace_root_hash: "abc..."
    ↓  anchor_hash="abc..." baked into DT-FEM-01 Step 1
DT-FEM-01  trace_root_hash: "def..."
    ↓  anchor_hash="def..." baked into DRIFT-01 Step 1
DRIFT-01   trace_root_hash: "ghi..."
```

Verify full chain: `python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/`

---

## How to verify everything works

```bash
python scripts/steward_audit.py          # → STEWARD AUDIT: PASS
python -m pytest tests/ -q               # → 223 passed
python scripts/deep_verify.py            # → ALL 10 TESTS PASSED ✅
python demos/open_data_demo_01/run_demo.py  # → PASS PASS
```

---

## What is next

- [ ] GitHub Release v0.2.0 — tag after all PRs merged
- [ ] Outreach: Elena Samuylova (resend WITH subject), Anand Kannappan, Vikram Chatterji, Woody Sherman, Jonathan Godwin
- [ ] Non-provisional patent attorney (deadline 2027-03-05)
- [ ] First paying customer ($299)
- [ ] r/MachineLearning post, MLOps Community Slack

## What is done (this session 2026-03-15)

- [x] Step Chain in all 14 claims (execution_trace + trace_root_hash)
- [x] Cross-Claim Cryptographic Chain (MTR-1 → DT-FEM-01 → DRIFT-01)
- [x] ML_BENCH-02/03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01 (6 new claims)
- [x] deep_verify.py (10-test proof script) in scripts/
- [x] MVP v0.1 → v0.2 synced in all 22 backend/scripts/tests files
- [x] All docs audited: ARCHITECTURE, ROADMAP, PROTOCOL, HOW_TO_ADD_CLAIM, USE_CASES
- [x] system_manifest protocol v0.2
- [x] known_faults, CLAIMS_DRAFT_v2, USPTO_PPA_TEXT all updated to 223
- [x] .gitignore temp scripts protected
- [x] index.html site: 14/223/3/7 all correct
- [x] canonical_state.md LOCKED in policy gate

---

## Outreach tracker

| Name | Email | Status |
|------|-------|--------|
| Tongqi Wen (ElaTBot) | tongqwen@gmail.com | Sent 2026-03-05 |
| Giovanni Pizzi (PSI/AiiDA) | giovanni.pizzi@psi.ch | Sent 2026-03-07 |
| Brian Nosek (UVA/COS) | ban2b@virginia.edu | Sent 2026-03-07 |
| Peter Coveney (UCL) | p.v.coveney@ucl.ac.uk | Sent 2026-03-08 |
| Arvind Narayanan (Princeton) | arvindn@cs.princeton.edu | Sent 2026-03-08 |
| Jeffrey Ip (Confident AI) | jeffreyip@confident-ai.com | Sent 2026-03-11 |
| Elena Samuylova (Evidently AI) | founders@evidentlyai.com | Sent 2026-03-11 — NO SUBJECT — resend needed |
| Jonah Cool (Anthropic) | jonah@anthropic.com | Sent 2026-03-12 |
| Anand Kannappan (Patronus AI) | anand@patronus.ai | PENDING |
| Vikram Chatterji (Galileo AI) | vikram@galileo.ai | PENDING |
| Woody Sherman (PsiThera) | woody.sherman@psithera.com | PENDING |
| Jonathan Godwin (Orbital) | jonathan@orbitalmaterials.com | PENDING — verify email |

*All outreach from yehor@metagenesis-core.dev (Zoho), NOT Gmail.*

---

*Updated: 2026-03-15 | Maintained by: Yehor Bazhynov*
*Next update: after first paying customer or new claim*
