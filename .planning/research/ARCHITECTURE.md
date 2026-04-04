# Architecture Research: Test Coverage Hardening (P1-P10 Integration)

**Domain:** Verification protocol test suite expansion
**Researched:** 2026-03-17
**Confidence:** HIGH (based on direct codebase analysis of all 48 existing test files, runner.py, and mg.py _verify_semantic)

## Existing Test Architecture

### Directory Layout and Ownership

```
tests/
├── steward/                  # Governance, adversarial proofs, structural tests
│   ├── test_cert01_*         # Layer 1: SHA-256 integrity
│   ├── test_cert02_*         # Layer 2: Semantic verification
│   ├── test_cert03_*         # Layer 3: Step chain tamper
│   ├── test_cert04_*         # Layer 3: Cross-claim anchor hash
│   ├── test_cert05_*         # 5-attack gauntlet (Layers 1-3)
│   ├── test_cert06_*         # 6 real-world scenarios
│   ├── test_cert07_*         # Layer 4: HMAC bundle signing
│   ├── test_cert08_*         # Reproducibility proofs
│   ├── test_cert09_*         # Layer 4: Ed25519 attacks
│   ├── test_cert10_*         # Layer 5: Temporal attacks
│   ├── test_cert_5layer_*    # 5-layer independence proof
│   ├── test_cross_claim_*    # Cross-claim chain (MTR-1 -> DT-FEM-01 -> DRIFT-01)
│   ├── test_step_chain_*     # Step chain structural tests (7/14 claims)
│   ├── test_stew01-07_*      # Steward governance tests
│   ├── test_ed25519.py       # Ed25519 key generation/signing
│   ├── test_signing_upgrade  # HMAC -> Ed25519 migration
│   ├── test_temporal.py      # Temporal commitment basics
│   └── test_drift01_*        # DRIFT-01 calibration anchor
├── materials/                # MTR-1/2/3 claim domain tests
├── ml/                       # ML_BENCH-01/02/03, PHARMA-01, FINRISK-01
├── digital_twin/             # DT-FEM-01, DT-SENSOR-01, DT-CALIB-LOOP-01
├── data/                     # DATA-PIPE-01 quality certificate
├── systems/                  # SYSID-01 ARX calibration
├── cli/                      # CLI integration / E2E tests
├── progress/                 # Progress store and evidence index
└── fixtures/                 # Shared test data
```

### Established Patterns (3 Core Patterns)

**Pattern 1: CERT-XX Gauntlet (Adversarial Proofs)**

Every CERT file follows this exact structure:
- Module docstring listing ALL attack scenarios with layer attribution
- Helper function `_make_*_bundle()` to construct minimal valid bundles
- Single test class `TestCertXX*` containing:
  - Named attack methods: `test_attack[N]_[descriptive_name]` (CERT-05) or `test_[letter]_[name]` (CERT-09/10)
  - Each attack builds/modifies a bundle, then asserts verification FAILS
  - Composite summary test `test_[z_]gauntlet_summary` documenting attack-to-layer coverage
- Imports from `scripts/mg.py`, `scripts/mg_sign.py`, `scripts/mg_temporal.py` as needed

**Pattern 2: Step Chain Structural Tests**

`test_step_chain_all_claims.py` uses:
- Module-level shared helpers: `_assert_trace_valid()` and `_get_trace_root()`
- Per-claim class `TestStepChain[CLAIM_ID]` with exactly 4 tests:
  - `test_[claim]_trace_present` -- validates 4-step trace structure via `_assert_trace_valid()`
  - `test_[claim]_trace_four_steps` -- validates step count (and sometimes step names)
  - `test_[claim]_trace_deterministic` -- same inputs produce same `trace_root_hash`
  - `test_[claim]_trace_changes_with_[param]` -- different inputs produce different hash

**Pattern 3: Cross-Claim Chain Tests**

`test_cross_claim_chain.py` tests one chain: MTR-1 -> DT-FEM-01 -> DRIFT-01.
Uses `anchor_hash` and `anchor_claim_id` kwargs to link claims.
Single class `TestCrossClaimChain` with 6 tests covering: chain formation, anchor propagation, tamper detection, backward compatibility.

## Component Mapping: P1-P10 to Files

### Files to MODIFY (extend existing)

| Priority | Gap | Existing File | What to Add | Est. Tests |
|----------|-----|---------------|-------------|------------|
| P1 | Step chain structural (7 missing claims) | `tests/steward/test_step_chain_all_claims.py` | 7 new `TestStepChain*` classes for: ML_BENCH-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01 | 28 |
| P3+P8 | Cross-claim cascade + additional chains | `tests/steward/test_cross_claim_chain.py` | New class `TestCrossClaimCascadeFailure` (break MTR-1, verify DT-FEM-01 and DRIFT-01 anchor invalidation). New class `TestDriftCalibChain` for DRIFT-01 -> DT-CALIB-LOOP-01 chain | 8 |

### Files to CREATE (new)

| Priority | Gap | New File | Pattern | Est. Tests |
|----------|-----|----------|---------|------------|
| P2 | CERT-11 coordinated attack | `tests/steward/test_cert11_coordinated_attack.py` | CERT-XX gauntlet | 6 |
| P4 | Step chain ordering attacks | `tests/steward/test_step_chain_ordering.py` | Structural test | 6 |
| P5 | Partial corruption / CERT-12 encoding | `tests/steward/test_cert12_encoding_attacks.py` | CERT-XX gauntlet | 5 |
| P6 | Layer 2 semantic edge cases | `tests/steward/test_cert02_semantic_edge_cases.py` | Semantic test | 8 |
| P7 | Runner error paths | `tests/progress/test_runner_error_paths.py` | Unit test | 8 |
| P9 | Manifest version rollback | `tests/steward/test_manifest_rollback.py` | Adversarial test | 3 |
| P10 | Documentation drift detection | `tests/steward/test_documentation_drift.py` | Meta-governance | 5 |

**Total estimated new tests: ~77** (exceeds the 60+ target)

## CERT-11: Coordinated Multi-Vector Attack Architecture

CERT-11 is the flagship test for the JOSS paper's independence thesis. It must prove that an attacker who bypasses Layer N still fails on Layer N+1 -- tested as a single coordinated attack sequence, not isolated per-layer proofs (which CERT-05 and test_cert_5layer_independence.py already cover).

### Why CERT-11 is NOT Redundant

| Existing Test | What It Proves | What It Misses |
|---------------|----------------|----------------|
| CERT-05 | 5 isolated attacks, each caught by one layer | Never combines attacks |
| test_cert_5layer_independence | Each layer catches a unique attack class the other 4 miss | Tests one bypass per layer, never coordinates |
| **CERT-11** | **A single attacker applies ALL bypass techniques simultaneously** | **This is the new proof** |

### Proposed Attack Scenarios

```python
"""
CERT-11: Coordinated Multi-Vector Attack Gauntlet.

ATTACK SCENARIOS:
  Attack 1 -- Full Bypass Attempt (all 5 layers targeted simultaneously)
    Attacker modifies evidence, rebuilds SHA-256 (bypass L1),
    preserves job_snapshot structure (bypass L2), keeps valid trace format (bypass L3),
    re-signs with a different key (attempt bypass L4).
    Layer 4 catches: key fingerprint mismatch in signature.

  Attack 2 -- Cascading Layer Bypass (L1+L2+L3 bypassed, L4 catches)
    Attacker modifies result, updates manifest hashes, keeps semantic structure,
    preserves trace structure, but lacks original signing key.
    Layer 4 catches: signature over old root_hash does not match new root_hash.

  Attack 3 -- Semantic + Chain Combined Attack
    Attacker swaps claim domain AND modifies step chain hash simultaneously.
    Both L2 and L3 detect -- proves layers fire independently, not sequentially.

  Attack 4 -- Insider Threat (has signing key, attacks evidence)
    Attacker with valid signing key modifies evidence and re-signs the bundle.
    Layer 3 catches: step chain trace_root_hash does not match tampered content.
    Proves: even authorized signers cannot forge computation results.

  Attack 5 -- Temporal Replay with Fresh Signature
    Attacker replays an old bundle, re-signs with valid key, re-creates temporal commitment.
    Tests whether the protocol can detect content substitution when L4+L5 are validly recreated.
    Layer 3 catches: trace_root_hash was computed from different inputs.
"""
```

### Data Flow for Coordinated Attack Tests

```
_make_full_5layer_bundle()          (reuse from test_cert_5layer_independence.py)
         |
         v
    Valid 5-layer bundle
         |
    +---------+---------+---------+---------+---------+
    |         |         |         |         |         |
  Attack 1  Attack 2  Attack 3  Attack 4  Attack 5  Summary
    |         |         |         |         |         |
  Modify    Modify    Swap +    Modify +  Replay     Document
  evidence  result    modify    re-sign   old bundle coverage
  rebuild   rebuild   chain    (insider)  re-sign +
  manifest  manifest                      re-temporal
  re-sign
    |         |         |         |         |
  Verify    Verify    Verify    Verify    Verify
  all 5     all 5     L2+L3    all 5     all 5
  layers    layers    both     layers    layers
    |         |         |         |         |
  L4 FAIL   L4 FAIL   L2+L3    L3 FAIL   L3 FAIL
                       FAIL
```

### Key Design Decision: Reuse `_make_full_5layer_bundle()`

The `test_cert_5layer_independence.py` file has a well-tested `_make_full_5layer_bundle()` helper (lines 80-186) plus `_rebuild_manifest()` (lines 189-210) and `_build_valid_trace()` (lines 60-77). CERT-11 should reuse these.

**Recommended approach:** Extract helpers into `tests/steward/_bundle_helpers.py` (underscore prefix prevents pytest collection). Both `test_cert_5layer_independence.py` and `test_cert11_coordinated_attack.py` import from it. This avoids cross-test-file imports that can cause pytest collection issues.

```python
# tests/steward/_bundle_helpers.py
"""Shared bundle construction helpers for adversarial test files."""

def _hash_step(step_name, step_data, prev_hash): ...
def _build_valid_trace(): ...
def _make_full_5layer_bundle(tmp_path, name="bundle"): ...
def _rebuild_manifest(bundle): ...
def _make_minimal_pack(tmp_path, job_kind, claim_id, **kwargs): ...
```

## CERT-12: Encoding Attack Architecture

CERT-12 tests partial corruption and encoding edge cases -- attacks that exploit the boundary between "valid JSON" and "valid evidence."

### Proposed Attack Scenarios

```python
"""
CERT-12: Encoding and Partial Corruption Attack Gauntlet.

ATTACK SCENARIOS:
  Attack A -- Unicode Homoglyph in claim_id
    Attacker uses Unicode lookalike characters in mtr_phase field.
    e.g., "MTR-1" (hyphen-minus U+002D) vs "MTR\u20101" (figure dash U+2010).
    Layer 2 catches: mtr_phase does not match expected claim_id.

  Attack B -- BOM Injection in Evidence JSON
    Attacker prepends UTF-8 BOM (\xef\xbb\xbf) to run_artifact.json.
    Layer 1 catches: SHA-256 of BOM-prefixed file does not match manifest hash.

  Attack C -- Null Byte Injection in trace_root_hash
    Attacker injects null bytes into hash string.
    Step chain validation catches: hash is not valid 64-char lowercase hex.

  Attack D -- Duplicate JSON Keys
    Attacker provides duplicate "trace_root_hash" keys with different values.
    Python json.loads() takes last value -- test verifies protocol is not confused.

  Attack E -- Oversized Execution Trace (5+ steps)
    Attacker adds extra steps beyond the required 4.
    Tests whether the protocol enforces exactly 4 steps.
    NOTE: Current _verify_semantic() checks len(execution_trace) > 0 but
    does NOT enforce len == 4. This test documents the behavior.
"""
```

### Rationale for Separation from CERT-05/CERT-11

CERT-05 and CERT-11 test logical attacks (evidence stripping, result manipulation, domain substitution). CERT-12 tests encoding-level attacks that exploit parser behavior. These are fundamentally different attack surfaces.

## Build Order (Dependency-Aware)

### Phase 1: Foundation (no inter-test dependencies)

These tests are self-contained and can be built in any order within the phase.

| Order | Gap | File Action | Est. Tests | Rationale |
|-------|-----|-------------|------------|-----------|
| 1.1 | P1 | EXTEND `test_step_chain_all_claims.py` | 28 | Pure structural tests. No dependencies. Uses established 4-test-per-claim pattern exactly. Biggest test count boost (28 new tests). Build first because P3 cascade tests depend on all 14 claims having verified step chains. |
| 1.2 | P7 | CREATE `tests/progress/test_runner_error_paths.py` | 8 | Pure unit tests against `runner.py` `_execute_job_logic()`. Tests: unknown JOB_KIND raises ValueError, missing payload.kind, None payload, exception propagation. No dependencies on other test infrastructure. |
| 1.3 | P4 | CREATE `tests/steward/test_step_chain_ordering.py` | 6 | Tests step chain structural invariants: reordered steps, duplicate step numbers, missing step, extra 5th step, non-sequential step numbers, empty trace. Uses `_assert_trace_valid()` helper from test_step_chain_all_claims.py and `_hash_step()` for constructing invalid traces. |

### Phase 2: Layer Hardening (no cross-phase dependencies)

| Order | Gap | File Action | Est. Tests | Rationale |
|-------|-----|-------------|------------|-----------|
| 2.1 | P6 | CREATE `tests/steward/test_cert02_semantic_edge_cases.py` | 8 | Exercises `_verify_semantic()` edge cases not covered by CERT-02. Tests: malformed evidence_index.json (not a dict, empty dict, missing job_kind), invalid run_artifact JSON, empty ledger file, UQ block edge cases (ci_low >= ci_high, stability_score out of range, missing UQ fields), anchor_hash format validation (uppercase hex, wrong length). |
| 2.2 | P9 | CREATE `tests/steward/test_manifest_rollback.py` | 3 | Tests manifest version field attacks: downgrade version string, missing version field, inject extra fields into manifest. Verifies the protocol rejects or handles these correctly. |
| 2.3 | P5 | CREATE `tests/steward/test_cert12_encoding_attacks.py` | 5 | Encoding attacks (see CERT-12 section above). Independent of other CERT tests. |

### Phase 3: Chain and Cascade (depends on P1)

| Order | Gap | File Action | Est. Tests | Rationale |
|-------|-----|-------------|------------|-----------|
| 3.1 | P3+P8 | EXTEND `test_cross_claim_chain.py` | 8 | Cascade failure tests: (1) break MTR-1 seed, verify entire MTR-1 -> DT-FEM-01 -> DRIFT-01 chain invalidates. (2) New chain: DRIFT-01 -> DT-CALIB-LOOP-01. (3) Orphaned anchor: provide anchor_hash from non-existent upstream. (4) Circular anchor detection. Depends on P1 confirming all claims produce valid traces. |

### Phase 4: Flagship (depends on all prior phases)

| Order | Gap | File Action | Est. Tests | Rationale |
|-------|-----|-------------|------------|-----------|
| 4.1 | P2 | CREATE `tests/steward/test_cert11_coordinated_attack.py` | 6 | The coordinated attack proof. Must be built last because it synthesizes ALL attack vectors from prior phases. Reuses `_make_full_5layer_bundle()` helper. This is the JOSS paper's proof of independence thesis under coordinated attack. |

### Phase 5: Meta (independent, parallel with Phase 4)

| Order | Gap | File Action | Est. Tests | Rationale |
|-------|-----|-------------|------------|-----------|
| 5.1 | P10 | CREATE `tests/steward/test_documentation_drift.py` | 5 | Governance meta-tests: verify test count, claim count, layer count, and innovation count are consistent across CLAUDE.md, index.html, README.md, CONTEXT_SNAPSHOT.md, llms.txt, system_manifest.json. Pure file-scanning tests. No verification logic dependencies. |

### Dependency Graph

```
P1 (step chain 7 claims) ─────────┐
P7 (runner error paths)            │
P4 (step chain ordering)           │
                                   ├──> P3+P8 (cascade) ──> P2 (CERT-11)
P6 (semantic edge cases)           │                              ^
P9 (manifest rollback)  ──────────┘                              |
P5 (CERT-12 encoding)  ─────────────────────────────────────────┘

P10 (doc drift) ── fully independent, build anytime
```

### Critical Path

The longest dependency chain is:
```
P1 (28 tests) -> P3+P8 (8 tests) -> P2 (6 tests)
```
This path must complete in order. All other gaps can be parallelized.

## Integration Points

### Shared Helper Extraction Plan

If CERT-11 needs `_make_full_5layer_bundle()` from test_cert_5layer_independence.py, extract shared helpers:

```
tests/steward/_bundle_helpers.py     (new, underscore prefix = no pytest collection)
  ├── _hash_step()                   from test_cert_5layer_independence.py
  ├── _build_valid_trace()           from test_cert_5layer_independence.py
  ├── _make_full_5layer_bundle()     from test_cert_5layer_independence.py
  ├── _rebuild_manifest()            from test_cert_5layer_independence.py
  └── _make_minimal_pack()           from test_cert05_adversarial_gauntlet.py
```

**Decision gate:** Only extract if 2+ new files need the same helper. If only CERT-11 needs the 5-layer helper, direct import is simpler. Monitor during Phase 4 implementation.

### Import Dependencies for Each New File

| New File | Imports From Production Code | Imports From Test Code |
|----------|------------------------------|------------------------|
| P1 extension | `backend.progress.*` (7 claim modules) | `_assert_trace_valid()` already in same file |
| P7 runner paths | `backend.progress.runner.ProgressRunner`, `backend.progress.store.JobStore`, `backend.ledger.ledger_store.LedgerStore` | None |
| P4 ordering | `scripts.mg._verify_semantic` | `_assert_trace_valid()` from test_step_chain_all_claims |
| P6 semantic | `scripts.mg._verify_semantic` | `_make_minimal_pack()` from test_cert05 or _bundle_helpers |
| P5 CERT-12 | `scripts.mg._verify_semantic` | `_make_minimal_pack()` from test_cert05 or _bundle_helpers |
| P9 rollback | `scripts.mg._verify_semantic` or CLI subprocess | None |
| P2 CERT-11 | `scripts.mg._verify_semantic`, `scripts.mg_sign.*`, `scripts.mg_temporal.*`, `scripts.mg_ed25519.*` | `_make_full_5layer_bundle()` from test_cert_5layer_independence or _bundle_helpers |
| P3+P8 cascade | `backend.progress.{mtr1, dtfem1, drift_monitor, dtcalib1}` | Existing helpers in test_cross_claim_chain.py |
| P10 doc drift | None (pure filesystem scanning) | None |

## Anti-Patterns to Avoid

### Anti-Pattern 1: Duplicating Bundle Construction Helpers

**What people do:** Each new CERT test file reimplements `_make_minimal_pack()` with slight variations.
**Why it's wrong:** Bundle construction bugs become hard to track. A fix in one file doesn't propagate.
**Do this instead:** Import from the existing file or extract to `_bundle_helpers.py` if 2+ files need it.

### Anti-Pattern 2: Monolithic CERT-11

**What people do:** Create one giant test that attempts all 5 attacks in sequence within a single test function.
**Why it's wrong:** If attack 2 fails, attacks 3-5 never run. Hard to diagnose which layer broke.
**Do this instead:** Separate test methods per attack scenario, matching CERT-05/09/10 pattern. The `test_z_gauntlet_summary` documents the composite proof.

### Anti-Pattern 3: Step Chain Tests Without Sensitivity Check

**What people do:** Only test `trace_present` and `trace_deterministic`, skipping the sensitivity check.
**Why it's wrong:** A claim that returns a hardcoded trace would pass both tests but provide zero verification value.
**Do this instead:** Always include `test_[claim]_trace_changes_with_[param]`, matching the existing 4-test pattern.

### Anti-Pattern 4: Testing Exact Error Messages

**What people do:** Assert `msg == "Run artifact ... missing required key: job_snapshot"` character-by-character.
**Why it's wrong:** Error messages may change in future versions; the test should verify detection, not wording.
**Do this instead:** Use substring checks (`"job_snapshot" in msg`) or category checks (`ok is False`), consistent with existing CERT tests.

### Anti-Pattern 5: Subprocess for Unit-Level Tests

**What people do:** Use `subprocess.run(["python", "scripts/mg.py", ...])` for every test, even when testing `_verify_semantic()` directly.
**Why it's wrong:** Subprocess tests are slower, harder to debug, and sensitive to environment differences (PATH, venv, CRLF).
**Do this instead:** Import and call `_verify_semantic()` directly for Layer 2/3 tests. Use subprocess only for CLI integration tests (CERT-01, CERT-02).

## Sources

- Direct analysis of all 48 test files in the repository
- `scripts/mg.py` `_verify_semantic()` function (lines 149-269) for Layer 2 edge case surface
- `backend/progress/runner.py` `_execute_job_logic()` (lines 188-419) for runner dispatch coverage
- `test_cert05_adversarial_gauntlet.py` for CERT gauntlet pattern (5 attacks + summary)
- `test_cert09_ed25519_attacks.py` for CERT gauntlet pattern variant (letter-named attacks)
- `test_cert10_temporal_attacks.py` for CERT gauntlet pattern with mocked external services
- `test_cert_5layer_independence.py` for 5-layer bundle construction and independence matrix
- `test_step_chain_all_claims.py` for step chain structural test pattern (7 existing claim classes)
- `test_cross_claim_chain.py` for cross-claim chain test pattern (anchor_hash propagation)

---
*Architecture research for: MetaGenesis Core v0.5.0 Test Coverage Hardening*
*Researched: 2026-03-17*
