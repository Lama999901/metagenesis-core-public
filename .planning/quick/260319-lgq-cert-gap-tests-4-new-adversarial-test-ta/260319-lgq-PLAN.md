---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - AGENT_TASKS.md
  - scripts/agent_research.py
  - tests/steward/test_cert_adv_sysid01_semantic.py
  - tests/steward/test_cert_adv_multichain.py
  - tests/steward/test_cert_adv_sign_integrity.py
  - tests/steward/test_cert_adv_temporal_pure.py
  - reports/AGENT_REPORT_20260319.md
autonomous: true
requirements: [CERT-GAP-011, CERT-GAP-012, CERT-GAP-013, CERT-GAP-014]
must_haves:
  truths:
    - "TASK-011 through TASK-014 exist in AGENT_TASKS.md with DONE status"
    - "execute_task_011 through execute_task_014 exist in agent_research.py dispatch"
    - "4 new test files exist in tests/steward/ and pass pytest"
    - "All changes committed to feat/cert-gap-tests branch and pushed"
  artifacts:
    - path: "AGENT_TASKS.md"
      provides: "4 new task entries (011-014)"
      contains: "TASK-014"
    - path: "scripts/agent_research.py"
      provides: "4 new handler functions"
      contains: "execute_task_014"
    - path: "tests/steward/test_cert_adv_sysid01_semantic.py"
      provides: "Layer 2 semantic stripping for SYSID-01"
    - path: "tests/steward/test_cert_adv_multichain.py"
      provides: "Layer 3 + Layer 5 multi-vector attack"
    - path: "tests/steward/test_cert_adv_sign_integrity.py"
      provides: "Layer 1 + Layer 4 file mod + wrong key"
    - path: "tests/steward/test_cert_adv_temporal_pure.py"
      provides: "Layer 5 isolation pure temporal attacks"
  key_links:
    - from: "scripts/agent_research.py"
      to: "AGENT_TASKS.md"
      via: "parse_tasks() reads task entries, dispatch calls handler"
    - from: "execute_task_011"
      to: "tests/steward/test_cert_adv_sysid01_semantic.py"
      via: "handler reads CERT-02 + sysid1 source as templates, writes test file"
---

<objective>
Add 4 new CERT gap adversarial test tasks (TASK-011 through TASK-014) to the agent research system, implement handlers that generate real test files by reading existing CERT tests as templates, execute all 4 tasks, then commit and push to feat/cert-gap-tests.

Purpose: Close the adversarial test gaps identified by TASK-010 cross-layer attack surface analysis. Each test targets a specific layer combination gap.
Output: 4 new test files in tests/steward/, updated AGENT_TASKS.md, updated agent_research.py, all on feat/cert-gap-tests branch.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@AGENT_TASKS.md
@scripts/agent_research.py

Key existing patterns to follow:
- Handler functions return markdown string (report content)
- Each handler reads real repo files (Path reads, not subprocess) for template/analysis
- Handlers use REPO_ROOT / "path" pattern for file access
- Test files follow _ROOT = Path(__file__).resolve().parent.parent.parent pattern
- Test files import from scripts.mg, scripts.mg_sign, scripts.mg_temporal, scripts.mg_ed25519
- Use _make_sem_pack() helper pattern from test_cert02 for building synthetic packs
- Use _hash_step() helper from test_cert11 for step chain construction

Key template files for handlers to read:
- tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py (Layer 2 template, has _make_sem_pack)
- tests/steward/test_cert10_temporal_attacks.py (Layer 5 template, 5 attack scenarios)
- tests/steward/test_cert11_coordinated_attack.py (multi-vector template, has _hash_step helper)
- tests/steward/test_cert09_ed25519_attacks.py (signing attacks template)
- backend/progress/sysid1_arx_calibration.py (SYSID-01 claim for semantic test)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add TASK-011 to TASK-014 entries + implement all 4 handlers</name>
  <files>AGENT_TASKS.md, scripts/agent_research.py</files>
  <action>
**Step 1: Append 4 new task entries to AGENT_TASKS.md** after TASK-010:

```
### TASK-011
- **Title:** Write adversarial test: SYSID-01 Layer 2 semantic stripping
- **Status:** PENDING
- **Priority:** P1
- **Output:** tests/steward/test_cert_adv_sysid01_semantic.py
- **Description:** Generate test file that builds a SYSID-01 pack using _make_sem_pack pattern, then strips required semantic fields (mtr_phase, execution_trace, inputs, result) one at a time. Each test asserts _verify_semantic() returns FAIL. Read sysid1_arx_calibration.py for exact field names and test_cert02 for _make_sem_pack pattern.

### TASK-012
- **Title:** Write adversarial test: Layer 3 + Layer 5 multi-vector attack
- **Status:** PENDING
- **Priority:** P1
- **Output:** tests/steward/test_cert_adv_multichain.py
- **Description:** Generate test file combining step chain tamper (Layer 3) with temporal replay (Layer 5). Scenario: attacker modifies execution_trace hashes AND replays old temporal_commitment.json. Prove both layers catch independently. Read test_cert11 for multi-vector pattern and test_cert10 for temporal helpers.

### TASK-013
- **Title:** Write adversarial test: Layer 1 + Layer 4 file mod + wrong key signing
- **Status:** PENDING
- **Priority:** P2
- **Output:** tests/steward/test_cert_adv_sign_integrity.py
- **Description:** Generate test file: (1) modify evidence file content, update SHA-256 in manifest (Layer 1 bypass), then verify Layer 4 catches because signature no longer matches. (2) Re-sign with wrong key, verify signature check fails. Read test_cert09 for Ed25519 patterns and test_cert07 for signing patterns.

### TASK-014
- **Title:** Write adversarial test: Layer 5 pure temporal isolation
- **Status:** PENDING
- **Priority:** P2
- **Output:** tests/steward/test_cert_adv_temporal_pure.py
- **Description:** Generate test file with 4 pure temporal attacks that do NOT involve other layers: (1) truncated beacon value, (2) empty timestamp string, (3) swapped pre_commitment fields between two bundles, (4) temporal_commitment.json with valid structure but all-zero hashes. Read test_cert10 for temporal API usage.
```

**Step 2: Add handlers to scripts/agent_research.py**

Add `"TASK-011": execute_task_011, "TASK-012": execute_task_012, "TASK-013": execute_task_013, "TASK-014": execute_task_014` to the `handlers` dict in `execute_task()`.

**Step 3: Implement execute_task_011()**

Handler must:
1. Read `backend/progress/sysid1_arx_calibration.py` to extract JOB_KIND, field names, threshold
2. Read `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` to get the _make_sem_pack pattern
3. Generate `tests/steward/test_cert_adv_sysid01_semantic.py` with these tests:
   - `test_sysid01_strip_mtr_phase`: Set mtr_phase=None, assert _verify_semantic fails
   - `test_sysid01_strip_execution_trace`: Remove execution_trace but keep trace_root_hash, assert fails
   - `test_sysid01_strip_inputs`: Remove inputs dict, assert fails
   - `test_sysid01_strip_result`: Remove result dict, assert fails
   - `test_sysid01_empty_job_kind`: Set job_kind="" in evidence_index, assert fails
4. Test file must use _make_sem_pack pattern adapted for SYSID-01 (claim_id="SYSID-01", job_kind="sysid1_arx_calibration", appropriate result fields)
5. Write test file to disk using Path.write_text()
6. Return markdown report with source analysis + generated test summary

**Step 4: Implement execute_task_012()**

Handler must:
1. Read `tests/steward/test_cert11_coordinated_attack.py` for _hash_step helper and multi-vector pattern
2. Read `tests/steward/test_cert10_temporal_attacks.py` for temporal API imports
3. Generate `tests/steward/test_cert_adv_multichain.py` with:
   - Helper: `_build_valid_pack_with_temporal(tmp_path)` that creates a signed+temporal-committed pack
   - `test_multichain_tamper_trace_and_replay_temporal`: Modify step chain hash in evidence, copy temporal from different pack, verify BOTH Layer 3 and Layer 5 catch independently
   - `test_multichain_tamper_trace_only`: Tamper step chain only, temporal valid -> Layer 3 catches
   - `test_multichain_replay_temporal_only`: Valid step chain, replayed temporal -> Layer 5 catches
4. Uses imports: `from scripts.mg import _verify_pack, _verify_semantic`, `from scripts.mg_temporal import create_temporal_commitment, verify_temporal_commitment, write_temporal_commitment, TEMPORAL_FILE`
5. Write test file to disk, return report

**Step 5: Implement execute_task_013()**

Handler must:
1. Read `tests/steward/test_cert09_ed25519_attacks.py` for Ed25519 patterns
2. Read `tests/steward/test_cert07_bundle_signing.py` for sign/verify patterns
3. Generate `tests/steward/test_cert_adv_sign_integrity.py` with:
   - `test_modify_evidence_bypass_l1_caught_by_l4`: Modify evidence content, update manifest SHA-256 + root_hash (bypasses L1), assert signature verification fails (L4 catches)
   - `test_resign_with_wrong_key`: Sign valid bundle, then re-sign with different key, verify with original pubkey fails
   - `test_unsigned_bundle_after_content_mod`: Modify content + update manifest, no signature -> L4 check shows unsigned
4. Uses: `from scripts.mg_sign import sign_bundle, verify_bundle_signature, SIGNATURE_FILE`, `from scripts.mg_ed25519 import generate_key_files`
5. Write test file to disk, return report

**Step 6: Implement execute_task_014()**

Handler must:
1. Read `tests/steward/test_cert10_temporal_attacks.py` for temporal API
2. Generate `tests/steward/test_cert_adv_temporal_pure.py` with:
   - `test_temporal_truncated_beacon_value`: Create commitment with truncated beacon_output_value, verify fails
   - `test_temporal_empty_timestamp`: Create commitment with beacon_timestamp="", verify fails
   - `test_temporal_swapped_precommitment`: Create two commitments for different root_hashes, swap pre_commitment_hash between them, verify both fail
   - `test_temporal_allzero_hashes`: Create temporal_commitment.json with all fields set to "0"*64, verify fails
3. Uses: `from scripts.mg_temporal import create_temporal_commitment, verify_temporal_commitment, write_temporal_commitment, TEMPORAL_FILE`
4. Write test file to disk, return report

**IMPORTANT for all handlers:**
- Each handler MUST write the actual test .py file to disk (not just report about it)
- Use `(REPO_ROOT / "tests/steward/<filename>").write_text(test_code, encoding="utf-8")`
- Test files must have proper `#!/usr/bin/env python3` header, docstring, imports, _ROOT setup
- Test files must use `import pytest` and follow existing naming patterns
- Do NOT use `any` types; use proper field names from source claim files
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && grep -c "TASK-014" AGENT_TASKS.md && python -c "import scripts.agent_research as ar; assert 'TASK-014' in ar.execute_task.__code__.co_consts or hasattr(ar, 'execute_task_014')"</automated>
  </verify>
  <done>AGENT_TASKS.md has 4 new PENDING entries (TASK-011 to TASK-014). agent_research.py has 4 new handler functions registered in dispatch dict. Each handler reads real template files and writes actual test code to tests/steward/.</done>
</task>

<task type="auto">
  <name>Task 2: Execute all 4 tasks, run tests, branch, commit, push</name>
  <files>
    AGENT_TASKS.md,
    tests/steward/test_cert_adv_sysid01_semantic.py,
    tests/steward/test_cert_adv_multichain.py,
    tests/steward/test_cert_adv_sign_integrity.py,
    tests/steward/test_cert_adv_temporal_pure.py,
    reports/AGENT_REPORT_20260319.md
  </files>
  <action>
**Step 1: Run agent_research.py 4 times** to execute TASK-011, TASK-012, TASK-013, TASK-014 sequentially:
```bash
cd C:/Users/999ye/Downloads/metagenesis-core-public
python scripts/agent_research.py   # executes TASK-011
python scripts/agent_research.py   # executes TASK-012
python scripts/agent_research.py   # executes TASK-013
python scripts/agent_research.py   # executes TASK-014
```

After each run, verify:
- Output says "Executing TASK-0XX" and "TASK_DONE"
- The corresponding test file was written to tests/steward/

**Step 2: Verify all 4 test files exist:**
```bash
ls -la tests/steward/test_cert_adv_sysid01_semantic.py
ls -la tests/steward/test_cert_adv_multichain.py
ls -la tests/steward/test_cert_adv_sign_integrity.py
ls -la tests/steward/test_cert_adv_temporal_pure.py
```

**Step 3: Run pytest on the new test files** to verify they pass:
```bash
python -m pytest tests/steward/test_cert_adv_sysid01_semantic.py -v --timeout=60
python -m pytest tests/steward/test_cert_adv_multichain.py -v --timeout=60
python -m pytest tests/steward/test_cert_adv_sign_integrity.py -v --timeout=60
python -m pytest tests/steward/test_cert_adv_temporal_pure.py -v --timeout=60
```

If any test fails, read the test file, diagnose the failure, fix the test code directly (not via re-running the handler), and re-run pytest until it passes.

**Step 4: Verify AGENT_TASKS.md shows all 4 tasks as DONE**

**Step 5: Create branch, commit, push:**
```bash
git checkout -b feat/cert-gap-tests
git add AGENT_TASKS.md scripts/agent_research.py tests/steward/test_cert_adv_*.py reports/AGENT_REPORT_*.md
git commit -m "feat: add 4 CERT gap adversarial tests (TASK-011 to TASK-014)

- TASK-011: Layer 2 semantic stripping for SYSID-01
- TASK-012: Layer 3 + Layer 5 multi-vector attack
- TASK-013: Layer 1 + Layer 4 file mod + wrong key signing
- TASK-014: Layer 5 isolation pure temporal attacks

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push origin feat/cert-gap-tests
```

**IMPORTANT:** If any test file has issues after handler execution, fix the test file directly rather than modifying the handler and re-running. The goal is working tests on the branch.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -m pytest tests/steward/test_cert_adv_sysid01_semantic.py tests/steward/test_cert_adv_multichain.py tests/steward/test_cert_adv_sign_integrity.py tests/steward/test_cert_adv_temporal_pure.py -v && git log --oneline -1 | grep "cert-gap"</automated>
  </verify>
  <done>All 4 test files pass pytest. AGENT_TASKS.md shows TASK-011 through TASK-014 as DONE. Everything committed to feat/cert-gap-tests branch and pushed to origin.</done>
</task>

</tasks>

<verification>
1. `grep "TASK-014" AGENT_TASKS.md` returns a match with DONE status
2. `python -m pytest tests/steward/test_cert_adv_*.py -v` -- all tests pass
3. `git branch --show-current` returns `feat/cert-gap-tests`
4. `git log --oneline -3` shows the commit with cert-gap in message
5. `python scripts/steward_audit.py` still passes (STEWARD AUDIT: PASS)
</verification>

<success_criteria>
- 4 new adversarial test files exist in tests/steward/ and pass pytest
- AGENT_TASKS.md has TASK-011 through TASK-014 all marked DONE
- agent_research.py has 14 handlers (10 original + 4 new) in dispatch
- All changes on feat/cert-gap-tests branch, committed and pushed
- Existing test suite not broken (steward audit still passes)
</success_criteria>

<output>
After completion, create `.planning/quick/260319-lgq-cert-gap-tests-4-new-adversarial-test-ta/260319-lgq-SUMMARY.md`
</output>
