---
phase: quick
plan: 260319-szi
type: execute
wave: 1
depends_on: []
files_modified:
  - .github/workflows/weekly_agent_health.yml
  - AGENT_TASKS.md
  - .zenodo.json
  - docs/SOFTWAREX_PLAN.md
  - reports/AGENT_REPORT_20260319.md
autonomous: true
requirements: []
must_haves:
  truths:
    - "weekly_agent_health.yml contains all 8 python script invocations"
    - "TASK-016, TASK-017, TASK-018 are executed via agent_research.py"
    - "Changes committed to fix/ci-divine branch and pushed"
  artifacts:
    - path: ".github/workflows/weekly_agent_health.yml"
      provides: "Complete CI workflow with all 8 agent scripts"
      contains: "agent_evolve_self"
  key_links: []
---

<objective>
Fix 2 gaps in the weekly agent health CI workflow and execute 3 pending research tasks.

Purpose: The weekly_agent_health.yml is missing 4 agent script steps, and TASK-016/017/018 have never been executed.
Output: Complete CI workflow with all 8 scripts, 3 research tasks executed, committed and pushed on fix/ci-divine.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.github/workflows/weekly_agent_health.yml
@AGENT_TASKS.md
@scripts/agent_evolution.py
@scripts/agent_chronicle.py
@scripts/agent_coverage.py
@scripts/agent_evolve_self.py
@scripts/agent_research.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add 4 missing steps to weekly_agent_health.yml</name>
  <files>.github/workflows/weekly_agent_health.yml</files>
  <action>
Edit .github/workflows/weekly_agent_health.yml to add 4 new steps AFTER the "Agent signals (external relay)" step and BEFORE the "Agent learning (observe and record)" step. The 4 new steps are:

```yaml
      - name: Agent evolution summary
        run: |
          python scripts/agent_evolution.py --summary

      - name: Agent chronicle summary
        run: |
          python scripts/agent_chronicle.py --summary

      - name: Agent coverage summary
        run: |
          python scripts/agent_coverage.py --summary

      - name: Agent self-evolution summary
        run: |
          python scripts/agent_evolve_self.py --summary
```

The final step order in the workflow must be:
1. Checkout repo
2. Set up Python
3. Install dependencies
4. Agent research (execute next pending task)
5. Agent signals (external relay)
6. Agent evolution summary
7. Agent chronicle summary
8. Agent coverage summary
9. Agent self-evolution summary
10. Agent learning (observe and record)

Ensure proper YAML indentation (6 spaces for step names, 8 spaces for run content).
  </action>
  <verify>
    <automated>grep -c "python scripts/agent_" .github/workflows/weekly_agent_health.yml | grep -q "^7$" && echo "PASS: 7 agent script lines found" || echo "FAIL"</automated>
  </verify>
  <done>weekly_agent_health.yml contains all 7 python scripts/agent_* invocations (agent_research, agent_signals, agent_evolution, agent_chronicle, agent_coverage, agent_evolve_self, agent_learn) across 7 workflow steps</done>
</task>

<task type="auto">
  <name>Task 2: Execute TASK-016, TASK-017, TASK-018 via agent_research.py</name>
  <files>AGENT_TASKS.md, .zenodo.json, docs/SOFTWAREX_PLAN.md, reports/AGENT_REPORT_20260319.md</files>
  <action>
Run `python scripts/agent_research.py` three times sequentially. Each run picks up the next PENDING task:
- Run 1: executes TASK-016 (Zenodo DOI preparation -> .zenodo.json)
- Run 2: executes TASK-017 (SoftwareX submission plan -> docs/SOFTWAREX_PLAN.md)
- Run 3: executes TASK-018 (Client outreach analysis -> reports/AGENT_REPORT_*.md)

After each run, verify the output file was created. If agent_research.py does not auto-advance to the next task, check AGENT_TASKS.md to confirm status changes.

Note: The exact output files depend on agent_research.py's implementation. Check what it produces after each run.
  </action>
  <verify>
    <automated>python scripts/agent_research.py 2>&1 | tail -5; python scripts/agent_research.py 2>&1 | tail -5; python scripts/agent_research.py 2>&1 | tail -5; echo "---"; grep -c "DONE\|COMPLETE" AGENT_TASKS.md</automated>
  </verify>
  <done>TASK-016, TASK-017, TASK-018 all marked as DONE/COMPLETE in AGENT_TASKS.md, output files exist</done>
</task>

<task type="auto">
  <name>Task 3: Verify, commit to fix/ci-divine, and push</name>
  <files></files>
  <action>
1. Verify weekly_agent_health.yml has all 8 python script invocations (7 agent_* scripts + 1 agent_learn.py observe):
   ```bash
   grep "python scripts/" .github/workflows/weekly_agent_health.yml
   ```
   Expected: 7 lines with agent_research, agent_signals, agent_evolution, agent_chronicle, agent_coverage, agent_evolve_self, agent_learn.

2. Switch to branch fix/ci-divine (create if needed from current branch):
   ```bash
   git checkout -b fix/ci-divine 2>/dev/null || git checkout fix/ci-divine
   ```

3. Stage all changed files:
   ```bash
   git add .github/workflows/weekly_agent_health.yml AGENT_TASKS.md
   ```
   Also stage any output files from TASK-016/017/018 (e.g., .zenodo.json, docs/SOFTWAREX_PLAN.md, reports/AGENT_REPORT_*.md).

4. Commit with message: "fix: add 4 missing agent steps to weekly_agent_health.yml + execute TASK-016/017/018"

5. Push: `git push origin fix/ci-divine`
  </action>
  <verify>
    <automated>git log --oneline -1 && git branch --show-current | grep -q "fix/ci-divine" && echo "PASS" || echo "FAIL"</automated>
  </verify>
  <done>All changes committed on fix/ci-divine branch and pushed to origin. weekly_agent_health.yml has all 8 python scripts. TASK-016/017/018 executed.</done>
</task>

</tasks>

<verification>
- `grep "python scripts/" .github/workflows/weekly_agent_health.yml` shows 7 lines
- `git branch --show-current` returns `fix/ci-divine`
- `git log --oneline -1` shows the fix commit
- AGENT_TASKS.md shows TASK-016/017/018 as DONE
</verification>

<success_criteria>
1. weekly_agent_health.yml has all 7 agent script invocations (research, signals, evolution, chronicle, coverage, evolve_self, learn)
2. TASK-016, TASK-017, TASK-018 executed and marked done
3. Changes committed and pushed on fix/ci-divine branch
</success_criteria>

<output>
After completion, create `.planning/quick/260319-szi-fix-ci-weekly-agent-health-yml-gaps-exec/260319-szi-SUMMARY.md`
</output>
