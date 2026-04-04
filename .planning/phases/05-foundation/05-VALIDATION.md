---
phase: 5
slug: foundation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-17
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.1 |
| **Config file** | none — existing infrastructure |
| **Quick run command** | `python -m pytest tests/steward/test_step_chain_all_claims.py tests/steward/test_cert03_step_chain_verify.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -q`
- **After every plan wave:** Run `python -m pytest tests/ -q && python scripts/steward_audit.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CHAIN-01 | unit | `python -m pytest tests/steward/test_step_chain_all_claims.py -q` | Extends existing | pending |
| 05-02-01 | 02 | 1 | CHAIN-02,03,04 | unit | `python -m pytest tests/steward/test_cert03_step_chain_verify.py -q` | Extends existing | pending |
| 05-03-01 | 03 | 1 | ERR-01,02,03 | unit | `python -m pytest tests/steward/test_runner_error_paths.py -q` | New file | pending |
| 05-03-02 | 03 | 1 | GOV-01,02,03 | unit | `python -m pytest tests/steward/test_stew08_documentation_drift.py -q` | New file | pending |

*Status: pending*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No new framework install, conftest, or stub creation needed.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have automated verify
- [x] Sampling continuity: every task has a test command
- [x] Wave 0 covers all MISSING references (none needed)
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
