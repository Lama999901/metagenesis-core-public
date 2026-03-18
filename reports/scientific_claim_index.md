# Scientific Claim Index v0.4

Documentation-only registry of domain claims so new cases remain uniquely
structured and submission-ready. No code or policy changes; docs only.

---

## MTR-1

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **domain** | Materials Science |
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
| **domain** | Materials Science |
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
| **domain** | Materials Science |
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
| **domain** | Data Pipeline |
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
| **domain** | System Identification |
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
| **domain** | Simulation Correction / Calibration Traceability |
| **job_kind** | `drift_calibration_monitor` |
| **reproduction** | `python -m pytest tests/steward/test_drift01_calibration_anchor.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result`. Contains mtr_phase, inputs (anchor_claim_id, anchor_value, anchor_units, current_value, drift_threshold_pct), result (anchor_value, current_value, drift_pct, drift_threshold_pct, drift_detected, correction_required). |
| **V&V thresholds** | drift_threshold_pct 5.0%; drift_detected False when within threshold; drift_detected True when >5%. |
| **notes (canary vs normal)** | Same job kind runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts for both. |

### Purpose

Verified calibration results (e.g. MTR-1 Young's modulus = 70 GPa) become trusted
anchor points. Any future computation is compared against the anchor. Drift beyond
threshold signals that simulation correction is required.

### V&V Thresholds (summary)

| Parameter | Value |
|-----------|-------|
| drift_threshold_pct | 5.0% |
| anchor_value (MTR-1 default) | 70000000000.0 Pa |
| drift_detected (no-drift case) | False |
| drift_detected (drift case, >5%) | True |

---

## ML_BENCH-01

| Field | Value |
|-------|--------|
| **claim_id** | ML_BENCH-01 |
| **domain** | Machine Learning / AI Benchmarking |
| **job_kind** | `mlbench1_accuracy_certificate` |
| **reproduction** | `python -m pytest tests/ml/test_mlbench01_accuracy_certificate.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result`. Contains `mtr_phase` (ML_BENCH-01), `inputs` (seed, claimed_accuracy, accuracy_tolerance, n_samples, n_features, noise_scale, mode), `result` (actual_accuracy, claimed_accuracy, absolute_error, tolerance, pass, precision, recall, f1, n_samples), `execution_trace` (4-step cryptographic chain: init_params → generate_dataset → compute_metrics → threshold_check; each step hashes previous step), `trace_root_hash` (SHA-256 of full chain — tampering any step invalidates root hash). |
| **V&V thresholds** | `abs(actual_accuracy - claimed_accuracy) <= accuracy_tolerance` (default tolerance 0.02). `result.pass` must be True for certificate to be valid. |
| **notes (canary vs normal)** | Same as all other claims: job runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts produced for both; canary marked in artifact `canary_mode: true`. |

## ML_BENCH-02

| Field | Value |
|-------|--------|
| **claim_id** | ML_BENCH-02 |
| **domain** | Machine Learning / AI — Regression |
| **job_kind** | `mlbench2_regression_certificate` |
| **reproduction** | `python -m pytest tests/ml/test_mlbench02_regression_certificate.py -v` |
| **evidence_fields** | `mtr_phase` (ML_BENCH-02), `inputs` (seed, claimed_rmse, rmse_tolerance, n_samples, n_features, noise_scale, mode), `result` (actual_rmse, claimed_rmse, absolute_error, tolerance, pass, mae, r2, n_samples), `execution_trace` (4-step chain), `trace_root_hash`. |
| **V&V thresholds** | `abs(actual_rmse - claimed_rmse) <= rmse_tolerance` (default 0.02). `result.pass` must be True. |
| **notes (canary vs normal)** | Same as ML_BENCH-01: runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts for both. |

## ML_BENCH-03

| Field | Value |
|-------|--------|
| **claim_id** | ML_BENCH-03 |
| **domain** | Machine Learning / AI — Time-Series Forecasting |
| **job_kind** | `mlbench3_timeseries_certificate` |
| **reproduction** | `python -m pytest tests/ml/test_mlbench03_timeseries_certificate.py -v` |
| **V&V thresholds** | `abs(actual_mape - claimed_mape) <= mape_tolerance` (default 0.02). `result.pass` must be True. |

## PHARMA-01

| Field | Value |
|-------|--------|
| **claim_id** | PHARMA-01 |
| **domain** | Pharma / ADMET — Prediction Certificate |
| **job_kind** | `pharma1_admet_certificate` |
| **reproduction** | `python -m pytest tests/ml/test_pharma01_admet_certificate.py -v` |
| **V&V thresholds** | `abs(predicted_value - claimed_value) <= tolerance`. `result.pass` must be True. FDA 21 CFR Part 11 compatible. |

## FINRISK-01

| Field | Value |
|-------|--------|
| **claim_id** | FINRISK-01 |
| **domain** | Financial Risk — VaR Model Certificate |
| **job_kind** | `finrisk1_var_certificate` |
| **reproduction** | `python -m pytest tests/ml/test_finrisk01_var_certificate.py -v` |
| **V&V thresholds** | `abs(actual_var - claimed_var) <= var_tolerance`. `result.pass` must be True. Basel III/IV alignment. |

## DT-SENSOR-01

| Field | Value |
|-------|--------|
| **claim_id** | DT-SENSOR-01 |
| **domain** | Digital Twin — IoT Sensor Data Integrity |
| **job_kind** | `dtsensor1_iot_certificate` |
| **reproduction** | `python -m pytest tests/digital_twin/test_dtsensor01_iot_certificate.py -v` |
| **V&V thresholds** | Schema, range, temporal validation; no issues. `result.pass` must be True. |

## DT-CALIB-LOOP-01

| Field | Value |
|-------|--------|
| **claim_id** | DT-CALIB-LOOP-01 |
| **domain** | Digital Twin — Calibration Convergence |
| **job_kind** | `dtcalib1_convergence_certificate` |
| **reproduction** | `python -m pytest tests/digital_twin/test_dtcalib1_convergence_certificate.py -v` |
| **V&V thresholds** | Drift monotonically decreasing; final drift_pct <= convergence_threshold. `result.pass` must be True. |

### Purpose

Any ML model that claims a specific accuracy can have that claim packaged into
a tamper-evident evidence bundle. A third party verifies it offline with one
command — PASS or FAIL — without access to the model, training data, or
compute environment.

Supports two modes:
- **Synthetic mode** (default): deterministic dataset generated from seed. Same seed → same result always. Used for baseline certification and regression testing.
- **Real data mode**: CSV with `y_true`/`y_pred` columns. SHA-256 fingerprinted. Used for certifying actual model predictions.

### V&V Thresholds (summary)

| Parameter | Value |
|-----------|-------|
| accuracy_tolerance (default) | 0.02 (±2 percentage points) |
| pass condition | `abs(actual_accuracy - claimed_accuracy) <= tolerance` |
| minimum test samples | 10 |
| adversarial test | noise_scale=1.0 → FAIL (accuracy degrades below tolerance) |

### Use case examples

**AI benchmark certification:** A team claims 94.3% accuracy on a held-out test
set. ML_BENCH-01 packages the predictions (y_true/y_pred CSV, SHA-256 fingerprinted)
into a bundle. Any reviewer verifies: `mg.py verify --pack bundle.zip` → PASS or FAIL.
No model access required.

**SOTA claim verification:** A paper claims state-of-the-art results. Bundle the
predictions. Any third party offline verification. Evidence is tamper-evident
under trusted verifier assumptions.

**Regulatory submission:** FDA, EMA, or financial regulator requires model
performance evidence. Bundle contains: dataset fingerprint, predictions, accuracy
metrics, drift monitoring against approved baseline.

---

## DT-FEM-01

| Field | Value |
|-------|--------|
| **claim_id** | DT-FEM-01 |
| **domain** | Digital Twin / FEM Verification |
| **job_kind** | `dtfem1_displacement_verification` |
| **reproduction** | `python -m pytest tests/digital_twin/test_dtfem01_displacement_verification.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result`. Contains `mtr_phase` (DT-FEM-01), `inputs` (seed, reference_value, rel_err_threshold, noise_scale, quantity, units), `result` (fem_value, reference_value, rel_err, rel_err_threshold, pass, quantity, units, method, algorithm_version). Real data mode adds: per_row list, max_rel_err, n_points, dataset fingerprint. |
| **V&V thresholds** | `rel_err <= 0.02` (2%). For real data mode: `max_rel_err <= rel_err_threshold`. `result.pass` must be True for certificate to be valid. |
| **notes (canary vs normal)** | Same as all other claims: job runs in normal or canary mode via `run_job(..., canary_mode=...)`; evidence artifacts produced for both; canary marked in artifact `canary_mode: true`. |

### Purpose

Any FEM or simulation solver (ANSYS, FEniCS, OpenFOAM, COMSOL, custom)
produces a computed physical value. DT-FEM-01 packages that computed value
alongside the physical reference measurement (lab result, known constant)
into a tamper-evident evidence bundle. A third party verifies:
`mg.py verify --pack bundle.zip` → PASS or FAIL — offline, without access
to the FEM solver, model, or compute environment.

This is the universal verification layer for digital twin calibration.
The verified result becomes a trusted anchor for DRIFT-01 monitoring:
as the twin evolves, drift against the anchor is quantified and
correction requirements are signalled automatically.

Supports two modes:
- **Synthetic mode** (default): deterministic FEM/reference pair from seed.
  Same seed → same result always. Used for baseline certification.
- **Real data mode**: CSV with `fem_value`/`measured_value`/`quantity` columns.
  SHA-256 fingerprinted. Used for certifying actual FEM solver outputs.

### V&V Thresholds (summary)

| Parameter | Value |
|-----------|-------|
| rel_err_threshold (default) | 0.02 (2% relative error) |
| pass condition | `rel_err <= rel_err_threshold` |
| real data pass condition | `max_rel_err <= rel_err_threshold` |
| adversarial test | noise_scale=0.5 → FAIL (rel_err >> 0.02) |

### Use case examples

**Structural engineering:** FEM predicts max displacement 12.3 mm under
load. Lab measures 12.1 mm. rel_err = 1.6% < 2% → PASS. Bundle sent to
client contains: FEM output, reference measurement, error, threshold —
independently verifiable with one command.

**Thermal simulation:** CFD predicts junction temperature 85.2°C.
Thermocouple reads 84.0°C. rel_err = 1.4% < 2% → PASS. Bundle is the
evidence for regulatory submission — no model access required.

**Digital twin calibration loop:** MTR-1 verifies E=70 GPa (anchor).
FEM runs with this property. DT-FEM-01 verifies FEM displacement output.
DRIFT-01 monitors drift as real-world measurements accumulate.
Each step is independently verifiable — the full calibration chain
is tamper-evident.

---

---

## Protocol Capabilities (v0.4)

### 5-Layer Verification Architecture

The MetaGenesis Verification Protocol implements 5 independent verification layers.
Each layer catches attacks that the other 4 miss. Independence proven by
`tests/steward/test_cert_5layer_independence.py`.

| Layer | Name | What it catches | Proof |
|-------|------|-----------------|-------|
| 1 | SHA-256 Integrity | File modified after packaging | `pack_manifest.json root_hash` |
| 2 | Semantic | Evidence stripped, hashes recomputed | `test_cert02` |
| 3 | Step Chain | Computation inputs changed, steps reordered | `test_cert03` |
| 4 | Bundle Signing | Unauthorized bundle creator, signature tampering | `test_cert07` + `test_cert09` |
| 5 | Temporal Commitment | Backdated bundles, timestamp forgery | `test_cert10` |

### Ed25519 Asymmetric Signing (Innovation #6 upgrade)

Bundle signing supports dual algorithms:
- **HMAC-SHA256**: Shared-secret signing for same-organization workflows
- **Ed25519**: Asymmetric signing for third-party auditor verification

Ed25519 provides cryptographic proof of WHO created the bundle without sharing
private key material. Key generation, signing, and verification via `scripts/mg_sign.py`.
Pure-Python Ed25519 implementation in `scripts/mg_ed25519.py` validated against
RFC 8032 test vectors.

| Component | File |
|-----------|------|
| Ed25519 implementation | `scripts/mg_ed25519.py` |
| Signing CLI (dual algorithm) | `scripts/mg_sign.py` |
| Ed25519 attack proofs | `tests/steward/test_cert09_ed25519_attacks.py` |
| Bundle signing tests | `tests/steward/test_cert07_bundle_signing.py` |
| Ed25519 unit tests | `tests/steward/test_ed25519.py` |

### Temporal Commitment (Innovation #7, Layer 5)

Cryptographic proof of WHEN a bundle was signed using NIST Randomness Beacon 2.0
pre-commitment scheme:

1. Compute `pre_commitment = SHA-256(root_hash)` before fetching beacon
2. Fetch NIST Beacon pulse (random value + timestamp)
3. Compute `temporal_binding = SHA-256(pre_commitment || beacon_value)`
4. Store all three values in `temporal_commitment.json`

Verification checks that `temporal_binding` matches recomputed value from
`pre_commitment` and `beacon_value`. The ordering guarantee (pre-commitment
before beacon) prevents backdating.

| Component | File |
|-----------|------|
| Temporal commitment module | `scripts/mg_temporal.py` |
| Temporal attack proofs | `tests/steward/test_cert10_temporal_attacks.py` |
| Temporal unit tests | `tests/steward/test_temporal.py` |

---

*Index authority: MetaGenesis Core / SCI-01 v0.4. Append new claims as sections.*
