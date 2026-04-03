---
phase: 07
slug: flagship-proofs
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-18
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest runs from repo root |
| **Quick run command** | `python -m pytest tests/steward/test_cert11_coordinated_attack.py tests/steward/test_cert12_encoding_attacks.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/steward/test_cert11_coordinated_attack.py tests/steward/test_cert12_encoding_attacks.py -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | ADV-01, ADV-02 | adversarial | `pytest tests/steward/test_cert11_coordinated_attack.py -q` | ❌ W0 | ⬜ pending |
| 07-01-02 | 01 | 1 | ADV-03, ADV-04 | adversarial | `pytest tests/steward/test_cert11_coordinated_attack.py -q` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 2 | ADV-05 | encoding | `pytest tests/steward/test_cert12_encoding_attacks.py -q` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 2 | ADV-06 | encoding | `pytest tests/steward/test_cert12_encoding_attacks.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/steward/test_cert11_coordinated_attack.py` — stubs for ADV-01 through ADV-04
- [ ] `tests/steward/test_cert12_encoding_attacks.py` — stubs for ADV-05, ADV-06

*Existing pytest infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
