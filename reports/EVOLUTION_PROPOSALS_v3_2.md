# Evolution Proposals — v3.2.0 Milestone

> **Source:** Council-style synthesis from 7 sources, conducted as part of the deeper-validation re-audit (`reports/AGENT_LEARN_DEEPER_VALIDATION_2026_04_28.md`, branch `chore/audit-data-loss-deeper-validation`).
>
> **Sources read:**
> 1. PR #283 — `reports/AGENT_LEARN_FULL_AUDIT_2026_04_28.md` (commit `ec72d0b`)
> 2. PR #283 deeper validation — `reports/AGENT_LEARN_DEEPER_VALIDATION_2026_04_28.md` (this branch)
> 3. `resolved_patterns.json` — *not accessible (lost in 2026-04-25 cleanup)*. Substituted: 10 patterns preserved in `reports/WEEKLY_REPORT_20260318.md`
> 4. EVOLUTION_LOG.md entries — *not accessible (file does not yet exist; will be created by WS-A.0 successor)*
> 5. Recent commits since 2026-04-21 — `git log main --since=2026-04-21` (3 commits: PR #281, #282, deferred WS-A.0 successor work)
> 6. Open issues / TODO comments — `agent_evolution_council.py` enumeration of council inputs
> 7. `.planning/ROADMAP.md` unfinished phases — v3.1.0 Phases 28-32 (USE_CASES, Client Journeys, Why Not Alternatives, Regulatory Gaps + README, Audit + Readiness)
>
> **Synthesis target:** 10 proposals for the v3.2.0 milestone, with at least 3 in classes A/B/C from the AGENT-LEARNING-01 framing addition.
>
> **Class taxonomy:**
> - **Class A** — AGENT-LEARNING-01 design refinements informed by the loss event
> - **Class B** — Memory persistence architecture
> - **Class C** — Loss event as future-proof case study (patent + roadmap connections)

---

## PROP-001 — [Class A] AGENT-LEARNING-01: Cryptographic baseline for observer

**Source:** Loss event (PR #283, this audit) + `EVOLUTIONARY_ARCHITECTURE.md` §3 description of `knowledge_base.json` as "permanent, auditable log."

**Problem:** Currently `agent_learn.py observe` writes session entries with no cryptographic protection. Any modification, deletion, or corruption is silent and undetectable post-fact. The 2026-04-22 → 2026-04-25 loss is the realisation of this gap.

**Proposal:** Each session entry, when written by `observe()`, is signed with the project Ed25519 key. The signature includes the previous session's signature (chain). Verification is performed by a new `agent_evolution.py` check #23 (`kb_chain_integrity`).

**Implementation sketch:**
- Schema add to each KB entry: `prev_sig`, `entry_sig`, `signed_payload_hash`
- `agent_learn.py observe`: read tail entry, sign `prev_sig + new_payload_hash`, append
- `agent_learn.py verify`: walk chain, verify each signature
- `agent_evolution.py` new check #23: invoke `agent_learn.py verify`; FAIL if chain broken or any entry has invalid signature

**Effort:** ~2 days (Ed25519 utilities already exist in `mg_ed25519.py`).

**Impact:** High. Closes a structural gap in self-verification; makes silent loss impossible.

**Patent connection:** Becomes part of AGENT-LEARNING-01 claim language ("…cryptographically chained session record…").

---

## PROP-002 — [Class A] AGENT-LEARNING-01: Append-only KB enforcement

**Source:** Loss event + first audit's observation that KB was "append-only in practice" (per `EVOLUTIONARY_ARCHITECTURE.md:64`) — but practice is not enforcement.

**Problem:** The KB schema permits arbitrary writes. A buggy `observe()` invocation, a manual edit, or a malicious modification can silently rewrite history. The current "append-only in practice" claim is a hope, not a guarantee.

**Proposal:** Add an `agent_evolution.py` check #24 (`kb_append_only`) that:
1. Reads `knowledge_base.json` snapshot from the previous CI run (committed snapshot — see PROP-004)
2. Compares: every entry in the previous snapshot must appear unchanged in the current KB; the current KB may have additional new entries appended
3. FAIL on any divergence (entry deleted, entry modified, entry inserted in middle, ordering changed)

**Implementation sketch:**
- New check `check_kb_append_only()` in `agent_evolution.py`
- Reads `docs/memory_snapshots/<latest>.json.zst` (PROP-004) as ground truth
- Diff via JSON-pointer-aware comparison

**Effort:** ~1 day (after PROP-004 lands).

**Impact:** Medium-high. Makes append-only a structural property, not a hope.

---

## PROP-003 — [Class A] AGENT-LEARNING-01: Per-session verification receipt

**Source:** First audit observed that `mg_receipt.py` produces receipts for external bundle verifications — but observer-internal sessions have no equivalent artefact.

**Problem:** A reviewer asks "show me what session 47 actually did" — currently we read the KB entry (now lost). A tamper-evident, self-contained per-session artefact would survive any KB loss.

**Proposal:** Each `agent_learn.py observe` invocation writes a session-receipt to `proof_library/session_receipts/<timestamp>_<sha-prefix>.json`. The receipt is independently verifiable offline (Ed25519 signature, anchor hash, gate outcomes embedded). Receipts are git-tracked (gitignored only for size control if they grow large; cf. PROP-006).

**Implementation sketch:**
- Add `mg_session_receipt.py` mirroring `mg_receipt.py` structure
- `agent_learn.py observe` calls receipt generator after writing KB entry
- Receipts directory committed; KB stays gitignored (PROP-004 supersedes the size argument)

**Effort:** ~1.5 days.

**Impact:** High. Receipts are independently auditable even if KB itself is lost. Lined up with the protocol's overall "every artefact is independently verifiable" thesis.

**Patent connection:** Direct AGENT-LEARNING-01 claim element.

---

## PROP-004 — [Class B] Append-only daily KB snapshots committed to repo

**Source:** Loss event. First audit §5.5.1 future-proofing recommendation #1.

**Problem:** `.agent_memory/knowledge_base.json` is gitignored (line 97 of `.gitignore`). Reasonable per-PR-churn argument, but provides zero loss recovery surface.

**Proposal:** Daily compressed snapshot of `knowledge_base.json` committed to `docs/memory_snapshots/YYYY-MM-DD.json.zst` (or per-release-tag instead of daily, depending on observed cadence). Append-only directory. Each snapshot is signed by the previous snapshot's hash (chain).

**Implementation sketch:**
- New script `scripts/agent_learn_snapshot.py` invoked by `.github/workflows/weekly_agent_health.yml`
- Workflow change is permitted under SEALED rules (`.github/workflows/` is modify-only, but adding a new file is permitted; this is *modifying* an existing workflow, requires user approval per SEALED policy — confirm scope before implementing)
- Compressed with zstd (~5–10× compression on JSON)
- Filename pattern enables `git log docs/memory_snapshots/` to show longitudinal record

**Effort:** ~1 day for script + workflow change.

**Impact:** High. Would have prevented this incident. Costs ~1 KB/day repo bloat after compression.

**Cross-reference:** PROP-002 depends on this for the previous-snapshot ground truth.

---

## PROP-005 — [Class B] Pattern signed-chain in `patterns.json`

**Source:** Loss event. First audit's recovery analysis showed that `patterns.json` had structured `auto_fix_hint` content that is now irreplaceable.

**Problem:** `patterns.json` is plain JSON; entries can be silently mutated. The 8 hand-curated `auto_fix_hint` entries that the verdict-B diagnostic identified are gone with no integrity proof of when they were added or who authored them.

**Proposal:** Add to each pattern entry: `prev_pattern_hash`, `entry_signature`, `author_attestation`. Patterns become append-only with verifiable provenance. New `agent_evolution.py` check verifies the chain.

**Implementation sketch:**
- Schema migration of existing `patterns.json` (creates a v2 schema)
- `agent_learn.py` pattern-write functions sign new entries
- New check `check_patterns_chain` in `agent_evolution.py`

**Effort:** ~1.5 days.

**Impact:** Medium. Patterns are smaller-scale than KB but the same logic applies. Makes the hand-curated `auto_fix_hint` library a verifiable archive.

---

## PROP-006 — [Class B] Minimal external backup workflow

**Source:** Loss event root cause: working-copy cleanup wiped data with no out-of-band backup.

**Problem:** Even with PROP-001/004 (in-repo cryptographic + snapshot protection), a `Downloads/` cleanup or disk failure on a single workstation could still wipe local KB before the next snapshot CI run. Belt-and-suspenders missing.

**Proposal:** A 5-line shell script (or PowerShell scheduled task) running daily on the developer workstation:
```
tar czf $HOME/.metagenesis-backups/$(date +%Y-%m-%d).tar.gz \
  --exclude='*/node_modules' --exclude='*/__pycache__' \
  $HOME/metagenesis-core-public/.agent_memory/
find $HOME/.metagenesis-backups/ -mtime +14 -delete
```

Or: enable OneDrive Personal Vault sync for `.agent_memory/` specifically (separate from the working-copy directory).

**Implementation:** Documentation, not code. Add to `CONTRIBUTING.md` or a new `OPERATIONS.md`.

**Effort:** ~30 min docs.

**Impact:** Low cost, high resilience. Should have been in place pre-loss.

---

## PROP-007 — [Class C] Cite this loss event in non-provisional patent filing

**Source:** AGENT-LEARNING-01 design intent (per user's brief addition) + AGENT_TASKS.md TASK-036 (non-provisional deadline 2027-03-05).

**Problem:** The non-provisional patent filing requires demonstrated motivation for each independent claim. AGENT-LEARNING-01 is currently planned as the 21st claim — but absent a concrete incident, its motivation reads as theoretical.

**Proposal:** When the patent attorney engagement begins (Q3 2026 per TASK-036), provide the patent attorney with:
1. `EVOLUTION_LOG.md` entry for the 2026-04-28 loss event (created by WS-A.0 successor)
2. PR #283 audit report (commit `ec72d0b`)
3. This deeper-validation report
4. The three-tier framing from §5.2: WS-A.0 → AGENT-LEARNING-01 → recursive AI evolution layer

The loss event becomes the **empirical motivation** for the AGENT-LEARNING-01 claim: a real incident demonstrating that without cryptographic protection of the learning layer, the protocol's "proof not trust" guarantee is incomplete.

**Implementation:** Document handoff to attorney; no code.

**Effort:** ~2 hours (assemble document bundle for attorney).

**Impact:** Strengthens patent filing. Real-world incident citations carry more weight than hypothetical motivation.

---

## PROP-008 — [Class C] Update `docs/ROADMAP_VISION.md` to connect AGENT-LEARNING-01 to recursive AI evolution

**Source:** AGENT-LEARNING-01 design intent + the three-tier framing in deeper-validation §5.2.

**Problem:** `docs/ROADMAP_VISION.md` (per first-audit grep) describes the protocol's evolution but does not yet articulate why AGENT-LEARNING-01 is structurally necessary for higher-autonomy levels (the recursive AI evolution layer).

**Proposal:** Add a section to `docs/ROADMAP_VISION.md` that articulates:
> Without a verified, signed, append-only learning layer, recursive AI evolution has no audit trail. AGENT-LEARNING-01 closes that gap by applying the protocol's 5-layer verification to the learning record itself. The 2026-04-28 loss event (see EVOLUTION_LOG.md) is the empirical proof that this gap exists today and must be closed before the protocol scales to higher autonomy.

**Implementation:** ~10 line edit to `docs/ROADMAP_VISION.md` + cross-link.

**Effort:** ~1 hour.

**Impact:** Narrative coherence. Connects loss event → claim → vision.

---

## PROP-009 — v3.1.0 Phases 28-32 execution

**Source:** `.planning/ROADMAP.md` lines 89-93 — five phases ready to plan.

**Problem:** v3.1.0 Documentation Deep Pass is `roadmap_defined` but no phase has begun planning. Five phases × 31 requirements outstanding.

**Proposal:** After WS-A.0 successor merges, proceed with `/gsd-plan-phase 28` (USE_CASES Deep Rewrite) per `STATE.md:30`. Phases 28-31 can run in parallel waves (independent per `STATE.md:42`); Phase 32 is terminal audit gate.

**Effort:** Per-phase budget per ROADMAP — not estimated here.

**Impact:** Closes v3.1.0 milestone, unblocks v3.2.0 milestone planning.

**Cross-reference:** v3.2.0 milestone planning should incorporate PROP-001..PROP-008 as concrete phase candidates.

---

## PROP-010 — Fix `semantic_audit` 1/22 FAIL (4 client-scenario demos verify=False)

**Source:** Deeper-validation §2 (this audit) — confirmed pre-existing since at least 2026-04-12.

**Problem:** `agent_evolution.py --summary` reports 21/22 PASS. The 1 FAIL is `semantic_audit` due to 4 client-scenario demos (NeuralBench, PsiThera, QuantRisk, AeroSim) running narrative scripts but not producing verifiable bundles.

**Proposal:** Extend each `demos/client_scenarios/<n>/run_scenario.py` to invoke `mg_claim_builder.py` for its representative claim and emit a real bundle. Each demo gets a bundle artefact; `semantic_audit` then sees `run=True, verify=True` and passes.

**Implementation sketch:**
- For each of 4 demos, identify representative claim:
  - 01_ai_benchmark → ML_BENCH-01 or ML_BENCH-02
  - 02_pharma → PHARMA-01
  - 03_finance → FINRISK-01
  - 04_digital_twin → DT-FEM-01
- Add `mg_claim_builder.py` invocation at end of each `run_scenario.py`
- Bundle output goes to `demos/client_scenarios/<n>/bundle/`
- `semantic_audit` check picks up the bundle automatically

**Effort:** ~1 day (4 demos × ~2 hours each).

**Impact:** 22/22 gate. Closes a long-standing pre-existing FAIL; protocol-aligned (every demo produces a verifiable artefact).

**Note:** Out of scope for WS-A.0 successor; appropriate for an early v3.2.0 quick task or as part of v3.1.0 Phase 28.

---

## Class distribution

- **Class A — AGENT-LEARNING-01 design**: PROP-001, PROP-002, PROP-003 (3)
- **Class B — Memory persistence**: PROP-004, PROP-005, PROP-006 (3)
- **Class C — Loss-event case study**: PROP-007, PROP-008 (2)
- **Other (v3.1.0 / v3.2.0 housekeeping)**: PROP-009, PROP-010 (2)

**Total: 10 proposals; 8 in classes A/B/C** (≥3 requirement met three times over).

---

## Synthesis verdict

The loss event reframes AGENT-LEARNING-01 from a planned-future claim into an **architecturally required claim**. PROP-001 through PROP-005 collectively close the structural gap the loss event exposed. PROP-006 is the operational backstop. PROP-007 and PROP-008 carry the lesson into patent and vision documentation. PROP-009 and PROP-010 are housekeeping items that should not be lost in the v3.2.0 planning.

**Recommendation to roadmap planner:** v3.2.0 should explicitly bundle PROP-001 + PROP-003 + PROP-004 as the AGENT-LEARNING-01 claim package. PROP-002 and PROP-005 follow as hardening. PROP-006/007/008 are documentation/operations work runnable in parallel.

— end of proposals —
