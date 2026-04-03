# Phase 6: Layer Hardening - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden Layer 2 semantic verification against edge cases (partial fields, extra fields, meaningless values), test cross-claim cascade failure propagation through the full 4-hop anchor chain (MTR-1→DT-FEM-01→DRIFT-01→DT-CALIB-LOOP-01), and reject manifest protocol_version rollback attacks. Tests-only milestone with minimal, targeted production code changes where required for testability.

</domain>

<decisions>
## Implementation Decisions

### Semantic Edge Cases (SEM-01/02/03)
- **SEM-01 (partial fields):** Test both missing nested keys AND present-but-null values. E.g., result exists but result.pass is missing; trace_root_hash present but null.
- **SEM-02 (extra fields):** Warn but pass — extra unexpected fields are logged/noted in the verification report but do NOT cause FAIL. Forward-compatible approach.
- **SEM-03 (meaningless values):** Reject empty strings for mtr_phase/job_kind, zero for physical quantities where physically impossible (E=0 GPa, rel_err_threshold=0), AND negative values for inherently positive quantities (thresholds, physical constants, step counts).
- **Approach:** Test-driven — write tests first showing the gap in current _verify_semantic(), then add minimal validation to mg.py so the tests pass.
- **Semantic tests extend test_cert02_semantic_bypass.py** with new test classes.

### Cross-Claim Cascade Failure (CASCADE-01/02/03)
- **CASCADE-01 (full chain):** Test the complete 4-hop anchor chain: MTR-1→DT-FEM-01→DRIFT-01→DT-CALIB-LOOP-01. Not just the 3-hop chain in the existing test.
- **CASCADE-02 (failure propagation):** Verify both: different trace_root_hash at every downstream hop when upstream is tampered, PLUS verify that _verify_chain() correctly reports the break. Tests the detection mechanism, not just the math.
- **CASCADE-03 (tamper at any position):** Parametrize over ALL hops (hop 1, 2, 3) PLUS test swapping a middle claim entirely (replace DT-FEM-01 with a different run). Catches both hash tampering and claim substitution.
- **Cascade tests extend test_cross_claim_chain.py** with new TestFullAnchorChain class alongside existing TestCrossClaimChain.

### Manifest Version Rollback (ADV-07)
- **protocol_version lives in pack_manifest.json** — natural place since manifest is the pack's metadata.
- **Integer version format** (1, 2, 3...) — verifier rejects if version < minimum_supported_version. Simple to compare.
- **Minimal production code changes OK** — add protocol_version to steward_submission_pack.py (pack builder) AND version check to mg.py (_verify_pack). Required for testability.
- **Rollback test in new file** test_manifest_rollback.py (or similar) — since no existing cert file covers this specific attack vector.

### Claude's Discretion
- Exact field allowlist for SEM-02 warning (which fields to flag as unexpected)
- How to report SEM-02 warnings in the verification output (report dict structure)
- Specific minimum_supported_version constant placement (in mg.py or config)
- Test parametrization details for CASCADE-03 hop positions

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Layer 2 Semantic Verification
- `scripts/mg.py` §_verify_semantic (lines 149-279) — Current semantic validation logic, all existing checks
- `tests/steward/test_cert02_semantic_bypass.py` — Existing semantic bypass proof tests (extend this file for SEM tests)

### Cross-Claim Chain
- `tests/steward/test_cross_claim_chain.py` — Existing 3-hop chain tests MTR-1→DT-FEM-01→DRIFT-01 (extend for 4-hop)
- `tests/steward/test_cert04_anchor_hash_verify.py` — anchor_hash format validation tests, reusable _make_pack() helper
- `scripts/mg.py` §_verify_chain (lines 282+) — Cross-claim chain verification logic
- `backend/progress/dtcalib1_convergence_certificate.py` — DT-CALIB-LOOP-01 implementation (anchor_hash parameter at line 57)
- `backend/progress/drift_monitor.py` — DRIFT-01 implementation (anchor_hash support)
- `backend/progress/dtfem1_displacement_verification.py` — DT-FEM-01 implementation (anchor_hash support)

### Manifest & Pack Building
- `scripts/steward_submission_pack.py` — Pack builder (add protocol_version field here)
- `tests/steward/test_cert01_pack_manifest_verify.py` — Existing manifest integrity tests (reference for pack test patterns)

### Architecture
- `.planning/codebase/ARCHITECTURE.md` — Layer descriptions and data flow
- `.planning/codebase/TESTING.md` — Test organization and naming conventions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_make_pack()` in test_cert04: builds minimal pack directory with evidence_index.json — reusable for SEM and rollback tests
- `_verify_semantic()` import pattern: `from scripts.mg import _verify_semantic` — direct import, no subprocess
- `TestCrossClaimChain` class: `_run_mtr1()`, `_run_dtfem()`, `_run_drift()` helpers — extend with `_run_dtcalib()`
- Existing `_VALID_HASH = "a" * 64` pattern for synthetic test hashes

### Established Patterns
- Alphabetical test prefixes: test_a_, test_b_, test_c_ for ordering within a class
- Module-level helpers (no conftest.py fixtures)
- CRLF-safe: use write_text(encoding="utf-8") for test artifacts
- Each claim imported directly: `from backend.progress.<module> import <function>`

### Integration Points
- SEM tests call _verify_semantic() with synthetic packs (same as test_cert02/cert04)
- CASCADE tests call claim run functions directly and chain anchor_hash parameters
- Rollback tests call _verify_pack() or _verify_semantic() with synthetic manifests containing old protocol_version

</code_context>

<specifics>
## Specific Ideas

- SEM-01 should test mtr_phase=null, trace_root_hash=null, and execution_trace with missing step hashes
- SEM-03 zero-value check: E=0 GPa is physically impossible for aluminum, so inputs referencing physical constants should reject zero
- CASCADE-03 "middle swap" test: run DT-FEM-01 with seed=99 instead of seed=42 while keeping same anchor_hash — proves the chain detects substituted computations
- ADV-07 test should verify that version=0 or version=-1 is rejected even if the rest of the manifest is valid

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-layer-hardening*
*Context gathered: 2026-03-17*
