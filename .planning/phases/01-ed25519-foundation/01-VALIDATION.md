---
phase: 01
slug: ed25519-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-17
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/ directory (existing) |
| **Quick run command** | `python -m pytest tests/test_ed25519.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds (full suite with 295+ tests) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_ed25519.py -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SIGN-01 | unit | `python scripts/mg_ed25519.py` (self-test) | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | SIGN-01 | unit | `python -m pytest tests/test_ed25519.py -q` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | SIGN-02 | unit | `python scripts/mg_ed25519.py keygen --out /tmp/test_key.json` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | SIGN-05 | unit | `test -f /tmp/test_key.pub.json` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ed25519.py` — RFC 8032 vector tests + keygen tests
- [ ] `scripts/mg_ed25519.py` — module with self-test mode

*Existing pytest infrastructure covers framework needs. No new dependencies required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Public key file readable by third party | SIGN-05 | Requires inspecting JSON structure for auditor usability | Open key.pub.json, verify it contains only version, public_key_hex, fingerprint (no private key) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
