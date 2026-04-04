# Phase 2: Signing Upgrade - Research

**Researched:** 2026-03-17
**Domain:** Dual-algorithm bundle signing (Ed25519 + HMAC-SHA256 backward compatibility)
**Confidence:** HIGH

## Summary

Phase 2 integrates the Phase 1 Ed25519 implementation (`scripts/mg_ed25519.py`) into the existing bundle signing system (`scripts/mg_sign.py`) while preserving full backward compatibility with HMAC-SHA256-signed bundles from v0.3.0. The core challenge is a clean dual-algorithm dispatch: the `version` field in key files (`"hmac-sha256-v1"` vs `"ed25519-v1"`) determines which algorithm is used for signing and verification, and the verifier must reject algorithm mismatches to prevent downgrade attacks.

The existing `mg_sign.py` is well-structured with clear separation between key management, signing, and verification. The upgrade requires modifying `sign_bundle()` to dispatch on key version, modifying `verify_bundle_signature()` to dispatch on key version AND validate against the bundle's declared version, and updating the CLI to accept Ed25519 keys seamlessly. The `bundle_signature.json` format gains a new version value (`"ed25519-v1"`) but the schema is unchanged. The `mg.py` CLI integration (lines 476-523) imports from `mg_sign` via lazy imports and needs no structural changes -- it just needs to pass through Ed25519 keys.

**Primary recommendation:** Modify `mg_sign.py` to add Ed25519 dispatch alongside HMAC, using the key file `version` field as the single discriminator. The bundle signature `version` field records which algorithm was used. Verification checks that the verifier's key type matches the bundle's declared algorithm type before proceeding -- any mismatch is an immediate rejection (downgrade attack prevention).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SIGN-03 | Bundle signing with Ed25519 private key produces verifiable signature | `sign_bundle()` dispatches on key version field; Ed25519 signs `root_hash.encode("utf-8")` using `mg_ed25519.sign()`, stores 128-char hex signature in same `bundle_signature.json` format |
| SIGN-04 | Signature verification with Ed25519 public key confirms bundle authenticity | `verify_bundle_signature()` dispatches on key version; Ed25519 path uses `mg_ed25519.verify()` with public key from key file; public-only key files (`.pub.json`) work for verification |
| SIGN-06 | Dual-algorithm auto-detection from key file version field | `load_key()` reads `version` field; `"hmac-sha256-v1"` routes to HMAC path, `"ed25519-v1"` routes to Ed25519 path; unknown versions are rejected with clear error |
| SIGN-07 | Existing HMAC-signed bundles continue to verify without modification | HMAC verification path is unchanged; existing `bundle_signature.json` files with `"version": "hmac-sha256-v1"` continue to work with HMAC keys as before |
| SIGN-08 | Downgrade attack prevention -- verifier's key type is authoritative | Before computing any signature, verification checks that the key's version matches the bundle signature's version; a mismatch (e.g., HMAC key vs Ed25519-signed bundle) is an immediate FAIL with "algorithm mismatch" error |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11 | Runtime | Already in use throughout project |
| `scripts/mg_ed25519.py` | Phase 1 output | Ed25519 sign/verify/generate_keypair | Pure-Python, stdlib-only, RFC 8032 validated |
| `scripts/mg_sign.py` | v0.3.0 | Bundle signing (HMAC path, being extended) | Existing module, minimal modification |
| hashlib (stdlib) | ships with 3.11 | SHA-256 for fingerprints, HMAC-SHA256 for legacy | Already used |
| hmac (stdlib) | ships with 3.11 | HMAC-SHA256 legacy path + constant-time comparison | Already used |
| json (stdlib) | ships with 3.11 | Key files, signature files, manifests | Project standard |
| argparse (stdlib) | ships with 3.11 | CLI | Already used |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.4.1 | Test framework | All new signing tests |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Modifying mg_sign.py | New mg_sign_v2.py | Would break existing imports in mg.py and test_cert07; modification is cleaner |
| Key version field dispatch | Separate CLI flags (--algo hmac/ed25519) | Violates auto-detection requirement SIGN-06; version field is already in key files |

**Installation:**
```bash
# No new packages needed. Ed25519 is stdlib-only from Phase 1.
```

## Architecture Patterns

### Modified File Map

```
scripts/
  mg_sign.py             # MODIFIED: add Ed25519 dispatch to sign_bundle + verify_bundle_signature
  mg_ed25519.py          # UNCHANGED (Phase 1 output, imported by mg_sign.py)
  mg.py                  # MINIMAL CHANGE: update CLI sign keygen to support Ed25519 keys
tests/
  steward/
    test_cert07_bundle_signing.py   # UNCHANGED: all 11 existing HMAC tests must still pass
    test_signing_upgrade.py         # NEW: Ed25519 signing + dual-algorithm + downgrade tests
```

### Pattern 1: Algorithm Dispatch via Key Version Field

**What:** The `version` field in key files is the single discriminator for algorithm selection. No separate flags, no runtime detection.

**When to use:** Every call to `sign_bundle()` and `verify_bundle_signature()`.

**Example:**
```python
# In mg_sign.py

def _detect_algorithm(key_data: dict) -> str:
    """Detect signing algorithm from key file version field."""
    version = key_data.get("version", "")
    if version == "hmac-sha256-v1":
        return "hmac"
    elif version == "ed25519-v1":
        return "ed25519"
    else:
        raise ValueError(f"Unknown key version: {version!r}")
```

### Pattern 2: Ed25519 Signature Computation

**What:** Ed25519 signs the root_hash string (encoded as UTF-8 bytes) -- same message that HMAC signs. The signature is stored as hex in `bundle_signature.json`.

**Example:**
```python
def _compute_ed25519_signature(root_hash: str, key_data: dict) -> str:
    """Compute Ed25519 signature over root_hash."""
    from scripts.mg_ed25519 import sign as ed25519_sign
    private_seed = bytes.fromhex(key_data["private_key_hex"])
    message = root_hash.encode("utf-8")
    sig_bytes = ed25519_sign(private_seed, message)
    return sig_bytes.hex()
```

### Pattern 3: Ed25519 Verification

**What:** Ed25519 verification uses the public key (available in both private key files and `.pub.json` files). The signature hex from `bundle_signature.json` is decoded and verified.

**Example:**
```python
def _verify_ed25519_signature(root_hash: str, signature_hex: str, key_data: dict) -> bool:
    """Verify Ed25519 signature."""
    from scripts.mg_ed25519 import verify as ed25519_verify
    public_key = bytes.fromhex(key_data["public_key_hex"])
    message = root_hash.encode("utf-8")
    sig_bytes = bytes.fromhex(signature_hex)
    return ed25519_verify(public_key, message, sig_bytes)
```

### Pattern 4: Downgrade Attack Prevention

**What:** Before performing any cryptographic operation during verification, the verifier checks that the key's algorithm matches the bundle's declared algorithm. The key type is authoritative -- the bundle cannot override it.

**Example:**
```python
# In verify_bundle_signature(), after loading both sig_data and key_data:
key_algo = _detect_algorithm(key_data)
sig_version = sig_data.get("version", "")

# Map signature versions to expected key algorithms
expected = {"hmac-sha256-v1": "hmac", "ed25519-v1": "ed25519"}
sig_algo = expected.get(sig_version)

if sig_algo is None:
    return False, f"Unknown signature version: {sig_version!r}"

if key_algo != sig_algo:
    return False, (
        f"SIGNATURE INVALID: algorithm mismatch (downgrade attack prevention).\n"
        f"  bundle declares: {sig_version}\n"
        f"  verifier key is: {key_data['version']}\n"
        f"  The verifier's key type is authoritative."
    )
```

### Pattern 5: Signature File Format (Ed25519)

**What:** `bundle_signature.json` has the same schema for both algorithms, differing only in `version` and signature length.

**Example -- Ed25519 bundle_signature.json:**
```json
{
  "version": "ed25519-v1",
  "signed_root_hash": "<64 hex chars>",
  "signature": "<128 hex chars, 64 bytes>",
  "key_fingerprint": "<64 hex chars, SHA-256 of public key>",
  "note": "Verify with: python scripts/mg_sign.py verify --pack <dir> --key <keyfile>"
}
```

**Key difference from HMAC:** HMAC signature is 64 hex chars (32 bytes). Ed25519 signature is 128 hex chars (64 bytes). The verifier does not need to check length -- it dispatches by version field.

### Pattern 6: load_key Enhancement for Ed25519

**What:** `load_key()` currently requires `key_hex` field (HMAC). Must accept Ed25519 keys which have `private_key_hex` or `public_key_hex` instead. Public-only key files (`.pub.json`) must work for verification.

**Example:**
```python
def load_key(key_path: Path) -> dict:
    """Load signing key from JSON file. Supports HMAC and Ed25519 formats."""
    try:
        data = json.loads(Path(key_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ValueError(f"Cannot load key from {key_path}: {e}")
    version = data.get("version", "")
    if version == "hmac-sha256-v1":
        if "key_hex" not in data:
            raise ValueError(f"HMAC key file missing 'key_hex': {key_path}")
    elif version == "ed25519-v1":
        if "public_key_hex" not in data:
            raise ValueError(f"Ed25519 key file missing 'public_key_hex': {key_path}")
        # private_key_hex is optional (public-only keys work for verification)
    else:
        raise ValueError(f"Unknown key version {version!r} in {key_path}")
    return data
```

### Anti-Patterns to Avoid

- **Separate CLI flags for algorithm selection:** The version field in the key file IS the algorithm selector. Adding `--algo` flags creates two sources of truth.
- **Modifying bundle_signature.json schema:** The existing 4-field schema (version, signed_root_hash, signature, key_fingerprint) works for both algorithms. Do not add new fields.
- **Breaking existing mg_sign.py function signatures:** `sign_bundle(pack_dir, key_path)` and `verify_bundle_signature(pack_dir, key_path, expected_fingerprint)` signatures must remain unchanged. Algorithm dispatch happens internally.
- **Importing mg_ed25519 at module top level:** Use lazy imports inside the Ed25519 branches to avoid loading Ed25519 math when only HMAC is used. This matches mg.py's pattern.
- **Modifying test_cert07_bundle_signing.py:** These 11 tests validate the existing HMAC path. They must pass unmodified to prove backward compatibility (SIGN-07).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ed25519 signing | Custom signing code in mg_sign.py | `from scripts.mg_ed25519 import sign` | Already validated against RFC 8032 in Phase 1 |
| Ed25519 verification | Custom verify code in mg_sign.py | `from scripts.mg_ed25519 import verify` | Same |
| HMAC-SHA256 | Custom HMAC | `hmac.new()` + `hmac.compare_digest()` | Already working in mg_sign.py |
| Constant-time comparison | Manual byte-by-byte comparison | `hmac.compare_digest()` | Prevents timing side-channels; already used |

**Key insight:** mg_sign.py is a dispatcher/orchestrator. The actual cryptographic operations live in the stdlib (HMAC) or mg_ed25519.py (Ed25519). mg_sign.py should never contain raw cryptographic math.

## Common Pitfalls

### Pitfall 1: Ed25519 Signing Requires Private Key, Verification Requires Only Public

**What goes wrong:** The Ed25519 private key file has both `private_key_hex` and `public_key_hex`. The public key file (`.pub.json`) has only `public_key_hex`. Signing with a public-only key file must fail with a clear error; verification with either file type must succeed.

**Why it happens:** HMAC uses the same `key_hex` for both sign and verify (symmetric). Ed25519 is asymmetric -- the mental model from HMAC does not transfer.

**How to avoid:** In `sign_bundle()`, when algorithm is Ed25519, check for `private_key_hex` and raise `ValueError` if missing. In `verify_bundle_signature()`, only read `public_key_hex`.

**Warning signs:** Tests pass when using private key files but crash when using `.pub.json` files for verification.

### Pitfall 2: Fingerprint Semantics Differ Between HMAC and Ed25519

**What goes wrong:** HMAC fingerprint = SHA-256(key_hex bytes). Ed25519 fingerprint = SHA-256(public_key bytes). When comparing fingerprints during verification, using the wrong field from the key file produces a mismatch.

**Why it happens:** HMAC key files have `key_hex` + `fingerprint`. Ed25519 key files have `private_key_hex` + `public_key_hex` + `fingerprint`. The fingerprint derivation differs.

**How to avoid:** Always read the `fingerprint` field directly from the key file -- never recompute it during verification. Both key formats store the correct fingerprint value. Fingerprint comparison code in `verify_bundle_signature()` already uses `key_data["fingerprint"]` and does not need to change.

### Pitfall 3: HMAC Keygen in mg.py CLI Still Uses Old generate_key

**What goes wrong:** The `mg.py sign keygen` command (line 492-500) currently calls `mg_sign.generate_key()` which generates HMAC keys. It needs to support Ed25519 key generation too. Forgetting to update this means `mg.py sign keygen` can only produce HMAC keys.

**Why it happens:** mg.py has its own keygen handler that wraps mg_sign.generate_key() directly.

**How to avoid:** Add `--algo` flag (or `--type`) to `mg.py sign keygen` that defaults to Ed25519 (the new standard) but allows `hmac` for backward compatibility. Alternatively, add a separate `mg.py sign keygen-ed25519` subcommand. The cleanest approach: add `--type ed25519|hmac` flag with default `ed25519`.

### Pitfall 4: Ed25519 Signature is 128 Hex Chars, HMAC is 64

**What goes wrong:** If any code validates signature length, it would reject Ed25519 signatures. Currently no length validation exists in mg_sign.py, but future code or tests might add it.

**Why it happens:** Ed25519 signatures are 64 bytes (128 hex), HMAC-SHA256 signatures are 32 bytes (64 hex).

**How to avoid:** Do not add signature length validation. Dispatch by version field only.

### Pitfall 5: Breaking the 295 Existing Tests

**What goes wrong:** Modifying `mg_sign.py` function signatures, changing `load_key()` behavior for HMAC keys, or altering the `SIGNATURE_VERSION` constant breaks existing HMAC tests.

**Why it happens:** test_cert07_bundle_signing.py imports directly from mg_sign and depends on specific behavior.

**How to avoid:** The existing HMAC path must be the default/unchanged path. Ed25519 is an addition, not a replacement. Run `python -m pytest tests/steward/test_cert07_bundle_signing.py -x -q` after every change to mg_sign.py.

### Pitfall 6: mg_sign.py Constants Scope

**What goes wrong:** `SIGNATURE_VERSION = "hmac-sha256-v1"` is a module-level constant. If changed to `"ed25519-v1"`, all HMAC tests break. If kept as-is, it misleads developers into thinking Ed25519 uses this constant.

**Why it happens:** The constant was designed for a single-algorithm module.

**How to avoid:** Keep the existing constant for backward compatibility. Ed25519 signing sets `"version": "ed25519-v1"` explicitly in the signature dict. The constant becomes the HMAC default, not the universal default.

## Code Examples

### Modified sign_bundle (Dual Algorithm)

```python
def sign_bundle(pack_dir: Path, key_path: Path) -> dict:
    """Sign a bundle with the provided key (auto-detects HMAC or Ed25519)."""
    pack_dir = Path(pack_dir)
    manifest_path = pack_dir / "pack_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(
            f"pack_manifest.json not found in {pack_dir}. "
            "Build the bundle first with: python scripts/mg.py pack build"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root_hash = manifest.get("root_hash", "")
    if not root_hash or len(root_hash) != 64:
        raise ValueError(f"Invalid root_hash: {root_hash!r}")

    key_data = load_key(key_path)
    algo = _detect_algorithm(key_data)

    if algo == "hmac":
        signature = _compute_signature(root_hash, key_data["key_hex"])
        sig_version = SIGNATURE_VERSION  # "hmac-sha256-v1"
    elif algo == "ed25519":
        if "private_key_hex" not in key_data:
            raise ValueError("Ed25519 signing requires private key (not public-only)")
        signature = _compute_ed25519_signature(root_hash, key_data)
        sig_version = "ed25519-v1"
    else:
        raise ValueError(f"Unsupported algorithm: {algo}")

    fingerprint = key_data["fingerprint"]

    sig_dict = {
        "version": sig_version,
        "signed_root_hash": root_hash,
        "signature": signature,
        "key_fingerprint": fingerprint,
        "note": (
            "Verify with: python scripts/mg_sign.py verify "
            "--pack <dir> --key <keyfile>"
        ),
    }

    sig_path = pack_dir / SIGNATURE_FILE
    sig_path.write_text(json.dumps(sig_dict, indent=2), encoding="utf-8")
    return sig_dict
```

### Modified verify_bundle_signature (Key Sections)

```python
# After loading sig_data and key_data, BEFORE any crypto:

# Downgrade attack prevention (SIGN-08)
key_algo = _detect_algorithm(key_data)
sig_version = sig_data["version"]
expected_algo_map = {"hmac-sha256-v1": "hmac", "ed25519-v1": "ed25519"}
sig_algo = expected_algo_map.get(sig_version)

if sig_algo is None:
    return False, f"Unknown signature algorithm: {sig_version!r}"

if key_algo != sig_algo:
    return False, (
        f"SIGNATURE INVALID: algorithm mismatch.\n"
        f"  bundle signed with: {sig_version}\n"
        f"  verifier key type:  {key_data['version']}\n"
        f"  This may indicate a downgrade attack."
    )

# Then dispatch to the correct verification path:
if key_algo == "hmac":
    expected_sig = _compute_signature(sig_data["signed_root_hash"], key_data["key_hex"])
    if not hmac.compare_digest(sig_data["signature"], expected_sig):
        return False, "SIGNATURE INVALID: HMAC verification failed."
elif key_algo == "ed25519":
    from scripts.mg_ed25519 import verify as ed25519_verify
    pub_key = bytes.fromhex(key_data["public_key_hex"])
    msg = sig_data["signed_root_hash"].encode("utf-8")
    sig_bytes = bytes.fromhex(sig_data["signature"])
    if not ed25519_verify(pub_key, msg, sig_bytes):
        return False, "SIGNATURE INVALID: Ed25519 verification failed."
```

### mg.py CLI Keygen Update

```python
# In mg.py, update _cmd_sign_keygen to support key type:
def _cmd_sign_keygen(a):
    key_type = getattr(a, 'type', 'ed25519')
    if key_type == 'ed25519':
        from scripts.mg_ed25519 import generate_key_files
        key_data = generate_key_files(Path(a.out))
    else:
        from scripts.mg_sign import generate_key
        import json as _j
        key = generate_key()
        Path(a.out).write_text(_j.dumps(key, indent=2), encoding="utf-8")
        key_data = key
    print(f"Signing key ({key_type}): {a.out}")
    print(f"Fingerprint: {key_data['fingerprint']}")
    return 0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HMAC-SHA256 only (mg_sign.py v0.3.0) | Dual HMAC + Ed25519 dispatch | This phase (v0.4.0) | Third-party auditors verify with public key only |
| Single algorithm constant | Version-field dispatch | This phase | Future algorithms can be added without breaking existing bundles |

**Not deprecated:**
- HMAC-SHA256 signing remains fully functional for backward compatibility
- Existing HMAC key files and signed bundles work without modification
- `python scripts/mg_sign.py keygen` still generates HMAC keys by default (or with explicit flag)

## Open Questions

1. **Default algorithm for mg.py sign keygen**
   - What we know: Phase 2 introduces Ed25519 as the preferred algorithm. HMAC must remain available.
   - What's unclear: Should `mg.py sign keygen --out key.json` default to Ed25519 or HMAC? Defaulting to Ed25519 is forward-looking but changes existing behavior.
   - Recommendation: Default to Ed25519 since this is v0.4.0 (new major feature). Add `--type hmac` flag for explicit HMAC key generation. The existing `mg_sign.py keygen` CLI can keep HMAC as default for backward compatibility.

2. **mg_sign.py CLI vs mg.py CLI**
   - What we know: Both `mg_sign.py` and `mg.py` expose keygen/sign/verify commands. mg.py wraps mg_sign.py.
   - What's unclear: Should mg_sign.py's own CLI also gain Ed25519 support, or only mg.py?
   - Recommendation: mg_sign.py should gain Ed25519 support because it's imported directly by tests and can be used standalone. mg.py just wraps it.

3. **Fingerprint-only verification with Ed25519 bundles**
   - What we know: The existing fingerprint-only path checks `key_fingerprint` without any key. This works identically for both algorithms since it's just string comparison.
   - What's unclear: Nothing -- this is straightforward.
   - Recommendation: No changes needed. Fingerprint-only verification is algorithm-agnostic.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 |
| Config file | None in repo root (uses defaults) |
| Quick run command | `python -m pytest tests/steward/test_signing_upgrade.py -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SIGN-03 | Ed25519 key signs bundle, produces valid bundle_signature.json | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_sign_creates_ed25519_signature -x` | No -- Wave 0 |
| SIGN-03 | Ed25519 signature round-trips (sign then verify) | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_ed25519_sign_verify_roundtrip -x` | No -- Wave 0 |
| SIGN-04 | Ed25519 public-key-only file can verify signature | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_verify_with_public_key_only -x` | No -- Wave 0 |
| SIGN-04 | Invalid Ed25519 signature is rejected | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_forged_ed25519_signature_fails -x` | No -- Wave 0 |
| SIGN-04 | Wrong Ed25519 key rejects signature | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_wrong_ed25519_key_fails -x` | No -- Wave 0 |
| SIGN-04 | Bundle modified after Ed25519 signing is detected | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_bundle_modified_after_ed25519_signing -x` | No -- Wave 0 |
| SIGN-06 | HMAC key auto-detected, routes to HMAC path | unit | `python -m pytest tests/steward/test_signing_upgrade.py::TestAlgorithmDispatch::test_hmac_key_detected -x` | No -- Wave 0 |
| SIGN-06 | Ed25519 key auto-detected, routes to Ed25519 path | unit | `python -m pytest tests/steward/test_signing_upgrade.py::TestAlgorithmDispatch::test_ed25519_key_detected -x` | No -- Wave 0 |
| SIGN-06 | Unknown key version rejected with clear error | unit | `python -m pytest tests/steward/test_signing_upgrade.py::TestAlgorithmDispatch::test_unknown_version_rejected -x` | No -- Wave 0 |
| SIGN-07 | All 11 existing HMAC tests pass unmodified | regression | `python -m pytest tests/steward/test_cert07_bundle_signing.py -x -q` | Yes (existing, 11 tests) |
| SIGN-08 | HMAC key vs Ed25519 bundle rejected | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestDowngradeAttack::test_hmac_key_ed25519_bundle_rejected -x` | No -- Wave 0 |
| SIGN-08 | Ed25519 key vs HMAC bundle rejected | integration | `python -m pytest tests/steward/test_signing_upgrade.py::TestDowngradeAttack::test_ed25519_key_hmac_bundle_rejected -x` | No -- Wave 0 |
| REGR | All 295+ existing tests still pass | regression | `python -m pytest tests/ -q` | Yes (existing) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/steward/test_signing_upgrade.py tests/steward/test_cert07_bundle_signing.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green + `python scripts/steward_audit.py` + `python scripts/deep_verify.py` before verify-work

### Wave 0 Gaps

- [ ] `tests/steward/test_signing_upgrade.py` -- covers SIGN-03, SIGN-04, SIGN-06, SIGN-07 (indirectly via existing), SIGN-08
- [ ] No framework install needed (pytest 8.4.1 already present)
- [ ] No conftest changes needed (new tests are self-contained)

## Sources

### Primary (HIGH confidence)

- `scripts/mg_sign.py` -- read directly; existing HMAC signing implementation (359 lines), all function signatures, key format, signature format, CLI structure documented above
- `scripts/mg_ed25519.py` -- read directly; Phase 1 Ed25519 implementation, function signatures: `sign(private_seed, message) -> bytes`, `verify(public_key, message, signature) -> bool`, `generate_keypair(private_seed=None) -> (seed, pub)`, `generate_key_files(out_path) -> dict`
- `scripts/mg.py` lines 476-523 -- read directly; CLI integration point for signing, lazy imports from mg_sign
- `tests/steward/test_cert07_bundle_signing.py` -- read directly; 11 existing HMAC signing tests, import pattern, helper functions
- `tests/steward/test_ed25519.py` -- read directly; 37 existing Ed25519 correctness tests, import pattern
- `CLAUDE.md` -- project constraints, sealed files, verification gates
- `.planning/REQUIREMENTS.md` -- requirement definitions for SIGN-03, SIGN-04, SIGN-06, SIGN-07, SIGN-08

### Secondary (MEDIUM confidence)

- `.planning/phases/01-ed25519-foundation/01-RESEARCH.md` -- Phase 1 research, key file format decisions, Ed25519 architecture

### Tertiary (LOW confidence)

- None -- all findings verified against codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all stdlib, no new dependencies, Ed25519 already proven in Phase 1
- Architecture: HIGH -- mg_sign.py structure is clear, modification points identified, code examples verified against actual codebase
- Pitfalls: HIGH -- all pitfalls derived from reading actual code (field name differences between HMAC/Ed25519 key files, constant scoping, import patterns)

**Research date:** 2026-03-17
**Valid until:** 2026-04-17 (stable domain; all code is in-repo, no external API dependencies)

---
*Phase: 02-signing-upgrade*
*Research completed: 2026-03-17*
