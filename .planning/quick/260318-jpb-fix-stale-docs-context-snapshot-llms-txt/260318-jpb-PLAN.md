---
phase: quick
plan: 260318-jpb
type: execute
wave: 1
depends_on: []
files_modified:
  - CONTEXT_SNAPSHOT.md
  - llms.txt
  - README.md
  - AGENTS.md
autonomous: true
requirements: [STALE-DOCS]

must_haves:
  truths:
    - "All 4 files show 8 innovations (not 7)"
    - "CONTEXT_SNAPSHOT.md and llms.txt show date 2026-03-18"
    - "CERT-11 and CERT-12 appear in adversarial sections of CONTEXT_SNAPSHOT.md, llms.txt, and README.md"
    - "AGENTS.md architecture paragraph mentions all 5 verification layers"
    - "llms.txt deep_verify shows 13-test (not 10-test)"
    - "agent_learn.py observe reports clean state"
  artifacts:
    - path: "CONTEXT_SNAPSHOT.md"
      provides: "Updated snapshot with 8 innovations, 2026-03-18 date, CERT-11/12"
    - path: "llms.txt"
      provides: "Updated LLM summary with 8 innovations, 2026-03-18 date, 13-test deep_verify, CERT-11/12"
    - path: "README.md"
      provides: "Updated README with 8 innovations, CERT-11/12 in adversarial section"
    - path: "AGENTS.md"
      provides: "Architecture paragraph mentioning all 5 layers"
  key_links: []
---

<objective>
Fix 4 stale documentation files to reflect current v0.5.0 state: 8 innovations (adding Temporal Commitment as 8th), current date, CERT-11/CERT-12 adversarial tests, 13-test deep_verify, and 5-layer architecture in AGENTS.md.

Purpose: Documentation consistency across all AI context files after v0.5.0 release.
Output: 4 updated files passing stale-docs check.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CONTEXT_SNAPSHOT.md
@llms.txt
@README.md
@AGENTS.md
@CLAUDE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix CONTEXT_SNAPSHOT.md and llms.txt</name>
  <files>CONTEXT_SNAPSHOT.md, llms.txt</files>
  <action>
Use the Edit tool for precise string replacements in each file.

**CONTEXT_SNAPSHOT.md — 6 edits:**

1. Line 5: `> Updated: 2026-03-17` → `> Updated: 2026-03-18`

2. Line 30: `| Innovations | 7 (5 PPA + bundle signing + temporal commitment) |` → `| Innovations | 8 (5 PPA + HMAC signing + Ed25519 signing + temporal commitment) |`

3. Line 33: `| Adversarial tests | CERT-05 (5 attacks) + CERT-06 (5 scenarios) |` → `| Adversarial tests | CERT-05 (5 attacks) + CERT-06 (5 scenarios) + CERT-07 (signing) + CERT-08 (reproducibility) + CERT-09 (Ed25519 attacks) + CERT-10 (temporal attacks) + CERT-11 (coordinated multi-vector) + CERT-12 (encoding attacks) |`

4. Line 78: `## 7 innovations` → `## 8 innovations`
   Then add innovation #8 after line 86 (after the Temporal Commitment line 7):
   ```
   8. **5-Layer Independence (CERT-11 coordinated + CERT-12 encoding)** → test_cert11 + test_cert12 [proves each layer catches attacks others miss]
   ```

5. Line 141: `- scripts/deep_verify.py — 10-test proof-not-trust verification script` → `- scripts/deep_verify.py — 13-test proof-not-trust verification script`

6. Line 157: `*Updated: 2026-03-17 | Next update: first response or first client*` → `*Updated: 2026-03-18 | Next update: first response or first client*`

**llms.txt — 5 edits:**

1. Line 88: `## 7 innovations (USPTO PPA #63/996,819)` → `## 8 innovations (USPTO PPA #63/996,819)`

2. After line 96 (Temporal Commitment innovation #7), add:
   ```
   8. 5-Layer Independence (CERT-11 + CERT-12) → test_cert11 (coordinated multi-vector) + test_cert12 (encoding attacks)  [proves each layer catches attacks others miss]
   ```

3. Line 104: `## Current state (2026-03-15)` → `## Current state (2026-03-18)`

4. Line 141: `- scripts/deep_verify.py — 10-test proof-not-trust verification script` → `- scripts/deep_verify.py — 13-test proof-not-trust verification script`

5. After the adversarial test commands block (around line 99-101), there is no explicit adversarial section in llms.txt. The CERT references are inline in innovations section (lines 91-96). The added innovation #8 covers CERT-11/CERT-12. No additional adversarial section edit needed.

IMPORTANT: The 8th innovation is the formalization of 5-layer independence proved by CERT-11 (coordinated multi-vector attacks proving each layer catches what others miss) and CERT-12 (encoding attacks like BOM, null bytes, homoglyphs, truncated JSON). This is distinct from innovation #7 (Temporal Commitment) which is a single layer capability.
  </action>
  <verify>
    <automated>grep -n "8 innovations" CONTEXT_SNAPSHOT.md llms.txt && grep -n "2026-03-18" CONTEXT_SNAPSHOT.md llms.txt && grep -n "CERT-11" CONTEXT_SNAPSHOT.md llms.txt && grep -n "13-test" CONTEXT_SNAPSHOT.md llms.txt</automated>
  </verify>
  <done>Both files show 8 innovations, date 2026-03-18, CERT-11/CERT-12 references, and 13-test deep_verify</done>
</task>

<task type="auto">
  <name>Task 2: Fix README.md and AGENTS.md</name>
  <files>README.md, AGENTS.md</files>
  <action>
Use the Edit tool for precise string replacements.

**README.md — 3 edits:**

1. Line 179: `## 7 innovations (USPTO PPA #63/996,819)` → `## 8 innovations (USPTO PPA #63/996,819)`

2. After line 225 (innovation #7 Temporal Commitment block ending with test references), add innovation #8:
   ```markdown
   ### 8 — 5-Layer Independence Proof (CERT-11 + CERT-12)
   Formal proof that all five verification layers are independently necessary. CERT-11 constructs coordinated multi-vector attacks; CERT-12 tests encoding edge cases (BOM injection, null bytes, homoglyphs, truncated JSON). Each layer catches attacks the other four miss.
   ```
   followed by:
   ```
   Evidence: tests/steward/test_cert11_* + tests/steward/test_cert12_*
   Proof:    test_cert_5layer_independence
   ```

3. After the CERT-05 adversarial table (line 130, after `| Anchor Chain Reversal |...`), add rows for CERT-11 and CERT-12:
   After the existing table, add a new section:
   ```markdown

   **Coordinated Multi-Vector Attacks — 5-layer independence proven (CERT-11):**
   Each verification layer catches attacks that the other four miss. Proves all five layers are independently necessary.
   ```bash
   python -m pytest tests/steward/test_cert11_coordinated_multi_vector.py -v
   ```

   **Encoding Attack Resistance (CERT-12):**
   BOM injection, null bytes, homoglyph claim IDs, truncated JSON — all caught.
   ```bash
   python -m pytest tests/steward/test_cert12_encoding_attacks.py -v
   ```
   ```

4. Line 137: `The summary test explicitly proves all three layers are necessary — no single layer catches all attacks.` → `The summary test explicitly proves all five layers are necessary — no single layer catches all attacks.`

**AGENTS.md — 1 edit:**

Lines 153-157: The architecture paragraph currently only lists 3 layers in the verification flow:
```
→ mg.py verify runs five independent layers:
  Layer 1: SHA-256 integrity (file modification)
  Layer 2: semantic (job_snapshot present, canary_mode correct, payload.kind matches)
  Layer 3: step chain (trace_root_hash == final execution step hash)
→ PASS or FAIL with specific layer and reason.
```

Replace lines 153-157 with:
```
→ mg.py verify runs five independent layers:
  Layer 1: SHA-256 integrity (file modification)
  Layer 2: semantic (job_snapshot present, canary_mode correct, payload.kind matches)
  Layer 3: step chain (trace_root_hash == final execution step hash)
  Layer 4: bundle signing (HMAC-SHA256 or Ed25519 signature verification)
  Layer 5: temporal commitment (NIST Beacon pre-commitment proves WHEN signed)
→ PASS or FAIL with specific layer and reason.
```

This adds the missing Layer 4 and Layer 5 lines to match the actual 5-layer architecture.
  </action>
  <verify>
    <automated>grep -n "8 innovations" README.md && grep -n "CERT-11" README.md && grep -n "Layer 4" AGENTS.md && grep -n "Layer 5" AGENTS.md</automated>
  </verify>
  <done>README.md shows 8 innovations with CERT-11/CERT-12, AGENTS.md architecture paragraph lists all 5 layers</done>
</task>

<task type="auto">
  <name>Task 3: Verify clean state with agent_learn.py</name>
  <files></files>
  <action>
Run the stale docs verification command to confirm all files are now current:

```bash
PYTHONIOENCODING=utf-8 python scripts/agent_learn.py observe
```

If any files still show as stale, fix them using Edit tool.

Also run:
```bash
python scripts/check_stale_docs.py
```

Both commands must report clean/current state.
  </action>
  <verify>
    <automated>PYTHONIOENCODING=utf-8 python scripts/agent_learn.py observe 2>&1 | head -20 && python scripts/check_stale_docs.py 2>&1 | head -10</automated>
  </verify>
  <done>agent_learn.py observe and check_stale_docs.py both report no stale files</done>
</task>

</tasks>

<verification>
- All 4 files updated with correct values
- Innovation count is 8 everywhere (not 7)
- CERT-11 and CERT-12 mentioned in adversarial sections
- AGENTS.md architecture paragraph lists all 5 layers
- agent_learn.py observe reports clean state
</verification>

<success_criteria>
- `grep -c "8 innovations" CONTEXT_SNAPSHOT.md llms.txt README.md` returns 1 for each file
- `grep -c "CERT-11" CONTEXT_SNAPSHOT.md llms.txt README.md` returns >= 1 for each file
- `grep -c "Layer 5" AGENTS.md` returns >= 1
- `PYTHONIOENCODING=utf-8 python scripts/agent_learn.py observe` reports clean state
- `python scripts/check_stale_docs.py` reports all documentation is current
</success_criteria>

<output>
After completion, create `.planning/quick/260318-jpb-fix-stale-docs-context-snapshot-llms-txt/260318-jpb-SUMMARY.md`
</output>
