# Phase 4: Adversarial Proofs and Polish - Research

**Researched:** 2026-03-17
**Domain:** Adversarial testing, deep verification expansion, documentation counters
**Confidence:** HIGH

## Summary

Phase 4 is the culmination of the v0.4.0 milestone. All new capabilities from Phases 1-3 (Ed25519 signing, dual-algorithm dispatch, temporal commitment with NIST Beacon) must now be proven through adversarial tests. The phase creates two new CERT test files (CERT-09, CERT-10), expands deep_verify.py from 10 to 13 tests, demonstrates 5-layer independence, and updates all documentation counters to reflect the v0.4.0 state.

The codebase has well-established patterns for adversarial gauntlet tests (CERT-05 with 5 attacks, CERT-07 with 13 signing tests, CERT-08 with 10 reproducibility proofs). Phase 4 follows these exact patterns -- no new test infrastructure or libraries needed. The primary technical risk is ensuring the 5-layer independence proof correctly constructs attacks that pass exactly 4 layers and fail only the target layer. The secondary concern is getting the counter updates right across 6+ files with 11+ locations in index.html alone.

**Primary recommendation:** Split into 3 plans: (1) CERT-09 + CERT-10 + deep_verify Tests 11-13, (2) 5-layer independence proof, (3) counter updates. Counter updates must be last since they depend on the final test count.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Test 11 (signing integrity): Sign bundle with Ed25519, verify PASS, tamper signature bytes, verify FAIL
- Test 12 (reproducibility): Same inputs produce identical Ed25519 signatures and trace hashes across runs
- Test 13 (temporal commitment): Sign with temporal commitment, verify Layer 5 PASS, tamper temporal_binding hash, verify FAIL
- All 3 deep_verify tests follow existing pattern: subprocess calls to mg.py/mg_sign.py, assert on PASS/FAIL, print [PASS]/[FAIL]
- Final line updated to "ALL 13 TESTS PASSED"
- CERT-09 file: `tests/steward/test_cert09_ed25519_attacks.py` with 5+ attack scenarios (wrong key, bit-flip, downgrade, type mismatch, truncated signature)
- CERT-10 file: `tests/steward/test_cert10_temporal_attacks.py` with 5+ attack scenarios (replay, future-date, beacon forge, binding tamper, pre-commitment tamper)
- 5-layer independence: matrix approach, each layer catches unique attack that passes other 4
- Counter updates: layers 3->5, innovations 6->7, dynamic test count, protocol version bump
- Files to update: index.html (11+), README.md, AGENTS.md, llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md
- scientific_claim_index.md updated with new capabilities (DOCS-03)
- paper.md references updated (DOCS-04)

### Claude's Discretion
- Internal structure of CERT-09 and CERT-10 (helper functions, fixtures)
- Whether 5-layer independence is its own test file or integrated into existing gauntlets
- Exact wording of deep_verify test output messages
- Order of documentation updates
- How to handle test count in system_manifest.json (hardcoded vs dynamic)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CERT-01 | deep_verify Test 11 -- bundle signing integrity proof | Existing deep_verify pattern (subprocess + assert + print), mg_sign.py Ed25519 sign/verify API |
| CERT-02 | deep_verify Test 12 -- cross-environment reproducibility proof | Existing CERT-08 determinism pattern, Ed25519 signing determinism property |
| CERT-03 | deep_verify Test 13 -- temporal commitment verification proof | mg_temporal.py create/verify API, mock beacon pattern from test_temporal.py |
| CERT-04 | 5-layer independence proof -- each layer catches attacks others miss | Existing CERT-05 gauntlet pattern extended to 5 layers, _verify_semantic + verify_bundle_signature + verify_temporal_commitment APIs |
| CERT-05 | CERT-09 signing attack gauntlet (Ed25519 attacks) | mg_ed25519.py sign/verify, mg_sign.py verify_bundle_signature with Ed25519 keys, downgrade attack prevention in verify_bundle_signature |
| CERT-06 | CERT-10 temporal attack gauntlet (temporal attacks) | mg_temporal.py verify_temporal_commitment, temporal_commitment.json structure, binding hash computation |
| DOCS-01 | All counter updates across 6+ files | Counter locations mapped: index.html 11+ places, system_manifest.json fields, README/AGENTS/llms.txt/CONTEXT_SNAPSHOT |
| DOCS-02 | system_manifest.json protocol version bump | Current: v0.3 protocol, 295 test_count, 7 innovations -- needs bump |
| DOCS-03 | scientific_claim_index.md updated | Current: v0.2, needs new capability entries for Ed25519 + temporal |
| DOCS-04 | paper.md references updated | Needs Innovation #7 citation, 5-layer architecture reference |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | (existing) | Test framework | Already used across 373 tests |
| hashlib | stdlib | SHA-256 for tampering/verification | Core to all attack simulations |
| json | stdlib | Bundle manifest/artifact manipulation | Required for attack construction |
| tempfile | stdlib | Temporary directories for bundle manipulation | Established pattern in CERT-05/07 |
| subprocess | stdlib | deep_verify test execution | Established deep_verify pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock | stdlib | NIST Beacon mocking for temporal tests | CERT-10 temporal attack scenarios that need predictable beacon values |
| pathlib | stdlib | File path manipulation | All test files |

No new dependencies required. stdlib-only constraint applies.

## Architecture Patterns

### Recommended Project Structure
```
tests/steward/
  test_cert09_ed25519_attacks.py    # NEW - Ed25519 attack gauntlet
  test_cert10_temporal_attacks.py   # NEW - Temporal attack gauntlet
scripts/
  deep_verify.py                    # MODIFIED - add Tests 11-13
```

### Pattern 1: Gauntlet Test Structure (from CERT-05)
**What:** Multiple attack scenarios in one test file, each as separate test function
**When to use:** CERT-09 and CERT-10
**Example:**
```python
# Source: tests/steward/test_cert05_adversarial_gauntlet.py
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

class TestAdversarialGauntlet:
    def test_attack1_name(self, tmp_path):
        """ATTACK: description. Layer N catches it."""
        # 1. Build valid bundle
        # 2. Apply attack (tamper specific field)
        # 3. Verify -> MUST return (False, msg) or nonzero exit
        # 4. Assert specific error message content

    def test_gauntlet_summary(self):
        """Composite proof: all attack classes documented."""
        coverage = { ... }
        assert len(coverage) == N
```

### Pattern 2: deep_verify Test Pattern (from existing Tests 1-10)
**What:** Sequential numbered tests using subprocess, print status, assert
**When to use:** Tests 11-13
**Example:**
```python
# Source: scripts/deep_verify.py
print("\n" + "=" * 60)
print("TEST N: description")
print("=" * 60)
r = subprocess.run([sys.executable, "scripts/mg_sign.py", "verify", ...],
                   capture_output=True, text=True, cwd=root)
# Assert on result
print(f"  {OK if condition else ERR} description")
assert condition
```

### Pattern 3: Verification Return Tuple
**What:** All verification functions return `(ok: bool, message: str)`
**When to use:** All test assertions against verify functions
**Example:**
```python
# verify_bundle_signature returns (bool, str)
ok, msg = verify_bundle_signature(bundle, key_path=key_file)
assert ok is False, "Attack was NOT detected"
assert "expected_keyword" in msg

# verify_temporal_commitment returns (bool, str)
ok, msg = verify_temporal_commitment(pack_dir)
assert ok is False
assert "temporal_binding hash mismatch" in msg
```

### Pattern 4: Bundle Construction Helper
**What:** Helper function to create minimal valid bundles for tampering
**When to use:** Both CERT-09 and CERT-10 need bundle construction
**Example:**
```python
# Source: test_cert07_bundle_signing.py
def _make_signed_bundle(tmp_path: Path) -> tuple[Path, dict]:
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    # Create evidence file, build manifest, sign
    return bundle, key_data
```

### Pattern 5: 5-Layer Independence Matrix
**What:** For each of 5 layers, construct an attack passing 4 others but failing target
**When to use:** CERT-04 requirement
**Key insight from codebase analysis:**
- Layer 1 (SHA-256): Modify file but update manifest hash -- bypasses L1 but semantic (L2) catches
- Layer 2 (Semantic): Strip job_snapshot but keep hashes valid -- L1 passes, L2 catches
- Layer 3 (Step Chain): Change result value, recompute evidence -- trace_root_hash mismatch
- Layer 4 (Signing): Construct valid 3-layer bundle without signing key -- L1-3 pass, L4 catches
- Layer 5 (Temporal): Replay temporal_commitment.json from different bundle -- L1-4 pass, L5 catches (binding hash won't match new root_hash)

### Anti-Patterns to Avoid
- **Hardcoding test counts in deep_verify:** Test 2 already uses dynamic count (`re.search(r'(\d+) passed', r.stdout)`). Continue this pattern.
- **Network calls in tests:** CERT-10 must mock the beacon. Never call real NIST Beacon in tests.
- **Modifying sealed files:** Never touch steward_audit.py, mg_policy_gate_policy.json, canonical_state.md per CLAUDE.md.
- **Updating counters before tests finalize:** Counter updates must happen LAST after all new tests are confirmed passing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bundle construction for tests | New helper from scratch | Reuse `_make_signed_bundle` pattern from CERT-07 and `_make_minimal_pack` from CERT-05 | These helpers handle manifest hash computation correctly |
| Ed25519 key generation for tests | Manual key bytes | `generate_key_files()` from mg_ed25519.py | Produces properly formatted key files with correct version field |
| Temporal commitment for tests | Manual JSON construction | `create_temporal_commitment()` with mocked beacon | Ensures correct binding hash computation |
| Counter search/replace in index.html | Manual editing | PowerShell batch replace per CLAUDE.md BUG 7 | index.html has 11+ counter locations including prose text |

## Common Pitfalls

### Pitfall 1: deep_verify hardcoded paths
**What goes wrong:** deep_verify.py uses `root = Path(r"C:\Users\999ye\Downloads\metagenesis-core-public")` -- hardcoded absolute path.
**Why it happens:** Existing code was written for specific environment.
**How to avoid:** Tests 11-13 must use the same `root` variable and `sys.executable` for subprocess calls.
**Warning signs:** Tests pass locally but fail in CI.

### Pitfall 2: Ed25519 vs HMAC algorithm detection
**What goes wrong:** CERT-09 downgrade attack test must correctly exercise the algorithm mismatch path in `verify_bundle_signature`.
**Why it happens:** The verify function checks `key_algo != sig_algo` -- bundle declares one algorithm, verifier key is another type.
**How to avoid:** Create bundle signed with Ed25519, then try to verify with HMAC key (and vice versa). The `_detect_algorithm` function reads the `version` field.
**Warning signs:** Test passes but doesn't actually exercise the downgrade prevention code path.

### Pitfall 3: Temporal binding computation order
**What goes wrong:** CERT-10 tests must construct the binding hash in the exact order: `pre_commitment_hash + beacon_output_value + beacon_timestamp`.
**Why it happens:** SHA-256 of concatenated strings is order-dependent.
**How to avoid:** Reference `create_temporal_commitment()` source for exact concatenation order.
**Warning signs:** "Valid" temporal commitment fails verification.

### Pitfall 4: Counter update atomicity
**What goes wrong:** Updating some files but not others leaves inconsistent state.
**Why it happens:** 6+ files with counters, easy to miss one.
**How to avoid:** Use a checklist and verify all files in a single plan step. Run deep_verify Test 7 (site numbers match code) to catch mismatches.
**Warning signs:** deep_verify Test 7 fails after counter updates.

### Pitfall 5: Test 7 in deep_verify checks specific counter values
**What goes wrong:** Current Test 7 asserts `">3<" in html` for layers and `"v0.2" in manifest["protocol"]`.
**Why it happens:** These assertions are hardcoded for v0.3.0 state.
**How to avoid:** Test 7 must be updated alongside counter updates to check for new values (5 layers, v0.4 protocol).
**Warning signs:** deep_verify fails on Test 7 after counter updates because assertions still check old values.

### Pitfall 6: system_manifest.json innovation list
**What goes wrong:** The `verified_innovations` array needs a new entry for temporal commitment.
**Why it happens:** Easy to update test_count but forget innovation list.
**How to avoid:** Add `"temporal_commitment_nist_beacon"` (or similar) to the array. Current array has 7 entries, should become 8.
**Warning signs:** Innovation count in index.html doesn't match manifest.

## Code Examples

### CERT-09: Ed25519 Wrong Key Attack
```python
# Pattern from test_cert07, adapted for Ed25519
from scripts.mg_ed25519 import generate_key_files
from scripts.mg_sign import sign_bundle, verify_bundle_signature

def test_attack1_wrong_key_verification(self, tmp_path):
    """Sign with key A, verify with key B -> FAIL."""
    bundle = _make_ed25519_signed_bundle(tmp_path, "key_a")
    key_b_path = tmp_path / "key_b.json"
    generate_key_files(key_b_path)
    pub_b_path = tmp_path / "key_b.pub.json"
    ok, msg = verify_bundle_signature(bundle, key_path=pub_b_path)
    assert ok is False
    assert "fingerprint" in msg.lower() or "mismatch" in msg.lower()
```

### CERT-09: Downgrade Attack
```python
def test_attack3_downgrade_ed25519_to_hmac(self, tmp_path):
    """Ed25519-signed bundle verified with HMAC key -> FAIL (algorithm mismatch)."""
    bundle = _make_ed25519_signed_bundle(tmp_path, "ed_key")
    # Generate HMAC key
    from scripts.mg_sign import generate_key
    hmac_key = generate_key()
    hmac_key_file = tmp_path / "hmac_key.json"
    hmac_key_file.write_text(json.dumps(hmac_key, indent=2))
    ok, msg = verify_bundle_signature(bundle, key_path=hmac_key_file)
    assert ok is False
    assert "algorithm mismatch" in msg.lower() or "downgrade" in msg.lower()
```

### CERT-10: Replay Attack
```python
def test_attack1_replay_temporal(self, tmp_path):
    """Copy temporal_commitment.json from bundle A to bundle B -> binding check fails."""
    # Bundle A
    bundle_a = _make_bundle_with_temporal(tmp_path / "a", root_hash="a"*64)
    tc_a = json.loads((bundle_a / "temporal_commitment.json").read_text())

    # Bundle B (different root_hash)
    bundle_b = _make_bundle_with_temporal(tmp_path / "b", root_hash="b"*64)

    # ATTACK: copy A's temporal commitment to B
    (bundle_b / "temporal_commitment.json").write_text(json.dumps(tc_a))

    ok, msg = verify_temporal_commitment(bundle_b)
    assert ok is False
    assert "pre_commitment_hash does not match" in msg
```

### deep_verify Test 11 Pattern
```python
print("\n" + "=" * 60)
print("TEST 11: Ed25519 signing integrity")
print("=" * 60)
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    # 1. Generate Ed25519 key pair
    key_path = tmp / "test_key.json"
    subprocess.run([sys.executable, str(root / "scripts/mg_sign.py"),
                    "keygen", "--out", str(key_path), "--type", "ed25519"],
                   capture_output=True, text=True, cwd=root)
    # 2. Create minimal bundle, sign it
    # 3. Verify PASS
    # 4. Tamper signature bytes
    # 5. Verify FAIL
    print(f"  {OK} Ed25519 signing integrity proven")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 3 verification layers | 5 verification layers | v0.4.0 (Phase 1-3) | Layer 4 (signing) + Layer 5 (temporal) added |
| HMAC-only signing | Dual HMAC+Ed25519 | v0.4.0 Phase 1-2 | Asymmetric signing for third-party audits |
| 10 deep_verify tests | 13 deep_verify tests | v0.4.0 Phase 4 | Tests 11-13 cover signing, reproducibility, temporal |
| 295 pytest tests | ~373+ pytest tests | v0.4.0 Phases 1-3 | Ed25519 + temporal + signing upgrade tests added |
| 6 innovations | 7 innovations | v0.4.0 Phase 3 | Innovation #7: Temporal Commitment |

**Current test count:** 373 tests collected (as of Phase 3 completion). CERT-09 and CERT-10 will add approximately 12-15 more tests, bringing total to ~385-390.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | existing pytest configuration in repo |
| Quick run command | `python -m pytest tests/steward/test_cert09_ed25519_attacks.py tests/steward/test_cert10_temporal_attacks.py -q` |
| Full suite command | `python -m pytest tests/ -q && python scripts/deep_verify.py` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CERT-01 | deep_verify Test 11 signing integrity | integration | `python scripts/deep_verify.py` (checks all 13) | Modify existing |
| CERT-02 | deep_verify Test 12 reproducibility | integration | `python scripts/deep_verify.py` | Modify existing |
| CERT-03 | deep_verify Test 13 temporal commitment | integration | `python scripts/deep_verify.py` | Modify existing |
| CERT-04 | 5-layer independence proof | unit | `python -m pytest tests/steward/test_cert09_ed25519_attacks.py -k independence -x` or separate file | Wave 0 |
| CERT-05 | CERT-09 Ed25519 attack gauntlet | unit | `python -m pytest tests/steward/test_cert09_ed25519_attacks.py -x` | Wave 0 |
| CERT-06 | CERT-10 temporal attack gauntlet | unit | `python -m pytest tests/steward/test_cert10_temporal_attacks.py -x` | Wave 0 |
| DOCS-01 | Counter updates | integration | `python scripts/deep_verify.py` (Test 7 checks site numbers) | Existing |
| DOCS-02 | system_manifest.json version bump | integration | `python scripts/deep_verify.py` (Test 7) | Existing |
| DOCS-03 | scientific_claim_index.md | manual-only | Visual review | Existing |
| DOCS-04 | paper.md references | manual-only | Visual review | Existing |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/steward/ -q --tb=short`
- **Per wave merge:** `python -m pytest tests/ -q && python scripts/deep_verify.py`
- **Phase gate:** Full suite green + all 13 deep_verify tests PASS

### Wave 0 Gaps
- [ ] `tests/steward/test_cert09_ed25519_attacks.py` -- covers CERT-05, partially CERT-04
- [ ] `tests/steward/test_cert10_temporal_attacks.py` -- covers CERT-06, partially CERT-04
- [ ] deep_verify.py Tests 11-13 -- covers CERT-01, CERT-02, CERT-03

## Open Questions

1. **Test 7 in deep_verify needs updating alongside counters**
   - What we know: Test 7 currently asserts `">3<" in html` for layers and `"v0.2" in manifest["protocol"]`
   - What's unclear: Should Test 7 be updated in the same plan as counter updates, or separately?
   - Recommendation: Update Test 7 assertions in the same commit as counter updates to keep deep_verify passing atomically

2. **5-layer independence proof: separate file or integrated?**
   - What we know: User says "Claude's discretion" on organization
   - What's unclear: Whether to add to CERT-09/CERT-10 or create a separate test_cert_5layer_independence.py
   - Recommendation: Integrate into CERT-09 and CERT-10 since they already test Layer 4 and Layer 5 respectively, and add a summary test that documents the full 5-layer matrix. Alternatively, a single dedicated class `TestFiveLayerIndependence` in one of the files provides clearer documentation of the architectural proof.

3. **system_manifest.json protocol version**
   - What we know: Currently "MetaGenesis Verification Protocol (MVP) v0.3", needs bump
   - What's unclear: Should it become "v0.4" or "v0.4.0"?
   - Recommendation: Use "v0.4" to match existing format pattern

## Sources

### Primary (HIGH confidence)
- `scripts/deep_verify.py` -- existing 10 tests, pattern for Tests 11-13
- `tests/steward/test_cert05_adversarial_gauntlet.py` -- gauntlet pattern with 5 attacks
- `tests/steward/test_cert07_bundle_signing.py` -- signing test helpers and patterns
- `tests/steward/test_cert08_reproducibility.py` -- reproducibility proof pattern
- `scripts/mg_sign.py` -- sign_bundle, verify_bundle_signature, Ed25519 dispatch
- `scripts/mg_temporal.py` -- create/verify temporal commitment
- `scripts/mg_ed25519.py` -- Ed25519 sign/verify/generate_key_files
- `tests/steward/test_temporal.py` -- temporal mock beacon pattern
- `tests/steward/test_ed25519.py` -- Ed25519 test patterns
- `scripts/mg.py` -- _verify_semantic, _verify_pack, Layer 5 integration
- `system_manifest.json` -- current counters and fields

### Secondary (MEDIUM confidence)
- `index.html` counter locations (grep confirmed 11+ locations)
- Test count of 373 (confirmed via `pytest --co`)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all stdlib + pytest
- Architecture: HIGH - all patterns established in CERT-05/07/08, direct reuse
- Pitfalls: HIGH - identified from reading actual source code and existing test patterns
- Counter updates: MEDIUM - index.html has many locations, PowerShell batch replace recommended but exact count needs verification during implementation

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable -- project internals, no external dependency changes)
