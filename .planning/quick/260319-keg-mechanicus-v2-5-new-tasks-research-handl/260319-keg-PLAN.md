---
phase: quick
plan: 260319-keg
type: execute
wave: 1
depends_on: []
files_modified:
  - AGENT_TASKS.md
  - scripts/agent_research.py
  - scripts/agent_evolution.py
autonomous: true
requirements: [MECH-V2]
must_haves:
  truths:
    - "AGENT_TASKS.md contains TASK-006 through TASK-010 with PENDING status"
    - "agent_research.py has execute_task_006 through execute_task_010 handlers that read real repo files"
    - "agent_evolution.py section() calls include Mechanicus atmosphere lines without changing functional code"
    - "Running agent_research.py executes TASK-006 successfully and produces a dated report"
    - "All changes are committed on feat/mechanicus-v2 branch and pushed"
  artifacts:
    - path: "AGENT_TASKS.md"
      provides: "5 new PENDING tasks (TASK-006 through TASK-010)"
      contains: "TASK-010"
    - path: "scripts/agent_research.py"
      provides: "Handlers execute_task_006 through execute_task_010"
      contains: "execute_task_010"
    - path: "scripts/agent_evolution.py"
      provides: "Mechanicus atmosphere in section() calls"
    - path: "reports/AGENT_REPORT_20260319.md"
      provides: "TASK-006 execution output"
  key_links:
    - from: "scripts/agent_research.py"
      to: "AGENT_TASKS.md"
      via: "execute_task dispatch dict"
      pattern: "TASK-006.*execute_task_006"
---

<objective>
Upgrade Mechanicus agent system to v2: add 5 new research tasks (TASK-006 through TASK-010), implement real handlers, add atmosphere lines to evolution script, execute TASK-006, and ship on feat/mechanicus-v2 branch.

Purpose: Expand agent research capabilities with adversarial testing, claim dependency mapping, temporal verification audit, bundle size optimization, and cross-layer attack surface analysis.
Output: Updated AGENT_TASKS.md, agent_research.py, agent_evolution.py, execution report, pushed branch.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@AGENT_TASKS.md
@scripts/agent_research.py
@scripts/agent_evolution.py
@CLAUDE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add 5 new tasks to AGENT_TASKS.md and implement handlers in agent_research.py</name>
  <files>AGENT_TASKS.md, scripts/agent_research.py</files>
  <action>
**AGENT_TASKS.md** — Append 5 new task blocks after TASK-005, all with Status: PENDING:

```
### TASK-006
- **Title:** Adversarial tests for SYSID-01 (weakest coverage claim)
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** SYSID-01 was identified as weakest-coverage claim in TASK-001. Write 3 adversarial test scenarios: (1) step chain hash tamper, (2) semantic field stripping, (3) threshold boundary injection. Read sysid1_arx_calibration.py to extract exact thresholds and field names.

### TASK-007
- **Title:** Map claim dependency graph
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Analyze all 14 claim files in backend/progress/ to build a dependency graph. Find which claims reference other claims (e.g., DRIFT-01 depends on MTR-1, DT-CALIB-LOOP-01 depends on DRIFT-01). Output adjacency list and identify isolated claims with no dependencies.

### TASK-008
- **Title:** Temporal verification layer audit
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read scripts/mg_temporal.py and tests/steward/test_cert10*. Audit: (1) which NIST Beacon features are used, (2) what attack vectors CERT-10 covers, (3) propose 2 new temporal attack scenarios not yet tested (e.g., timezone manipulation, leap second edge case).

### TASK-009
- **Title:** Bundle size optimization analysis
- **Status:** PENDING
- **Priority:** P3
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Analyze a typical pack bundle output. Measure sizes of pack_manifest.json, evidence files, and signature files. Identify which components dominate bundle size. Propose compression or deduplication strategies without breaking SHA-256 integrity verification.

### TASK-010
- **Title:** Cross-layer attack surface analysis
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** For each of the 5 verification layers, enumerate the exact attack vectors tested by CERT-02 through CERT-12. Build a matrix: layers (rows) x CERT tests (columns). Find any layer that has fewer than 2 dedicated attack tests. Propose gap-closing tests.
```

**scripts/agent_research.py** — Make two changes:

1. **Update the dispatch dict** in `execute_task()` (around line 87-93) to add entries for TASK-006 through TASK-010:
```python
handlers = {
    "TASK-001": execute_task_001,
    "TASK-002": execute_task_002,
    "TASK-003": execute_task_003,
    "TASK-004": execute_task_004,
    "TASK-005": execute_task_005,
    "TASK-006": execute_task_006,
    "TASK-007": execute_task_007,
    "TASK-008": execute_task_008,
    "TASK-009": execute_task_009,
    "TASK-010": execute_task_010,
}
```

2. **Add 5 new handler functions** after `execute_task_005()` (after line 862), before the `mark_task_done` section. Each handler MUST read real repo files and produce substantive analysis. Follow the same pattern as existing handlers (return markdown string built from `lines` list).

**execute_task_006():** Read `backend/progress/sysid1_arx_calibration.py` to extract JOB_KIND, threshold, step chain fields. Read `tests/` to find existing SYSID-01 tests. Generate 3 concrete adversarial test scenarios with exact file paths, function names, and assertion logic. Include the actual threshold value and field names from the source file.

**execute_task_007():** Read all 14 claim files from `backend/progress/`. For each file, search for imports or references to other claim modules (e.g., `import`, `from backend.progress`, references to other claim IDs). Build an adjacency list. Count isolated vs connected claims. Format as a dependency table.

**execute_task_008():** Read `scripts/mg_temporal.py` and glob `tests/steward/test_cert10*`. Extract: what functions mg_temporal exports, what attack scenarios test_cert10 covers (by parsing test function names and docstrings). Propose 2 new attack scenarios.

**execute_task_009():** Check if `build/` or any pack output directory exists. Read `scripts/mg.py` to find pack-related functions. Analyze what files go into a bundle by reading the pack logic. Estimate sizes from code structure. Propose optimization strategies.

**execute_task_010():** Read all `tests/steward/test_cert*.py` files. For each CERT test file, extract test function names. Map each test to the layer(s) it tests (Layer 1=SHA-256, Layer 2=Semantic, Layer 3=Step Chain, Layer 4=Signing, Layer 5=Temporal). Build a matrix and identify gaps.

Each handler should be ~60-120 lines following the exact pattern of existing handlers (lines list, datetime header, file reads via Path, regex extraction, markdown output).
  </action>
  <verify>
    <automated>python -c "from scripts.agent_research import execute_task_006, execute_task_007, execute_task_008, execute_task_009, execute_task_010; print('All 5 handlers import OK')"</automated>
  </verify>
  <done>AGENT_TASKS.md has TASK-006 through TASK-010 all with PENDING status. agent_research.py dispatch dict maps all 10 tasks. All 5 new handler functions exist and are importable.</done>
</task>

<task type="auto">
  <name>Task 2: Add Mechanicus atmosphere lines to agent_evolution.py section() calls</name>
  <files>scripts/agent_evolution.py</files>
  <action>
Add Mechanicus 40K atmosphere flavor text to the `section()` calls in agent_evolution.py. ONLY modify the string arguments to existing `section()` calls — do NOT change any functional code, logic, conditionals, return values, or variable names.

Current section() calls and their replacements:

- Line 56: `section("STEWARD AUDIT")` -> `section("STEWARD AUDIT — Inquisitorial Inspection")`
- Line 69: `section("TEST SUITE")` -> `section("TEST SUITE — Machine Spirit Awakening")`
- Line 85: `section("DEEP VERIFY")` -> `section("DEEP VERIFY — Rite of Pure Thought")`
- Line 100: `section("STALE DOCUMENTATION")` -> `section("STALE DOCUMENTATION — Noosphere Scan")`
- Line 117: `section("MANIFEST CONSISTENCY")` -> `section("MANIFEST CONSISTENCY — Codex Verification")`
- Line 149: `section("FORBIDDEN TERMS")` -> `section("FORBIDDEN TERMS — Hereticus Detection")`
- Line 209: `section("COVERAGE GAP ANALYSIS")` -> `section("COVERAGE GAP ANALYSIS — Forge World Audit")`
- Line 271: `section("CLAUDE.MD FRESHNESS")` -> `section("CLAUDE.MD FRESHNESS — Lexmechanic Rites")`
- Line 299: `section("WATCHLIST COVERAGE")` -> `section("WATCHLIST COVERAGE — Servo-skull Patrol")`
- Line 323: `section("BRANCH SYNC")` -> `section("BRANCH SYNC — Skitarii Synchronization")`
- Line 370: `section("SUMMARY")` -> `section("SUMMARY — Omnissiah's Verdict")`

CRITICAL: Only change the string literal inside section(). No other changes whatsoever. The functional behavior must remain identical.
  </action>
  <verify>
    <automated>python scripts/agent_evolution.py --summary 2>&1 | head -5</automated>
  </verify>
  <done>All 11 section() calls in agent_evolution.py have Mechanicus atmosphere suffixes. No functional code changed. Script runs identically to before except for cosmetic section headers.</done>
</task>

<task type="auto">
  <name>Task 3: Run TASK-006, create branch, commit, and push</name>
  <files>reports/AGENT_REPORT_20260319.md</files>
  <action>
Step 1: Create and switch to feat/mechanicus-v2 branch from current HEAD:
```bash
git checkout -b feat/mechanicus-v2
```

Step 2: Run agent_research.py to execute TASK-006 (first PENDING task):
```bash
python scripts/agent_research.py
```
This will: execute TASK-006 handler, write report to reports/AGENT_REPORT_20260319.md, mark TASK-006 as DONE in AGENT_TASKS.md.

Step 3: Verify the report was created and contains substantive SYSID-01 analysis:
```bash
head -30 reports/AGENT_REPORT_20260319.md
```

Step 4: Stage all modified files and commit:
```bash
git add AGENT_TASKS.md scripts/agent_research.py scripts/agent_evolution.py reports/AGENT_REPORT_20260319.md
git commit -m "feat: Mechanicus v2 — 5 new research tasks, handlers, atmosphere lines, TASK-006 executed"
```

Step 5: Push the branch:
```bash
git push origin feat/mechanicus-v2
```

NOTE: If agent_research.py also generates a WEEKLY_REPORT file, include that in the commit too. Also include any reports/ files that were created.
  </action>
  <verify>
    <automated>git log --oneline -1 && git branch --show-current && test -f reports/AGENT_REPORT_20260319.md && echo "ALL OK"</automated>
  </verify>
  <done>feat/mechanicus-v2 branch exists with commit containing all changes. TASK-006 report exists in reports/. Branch is pushed to origin. AGENT_TASKS.md shows TASK-006 as DONE and TASK-007 through TASK-010 as PENDING.</done>
</task>

</tasks>

<verification>
1. AGENT_TASKS.md contains exactly 10 tasks (TASK-001 through TASK-010)
2. TASK-001 through TASK-006 are DONE, TASK-007 through TASK-010 are PENDING
3. agent_research.py dispatch dict has all 10 entries
4. All 5 new handlers are callable and produce markdown output
5. agent_evolution.py section headers have Mechanicus flavor text
6. agent_evolution.py still runs without errors
7. reports/AGENT_REPORT_20260319.md exists with SYSID-01 adversarial analysis
8. feat/mechanicus-v2 branch exists and is pushed
</verification>

<success_criteria>
- `python -c "from scripts.agent_research import execute_task_010"` succeeds
- `python scripts/agent_evolution.py --summary` runs without errors
- `git log --oneline feat/mechanicus-v2 -1` shows the commit
- `grep -c "PENDING" AGENT_TASKS.md` returns 4 (TASK-007 through TASK-010)
- reports/AGENT_REPORT_20260319.md contains "SYSID-01" and adversarial test proposals
</success_criteria>

<output>
After completion, create `.planning/quick/260319-keg-mechanicus-v2-5-new-tasks-research-handl/260319-keg-SUMMARY.md`
</output>
