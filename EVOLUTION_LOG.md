# Evolution Log

> **Purpose.** A public, append-only record of significant operational events in the MetaGenesis Core protocol's own history — losses, recoveries, architectural pivots, and governance decisions that change how the protocol verifies itself.
>
> **Convention.** Each entry has: a date header, a short title, an event description, the action taken, and cross-references to PRs, commits, and audit artefacts. Entries are append-only; corrections are added as new dated entries, not edits to old ones. The protocol applies its "proof, not trust" principle to itself — including to its own incidents.
>
> **Scope.** This log records *operational and architectural* events. Routine commits, PR merges, and ordinary feature work are tracked in git history and `.planning/STATE.md`. EVOLUTION_LOG entries are reserved for events that change the protocol's posture toward its own integrity.

---

## 2026-04-28 — Agent Memory Data Loss Event

### Event

Between approximately 2026-04-22 and 2026-04-25 08:32 -0800, a routine cleanup of `C:\Users\999ye\Downloads\metagenesis-core-public\` deleted the working copy of the `.agent_memory/` directory along with several uncommitted artefacts. The protocol's per-session learning record (`.agent_memory/knowledge_base.json`, ~125 entries spanning 2026-03-18 → 2026-04-16) and its derived synthesis outputs (`resolved_patterns.json`, `strategic_memory.json`, `project_trajectory.json`, `security_learnings.json`, `verification_stats.json`) are unrecoverable from any local source. Nine quick-task directories from 2026-04-07 → 2026-04-21 — listed in `.planning/STATE.md` as `_pending_` for commit but never reaching git — are also lost. Among those is `260421-s3f-agent-learn-diagnostic`, the verdict-B diagnostic directory whose findings motivated the audit chain that produced this entry.

The cleanup was operator-driven, not a protocol failure. The reason it became significant: the protocol's own learning record was outside the protocol's verification scope. `.agent_memory/` is gitignored (`.gitignore:97`, "Claude Project Knowledge — internal — not for public repo"). It had no cryptographic protection, no signed-chain integrity, no append-only enforcement, no out-of-band backup. Loss was therefore silent — detectable only by absence, not by tamper-evidence on the data itself.

Recovery investigation across three independent paths exhausted the recovery surface:
- **Git history** — file family was always gitignored; never tracked. Zero blob in any commit, on any branch, in any reflog, in `git fsck --full --unreachable --dangling --lost-found`.
- **VSS shadow copy** — only one snapshot existed (`HarddiskVolumeShadowCopy2`, 2026-04-27), post-deletion. Mounted via `mklink /D C:\shadow_2026_04_27 \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy2\`; contents matched current disk state (no recovery surface).
- **OneDrive / File History** — neither enabled for this directory. No external backup existed.

A second-layer triangulation across an additional eight paths (Windows File History, deeper reflog dive, full fsck, VS Code workspace cache, Windows Search index, Recycle Bin metadata, Claude tooling caches, the nine specific lost-slug names) confirmed the same: zero bytes recoverable.

### Effective impact

The data lost is the *narrative* of the protocol's evolution over a 30-day window — timestamps of detection, severity assessments, eight hand-curated `auto_fix_hint` entries, the aggregate clean-ratio time series, and the verdict-B diagnostic content. The data preserved is the *substance* of that evolution — 137 PRs, 8 release tags (v0.5.0 through v3.0.0 / v1.0.0-rc1), 47 surviving quick-task slugs from 2026-03-17 → 2026-04-03, and 27 weekly and ad-hoc reports including `WEEKLY_REPORT_20260318.md` and `WEEKLY_REPORT_20260319.md` which preserve early-period pattern schema with `auto_fix` hints.

The protocol's verifiable claims — cryptography, claim count (20), test count (2407), real-ratio (51.2%), coverage, the 5-layer verification chain, the cross-claim chain, all four PPA-filed innovations and four post-filing innovations — are 100% intact. None of them depended on `.agent_memory/` content.

Effective information loss against the verifiable-claim surface: ~5%. Effective loss against the narrative-history surface: ~20%.

### Why this entry exists

A verification protocol whose central claim is "proof, not trust" cannot quietly absorb the loss of its own learning record. The "proof" applies recursively: if the protocol's verification gates do not protect the protocol's own operational data, then the protocol verifies its inputs but not itself.

The 2026-04-28 event is the empirical realisation of that structural gap. Treating it as embarrassing and hiding it would contradict the protocol's stated values. Registering it transparently — with the audit trail, the recovery investigation outcomes, and the architectural response — converts a liability into evidence that the protocol's self-application of its own principles works as advertised: the gap was detected, audited end-to-end, and the architectural fix was specified.

### Three-tier framing

This entry is the first of three connected layers:

1. **WS-A.0 (this PR)** — register the loss, correct affected public docs, cement architectural design for the structural fix.
2. **v3.2.0 — AGENT-LEARNING-01** — implement the structural fix. Apply the protocol's 5-layer verification recursively to the protocol's own learning record. After implementation, a future loss of this kind would be detectable, the integrity would be cryptographically attested, and the rebuild would have a verifiable baseline. See `docs/INNOVATION_09_SELF_VERIFYING_LEARNING.md`.
3. **Future recursive AI evolution layer** — use the verified learning substrate as the integrity foundation for higher-autonomy operations. Without that substrate, recursive self-improvement has no audit trail and "proof, not trust" cannot scale beyond the current Level-3 governance ceiling.

This entry becomes the motivating case study for including AGENT-LEARNING-01 in the non-provisional patent filing (deadline 2027-03-05). A real incident demonstrating the structural gap is more credible motivation than hypothetical reasoning.

### Action taken (in this PR)

- **Created** this `EVOLUTION_LOG.md` (the file did not previously exist; it was once briefly tracked in 2026-03-18 era and removed per `WEEKLY_REPORT_20260318.md:35` "PRIVATE FILE IN REPO" pattern; this re-introduction reverses that decision under a different convention — a public operational log, not a private notebook).
- **Corrected** 9 lines across 5 files where stale "120 / 122 / 125 sessions" claims overstated the current session-tracking state.
- **Cemented** architectural design intent for Innovation 9 (`docs/INNOVATION_09_SELF_VERIFYING_LEARNING.md`) and Innovation 10 (`docs/INNOVATION_10_FEDERATED_REGISTRY.md`) — patent priority via git timestamp before non-provisional filing.
- **Updated** README.md and `llms.txt` to reflect the honest "10 innovations: 4 filed in PPA + 4 post-filing implemented + 2 planned" framing.

### Cross-references

- **PR #283** — `chore/audit-data-loss-pre-recovery`, commit `ec72d0b`. Layer-1 breadth-first audit. Verdict: Option C (full transparent registration). Report: `reports/AGENT_LEARN_FULL_AUDIT_2026_04_28.md`.
- **PR #284** — `chore/audit-data-loss-deeper-validation`, commit `70954f0`. Layer-2 triangulation. Confirmed Option C with one numeric revision (doc-correction surface 7 lines / 4 files → 9 lines / 5 files). Reports: `reports/AGENT_LEARN_DEEPER_VALIDATION_2026_04_28.md`, `reports/EVOLUTION_PROPOSALS_v3_2.md`.
- **This PR** — `feat/ws-a0-data-loss-registration-plus-innovations`. Implements Option C and adds patent-priority cementation for Innovations 9 and 10.

### Out of scope (post-merge follow-ups)

- PROP-006 — minimal external backup workflow (next `/gsd-quick`).
- PROP-010 — fix the pre-existing `semantic_audit` 1/22 FAIL (4 client-scenario demos `verify=False`).
- Implementation of Innovation 9 in code (v3.2.0 — PROP-001 / 003 / 004 first).
- Innovation 10 reference implementation (v4.0.0).
- Patent attorney engagement (Q3 2026 per `AGENT_TASKS.md` TASK-036).

---

*— end of 2026-04-28 entry —*
