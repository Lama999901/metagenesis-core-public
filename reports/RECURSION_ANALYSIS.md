# Recursion Analysis -- MetaGenesis Core Agent Evolution

## Current Recursion Depth

- **Level 1: OBSERVE** -- `agent_evolution.py` runs 22 check_ functions, `agent_learn.py observe` records findings to `.agent_memory/`
- **Level 2: PATTERN** -- `agent_learn.py` tracks recurring issues in `patterns.json` (15 patterns, 15 with fix hints)
- **Level 3: PROPOSE** -- `agent_evolution_council.py` reads 7 sources (including patterns.json via agent_learn recall) and writes ranked proposals to `.planning/EVOLUTION_PROPOSALS.md`
- **Level 4: GOVERN** -- Proposals sit in EVOLUTION_PROPOSALS.md. Nothing reads them back into agent_evolution.py. The loop is open.

Note: `agent_pattern_promoter.py` does not exist. There is no script that promotes high-frequency patterns to governance changes.

## What Is Truly Recursive (Evidence from Code)

**observe -> record:** `agent_learn.py:140-229` -- `observe()` runs steward audit, deep verify, manifest check, scans critical files, then writes results to `knowledge_base.json` (line 229) and `patterns.json` (line 230).

**record -> recall:** `agent_learn.py:283-321` -- `recall()` reads `KB_FILE` (line 290) and `PATTERNS_FILE` (line 287), displays sessions, auto-fix hints, and most common issues. This is consumed by humans and by the council.

**recall -> propose:** `agent_evolution_council.py:65-79` -- `read_agent_learn()` shells out to `python scripts/agent_learn.py recall`, parses `[Nx]` patterns with count >= 3, feeds them into proposal generation.

**propose -> rank:** `agent_evolution_council.py:473-518` -- `generate_proposals()` scores all items by impact/effort ratio, sorts, writes top 10 to `EVOLUTION_PROPOSALS.md`.

**CI automation:** `.github/workflows/weekly_agent_health.yml:43-68` -- runs agent_evolution, agent_learn observe, and auto-commits results to `.agent_memory/` daily at 09:00 UTC. This means Levels 1-2 run automatically without human intervention.

## What Is Recorded But Not Looped Back

**The chain breaks at Level 3 -> Level 4.** Specifically:

1. `agent_evolution_council.py` writes `EVOLUTION_PROPOSALS.md` (line 600) but nothing reads it.
2. No script modifies `agent_evolution.py` based on proposals. The 22 checks are static -- hand-edited by a human.
3. `patterns.json` contains `auto_fix` and `prevention` fields (e.g., line 8-9 of patterns.json), but no script executes those commands automatically. They are hints for human copy-paste.
4. The CI workflow does not run `agent_evolution_council.py`. Proposals are only generated on manual invocation.
5. `EVOLUTION_PROPOSALS.md` is overwritten on each council run -- there is no history of which proposals were accepted or rejected.

**Summary:** The system observes, records, and proposes. It does not act on its own proposals.

## What One Change Would Make Recursion Complete

Add a function `apply_approved_proposals()` to `agent_evolution_council.py` that:

1. Reads `EVOLUTION_PROPOSALS.md` for proposals marked `STATUS: APPROVED` (requires adding a status field)
2. For proposals sourced from `agent_learn` patterns with `auto_fix` hints in `patterns.json`, executes the fix command
3. For proposals sourced from `coverage` or `agent_evolution`, generates a new check_ function stub in `agent_evolution.py`
4. Logs what was applied to `.agent_memory/applied_proposals.json`
5. Runs `agent_evolution.py` to verify nothing broke

This would close the loop: observe -> pattern -> propose -> apply -> observe.

But this is intentionally not built. See below.

## Honest Limitations

1. **Self-modifying code is dangerous.** Auto-editing `agent_evolution.py` means a bad pattern could disable its own detection. The system would need a rollback mechanism and a "constitution" of checks that cannot be removed.

2. **The human governance gate is a feature, not a bug.** EVOLUTION_PROPOSALS.md is a decision document for humans. The value is in surfacing problems with evidence and ranked priority, not in auto-fixing them. Most proposals (PROP-003 through PROP-010 in the current file) are "reduce file churn" -- not actionable by code.

3. **The auto_fix hints in patterns.json are shell commands, not verified code.** Executing them blindly risks data loss (e.g., `git filter-repo` in the signing key pattern).

4. **The council's 7 data sources are read-only.** It queries but never mutates. This is correct -- separating observation from action prevents feedback loops where a fix creates a new problem that triggers another fix.

5. **Current proposals are low-signal.** The 10 proposals in EVOLUTION_PROPOSALS.md are dominated by "file changed N times" git churn noise. The council's scoring heuristics (`_classify_impact`, `_classify_effort`) are hardcoded, not learned. The recursion would need better signal-to-noise before auto-application would be useful.

6. **Real recursion depth is 2, not 4.** Levels 1-2 (observe + pattern) run automatically in CI. Level 3 (propose) requires manual invocation. Level 4 (govern/apply) does not exist in code.
