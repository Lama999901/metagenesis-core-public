# Project Research Summary

**Project:** MetaGenesis Core v0.5.0 — Adversarial Test Coverage Hardening
**Domain:** Cryptographic verification protocol test suite expansion
**Researched:** 2026-03-17
**Confidence:** HIGH

## Executive Summary

MetaGenesis Core v0.5.0 is a tests-only milestone that closes 10 identified coverage gaps (P1-P10) in the existing 391-test adversarial suite for a 5-layer cryptographic verification protocol. The project adds approximately 60-77 new tests across structural, adversarial, semantic, cascade, and governance categories — all using stdlib-only tooling (pytest 8.4.1, Python 3.11) with zero new dependencies. The clear expert pattern, derived from direct codebase analysis of 48 existing test files, is a three-phase build order: foundation first (step chain structural + runner error paths), then layer hardening (semantic edge cases + cascade failures), then flagship adversarial proofs (CERT-11 coordinated attack + CERT-12 encoding attacks).

The recommended approach starts with Phase 0 infrastructure work (`.gitattributes` for CRLF normalization, shared pack builder extraction decision) before writing any new tests. This prevents the most critical pitfalls from propagating across all subsequent phases. The CERT-11 coordinated multi-vector attack gauntlet is the flagship deliverable and the most technically demanding item — it must prove the 5-layer independence thesis under simultaneous multi-layer attack, which is the central claim of the JOSS paper. All other phases build toward and support CERT-11.

The primary risks are: (1) false positives in coordinated attack tests where Layer 1 catches attacks that are intended to prove Layer 3 or Layer 4, (2) Windows CRLF hash mismatches from a missing `.gitattributes` and inconsistent `write_text` encoding parameters, and (3) governance meta-tests with hardcoded integer counts that become maintenance burdens. All three are preventable with specific, low-cost interventions before Phase 1 begins.

## Key Findings

### Recommended Stack

The entire v0.5.0 milestone uses the existing stack with no new dependencies. pytest 8.4.1 provides all required test infrastructure via `parametrize`, `tmp_path`, `pytest.param` with `id=`, class-based grouping, and `pytest.raises`. All encoding attack payloads, YAML/MD parsing for governance tests, and homoglyph generation are handled with Python 3.11 stdlib (`re`, `codecs`, `hashlib`, `pathlib`, `unittest.mock`).

**Core technologies:**
- **pytest 8.4.1**: Test framework — already pinned, all required features stable since pytest 6.x; `parametrize` for attack matrices, `tmp_path` for isolated bundle construction, `pytest.raises` for error path tests
- **Python 3.11 stdlib (`re`, `pathlib`, `hashlib`)**: Encoding attack generation and governance parsing — avoids PyYAML, hypothesis, and confusable-homoglyphs dependencies; `write_bytes()` is the correct primitive for raw encoding attack payloads
- **`unittest.mock`**: Mocking NIST Beacon in temporal attack tests — already used in `test_cert_5layer_independence.py`

No `conftest.py` currently exists in the test tree. Adding one changes pytest discovery behavior for all 391 existing tests and must be done with explicit intent, not as a convenience reflex. The project pattern is self-contained module-level helpers per CERT file.

### Expected Features

All 10 gaps are P1 priority for this milestone — there is no "nice to have" in a gap-closure release. Ordering within the milestone determines implementation sequence, not relative importance.

**Must have (table stakes — coverage completeness):**
- P1: Step chain structural tests for 7 missing claims (ML_BENCH-01/02/03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01) — 28 new tests following the exact 4-test-per-claim pattern plus one claim-specific assertion each
- P6: Layer 2 semantic edge case tests — Layer 2 is the weakest-tested layer (only 2 dedicated tests) despite being the primary defense against evidence stripping
- P7: Runner error path tests — zero coverage of unknown job kind, missing payload, and exception propagation in `_execute_job_logic`

**Should have (differentiators — JOSS paper support):**
- P2: CERT-11 coordinated multi-vector attack gauntlet — flagship proof that the independence thesis survives a sophisticated attacker targeting all 5 layers simultaneously
- P3+P8: Cross-claim cascade failure tests — extend existing MTR-1→DT-FEM-01→DRIFT-01 chain to include DRIFT-01→DT-CALIB-LOOP-01 and the full 4-claim cascade
- P5: CERT-12 encoding/partial corruption attacks — BOM injection, Unicode homoglyphs, null bytes, truncated JSON (these go beyond what `canonicalize_bytes` already handles)

**Defer (anti-features — explicitly out of scope):**
- Fuzz testing with Hypothesis — non-deterministic, adds dependency, attacks are finite and enumerable for this protocol
- Concurrent signing tests — single-user CLI tool, not a realistic attack vector
- Key lifecycle/expiry tests — key metadata has no expiry field yet (v0.6.0+)
- Exhaustive cross-claim permutation testing — test only documented dependency chains; 14! permutations is combinatorial explosion

### Architecture Approach

The test suite uses three core patterns consistently across all 48 existing files: (1) CERT-XX gauntlet (single class, named attack methods, direct `_verify_semantic` imports, composite summary test), (2) step chain structural tests (class-per-claim, 4 tests each, shared `_assert_trace_valid` helper), and (3) cross-claim chain tests (anchor_hash propagation, cascade invalidation). All new tests must extend or follow these patterns — deviation creates coupling and collection order dependencies.

**Major components and file targets:**
1. **`tests/steward/test_step_chain_all_claims.py` (extend)** — 7 new `TestStepChain*` classes for missing claims; use `parametrize` for the 4 structural assertions, add one claim-specific assertion per claim
2. **`tests/steward/test_cert11_coordinated_attack.py` (new)** — 5-6 attack scenarios each targeting 2+ layers simultaneously; each scenario asserts the specific catching layer via `msg` keyword checks
3. **`tests/steward/test_cert12_encoding_attacks.py` (new)** — parametrized encoding attack table (BOM, homoglyphs, null bytes, truncated JSON, NaN values); all payloads written with `write_bytes()`
4. **`tests/steward/test_cert02_semantic_edge_cases.py` (new)** — exercises `_verify_semantic()` edge cases not covered by existing 2 semantic tests
5. **`tests/steward/test_cross_claim_chain.py` (extend)** — new `TestCrossClaimCascadeFailure` and `TestDriftCalibChain` classes
6. **`tests/progress/test_runner_error_paths.py` (new)** — unit tests using `pytest.raises` against `runner.py._execute_job_logic()`
7. **`tests/steward/test_documentation_drift.py` (new)** — relational assertions (set equality, not hardcoded counts) across CLAUDE.md, index.html, README.md, system_manifest.json
8. **`tests/steward/_bundle_helpers.py` (new, conditional)** — extract shared bundle helpers only if 2+ new CERT files need the same builder; underscore prefix prevents pytest collection

**Critical path:** P1 (28 tests) → P3+P8 (8 tests) → P2 CERT-11 (6 tests). All other gaps can be parallelized within phases.

### Critical Pitfalls

1. **False positives in coordinated attack tests** — CERT-11 must assert WHICH layer caught the attack (`assert "Step Chain" in msg` or `assert "semantic" in msg`), not just that detection occurred (`assert ok is False`). Layer 1 trivially catches most attacks before Layer 2/3 ever runs; every CERT-11 scenario that intends to prove Layer 2/3 independence must call `_verify_semantic` directly to bypass Layer 1, following the CERT-05 pattern.

2. **Windows CRLF silently breaking SHA-256 comparisons** — no `.gitattributes` exists in the repo; `write_text()` without `newline="\n"` converts `\n` to `\r\n` on Windows; `canonicalize_bytes` handles CRLF normalization but only if actually called. Fix before writing any test code: add `.gitattributes` with `* text=auto eol=lf`, use `write_text(data, encoding="utf-8", newline="\n")` or `write_bytes(data.encode("utf-8"))` in all new test file-writing code.

3. **Governance meta-tests with hardcoded counts** — `assert claim_count == 14` breaks on every legitimate claim addition. Use relational assertions (`set_A == set_B`, `>= N`) and read expected values from `system_manifest.json`, following the `steward_audit.py` pattern of extracting from source A, extracting from source B, and comparing.

4. **Shared mutable state between adversarial tests** — class-level imports execute at class definition time and share `sys.modules`; `runner.py` has `sys.path.insert(0, '/app')` at module level as a side effect. All new tests must put imports inside test methods; use `tmp_path` (fresh per test) for all bundle construction; never store results as class attributes between test methods.

5. **Fixture divergence from helper duplication** — `_make_minimal_pack` in `test_cert05` is frozen and proven; never modify it. New CERT tests that need a bundle builder should either use a new `tests/steward/_bundle_helpers.py` module (if 2+ files need the same helper) or define their own minimal helpers. Cross-test-file imports (e.g., importing from `test_cert05`) create fragile collection-order coupling.

## Implications for Roadmap

Based on research, the dependency graph is fully defined and the phase structure is well-supported:

### Phase 0: Infrastructure Prerequisites
**Rationale:** Three pitfalls affect all subsequent phases if not fixed first — CRLF hash mismatches affect every test that writes files, shared pack builder coupling affects every new CERT test, and test isolation patterns affect every adversarial test. No production test code should be written before this phase completes.
**Delivers:** `.gitattributes` with `eol=lf`, extraction decision on `_bundle_helpers.py`, encoding conventions documented and enforced
**Addresses:** Pitfalls 1 (shared state), 2 (CRLF), 5 (fixture divergence)
**Estimated effort:** LOW — file additions only, no changes to production code or existing tests

### Phase 1: Foundation — Structural and Unit Tests
**Rationale:** P1 (step chain structural for 7 missing claims) is the dependency blocker for cascade tests (P3+P8) and CERT-11 (P2) — cascade tests cannot distinguish attack detection from pre-existing structural failures if any claim's step chain is unverified. P4, P7, and P10 are independent and can be built in parallel within this phase.
**Delivers:** ~46 new tests; full step chain coverage for all 14 claims; runner error path coverage; governance drift detection baseline
**Addresses:** P1 (28 tests), P4 step chain ordering (6 tests), P7 runner error paths (8 tests), P10 governance meta-tests (5 tests)
**Uses:** Existing 4-test-per-claim pattern from `test_step_chain_all_claims.py`; relational assertion pattern from `steward_audit.py`; `pytest.raises` for runner error paths
**Avoids:** Pitfall 7 (copy-paste structural tests) — use `parametrize` for the 4 structural assertions, add one unique claim-specific assertion per claim

### Phase 2: Layer Hardening — Semantic and Cascade
**Rationale:** Semantic edge cases (P6) must be characterized before CERT-12 encoding attacks (P5) to establish the clean-but-invalid baseline. Cross-claim cascade (P3+P8) depends on Phase 1 confirming all 14 claims produce structurally valid step chains. Manifest rollback (P9) is independent but logically belongs with this layer-focused phase.
**Delivers:** ~19 new tests; Layer 2 semantic coverage hardened; full cross-claim dependency chain tested including DRIFT-01→DT-CALIB-LOOP-01; manifest rollback documented
**Addresses:** P6 Layer 2 semantic edge cases (8 tests), P3+P8 cross-claim cascade (8 tests), P9 manifest rollback (3 tests)
**Implements:** `_verify_semantic` edge case surface (lines 149-269 of `mg.py`); anchor_hash cascade invalidation pattern
**Avoids:** Pitfall 6 (encoding tests too narrow) — this phase tests clean-but-invalid inputs, leaving CERT-12 to test the parser encoding boundary

### Phase 3: Flagship Adversarial Proofs — CERT-11 and CERT-12
**Rationale:** CERT-11 is the last item because it synthesizes all prior attack vectors and requires confidence in all individual layers to correctly attribute catching to the right layer. CERT-12 can be built alongside CERT-11 since encoding attacks are a distinct attack surface. Both are capstones for the JOSS paper.
**Delivers:** ~11 new tests; coordinated multi-vector attack independence proof; encoding attack resistance proof
**Addresses:** P2 CERT-11 coordinated attack (6 tests), P5 CERT-12 encoding attacks (5 tests)
**Uses:** `_make_full_5layer_bundle()` (from `test_cert_5layer_independence.py` or extracted `_bundle_helpers.py`); parametrized attack table with `pytest.param` `id=` for readable CI output; `write_bytes()` for all encoding payloads
**Avoids:** Pitfall 2 (false positives) — every CERT-11 attack scenario asserts the specific catching layer via message keyword checks, not just `ok is False`

### Phase Ordering Rationale

- Phase 0 before everything because CRLF issues and fixture coupling affect 100% of new test code.
- Phase 1 before Phase 2 because P3+P8 cascade tests require all 14 claims to have verified step chains — a corrupted step chain is indistinguishable from a detected attack.
- Phase 2 before Phase 3 because CERT-11 requires confidence that Layer 2 and Layer 3 are well-characterized independently; otherwise coordinated attack detection may be attributed to the wrong layer.
- P10 governance tests placed in Phase 1 so automated counter drift detection is active during Phase 2 and Phase 3 when counter updates are most likely.

### Research Flags

Phases with standard patterns (no additional research needed):
- **Phase 0:** Standard git configuration; module extraction is a refactoring decision, not a research question
- **Phase 1 (P1, P4, P7, P10):** All patterns directly observable in existing codebase; no ambiguity in approach
- **Phase 2 (P6, P9):** `_verify_semantic` edge case surface is directly inspectable; cross-claim anchor pattern is directly observable in `test_cross_claim_chain.py`

Phases needing design work before coding:
- **Phase 3 (P2 — CERT-11):** The attack scenario enumeration and per-scenario layer attribution table must be written as a design document before any test code. The false-positive pitfall is highest here. Each of the 5-6 attack scenarios must specify: what the attacker does, which layers they bypass, which layer catches them, and what keyword appears in the error message.
- **Phase 3 (P5 — CERT-12):** Verify the exact scope of `canonicalize_bytes` (handles CRLF/CR, does NOT handle BOM/NFC-NFD/null bytes) against the production implementation before finalizing the CERT-12 test vector list. The encoding attack surface beyond CRLF is partially inferred rather than directly tested.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Stdlib-only constraint eliminates all technology choices; every technique directly observed in 6+ existing test files |
| Features | HIGH | 10 gaps fully documented in PROJECT.md with clear scope boundaries; all priorities and dependencies confirmed by codebase analysis; no ambiguity |
| Architecture | HIGH | All 48 existing test files analyzed; three core patterns clearly identified; file targets and import dependencies fully mapped |
| Pitfalls | HIGH | 6 of 7 pitfalls derived from direct codebase evidence (missing `.gitattributes`, inconsistent `write_text` encoding, `sys.path` mutation in `runner.py`, no governance relational assertions); Pitfall 6 (encoding attack surface beyond CRLF) is MEDIUM confidence based on established security patterns |

**Overall confidence:** HIGH

### Gaps to Address

- **CERT-11 attack-to-layer attribution design:** The specific mapping of which layer catches which coordinated attack scenario is not yet resolved. The attack enumeration in FEATURES.md (attacks A-F) is a starting point, but exact assertions require `_verify_semantic` return value analysis before coding. Design this before Phase 3.
- **`_bundle_helpers.py` extraction decision gate:** Can only be resolved after Phase 1 implementation reveals whether CERT-11 actually needs `_make_full_5layer_bundle` as-is or needs a modified variant. Monitor during Phase 1 to avoid premature extraction.
- **CERT-12 BOM behavior:** Needs to be verified whether `_verify_semantic` sees the BOM-prefixed JSON (Layer 2 concern) or Layer 1 catches the SHA-256 hash change first (meaning CERT-12 would need to use `_verify_semantic` directly to test encoding resilience at Layer 2). Verify against actual `canonicalize_bytes` implementation before writing CERT-12 test vectors.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `tests/steward/test_cert05_adversarial_gauntlet.py` — CERT gauntlet pattern reference (5 attacks + summary structure, `_make_minimal_pack` helper)
- Existing codebase: `tests/steward/test_step_chain_all_claims.py` — structural test pattern (7/14 claims, 4-test-per-claim, `_assert_trace_valid` helper)
- Existing codebase: `tests/steward/test_cert_5layer_independence.py` — `_make_full_5layer_bundle` helper and 5-layer independence proof pattern
- Existing codebase: `tests/steward/test_cross_claim_chain.py` — anchor_hash cross-claim chain pattern
- Existing codebase: `backend/progress/data_integrity.py` — `canonicalize_bytes` limitations confirmed (handles CRLF, does NOT handle BOM/NFC-NFD/null bytes)
- Existing codebase: `backend/progress/runner.py` — `_execute_job_logic` dispatch structure; `sys.path.insert(0, '/app')` module-level side effect at line 19
- Existing codebase: `scripts/mg.py` `_verify_semantic()` lines 149-269 — Layer 2 edge case surface fully inspected
- Existing codebase: `scripts/steward_audit.py` — relational assertion pattern for governance (set equality, not hardcoded counts)
- Pytest documentation: `pytest.mark.parametrize`, `pytest.param` with `id=`, `tmp_path` fixture — all features stable since pytest 6.x

### Secondary (MEDIUM confidence)
- [PEP 672 — Unicode Security Considerations for Python](https://peps.python.org/pep-0672/) — homoglyph attack vectors, Cyrillic confusables relevant to claim ID spoofing
- [OWASP Cryptographic Failures](https://owasp.org/Top10/A02_2021-Cryptographic_Failures/) — encoding and corruption attack pattern taxonomy
- [Adversarial Exposure Validation Guide (CyCognito)](https://www.cycognito.com/learn/exposure-management/adversarial-exposure-validation/) — industry framework for coordinated multi-vector attack simulation

### Tertiary (contextual)
- [CMMTree Cryptographic Protocol Testing Methodology](https://www.mdpi.com/2076-3417/13/23/12668) — systematic protocol test coverage framework; alignment with v0.5.0 approach confirmed

---
*Research completed: 2026-03-17*
*Ready for roadmap: yes*
