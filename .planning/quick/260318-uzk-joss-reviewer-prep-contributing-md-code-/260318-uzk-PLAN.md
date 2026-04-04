---
phase: quick
plan: 260318-uzk
type: execute
wave: 1
depends_on: []
files_modified:
  - CONTRIBUTING.md
  - CODE_OF_CONDUCT.md
  - paper.md
  - paper.bib
autonomous: true
requirements: [JOSS-CONTRIB, JOSS-COC, JOSS-SOTF]
must_haves:
  truths:
    - "CONTRIBUTING.md contains the exact 6-step new claim procedure"
    - "CODE_OF_CONDUCT.md is Contributor Covenant v2.1"
    - "paper.md State of the Field mentions ReproZip and Binder as complementary container tools"
    - "paper.bib has citation entries for ReproZip and Binder"
  artifacts:
    - path: "CONTRIBUTING.md"
      provides: "Full contribution guide with 6-step claim procedure and PR workflow"
    - path: "CODE_OF_CONDUCT.md"
      provides: "Contributor Covenant v2.1 code of conduct"
    - path: "paper.md"
      provides: "Updated State of the Field section"
    - path: "paper.bib"
      provides: "New bib entries for ReproZip and Binder"
  key_links:
    - from: "paper.md"
      to: "paper.bib"
      via: "citation keys reprozip2015 and binder2018"
      pattern: "@reprozip|@binder"
---

<objective>
Prepare the repository for JOSS reviewer expectations: add a comprehensive CONTRIBUTING.md
with the mandatory 6-step new claim procedure, add a standard CODE_OF_CONDUCT.md
(Contributor Covenant v2.1), and update paper.md State of the Field to mention ReproZip
and Binder as complementary container-based reproducibility tools.

Purpose: JOSS reviewers check for CONTRIBUTING.md, CODE_OF_CONDUCT.md, and adequate
positioning against related tools. This closes all three gaps in one plan.

Output: Updated CONTRIBUTING.md, new CODE_OF_CONDUCT.md, updated paper.md + paper.bib.
All on a fix/joss-reviewer-prep branch with a PR.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CONTRIBUTING.md
@paper.md
@paper.bib
@CLAUDE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update CONTRIBUTING.md with 6-step claim procedure and add CODE_OF_CONDUCT.md</name>
  <files>CONTRIBUTING.md, CODE_OF_CONDUCT.md</files>
  <action>
**CONTRIBUTING.md** — Rewrite to include the following sections (preserve existing content where applicable but restructure):

1. **Before you start** — Keep existing verification commands (steward_audit, pytest, deep_verify). Keep "Current state: 14 claims, 511 tests, 5 verification layers."

2. **Git Workflow** — Add section:
   - Always branch from main: `git checkout -b feat/description` or `fix/description`
   - Never push directly to main
   - PR required, CI must pass before merge

3. **What you can contribute** — Keep existing list.

4. **Adding a New Claim — Mandatory 6 Steps** — This is the critical addition. Copy the exact 6-step procedure from CLAUDE.md:
   ```
   1. backend/progress/<claim_id>.py — implementation + 4-step Step Chain
   2. backend/progress/runner.py — add dispatch block
   3. reports/scientific_claim_index.md — register claim
   4. reports/canonical_state.md — add to current_claims_list
   5. tests/<domain>/test_<claim_id>.py — pass/fail/determinism tests
   6. UPDATE COUNTERS in: index.html (11 places incl prose), README.md, AGENTS.md,
      llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md, known_faults.yaml
   ```
   Also include the Step Chain template code block from CLAUDE.md and the required return structure.

5. **What NOT to change** — Keep existing sealed files list.

6. **Pull request requirements** — Keep existing 3 requirements.

7. **Full verification** — Keep existing deep_verify section.

**CODE_OF_CONDUCT.md** — Create as Contributor Covenant v2.1. Use the standard text from https://www.contributor-covenant.org/version/2/1/code_of_conduct/. Set contact method to: GitHub Issues on this repository. Set community name to "MetaGenesis Core".

IMPORTANT: Do NOT use any banned terms (see CLAUDE.md). Use "tamper-evident" not "tamper-proof".
  </action>
  <verify>
    <automated>grep -c "6 Steps\|Step Chain\|_hash_step\|trace_root_hash" CONTRIBUTING.md | xargs test 4 -le && grep -c "Contributor Covenant" CODE_OF_CONDUCT.md | xargs test 1 -le && echo "PASS"</automated>
  </verify>
  <done>
    CONTRIBUTING.md contains the full 6-step new claim procedure with Step Chain template.
    CODE_OF_CONDUCT.md exists as Contributor Covenant v2.1.
  </done>
</task>

<task type="auto">
  <name>Task 2: Update paper.md State of the Field with ReproZip and Binder, add bib entries</name>
  <files>paper.md, paper.bib</files>
  <action>
**paper.bib** — Add two new entries:

```bibtex
@inproceedings{chirigati2016reprozip,
  title     = {{ReproZip}: Computational Reproducibility With Ease},
  author    = {Chirigati, Fernando and Rampin, R{\'e}mi and Shasha, Dennis and Freire, Juliana},
  booktitle = {Proceedings of the 2016 International Conference on Management of Data (SIGMOD)},
  pages     = {2085--2088},
  year      = {2016},
  doi       = {10.1145/2882903.2899401}
}

@article{jupyter2018binder,
  title   = {Binder 2.0 -- Reproducible, Interactive, Sharable Environments for Science at Scale},
  author  = {{Project Jupyter} and others},
  journal = {Proceedings of the 17th Python in Science Conference (SciPy)},
  pages   = {113--120},
  year    = {2018},
  doi     = {10.25080/Majora-4af1f417-011}
}
```

**paper.md** — In the "State of the Field" section, after the first paragraph (ending with "collaborative experiment dashboards."), insert a new paragraph:

```
Container-based approaches complement these tracking tools. ReproZip
[@chirigati2016reprozip] captures system-level dependencies into a
self-contained package that can be replayed on any machine. Binder
[@jupyter2018binder] wraps repositories into executable cloud environments,
enabling one-click reproduction of notebooks. These tools solve the
environment problem — ensuring the same code runs in the same context —
but do not produce cryptographic evidence that a specific computation
met a specific verification threshold.
```

This goes AFTER "collaborative experiment dashboards." paragraph and BEFORE "These tools excel at tracking" paragraph.

Do NOT change any other section of paper.md. Minimal, surgical edit.
  </action>
  <verify>
    <automated>grep -c "ReproZip\|Binder\|chirigati2016reprozip\|jupyter2018binder" paper.md paper.bib | grep -v ":0" | wc -l | xargs test 4 -le && echo "PASS"</automated>
  </verify>
  <done>
    paper.md State of the Field mentions ReproZip and Binder as complementary container tools.
    paper.bib has citation entries for both.
    No other sections of paper.md are modified.
  </done>
</task>

<task type="auto">
  <name>Task 3: Create branch, commit, push, and open PR</name>
  <files></files>
  <action>
1. Create branch from main: `git checkout -b fix/joss-reviewer-prep`
2. Stage the 4 modified files: CONTRIBUTING.md, CODE_OF_CONDUCT.md, paper.md, paper.bib
3. Commit with message: "docs: add CODE_OF_CONDUCT.md, expand CONTRIBUTING.md, update paper.md State of the Field"
4. Push: `git push -u origin fix/joss-reviewer-prep`
5. Create PR using gh CLI:
   - Title: "JOSS reviewer prep: CONTRIBUTING, CODE_OF_CONDUCT, State of the Field"
   - Body should summarize:
     - Added CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
     - Expanded CONTRIBUTING.md with mandatory 6-step new claim procedure and Step Chain template
     - Updated paper.md State of the Field to mention ReproZip and Binder as complementary container-based tools
     - Added paper.bib entries for ReproZip (Chirigati et al. 2016) and Binder (Project Jupyter 2018)

IMPORTANT: Do NOT run verification gates (steward_audit, pytest, deep_verify) — these are doc-only changes and the executor should not spend context on 511 tests. But DO run `python scripts/check_stale_docs.py` to ensure no stale doc issues.

IMPORTANT: Create the branch BEFORE making commits. Do not commit to main.
  </action>
  <verify>
    <automated>git log --oneline -1 | grep -q "joss-reviewer-prep\|CONTRIBUTING\|CODE_OF_CONDUCT\|State of the Field" && gh pr view --json state -q .state 2>/dev/null | grep -q "OPEN" && echo "PASS"</automated>
  </verify>
  <done>
    Branch fix/joss-reviewer-prep exists with the commit.
    PR is open on GitHub with descriptive title and body.
  </done>
</task>

</tasks>

<verification>
- CONTRIBUTING.md has the 6-step claim procedure with Step Chain template
- CODE_OF_CONDUCT.md is Contributor Covenant v2.1
- paper.md State of the Field mentions ReproZip and Binder
- paper.bib has entries for chirigati2016reprozip and jupyter2018binder
- PR is open on GitHub from fix/joss-reviewer-prep branch
- No banned terms used anywhere
</verification>

<success_criteria>
PR created and visible on GitHub. All four files updated correctly.
CONTRIBUTING.md contains the exact 6-step new claim procedure from CLAUDE.md.
CODE_OF_CONDUCT.md is standard Contributor Covenant v2.1.
paper.md mentions ReproZip and Binder in State of the Field only.
</success_criteria>

<output>
After completion, create `.planning/quick/260318-uzk-joss-reviewer-prep-contributing-md-code-/260318-uzk-SUMMARY.md`
</output>
