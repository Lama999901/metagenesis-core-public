---
phase: quick
plan: 260319-ult
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/check_stale_docs.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "scripts/agent_evolution.py appears in CONTENT_CHECKS dict in check_stale_docs.py"
    - "auto_watchlist_scan.py reports 0 unwatched files"
  artifacts:
    - path: "scripts/check_stale_docs.py"
      provides: "CONTENT_CHECKS entry for agent_evolution.py"
      contains: "scripts/agent_evolution.py"
  key_links: []
---

<objective>
Add scripts/agent_evolution.py to the CONTENT_CHECKS dictionary in scripts/check_stale_docs.py so the stale docs checker validates its content. Then confirm the auto_watchlist_scan reports 0 unwatched files. Commit on fix/watchlist-evolution branch and push.

Purpose: Close the watchlist gap where agent_evolution.py is not tracked by the content checker.
Output: Updated check_stale_docs.py with new CONTENT_CHECKS entry, pushed to fix/watchlist-evolution.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/check_stale_docs.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add agent_evolution.py to CONTENT_CHECKS and verify watchlist</name>
  <files>scripts/check_stale_docs.py</files>
  <action>
In scripts/check_stale_docs.py, add a new entry to the CONTENT_CHECKS dict (after the existing entries, before the closing brace on line 242). The entry should be:

```python
    "scripts/agent_evolution.py": {
        "banned": [],
        "required": ["check_signals", "check_chronicle", "v0.6.0"],
    },
```

This follows the exact same pattern as other script entries like "scripts/agent_signals.py" (line 226) and "scripts/agent_chronicle.py" (line 230).

Then:
1. Run `python scripts/check_stale_docs.py` to confirm the new entry passes (agent_evolution.py contains all three required strings).
2. Run `python scripts/auto_watchlist_scan.py` to confirm 0 unwatched files.
3. Create branch fix/watchlist-evolution: `git checkout -b fix/watchlist-evolution`
4. Stage and commit: `git add scripts/check_stale_docs.py && git commit -m "fix: add agent_evolution.py to CONTENT_CHECKS watchlist"`
5. Push: `git push origin fix/watchlist-evolution`
  </action>
  <verify>
    <automated>python scripts/auto_watchlist_scan.py 2>&1 | grep "unwatched" && python scripts/check_stale_docs.py 2>&1 | grep "agent_evolution"</automated>
  </verify>
  <done>scripts/agent_evolution.py is in CONTENT_CHECKS with required=["check_signals", "check_chronicle", "v0.6.0"] and banned=[], auto_watchlist_scan reports 0 unwatched, changes committed and pushed to fix/watchlist-evolution</done>
</task>

</tasks>

<verification>
- `python scripts/check_stale_docs.py` shows OK for scripts/agent_evolution.py
- `python scripts/auto_watchlist_scan.py` shows 0 unwatched
- `git log -1 --oneline` shows the commit on fix/watchlist-evolution
</verification>

<success_criteria>
- CONTENT_CHECKS contains "scripts/agent_evolution.py" with correct required and banned lists
- auto_watchlist_scan.py reports 0 unwatched files
- Changes pushed to fix/watchlist-evolution branch
</success_criteria>

<output>
After completion, create `.planning/quick/260319-ult-add-agent-evolution-py-to-content-checks/260319-ult-SUMMARY.md`
</output>
