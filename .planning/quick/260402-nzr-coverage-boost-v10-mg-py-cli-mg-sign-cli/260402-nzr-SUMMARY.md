---
phase: quick
plan: 260402-nzr
subsystem: tests
tags: [coverage, mg-cli, mg-sign-cli, ledger-models, agent-main]
key-files:
  created:
    - tests/scripts/test_mg_cli_extended.py
    - tests/scripts/test_mg_sign_cli_extended.py
    - tests/backend/test_ledger_models_extended.py
    - tests/scripts/test_agent_main_functions.py
  modified:
    - system_manifest.json
    - scripts/check_stale_docs.py
    - CLAUDE.md
    - AGENTS.md
    - README.md
    - index.html
    - llms.txt
    - CONTEXT_SNAPSHOT.md
    - paper.md
    - ppa/README_PPA.md
    - docs/ARCHITECTURE.md
    - docs/ROADMAP.md
    - CONTRIBUTING.md
    - CITATION.cff
    - CURSOR_MASTER_PROMPT_v2_3.md
    - docs/HOW_TO_ADD_CLAIM.md
    - docs/REAL_DATA_GUIDE.md
    - docs/USE_CASES.md
    - reports/scientific_claim_index.md
    - reports/known_faults.yaml
decisions:
  - Temporal functions in mg_sign.py are imported locally inside cmd functions, so tests mock via sys.modules dict patching
  - Agent scripts replace sys.stdout at import time, breaking capsys; tests verify return codes instead of captured output
metrics:
  duration: ~8min
  completed: 2026-04-01
  tests_before: 1198
  tests_after: 1273
  tests_added: 75
---

# Quick Task 260402-nzr: Coverage Boost v10 Summary

75 new tests targeting mg.py CLI wrappers, mg_sign.py CLI commands, ledger models from_dict/to_dict, and agent main() entry points across 6 scripts. Test count 1198 to 1273. All counter files and check_stale_docs.py rules updated.

## Tasks Completed

### Task 1: Write 75 new test files (4 files)

| File | Tests | Target |
|------|-------|--------|
| tests/scripts/test_mg_cli_extended.py | 25 | mg.py CLI: cmd_pack_verify, cmd_verify_chain, cmd_bench_run, cmd_claim_run_mtr1, main() |
| tests/scripts/test_mg_sign_cli_extended.py | 15 | mg_sign.py CLI: cmd_keygen, cmd_sign, cmd_verify, cmd_temporal, main() |
| tests/backend/test_ledger_models_extended.py | 15 | ledger/models.py: from_dict, to_dict, ArtifactReference edge cases |
| tests/scripts/test_agent_main_functions.py | 20 | main() in agent_chronicle, agent_signals, agent_diff_review, agent_audit, steward_dossier, agent_evolution |

**Commit:** 8fbc73a

### Task 2: Update counters 1198 to 1273

Updated 20 files: system_manifest.json, 18 documentation files, and check_stale_docs.py (required strings updated, 1198 added to banned lists).

**Commit:** eb7e4a8

## Verification

- `python -m pytest tests/ -q --tb=no` -- 1273 passed, 2 skipped
- `python scripts/check_stale_docs.py` -- All critical documentation is current
- `python scripts/steward_audit.py` -- PASS
- `python scripts/deep_verify.py` -- ALL 13 TESTS PASSED

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed temporal function mocking in mg_sign CLI tests**
- **Found during:** Task 1
- **Issue:** mg_sign.py imports `create_temporal_commitment`, `write_temporal_commitment`, and `verify_temporal_commitment` locally inside cmd functions via `from scripts.mg_temporal import ...`, so `patch("mg_sign.func")` fails with AttributeError
- **Fix:** Used `patch.dict("sys.modules", {"scripts.mg_temporal": MagicMock(...)})` to mock the module before the local import executes
- **Files modified:** tests/scripts/test_mg_sign_cli_extended.py

**2. [Rule 3 - Blocking] Agent scripts break capsys by replacing sys.stdout**
- **Found during:** Task 1
- **Issue:** Agent scripts (chronicle, signals, diff_review, etc.) replace `sys.stdout` with `io.TextIOWrapper` at import time, which prevents pytest capsys from capturing output
- **Fix:** Changed tests to verify return codes instead of captured output text
- **Files modified:** tests/scripts/test_agent_main_functions.py

## Known Stubs

None.

## Self-Check: PASSED
