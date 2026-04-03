# Phase 7: Flagship Proofs - Research

**Researched:** 2026-03-18
**Domain:** Adversarial test design for 5-layer cryptographic verification protocol
**Confidence:** HIGH

## Summary

Phase 7 creates two flagship adversarial proof files: CERT-11 (coordinated multi-vector attack proving 5-layer independence) and CERT-12 (encoding attack vectors). This is a tests-only phase with no production code changes. The codebase already has extensive adversarial test infrastructure (CERT-01 through CERT-10 plus test_cert_5layer_independence.py) with well-established patterns for constructing attack bundles, calling layer-specific verify functions, and asserting which layer caught the attack.

Key research findings: (1) `_make_full_5layer_bundle()` and `_rebuild_manifest()` in test_cert_5layer_independence.py are the primary reusable helpers for CERT-11; (2) Python's `json.loads()` already rejects BOM-prefixed and null-byte-containing JSON, so CERT-12 encoding tests will verify the protocol gracefully catches these via JSONDecodeError in `_verify_semantic` and `_verify_pack`; (3) `canonicalize_bytes()` does NOT strip BOM bytes, meaning BOM-prefixed files produce different SHA-256 hashes (Layer 1 integrity catch); (4) Unicode homoglyphs are same-length strings but fail Python string equality, so claim ID matching naturally rejects them.

**Primary recommendation:** Build CERT-11 as an escalating attacker series reusing `_make_full_5layer_bundle` + `_rebuild_manifest`, and CERT-12 using `write_bytes()` to inject exact byte sequences into otherwise-valid bundles.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Each CERT-11 test scenario MUST assert WHICH specific layer caught the attack, not just that verification failed
- Pattern: construct a pack that is valid at all layers BELOW the target, corrupted at the target layer
- Call the targeted layer's verify function directly (e.g., `_verify_semantic()`) to prove it fails
- Also call full `_verify_pack()` to prove end-to-end detection
- ADV-01: Attacker rebuilds Layer 1 (valid SHA-256) + fakes Layer 2 -> assert Layer 2 catches it (semantic failure), Layer 1 passes
- ADV-02: Attacker rebuilds Layers 1+2 + forges Layer 3 -> assert Layer 3 catches it (step chain mismatch), Layers 1+2 pass
- ADV-03: Stolen signing key + tampered evidence -> assert Layers 1-3 catch it (signature valid but content integrity fails)
- ADV-04: Coordinated 3-layer bypass -> assert remaining layers still detect the tampering
- ADV-05 (BOM): Write BOM-prefixed evidence_index.json -> test that fingerprint_file / integrity check detects the difference
- ADV-06 (null bytes): Inject null bytes into field values in evidence_index.json -> test rejection
- ADV-06 (truncated JSON): Write truncated JSON (missing closing braces) -> test parsing failure is caught gracefully
- ADV-06 (homoglyphs): Replace ASCII characters in claim IDs with Unicode lookalikes -> test that verification fails
- All encoding tests should use `write_bytes()` to control exact byte content
- New file: `tests/steward/test_cert11_coordinated_attack.py`
- New file: `tests/steward/test_cert12_encoding_attacks.py`
- Follow established CERT-XX naming pattern
- Each file has module-level docstring explaining the attack thesis being proved

### Claude's Discretion
- Exact number of test methods within each CERT file (aim for comprehensive coverage of each ADV requirement)
- Helper function structure (_make_pack variants for each scenario)
- Whether ADV-04 needs a single "ultimate" test or multiple sub-scenarios
- How to simulate temporal commitment bypass for ADV-04 (mock vs synthetic)
- Specific Unicode homoglyph characters to use in ADV-06

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ADV-01 | CERT-11 proves attacker who rebuilds Layer 1 + fakes Layer 2 is caught by Layer 2 | Use `_make_full_5layer_bundle` + `_rebuild_manifest` to construct valid L1, then strip `job_snapshot`. Call `_verify_semantic` directly to prove L2 failure. |
| ADV-02 | CERT-11 proves attacker who rebuilds Layers 1+2 + forges Layer 3 is caught by Layer 3 | Modify `trace_root_hash` to mismatch final step hash. L1 passes (manifest rebuilt), L2 passes (job_snapshot intact), L3 fails on `trace_root_hash != last_hash`. |
| ADV-03 | CERT-11 proves stolen signing key with tampered evidence is caught by Layers 1-3 | Sign bundle with valid key, then tamper evidence. L4 signature still valid (signed_root_hash matches OLD root_hash). But L1 catches SHA mismatch OR rebuild manifest and L2/L3 catch semantic/chain tampering. |
| ADV-04 | CERT-11 proves coordinated 3-layer bypass still fails at remaining layers | Bypass L1+L2+L3 simultaneously, L4 catches (signed_root_hash mismatch after manifest rebuild) OR L5 catches (pre_commitment_hash mismatch). Use mock beacon for L5. |
| ADV-05 | CERT-12 proves BOM-prefixed files are detected or handled safely | `json.loads()` rejects BOM (JSONDecodeError). `canonicalize_bytes()` preserves BOM so SHA-256 differs. Both L1 and semantic parsing catch this. |
| ADV-06 | CERT-12 proves null bytes / truncated JSON / homoglyphs are caught | `json.loads()` rejects null bytes and truncated JSON. Homoglyphs pass JSON parsing but fail claim ID string equality. |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | (existing) | Test framework | Already used for all 498 tests in codebase |
| unittest.mock | stdlib | Mocking NIST Beacon for temporal tests | Used in test_cert_5layer_independence.py |
| hashlib | stdlib | SHA-256 computation for attack bundles | Core protocol dependency |
| json | stdlib | JSON serialization for evidence artifacts | Core protocol dependency |
| pathlib | stdlib | File system operations for pack construction | Standard in all CERT tests |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tempfile | stdlib | Isolated test directories | Via pytest `tmp_path` fixture |

**No new dependencies required.** This phase uses only existing stdlib and pytest.

## Architecture Patterns

### Recommended Test File Structure
```
tests/steward/
  test_cert11_coordinated_attack.py    # CERT-11: 5-layer coordinated attack gauntlet
  test_cert12_encoding_attacks.py      # CERT-12: encoding and corruption attacks
```

### Pattern 1: Escalating Attacker Series (CERT-11)
**What:** Each test represents a progressively more sophisticated attacker who has overcome the previous layer's protection. Tests build valid bundles at all layers below the target, then corrupt the target layer.
**When to use:** CERT-11 ADV-01 through ADV-04
**Example:**
```python
# Source: test_cert_5layer_independence.py (verified in codebase)
def test_adv01_layer2_catches_semantic_bypass(self, tmp_path):
    """ADV-01: Attacker rebuilds L1, but L2 catches stripped evidence."""
    bundle, key_path, pub_key_path = _make_full_5layer_bundle(tmp_path)

    # ATTACK: Strip job_snapshot (L2 target)
    run_path = list(bundle.rglob("run_artifact.json"))[0]
    data = json.loads(run_path.read_text(encoding="utf-8"))
    del data["job_snapshot"]
    run_path.write_text(json.dumps(data), encoding="utf-8")

    # Rebuild manifest to bypass L1
    _rebuild_manifest(bundle)

    # Assert L2 specifically catches it
    ei_path = bundle / "evidence_index.json"
    ok, msg, errors = _verify_semantic(bundle, ei_path)
    assert not ok
    assert "job_snapshot" in msg
```

### Pattern 2: Byte-Level Injection (CERT-12)
**What:** Use `write_bytes()` to inject exact byte sequences into otherwise-valid JSON files, bypassing Python's text encoding normalization.
**When to use:** CERT-12 ADV-05 and ADV-06
**Example:**
```python
# Source: verified via Python REPL testing
def test_adv05_bom_prefixed_evidence(self, tmp_path):
    """ADV-05: BOM-prefixed evidence_index.json is caught."""
    bundle, _, _ = _make_full_5layer_bundle(tmp_path)
    ei_path = bundle / "evidence_index.json"

    # Inject BOM prefix
    original = ei_path.read_bytes()
    ei_path.write_bytes(b'\xef\xbb\xbf' + original)

    # Rebuild manifest (L1 passes with new SHA)
    _rebuild_manifest(bundle)

    # json.loads rejects BOM -> semantic check fails
    ok, msg, errors = _verify_semantic(bundle, ei_path)
    assert not ok
    assert "evidence_index.json" in msg
```

### Pattern 3: Dual Assertion (Layer Attribution)
**What:** Every CERT-11 test asserts BOTH (a) which specific layer caught the attack by calling the layer function directly, AND (b) full `_verify_pack()` end-to-end detection.
**When to use:** All CERT-11 scenarios
**Example:**
```python
# Layer-specific assertion
ok_l2, msg_l2, _ = _verify_semantic(bundle, ei_path)
assert not ok_l2, "Layer 2 should catch this"

# End-to-end assertion
ok_full, msg_full, report = _verify_pack(bundle)
assert not ok_full, "Full verification should also catch this"
```

### Anti-Patterns to Avoid
- **Testing only pass/fail without layer attribution:** Every CERT-11 test MUST identify which layer caught the attack, not just assert failure.
- **Using `write_text()` for encoding attacks:** BOM and null byte tests MUST use `write_bytes()` to control exact byte content.
- **Rebuilding manifest incorrectly:** Always use `_rebuild_manifest()` helper (from test_cert_5layer_independence.py) which correctly recomputes file hashes and root_hash.
- **Forgetting to re-sign after manifest rebuild:** If L4 should pass, must re-sign after `_rebuild_manifest()`. If L4 should catch, do NOT re-sign.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Valid 5-layer bundle construction | Custom bundle builder | `_make_full_5layer_bundle()` from test_cert_5layer_independence.py | Already handles evidence, manifest, signing, temporal with mock beacon |
| Manifest hash recomputation | Manual SHA-256 loop | `_rebuild_manifest()` from test_cert_5layer_independence.py | Correctly handles file ordering, root_hash computation |
| Valid step chain construction | Manual hash chain | `_build_valid_trace()` from test_cert_5layer_independence.py | Produces correct 4-step trace with valid hash linkage |
| Ed25519 key generation | Custom key code | `generate_key_files()` from mg_ed25519 | Produces key + pub key pair for signing tests |
| Temporal commitment mocking | Real beacon calls | `unittest.mock.patch("scripts.mg_temporal._fetch_beacon_pulse")` | Deterministic, no network dependency |

**Key insight:** The test_cert_5layer_independence.py file already provides ALL the bundle construction and manipulation helpers needed. Import and reuse -- do not duplicate.

## Common Pitfalls

### Pitfall 1: Manifest Not Rebuilt After Evidence Tampering
**What goes wrong:** Test modifies evidence file but doesn't rebuild manifest, so L1 catches it instead of the intended layer.
**Why it happens:** Developer forgets that L1 checks raw file SHA-256 against manifest hashes.
**How to avoid:** After ANY evidence file modification, call `_rebuild_manifest(bundle)` to bypass L1 if testing L2/L3/L4/L5.
**Warning signs:** Test error message mentions "SHA256 mismatch" when L2/L3 was the intended catch layer.

### Pitfall 2: Signature Invalidated by Manifest Rebuild
**What goes wrong:** After `_rebuild_manifest()`, the root_hash changes, so `signed_root_hash` in bundle_signature.json no longer matches. L4 catches this even though L4 wasn't the intended test target.
**Why it happens:** `_rebuild_manifest()` produces a new root_hash. The signature was computed over the old root_hash.
**How to avoid:** If L4 should pass, must re-sign after rebuild: `sign_bundle(bundle, key_path)`. If testing L4, deliberately do NOT re-sign.
**Warning signs:** Test fails with "bundle was modified after signing" when targeting L2 or L3.

### Pitfall 3: Temporal Commitment Pre-Hash Mismatch
**What goes wrong:** After manifest rebuild, `pre_commitment_hash` (SHA-256 of old root_hash) no longer matches the new root_hash. L5 catches it unexpectedly.
**Why it happens:** Temporal commitment was created with old root_hash.
**How to avoid:** If L5 should pass, recreate temporal commitment after rebuild. If testing L5, deliberately keep old commitment.
**Warning signs:** "pre_commitment_hash does not match root_hash" when targeting L2 or L3.

### Pitfall 4: BOM Handling in read_text vs read_bytes
**What goes wrong:** Using `read_text(encoding="utf-8")` then `json.loads()` -- the BOM character is decoded to U+FEFF which json.loads rejects. Using `read_text(encoding="utf-8-sig")` would silently strip the BOM.
**Why it happens:** Python's utf-8-sig codec strips BOM; utf-8 preserves it.
**How to avoid:** The codebase uses `encoding="utf-8"` consistently (not "utf-8-sig"), which means BOM IS detected. CERT-12 should verify this behavior continues.
**Warning signs:** BOM test passes when it shouldn't (someone changed encoding to utf-8-sig).

### Pitfall 5: Homoglyph Claims Pass JSON Parsing
**What goes wrong:** Developer expects JSON parsing to reject homoglyphs -- it won't. JSON accepts any valid Unicode string.
**Why it happens:** Homoglyphs are valid Unicode characters; JSON has no concept of "expected character range."
**How to avoid:** Homoglyph detection happens at the claim ID comparison level, not JSON parsing. Test should verify that a homoglyph claim ID does NOT match any known claim, causing verification to fail at the semantic level (claim not found / job_kind mismatch).
**Warning signs:** Test asserts JSONDecodeError for homoglyphs (wrong -- will get assertion error).

### Pitfall 6: ADV-03 Attack Vector Design
**What goes wrong:** Developer assumes "stolen signing key" means L4 fails -- it doesn't. If the attacker HAS the key, they can re-sign. The attack is: valid signature but tampered evidence underneath.
**Why it happens:** Misunderstanding the threat model. ADV-03's point is that signing alone is insufficient.
**How to avoid:** ADV-03 should: (1) create valid bundle, (2) tamper evidence, (3) rebuild manifest, (4) re-sign with stolen key. Now L4 passes (valid signature) but L2/L3 catch the content tampering.
**Warning signs:** ADV-03 test only checks L4 -- misses the point that L1-3 are the actual defenders.

## Code Examples

### Importing Shared Helpers
```python
# Source: test_cert_5layer_independence.py (codebase)
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.mg import _verify_pack, _verify_semantic
from scripts.mg_sign import sign_bundle, verify_bundle_signature, SIGNATURE_FILE
from scripts.mg_ed25519 import generate_key_files
from scripts.mg_temporal import (
    create_temporal_commitment, verify_temporal_commitment,
    write_temporal_commitment, TEMPORAL_FILE,
)

# Import the helper functions from existing test file
from tests.steward.test_cert_5layer_independence import (
    _make_full_5layer_bundle,
    _rebuild_manifest,
    _build_valid_trace,
    _hash_step,
)
```

Note: If importing from another test file causes issues (e.g., pytest collection), copy the helper functions directly instead. The functions are ~30 lines each and self-contained.

### ADV-04 Crown Jewel Pattern (Coordinated 3-Layer Bypass)
```python
# Conceptual pattern for ADV-04
def test_adv04_coordinated_3layer_bypass(self, tmp_path):
    """
    ATTACK: Bypass L1+L2+L3 simultaneously.
    Attacker rebuilds manifest (L1), keeps semantic fields intact (L2),
    forges a valid-looking step chain with matching trace_root_hash (L3).

    Layer 4 (signature) catches: signed_root_hash no longer matches.
    Layer 5 (temporal) catches: pre_commitment_hash no longer matches.
    """
    bundle, key_path, pub_key_path = _make_full_5layer_bundle(tmp_path)

    # Build a completely new trace with different data (bypass L3)
    new_trace, new_root_hash = _build_valid_trace()
    # Modify evidence to use new trace (bypass L2 - keep all required fields)
    run_path = list(bundle.rglob("run_artifact.json"))[0]
    data = json.loads(run_path.read_text(encoding="utf-8"))
    data["job_snapshot"]["result"]["execution_trace"] = new_trace
    data["job_snapshot"]["result"]["trace_root_hash"] = new_root_hash
    run_path.write_text(json.dumps(data), encoding="utf-8")

    # Rebuild manifest (bypass L1)
    new_root = _rebuild_manifest(bundle)
    # DO NOT re-sign (L4 catches) and DO NOT update temporal (L5 catches)

    # L4: signed_root_hash mismatches new root_hash
    ok_l4, msg_l4 = verify_bundle_signature(bundle, key_path=pub_key_path)
    assert not ok_l4
    assert "modified after signing" in msg_l4

    # L5: pre_commitment_hash mismatches new root_hash
    ok_l5, msg_l5 = verify_temporal_commitment(bundle)
    assert not ok_l5
    assert "pre_commitment_hash" in msg_l5
```

### CERT-12 BOM Attack (Verified Behavior)
```python
# Source: verified via Python REPL 2026-03-18
# json.loads() rejects BOM with: "Unexpected UTF-8 BOM (decode using utf-8-sig)"
# canonicalize_bytes() preserves BOM (does NOT strip it)
# _verify_pack uses hashlib.sha256(fp.read_bytes()) -- raw bytes, not canonicalized

def test_adv05_bom_in_evidence_index(self, tmp_path):
    """ADV-05: BOM-prefixed evidence_index.json causes JSONDecodeError in semantic check."""
    bundle, _, _ = _make_full_5layer_bundle(tmp_path)
    ei_path = bundle / "evidence_index.json"

    # Inject UTF-8 BOM at start of file
    original_bytes = ei_path.read_bytes()
    ei_path.write_bytes(b'\xef\xbb\xbf' + original_bytes)

    # Rebuild manifest so L1 passes
    _rebuild_manifest(bundle)

    # L2 (_verify_semantic) reads file with encoding="utf-8" and json.loads fails
    ok, msg, _ = _verify_semantic(bundle, ei_path)
    assert not ok
    assert "evidence_index.json" in msg.lower() or "bom" in msg.lower() or "json" in msg.lower()
```

### CERT-12 Null Byte Attack (Verified Behavior)
```python
# json.loads() rejects null bytes with: "Invalid control character at..."

def test_adv06_null_bytes_in_evidence(self, tmp_path):
    """ADV-06: Null bytes in run_artifact.json cause JSONDecodeError."""
    bundle, _, _ = _make_full_5layer_bundle(tmp_path)
    run_path = list(bundle.rglob("run_artifact.json"))[0]

    # Inject null byte into JSON content
    original = run_path.read_bytes()
    corrupted = original.replace(b'"success"', b'"succ\x00ess"')
    run_path.write_bytes(corrupted)

    # Rebuild manifest so L1 passes
    _rebuild_manifest(bundle)

    # _verify_semantic will hit json.JSONDecodeError when loading run_artifact
    ei_path = bundle / "evidence_index.json"
    ok, msg, _ = _verify_semantic(bundle, ei_path)
    assert not ok
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 3-layer verification (L1+L2+L3) | 5-layer verification (+ Ed25519 signing + temporal commitment) | v0.4.0 | CERT-11 must prove all 5 layers, not just 3 |
| CERT-05: 5 attacks, 3 layers | CERT-11: coordinated multi-vector, 5 layers | Phase 7 | Escalating sophistication, layer attribution |
| HMAC-only signing | HMAC + Ed25519 dual mode | v0.4.0 | ADV-03/04 tests should work with Ed25519 keys (codebase default) |
| No temporal commitment | NIST Beacon pre-commitment | v0.4.0 | ADV-04 must test L5 catch via mock beacon |

## Open Questions

1. **ADV-04: Single ultimate test or multiple sub-scenarios?**
   - What we know: ADV-04 is the "crown jewel" -- attacker bypasses 3 layers simultaneously
   - What's unclear: Whether one test suffices or multiple scenarios (L1+L2+L3 bypass caught by L4; L1+L2+L3 bypass caught by L5; both L4+L5 catch simultaneously)
   - Recommendation: Multiple sub-tests -- one proving L4 catches when L1+L2+L3 bypassed, one proving L5 catches, and one proving even bypassing L1+L2+L3+L4 (re-sign with stolen key) is still caught by L5

2. **Importing helpers from test_cert_5layer_independence.py**
   - What we know: The helpers (`_make_full_5layer_bundle`, `_rebuild_manifest`, `_build_valid_trace`) are defined as module-level functions
   - What's unclear: Whether pytest will have issues importing from another test file
   - Recommendation: Copy the helpers into each new test file (they're ~30 lines each) to avoid cross-test-file import fragility

3. **ADV-05 BOM: test at evidence_index.json level or run_artifact.json level?**
   - What we know: Both files are loaded via `json.loads(path.read_text(encoding="utf-8"))` -- both reject BOM
   - What's unclear: CONTEXT.md says "evidence_index.json" specifically
   - Recommendation: Test BOM on evidence_index.json (as specified) plus optionally on run_artifact.json for completeness

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | No pytest.ini (uses defaults) |
| Quick run command | `python -m pytest tests/steward/test_cert11_coordinated_attack.py tests/steward/test_cert12_encoding_attacks.py -v` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADV-01 | L2 catches L1-rebuilt + semantic-faked attack | unit | `python -m pytest tests/steward/test_cert11_coordinated_attack.py -k adv01 -x` | Wave 0 |
| ADV-02 | L3 catches L1+L2-rebuilt + forged step chain | unit | `python -m pytest tests/steward/test_cert11_coordinated_attack.py -k adv02 -x` | Wave 0 |
| ADV-03 | L1-3 catch stolen-key + tampered evidence | unit | `python -m pytest tests/steward/test_cert11_coordinated_attack.py -k adv03 -x` | Wave 0 |
| ADV-04 | Remaining layers catch 3-layer coordinated bypass | unit | `python -m pytest tests/steward/test_cert11_coordinated_attack.py -k adv04 -x` | Wave 0 |
| ADV-05 | BOM-prefixed files detected | unit | `python -m pytest tests/steward/test_cert12_encoding_attacks.py -k bom -x` | Wave 0 |
| ADV-06 | Null/truncated/homoglyph caught | unit | `python -m pytest tests/steward/test_cert12_encoding_attacks.py -k "null or truncat or homoglyph" -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/steward/test_cert11_coordinated_attack.py tests/steward/test_cert12_encoding_attacks.py -v`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/steward/test_cert11_coordinated_attack.py` -- covers ADV-01, ADV-02, ADV-03, ADV-04
- [ ] `tests/steward/test_cert12_encoding_attacks.py` -- covers ADV-05, ADV-06

No framework install needed -- pytest and all dependencies already in place (498 tests passing).

## Sources

### Primary (HIGH confidence)
- `scripts/mg.py` _verify_pack (lines 51-168) -- full verification pipeline, Layer 1+2+3+5 checks, directly read
- `scripts/mg.py` _verify_semantic (lines 177-330) -- Layer 2 semantic verification, all field checks, directly read
- `scripts/mg_sign.py` verify_bundle_signature (lines 230-363) -- Layer 4 signature verification, directly read
- `scripts/mg_temporal.py` verify_temporal_commitment (lines 95-138) -- Layer 5 temporal check, directly read
- `tests/steward/test_cert_5layer_independence.py` -- Existing 5-layer helpers, directly read
- `tests/steward/test_cert05_adversarial_gauntlet.py` -- CERT-05 patterns, directly read
- `backend/progress/data_integrity.py` canonicalize_bytes -- BOM/CRLF handling, directly read
- Python REPL verification -- BOM, null byte, truncated JSON, homoglyph behavior confirmed via live testing

### Secondary (MEDIUM confidence)
- None

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, all existing
- Architecture: HIGH -- all helpers and patterns verified by reading source code and running live tests
- Pitfalls: HIGH -- each pitfall verified by tracing code paths through mg.py verify pipeline

**Research date:** 2026-03-18
**Valid until:** Stable -- these are test patterns against existing protocol code (60+ days)
