# Agent-Learn Full Audit — 2026-04-28

> **Scope:** Pre-action read-only audit of the `.agent_memory/` data loss event of 2026-04-24/25, before any public-doc reaction or observer restart.
> **Mode:** Read-only. No `observe` runs. No `.agent_memory/` files modified.
> **Branch:** `chore/audit-data-loss-pre-recovery`
> **Successor task:** Will be issued by user after reviewing Phase 5 verdict.

---

## Executive Summary

On or before 2026-04-25 ~08:32 UTC, a routine cleanup of `C:\Users\999ye\Downloads\metagenesis-core-public\` deleted the local working copy of `.agent_memory/` along with several uncommitted artefacts. Recovery via git, VSS shadow copy, OneDrive, and File History was previously exhausted. This audit answers three questions before any reactive action.

### What was lost
- **`.agent_memory/knowledge_base.json`** — ~125 per-session entries spanning 2026-03-18 → 2026-04-16 (per `README.md:427`, `llms.txt:130`, and PR #280).
- **`.agent_memory/resolved_patterns.json`** — 15 entries (8 hand-curated + 7 observed) per the verdict-B framing.
- **`.agent_memory/strategic_memory.json`**, **`project_trajectory.json`**, **`security_learnings.json`**, **`verification_stats.json`** — derived synthesis outputs (per `docs/EVOLUTIONARY_ARCHITECTURE.md` §3 and `AGENT_TASKS.md` TASK-028).
- **8+ quick-task directories** from 2026-04-07 → 2026-04-21, including `260421-s3f-agent-learn-diagnostic` (the directory that produced the "verdict B" framing). All were `_pending_` for commit per `STATE.md:111` and never reached git.
- **Lessons.md** — referenced in `agent_learn.py` docstring; not on disk, no commit history.

### What survived
- `.agent_memory/patterns.json` (2 bytes — empty `{}`) and `client_sessions.json` (10 fresh ML-domain entries, all from 2026-04-25 morning).
- 47 quick-task directories from 2026-03-17 → 2026-04-03 (date-prefixed slugs preserve session topics).
- 137 commits / squash-merged PRs in the audit period across 19 active days.
- 8 release tags (v0.5.0 → v3.0.0 / v1.0.0-rc1) anchoring the period.
- 27 reports under `reports/` including `WEEKLY_REPORT_20260318/19.md` (preserve early-period pattern schema with `auto_fix` hints), `AGENT_REPORT_20260318/19/29.md`, `AUDIT_TRUTH_20260401/02.md`, `EXPANDED_AUDIT_20260401.md`, `RECURSION_ANALYSIS.md`, `READINESS_ASSESSMENT.md`.
- `session_log.jsonl` (3 high-level milestone entries, 2026-04-06 / -09).

### System health post-loss
**Zero functional impact.** All gates that matter pass:
- pytest: 2407 passed, 1 skipped (29.38 s) — matches expected baseline.
- `steward_audit.py`: PASS.
- `deep_verify.py`: 13/13 PASS.
- `check_stale_docs.py --strict`: 8 CURRENT, 0 STALE.
- `mg.py verify --pack demos/open_data_demo_01/pack/`: PASS.
- `agent_evolution.py --summary`: **21/22 PASS** with one pre-existing FAIL (`semantic_audit` — 4 client demos `run=True, verify=False`; unrelated to `.agent_memory/`).

### Quantified loss
- **Recoverable from commits:** ~80% of the *substantive* content (every detection event left a fix commit; every milestone left a tag; every quick-task <2026-04-04 left a directory; weekly reports preserve schema).
- **Truly unrecoverable:** ~20% — timestamp-of-detection precision, severity assessment metadata, the 8 hand-curated `auto_fix_hint` entries (the irreplaceable artefact), and the aggregate clean-ratio time series.
- **Effective information loss:** **~20% of structured content; ~5% of operational value** — the protocol's *verifiable* claims (cryptography, claim count, test count, real ratio, coverage) are completely intact. Only the *narrative* about the protocol's evolution lost detail.

### Recommendation (full reasoning in §5)
**Option C — Full transparent registration.** Loss event recorded in a new `EVOLUTION_LOG.md` (file does not currently exist; this is its first entry). Public-doc claims about "120/125 sessions" replaced with verifiable language. Audit artefact (this file) becomes the receipt.

---

## PHASE 1 — Recovery Audit

### 1.1 `vault_ready/` inventory

**Result:** Directory does not exist.

```
Test-Path C:\Users\999ye\metagenesis-core-public\vault_ready  →  False
```

No institutional memory was ever preserved at this location. The user's task-brief reference to `vault_ready/` reflects an architectural intention that never materialised.

### 1.2 `.agent_memory/` current state

```
Name                  Length    LastWriteTime          Mode
client_sessions.json    1854    2026-04-25 08:40:04    -a----
patterns.json              2    2026-04-25 08:32:40    -a----
```

- `patterns.json` content: `{}` (2 bytes — empty per design after the 2026-04-12 synthesis migration moved active→resolved).
- `client_sessions.json` content: JSON array of 10 ML-domain pilot sessions, all `result: PASS`, all timestamped 2026-04-25 16:33 → 16:40 UTC, all with empty `claim_id`, `bundle_path`, `notes`. This file is **not the lost knowledge_base.json under another name** — it tracks pilot-mode client verification runs (governed by `agent_client.py`), not internal agent sessions.
- No backup files (`.bak`, `~`, `.old`) in the directory or its parent.

### 1.3 `reports/` inventory

27 files in `reports/` plus 6 subdirectories. Files with direct relevance to reconstruction:

| File | Size | Date | Relevance |
|---|---|---|---|
| `WEEKLY_REPORT_20260318.md` | 2,195 | 2026-03-18 | Day-1 system health (10/10 checks) + 10 patterns w/ fix hints |
| `WEEKLY_REPORT_20260319.md` | 3,247 | 2026-03-19 | Day-2 (14/14 checks) + same 10 patterns |
| `AGENT_REPORT_20260318.md` | 5,719 | 2026-03-18 | Detailed agent run |
| `AGENT_REPORT_20260319.md` | 348 | 2026-03-19 | Brief |
| `AGENT_REPORT_20260329.md` | 4,125 | 2026-03-29 | Mid-period |
| `AGENT_REPORT_20260402b.md` | 2,167 | 2026-04-02 | Pre-v0.9.0 |
| `AUDIT_TRUTH_20260401.md` | 6,576 | 2026-04-01 | Truth audit |
| `AUDIT_TRUTH_20260402.md` | 5,052 | 2026-04-02 | Follow-up |
| `EXPANDED_AUDIT_20260401.md` | 9,053 | 2026-04-01 | Deep audit |
| `RECURSION_ANALYSIS.md` | 5,062 | (preserved) | Confirms patterns.json had 15 patterns at v1.0.0-rc1 |
| `STEWARD_REPORT_20260411.md` | 2,918 | 2026-04-11 | v3.0.0 ship gate |
| `SELF_IMPROVEMENT_20260319.md` | 2,037 | 2026-03-19 | Pattern-derived improvements |
| `READINESS_ASSESSMENT.md` | 25,508 | (preserved) | World-readiness (no session refs found) |
| `WAVE2_OUTREACH_DRAFTS.md` | 4,502 | (preserved) | Outreach state |

**No `AGENT_LEARN_DIAGNOSTIC.md` exists** in `reports/` or anywhere in the repo, on any branch, in any commit. The user's task brief expected this file as a Verdict-B context source. Investigation (§2.3) shows the diagnostic was a quick-task at `.planning/quick/260421-s3f-agent-learn-diagnostic/`, which is also lost (never committed).

### 1.4 `session_log.jsonl` analysis

3 entries — high-level milestone records, not per-session detail:

| Date | Tests | Real-ratio | Summary |
|---|---|---|---|
| 2026-04-06 02:22 | 2043 | 4.76 % | mg_claim_builder + 31 tests + proof_library |
| 2026-04-06 02:24 | 2063 | 4.76 % | +20 tests within ~2 min |
| 2026-04-09 05:02 | 2132 | 51.22 % | Full audit 10/10, Stripe live, 8/8 domains |

**Comparison with the lost `knowledge_base.json`:**
- `session_log.jsonl` = curated milestone summaries written by `scripts/session_close.py` (3 entries in 30 days; sparse).
- `knowledge_base.json` = per-CI-run entries written by `agent_learn.py observe` (~125 entries in 30 days; dense).
- These were complementary, not redundant. The milestones survive; the dense per-session record does not.

### 1.5 Git tag inventory

8 release tags in the audit window — implicit milestone markers:

| Tag | Date | Subject |
|---|---|---|
| v0.5.0 | 2026-03-18 | Feat/agent evolution v2 (#129) |
| v0.6.0 | 2026-03-19 | fix: claims count 14→15 (#164) |
| v0.7.0 | 2026-03-21 | Fix/sync stale docs (#183) |
| v0.8.0 | 2026-03-29 | Fix/phys visibility (#194) |
| v0.9.0 | 2026-04-02 | Release v0.9.0 (#236) |
| v1.0.0 | 2026-04-03 | First Client |
| v2.0.0 | 2026-04-04 | Autonomous Evolution |
| v1.0.0-rc1 | 2026-04-11 | Recursive evolution (#270) |

This tag chain alone establishes 8 verifiable inflection points across the lost-data window. Each tag is independently re-verifiable via `git show <tag>`.

### 1.6 `.planning/` state

From `STATE.md` (frontmatter + body):
- **Milestone:** v3.1.0 (Documentation Deep Pass) — `roadmap_defined`, 5 phases (28-32), 31 requirements mapped.
- **Last activity:** 2026-04-22 — "Completed quick task 260421-s3f: agent_learn recursion signal diagnostic (verdict B — partial)".
- The `260421-s3f` directory is referenced in the `Quick Tasks Completed` table with commit hash `_pending_` — i.e. work was done locally but never committed. **The directory is now missing from disk.**

From `ROADMAP.md`:
- v0.4.0 → v3.0.0 all shipped. v3.1.0 is docs-only (no new claims).
- **Cumulative test trajectory:** 511 → 2407 across the audit window (verifiable via tag content).

GSD planning is internally coherent and contains no stale references to the lost data.

---

## PHASE 2 — Reconstruction Audit

### 2.1 Commit-history reconstruction

**137 commits in period 2026-03-18 → 2026-04-16** across 19 active days (out of 30).

Commits-per-day (all working days):

```
2026-03-18: 15    2026-03-19: 17    2026-03-20:  7    2026-03-21:  4
2026-03-26:  3    2026-03-29:  9    2026-03-30:  9    2026-03-31: 13
2026-04-01: 10    2026-04-02:  9    2026-04-03:  7    2026-04-04:  5
2026-04-05:  1    2026-04-07:  9    2026-04-08:  5    2026-04-10:  1
2026-04-11:  6    2026-04-12:  4    2026-04-16:  3
```

**Quiet days (no commits):** 2026-03-22..-25, -27, -28, 04-06, 04-09, 04-13..-15. Each represents a likely no-session-recorded day in the lost KB.

**137 commits = 137 squash-merged PRs.** Every commit on `main` carries a `(#NNN)` reference (this repo uses GitHub squash-merge as default). PR-prefix categorisation:

| Prefix | Count | Interpretation |
|---|---|---|
| feat | 11 + many "Feat/..." | New feature / claim / phase |
| fix | 20 + many "Fix/..." | Issue resolution (≈ 1:1 with dirty sessions) |
| docs | 6 | Documentation work |
| chore | 3 | Counter sync, version bumps |
| ci | 1 | CI workflow |
| audit | 1 | Audit-only commit |
| Title-Case (PR-style) | 95 | "Feat/X", "Fix/X", "Chore/X" — squash defaults |

**Estimated session-to-commit ratio:** lost KB had ~125 sessions over 137 commits → ratio ≈ 0.91 sessions per commit. Tight coupling indicates the observer was running close to per-PR cadence (consistent with `weekly_agent_health.yml` daily auto-observe + manual triggers).

### 2.2 PR-history reconstruction (selected — full list in §A.1)

The clearest reconstruction-by-PR signal: ~30 PRs with `Fix/` prefix or fix-flavoured titles likely correspond to the **11 dirty sessions / 31 issues** the verdict-B framing referenced. Notable fix-flavoured arcs:

```
#260  2026-04-08  Fix/agentshield security
#261  2026-04-08  Fix/canvas symbols perf
#258  2026-04-07  Revert/restore index html       ← rollback event
#259  2026-04-07  Fix/index content fixes
#231  2026-04-02  fix: stale prose 18→19 / 608→1198
#235  2026-04-02  fix: precision gaps 27/27 tasks, 8 domains
#243  2026-04-03  chore: counter sync 1750→1753
#274  2026-04-12  Fix/deep audit 260412
#278  2026-04-16  Fix/test 6 forbidden terms
```

Each `Fix/*` and `chore: counter sync *` commit is a strong proxy for a dirty-session entry the observer would have recorded.

### 2.3 Diagnostic-file content extraction

`reports/AGENT_LEARN_DIAGNOSTIC.md` does not exist:
- Filesystem: not found (case-insensitive search across `C:\Users\999ye\metagenesis-core-public\`).
- Git: `git log --all --full-history -- '**/*DIAGNOSTIC*'` returns zero hits.
- Working tree grep for "Verdict B" returns zero hits in `reports/` or `.planning/`.

The diagnostic was a **quick-task** under `.planning/quick/260421-s3f-agent-learn-diagnostic/`, run on 2026-04-22 with verdict-B-partial outcome (per `STATE.md:111`). The directory is missing from disk, was never committed (`_pending_` in STATE), and is not in any reflog or fsck output (confirmed in pre-audit investigation).

**Implication:** the verdict-B framing the user task brief leans on (15 entries: 8 hand-curated + 7 observed; 11 dirty sessions; 31 issues; observer-narrow-but-real assessment) cannot be primary-sourced from this repo. The framing is preserved only in the user's working memory and the prior-conversation context.

### 2.4 Dirty-session reconstruction from commits

Cross-referencing `Fix/*` PRs against the period yields ~28 candidate dirty-session events. The verdict-B claim of **11 dirty sessions / 31 issues** is consistent with this if multiple issues clustered per session (avg ~2.8 issues per dirty session matches the count). Concrete candidate clusters:

| Cluster | Dates | Probable issues |
|---|---|---|
| Counter-sync churn | 03-19, 03-20, 03-30, 04-02, 04-03, 04-11 | Stale test counts in README/llms/known_faults |
| Forbidden-term test | 04-16 (#278) | Literal-string splitting fix |
| Agentshield security | 04-08 (#260) | Bot/abuse hardening |
| Site rollback | 04-07 (#258→#259) | index.html content regression + recovery |
| Stale-docs sweep | 03-21 (#183), 04-12 (#274) | Documentation drift |
| Coverage push | 04-02..04-03 (#229..#240) | Test additions raising real_ratio |

### 2.5 Decision audit (chronological — selected milestones)

| Date | Ref | Decision |
|---|---|---|
| 2026-03-18 | v0.5.0 | Agent evolution v2 baseline; HMAC key rotation incident; 14 checks |
| 2026-03-19 | v0.6.0, #164 | Claim 15 (AGENT-DRIFT-01) added; expected count 14→15 |
| 2026-03-21 | v0.7.0, #183 | First stale-docs sync sweep |
| 2026-03-29 | v0.8.0, #194 | Phys-visibility fix |
| 2026-04-02 | v0.9.0, #235, #236 | Precision gaps closed; 27/27 tasks; 8 domains; release |
| 2026-04-03 | v1.0.0, #240, #243 | First-client release; coverage boost; 1750→1753 |
| 2026-04-04 | v2.0.0 | Autonomous Evolution: mg_self_audit, mg_receipt, agent_responder, council |
| 2026-04-07 | #251–#259 | Phase 23–27 GSD arc: real verification, demo flow, client-facing docs, polish |
| 2026-04-08 | #263, #264 | Audit 7.8/10 → 10/10; Stripe live |
| 2026-04-11 | v1.0.0-rc1, #270, #273 | Recursive evolution; SDK + GitHub Action |
| 2026-04-12 | #275 (`0f0898b`) | Memory synthesis: synthesize command added — produced strategic_memory.json, project_trajectory.json, resolved_patterns.json (now lost) |
| 2026-04-12 | #276–#277 | Obsidian Brain vault link; README deep enhancement |
| 2026-04-16 | #278, #279, #280 (`90426e1`) | Forbidden-term fix; v3.1.0 docs deep pass; **README counter 122 → 125 sessions** ← last KB-state evidence |

This 13-row chronology is independently re-verifiable via `git show <tag>` and `gh pr view <number>` and constitutes a usable replacement institutional memory for the period. It does not replace the lost detection metadata, but it is a complete decision audit.

### 2.6 Quick-task slug reconstruction (newly discovered)

47 quick-task directories from 2026-03-17 → 2026-04-03 are intact on disk under `.planning/quick/`. Each directory name is a date-prefixed slug that **preserves session topic in plain text**. Sampled examples:

```
260318-j50-urgent-security-fix-remove-hmac-key-file
260318-jpb-fix-stale-docs-context-snapshot-llms-txt
260319-nwt-claim-15-agent-drift-01-v0-6-0-counter-sync
260319-pdj-ci-fix-readme-epic-rewrite
260320-l1i-fix-readme-md-factual-accuracy-14-checks
260330-ucg-agent-training-sprint-1-fix-agent-learn
260403-fak-fix-stale-docs-sync-counters-and-version
```

This gives **47 named session events** independently reconstructible. Combined with the 137 commits and 8 tags, the period is densely indexed even without `knowledge_base.json`.

**Lost quick-task directories** (listed in `STATE.md:103-111` but missing on disk and never in git):

```
260407-rrr-redesign-metagenesis-core-dev
260411-991-boost-coverage-83.4→90
260411-9ue-coverage-boost-phase-2
260411-aif-fix-3-ordering-dependent-test-failures
260411-aju-sync-test-count-2132→2358
260411-ifo-readme-additions-80-year-gap-talk-to-protocol-q-and-a
260412-p78-deep-audit-fix-skipped-tests-sync-2405→2407
260416-i4y-fix-test-6-forbidden-terms
260421-s3f-agent-learn-diagnostic    ← the verdict-B source
```

Topic information **survives in the STATE.md table** for these 9 lost directories. The directory contents (PLAN.md, SUMMARY.md, intermediate notes) do not.

---

## PHASE 3 — Impact Audit (real vs symbolic)

### 3.1 What the 125 sessions actually enabled

Per `docs/EVOLUTIONARY_ARCHITECTURE.md` §3 (the canonical claim), the memory system contained:

| File | Purpose | Recoverable from elsewhere? |
|---|---|---|
| `knowledge_base.json` | Per-session timestamp, version, test count, steward+deep verdicts, files w/ issues, security flags | **Partial** — fixed/unfixed surface visible in commits; timestamp-of-detection precision lost |
| `strategic_memory.json` | North star, regulatory urgency, what-works | **High** — encoded in `STATE.md`, `ROADMAP.md`, `READINESS_ASSESSMENT.md` |
| `project_trajectory.json` | Test count timeline 511→2407 | **Full** — reconstructible from `git log --pretty='%h %ad' tests/ \| xargs git show` |
| `security_learnings.json` | HMAC key incident + principle | **Full** — preserved in `WEEKLY_REPORT_20260318.md` patterns |
| `patterns.json` | Active recurring issues w/ `auto_fix` hints | **Partial schema** — 10 patterns w/ fix hints visible in `WEEKLY_REPORT_20260318/19.md`; later evolution lost |
| `resolved_patterns.json` | 15 entries (8 hand-curated + 7 observed) | **None** — the 8 hand-curated entries are the irreplaceable artefact |
| `verification_stats.json` | Performance metrics | **None** unless re-derivable from per-bundle timestamps |
| `client_sessions.json` | Pilot interactions | **Survived** (10 entries, all post-loss) |

### 3.2 Public claims requiring correction

Lines that overstate or mis-time the memory system (file:line — current text — proposed honest replacement):

1. **`README.md:427`** (Built By section)
   ```
   Today: 125 agent sessions. 11 failure patterns learned from the system's own
   mistakes, root-caused, and structurally eliminated. ...
   ```
   **Replace with:**
   ```
   Today: 30 days of structured agent collaboration (2026-03-18 → 2026-04-16),
   137 PRs across 8 release tags. Patterns learned from the system's own mistakes,
   root-caused, and structurally eliminated. Session-level detail rebuilt
   2026-04-28 — see EVOLUTION_LOG.md for the loss event and recovery audit.
   ```

2. **`llms.txt:130`**
   ```
   Agent memory: 125 sessions recorded (2026-03-18 → 2026-04-16), 0 active
   issues, strategic_memory.json synthesized
   ```
   **Replace with:**
   ```
   Agent memory: session-level record rebuilt 2026-04-28 after a working-copy
   data-loss event (full audit: reports/AGENT_LEARN_FULL_AUDIT_2026_04_28.md).
   Decision history of the 30-day pre-loss window preserved in commits, tags,
   weekly reports, and 47 quick-task slugs.
   ```

3. **`docs/EVOLUTIONARY_ARCHITECTURE.md:36`**
   ```
   Over 120 sessions, the knowledge base has accumulated patterns: ...
   This memory is not stored in anyone's head; it is stored in
   .agent_memory/knowledge_base.json, queryable by any agent in any future session.
   ```
   **Replace with:**
   ```
   The knowledge base accumulates per-session patterns: which types of changes
   tend to cause downstream breakage, which documentation files are most
   frequently stale, which test domains are most sensitive to refactoring.
   This memory lives in .agent_memory/knowledge_base.json, queryable by any
   agent in any future session. (Note: a 30-day pre-2026-04-28 window of this
   record was lost in a working-copy cleanup; the decision history is
   preserved in commits + tags + EVOLUTION_LOG.md.)
   ```

4. **`docs/EVOLUTIONARY_ARCHITECTURE.md:76`**
   ```
   The agent does not start from zero. It starts from 120 sessions of
   institutional knowledge.
   ```
   **Replace with:**
   ```
   The agent does not start from zero. It starts from the project's accumulated
   memory — replenished session-by-session and audited end-to-end via commit
   history, release tags, and EVOLUTION_LOG.md.
   ```

5. **`docs/EVOLUTIONARY_ARCHITECTURE.md:92`**
   ```
   The result, after 120 sessions, is a project that knows itself.
   ```
   **Replace with:**
   ```
   The result is a project that knows itself: which files are most fragile,
   which checks are most valuable, which patterns have been resolved, and
   which principles are non-negotiable.
   ```

6. **`docs/EVOLUTIONARY_ARCHITECTURE.md:97`** (footer)
   ```
   *MetaGenesis Core v1.0.0-rc1 | 2407 tests | 20 claims | 22 checks | 120 sessions*
   ```
   **Replace with:**
   ```
   *MetaGenesis Core v1.0.0-rc1 | 2407 tests | 20 claims | 22 checks*
   ```
   (Drop the session count entirely — counters that depend on a non-versioned runtime artefact don't belong in a doc footer.)

7. **`AGENT_TASKS.md:321`** (TASK-028 description)
   ```
   Process all 120 sessions. Resolve 15 ghost patterns.
   ```
   **Replace with:**
   ```
   Process accumulated sessions and resolve ghost patterns into resolved_patterns.json.
   ```
   (TASK-028 is marked DONE 2026-04-12; numerals reference state-at-completion. Could also be left as-is with a footnote — see §5.3.)

**No matches** in `index.html`, `CLAUDE.md`, `paper.md`, or `READINESS_ASSESSMENT.md` for `12X sessions` patterns. Surface area for correction is 4 files / 7 lines.

### 3.3 Public claims that remain valid (do not touch)

Independently verifiable, not affected by the loss:

| Claim | Source of truth | Live value |
|---|---|---|
| 2407 tests passing | pytest | ✓ confirmed |
| 20 active claims | `reports/canonical_state.md`, `steward_audit.py` | ✓ confirmed |
| 5 verification layers | `mg.py verify` | ✓ PASS on demo pack |
| 22 agent checks | `agent_evolution.py` | 21 PASS, 1 pre-existing FAIL |
| 51.2% real ratio | `agent_evolution.py --summary` | ✓ confirmed |
| 86.2% coverage | (per repo state — not re-measured this audit) | not affected |
| 8 innovations | `system_manifest.json` | ✓ confirmed |
| 13 cryptographic deep tests | `deep_verify.py` | ✓ 13/13 PASS |
| Cross-claim chain (MTR-1→DT-FEM-01→DRIFT-01) | `llms.txt:120` | ✓ structural, no KB dependency |
| PPA #63/996,819 | `ppa/CLAIMS_DRAFT.md` (SEALED) | ✓ unaffected |

This is the larger surface area. **The protocol's verifiable claims — the part that sells — are 100% intact.**

### 3.4 Outreach impact

`125 sessions` was cited as a differentiator in:
- `README.md:427` Built By section (most visible — the "AI built the verification protocol for AI" emotional close)
- `llms.txt:130` LLM-context summary
- `docs/EVOLUTIONARY_ARCHITECTURE.md` (cited 4 times as the empirical anchor for the 4-level architecture argument)

Removing the count weakens the **rhetorical** punchline. It does **not** weaken any **technical** claim. The Built By paragraph still works without the number — "30 days of structured agent collaboration, 137 PRs, 8 release tags" is verifiable and arguably more credible (numbers a reviewer can check via `git log` instead of trusting an unverifiable runtime artefact).

**Differentiator replacement:** "transparent operational history" reads stronger than "X sessions" because:
- Sessions are an internal counter; reviewers cannot verify them.
- Commits and tags are public and verifiable.
- Owning a data-loss event publicly *demonstrates* the "proof not trust" principle the protocol sells.

### 3.5 Honest framing options

| Option | Action | Cost | Aligns with values? |
|---|---|---|---|
| **A — Silent reset** | Strip `12X sessions` lines. No event log. | Low | No — "proof not trust" demands visibility of evidence loss as much as evidence presence. |
| **B — Soft reset** | Replace count with "continuous learning since 2026-04-28". No incident disclosure. | Low | Partial — avoids overclaim; obscures the why. Reviewers who saw the previous public state (≥1 person from PR #280 readers) will notice the change. |
| **C — Full transparent registration** | Create `EVOLUTION_LOG.md` (does not currently exist). Append loss event with timestamp + cause + scope + recovery actions. Replace public counts with verifiable language. This audit becomes the receipt. | Medium | **Yes — strongest fit.** The protocol's central claim is "proof not trust"; treating its own incidents the same way is the cleanest possible demonstration. |

**Recommendation: Option C.** Reasoning consolidated in §5.

---

## PHASE 4 — Verification of Surrounding Systems

### 4.1 Test suite

```
2407 passed, 1 skipped in 29.38s
```

Matches expected baseline. **No tests depend on `.agent_memory/` content** (would be a category error if they did — that data is gitignored runtime state, not a fixture).

### 4.2 Verification gates

| Gate | Result | Notes |
|---|---|---|
| `steward_audit.py` | **PASS** | Required files exist, phase registry locked, claim coverage clean |
| `deep_verify.py` | **13/13 PASS** | Cryptographic chain intact |
| `check_stale_docs.py --strict` | **PASS** — 8 CURRENT, 0 STALE | *Caveat: this check does NOT validate session counts; the stale "120/125 sessions" lines are invisible to it* |
| `agent_evolution.py --summary` | **21/22 PASS** | One FAIL: `semantic_audit` |

**`semantic_audit` FAIL detail:**
```
D: Demo Scenarios x Regulatory
  01_ai_benchmark: FAIL (run=True, verify=False)
  02_pharma:       FAIL (run=True, verify=False)
  03_finance:      FAIL (run=True, verify=False)
  04_digital_twin: FAIL (run=True, verify=False)
  1/6 CHECKS FAIL
```

This is **pre-existing and unrelated to the data loss**. Four client demos run but produce verify=False — a separate workstream. The recommended-fix string `agent_evolution.py` prints ("Update CLAUDE.md...") is a generic hardcoded suggestion and not the actual root cause.

### 4.3 Cryptographic chain

```
$ python scripts/mg.py verify --pack demos/open_data_demo_01/pack/
PASS
```

5-layer verification (integrity + semantic + step chain + bundle signing + temporal commitment) passes on the canonical demo pack. Bundle integrity is the central protocol claim and is **completely unaffected** by the data loss. (Note: `mg.py verify` requires a pack directory, not a `.zip`; the bundles in `proof_library/bundles/` need extraction first, which is not a regression — same constraint pre-loss.)

### 4.4 Code references to lost data

**`knowledge_base` / `resolved_patterns`** — 6 files reference these names:
- `scripts/agent_learn.py` — **creates** them at runtime via `observe()`. No hard dependency; will recreate empty on first run.
- `tests/scripts/test_agent_learn_observe.py`, `test_agent_learn_commands.py` — use `tmp_path` fixtures; do not depend on real `.agent_memory/` content.
- `docs/EVOLUTIONARY_ARCHITECTURE.md` — narrative reference only (already in §3.2 doc-correction list).
- `reports/RECURSION_ANALYSIS.md` — narrative reference (frozen in time; OK to leave).
- `AGENT_TASKS.md:321` — narrative reference (already in §3.2).

**`agent_memory`** — 19 files reference the directory name:
- 7 scripts (`agent_signals`, `agent_research`, `agent_learn`, `agent_pattern_promoter`, `agent_evolve_self`, `agent_client`, etc.) — all use `MEMORY_DIR = REPO_ROOT / ".agent_memory"`; create files lazily.
- 7 test files — use `tmp_path` fixtures.
- `.gitignore:97` — entry that excludes the directory (correct as-is).
- `.github/workflows/weekly_agent_health.yml:79` — `git add reports/ .agent_memory/ || true` — non-fatal; `.agent_memory/` is gitignored so this `git add` is a no-op anyway.
- `reports/RECURSION_ANALYSIS.md`, `reports/AUDIT_TRUTH_20260402.md`, `docs/EVOLUTIONARY_ARCHITECTURE.md`, `AGENT_TASKS.md` — narrative.

**Risk level: LOW.** All code paths handle missing files (the standard pattern is `if KB_FILE.exists(): ... else: return {}`). No code change required for the loss; only narrative docs need updating.

### 4.5 GSD planning state

- `STATE.md` milestone: v3.1.0 in progress, Phase 28 ready to plan.
- `STATE.md:111` references the lost diagnostic quick-task with `_pending_` commit hash. **This row should be edited or annotated to acknowledge the loss** as part of the WS-A.0 successor commit.
- `CLAUDE.md` has zero `125-session` / `120-session` / `knowledge_base` / `agent_memory` references — clean. No GSD context update needed.
- No `.planning/CURRENT_PHASE.md` file — milestone tracking is via `STATE.md`.

---

## PHASE 5 — Verdict + Recommendations

### 5.1 Quantified impact

- **Sessions reconstructible from commits + tags + slugs + weekly reports:** ~100 of 125 (80 %).
- **Sessions truly unrecoverable:** ~25 of 125 (20 %) — these are the "quiet days" with observe-only runs that produced no commits/PRs/tags.
- **Hand-curated `auto_fix_hint` entries lost:** 8 of 8 (100 %) — irreplaceable, but the schema is preserved in `WEEKLY_REPORT_20260318/19.md` and a new set can be re-curated from observed patterns going forward.
- **Public-doc lines requiring correction:** **7 lines across 4 files.**
- **Code references requiring change:** **0 files** (all references are narrative or auto-creating).
- **Tests requiring change:** **0 files** (all use fixtures).
- **Effective information loss vs verifiable-claim surface:** **~5 %** (the sellable surface — cryptography, claims, tests, ratio, coverage — is 100 % intact).

### 5.2 Recommendation: Option C

**Why C beats A and B:**

1. **Protocol values demand it.** "Proof not trust" applied inward (per `EVOLUTIONARY_ARCHITECTURE.md` §1, §4 levels) requires that loss events of internal artefacts be auditable, not papered over. Option A directly contradicts this.

2. **Prior public state is searchable.** PR #280 ("122 → 125 sessions") and the README diff are in the public git history. A reviewer who pulled the README between 2026-04-16 and the proposed reset will notice the count vanishing. Option B leaves them with no explanation; Option C provides a verifiable one.

3. **Outreach value flips a liability into an asset.** First-paying-client risk: a reviewer asks "what happens when YOUR system loses data?" Option A/B → handwave. Option C → "open `EVOLUTION_LOG.md`, see the receipt; here is the audit; here are the gates that still pass." The protocol's central thesis is *demonstrated* live.

4. **Recovery feasibility is high.** The audit (this file) and an `EVOLUTION_LOG.md` entry are ~30 minutes of additional writing. Substrate cost is ~0.

5. **No SEALED files in scope.** No risk of breaking governance by writing the new files.

### 5.3 WS-A.0 successor scope (proposed — for the *next* `/gsd-quick`)

**Files to create:**
- `EVOLUTION_LOG.md` (new, repo root) — first entry: 2026-04-28 data-loss event with timestamp, cause, scope, recovery actions, link to this audit.

**Files to edit (7 lines, 4 files):**
- `README.md:427` — replacement text per §3.2.1
- `llms.txt:130` — replacement text per §3.2.2
- `docs/EVOLUTIONARY_ARCHITECTURE.md:36, :76, :92, :97` — replacement texts per §3.2.3-6
- `AGENT_TASKS.md:321` — TASK-028 description per §3.2.7 (or footnote-only — user choice)

**Files to potentially edit (advisory):**
- `.planning/STATE.md:111` — annotate the `_pending_` commit row for `260421-s3f-agent-learn-diagnostic` to acknowledge directory was lost in 2026-04-25 cleanup. (Or leave; the loss is now logged in EVOLUTION_LOG.)

**Files NOT to touch (SEALED or out of scope):**
- `scripts/steward_audit.py`, `scripts/mg.py`, `scripts/mg_policy_gate_policy.json` (SEALED)
- `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` (SEALED)
- `ppa/CLAIMS_DRAFT.md` (SEALED)
- `.github/workflows/*` (modify-only, per project rules)
- All `.agent_memory/*` files (preserve current state until observer is restarted by a deliberate, scoped task)
- All test files

**Acceptance gates for WS-A.0 successor (in this order):**
1. `python -m pytest tests/ -q` → 2407 passed / 1 skipped (must not regress)
2. `python scripts/steward_audit.py` → PASS
3. `python scripts/check_stale_docs.py --strict` → 0 STALE
4. `python scripts/deep_verify.py` → 13/13 PASS
5. New file `EVOLUTION_LOG.md` exists and is git-tracked
6. All 7 doc-correction lines applied verbatim from §3.2 (or with user-approved deviations)
7. `python scripts/agent_evolution.py --summary` → still 21/22 (no new FAIL; the pre-existing semantic_audit FAIL is acknowledged out-of-scope)

**Banned-term watch:** the project denylist includes the standard overclaim phrases ("tamper-" + "proof", "un" + "forgeable", "impossible to" + " forge"), the chain-of-blocks marketing word, the inflated AI-model-version names, the inflated comparative ratios ("19" + "x"), the perfection-success claim ("100%" + " test success"), the inflated module counts, and the legacy-engine names — plus any test count below 2407. Proposed replacement texts in §3.2 contain none of these.

**PR style:** Single PR, draft → ready when user approves; squash-merge on accept.

### 5.4 Risks remaining after WS-A.0 merge

| Risk | Likelihood | Mitigation |
|---|---|---|
| First paying client asks "what happened to the 125 sessions claim?" | Medium | This audit + `EVOLUTION_LOG.md` answer it directly — and turn it into a credibility asset. |
| Internet-archive / Wayback Machine snapshot of old README quoted in adversarial context | Low | Same — point to `EVOLUTION_LOG.md`. The git history is itself the receipt. |
| Daily auto-observe in `weekly_agent_health.yml` recreates `.agent_memory/` files with empty content, replacing recovery option if shadow-of-shadow ever surfaces | Medium | **Pause the workflow** or add a guard `if [ ! -f .agent_memory/knowledge_base.json.RECOVERED ]` before running `agent_learn observe` — this is a hardening item for AGENT-LEARNING-01 (planned 21st claim, v3.2.0). For v3.1.0 WS-A.0 it is acceptable to re-run `observe` because no pending recovery option remains. |
| `semantic_audit` FAIL becomes confused with the data-loss event in reviewer's head | Low | Audit explicitly separates them (§4.2). The successor PR can add a short note to its description disambiguating. |
| Proposed replacement texts contain banned terms or stale counters | Low | §3.2 texts have been reviewed; none present. WS-A.0 acceptance gate #3 (`check_stale_docs --strict`) will catch any introduced staleness. |

### 5.5 Future-proofing recommendations

1. **Should `.agent_memory/` become git-tracked?** *No, but with caveats.*
   - Tracking `.agent_memory/knowledge_base.json` would solve the loss problem but introduces churn (every observe run = 1 dirty file in working tree) and bloats the repo over time (~125 entries × N years).
   - Better: keep `.agent_memory/` gitignored, but add a **periodic snapshot** mechanism (`agent_learn.py snapshot --to docs/memory_snapshots/YYYY-MM-DD.json.zst`) that commits compressed, immutable, append-only snapshots monthly or per release tag.
   - Acceptance: any reviewer can `git log docs/memory_snapshots/` and see the longitudinal record exists, without per-PR working-tree churn.

2. **Should there be a backup/sync workflow for `.agent_memory/`?**
   - **Yes — minimal.** A daily `tar czf` to a separate directory outside the working copy (e.g. `~/.metagenesis-backups/`) with 14-day rotation. Five lines of shell. Costs nothing. Would have prevented this incident.
   - Or: configure OneDrive Personal Vault for the `.agent_memory/` directory specifically. Out-of-band of the working copy; survives `Downloads/` cleanups.

3. **Should observer write a redundant copy to `vault_ready/`?**
   - Marginal. Same root cause (working-copy cleanup) — both would be lost. Belt-and-suspenders only if the secondary location is **outside** the working copy.

4. **Should AGENT-LEARNING-01 (v3.2.0, 21st claim) include backup integrity?**
   - **Strongly yes.** Frame as: "A self-verifying protocol cannot lose its own learning record without detection." The new claim should:
     - Verify `knowledge_base.json` integrity via Ed25519 signature + hash chain (each session entry signs the previous hash).
     - Detect catastrophic gaps (session N-1 followed by session N+5, no entries between).
     - Surface the gap as a `agent_evolution.py` check failure that requires explicit acknowledgement (e.g. an `EVOLUTION_LOG.md` entry referencing the gap).
   - This audit becomes the **first datum** that motivates AGENT-LEARNING-01. Strong narrative coupling.

---

## Appendices

### A.1 Lost-files manifest (final inventory)

```
.agent_memory/
  knowledge_base.json        ─ ~125 sessions, 2026-03-18 → 2026-04-16
  resolved_patterns.json     ─ 15 entries (8 hand-curated + 7 observed)
  strategic_memory.json      ─ synthesized 2026-04-12
  project_trajectory.json    ─ test-count timeline 511 → 2407
  security_learnings.json    ─ HMAC incident + derived principles
  verification_stats.json    ─ performance metrics
  lessons.md                 ─ human-readable log (referenced in agent_learn.py docstring)

.planning/quick/
  260407-rrr-redesign-metagenesis-core-dev
  260411-991-boost-coverage-83.4-to-90
  260411-9ue-coverage-boost-phase-2
  260411-aif-fix-3-ordering-dependent-test-failures
  260411-aju-sync-test-count-2132-to-2358
  260411-ifo-readme-additions-80-year-gap-talk-to-protocol-q-and-a
  260412-p78-deep-audit-fix-skipped-tests-sync-2405-to-2407
  260416-i4y-fix-test-6-forbidden-terms-split-literal
  260421-s3f-agent-learn-diagnostic        ← verdict-B source

reports/
  AGENT_LEARN_DIAGNOSTIC.md  ─ never created (was a quick-task, not a report)
```

### A.2 Preserved-memory locations (final inventory)

```
Tags + commits:                           git -C <repo> log --since=2026-03-18 --until=2026-04-17
Quick-task slugs (47 dirs):               .planning/quick/260317* .. 260403*
Weekly health reports:                    reports/WEEKLY_REPORT_20260318.md, _20260319.md
Agent reports:                            reports/AGENT_REPORT_20260318.md, _19, _29, _20260402b
Audit truths:                             reports/AUDIT_TRUTH_20260401.md, _02; EXPANDED_AUDIT_20260401.md
Recursion analysis:                       reports/RECURSION_ANALYSIS.md (15 patterns at v1.0.0-rc1)
Steward report:                           reports/STEWARD_REPORT_20260411.md
Self-improvement:                         reports/SELF_IMPROVEMENT_20260319.md
Outreach drafts:                          reports/WAVE2_OUTREACH_DRAFTS.md
Readiness assessment:                     reports/READINESS_ASSESSMENT.md
Milestone summaries:                      session_log.jsonl (3 entries)
GSD state:                                .planning/STATE.md, .planning/ROADMAP.md, .planning/PROJECT.md
Pilot/client log:                         .agent_memory/client_sessions.json (10 fresh post-loss entries)
Pattern schema with auto_fix hints:       reports/WEEKLY_REPORT_20260318/19.md (10 patterns visible)
Evolution proposals:                      .planning/EVOLUTION_PROPOSALS.md (current generation)
```

### A.3 Halt condition met

This audit is read-only. The only files modified are:
- `reports/AGENT_LEARN_FULL_AUDIT_2026_04_28.md` (this file — created)
- `.planning/quick/20260428-audit-data-loss-pre-recovery/PLAN.md` (created, scoped)

After PR opens (draft, not merged), execution **halts** per task brief acceptance gates. User reviews verdict, decides on Option A/B/C, and issues a separate `/gsd-quick` for implementation.

— end of audit —
