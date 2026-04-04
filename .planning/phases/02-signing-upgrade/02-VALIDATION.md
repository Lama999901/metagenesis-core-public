---
phase: 2
slug: signing-upgrade
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 |
| **Config file** | none — uses defaults |
| **Quick run command** | `python -m pytest tests/steward/test_signing_upgrade.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/steward/test_signing_upgrade.py tests/steward/test_cert07_bundle_signing.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green + `python scripts/steward_audit.py` + `python scripts/deep_verify.py`
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | SIGN-03 | integration | `pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_sign_creates_ed25519_signature -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | SIGN-03 | integration | `pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_ed25519_sign_verify_roundtrip -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | SIGN-04 | integration | `pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_verify_with_public_key_only -x` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | SIGN-04 | integration | `pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_forged_ed25519_signature_fails -x` | ❌ W0 | ⬜ pending |
| 02-01-05 | 01 | 1 | SIGN-04 | integration | `pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_wrong_ed25519_key_fails -x` | ❌ W0 | ⬜ pending |
| 02-01-06 | 01 | 1 | SIGN-04 | integration | `pytest tests/steward/test_signing_upgrade.py::TestEd25519BundleSigning::test_bundle_modified_after_ed25519_signing -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | SIGN-06 | unit | `pytest tests/steward/test_signing_upgrade.py::TestAlgorithmDispatch::test_hmac_key_detected -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | SIGN-06 | unit | `pytest tests/steward/test_signing_upgrade.py::TestAlgorithmDispatch::test_ed25519_key_detected -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | SIGN-06 | unit | `pytest tests/steward/test_signing_upgrade.py::TestAlgorithmDispatch::test_unknown_version_rejected -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | SIGN-07 | regression | `pytest tests/steward/test_cert07_bundle_signing.py -x -q` | ✅ | ⬜ pending |
| 02-04-01 | 04 | 2 | SIGN-08 | integration | `pytest tests/steward/test_signing_upgrade.py::TestDowngradeAttack::test_hmac_key_ed25519_bundle_rejected -x` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 2 | SIGN-08 | integration | `pytest tests/steward/test_signing_upgrade.py::TestDowngradeAttack::test_ed25519_key_hmac_bundle_rejected -x` | ❌ W0 | ⬜ pending |
| 02-REGR | - | 2 | REGR | regression | `pytest tests/ -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/steward/test_signing_upgrade.py` — stubs for SIGN-03, SIGN-04, SIGN-06, SIGN-08
- No framework install needed (pytest 8.4.1 already present)
- No conftest changes needed (new tests are self-contained)

*Wave 0 test file must exist before execution begins.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
