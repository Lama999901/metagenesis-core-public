# MetaGenesis Core — First Client (v1.0.0)

## What This Is

MetaGenesis Core is a verification protocol layer that makes computational claims tamper-evident, reproducible, and independently auditable offline. One command (`python scripts/mg.py verify --pack bundle.zip`) certifies that a computation produced exactly this result, at exactly this time, in exactly this way. Currently v0.9.0 LIVE with 1634 tests, 20 claims, 5 independent verification layers, and 8 innovations including Ed25519 signing and NIST Beacon temporal commitment.

## Core Value

Every verification claim must be independently auditable offline with cryptographic proof of integrity, provenance, and temporal commitment.

## Current Milestone: v1.0.0 First Client

**Goal:** Make MetaGenesis Core client-ready — automate pilot onboarding, harden coverage to 90%+, add academic citation infrastructure, and ensure every autonomous agent supports the $299 conversion pipeline.

**Target features:**
- Client onboarding automation (agent_pilot.py — form submission to verified bundle to email draft)
- Coverage boost to 90%+ (check_stale_docs, agent_evolve_self, agent_research targets)
- Zenodo DOI + CITATION.cff for academic credibility (JOSS resubmit Sep 2026)
- Pilot queue staleness detector in agent_pr_creator.py (5th detector)
- System hardening pass (fix anything that blocks first client)

## Requirements

### Validated

- ✓ 5-layer verification (SHA-256 integrity, semantic, step chain, Ed25519 signing, temporal commitment) — v0.4.0
- ✓ 20 active claims with 4-step step chains — v0.9.0
- ✓ 1634 tests passing across all verification layers — v0.9.0
- ✓ Bundle signing via HMAC + Ed25519 (Innovations #6-7) — v0.4.0
- ✓ Temporal Commitment via NIST Beacon (Layer 5, Innovation #8) — v0.4.0
- ✓ Adversarial proof suite (CERT-02 through CERT-12) — v0.5.0
- ✓ deep_verify.py with 13 proof tests — v0.5.0
- ✓ Policy gate and steward audit governance — v0.3.0
- ✓ 85.7% code coverage — v0.9.0
- ✓ Level 3 autonomous agent forge (19 checks) — v0.9.0
- ✓ mg_client.py client bundle generator — v0.9.0
- ✓ All 24 v0.5.0 requirements complete — v0.5.0
- ✓ Wave-2 outreach sent (Patronus, Chollet, LMArena, Percy Liang) — v1.0.0

### Active

- [ ] Client onboarding automation (agent_pilot.py)
- [ ] Coverage 90%+ overall
- [ ] Zenodo DOI + CITATION.cff
- [ ] Pilot queue staleness detector (agent_pr_creator.py detector #5)
- [ ] System hardening pass

### Out of Scope

- New verification layers or innovations — testing and automating what exists
- New claim domains beyond existing 20 — client onboarding uses existing claims
- Modifying steward_audit.py — sealed, CI-locked
- Real-time Zoho Mail API integration — email drafts are file-based for now
- Pricing changes — $299 is fixed, Stripe link is live
- Mobile/web dashboard — CLI-first, dashboard deferred

## Context

MetaGenesis Core v0.9.0 is LIVE. Wave-2 outreach was sent 2026-04-03 to Patronus, Chollet (ARC-AGI), LMArena, and Percy Liang (Stanford HAI). Stripe payment link is live. Zoho Mail is connected to Claude. The gap between "technically ready" and "client-ready" is: (1) pilot onboarding is 100% manual (2-hour process), (2) no academic DOI for credibility, (3) no autonomous reminder when pilot requests go stale. This milestone closes those gaps.

mg_client.py already generates bundles for demo domains. agent_pr_creator.py has 4 detectors. The pilot form (Formspree xlgpdwop) posts to metagenesis-core.dev/#pilot. Coverage reports exist at reports/COVERAGE_REPORT_*.md.

## Constraints

- **Deadline**: First client this week (2026-04-03 to 2026-04-10)
- **Sealed files**: steward_audit.py, mg_policy_gate_policy.json, CLAIMS_DRAFT.md, canonical_state.md
- **stdlib only**: No new dependencies
- **Git workflow**: All changes via branch + PR
- **All 1634 existing tests must pass**: Zero regressions
- **Commercial focus**: Every feature must serve the $299 conversion

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ed25519 + HMAC dual support | Existing bundles must still verify | ✓ Good |
| Temporal layer is optional/graceful | Offline-first principle | ✓ Good |
| 5-layer architecture proven independent | CERT-11 coordinated attack proof | ✓ Good |
| $299 price point | Low enough for pilot, high enough for value signal | — Pending |
| File-based email drafts (not Zoho API) | Simpler, no auth dependency, manual review before send | — Pending |
| agent_pilot.py as autonomous agent | Consistent with existing agent architecture | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-03 after milestone v1.0.0 start*
