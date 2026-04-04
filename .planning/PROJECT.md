# MetaGenesis Core — v2.0.0 Autonomous Evolution

## What This Is

MetaGenesis Core is a verification protocol layer that makes computational claims tamper-evident, reproducible, and independently auditable offline. One command (`python scripts/mg.py verify --pack bundle.zip`) certifies that a computation produced exactly this result, at exactly this time, in exactly this way. v1.0.0 ships with 1753 tests, 20 claims, 5 independent verification layers, 8 innovations, 91.9% code coverage, and automated pilot onboarding.

## Core Value

Every verification claim must be independently auditable offline with cryptographic proof of integrity, provenance, and temporal commitment.

## Requirements

### Validated

- ✓ 5-layer verification (SHA-256 integrity, semantic, step chain, Ed25519 signing, temporal commitment) — v0.4.0
- ✓ 20 active claims with 4-step step chains — v0.9.0
- ✓ Bundle signing via HMAC + Ed25519 (Innovations #6-7) — v0.4.0
- ✓ Temporal Commitment via NIST Beacon (Layer 5, Innovation #8) — v0.4.0
- ✓ Adversarial proof suite (CERT-02 through CERT-12) — v0.5.0
- ✓ deep_verify.py with 13 proof tests — v0.5.0
- ✓ Policy gate and steward audit governance — v0.3.0
- ✓ Level 3 autonomous agent forge (19 checks) — v0.9.0
- ✓ mg_client.py client bundle generator — v0.9.0
- ✓ All 24 v0.5.0 requirements complete — v0.5.0
- ✓ Wave-2 outreach sent (Patronus, Chollet, LMArena, Percy Liang) — v1.0.0
- ✓ Zenodo DOI metadata + CITATION.cff + README badge + paper.md cross-refs — v1.0.0
- ✓ 91.9% code coverage (excluding deep_verify.py) with 1753 tests — v1.0.0
- ✓ Client onboarding automation (agent_pilot.py: CSV → domain detect → bundle → email draft → queue) — v1.0.0
- ✓ Pilot queue staleness detector (agent_pr_creator.py detector #5) — v1.0.0
- ✓ System hardening: all counters consistent, all 5 gates green — v1.0.0

### Active

## Current Milestone: v2.0.0 Autonomous Evolution

**Goal:** Transform MetaGenesis Core from a protocol into a self-verifying, client-ready standard with response infrastructure, recursive integrity, and architectural seeds for the future.

**Target features:**
- Recursive self-audit (protocol verifies itself via Ed25519-signed hash baseline)
- Verification receipts (human-readable proof for clients and auditors)
- Response infrastructure (60-second reply kit for outreach contacts)
- Evolution council (evidence-based improvement proposals from system analysis)
- Agent charter (constitutional governance for autonomous agents)
- Protocol hardening (PROTOCOL.md deepening, inline code comments, CLAUDE.md updates)
- Hidden potential audit (8-lens system investigation)
- Vision seeds (4-level evolution roadmap: Protocol → Registry → Agent Economy → Self-Evolution)

### Out of Scope

- New verification layers or innovations — testing and automating what exists
- New claim domains beyond existing 20 — client onboarding uses existing claims
- Modifying steward_audit.py — sealed, CI-locked
- Real-time Zoho Mail API integration — email drafts are file-based for now
- Pricing changes — $299 is fixed, Stripe link is live
- Mobile/web dashboard — CLI-first, dashboard deferred
- deep_verify.py coverage — load_module uses subprocess, untestable without refactor

## Context

MetaGenesis Core v1.0.0 shipped 2026-04-04. 1753 tests pass, 91.9% coverage. Pilot onboarding automated end-to-end. Academic citation infrastructure ready. Wave-2+3 outreach sent 2026-04-03 to 9 contacts: Patronus AI, Bureau Veritas, Chollet (ARC-AGI), Percy Liang (HELM), LMArena, IQVIA, South Pole. Replies may arrive any time — response infrastructure is the critical path.

**Immediate priorities:**
1. First paying customer at $299 (Stripe link live, 9 outreach emails sent)
2. Response infrastructure ready for when replies come
3. Protocol self-verification (recursive integrity)
4. Zenodo DOI minting (manual — 5 min at zenodo.org)
5. JOSS resubmission (Sep 2026, 6 months public history)
6. Patent attorney engagement (deadline 2027-03-05)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Ed25519 + HMAC dual support | Existing bundles must still verify | ✓ Good |
| Temporal layer is optional/graceful | Offline-first principle | ✓ Good |
| 5-layer architecture proven independent | CERT-11 coordinated attack proof | ✓ Good |
| $299 price point | Low enough for pilot, high enough for value signal | — Pending |
| File-based email drafts (not Zoho API) | Simpler, no auth dependency, manual review before send | ✓ Good |
| agent_pilot.py as autonomous agent | Consistent with existing agent architecture | ✓ Good |
| detect_pilot_queue_stale() dict unwrap | agent_pilot saves {entries:[...]}, detector must handle both formats | ✓ Fixed in audit |

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-04-04 after v2.0.0 milestone started*
