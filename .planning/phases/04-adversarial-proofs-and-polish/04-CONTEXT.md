# Phase 4: Adversarial Proofs and Polish - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Prove all new v0.4.0 capabilities (Ed25519 signing, temporal commitment, 5-layer architecture) through adversarial tests, expand deep_verify from 10 to 13 tests, create CERT-09 (Ed25519 attack gauntlet) and CERT-10 (temporal attack gauntlet), demonstrate 5-layer independence, and update all documentation counters to reflect v0.4.0 state.

</domain>

<decisions>
## Implementation Decisions

### deep_verify Tests 11-13
- Test 11 (signing integrity): Sign a bundle with Ed25519 key, verify it passes, tamper the signature bytes, verify it fails — proves Layer 4 Ed25519 path works end-to-end
- Test 12 (reproducibility): Same inputs produce identical Ed25519 signatures and trace hashes across runs — proves determinism holds with new signing
- Test 13 (temporal commitment): Sign with temporal commitment, verify Layer 5 passes, tamper temporal_binding hash, verify Layer 5 fails — proves temporal layer catches forgery
- All 3 tests follow deep_verify's existing pattern: subprocess calls to mg.py/mg_sign.py, assert on PASS/FAIL output, print `[PASS]`/`[FAIL]` status
- Final line updated to "ALL 13 TESTS PASSED"

### CERT-09: Ed25519 attack gauntlet
- New test file: `tests/steward/test_cert09_ed25519_attacks.py`
- 5 attack scenarios minimum:
  1. Wrong key verification — sign with key A, verify with key B → FAIL
  2. Signature bit-flip — flip one bit in signature → FAIL
  3. Downgrade attack — Ed25519-signed bundle verified with HMAC key → FAIL (version mismatch rejection)
  4. Key type mismatch — bundle self-declares hmac but verifier holds ed25519 key → FAIL
  5. Truncated/malformed signature — corrupted signature field → FAIL
- Follow existing cert05 gauntlet pattern (multiple attacks in one test file)

### CERT-10: Temporal attack gauntlet
- New test file: `tests/steward/test_cert10_temporal_attacks.py`
- 5 attack scenarios minimum:
  1. Replay attack — copy temporal_commitment.json from bundle A to bundle B (different root_hash) → binding check fails
  2. Future-date timestamp — forge a timestamp ahead of current time → binding hash mismatch
  3. Beacon value forge — replace beacon_value with different random → binding hash mismatch
  4. Binding hash tamper — modify temporal_binding field directly → verification detects mismatch
  5. Pre-commitment hash tamper — modify pre_commitment_hash to not match SHA-256(root_hash) → first verification check fails
- Follow existing cert05/cert07 gauntlet patterns

### 5-layer independence proof
- Matrix approach: for each of the 5 layers, construct an attack that passes all OTHER 4 layers but fails only the target layer
- This proves each layer is independently necessary — removing any one layer leaves an exploitable gap
- Can be part of CERT-09/CERT-10 or a separate test (Claude's discretion on organization)
- Must explicitly demonstrate: Layer 1 (SHA-256), Layer 2 (semantic), Layer 3 (step chain), Layer 4 (signing), Layer 5 (temporal) each catch unique attack classes

### Documentation counter updates
- Determine actual test count dynamically after all new tests pass
- Update layers: 3 → 5 (Layers 4 and 5 now proven)
- Update innovations: 6 → 7 (Innovation #7: Temporal Commitment)
- Files to update: index.html (11+ places including prose), README.md, AGENTS.md, llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md
- system_manifest.json protocol version bump (DOCS-02)
- reports/scientific_claim_index.md updated with new capabilities (DOCS-03)
- paper.md references updated to cite implemented innovations (DOCS-04)
- Use PowerShell batch replace for index.html per CLAUDE.md BUG 7 guidance

### Claude's Discretion
- Internal structure of CERT-09 and CERT-10 (helper functions, fixtures)
- Whether 5-layer independence is its own test file or integrated into existing gauntlets
- Exact wording of deep_verify test output messages
- Order of documentation updates
- How to handle test count in system_manifest.json (hardcoded vs dynamic)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing adversarial proof suite
- `tests/steward/test_cert05_adversarial_gauntlet.py` -- Pattern for multi-attack gauntlet tests (5 attacks, proves 3 layers needed)
- `tests/steward/test_cert07_bundle_signing.py` -- 13 bundle signing tests, pattern for Layer 4 attack scenarios
- `tests/steward/test_cert08_reproducibility.py` -- 10 reproducibility proofs, pattern for determinism testing

### deep_verify expansion
- `scripts/deep_verify.py` -- Current 10 tests, needs Tests 11-13 appended. Follow existing test pattern (subprocess + assert)

### Signing infrastructure (Phase 1-2 outputs)
- `scripts/mg_ed25519.py` -- Ed25519 implementation, sign/verify functions, key generation
- `scripts/mg_sign.py` -- Dual-algorithm dispatch (HMAC + Ed25519), sign_bundle(), verify_bundle()
- `scripts/mg.py` -- Core verifier CLI, Layer 4 verification path

### Temporal infrastructure (Phase 3 output)
- `scripts/mg_temporal.py` -- Temporal commitment module, create/verify functions, pre-commitment scheme
- `tests/steward/test_temporal.py` -- Existing temporal tests (basic pass/fail)
- `tests/steward/test_ed25519.py` -- Existing Ed25519 tests (basic pass/fail)

### Documentation targets
- `index.html` -- 11+ counter locations (claims, tests, layers, domains, innovations) per CLAUDE.md BUG 7
- `system_manifest.json` -- protocol version, test_count, active_claims
- `README.md`, `AGENTS.md`, `llms.txt`, `CONTEXT_SNAPSHOT.md` -- Counter references
- `reports/scientific_claim_index.md` -- Claim registry, needs new capability entries
- `paper.md` -- JOSS paper, needs innovation references (DOCS-04)

### Project constraints
- `CLAUDE.md` -- Sealed files list, banned terms, verification gates, counter update guidance

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/steward/test_cert05_adversarial_gauntlet.py`: Multi-attack gauntlet pattern — reuse for CERT-09 and CERT-10 structure
- `tests/steward/test_cert07_bundle_signing.py`: Bundle signing test helpers — reuse for Ed25519 attack scenarios
- `scripts/deep_verify.py`: Test pattern (subprocess + assert + print status) — append Tests 11-13 following same style
- `scripts/mg_sign.py:sign_bundle()` and `verify_bundle()`: Direct function imports for test scenarios
- `scripts/mg_temporal.py:create_temporal_commitment()` and `verify_temporal_commitment()`: Direct imports for temporal attack tests

### Established Patterns
- Gauntlet tests: multiple attack scenarios in one file, each as separate test function with `test_a_`, `test_b_` prefix ordering
- deep_verify: sequential numbered tests, subprocess-based, print `[PASS]`/`[FAIL]`, final summary line
- `(ok, message)` return tuple for verification — check `ok is False` and message contains expected error
- Temporary directories via `tempfile.TemporaryDirectory()` for bundle manipulation
- SHA-256 recalculation after tampering (update manifest to bypass Layer 1, then test Layer 2+)

### Integration Points
- deep_verify.py Tests 11-13 append after Test 10 (verify-chain CLI exists)
- CERT-09 and CERT-10 are new files in `tests/steward/` — follow naming `test_cert09_*.py` and `test_cert10_*.py`
- Counter updates touch multiple files simultaneously — must be atomic (all or nothing)
- system_manifest.json test_count must match actual `pytest tests/ -q` count after all new tests added

</code_context>

<specifics>
## Specific Ideas

- The 5-layer independence proof is the crown jewel — it demonstrates that MetaGenesis Core's multi-layer approach is architecturally necessary, not just defense-in-depth theater
- CERT-09 and CERT-10 follow the established "proof, not trust" philosophy — each attack scenario proves a security property
- deep_verify Tests 11-13 should be runnable independently (each test is self-contained) like existing Tests 1-10
- Counter updates should be the LAST step — only after all tests pass and the final test count is known
- The "5 attacks, proves N layers needed" pattern from CERT-05 extends naturally to "5 attacks, proves 5 layers needed"

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 04-adversarial-proofs-and-polish*
*Context gathered: 2026-03-17*
