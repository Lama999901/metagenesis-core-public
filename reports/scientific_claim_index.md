# Scientific Claim Index v0.1

Documentation-only registry of domain claims so new cases remain uniquely structured and submission-ready. No code or policy changes; docs only.

---

## MTR-1

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **job_kind** | `mtr1_youngs_modulus_calibration` |
| **reproduction** | `python -m pytest tests/materials/test_mtr1_youngs_modulus.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result` in the run artifact JSON. Contains `mtr_phase`, `inputs`, and `result` (estimated_E, rmse, relative_error, method, algorithm_version, n_points). |
| **V&V thresholds** | `relative_error <= 0.01`; `rmse <= (E_true * max_strain) * 0.02`. |
| **notes (canary vs normal)** | Same job kind runs in normal (authoritative) or canary (non-authoritative) mode via Progress Engine `run_job(..., canary_mode=...)`. Ledger action/actor differ (job_completed vs job_completed_canary; scheduler_v1 vs scheduler_v1_canary). Evidence artifacts are produced for both; canary runs are marked in artifact `canary_mode: true`. |

---

## MTR-2

| Field | Value |
|-------|--------|
| **claim_id** | MTR-2 |
| **job_kind** | `mtr2_thermal_paste_conductivity_calibration` |
| **reproduction** | `python -m pytest tests/materials/test_mtr2_thermal_paste_conductivity.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result` in the run artifact JSON. Contains `mtr_phase`, `inputs`, and `result` (estimated_k, rmse, relative_error, method, algorithm_version). |
| **V&V thresholds** | `relative_error <= 0.02`; `rmse <= max(deltaT_true) * 0.03`. |
| **notes (canary vs normal)** | Same as MTR-1: job runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts produced for both; canary marked in artifact `canary_mode: true`. |

---

## MTR-3

| Field | Value |
|-------|--------|
| **claim_id** | MTR-3 |
| **job_kind** | `mtr3_thermal_multilayer_contact_calibration` |
| **reproduction** | `python -m pytest tests/materials/test_mtr3_thermal_multilayer.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result` in the run artifact JSON. Contains `mtr_phase`, `inputs`, and `result` (estimated_k, estimated_r_contact, rmse, rel_err_k, rel_err_r, method, algorithm_version). |
| **V&V thresholds** | `rel_err_k <= 0.03`; `rel_err_r <= 0.05`; `rmse <= max(deltaT_true) * 0.05`. |
| **notes (canary vs normal)** | Same as MTR-1/MTR-2: job runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts produced for both; canary marked in artifact `canary_mode: true`. |

---

## DATA-PIPE-01

| Field | Value |
|-------|--------|
| **claim_id** | DATA-PIPE-01 |
| **job_kind** | `datapipe1_quality_certificate` |
| **reproduction** | `python -m pytest tests/data/test_datapipe01_quality_certificate.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result`. Contains domain, claim_id, inputs (dataset with sha256, relpath), result (pass, issues, metrics). |
| **V&V thresholds** | pass is True when schema/range checks pass; no absolute paths in output. |
| **notes (canary vs normal)** | Same as MTR: job runs in normal or canary mode; evidence artifacts for both. |

---

## SYSID-01

| Field | Value |
|-------|--------|
| **claim_id** | SYSID-01 |
| **job_kind** | `sysid1_arx_calibration` |
| **reproduction** | `python -m pytest tests/systems/test_sysid01_arx_calibration.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result` in the run artifact JSON. Contains domain, claim_id, inputs, and result (estimated_a, estimated_b, rmse, rel_err_a, rel_err_b, method, algorithm_version). |
| **V&V thresholds** | `rel_err_a <= 0.03`; `rel_err_b <= 0.03`; `rmse <= 0.05 * (|a_true| + |b_true|) * u_max`. |
| **notes (canary vs normal)** | Same as MTR: job runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts produced for both; canary marked in artifact `canary_mode: true`. |

---

## DRIFT-01

| Field | Value |
|-------|--------|
| **claim_id** | DRIFT-01 |
| **job_kind** | `drift_calibration_monitor` |
| **domain** | Simulation Correction / Calibration Traceability |
| **reproduction** | `python -m pytest tests/steward/test_drift01_calibration_anchor.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result`. Contains mtr_phase, inputs (anchor_claim_id, anchor_value, anchor_units, current_value, drift_threshold_pct), result (anchor_value, current_value, drift_pct, drift_threshold_pct, drift_detected, correction_required). |
| **V&V thresholds** | drift_threshold_pct 5.0%; drift_detected False when within threshold; drift_detected True when >5%. |
| **notes (canary vs normal)** | Same job kind runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts for both. |

### Purpose

Verified calibration results (e.g. MTR-1 Young's modulus = 70 GPa)
become trusted anchor points. Any future computation is compared
against the anchor. Drift beyond threshold signals that simulation
correction is required.

This is the foundational link between verification and simulation
accuracy: without verified anchors, you cannot know what your
simulation is drifting from.

### V&V Thresholds (summary)

| Parameter | Value |
|-----------|-------|
| drift_threshold_pct | 5.0% |
| anchor_value (MTR-1 default) | 70000000000.0 Pa |
| drift_detected (no-drift case) | False |
| drift_detected (drift case, >5%) | True |

---

*Index authority: MetaGenesis Core / SCI-01. Append new claims as table rows under new headings.*
