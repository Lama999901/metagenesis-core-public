# Architecture

## The verification proof loop

```
Your computation runs
(ML model, calibration, FEM simulation, data pipeline, ...)
           │
           ▼
    runner.run_job()
    backend/progress/runner.py
           │
           ├──── normal mode (authoritative)
           └──── canary mode (non-authoritative health check)
                                 │
                                 ▼
              run_artifact.json + ledger_snapshot.jsonl
              ├── job_snapshot (computation result + inputs)
              ├── execution_trace (4-step cryptographic chain)
              ├── trace_root_hash (SHA-256 of full chain)
              └── canary_mode flag
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
              mg.py verify --pack bundle.zip
              scripts/mg.py
                ├── Layer 1: integrity (SHA-256 — detects file changes)
                ├── Layer 2: semantic  (detects content removal/substitution)
                └── Layer 3: step chain (detects execution tampering)
                         │
                         ▼
                    PASS or FAIL
                    (with specific reason and layer that failed)
```

Full protocol spec: [PROTOCOL.md](PROTOCOL.md)

---

## Three verification layers — why each is necessary

**The hierarchy of attacks:**

```
Attack 1: modify a file after packaging
→ Layer 1 (SHA-256) catches it
→ Layer 2 and 3 never reached

Attack 2: strip job_snapshot, recompute all hashes
→ Layer 1: PASS (hashes match)
→ Layer 2 (semantic): FAIL — job_snapshot missing
→ Layer 3 never reached

Attack 3: change computation inputs, recompute hashes
→ Layer 1: PASS
→ Layer 2: PASS (job_snapshot still present)
→ Layer 3 (step chain): FAIL — trace_root_hash broken
```

Each layer catches exactly what the previous layer misses. All three run on
every `mg.py verify`. Each proven by a dedicated adversarial test.

---

## Step Chain — execution trace integrity

Every claim execution produces a 4-step cryptographic hash chain:

```
init_params       → hash_1 = SHA256(inputs + "genesis")
compute           → hash_2 = SHA256(computation_outputs + hash_1)
metrics           → hash_3 = SHA256(metric_values + hash_2)
threshold_check   → trace_root_hash = SHA256(pass/fail + hash_3)
```

`trace_root_hash` = SHA256 fingerprint of the entire execution sequence.
Change any input, skip any step, reorder anything → `trace_root_hash` breaks.

This is not blockchain. No network. No consensus. No tokens.
Same concept as git commits (each commits to its parent).
Implemented in stdlib only. Works offline.

Implementation: `backend/progress/mlbench1_accuracy_certificate.py :: _hash_step()`
(same pattern in all 14 claims)

---

## Physical Anchor Chain (Cross-Claim Chain)

For physical domains, individual claim verification extends to end-to-end
chain verification. The `trace_root_hash` of one claim becomes `anchor_hash`
input to the next claim's Step Chain:

```
Physical reality:  E = 70 GPa  (aluminum — measured in thousands of labs worldwide)
        │
        ▼
MTR-1   trace_root_hash = "abc..."
        calibration against physical constant → rel_err ≤ 1% → PASS
        │
        │  anchor_hash = "abc..." baked into DT-FEM-01 init_params
        ▼
DT-FEM-01  trace_root_hash = "def..."
           FEM output vs physical reference → rel_err ≤ 2% → PASS
           Any change to MTR-1 → "abc..." changes → "def..." breaks
        │
        │  anchor_hash = "def..." baked into DRIFT-01 init_params
        ▼
DRIFT-01   trace_root_hash = "ghi..."
           drift vs anchor → drift ≤ 5% → PASS
           Any change to DT-FEM-01 or MTR-1 → all downstream hashes break
```

DRIFT-01's `trace_root_hash` cryptographically commits to the entire chain
from physical measurement to current simulation state.

Verified offline with one command. No FEM solver. No simulation environment.
No trust.

---

## Governance loop

```
Every pull request
        │
        ▼
  steward_audit.py
  scripts/steward_audit.py
        │
        ├── required files present?
        ├── runner dispatch kinds == claim_index job_kinds?  ← bidirectional
        └── canonical_state claims == claim_index claims?   ← bidirectional
                │
          all pass?
            │        │
           YES        NO
            │        │
         merge     blocked
```

No claim without implementation.
No implementation without claim.
Enforced on every PR — not by human review. Not periodically.
On every single merge.

---

## Policy-gate immutable anchors

```
.github/workflows/mg_policy_gate.yml
        │
        runs on every PR
        │
        ▼
scripts/mg_policy_gate.py
        │
        reads scripts/mg_policy_gate_policy.json
        │
        ├── locked_paths: [canonical_state.md, evidence_index.json, steward_audit.py]
        │   Any PR touching these → BLOCKED regardless of content
        │
        └── allow_globs: [scripts/**, tests/**, backend/progress/**, ...]
            Any file not matching → BLOCKED
```

No cryptographic key custody. No external timestamping. Works offline.
Evidence artifacts are immutable once locked — enforced by CI, not convention.

---

## Dual-mode canary pipeline

```
runner.run_job(job_id, canary_mode=False)
  → ledger actor: "scheduler_v1"
  → ledger action: "job_completed"
  → canary_mode: false
  → authoritative evidence slot

runner.run_job(job_id, canary_mode=True)
  → ledger actor: "scheduler_v1_canary"
  → ledger action: "job_completed_canary"
  → canary_mode: true
  → non-authoritative canary slot
```

Same computation. Different authority metadata.
Continuous health monitoring without contaminating authoritative evidence.
Semantic verifier checks canary_mode flag consistency per bundle slot.

---

## Active claims

| Claim | File | Domain | Step Chain | Physical Anchor |
|-------|------|--------|------------|-----------------|
| MTR-1 | mtr1_calibration.py | Materials | ✓ | E = 70 GPa |
| MTR-2 | mtr2_thermal_conductivity.py | Materials | ✓ | Physical constant |
| MTR-3 | mtr3_thermal_multilayer.py | Materials | ✓ | Physical constant |
| SYSID-01 | sysid1_arx_calibration.py | System ID | ✓ | — |
| DATA-PIPE-01 | datapipe1_quality_certificate.py | Data | ✓ | — |
| DRIFT-01 | drift_monitor.py | Drift | ✓ | MTR-1 anchor |
| ML_BENCH-01 | mlbench1_accuracy_certificate.py | ML/AI | ✓ | — |
| DT-FEM-01 | dtfem1_displacement_verification.py | Digital Twin | ✓ | MTR-1 anchor |
| ML_BENCH-02 | mlbench2_regression_certificate.py | ML/AI | ✓ | — |
| ML_BENCH-03 | mlbench3_timeseries_certificate.py | ML/AI | ✓ | — |
| PHARMA-01 | pharma1_admet_certificate.py | Pharma | ✓ | — |
| FINRISK-01 | finrisk1_var_certificate.py | Finance | ✓ | — |
| DT-SENSOR-01 | dtsensor1_iot_certificate.py | Digital Twin | ✓ | — |
| DT-CALIB-LOOP-01 | dtcalib1_convergence_certificate.py | Digital Twin | ✓ | DRIFT-01 anchor |

All 14 claims have Step Chain (execution_trace + trace_root_hash).
DT-FEM-01 and DRIFT-01 support anchor_hash for Cross-Claim Chain.

---

## Test coverage map

| Test file | What it proves |
|-----------|---------------|
| `test_cert01_pack_manifest_verify.py` | Integrity layer: SHA-256 + root_hash |
| `test_cert02_*` | Semantic layer: bypass attack caught |
| `test_cert03_step_chain_verify.py` | Step Chain layer: tamper detection in verifier |
| `test_step_chain_all_claims.py` | Step Chain present and valid in all 14 claims |
| `test_cross_claim_chain.py` | Cross-Claim Chain: anchor_hash links MTR-1→DT-FEM-01→DRIFT-01 |
| `test_stew01-07_*` | Governance: bidirectional coverage, steward audit |
| `test_drift01_*` | DRIFT-01 calibration anchor |
| Domain tests | Pass/fail/adversarial per claim |

223 tests total. steward_audit PASS.

---

*Architecture v0.2 — 2026-03-15 — MetaGenesis Core*
