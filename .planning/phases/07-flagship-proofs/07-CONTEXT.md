# Phase 7: Flagship Proofs - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

CERT-11 proves the 5-layer independence thesis under coordinated multi-vector attack (ADV-01 through ADV-04). CERT-12 proves encoding attacks (BOM-prefixed files, null bytes, truncated JSON, Unicode homoglyphs) are detected or handled safely (ADV-05, ADV-06). Tests-only — minimal production code changes only where required for testability.

</domain>

<decisions>
## Implementation Decisions

### Attack-to-Layer Attribution (CERT-11)
- Each CERT-11 test scenario MUST assert WHICH specific layer caught the attack, not just that verification failed
- Pattern: construct a pack that is valid at all layers BELOW the target, corrupted at the target layer
- Call the targeted layer's verify function directly (e.g., `_verify_semantic()`) to prove it fails
- Also call full `_verify_pack()` to prove end-to-end detection
- ADV-01: Attacker rebuilds Layer 1 (valid SHA-256) + fakes Layer 2 → assert Layer 2 catches it (semantic failure), Layer 1 passes
- ADV-02: Attacker rebuilds Layers 1+2 + forges Layer 3 → assert Layer 3 catches it (step chain mismatch), Layers 1+2 pass
- ADV-03: Stolen signing key + tampered evidence → assert Layers 1-3 catch it (signature valid but content integrity fails)
- ADV-04: Coordinated 3-layer bypass → assert remaining layers still detect the tampering

### Layer Bypass Simulation (CERT-11)
- Build valid lower layers, corrupt targeted layer — each scenario constructs a progressively more sophisticated attacker
- ADV-01 pack: recompute all SHA-256 hashes (L1 passes), but strip/corrupt semantic fields (L2 fails)
- ADV-02 pack: valid SHA-256 + valid semantic fields, but corrupted execution_trace hashes (L3 fails)
- ADV-03 pack: sign with valid key, but tamper evidence underneath → L1/L2/L3 catch pre-signature content
- ADV-04 pack: bypass L1+L2+L3 simultaneously → L4 (signature) or L5 (temporal) still catches
- Use `_build_valid_trace()` pattern from test_cert_5layer_independence.py for constructing valid step chains
- Use `_make_full_5layer_bundle()` pattern for full bundle construction

### Encoding Attack Vectors (CERT-12)
- ADV-05 (BOM): Write BOM-prefixed (`\xef\xbb\xbf`) evidence_index.json → test that `fingerprint_file` / integrity check detects the difference
- ADV-06 (null bytes): Inject null bytes (`\x00`) into field values in evidence_index.json → test rejection
- ADV-06 (truncated JSON): Write truncated JSON (missing closing braces) → test parsing failure is caught gracefully
- ADV-06 (homoglyphs): Replace ASCII characters in claim IDs with Unicode lookalikes (e.g., Cyrillic 'а' for Latin 'a') → test that verification fails or warns
- All encoding tests should use `write_bytes()` to control exact byte content (avoid Python text encoding normalization)
- Verify behavior against `fingerprint_file` from `backend.progress.data_integrity` (CRLF normalization)

### Test File Structure
- New file: `tests/steward/test_cert11_coordinated_attack.py` — CERT-11 coordinated multi-vector attack gauntlet
- New file: `tests/steward/test_cert12_encoding_attacks.py` — CERT-12 encoding and partial corruption attacks
- Follow established CERT-XX naming pattern (test_cert01 through test_cert10 exist)
- Each file has module-level docstring explaining the attack thesis being proved

### Claude's Discretion
- Exact number of test methods within each CERT file (aim for comprehensive coverage of each ADV requirement)
- Helper function structure (_make_pack variants for each scenario)
- Whether ADV-04 needs a single "ultimate" test or multiple sub-scenarios
- How to simulate temporal commitment bypass for ADV-04 (mock vs synthetic)
- Specific Unicode homoglyph characters to use in ADV-06

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### CERT-11 Coordinated Attack Patterns
- `tests/steward/test_cert05_adversarial_gauntlet.py` — 5-attack gauntlet proving 3-layer necessity (CERT-05 pattern to extend to 5 layers)
- `tests/steward/test_cert_5layer_independence.py` — 5-layer independence proof with `_build_valid_trace()`, `_make_full_5layer_bundle()` helpers
- `scripts/mg.py` §_verify_pack (line 51) — Full verification pipeline, Layer 1+2+3 checks
- `scripts/mg.py` §_verify_semantic (line 177) — Layer 2 semantic verification
- `scripts/mg.py` §_verify_chain (line 333) — Layer 3 step chain verification
- `scripts/mg_sign.py` — Layer 4 bundle signing (sign_bundle, verify_bundle_signature)
- `scripts/mg_temporal.py` — Layer 5 temporal commitment (create/verify/write functions)
- `scripts/mg_ed25519.py` — Ed25519 key generation for Layer 4 test bundles

### CERT-12 Encoding Attack Patterns
- `backend/progress/data_integrity.py` §fingerprint_file — CRLF normalization, SHA-256 computation
- `scripts/mg.py` §_verify_pack — Where integrity checks happen (BOM/null would be caught here)
- `tests/steward/test_cert01_pack_manifest_verify.py` — Existing integrity test patterns

### Requirements
- `.planning/REQUIREMENTS.md` — ADV-01 through ADV-06 acceptance criteria
- `.planning/phases/06-layer-hardening/06-CONTEXT.md` — Phase 6 decisions on protocol_version and semantic validation

### Architecture
- `CLAUDE.md` §4-LAYER VERIFICATION — Layer independence principle and key insight
- `CLAUDE.md` §PHYSICAL ANCHOR PRINCIPLE — Scope of physical anchor traceability vs tamper-evident provenance

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_build_valid_trace()` in test_cert_5layer_independence.py: builds valid 4-step execution trace with correct hash chain
- `_make_full_5layer_bundle()` in test_cert_5layer_independence.py: creates complete 5-layer bundle for testing
- `_make_minimal_pack()` in test_cert05: builds minimal pack with customizable fields
- `_hash_step()` helper: available in multiple test files for constructing step chains
- `_VALID_HASH_A/B/C/D` constants: synthetic 64-char hex hashes for test traces
- `generate_key_files()` from mg_ed25519: creates Ed25519 keypair for signing tests

### Established Patterns
- CERT test files: module docstring explaining thesis, `_ROOT` path setup, direct imports from scripts/
- Attack tests: construct invalid pack → call verify → assert specific failure
- 5-layer bundle: evidence_index.json + pack_manifest.json + signature + temporal commitment
- CRLF-safe writes: `write_bytes()` or `write_text(encoding="utf-8")` for all test artifacts
- Protocol version: integer format (1), enforced in `_verify_pack()` via `MINIMUM_PROTOCOL_VERSION`

### Integration Points
- CERT-11 tests import `_verify_pack`, `_verify_semantic` from scripts.mg
- CERT-11 tests import `sign_bundle`, `verify_bundle_signature` from scripts.mg_sign
- CERT-11 tests import temporal functions from scripts.mg_temporal
- CERT-12 tests import `fingerprint_file` from backend.progress.data_integrity
- Both files use `tmp_path` fixture for isolated test pack construction

</code_context>

<specifics>
## Specific Ideas

- CERT-11 should feel like an escalating series: each scenario represents a more sophisticated attacker who has overcome the previous layer's protection
- ADV-04 is the "crown jewel" test: proves that even an attacker who bypasses 3 layers simultaneously still gets caught
- CERT-12 BOM test should use exact byte sequence `b'\xef\xbb\xbf'` prepended to otherwise valid JSON
- Homoglyph test should use Cyrillic characters that look identical to Latin in most fonts (e.g., `\u0430` for 'a')
- Both CERT files should have clear docstrings explaining what they prove for the JOSS paper's independence thesis

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-flagship-proofs*
*Context gathered: 2026-03-18*
