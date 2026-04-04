---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - system_manifest.json
  - README.md
  - AGENTS.md
  - llms.txt
  - CLAUDE.md
  - index.html
  - CONTEXT_SNAPSHOT.md
  - reports/known_faults.yaml
  - scripts/check_stale_docs.py
  - CONTRIBUTING.md
  - CITATION.cff
  - docs/ARCHITECTURE.md
  - docs/ROADMAP.md
  - ppa/README_PPA.md
  - CURSOR_MASTER_PROMPT_v2_3.md
  - docs/HOW_TO_ADD_CLAIM.md
  - docs/REAL_DATA_GUIDE.md
  - docs/USE_CASES.md
  - reports/scientific_claim_index.md
  - paper.md
autonomous: true
requirements: [COUNTER-SYNC-608]
must_haves:
  truths:
    - "All files monitored by check_stale_docs.py pass content validation with 608 instead of 601"
    - "check_stale_docs.py itself requires 608 and bans 601"
    - "python scripts/check_stale_docs.py --strict exits 0"
  artifacts:
    - path: "system_manifest.json"
      provides: "test_count: 608"
      contains: "608"
    - path: "scripts/check_stale_docs.py"
      provides: "Updated banned/required strings"
      contains: "608"
  key_links:
    - from: "scripts/check_stale_docs.py"
      to: "all doc files"
      via: "CONTENT_CHECKS required/banned lists"
      pattern: "608"
---

<objective>
Update test count from 601 to 608 across all documentation and validation files after adding 7 new tests in test_agent_pr_creator.py.

Purpose: Keep all counters in sync per the project's update protocol (CLAUDE.md step 6).
Output: All files pass check_stale_docs.py --strict with 608 test count.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@scripts/check_stale_docs.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update check_stale_docs.py banned/required lists (601->608)</name>
  <files>scripts/check_stale_docs.py</files>
  <action>
In scripts/check_stale_docs.py CONTENT_CHECKS dictionary, for EVERY file entry that has "601" in its `required` list or references "601" anywhere:

1. Move "601" from `required` to `banned` (add "601 passing", "601 tests", "601 adversarial", "601" as appropriate — match the existing pattern of how older counts like "595 passed", "544 tests" etc. are banned).
2. Add "608" to `required` in its place (matching the same string format: "608 passing", "608 tests", "608 adversarial", "608" etc.).

Files affected in CONTENT_CHECKS (grep for "601"):
- CONTRIBUTING.md: required "601" -> ban "601 passed" (or "601"), require "608"
- CITATION.cff: required "601" -> ban "601", require "608"
- docs/ARCHITECTURE.md: required "601 tests" -> ban "601 tests", require "608 tests"
- docs/ROADMAP.md: required "601 adversarial" -> ban "601 adversarial", require "608 adversarial"
- ppa/README_PPA.md: required "601 tests" -> ban "601 tests", require "608 tests"
- README.md: required "601" -> ban "601 passing" (add to existing banned list), require "608"
- index.html: no "601" in required (uses span counts) — skip unless present
- paper.md: required "601 adversarial" -> ban "601 adversarial", require "608 adversarial"
- reports/known_faults.yaml: required "601 tests", "601 passed" -> ban those, require "608 tests", "608 passed"
- CLAUDE.md: required "601 tests" -> ban "601 tests", require "608 tests"
- CURSOR_MASTER_PROMPT_v2_3.md: required "601 tests" -> ban "601 tests", require "608 tests"
- docs/HOW_TO_ADD_CLAIM.md: required "601" -> ban "601", require "608"
- docs/REAL_DATA_GUIDE.md: required "601" -> ban "601", require "608"
- docs/USE_CASES.md: required "601" -> ban "601", require "608"
- reports/scientific_claim_index.md: required "601" -> ban "601", require "608"

Also update the BANNED TERMS section in CLAUDE.md itself: change `"100% test success" -> "601 tests PASS"` to `"100% test success" -> "608 tests PASS"`.

IMPORTANT: Do NOT modify any SEALED files listed in CLAUDE.md.
  </action>
  <verify>
    <automated>python -c "import ast; exec(open('scripts/check_stale_docs.py').read()); [print(f'FAIL: {k} still has 601 in required') for k,v in CONTENT_CHECKS.items() if any('601' in r for r in v.get('required',[]))]" 2>&1 | grep FAIL && echo "FAILED" || echo "PASSED - no 601 in required lists"</automated>
  </verify>
  <done>check_stale_docs.py CONTENT_CHECKS has 608 in all required lists where 601 was, and 601 is in banned lists</done>
</task>

<task type="auto">
  <name>Task 2: Update 601->608 in all documentation files</name>
  <files>
    system_manifest.json, README.md, AGENTS.md, llms.txt, CLAUDE.md,
    index.html, CONTEXT_SNAPSHOT.md, reports/known_faults.yaml,
    CONTRIBUTING.md, CITATION.cff, docs/ARCHITECTURE.md, docs/ROADMAP.md,
    ppa/README_PPA.md, CURSOR_MASTER_PROMPT_v2_3.md, docs/HOW_TO_ADD_CLAIM.md,
    docs/REAL_DATA_GUIDE.md, docs/USE_CASES.md, reports/scientific_claim_index.md,
    paper.md
  </files>
  <action>
For each file, replace all occurrences of "601" (test count) with "608". Be careful NOT to replace "601" that appears in non-test-count contexts (e.g., port numbers, dates, hash values). In practice for this repo, all "601" references ARE test counts.

Specific files and what to change:

1. **system_manifest.json** — "test_count": 601 -> 608
2. **README.md** — "601 passing" -> "608 passing", any other 601 test refs
3. **AGENTS.md** — acceptance threshold 601 -> 608
4. **llms.txt** — current state 601 -> 608
5. **CLAUDE.md** — "601 tests" -> "608 tests" in CURRENT STATE, BANNED TERMS, KEY FILES, header line. Multiple occurrences (~4-5 places).
6. **index.html** — Use PowerShell: `(Get-Content index.html -Raw) -replace '601', '608' | Set-Content index.html` — catches all 11+ places including prose.
7. **CONTEXT_SNAPSHOT.md** — 601 -> 608
8. **reports/known_faults.yaml** — "601 tests", "601 passed" -> "608 tests", "608 passed"
9. **CONTRIBUTING.md** — 601 -> 608
10. **CITATION.cff** — 601 -> 608
11. **docs/ARCHITECTURE.md** — "601 tests" -> "608 tests"
12. **docs/ROADMAP.md** — "601 adversarial" -> "608 adversarial"
13. **ppa/README_PPA.md** — "601 tests" -> "608 tests"
14. **CURSOR_MASTER_PROMPT_v2_3.md** — "601 tests" -> "608 tests"
15. **docs/HOW_TO_ADD_CLAIM.md** — 601 -> 608
16. **docs/REAL_DATA_GUIDE.md** — 601 -> 608
17. **docs/USE_CASES.md** — 601 -> 608
18. **reports/scientific_claim_index.md** — 601 -> 608
19. **paper.md** — "601 adversarial" -> "608 adversarial"

For index.html specifically, use PowerShell batch replace per CLAUDE.md BUG 7:
```powershell
(Get-Content index.html -Raw) -replace '601', '608' | Set-Content index.html
```

Do NOT touch SEALED files (steward_audit.py, canonical_state.md, etc.).
  </action>
  <verify>
    <automated>python scripts/check_stale_docs.py --strict</automated>
  </verify>
  <done>All files contain 608 test count. `python scripts/check_stale_docs.py --strict` exits 0 with no CONTENT issues. No file still contains "601" as a test count reference.</done>
</task>

</tasks>

<verification>
1. `python scripts/check_stale_docs.py --strict` exits 0
2. `grep -r "601" system_manifest.json README.md AGENTS.md llms.txt CLAUDE.md CONTEXT_SNAPSHOT.md` returns no matches
3. All banned/required lists in check_stale_docs.py reference 608, not 601
</verification>

<success_criteria>
- Every file that previously contained "601" as a test count now contains "608"
- check_stale_docs.py CONTENT_CHECKS bans "601" and requires "608" for all relevant files
- `python scripts/check_stale_docs.py --strict` passes cleanly
- Branch fix/counter-sync-608 committed and pushed
</success_criteria>

<output>
After completion, create `.planning/quick/260330-vbc-counter-sync-601-608-per-update-protocol/260330-vbc-SUMMARY.md`
</output>
