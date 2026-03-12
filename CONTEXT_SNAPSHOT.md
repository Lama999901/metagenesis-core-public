# CONTEXT_SNAPSHOT.md — Live State for AI Agents

> Read this file first if you are an AI agent starting a new session.
> This is the authoritative snapshot of what has been done and what is next.
> Updated: 2026-03-12

---

## Project identity

- **What:** Open verification protocol for computational claims (NOT a simulation platform)
- **Inventor:** Yehor Bazhynov
- **PPA:** USPTO #63/996,819 — filed 2026-03-05 — non-provisional deadline 2027-03-05
- **Repo:** https://github.com/Lama999901/metagenesis-core-public
- **Site:** https://metagenesis-core.dev (Vercel, auto-deploys from main)
- **Email:** yehor@metagenesis-core.dev

---

## Verified state (2026-03-12)

| Parameter | Value |
|---|---|
| Tests | 107 passing |
| steward_audit | PASS |
| CI | GREEN |
| Active claims | 8: MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01 |
| Last PR merged | #31 fix/site-audit-8-changes — 6 verticals, DT-FEM-01 verifier tab, mobile CSS |
| Site counters | 8 claims / 107 tests — CORRECT on live site |
| Stripe | buy.stripe.com/14AcN57qH19R1qN3QQ6Na00 — active at $299 |

---

## 8 active claims (full list)

| Claim | Domain | Threshold | File |
|---|---|---|---|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | backend/progress/mtr1_calibration.py |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | backend/progress/mtr2_thermal_conductivity.py |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03, rel_err_r ≤ 0.05` | backend/progress/mtr3_thermal_multilayer.py |
| SYSID-01 | System Identification | `rel_err_a ≤ 0.03, rel_err_b ≤ 0.03` | backend/progress/sysid1_arx_calibration.py |
| DATA-PIPE-01 | Data Pipelines | `schema pass · range pass` | backend/progress/datapipe1_quality_certificate.py |
| DRIFT-01 | Drift Monitoring | `drift_threshold 5.0%` | backend/progress/drift_monitor.py |
| ML_BENCH-01 | ML Benchmarking | `|actual − claimed| ≤ 0.02` | backend/progress/mlbench1_accuracy_certificate.py |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | backend/progress/dtfem1_displacement_verification.py |

**PPA filing basis (FROZEN):** MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01 (5 claims, 39 tests)
**Post-filing (include in non-provisional):** DRIFT-01, ML_BENCH-01, DT-FEM-01

---

## What was done (chronological)

| Date | Event |
|---|---|
| 2026-03-05 | PPA filed: 5 claims, 39 tests |
| 2026-03-07 | Outreach: Giovanni Pizzi (PSI/AiiDA), Brian Nosek (UVA) |
| 2026-03-08 | Outreach: Peter Coveney (UCL), Arvind Narayanan (Princeton) |
| 2026-03-09 | DRIFT-01 + ML_BENCH-01 added → 7 claims, 91 tests |
| 2026-03-10 | steward_audit.py CI-sealed; runner.py duplicates removed |
| 2026-03-11 | DT-FEM-01 added → 8 claims, 107 tests. Outreach: Jeffrey Ip (Confident AI), Elena Samuylova (Evidently AI) |
| 2026-03-12 | PR #26 (physics demo section) merged. PR #31 (site audit: 6 verticals, DT-FEM-01 verifier, mobile CSS) merged. Show HN email sent to Tom (moderator). Tom replied: ready to front page when Yehor is online. Reply sent: available after 17:00 PST. Outreach: Jonah Cool (Anthropic Head of Life Sciences). |

---

## What is next (priority order)

- [ ] **TONIGHT 17:00 PST** — email Tom (hn@ycombinator.com): "ready now" → HN front page
- [ ] Monitor HN thread, respond to comments actively (answers prepared)
- [ ] Show HN: post text ready — 8 claims, 107 tests — update if needed
- [ ] Commit + push index.html changes (91→107, DT-FEM-01 in pitch+terminal)
- [ ] Follow-up: Elena Samuylova (sent without subject 2026-03-11)
- [ ] Find Emanuele Bosoni email (EPFL) and send outreach
- [ ] Anand Kannappan (Patronus AI) — patronus.ai/contact
- [ ] Post to MLOps Community Slack #tools-and-frameworks
- [ ] Post to r/MachineLearning [P] post
- [ ] Create GitHub Release v0.1.0 (tag exists: v0.1.0-ppa-filing)
- [ ] Patent attorney for non-provisional review before 2027-03-05 (~$3K–8K)

---

## Git workflow

```powershell
# Repo is at:
cd C:\Users\999ye\Downloads\metagenesis-core-public

# Make changes, then:
git checkout -b fix/your-description
git add <files>
git commit -m "type: description"
git push origin fix/your-description
# Open PR on GitHub — CI runs — merge when green
```

**Main branch is protected** — direct push blocked, PR required.

---

## Files to NEVER touch without explicit instruction

```
scripts/steward_audit.py
scripts/mg.py
scripts/mg_policy_gate_policy.json
tests/steward/test_cert02_*
ppa/CLAIMS_DRAFT.md
reports/known_faults.yaml
docs/ROADMAP.md
.github/workflows/
```

---

## Forbidden language (never use)

- "tamper-proof" → use "tamper-evident under trusted verifier assumptions"
- "19x performance advantage" (no baseline citation)
- "GPT-5 integration" (not in codebase)
- "VacuumGenesisEngine" (vibe-code, not verified)
- "100% test success" (contradicted by known_faults.yaml)
- "500+ modules" (ok in founder story context only — describes development journey)

---

## 4 patentable innovations (core, do not misrepresent)

1. **Governance-Enforced Bidirectional Claim Coverage** → `scripts/steward_audit.py :: _claim_coverage_bidirectional()`
2. **Tamper-Evident Bundle + Semantic Verification Layer** → `scripts/mg.py :: _verify_pack() + _verify_semantic()` — PROOF: `tests/steward/test_cert02_*` PASS
3. **Policy-Gate Immutable Evidence Anchor** → `scripts/mg_policy_gate_policy.json` locked_paths (5 paths)
4. **Dual-Mode Canary Execution Pipeline** → `backend/progress/runner.py :: run_job(canary_mode=True/False)`

---

## Key contacts (outreach tracker)

| Name | Email | Org | Status |
|---|---|---|---|
| Tongqi Wen | tongqwen@gmail.com | ElaTBot | Sent 2026-03-05 |
| Giovanni Pizzi | giovanni.pizzi@psi.ch | PSI / AiiDA | Sent 2026-03-07 |
| Brian Nosek | ban2b@virginia.edu | UVA / COS | Sent 2026-03-07 |
| Peter Coveney | p.v.coveney@ucl.ac.uk | UCL | Sent 2026-03-08 |
| Arvind Narayanan | arvindn@cs.princeton.edu | Princeton | Sent 2026-03-08 |
| Jeffrey Ip | jeffreyip@confident-ai.com | Confident AI / DeepEval | Sent 2026-03-11 |
| Elena Samuylova | founders@evidentlyai.com | Evidently AI | Sent 2026-03-11 (no subject — follow up) |
| Jonah Cool | jonah@anthropic.com | Anthropic (Life Sciences) | Sent 2026-03-12 |
| Tom (HN moderator) | hn@ycombinator.com | Hacker News | ACTIVE — awaiting "ready" signal |
| Emanuele Bosoni | — find email — | EPFL | PENDING |
| Anand Kannappan | patronus.ai/contact | Patronus AI | PENDING |

---

## HN front page — prepared answers

Key questions and responses are prepared. Principles:
- Always cite file path + function name for technical claims
- Never say "tamper-proof", "impossible", "unforgeable"
- Acknowledge limitations honestly — point to known_faults.yaml
- Keep answers short and specific — no marketing language

---

## How to verify everything works (run before any commit)

```bash
python scripts/steward_audit.py          # → STEWARD AUDIT: PASS
python -m pytest tests/ -q               # → 107 passed
python demos/open_data_demo_01/run_demo.py  # → PASS PASS
grep -r "tamper-proof|GPT-5|19x|VacuumGenesis" docs/ scripts/ backend/ tests/
# → empty
```

---

*Updated: 2026-03-12 | Maintained by: Yehor Bazhynov*
*Next update: after HN front page session or new claim added*
