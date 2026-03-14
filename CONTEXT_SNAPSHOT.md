# CONTEXT_SNAPSHOT.md — Live State for AI Agents

> Read this file first if you are an AI agent starting a new session.
> This is the authoritative snapshot of what has been done and what is next.
> Updated: 2026-03-14

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

## Verified state (2026-03-14)

| Parameter | Value |
|---|---|
| Tests | **113 passing** |
| steward_audit | PASS |
| CI | GREEN |
| Active claims | 8: MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01 |
| Last PR merged | #47 feat/step-chain-verification — Step Chain + 107→113 tests + all docs synced |
| Site counters | 8 claims / 113 tests — CORRECT on live site |
| known_faults entries | 2: ENV_001 (test env) + SCOPE_001 (physical anchor scope) |
| HN post | https://news.ycombinator.com/item?id=47335416 — 9 points, 4 comments |
| GitHub Release | v0.1.0 — published at /releases/tag/v0.1.0 |

---

## 8 active claims

| Claim | Domain | Threshold | File |
|---|---|---|---|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | backend/progress/mtr1_calibration.py |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | backend/progress/mtr2_thermal_conductivity.py |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03, rel_err_r ≤ 0.05` | backend/progress/mtr3_thermal_multilayer.py |
| SYSID-01 | System Identification | `rel_err_a ≤ 0.03, rel_err_b ≤ 0.03` | backend/progress/sysid1_arx_calibration.py |
| DATA-PIPE-01 | Data Pipelines | `schema pass · range pass` | backend/progress/datapipe1_quality_certificate.py |
| DRIFT-01 | Drift Monitoring | `drift_threshold 5.0%` | backend/progress/drift_monitor.py |
| ML_BENCH-01 | ML Benchmarking + Step Chain | `\|actual − claimed\| ≤ 0.02` + `trace_root_hash` | backend/progress/mlbench1_accuracy_certificate.py |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | backend/progress/dtfem1_displacement_verification.py |

**PPA filing basis (FROZEN):** MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01 (5 claims, 39 tests)
**Post-filing (include in non-provisional):** DRIFT-01, ML_BENCH-01, DT-FEM-01, Step Chain Verification

---

## Step Chain Verification — what it is (NOT blockchain)

Added 2026-03-14 to ML_BENCH-01. This is a **cryptographic hash chain** (NOT a blockchain).

```
Step 1: init_params       → hash_1 = SHA256(step1_result)
Step 2: generate_dataset  → hash_2 = SHA256(hash_1 + step2_result)
Step 3: compute_metrics   → hash_3 = SHA256(hash_2 + step3_result)
Step 4: threshold_check   → trace_root_hash = SHA256(hash_3 + step4_result)
```

- Tampering ANY step invalidates `trace_root_hash`
- Works offline, no network, no external dependency
- Analogy: Merkle tree / git commit chain
- Evidence field: `execution_trace` + `trace_root_hash` in job_snapshot.result
- Tests: `tests/ml/test_mlbench01_accuracy_certificate.py :: TestExecutionTraceChain` (6 tests)

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
| 2026-03-12 | PR #26 (physics demo) merged. PR #31 (6 verticals, DT-FEM-01 verifier, mobile CSS) merged. Show HN live. Outreach: Jonah Cool (Anthropic). |
| 2026-03-13 | HN: 9 points. Physical Anchor principle + SCOPE_001. Site: hero reframe, anchor chain section. |
| 2026-03-14 | Step Chain Verification (6 tests) → **107→113 tests**. GitHub Release v0.1.0. NLnet grants submitted (2×€30K). Emergent Ventures ($15-25K). Full doc sync to 113 tests across all files. |

---

## What is next (priority order)

- [ ] Push pending branch: `git pull origin fix/unlock-claim-index-temporary --rebase && git push origin fix/unlock-claim-index-temporary`
- [ ] Open PR fix/unlock-claim-index-temporary → merge → Vercel deploys
- [ ] Follow-up: Elena Samuylova — resend with subject line
- [ ] Outreach: Anand Kannappan (Patronus AI) — patronus.ai/contact
- [ ] Find Emanuele Bosoni email (EPFL) → outreach
- [ ] Twitter/X tweet — Step Chain bypass attack hook, tag @karpathy @sayaboringthing @ylecun
- [ ] Post to MLOps Community Slack — mlops.community/slack → #tools-and-frameworks
- [ ] Patent attorney for non-provisional (~$3K–8K) before 2027-03-05
- [ ] Update Claude Project Knowledge files (CLAUDE_PROJECT_MASTER, EVOLUTION_LOG) with 2026-03-14 state

---

## UPDATE PROTOCOL — mandatory when test count changes

**Run this PowerShell command FIRST to find ALL stale numbers:**
```powershell
Select-String "OLD_NUMBER" `
  C:\Users\999ye\Downloads\metagenesis-core-public\index.html,`
  C:\Users\999ye\Downloads\metagenesis-core-public\README.md,`
  C:\Users\999ye\Downloads\metagenesis-core-public\AGENTS.md,`
  C:\Users\999ye\Downloads\metagenesis-core-public\llms.txt,`
  C:\Users\999ye\Downloads\metagenesis-core-public\CONTEXT_SNAPSHOT.md,`
  C:\Users\999ye\Downloads\metagenesis-core-public\system_manifest.json,`
  C:\Users\999ye\Downloads\metagenesis-core-public\ppa\README_PPA.md `
  | Where-Object {$_.Line -notmatch "rgba|255,140"}
```
Empty output = no stale numbers. Proceed to push.

**GROUP A — index.html (7 places):**
1. `.hbproof-val cy` — hero badge number
2. `.ttrack` ticker — first copy
3. `.ttrack` ticker — second copy (duplicate for infinite scroll)
4. `#cn2` stats counter HTML value
5. `.std` stats description text
6. `ct(cn2, NUMBER)` JavaScript animation
7. `#l7` demo terminal "N passed in 2.70s"
8. founder story paragraph "N passing tests"
9. canonical state demo panel

**GROUP B — docs (4 files):**
1. `README.md` — badge URL `Tests-N%20passing` + acceptance command comment
2. `AGENTS.md` — acceptance command comment (if present)
3. `llms.txt` — Current state section + verify command
4. `CONTEXT_SNAPSHOT.md` — Verified state table + verify command + history

**GROUP C — manifests (2 files):**
1. `system_manifest.json` — `test_count` field
2. `ppa/README_PPA.md` — Current state line + post-filing table

**GROUP D — Project Knowledge (Claude Projects — manual upload):**
1. `CLAUDE_PROJECT_MASTER_v*.md` — update and re-upload
2. `EVOLUTION_LOG.md` — update and re-upload

---

## GIT WORKFLOW — lessons learned (from 2026-03-14 session)

```powershell
# Standard push (when branch is clean):
cd C:\Users\999ye\Downloads\metagenesis-core-public
git add <files>
git commit -m "type: description"
git push origin <branch-name>

# If push is REJECTED (remote has new commits):
git stash                                          # save local uncommitted changes
git pull origin <branch-name> --rebase             # get remote changes
git stash pop                                      # restore local changes
git push origin <branch-name>                      # now push

# Always verify current branch before push:
git branch                                         # shows current branch with *
git push origin <EXACT_BRANCH_NAME_FROM_ABOVE>    # use exact name shown
```

**Common mistake:** Committing on branch X then trying to push branch Y.
Always run `git branch` to confirm which branch you're on.

---

## Physical Anchor Principle (introduced 2026-03-13)

| Concept | Question | Applies to |
|---|---|---|
| Tamper-evident provenance | "Was the bundle modified?" | ALL 8 claims |
| Physical anchor | "Does the number agree with physical reality?" | MTR-1/2/3, DT-FEM-01, DRIFT-01 ONLY |

Chain: E = 70 GPa (aluminium, measured in thousands of labs, NOT a chosen threshold)
→ MTR-1 → DT-FEM-01 → DRIFT-01 (each step verified and independently auditable)

ML_BENCH-01, DATA-PIPE-01, SYSID-01 use chosen convention thresholds.
Documented in `reports/known_faults.yaml` :: SCOPE_001.

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

## Forbidden language

| Forbidden | Use instead |
|---|---|
| "tamper-proof" | "tamper-evident under trusted verifier assumptions" |
| "blockchain" | "cryptographic hash chain" or "Step Chain Verification" |
| "19x performance advantage" | (no baseline — never use) |
| "GPT-5 integration" | (not in codebase — never use) |
| "VacuumGenesisEngine" | (vibe-code — never use) |
| "100% test success" | "N tests PASS (steward_audit PASS)" |

---

## 4 patentable innovations

1. **Bidirectional Claim Coverage** → `scripts/steward_audit.py :: _claim_coverage_bidirectional()`
2. **Tamper-Evident Bundle + Semantic Layer** → `scripts/mg.py :: _verify_pack() + _verify_semantic()`
3. **Policy-Gate Immutable Anchors** → `scripts/mg_policy_gate_policy.json` locked_paths
4. **Dual-Mode Canary Pipeline** → `backend/progress/runner.py :: run_job(canary_mode=True/False)`

---

## Key contacts

| Name | Email | Org | Status |
|---|---|---|---|
| Tongqi Wen | tongqwen@gmail.com | ElaTBot | Sent 2026-03-05 |
| Giovanni Pizzi | giovanni.pizzi@psi.ch | PSI / AiiDA | Sent 2026-03-07 |
| Brian Nosek | ban2b@virginia.edu | UVA / COS | Sent 2026-03-07 |
| Peter Coveney | p.v.coveney@ucl.ac.uk | UCL | Sent 2026-03-08 |
| Arvind Narayanan | arvindn@cs.princeton.edu | Princeton | Sent 2026-03-08 |
| Jeffrey Ip | jeffreyip@confident-ai.com | Confident AI | Sent 2026-03-11 |
| Elena Samuylova | founders@evidentlyai.com | Evidently AI | Sent 2026-03-11 — NO SUBJECT, follow-up needed |
| Jonah Cool | jonah@anthropic.com | Anthropic Life Sciences | Sent 2026-03-12 |
| Tom (HN moderator) | hn@ycombinator.com | Hacker News | HN post live — follow-up if needed |
| Emanuele Bosoni | find email | EPFL | PENDING |
| Anand Kannappan | patronus.ai/contact | Patronus AI | PENDING |

---

## How to verify everything works

```bash
python scripts/steward_audit.py          # → STEWARD AUDIT: PASS
python -m pytest tests/ -q               # → 113 passed
python demos/open_data_demo_01/run_demo.py  # → PASS PASS
grep -r "tamper-proof|GPT-5|19x|VacuumGenesis" docs/ scripts/ backend/ tests/
# → empty
```

---

*Updated: 2026-03-14 | Maintained by: Yehor Bazhynov*
*Next update: after first paying customer, grant decision, or new claim*
