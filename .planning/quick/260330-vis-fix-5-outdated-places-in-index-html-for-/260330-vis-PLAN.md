---
phase: quick
plan: 260330-vis
type: execute
wave: 1
depends_on: []
files_modified: [index.html]
autonomous: true
requirements: [SITE-V08-SYNC]
must_haves:
  truths:
    - "Footer shows MVP v0.8, not v0.7"
    - "Terminal canonical_state list shows all 20 claims"
    - "Site map (mega-overlay) canonical_state.md says 20 verified claims"
    - "Agent bar canonical_state.md says 20 verified claims"
    - "Mobile menu accordion lists all 20 claims (not just 8)"
  artifacts:
    - path: "index.html"
      provides: "All 5 outdated spots fixed"
  key_links: []
---

<objective>
Fix 5 outdated places in index.html that still reference v0.7 or show only 14-15 claims instead of 20.

Purpose: Bring the live site into sync with v0.8 and 20-claim state after MTR-4/5/6 + PHYS-01/02 + AGENT-DRIFT-01 were added.
Output: Updated index.html with all 5 fixes applied.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@index.html
</context>

<tasks>

<task type="auto">
  <name>Task 1: Apply 5 find-and-replace edits to index.html</name>
  <files>index.html</files>
  <action>
Make exactly these 5 edits in index.html using the Edit tool:

**Edit 1 — Footer version (line ~3015):**
Replace `MVP v0.7` with `MVP v0.8` in the footer span.

**Edit 2 — Terminal canonical_state claims list (line ~2282):**
The current `<span class="tok">` contains 14 claims ending at DT-CALIB-LOOP-01.
Replace the entire content of that span with all 20 claims:
```
['MTR-1','MTR-2','MTR-3','MTR-4','MTR-5','MTR-6','SYSID-01','DATA-PIPE-01','DRIFT-01','ML_BENCH-01','DT-FEM-01',<br>'ML_BENCH-02','ML_BENCH-03','PHARMA-01','FINRISK-01','DT-SENSOR-01','DT-CALIB-LOOP-01','AGENT-DRIFT-01','PHYS-01','PHYS-02']
```
Note: keep the `<br>` line break somewhere mid-list for visual wrapping (after DT-FEM-01 as before).

**Edit 3 — Site map / mega-overlay canonical_state.md link (line ~1522):**
Change `15 verified claims` to `20 verified claims` in:
```html
<a href="...canonical_state.md" ...>canonical_state.md<span>15 verified claims</span></a>
```

**Edit 4 — Agent bar canonical_state.md link (line ~2577):**
Change `15 verified claims` to `20 verified claims` in:
```html
<span class="agent-bar-fdesc">15 verified claims</span>
```

**Edit 5 — Mobile menu accordion (lines ~1540-1550):**
The mobile menu `<div class="mm-acc-body">` for CLAIMS currently lists only 8 claims (MTR-1, MTR-2, MTR-3, then SYSID-01 through DT-FEM-01).
Replace the entire accordion body content with all 20 claims, keeping the same link pattern. Group with dividers:
- MTR-1, MTR-2, MTR-3, MTR-4, MTR-5, MTR-6 (materials group)
- divider
- PHYS-01, PHYS-02 (physics constants group)
- divider
- SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01, AGENT-DRIFT-01

Each link follows the pattern:
```html
<a href="#claims" onclick="document.querySelector('.mobile-menu').classList.remove('open');document.getElementById('hbtn').classList.remove('open')">CLAIM-ID</a>
```

After all edits, create branch and commit:
```bash
git checkout -b fix/site-v0-8-canonical
git add index.html
git commit -m "fix: update 5 outdated places in index.html for v0.8 / 20 claims"
git push origin fix/site-v0-8-canonical
```
  </action>
  <verify>
    <automated>grep -c "MVP v0.8" index.html | grep -q "1" && grep -c "20 verified claims" index.html | grep -q "2" && grep -c "PHYS-01" index.html | grep -q "[0-9]" && grep -c "AGENT-DRIFT-01" index.html | grep -q "[0-9]" && echo "ALL 5 EDITS VERIFIED"</automated>
  </verify>
  <done>
    1. Footer says "MVP v0.8" (was v0.7)
    2. Terminal canonical_state lists all 20 claims (was 14)
    3. Mega-overlay canonical_state.md span says "20 verified claims" (was 15)
    4. Agent bar canonical_state.md span says "20 verified claims" (was 15)
    5. Mobile menu lists all 20 claims (was 8)
    6. Changes committed on fix/site-v0-8-canonical and pushed
  </done>
</task>

</tasks>

<verification>
- `grep "MVP v0.8" index.html` returns 1 match (footer)
- `grep "15 verified claims" index.html` returns 0 matches
- `grep "20 verified claims" index.html` returns 2 matches (mega-overlay + agent bar)
- `grep "AGENT-DRIFT-01" index.html` includes mobile menu and terminal canonical_state
- `grep "MVP v0.7" index.html` returns 0 matches
</verification>

<success_criteria>
All 5 outdated references fixed. No "v0.7" or "15 verified claims" remain. Branch pushed.
</success_criteria>

<output>
After completion, create `.planning/quick/260330-vis-fix-5-outdated-places-in-index-html-for-/260330-vis-SUMMARY.md`
</output>
