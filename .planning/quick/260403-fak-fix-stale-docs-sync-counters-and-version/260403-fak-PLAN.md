---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - docs/AGENT_SYSTEM.md
  - paper.md
  - llms.txt
  - CONTEXT_SNAPSHOT.md
  - reports/known_faults.yaml
autonomous: true
requirements: [STALE-DOCS]

must_haves:
  truths:
    - "All doc files reference test count 1634"
    - "All doc files reference v0.9.0"
    - "All doc files reference 8 innovations"
    - "All doc files reference 20 claims"
    - "check_stale_docs.py reports ALL CURRENT"
    - "agent_learn.py stale patterns are verified as resolved"
  artifacts:
    - path: "docs/AGENT_SYSTEM.md"
      provides: "Footer version updated to v0.9.0"
      contains: "v0.9.0"
  key_links:
    - from: "system_manifest.json"
      to: "all doc files"
      via: "counter values match"
      pattern: "1634.*test|v0\\.9\\.0|20 claims|8 innovation"
---

<objective>
Verify and fix stale counters/versions across paper.md, llms.txt, CONTEXT_SNAPSHOT.md, known_faults.yaml, and related docs.

Purpose: Ensure all documentation reflects current etalon values from system_manifest.json (v0.9.0, 1634 tests, 20 claims, 8 innovations, 5 layers, 19 checks).
Output: All docs synced; check_stale_docs.py passes; any genuinely stale values fixed.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@system_manifest.json
@scripts/check_stale_docs.py
@CLAUDE.md (etalon values and UPDATE_PROTOCOL v1.1 rule)

Etalon values (from system_manifest.json / CLAUDE.md):
- Version: v0.9.0
- Tests: 1634
- Claims: 20
- Innovations: 8
- Layers: 5
- Checks: 19
- Domains: 8
</context>

<tasks>

<task type="auto">
  <name>Task 1: Comprehensive stale value scan and fix</name>
  <files>docs/AGENT_SYSTEM.md, paper.md, llms.txt, CONTEXT_SNAPSHOT.md, reports/known_faults.yaml</files>
  <action>
IMPORTANT DISCOVERY: Pre-planning analysis found that paper.md, llms.txt, CONTEXT_SNAPSHOT.md, and known_faults.yaml are ALREADY CURRENT (confirmed by check_stale_docs.py). The agent_learn.py recall shows HISTORICAL stale patterns from past sessions, not current issues. These were fixed in prior quick tasks (260318-jpb, 260330-jy1, 260330-vbc, 260331-ov3).

One genuinely stale value was found:
- docs/AGENT_SYSTEM.md line 93: footer says "v0.8.0", should be "v0.9.0"

Steps:
1. Run `python scripts/check_stale_docs.py` to confirm baseline status.
2. Run a comprehensive Python scan across ALL documentation files (not just the 4 targets) checking for:
   - Test counts other than 1634 (excluding "13 tests" which is deep_verify)
   - Version strings older than v0.9.0 (v0.1 through v0.8)
   - Innovation counts other than 8
   - Claim counts other than 20
   - Layer counts other than 5
   Exclude: .claude/ directory, worktrees, demos/, reports/WEEKLY_REPORT_*, AGENTS.md banned-terms section (which lists old values as "do not use" rules), ppa/README_PPA.md (historical data).
3. Fix docs/AGENT_SYSTEM.md line 93: change "v0.8.0" to "v0.9.0" in the footer.
4. Fix any other stale values found in step 2.
5. If any values were changed in check_stale_docs.py-monitored files, verify check_stale_docs.py required strings still match (UPDATE_PROTOCOL v1.1 rule).
6. Re-run `python scripts/check_stale_docs.py` to confirm ALL CURRENT.
7. Run `python -m pytest tests/ -q --tb=no` to confirm no regressions.
  </action>
  <verify>
    <automated>python scripts/check_stale_docs.py && python -m pytest tests/ -q --tb=no -x</automated>
  </verify>
  <done>
- check_stale_docs.py reports "All critical documentation is current"
- No file in the repo (outside worktrees/demos/ppa) contains stale version/counter values
- docs/AGENT_SYSTEM.md footer reads v0.9.0
- All tests pass
  </done>
</task>

</tasks>

<verification>
python scripts/check_stale_docs.py  # -> All critical documentation is current
python scripts/steward_audit.py     # -> STEWARD AUDIT: PASS
python -m pytest tests/ -q --tb=no  # -> 1634 passed
</verification>

<success_criteria>
- check_stale_docs.py: ALL CURRENT
- steward_audit.py: PASS
- All tests pass (1634+)
- No documentation file contains stale version/counter values relative to system_manifest.json
</success_criteria>

<output>
After completion, create `.planning/quick/260403-fak-fix-stale-docs-sync-counters-and-version/260403-fak-SUMMARY.md`
</output>
