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

## Verified state (2026-03-11)

| Parameter | Value |
|---|---|
| Tests | 107 passing |
| steward_audit | PASS |
| CI | GREEN |
| Active claims | 8: MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01 |
| Last PR merged | #28 feat/physics-demo-section — counters 8/107, DT-FEM-01 card |

---

## What was done (chronological, 2026-03-10/11)

1. Full repo audit — 91 tests, all clean, steward_audit PASS
2. CI fix — PR #10 merged
3. Show HN post — fully written, not yet posted
4. Cold outreach emails sent:
   - Jeffrey Ip (Patronus AI) — sent
   - Elena Samuylova (Evidently AI) — sent
   - Giovanni Pizzi (PSI/AiiDA) — sent
   - Brian Nosek (UVA/reproducibility) — sent
5. Website improvements (PR #14 merged):
   - Founder story expanded (construction background, Claude, 500+ modules)
   - "In plain language" block added before How It Works
   - $B stat replaced with verifiable 50% VentureBeat stat
   - Mobile compare table: all 5 columns now visible (was cut off)
   - Mobile header labels shortened: MG / ML / Audit / PDF

---

## What is next (priority order)

- [ ] POST Show HN — obnovit' tekst: 8 claims, 107 tests
- [x] Send outreach: Peter Coveney (UCL) — sent 2026-03-08
- [x] Send outreach: Arvind Narayanan (Princeton) — sent 2026-03-08
- [ ] Find Emanuele Bosoni email (EPFL) and send outreach
- [ ] Post to MLOps Community Slack #tools-and-frameworks
- [ ] Post to r/MachineLearning [P] post
- [ ] DM @sayaboringthing (Sayash Kapoor) on Twitter/X
- [ ] Create GitHub Release v0.1.0
- [ ] Set up Stripe Payment Link ($299)
- [ ] Find patent attorney for non-provisional review before 2027-03-05
- [ ] TODO-NON-PROV-01: ppa/CLAIMS_DRAFT_v2.md with DRIFT-01 + ML_BENCH-01

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

- "tamper-proof" → use "tamper-evident"
- "19x performance advantage"
- "GPT-5 integration"
- "VacuumGenesisEngine"
- "100% test success"
- "500+ modules" (in code claims — ok in founder story context only)

---

## Key contacts (outreach tracker)

| Name | Email | Org | Status | Subject |
|---|---|---|---|---|
| Tongqi Wen | tongqwen (Gmail) | ElaTBot / atomistic sim | Sent 2026-03-05 | Verification layer for ElaTBot predictions |
| Giovanni Pizzi | giovanni.pizzi@psi.ch | PSI / AiiDA | Sent 2026-03-07 | Verification layer for AiiDA-generated computational claims |
| Brian Nosek | ban2b@virginia.edu | UVA / COS | Sent 2026-03-07 | Machine-enforceable claim verification layer beyond preregistration |
| Peter Coveney | p.v.coveney@ucl.ac.uk | UCL | Sent 2026-03-08 | Open-source tamper-evident verification layer for computational science claims |
| Arvind Narayanan | arvindn@cs.princeton.edu | Princeton | Sent 2026-03-08 | A technical layer for verifiable ML accuracy claims |
| Jeffrey Ip | jeffreyip@confident-ai.com | Confident AI / DeepEval | Sent 2026-03-11 | Offline-verifiable evidence bundles for DeepEval results |
| Elena Samuylova | founders@evidentlyai.com | Evidently AI | Sent 2026-03-11 | (no subject — check draft) |
| Emanuele Bosoni | — | EPFL | Find email first | — |
| Anand Kannappan | patronus.ai/contact | Patronus AI | PENDING | — |

---

*This file is maintained by the inventor. Update after each working session.*
