---
phase: quick
plan: 260319-sfq
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/check_stale_docs.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "agent_signals.py is tracked in CONTENT_CHECKS with required strings GitHub API and SIGNALS_"
    - "agent_chronicle.py is tracked in CONTENT_CHECKS with required strings CHRONICLE_ and system_manifest"
    - "auto_watchlist_scan.py reports 0 unwatched files"
    - "check_stale_docs.py --strict exits 0"
  artifacts:
    - path: "scripts/check_stale_docs.py"
      provides: "CONTENT_CHECKS entries for agent_signals.py and agent_chronicle.py"
      contains: "agent_signals.py"
  key_links: []
---

<objective>
Add 2 missing files to CONTENT_CHECKS in scripts/check_stale_docs.py so that the stale docs checker validates their content. Then verify both the watchlist scanner and stale docs checker pass clean.

Purpose: Close watchlist coverage gap for two new agent scripts.
Output: Updated check_stale_docs.py with 2 new CONTENT_CHECKS entries.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/check_stale_docs.py
@scripts/agent_signals.py
@scripts/agent_chronicle.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add agent_signals.py and agent_chronicle.py to CONTENT_CHECKS</name>
  <files>scripts/check_stale_docs.py</files>
  <action>
In scripts/check_stale_docs.py, add two new entries to the CONTENT_CHECKS dict (insert after the existing last entry, before the closing brace):

```python
    "scripts/agent_signals.py": {
        "banned": [],
        "required": ["GitHub API", "SIGNALS_"],
    },
    "scripts/agent_chronicle.py": {
        "banned": [],
        "required": ["CHRONICLE_", "system_manifest"],
    },
```

These required strings match actual content in the files:
- agent_signals.py contains "GitHub API" (line 33 comment in fetch_github_stats docstring) and "SIGNALS_" (line 157 in report filename)
- agent_chronicle.py contains "CHRONICLE_" (line 204 in report filename) and "system_manifest" (line 34 in manifest path)
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python scripts/auto_watchlist_scan.py --strict && python scripts/check_stale_docs.py --strict</automated>
  </verify>
  <done>Both scripts appear in CONTENT_CHECKS. auto_watchlist_scan.py reports 0 unwatched files. check_stale_docs.py --strict exits 0.</done>
</task>

<task type="auto">
  <name>Task 2: Commit and push to feat/agent-divine-v2</name>
  <files></files>
  <action>
Stage scripts/check_stale_docs.py and commit with message:
"fix: add agent_signals.py + agent_chronicle.py to CONTENT_CHECKS watchlist"

Then push to origin feat/agent-divine-v2.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && git log -1 --oneline</automated>
  </verify>
  <done>Commit exists on feat/agent-divine-v2 and is pushed to origin.</done>
</task>

</tasks>

<verification>
- python scripts/auto_watchlist_scan.py --strict exits 0 (0 unwatched)
- python scripts/check_stale_docs.py --strict exits 0 (no content failures)
- git log shows commit on feat/agent-divine-v2
</verification>

<success_criteria>
- CONTENT_CHECKS contains entries for scripts/agent_signals.py and scripts/agent_chronicle.py
- auto_watchlist_scan.py confirms 0 unwatched files
- check_stale_docs.py --strict confirms exit 0
- Changes committed and pushed to feat/agent-divine-v2
</success_criteria>

<output>
After completion, create `.planning/quick/260319-sfq-add-2-missing-files-to-content-checks-in/260319-sfq-SUMMARY.md`
</output>
