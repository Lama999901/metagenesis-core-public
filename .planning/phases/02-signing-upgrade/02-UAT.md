---
status: complete
phase: 02-signing-upgrade
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md]
started: 2026-03-18T01:00:00Z
updated: 2026-03-18T01:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Generate Ed25519 Key via mg.py (Default)
expected: Run `python scripts/mg.py sign keygen --out /tmp/test_ed25519.json`. Output shows key file created. File contains JSON with `"version": "ed25519-v1"`, `"private_key_hex"`, and `"public_key_hex"` fields. A companion `.pub.json` file is also created with only the public key.
result: pass

### 2. Generate HMAC Key via mg.py (--type hmac)
expected: Run `python scripts/mg.py sign keygen --out /tmp/test_hmac.json --type hmac`. Output shows key file created. File contains JSON with `"version": "hmac-sha256-v1"` and `"key_hex"` field (NOT private_key_hex).
result: pass

### 3. Sign Bundle with Ed25519 Key
expected: Run `python scripts/mg.py sign bundle --key /tmp/test_ed25519.json --pack <any_pack_dir>`. Creates `bundle_signature.json` with `"version": "ed25519-v1"` and a 128-character hex signature string.
result: pass

### 4. Verify Ed25519-Signed Bundle
expected: After signing with Ed25519 key, run `python scripts/mg.py sign verify --key /tmp/test_ed25519.json --pack <same_pack_dir>`. Output shows PASS/verification success.
result: pass

### 5. Verify with Public Key Only
expected: Run `python scripts/mg.py sign verify --key /tmp/test_ed25519.json.pub.json --pack <same_pack_dir>`. Verification succeeds using only the public key file (no private key needed).
result: pass

### 6. HMAC Backward Compatibility
expected: Run existing HMAC signing tests: `python -m pytest tests/steward/test_cert07_bundle_signing.py -x -q`. All 13 tests pass with no modifications.
result: pass

### 7. Downgrade Attack Prevention
expected: Attempt to verify an Ed25519-signed bundle with an HMAC key (or vice versa). The verifier rejects with a clear error about algorithm mismatch. Run: `python -m pytest tests/steward/test_signing_upgrade.py::TestDowngradeAttack -x -q`. Both downgrade attack tests pass.
result: pass

### 8. Full Regression Gate
expected: Run `python -m pytest tests/ -q && python scripts/steward_audit.py`. All 357+ tests pass, steward audit shows PASS. No regressions from signing upgrade.
result: pass

## Summary

total: 8
passed: 8
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
