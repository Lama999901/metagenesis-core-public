---
phase: 02-signing-upgrade
verified: 2026-03-17T00:00:00Z
status: gaps_found
score: 5/6 must-haves verified
re_verification: false
gaps:
  - truth: "User can generate Ed25519 keys via mg_sign.py keygen --out key.json --type ed25519"
    status: failed
    reason: >
      Running `python scripts/mg_sign.py keygen --out key.json --type ed25519` raises
      ModuleNotFoundError: No module named 'scripts'. The lazy import
      `from scripts.mg_ed25519 import generate_key_files` inside cmd_keygen fails because
      direct invocation of scripts/mg_sign.py places scripts/ on sys.path[0], not the repo
      root. mg_sign.py lacks the sys.path.insert(0, REPO_ROOT) fix that mg.py received in
      Plan 02 Task 1. The HMAC default path (stdlib only) is unaffected.
    artifacts:
      - path: "scripts/mg_sign.py"
        issue: "No sys.path fix for direct CLI invocation — cmd_keygen ed25519 branch fails with ModuleNotFoundError when called as `python scripts/mg_sign.py`"
    missing:
      - "Add REPO_ROOT sys.path fix to scripts/mg_sign.py (same as mg.py line 17-18: REPO_ROOT = Path(__file__).resolve().parents[1]; if str(REPO_ROOT) not in sys.path: sys.path.insert(0, str(REPO_ROOT)))"
---

# Phase 2: Signing Upgrade Verification Report

**Phase Goal:** Users can sign bundles with Ed25519 and verify them, while all existing HMAC-signed bundles continue to verify without modification
**Verified:** 2026-03-17
**Status:** GAPS FOUND (1 gap)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                     | Status      | Evidence                                                                                   |
|----|-------------------------------------------------------------------------------------------|-------------|--------------------------------------------------------------------------------------------|
| 1  | Ed25519 key signs a bundle and produces bundle_signature.json with version ed25519-v1     | VERIFIED  | test_sign_creates_ed25519_signature passes; sig["version"]=="ed25519-v1", 128 hex chars |
| 2  | Ed25519-signed bundle verifies PASS with corresponding public key (.pub.json)             | VERIFIED  | test_ed25519_sign_verify_roundtrip + test_verify_with_public_key_only pass               |
| 3  | Invalid/wrong/forged Ed25519 signatures are rejected                                      | VERIFIED  | test_forged_ed25519_signature_fails + test_wrong_ed25519_key_fails pass                  |
| 4  | Existing HMAC-signed bundles continue to verify without modification                      | VERIFIED  | test_cert07_bundle_signing.py: 11 tests pass unmodified; full suite 357 passed           |
| 5  | Algorithm mismatch between key type and bundle signature version is rejected              | VERIFIED  | test_hmac_key_ed25519_bundle_rejected + test_ed25519_key_hmac_bundle_rejected pass       |
| 6  | User can generate Ed25519 keys via mg_sign.py keygen --type ed25519                      | FAILED    | `python scripts/mg_sign.py keygen --out k.json --type ed25519` raises ModuleNotFoundError |

**Score:** 5/6 truths verified

---

## Required Artifacts

| Artifact                                       | Expected                                              | Status   | Details                                                                                     |
|------------------------------------------------|-------------------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| `scripts/mg_sign.py`                           | Dual-algorithm bundle signing (HMAC + Ed25519)        | VERIFIED | Contains _detect_algorithm, _compute_ed25519_signature, updated load_key/sign_bundle/verify |
| `tests/steward/test_signing_upgrade.py`        | Ed25519 signing integration tests + downgrade tests   | VERIFIED | 15 tests across 4 classes, 312 lines, all substantive (no stubs)                            |
| `scripts/mg.py`                                | Updated CLI with --type flag for keygen               | VERIFIED | --type flag present with ed25519 default; direct invocation works                           |
| `scripts/mg_sign.py` (CLI keygen --type ed25519) | Produces ed25519-v1 key via direct script invocation | PARTIAL  | Logic is correct but sys.path missing; invocation as `python scripts/mg_sign.py` fails     |

### Artifact Level 2 (Substantive) Checks

**scripts/mg_sign.py — passes all three levels for core signing logic:**
- `_detect_algorithm` function: exists, substantive, called in sign_bundle and verify_bundle_signature
- `_compute_ed25519_signature` function: exists, lazy imports mg_ed25519.sign, wired into sign_bundle
- `load_key`: accepts both hmac-sha256-v1 and ed25519-v1 versions, validates required fields
- `sign_bundle`: dispatches via _detect_algorithm, raises ValueError for public-only Ed25519 key
- `verify_bundle_signature`: downgrade check before any crypto, algorithm-dispatched verification

**tests/steward/test_signing_upgrade.py:**
- 15 tests collected, all classes complete with substantive implementations
- Helper `_make_ed25519_signed_bundle` fully wired to generate_key_files + sign_bundle
- No stubs or placeholder tests detected

---

## Key Link Verification

| From                                            | To                               | Via                                    | Status      | Details                                                               |
|-------------------------------------------------|----------------------------------|----------------------------------------|-------------|-----------------------------------------------------------------------|
| `scripts/mg_sign.py`                            | `scripts/mg_ed25519.py`          | lazy import in Ed25519 branches        | VERIFIED  | `from scripts.mg_ed25519 import sign as ed25519_sign` at line 151     |
| `scripts/mg_sign.py`                            | `scripts/mg_ed25519.py`          | lazy import in verify path             | VERIFIED  | `from scripts.mg_ed25519 import verify as ed25519_verify` at line 321 |
| `scripts/mg_sign.py::_detect_algorithm`         | `scripts/mg_sign.py::sign_bundle`| key version field dispatch             | VERIFIED  | `algo = _detect_algorithm(key_data)` at line 189                      |
| `scripts/mg_sign.py::verify_bundle_signature`   | downgrade attack check           | key_algo != sig_algo comparison        | VERIFIED  | Lines 294-300, checked before fingerprint and before crypto           |
| `scripts/mg.py::_cmd_sign_keygen`               | `scripts/mg_ed25519.py::generate_key_files` | lazy import for Ed25519 keygen | VERIFIED | `from scripts.mg_ed25519 import generate_key_files` at mg.py line 499 |
| `scripts/mg_sign.py::cmd_keygen`                | `scripts/mg_ed25519.py::generate_key_files` | lazy import for Ed25519 keygen | BROKEN   | Import is correct but sys.path not set — fails as direct CLI          |

---

## Requirements Coverage

| Requirement | Source Plan     | Description                                                                    | Status    | Evidence                                                                    |
|-------------|-----------------|--------------------------------------------------------------------------------|-----------|-----------------------------------------------------------------------------|
| SIGN-03     | 02-01, 02-02    | Bundle signing with Ed25519 private key produces verifiable signature          | SATISFIED | sign_bundle produces ed25519-v1 bundle_signature.json; 6 tests verify       |
| SIGN-04     | 02-01           | Signature verification with Ed25519 public key confirms bundle authenticity    | SATISFIED | verify_bundle_signature accepts .pub.json; test_verify_with_public_key_only |
| SIGN-06     | 02-01, 02-02    | Dual-algorithm auto-detection from key file version field                      | SATISFIED | _detect_algorithm dispatches hmac vs ed25519; TestAlgorithmDispatch (3 tests)|
| SIGN-07     | 02-01           | Existing HMAC-signed bundles continue to verify without modification           | SATISFIED | test_cert07_bundle_signing.py all 11 tests pass; SIGNATURE_VERSION unchanged |
| SIGN-08     | 02-01           | Downgrade attack prevention                                                    | SATISFIED | Algorithm mismatch check at lines 294-300; TestDowngradeAttack (2 tests)    |

**Orphaned requirements check:** REQUIREMENTS.md Traceability table maps SIGN-03, SIGN-04, SIGN-06, SIGN-07, SIGN-08 to Phase 2 — all claimed by plan frontmatter. No orphaned requirements.

**Note on SIGN-06 partial gap:** The auto-detection logic itself (in `verify_bundle_signature` and `sign_bundle`) is fully wired and passes all tests. The gap is in the CLI keygen command for `mg_sign.py` when invoked directly. SIGN-06 is counted satisfied because the core requirement (auto-detect from key file version field) is implemented and tested; the CLI invocation issue is a deployment/path issue, not an algorithm detection failure.

---

## Anti-Patterns Found

| File                                     | Line   | Pattern                              | Severity | Impact                                  |
|------------------------------------------|--------|--------------------------------------|----------|-----------------------------------------|
| `scripts/mg_sign.py`                     | 370    | `from scripts.mg_ed25519 import ...` | Warning  | Fails when `python scripts/mg_sign.py` invoked directly — no sys.path setup |

No TODO/FIXME/placeholder comments found in modified files. No empty implementations. No stub handlers.

---

## Human Verification Required

None — all critical behaviors are verified programmatically via the test suite.

---

## Gaps Summary

**1 gap blocking a plan acceptance criterion.**

`python scripts/mg_sign.py keygen --out key.json --type ed25519` fails with `ModuleNotFoundError: No module named 'scripts'` when invoked directly from the repo root. The lazy import `from scripts.mg_ed25519 import generate_key_files` inside `cmd_keygen` requires `scripts/` to NOT be on `sys.path[0]` — but direct script invocation places it there. The fix applied to `mg.py` in Plan 02 (adding `REPO_ROOT = Path(__file__).resolve().parents[1]; if str(REPO_ROOT) not in sys.path: sys.path.insert(0, str(REPO_ROOT))`) was not applied to `mg_sign.py`.

The HMAC default path (`python scripts/mg_sign.py keygen --out key.json`) works correctly because it uses only stdlib. All 15 new tests and all 11 existing HMAC tests pass (28 total, 357 full suite). The core dual-algorithm signing, verification, and downgrade attack prevention are all fully implemented and working. Only the direct CLI invocation of `mg_sign.py` with `--type ed25519` fails.

**Root cause:** Single missing sys.path setup block in `scripts/mg_sign.py` — same two-line fix that was applied to `mg.py`.

**Fix:** Add to `scripts/mg_sign.py` after existing imports:
```python
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
```

---

_Verified: 2026-03-17_
_Verifier: Claude (gsd-verifier)_
