---
phase: quick
plan: 260320-icp
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/test_coverage_boost.py
autonomous: true
requirements: [COVERAGE-BOOST]

must_haves:
  truths:
    - "12 new tests pass covering mg_sign.py and mg_ed25519.py"
    - "Tests use only pytest tmp_path fixture and stdlib"
    - "No existing tests break"
  artifacts:
    - path: "tests/test_coverage_boost.py"
      provides: "12 coverage-boost tests across 3 groups"
      min_lines: 80
  key_links:
    - from: "tests/test_coverage_boost.py"
      to: "scripts/mg_sign.py"
      via: "direct import"
      pattern: "from scripts.mg_sign import"
    - from: "tests/test_coverage_boost.py"
      to: "scripts/mg_ed25519.py"
      via: "direct import"
      pattern: "from scripts.mg_ed25519 import"
---

<objective>
Create tests/test_coverage_boost.py with 12 tests across 3 groups covering mg_sign.py and mg_ed25519.py functions. Commit to feat/coverage-65 and push.

Purpose: Boost test coverage for signing modules (Layer 4 + Ed25519).
Output: tests/test_coverage_boost.py with 12 passing tests.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/mg_sign.py
@scripts/mg_ed25519.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create tests/test_coverage_boost.py with 12 tests and push to feat/coverage-65</name>
  <files>tests/test_coverage_boost.py</files>
  <action>
Create tests/test_coverage_boost.py with 3 test groups (12 tests total). All tests use pytest tmp_path fixture where filesystem is needed.

**Imports needed:**
```python
import argparse
import json
import pytest
from pathlib import Path
from scripts.mg_sign import generate_key, sign_bundle, load_key, _compute_signature, cmd_keygen
from scripts.mg_ed25519 import run_self_test, generate_keypair, sign, verify, generate_key_files
```

**GROUP 1 -- mg_sign.py (5 tests):**

1. `test_generate_key`: Call `generate_key()`. Assert result is dict with keys "version", "key_hex", "fingerprint". Assert `len(result["key_hex"]) == 64` (32 bytes hex-encoded).

2. `test_sign_bundle_creates_signature(tmp_path)`: Create `pack_manifest.json` in tmp_path with `{"root_hash": "a" * 64}`. Generate key via `generate_key()`, write to `tmp_path / "key.json"`. Call `sign_bundle(tmp_path, tmp_path / "key.json")`. Assert `(tmp_path / "bundle_signature.json").exists()`.

3. `test_sign_bundle_missing_manifest_raises(tmp_path)`: Call `sign_bundle(tmp_path, tmp_path / "key.json")` on empty tmp_path. Assert raises `FileNotFoundError`.

4. `test_load_key(tmp_path)`: Generate key via `generate_key()`, write JSON to `tmp_path / "key.json"`. Call `load_key(tmp_path / "key.json")`. Assert result is dict containing "key_hex".

5. `test_compute_signature`: Generate key via `generate_key()`. Call `_compute_signature("a" * 64, key["key_hex"])`. Assert result is non-empty string.

**GROUP 2 -- mg_ed25519.py (5 tests):**

6. `test_run_self_test`: Call `run_self_test()`. Assert returns `True`.

7. `test_generate_keypair`: Call `generate_keypair()`. Assert returns tuple of length 2.

8. `test_sign_verify_roundtrip`: Call `generate_keypair()` to get (seed, pub). Call `sign(seed, b"test")` to get sig. Call `verify(pub, b"test", sig)`. Assert returns `True`.

9. `test_verify_wrong_message_fails`: Generate keypair. Sign `b"correct"`. Verify with `b"wrong"`. Assert returns `False`.

10. `test_generate_key_files(tmp_path)`: Call `generate_key_files(tmp_path / "key.json")`. Assert `(tmp_path / "key.json").exists()` and `(tmp_path / "key.pub.json").exists()`.

**GROUP 3 -- mg_sign.py cmd_ functions (2 tests):**

11. `test_cmd_keygen_hmac(tmp_path)`: Create `argparse.Namespace(out=str(tmp_path / "key.json"), type="hmac")`. Call `cmd_keygen(args)`. Assert `(tmp_path / "key.json").exists()`.

12. `test_cmd_keygen_ed25519(tmp_path)`: Create `argparse.Namespace(out=str(tmp_path / "key.json"), type="ed25519")`. Call `cmd_keygen(args)`. Assert `(tmp_path / "key.json").exists()`.

**After writing the file:**
1. Run `python -m pytest tests/test_coverage_boost.py -v` to confirm all 12 pass.
2. Create branch `feat/coverage-65` if not exists: `git checkout -b feat/coverage-65` (or `git switch -c feat/coverage-65`).
3. `git add tests/test_coverage_boost.py`
4. Commit: `git commit -m "test: add 12 coverage-boost tests for mg_sign.py and mg_ed25519.py"`
5. Push: `git push -u origin feat/coverage-65`
  </action>
  <verify>
    <automated>python -m pytest tests/test_coverage_boost.py -v</automated>
  </verify>
  <done>12 tests pass, committed and pushed to feat/coverage-65</done>
</task>

</tasks>

<verification>
python -m pytest tests/test_coverage_boost.py -v  -- 12 passed
git log --oneline -1  -- shows coverage boost commit
git branch --show-current  -- feat/coverage-65
</verification>

<success_criteria>
- tests/test_coverage_boost.py exists with 12 tests across 3 groups
- All 12 tests pass
- Committed and pushed to feat/coverage-65 branch
- No existing tests broken
</success_criteria>

<output>
After completion, create `.planning/quick/260320-icp-coverage-boost-tests-for-mg-sign-py-and-/260320-icp-SUMMARY.md`
</output>
