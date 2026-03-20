# Agent Research Report -- TASK-015: Boost coverage to 60% -- identify top uncovered functions, write test code

**Date:** 2026-03-19 18:59
**Task Description:** Read reports/COVERAGE_REPORT_20260319.md, identify the top uncovered functions in mg_sign.py and mg_temporal.py (both are core verification scripts with low coverage), and generate actual pytest test code targeting cmd_keygen, cmd_sign, cmd_verify, cmd_temporal, verify_bundle_signature in mg_sign.py plus create_temporal_commitment, verify_temporal_commitment in mg_temporal.py.
**Priority:** P1

---

## TASK-015: Boost Coverage to 60%

Date: 2026-03-19 18:59

### Coverage Report Analysis

- Read `reports/COVERAGE_REPORT_20260319.md`
- Overall coverage: 39.7%
- Target: 60%

### Top Uncovered Functions

**mg_sign.py** (46.8% coverage):
  - `_detect_algorithm`
  - `generate_key`
  - `load_key`
  - `_compute_signature`
  - `_compute_ed25519_signature`
  - `sign_bundle`
  - `verify_bundle_signature`
  - `cmd_keygen`
  - `cmd_sign`
  - `cmd_temporal`
  - `cmd_verify`
  - `main`

**mg_temporal.py** functions:
  - `_fetch_beacon_pulse`
  - `create_temporal_commitment`
  - `verify_temporal_commitment`
  - `write_temporal_commitment`

### Generated Test: tests/steward/test_mg_sign_coverage.py

- **Path:** `tests\steward\test_mg_sign_coverage.py`
- **Tests:** 11 test functions across 5 classes
- **Targets:** generate_key, _detect_algorithm, _compute_signature, load_key, sign_bundle, verify_bundle_signature

### Generated Test: tests/steward/test_mg_temporal_coverage.py

- **Path:** `tests\steward\test_mg_temporal_coverage.py`
- **Tests:** 10 test functions across 3 classes
- **Targets:** create_temporal_commitment, verify_temporal_commitment, write_temporal_commitment

### Impact Estimate

- 21 new tests targeting 8 previously-uncovered functions
- Expected coverage boost: ~8-12 percentage points
- Primary files covered: mg_sign.py (46.8% -> ~70%), mg_temporal.py (unknown -> ~60%)
