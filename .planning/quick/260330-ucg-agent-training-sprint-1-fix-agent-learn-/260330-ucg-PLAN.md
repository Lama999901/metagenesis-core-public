---
phase: quick
plan: 260330-ucg
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/agent_learn.py
  - AGENT_TASKS.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "agent_learn.py scan_file_for_stale no longer false-positives on '282' in ppa/README_PPA.md"
    - "AGENT_TASKS.md contains TASK-022 through TASK-026 after TASK-021"
  artifacts:
    - path: "scripts/agent_learn.py"
      provides: "Fixed scan_file_for_stale with skip_282 logic for README_PPA.md"
    - path: "AGENT_TASKS.md"
      provides: "5 new tasks (TASK-022 through TASK-026)"
  key_links: []
---

<objective>
Agent Training Sprint 1: Fix agent_learn.py false positive on "282" in ppa/README_PPA.md and append 5 new tasks (TASK-022 through TASK-026) to AGENT_TASKS.md.

Purpose: The "282" string in ppa/README_PPA.md is a legitimate PPA section number, not a stale test count. The current scan flags it as stale across 51+ sessions. Adding TASK-022-026 continues the agent task backlog.
Output: Patched agent_learn.py, extended AGENT_TASKS.md
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/agent_learn.py
@AGENT_TASKS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix agent_learn.py false positive and append AGENT_TASKS</name>
  <files>scripts/agent_learn.py, AGENT_TASKS.md</files>
  <action>
CHANGE 1 — scripts/agent_learn.py, function scan_file_for_stale():
Find lines 99-100:
```python
    old_counts = [c for c in ["295", "271", "270", "282", "389", "391", "471"]
                  if c in content and str(etalon_count) not in content]
```
Replace with:
```python
    skip_282 = path.name == 'README_PPA.md'
    old_counts = [c for c in ["295", "271", "270", "282", "389", "391", "471"]
                  if c in content
                  and str(etalon_count) not in content
                  and not (c == "282" and skip_282)]
```

CHANGE 2 — AGENT_TASKS.md:
Append after the TASK-021 block (after its Description line) the following 5 tasks:

### TASK-022
- **Title:** Fix stale docs false positive (282 in README_PPA.md)
- **Status:** DONE (2026-03-30)
- **Priority:** P1
- **Output:** scripts/agent_learn.py
- **Description:** Fix scan_file_for_stale() to skip "282" match in ppa/README_PPA.md since it is a PPA section number, not a stale test count. Eliminates 51-session recurring false positive.

### TASK-023
- **Title:** UPDATE_PROTOCOL.md v1.1
- **Status:** BACKLOG
- **Priority:** P2
- **Output:** docs/UPDATE_PROTOCOL.md
- **Description:** Create or update UPDATE_PROTOCOL.md documenting the exact counter-sync procedure: which files to update, in what order, with what commands. Codify lessons from 51 sessions of counter drift.

### TASK-024
- **Title:** Fix ppa/README_PPA.md version references
- **Status:** BACKLOG
- **Priority:** P2
- **Output:** ppa/README_PPA.md
- **Description:** Audit ppa/README_PPA.md for stale version strings (v0.4.0, v0.5.0 etc). Update to current version. Ensure PPA section numbers (like 282) are not confused with test counts.

### TASK-025
- **Title:** PHYS-01/PHYS-02 audit and adversarial tests
- **Status:** BACKLOG
- **Priority:** P1
- **Output:** tests/test_phys_adversarial.py
- **Description:** Audit PHYS-01 (Boltzmann) and PHYS-02 (Avogadro) claims for adversarial test coverage. Write tamper tests: modified constants, wrong units, trace manipulation. Verify 4-step chain integrity.

### TASK-026
- **Title:** Wave-2 outreach drafts
- **Status:** BACKLOG
- **Priority:** P3
- **Output:** docs/OUTREACH_WAVE2.md
- **Description:** Draft outreach messages for Wave-2 targets (Chollet, LMArena, Percy Liang). Each message should reference MetaGenesis verification protocol with specific relevance to their work.

Branch: fix/agent-training-sprint1. Commit message: "fix: agent_learn.py false positive + TASK-022-026". Push to origin.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -c "from scripts.agent_learn import scan_file_for_stale; from pathlib import Path; issues = scan_file_for_stale(Path('ppa/README_PPA.md'), 601, '0.7.0'); print('PASS' if not any('282' in str(i) for i in issues) else 'FAIL: ' + str(issues))"</automated>
  </verify>
  <done>
    - scan_file_for_stale returns no false positive for "282" when scanning ppa/README_PPA.md
    - AGENT_TASKS.md contains TASK-022 through TASK-026 with correct format
    - Changes committed on branch fix/agent-training-sprint1 and pushed
  </done>
</task>

</tasks>

<verification>
1. Python inline test confirms no "282" false positive on README_PPA.md
2. grep AGENT_TASKS.md for TASK-022 through TASK-026 — all 5 present
3. git log shows commit on fix/agent-training-sprint1
</verification>

<success_criteria>
- agent_learn.py no longer flags ppa/README_PPA.md for stale "282"
- AGENT_TASKS.md has 26 tasks (TASK-001 through TASK-026)
- Branch fix/agent-training-sprint1 pushed to origin
</success_criteria>

<output>
After completion, create `.planning/quick/260330-ucg-agent-training-sprint-1-fix-agent-learn-/260330-ucg-SUMMARY.md`
</output>
