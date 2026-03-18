---
phase: 4
slug: adversarial-proofs-and-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | existing pytest configuration |
| **Quick run command** | `python -m pytest tests/steward/test_cert09_ed25519_attacks.py tests/steward/test_cert10_temporal_attacks.py -q` |
| **Full suite command** | `python -m pytest tests/ -q && python scripts/deep_verify.py` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/steward/ -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -q && python scripts/deep_verify.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CERT-05 | unit | `python -m pytest tests/steward/test_cert09_ed25519_attacks.py -x` | W0 | pending |
| 04-01-02 | 01 | 1 | CERT-06 | unit | `python -m pytest tests/steward/test_cert10_temporal_attacks.py -x` | W0 | pending |
| 04-02-01 | 02 | 1 | CERT-01 | integration | `python scripts/deep_verify.py` | modify | pending |
| 04-02-02 | 02 | 1 | CERT-02 | integration | `python scripts/deep_verify.py` | modify | pending |
| 04-02-03 | 02 | 1 | CERT-03 | integration | `python scripts/deep_verify.py` | modify | pending |
| 04-02-04 | 02 | 1 | CERT-04 | unit | `python -m pytest tests/steward/test_cert_5layer_independence.py -x` | W0 | pending |
| 04-03-01 | 03 | 2 | DOCS-01 | integration | `python scripts/deep_verify.py` (Test 7) | modify | pending |
| 04-03-02 | 03 | 2 | DOCS-02 | integration | `python scripts/deep_verify.py` (Test 7) | modify | pending |
| 04-03-03 | 03 | 2 | DOCS-03 | manual | visual review | modify | pending |
| 04-03-04 | 03 | 2 | DOCS-04 | manual | visual review | modify | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/steward/test_cert09_ed25519_attacks.py` — created by Plan 01 Task 1 (CERT-05)
- [ ] `tests/steward/test_cert10_temporal_attacks.py` — created by Plan 01 Task 2 (CERT-06)
- [ ] `tests/steward/test_cert_5layer_independence.py` — created by Plan 02 Task 2 (CERT-04)

*Existing infrastructure (pytest, deep_verify.py) covers remaining requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| scientific_claim_index.md updated | DOCS-03 | Content review | Verify new capability entries for Ed25519 + temporal |
| paper.md references updated | DOCS-04 | Content review | Verify Innovation #7 citation, 5-layer architecture reference |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
