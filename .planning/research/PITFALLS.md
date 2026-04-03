# Pitfalls Research

**Domain:** Test coverage hardening for cryptographic verification protocol (adding ~60 adversarial/structural tests to existing 391-test suite)
**Researched:** 2026-03-17
**Confidence:** HIGH (derived from direct codebase analysis of existing test patterns, known bugs in CLAUDE.md, and established testing anti-patterns)

## Critical Pitfalls

### Pitfall 1: Shared Mutable State Between Adversarial Tests via Module-Level Imports

**What goes wrong:**
Tests that import claim modules at class level (e.g., `TestStepChainMTR1` line 65: `from backend.progress.mtr1_calibration import run_calibration as _run`) share the imported module object across all tests in the class. If any claim module caches results, uses module-level mutable state, or modifies `sys.path` as a side-effect, one test's mutations leak into the next. This is especially dangerous for coordinated attack tests (CERT-11) where multiple claims run in sequence -- a corrupted module-level variable from one attack scenario silently poisons the next scenario, producing false passes.

The existing codebase has a concrete manifestation: `runner.py` line 19 contains `sys.path.insert(0, '/app')` at module top level. Every test that imports from `runner.py` (directly or transitively) gets this path mutation. If a test also inserts a different path, the import resolution order changes unpredictably between test runs depending on collection order.

**Why it happens:**
Python's module system is global and cached. `import backend.progress.mtr1_calibration` executes the module once and caches it in `sys.modules`. Class-level imports (outside `def`) execute at class definition time, not at test time. Developers assume each test method gets a fresh environment, but they share `sys.modules`, `sys.path`, and any module-level variables.

**How to avoid:**
- Import inside test methods (the existing codebase already does this for some tests, e.g., `test_mtr1_trace_changes_with_seed` imports inside the method). Make this the universal pattern for all new tests.
- For CERT-11 coordinated attack tests, ensure each attack scenario builds its own evidence pack from scratch using `tmp_path` (pytest provides a unique `tmp_path` per test). Never share `pack_dir` between test methods.
- Never store results from one attack scenario as class attributes (`self.result_from_attack1`). Each test must be independently runnable via `pytest tests/steward/test_cert11.py::TestCERT11::test_attack_3 -v`.
- Add a `conftest.py` to `tests/` with `@pytest.fixture(autouse=True)` that resets any known mutable module state if any is discovered. Currently there is no `conftest.py` at all.

**Warning signs:**
- Tests that pass individually (`pytest test_cert11.py::test_attack1`) but fail when run as a class (`pytest test_cert11.py`)
- Tests that pass in isolation but fail when the full suite runs (order-dependent)
- Class-level attributes storing results from `setUp` or earlier tests
- `pytest --randomly-seed=X` producing different results than default collection order

**Phase to address:**
Phase 1 (structural step chain tests) and Phase 2 (CERT-11 coordinated attack). Establish the isolation pattern in Phase 1 so Phase 2 inherits it.

---

### Pitfall 2: False Positives in Coordinated Attack Tests -- Asserting Detection Without Verifying the Detection Mechanism

**What goes wrong:**
A coordinated attack test (CERT-11) chains multiple attacks: modify evidence, rebuild hashes, forge signature. The test asserts `verify returns FAIL`. But the test passes for the WRONG REASON -- Layer 1 catches the hash mismatch (trivial) before Layer 2 or Layer 3 ever runs. The test claims to prove "all layers are necessary" but actually only exercises Layer 1. This is exactly the pattern CERT-05's Attack 1 was designed to prevent: it uses `_verify_semantic` directly to bypass Layer 1.

The existing codebase has a second false-positive vector: `_verify_semantic` returns `(ok, msg, errors)` where `msg` is a string. Tests assert `ok is False` but do not check WHICH layer detected the attack. Example from `test_cert05` line 256: `assert "Step Chain" in msg or "trace_root_hash" in msg`. If the assertion is only `ok is False`, a coordinated attack test proves nothing about layer independence.

**Why it happens:**
It is satisfying to see `FAIL` and move on. Verifying that the CORRECT layer caught the attack requires understanding the verification pipeline deeply and writing assertions that inspect the error message or error list. For coordinated attacks that should trigger multiple layers simultaneously, the test must either (a) test each layer independently or (b) parse the multi-layer error report to confirm all expected layers fired.

**How to avoid:**
- For every attack in CERT-11, document explicitly WHICH layer(s) should detect it. Follow CERT-05's comment pattern: `# Layer 2 (semantic): FAIL -- job_snapshot missing regardless of hashes`.
- Assert on the detection mechanism, not just the detection result. Check `msg` or `errors` for layer-specific keywords (`"semantic"`, `"Step Chain"`, `"trace_root_hash"`, `"integrity"`, `"signature"`).
- For the coordinated attack specifically: the test should prove that disabling any single layer still results in detection by the remaining layers. This means running the attack through each layer independently (the way CERT-05 uses `_verify_semantic` directly) and through the full pipeline.
- Never write `assert ok is False` without a follow-up assertion on `msg` or `errors`.

**Warning signs:**
- Test passes but the attack description says "Layer 3 catches this" while `msg` says "integrity mismatch" (Layer 1)
- `assert ok is False` with no follow-up assertion on the error message
- Coordinated attack test with only one assertion
- Tests that pass even when the "attack" code is commented out (the pack was invalid from the start)

**Phase to address:**
Phase 2 (CERT-11 coordinated attack). The attack enumeration and expected-detection-layer mapping should be documented before any test code is written.

---

### Pitfall 3: Windows CRLF Silently Breaking SHA-256 Hash Comparisons in New Tests

**What goes wrong:**
On Windows, `Path.write_text(data)` without specifying `newline=""` will convert `\n` to `\r\n`. If a test writes JSON evidence to a file and then reads it back for hashing, the hash will differ from what the production code computes (which uses `canonicalize_bytes` to normalize CRLF to LF). This is documented in CLAUDE.md as BUG 2: `hashlib.sha256(file.read_bytes()).hexdigest()` is wrong; `fingerprint_file` is correct.

The existing test suite has an inconsistency that reveals this risk: some `write_text` calls specify `encoding="utf-8"` (e.g., `test_cert05` lines 117-118) while others do not (e.g., `test_cert05` line 286: `index_path.write_text(json.dumps(ev_index))`). On Windows, `write_text()` without `encoding` uses the system default encoding (cp1252 or utf-8 depending on Python version and Windows locale). More critically, `write_text()` on Windows opens the file in text mode, converting `\n` to `\r\n`.

The codebase has NO `.gitattributes` file. This means Git's `core.autocrlf` setting (which defaults to `true` on Windows) controls line endings. Fixture files checked out on Windows may have CRLF, while the same files on Linux have LF. Any test that computes a hash over a fixture file without using `canonicalize_bytes` will produce different results across platforms.

**Why it happens:**
Developers on Windows see tests pass locally (consistent CRLF everywhere). CI runs on Linux (consistent LF everywhere). Both pass. But if a test computes a hash over `file.read_bytes()` instead of `canonicalize_bytes(file.read_bytes())`, and the fixture file has CRLF on Windows but LF on Linux, the hashes diverge silently. The test "works" on both platforms but produces different hash values -- a latent bug that surfaces when cross-platform bundle verification is tested.

**How to avoid:**
- Add a `.gitattributes` file to the repo root: `* text=auto eol=lf`. This forces LF line endings on all platforms for text files, eliminating the CRLF/LF divergence at the source.
- In ALL new test code that writes files: use `write_text(data, encoding="utf-8", newline="\n")` (Python 3.10+) or `write_bytes(data.encode("utf-8"))` to bypass text-mode CRLF conversion.
- In ALL new test code that reads files for hashing: use `canonicalize_bytes(path.read_bytes())` from `backend.progress.data_integrity`, not raw `read_bytes()`.
- For encoding attack tests (P5/CERT-12): explicitly test BOM injection (`\xef\xbb\xbf` prefix), mixed line endings (`\r\n` in some lines, `\n` in others), and null bytes within JSON values. These are the actual attack vectors against the canonicalization layer.
- Create a shared test helper (in a new `tests/conftest.py` or `tests/helpers.py`) that wraps file writing with consistent encoding/newline handling.

**Warning signs:**
- Tests that pass on Windows but fail in Linux CI (or vice versa)
- Hash values in test assertions that are 64-character hex strings computed locally -- these will be platform-specific unless canonicalization was used
- `write_text()` calls without `encoding="utf-8"` anywhere in new test code
- `read_bytes()` followed by `hashlib.sha256()` without `canonicalize_bytes()` in between
- No `.gitattributes` file in the repo (currently the case)

**Phase to address:**
Phase 0 (before any test code is written). Add `.gitattributes` and the shared test helper. This is a prerequisite for all subsequent phases because it affects every test that touches files.

---

### Pitfall 4: Governance Meta-Tests with Hardcoded Counts That Break on Every Update

**What goes wrong:**
The P10 gap calls for "governance meta-tests" that detect documentation drift (e.g., "claim count in index.html matches actual claim count"). The naive implementation hardcodes the expected count: `assert count_in_index_html == 14`. When v0.6.0 adds claim 15, this test fails -- not because anything is wrong, but because the hardcoded expectation is stale. The test becomes a maintenance burden rather than a safety net.

The codebase already has this problem: `test_cert08_reproducibility.py` line 37 says "All 7 properties hold for all 14 claims" and line 82 says "Determinism holds across ALL 14 claims simultaneously." These are docstrings (not assertions), but if a governance meta-test asserts `len(claims) == 14`, it inherits the same brittleness.

The steward_audit.py approach is instructive: it does NOT hardcode counts. It extracts claim IDs from `canonical_state.md` and `scientific_claim_index.md` and checks that the two sets are EQUAL. This is the correct pattern -- it detects drift without embedding a specific count.

**Why it happens:**
Hardcoded assertions are the easiest to write and the most obvious to verify during review. `assert count == 14` reads clearly. The relational approach (`assert set_A == set_B`) requires more code and more thought about what "correct" means. Developers default to the easy path, especially under time pressure to close 10 gaps.

**How to avoid:**
- Governance meta-tests should assert CONSISTENCY, not specific values. Examples:
  - "The claim count in index.html matches the claim count in scientific_claim_index.md" (relational)
  - "Every claim in runner.py dispatch has a test file in tests/" (coverage)
  - "Every CERT-XX file referenced in CLAUDE.md exists and contains at least one test class" (structural)
- Use `steward_audit.py` as the reference pattern: extract from source A, extract from source B, compare.
- If a specific count MUST appear (e.g., "test suite has >= 450 tests"), use `>=` not `==`. The count should only go up.
- Store expected values in `system_manifest.json` (which is already the canonical source for counters) and have the meta-test read from there, not from inline constants.
- Never hardcode hash values in tests unless the test is specifically about hash stability (like `test_ed25519.py` line 83 which pins a known test vector).

**Warning signs:**
- `assert ... == 14` or `assert ... == 391` or any literal integer count in governance tests
- Tests that fail on main branch after a legitimate PR merge (not because of a bug, but because a counter changed)
- Meta-tests that must be updated every time a new claim or test file is added
- No reference to `system_manifest.json` or `canonical_state.md` in governance test code

**Phase to address:**
Phase 4 (P10 governance meta-tests). Design the relational assertion pattern before writing any governance test code.

---

### Pitfall 5: Test Fixture Changes That Silently Break Cross-Test Assumptions

**What goes wrong:**
The `_make_minimal_pack` helper in `test_cert05` (lines 77-148) builds a minimal evidence pack used by 5 attack scenarios. If a new CERT test (CERT-11, CERT-12) copies and modifies this helper -- adding a field, changing a default, restructuring the evidence directory -- and the original CERT-05 tests still import from their own copy, the two helpers diverge. Now CERT-05 tests a slightly different pack format than CERT-11, and neither tests the ACTUAL format that `mg.py verify` expects.

A more insidious variant: a "shared" helper in a common location is updated for CERT-11 requirements, and the change subtly breaks CERT-05 (e.g., adding a new required field that CERT-05's attack scenarios do not account for). The 391 existing tests break not because of a code bug but because a test fixture changed.

**Why it happens:**
DRY (Don't Repeat Yourself) pushes developers to extract shared helpers. But shared test helpers create coupling between test files that should be independent. A change to help CERT-11 breaks CERT-05. The alternative (duplicating helpers) creates divergence. Neither is ideal.

**How to avoid:**
- Create a `tests/helpers/pack_builder.py` module with a VERSIONED pack builder. The builder should have a `version` parameter that controls which fields are included, so CERT-05 can use `version="v1"` (original 3-layer format) and CERT-11 can use `version="v2"` (5-layer format with temporal + Ed25519).
- Never modify the existing `_make_minimal_pack` in `test_cert05`. That test is proven and documented. Copy the helper to the shared location, mark the original as "frozen" with a comment.
- When adding new required fields to the pack builder (e.g., `temporal_commitment`), make them OPTIONAL with defaults that match the existing behavior. This ensures old tests keep working unchanged.
- Run the full test suite after ANY helper modification, not just the tests that use the new helper.
- Each test file should document which pack format version it expects: `# Pack format: v1 (3-layer, no temporal, no Ed25519)`.

**Warning signs:**
- Multiple copies of `_make_minimal_pack` with slight differences across test files
- A test file importing helpers from another test file (e.g., `from tests.steward.test_cert05 import _make_minimal_pack`)
- Helper function with 10+ parameters (sign of accumulated complexity)
- Tests that fail after a "refactoring" of test helpers

**Phase to address:**
Phase 1 (first phase that adds new tests). Extract shared helpers before writing new tests, not after.

---

### Pitfall 6: Encoding Attack Tests (CERT-12) That Only Test What canonicalize_bytes Already Handles

**What goes wrong:**
The partial corruption / encoding attack tests (P5) should prove that the verification pipeline rejects malicious encoding tricks. But if all tests use attacks that `canonicalize_bytes` already normalizes (CRLF injection, missing trailing newline), the tests prove the canonicalization works -- not that the verification pipeline catches encoding attacks. The real attacks that matter are:
1. BOM injection (`\xef\xbb\xbf`) in JSON files -- `json.loads` ignores it on some Python versions, but the SHA-256 changes
2. Unicode normalization attacks -- NFC vs NFD encoding of the same character produces different bytes
3. Null byte injection in file paths -- `evidence/claim\x00/evil/run_artifact.json` can bypass path validation on some OS
4. Mixed encoding within a single file -- UTF-8 header with Latin-1 body
5. Overlong UTF-8 sequences -- `\xc0\xaf` as an encoding of `/` can bypass path filters

The `canonicalize_bytes` function (data_integrity.py lines 15-21) handles CRLF/CR normalization and trailing newline, but does NOT handle BOM stripping, Unicode normalization, null bytes, or overlong sequences. Tests that only throw CRLF variations at it are testing an already-solved problem.

**Why it happens:**
CRLF is the most visible encoding difference (especially on Windows) and the most commonly discussed. Developers test what they know. BOM, NFC/NFD, and overlong UTF-8 are specialist attacks that require understanding of Unicode encoding internals.

**How to avoid:**
- Enumerate the encoding attack surface BEFORE writing tests:
  - BOM in JSON evidence files: Does `json.loads` produce the same dict? Does the SHA-256 change?
  - Unicode normalization: Write a claim ID with an accented character in NFC and NFD. Does `_verify_semantic` treat them as the same claim?
  - Null bytes in file paths: Does `evidence_index.json` with a null-byte path cause `Path.open()` to fail safely or traverse?
  - Partial file truncation: JSON file cut mid-string. Does `json.loads` raise? Does the test verify it raises?
- For each attack, the test should have TWO parts: (1) the attack input, (2) the specific verification layer that catches it and HOW.
- Use `canonicalize_bytes` as a baseline and then test what it does NOT cover. The function's limitations are the encoding attack surface.

**Warning signs:**
- All encoding tests use `\r\n` variations only
- No test for BOM (`\xef\xbb\xbf`) handling
- No test for truncated/malformed JSON
- Tests that pass because `json.loads` silently succeeds rather than because the verification pipeline explicitly rejects

**Phase to address:**
Phase 3 (P5 encoding attack tests / CERT-12). The attack enumeration should list the specific encoding vectors above.

---

### Pitfall 7: Step Chain Structural Tests That Are Identical Copies With Different Claim Names

**What goes wrong:**
P1 requires step chain structural tests for 7 missing claims (ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01, and one more). The existing pattern in `test_step_chain_all_claims.py` has 4 tests per claim: trace_present, trace_four_steps, trace_deterministic, trace_changes_with_input. Copying this pattern 7 times adds 28 tests but proves nothing new -- if one claim's step chain works, they all work (the `_hash_step` function is identical across all claims).

The real value is testing claim-SPECIFIC behavior: Does PHARMA-01's step chain include the correct property_name? Does FINRISK-01's threshold_check include the VaR confidence level? Does DT-CALIB-LOOP-01's chain correctly reference DRIFT-01's anchor hash? Identical structural tests miss all of this.

**Why it happens:**
Copy-paste is the fastest way to close a gap count. "7 claims x 4 tests = 28 tests" looks like progress. But if all 28 tests are the same test with different imports, the marginal value of test 5-28 is approximately zero.

**How to avoid:**
- Use pytest parametrize to generate the common structural tests from a list of (claim_module, run_function, kwargs) tuples. This avoids copy-paste while still covering all 14 claims. One parametrized test class replaces 14 x 4 = 56 individual tests.
- For each claim, add ONE unique test that verifies claim-specific step chain content:
  - ML_BENCH-02: `_trace[0]["name"] == "init_params"` AND `result["inputs"]["claimed_rmse"]` appears in step chain data
  - PHARMA-01: Step chain includes `property_name` and `compound_id`
  - DT-CALIB-LOOP-01: Step chain includes `anchor_hash` referencing DRIFT-01
- The unique tests are where the real coverage gaps are. The structural tests are table stakes.

**Warning signs:**
- New test file with 28 methods that are textually identical except for the import line
- No claim-specific assertions beyond "trace has 4 steps and deterministic"
- PR diff showing 300+ added lines that are 90% identical

**Phase to address:**
Phase 1 (P1 step chain structural tests). The parametrize-plus-unique-per-claim pattern should be the design, not an afterthought.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Copy-pasting `_make_minimal_pack` into each new CERT file | Test is self-contained, no cross-file deps | 5 copies of the same 70-line function, divergence inevitable | Only for CERT-05 (already frozen); all new tests should use shared builder |
| Hardcoding `== 14` in governance tests | Quick to write, obvious to review | Breaks every time a claim is added | Never -- use relational assertions |
| Skipping `encoding="utf-8"` on `write_text()` | Fewer characters to type | Platform-dependent encoding, silent hash mismatches | Never in test code that produces files for hashing |
| Using `subprocess.run` to invoke `mg.py` in tests | Tests the full CLI path | Slow (Python interpreter startup per test), environment leaks, cwd-dependent | Only for true CLI integration tests (CERT-01); prefer direct function imports for unit/attack tests |
| No `conftest.py` for shared fixtures | Each test file is independent | Repeated boilerplate (sys.path manipulation, pack builder, encoding helpers) | Acceptable until test count exceeds ~40 files; at 45+ files (current state), extract shared setup |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| `_verify_semantic` from `mg.py` | Calling it with `pack_dir` that has backslashes on Windows (Path object works, string with `\` may not) | Always pass `Path` objects, never `str`. The function reads `evidence_index.json` using `Path` internally. |
| `runner.py` imports | Test imports `runner.py` which has `sys.path.insert(0, '/app')` at module level -- on Windows this adds a nonexistent path to sys.path | Harmless but noisy. Do not import runner.py directly in tests unless testing runner dispatch. Import the claim modules directly. |
| Existing test path pattern | Each test file uses `_ROOT = Path(__file__).resolve().parent.parent.parent` -- fragile if test directory nesting changes | Acceptable for now, but a shared `conftest.py` with a `repo_root` fixture would be more robust. |
| `json.dumps` with `write_text` | Writing `json.dumps(data)` with `write_text()` -- Windows adds `\r\n` for any `\n` in the JSON string values | Use `write_bytes(json.dumps(data).encode("utf-8"))` or `write_text(data, encoding="utf-8", newline="\n")` |
| `tmp_path` on Windows | `tmp_path` returns a Windows path (`C:\Users\...\AppData\Local\Temp\pytest-xxx`). If evidence_index.json contains paths with backslashes, `_verify_semantic` may fail to resolve them. | Always use `.as_posix()` or forward-slash strings for paths inside JSON evidence structures. |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Test that "proves" Layer 3 catches an attack but actually Layer 1 caught it first | False confidence in layer independence -- the independence thesis (JOSS paper core claim) is unproven | Every attack test must document which layer catches it and assert on the layer-specific error message |
| Encoding attack test that only tests canonicalization, not the hash chain | False confidence in encoding attack resistance -- canonicalization is one defense, hash binding is another | Test encoding attacks at BOTH the file level (canonicalization) and the hash chain level (does the hash change?) |
| Governance test with hardcoded claim count | Silent drift when claims are added/removed -- the governance test becomes a barrier to legitimate changes rather than a safety net | Use relational assertions (set equality, >= thresholds) not absolute values |

## "Looks Done But Isn't" Checklist

- [ ] **Step chain tests (P1):** Often missing claim-specific assertions -- verify each claim has at least one test that checks claim-specific data in the step chain (not just "4 steps, deterministic")
- [ ] **CERT-11 coordinated attack:** Often missing layer attribution -- verify each attack scenario asserts WHICH layer detected it, not just that detection occurred
- [ ] **Encoding tests (P5/CERT-12):** Often missing BOM and Unicode normalization vectors -- verify test includes `\xef\xbb\xbf`, NFC/NFD, and truncated JSON, not just CRLF
- [ ] **Cross-claim cascade (P3+P8):** Often missing the reverse direction -- verify that corrupting a DOWNSTREAM claim does NOT affect UPSTREAM verification (independence)
- [ ] **Runner error paths (P7):** Often missing the "no payload" case -- verify runner handles `payload=None`, `payload={}`, and `payload={"kind": "nonexistent"}` distinctly
- [ ] **Governance meta-tests (P10):** Often hardcoding counts -- verify no literal integers for claim count, test count, or layer count in assertions
- [ ] **Test isolation:** Often sharing state via module imports -- verify every test method can run independently via `pytest path::class::method`
- [ ] **Windows compatibility:** Often missing `encoding="utf-8"` on file operations -- verify every `write_text()` and `read_text()` in new test code specifies encoding

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Shared state between adversarial tests | LOW | Move imports inside methods, use `tmp_path` per test, run `pytest --randomly` to detect order-dependence |
| False positive in coordinated attack | MEDIUM | Add `msg` assertions to each existing `assert ok is False`, re-examine WHICH layer actually fires |
| CRLF hash mismatch on Windows | LOW | Add `.gitattributes` with `* text=auto eol=lf`, recheck all `write_text()` calls for encoding parameter |
| Hardcoded governance counts break | LOW | Replace `== N` with relational assertions (`set_A == set_B`, `>= N`), read expected values from `system_manifest.json` |
| Fixture change breaks existing tests | MEDIUM | Freeze existing helpers (copy, don't modify), create versioned shared builder, run full suite after any helper change |
| Encoding tests only cover CRLF | LOW | Add BOM, NFC/NFD, null byte, and truncated JSON test vectors to CERT-12 |
| Copy-paste structural tests | LOW | Refactor to parametrized tests, add per-claim unique assertions |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Shared mutable state (P1) | Phase 0 (infrastructure: conftest.py, shared helpers) | `pytest --randomly-seed=12345` produces same results as default order |
| False positives in attacks (P2) | Phase 2 (CERT-11 design, before coding) | Every `assert ok is False` has a follow-up `assert "expected_keyword" in msg` |
| CRLF/encoding (P3) | Phase 0 (add .gitattributes, encoding helper) | `pytest tests/ -q` passes on both Windows and Linux CI |
| Hardcoded governance counts (P4) | Phase 4 (P10 governance meta-test design) | `grep -rn "== 14\|== 391\|== 450" tests/` returns zero results (no hardcoded counts) |
| Fixture divergence (P5) | Phase 0 (extract shared pack builder before new tests) | Single `tests/helpers/pack_builder.py` imported by all CERT tests |
| Encoding tests too narrow (P6) | Phase 3 (CERT-12 attack enumeration) | CERT-12 test file docstring lists >= 5 distinct encoding attack vectors |
| Copy-paste structural tests (P7) | Phase 1 (P1 parametrize design) | `test_step_chain_all_claims.py` uses `@pytest.mark.parametrize` for common assertions |

## Sources

- Codebase analysis: `tests/steward/test_cert05_adversarial_gauntlet.py` -- attack pattern reference, `_make_minimal_pack` helper (lines 77-148)
- Codebase analysis: `tests/steward/test_step_chain_all_claims.py` -- existing structural test pattern, class-level imports (line 65)
- Codebase analysis: `backend/progress/data_integrity.py` -- `canonicalize_bytes` limitations (handles CRLF, does NOT handle BOM/NFC/NFD)
- Codebase analysis: `backend/progress/runner.py` -- `sys.path.insert(0, '/app')` module-level side-effect (line 19)
- Codebase analysis: `scripts/steward_audit.py` -- relational assertion pattern for governance (set equality, not hardcoded counts)
- CLAUDE.md BUG 2: SHA-256 mismatch on Windows due to CRLF -- confirms the CRLF hash issue is known and documented
- CLAUDE.md BUG 7: index.html has 11 counter locations -- confirms counter synchronization complexity
- No `.gitattributes` file exists in the repo (verified via filesystem check) -- confirms the CRLF risk is unmitigated
- No `tests/conftest.py` exists (verified via grep) -- confirms no shared fixtures infrastructure
- Inconsistent `write_text()` encoding usage across test files (some with `encoding="utf-8"`, some without) -- verified via grep

**Confidence notes:**
- Test isolation pitfalls: HIGH confidence (directly observed module-level import patterns and `sys.path` mutations in codebase)
- False positive risk in attack tests: HIGH confidence (directly observed assertion patterns in CERT-05, extrapolated to CERT-11)
- Windows CRLF issues: HIGH confidence (no `.gitattributes`, inconsistent encoding params, CLAUDE.md explicitly documents BUG 2)
- Governance count brittleness: HIGH confidence (steward_audit.py demonstrates the correct pattern; absence of it in tests confirms the risk)
- Encoding attack surface: MEDIUM confidence (canonicalize_bytes limitations directly observed; BOM/NFC/NFD attack relevance based on established encoding attack patterns, not codebase-specific evidence)

---
*Pitfalls research for: MetaGenesis Core test coverage hardening v0.5.0*
*Researched: 2026-03-17*
