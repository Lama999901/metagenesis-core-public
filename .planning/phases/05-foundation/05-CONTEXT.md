# Phase 5: Foundation - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Step chain structural tests for all 14 claims (closing P1 gap), step chain ordering invariants (P4), runner error path tests (P7), and governance meta-tests for documentation drift detection (P10). Tests only — no production code changes unless strictly required for testability.

</domain>

<decisions>
## Implementation Decisions

### Step Chain Structural Tests (P1)
- All 14 claims get 6-test pattern: trace_present, trace_four_steps, trace_deterministic, trace_changes_with_input, **genesis_hash_derivation**, **inter_step_hash_linkage**
- Backfill the existing 7 claims (MTR-1/2/3, SYSID-01, DATAPIPE-01, DRIFT-01, DT-FEM-01) with genesis+linkage checks for uniform 14/14 coverage
- New claims to add: ML_BENCH-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01
- All tests go in `tests/steward/test_step_chain_all_claims.py` following existing TestStepChain* class pattern

### Step Chain Ordering Invariants (P4)
- Extend `tests/steward/test_cert03_step_chain_verify.py` in-place (not a new file)
- Add 3-4 tests to existing TestStepChainVerification class: wrong step order (1,3,2,4), duplicate step numbers, extra steps beyond 4
- Reuses existing `_make_pack()` + `_verify_semantic()` pipeline

### Runner Error Paths (P7)
- Test through ProgressRunner dispatch: unknown JOB_KIND, None payload, missing 'kind' key, mid-computation exception
- Also test `_hash_step` helper with non-serializable inputs (datetime, set, circular ref) for defense-in-depth
- New file: `tests/steward/test_runner_error_paths.py`

### Governance Meta-Tests (P10)
- Full counter audit: test counts, layer counts, innovation counts, claim counts across index.html, README.md, AGENTS.md, llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md
- Dual authority: runner.py `registered` list is ground truth for which claims exist; system_manifest.json is ground truth for counters. Verify they agree, then check docs match.
- Cross-reference scientific_claim_index.md claim IDs against backend/progress/*.py JOB_KIND constants (set equality)
- Cross-reference known_faults.yaml entries against current code state
- Use relational assertions (set equality, `>=` thresholds), NEVER hardcoded counts
- New file: `tests/steward/test_stew08_documentation_drift.py`

### Claude's Discretion
- Exact parametrize structure for the 6-test-per-claim pattern
- How to import `_hash_step` for testing (it's a module-level function in each claim file)
- Which specific known_faults.yaml entries to validate (parse dynamically)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Step Chain Tests
- `tests/steward/test_step_chain_all_claims.py` -- Existing 7-claim pattern with `_assert_trace_valid()` helper
- `tests/steward/test_cert03_step_chain_verify.py` -- `_make_pack()` + `_verify_semantic()` for ordering tests

### Runner Implementation
- `backend/progress/runner.py` -- `_execute_job_logic()` dispatch, `registered` list (line 410-418)

### Governance Sources
- `reports/scientific_claim_index.md` -- Claim registry (cross-reference target)
- `reports/known_faults.yaml` -- Known limitations (accuracy check target)
- `system_manifest.json` -- Machine-readable counters (authoritative for counts)
- `tests/steward/test_stew07_jobkind_coverage.py` -- Existing governance pattern to follow
- `tests/steward/test_stew06_canonical_truth_consistency.py` -- Existing canonical state audit pattern

### Gap Analysis
- `.planning/quick/260317-q97-analyze-all-389-tests-across-the-full-te/TEST_GAP_REPORT.md` -- P1, P4, P7, P10 gap definitions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_assert_trace_valid()` in test_step_chain_all_claims.py: validates trace structure, can be extended for genesis+linkage
- `_make_pack()` in test_cert03: builds minimal fake pack directory for _verify_semantic() testing
- `_get_trace_root()` in test_step_chain_all_claims.py: extracts trace_root_hash from result dict
- Existing TestStepChain* classes: template for all 7 new + 7 backfill claim classes

### Established Patterns
- 4-test-per-claim class: test_trace_present, test_trace_four_steps, test_trace_deterministic, test_trace_changes_with_input
- Each claim imported directly: `from backend.progress.mtr1_calibration import run_calibration`
- Alphabetical test prefixes within files for ordering
- No conftest.py fixtures — module-level helpers only

### Integration Points
- Each new TestStepChain* class imports its claim's run function directly
- CERT-03 ordering tests use _verify_semantic from scripts/mg.py
- Governance tests parse files from repo root using Path(__file__).resolve()

</code_context>

<specifics>
## Specific Ideas

- Genesis hash check: verify step 1 hash is derived from `_hash_step("init_params", {...}, "genesis")` — the literal string "genesis" as prev_hash
- Inter-step linkage: verify each step N's prev_hash equals step N-1's hash
- Governance tests should be self-maintaining: when a new claim is added, the test automatically detects the mismatch without needing manual update

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-foundation*
*Context gathered: 2026-03-17*
