# Architecture

## The verification proof loop

```
Your computation runs
(ML model, calibration, data pipeline, risk model, ...)
           │
           ▼
    runner.run_job()
    backend/progress/runner.py
           │
           ├──── normal mode ────┐
           │                     │
           └──── canary mode ────┤
                                 │
                                 ▼
              run_artifact.json + ledger_snapshot.jsonl
              (per claim, per mode)
                                 │
                                 ▼
              evidence_index.json
              backend/progress/evidence_index.py
                                 │
                                 ▼
              Submission Pack
              scripts/steward_submission_pack.py
                ├── pack_manifest.json  (SHA-256 + root_hash)
                ├── evidence_index.json
                ├── claims/dossier_<ID>.md
                └── evidence/<CLAIM_ID>/
                      ├── normal/run_artifact.json
                      ├── normal/ledger_snapshot.jsonl
                      ├── canary/run_artifact.json
                      └── canary/ledger_snapshot.jsonl
                                 │
                                 ▼
              mg.py verify
              scripts/mg.py
                ├── integrity check (SHA-256 — detects file changes)
                └── semantic check  (detects content removal)
                         │
                         ▼
                    PASS or FAIL
                    (with specific reason)
```

Full protocol spec: [PROTOCOL.md](PROTOCOL.md)

---

## Why two verification layers

**Integrity alone is not enough.**

An adversary can:
1. Remove job_snapshot from run_artifact.json
2. Recompute all SHA-256 hashes
3. Produce a bundle where integrity = PASS

Semantic verification catches this:
- integrity: PASS (hashes match)
- semantic: FAIL (job_snapshot missing)

Proven by adversarial test:
`tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`
`::test_semantic_negative_missing_job_snapshot_fails_verify`

---

## Governance loop

```
Every pull request
        │
        ▼
  steward_audit.py
        │
        ├── required files exist?
        ├── phase 42 locked?
        ├── runner dispatch kinds == claim_index job_kinds?
        └── canonical_state claims == claim_index claims?
                │
         all pass?
           │        │
          YES        NO
           │        │
        merge    blocked
```

No claim without implementation.
No implementation without claim.
Enforced on every PR — not by human review.

---

## Calibration anchor and drift

```
Verified result (e.g. MTR-1: E = 70 GPa)
        │
        ▼
   DRIFT-01 anchor point
        │
   New computation: E = 76 GPa
        │
   drift = |76 - 70| / 70 * 100 = 8.6%
        │
   threshold = 5.0%
        │
   drift_detected = True
   correction_required = True
```

---

## ML accuracy certification

```
Model predictions (y_true / y_pred)
        │
        ▼
   ML_BENCH-01 run_certificate()
        │
        ├── synthetic mode (seed → deterministic dataset)
        └── real data mode (CSV + SHA-256 fingerprint)
        │
        ▼
   metrics: accuracy, precision, recall, F1
        │
   |actual_accuracy - claimed_accuracy| <= tolerance?
        │
   PASS or FAIL
```

---

## Active claims

| Claim | File | job_kind | Domain |
|-------|------|---------|--------|
| MTR-1 | backend/progress/mtr1_calibration.py | mtr1_youngs_modulus_calibration | Materials |
| MTR-2 | backend/progress/mtr2_thermal_conductivity.py | mtr2_thermal_paste_conductivity_calibration | Materials |
| MTR-3 | backend/progress/mtr3_thermal_multilayer.py | mtr3_thermal_multilayer_contact_calibration | Materials |
| SYSID-01 | backend/progress/sysid1_arx_calibration.py | sysid1_arx_calibration | System ID |
| DATA-PIPE-01 | backend/progress/datapipe1_quality_certificate.py | datapipe1_quality_certificate | Data |
| DRIFT-01 | backend/progress/drift_monitor.py | drift_calibration_monitor | Drift |
| ML_BENCH-01 | backend/progress/mlbench1_accuracy_certificate.py | mlbench1_accuracy_certificate | ML/AI |

---

## Supporting files

| File | Role |
|------|------|
| `system_manifest.json` | Top-level project identity and version metadata. Not a claim artifact; not part of evidence bundles. Referenced by external tooling only. |
| `phase_registry.json` | Pointer to `reports/phase_registry_v0_1.md`. Legacy phase artifact registry. Phase 42 locked status enforced by steward_audit via `reports/phase_registry_v0_1.md`. |
| `reports/phase_registry_v0_1.md` | Machine-readable phase registry. steward_audit parses this to verify phase 42 locked — a required governance invariant under the Third Innovation (Policy-Gate Immutable Evidence Anchors). |
