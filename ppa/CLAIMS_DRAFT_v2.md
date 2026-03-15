---

> **DRAFT v2** — Post-filing additions for non-provisional application.
> Filing deadline: 2027-03-05 (12 months from PPA #63/996,819).
> PPA filing basis (FROZEN): MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01.
> This document covers post-filing claims to include in non-provisional.
> Do NOT edit ppa/CLAIMS_DRAFT.md — that document is incorporated by
> reference into the filed PPA.

# MetaGenesis Core — Claims Draft v2
## For Non-Provisional Application (pre-2027-03-05)

---

## Status

| Claim | Added | Status | Tests |
|---|---|---|---|
| DRIFT-01 | Post 2026-03-05 | Active, 223 tests PASS | tests/steward/test_drift01_* |
| ML_BENCH-01 | Post 2026-03-05 | Active, 223 tests PASS | tests/ml/test_mlbench01_* |
| DT-FEM-01 | 2026-03-11 | Active, 223 tests PASS | tests/digital_twin/test_dtfem01_* |

All three claims use the same 4 patentable innovations filed in PPA
#63/996,819. They are domain-specific applications of the
domain-agnostic governance infrastructure (per PPA [0019]).

---

## DRIFT-01 — Calibration Anchor and Drift Monitor

**job_kind:** `drift_calibration_monitor`
**file:** `backend/progress/drift_monitor.py`
**V&V threshold:** `drift_pct ≤ drift_threshold_pct` (default 5.0%)

**What it verifies:** A verified calibration result (e.g. MTR-1:
E = 70 GPa) becomes a trusted anchor. Any future computation is
compared: `drift_pct = |current - anchor| / |anchor| * 100`.
If drift_pct > threshold → `correction_required = True`.

**Patent relevance:** Implements Innovation 4 (dual-mode canary pipeline)
and Innovation 1 (bidirectional claim coverage) for calibration traceability.
The anchor-drift pattern is the core mechanism for digital twin
calibration loop verification.

**Reproduction:**
```bash
python -m pytest tests/steward/test_drift01_calibration_anchor.py -v
```

---

## ML_BENCH-01 — ML Accuracy Certificate

**job_kind:** `mlbench1_accuracy_certificate`
**file:** `backend/progress/mlbench1_accuracy_certificate.py`
**V&V threshold:** `abs(actual_accuracy - claimed_accuracy) ≤ 0.02`

**What it verifies:** Any ML model claiming a specific accuracy on a
test set. Synthetic mode (deterministic from seed) or real data mode
(y_true/y_pred CSV, SHA-256 fingerprinted). `result.pass` must be True
for certificate to be valid.

**Patent relevance:** Demonstrates domain-agnostic extensibility of all
4 innovations to ML/AI domain. Directly addresses EU AI Act and FDA
AI/ML regulatory requirements for independent model performance
verification.

**Reproduction:**
```bash
python -m pytest tests/ml/test_mlbench01_accuracy_certificate.py -v
```

---

## DT-FEM-01 — Digital Twin FEM Verification Certificate

**job_kind:** `dtfem1_displacement_verification`
**file:** `backend/progress/dtfem1_displacement_verification.py`
**V&V threshold:** `rel_err ≤ 0.02` (2% relative error, configurable)

**What it verifies:** Any FEM or simulation solver output against a
physical reference measurement. `rel_err = |fem_value - reference| /
|reference|`. Supports synthetic mode (deterministic from seed) and
real data mode (CSV with fem_value/measured_value columns,
SHA-256 fingerprinted).

This claim is the universal verification layer for digital twin
calibration. The verified FEM output becomes a trusted anchor for
DRIFT-01 monitoring. The full chain:
MTR-1 (material property anchor) →
DT-FEM-01 (FEM output vs. physical reference) →
DRIFT-01 (ongoing drift monitoring)

Each step is independently verifiable offline.

**Patent relevance:** Domain-agnostic application of all 4 innovations
to engineering simulation / digital twin domain. Directly addresses
the verification gap in simulation-based design for aerospace, automotive,
medical device, and industrial digital twin applications.

**Reproduction:**
```bash
python -m pytest tests/digital_twin/test_dtfem01_displacement_verification.py -v
```

---

## Acceptance commands (run before non-provisional filing)
```bash
python scripts/steward_audit.py
# → STEWARD AUDIT: PASS

python -m pytest tests/ -q
# → 223 passed

grep -r "tamper-proof\|GPT-5\|19x\|VacuumGenesis" docs/ scripts/ backend/
# → empty
```

---

*Claims Draft v2. Authority: post-filing additions for non-provisional.*
*Deadline: 2027-03-05. Inventor: Yehor Bazhynov.*
*PPA basis: USPTO #63/996,819, filed 2026-03-05.*
