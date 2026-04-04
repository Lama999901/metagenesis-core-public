---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [CLAUDE.md]
autonomous: true
requirements: [QUICK-01]

must_haves:
  truths:
    - "CLAUDE.md mentions CERT-11 (coordinated multi-vector attacks) and CERT-12 (encoding attacks)"
    - "WHAT'S NEXT section shows all phases 5-8 complete"
    - "ADVERSARIAL PROOF SUITE lists all 10 cert tests including cert11 and cert12"
  artifacts:
    - path: "CLAUDE.md"
      provides: "Updated project context for AI agents"
      contains: "CERT-11"
  key_links: []
---

<objective>
Update CLAUDE.md to reflect completed v0.5.0 milestone: add CERT-11/12 references, mark all phases complete in WHAT'S NEXT, and update the adversarial proof suite listing.

Purpose: CLAUDE.md is the primary context file for all GSD agents. It must accurately reflect the current state after completing all 8 phases of v0.5.0.
Output: Updated CLAUDE.md with CERT-11/12, completed phase status, and accurate proof suite.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@.planning/STATE.md

Key facts from project state:
- All 8 phases complete (9/9 plans, 100%)
- 511 tests passing, 14 claims, 5 layers, 8 innovations
- CERT-11: Coordinated Multi-Vector Attack Gauntlet (tests/steward/test_cert11_coordinated_attack.py)
- CERT-12: Encoding and Partial Corruption Attack Proofs (tests/steward/test_cert12_encoding_attacks.py)
- deep_verify.py has 13 tests (unchanged)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update CLAUDE.md with CERT-11/12 and completed milestone status</name>
  <files>CLAUDE.md</files>
  <action>
Make these specific edits to CLAUDE.md:

1. **PROJECT IDENTITY section (line 18):** Change:
   `**CERT-09:** Ed25519 attacks | **CERT-10:** temporal attacks | **deep_verify:** 13 tests`
   To:
   `**CERT-09:** Ed25519 attacks | **CERT-10:** temporal attacks | **CERT-11:** coordinated multi-vector | **CERT-12:** encoding attacks | **deep_verify:** 13 tests`

2. **ADVERSARIAL PROOF SUITE section (after test_cert08 line, around line 258):** Add two new entries:
   ```
   test_cert09 → Ed25519 signing attack proofs
   test_cert10 → Temporal commitment attack proofs
   test_cert11 → Coordinated multi-vector attack gauntlet
   test_cert12 → Encoding and partial corruption attacks
   ```
   Note: CERT-09 and CERT-10 are already referenced in PROJECT IDENTITY but missing from the ADVERSARIAL PROOF SUITE list. Add all four missing entries.

3. **WHAT'S NEXT section (line 282-283):** Change:
   ```
   1. v0.5.0 — Coverage Hardening (in progress)
      Phase 5 OK Phase 6 OK Phase 7 > Phase 8 pending
   ```
   To:
   ```
   1. v0.5.0 — Coverage Hardening (COMPLETE)
      Phase 5 OK Phase 6 OK Phase 7 OK Phase 8 OK
   ```
   (Use the same emoji checkmarks as the original: Phase 5-8 all get checkmarks)

4. **Version stamp (last line):** Change:
   `*CLAUDE.md v1.2 — 2026-03-18 — MetaGenesis Core v0.5.0*`
   To:
   `*CLAUDE.md v1.3 — 2026-03-17 — MetaGenesis Core v0.5.0 LIVE*`

Do NOT modify any sealed files. Do NOT use banned terms. This is CLAUDE.md itself so no sealed restriction applies to it.
  </action>
  <verify>
    <automated>grep -c "CERT-11" CLAUDE.md && grep -c "CERT-12" CLAUDE.md && grep -c "COMPLETE" CLAUDE.md && grep -c "test_cert11" CLAUDE.md && grep -c "test_cert12" CLAUDE.md</automated>
  </verify>
  <done>CLAUDE.md contains CERT-11 and CERT-12 in both PROJECT IDENTITY and ADVERSARIAL PROOF SUITE sections. WHAT'S NEXT shows v0.5.0 as COMPLETE with all phases checked. Version bumped to v1.3.</done>
</task>

</tasks>

<verification>
- `grep "CERT-11" CLAUDE.md` returns matches in PROJECT IDENTITY and ADVERSARIAL PROOF SUITE
- `grep "CERT-12" CLAUDE.md` returns matches in both sections
- `grep "test_cert09\|test_cert10\|test_cert11\|test_cert12" CLAUDE.md` returns 4 lines
- `grep "COMPLETE" CLAUDE.md` shows v0.5.0 marked complete
- `grep "v1.3" CLAUDE.md` shows updated version stamp
- python scripts/steward_audit.py passes (CLAUDE.md is not sealed)
</verification>

<success_criteria>
CLAUDE.md accurately reflects completed v0.5.0 milestone with all CERT tests (02-12) documented, all phases marked complete, and version stamp updated.
</success_criteria>

<output>
After completion, create `.planning/quick/260317-vsv-update-claude-md-v0-5-0-live-511-tests-5/260317-vsv-SUMMARY.md`
</output>
