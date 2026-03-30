# AGENTS.md — Rules for AI Agents Working in This Repo

This file tells Cursor, Claude, Copilot, and any other AI agent
the rules of this repository. Read this before making any change.

---

## HOW TO FULLY ORIENT YOURSELF (read these files in order)

```
1. CONTEXT_SNAPSHOT.md   ← start here: current state, done, pending, contacts
2. AGENTS.md             ← this file: rules, forbidden terms, workflow
3. README.md             ← architecture, claims, quickstart
4. llms.txt              ← AI-optimized summary of entire repo
5. reports/canonical_state.md    ← verified claim list
6. reports/scientific_claim_index.md  ← all 20 claims with thresholds
7. reports/known_faults.yaml     ← known limitations, do not overclaim
8. docs/PROTOCOL.md      ← full protocol specification
```

After reading these 8 files you can answer any question about this project.

---

---

## What this repo is

MetaGenesis Core is an open verification protocol layer.
It implements the MetaGenesis Verification Protocol (MVP) v0.6.
It makes computational claims tamper-evident, reproducible, and
independently auditable offline by any third party.

It is NOT a simulation platform.
It is NOT an AI coordination system.
It is NOT a molecular assembler or bio-computational system.
It IS a governance + evidence + verification pipeline.

---

## Hard rules — never violate these

**1. Never invent implementations.**
If a file, function, or test does not exist in the repo,
say: "Not found in current project context. Please add: <path>"
Do not generate placeholder code and claim it is real.

**2. steward_audit must PASS after every change.**
Before completing any task, run:
python scripts/steward_audit.py
If it outputs anything other than STEWARD AUDIT: PASS — stop and fix.

**3. Never use forbidden language.**
Forbidden: "tamper-proof", "impossible", "unforgeable", "100% test success",
"19x performance", "GPT-5 integration", "VacuumGenesisEngine", "500+ modules"
Required: "tamper-evident under trusted verifier assumptions"

**4. Never add a claim without all four components.**
A claim requires ALL of:
  a) implementation file in backend/progress/
  b) test file in tests/
  c) entry in reports/scientific_claim_index.md (with job_kind in backticks)
  d) claim_id added to reports/canonical_state.md current_claims_list

**5. Never touch these without explicit instruction.**
- reports/canonical_state.md (except to add claim to current_claims_list)
- reports/known_faults.yaml (do not remove or downgrade any fault entry)
- scripts/steward_audit.py
- scripts/mg_policy_gate_policy.json
- tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py
- ppa/CLAIMS_DRAFT.md (frozen — incorporated by reference into USPTO PPA)
- docs/ROADMAP.md (do not change version numbers)
- .github/workflows/

**6. Separate FACTS from ASSUMPTIONS.**
Every technical claim must reference: file path + function name.
If you are not sure something exists, say so explicitly.

---

## How to add a new claim (correct procedure)

Step 1 — Create implementation:
File: backend/progress/<claim_id_lower>.py
Required: JOB_KIND constant, run_*() function returning dict with mtr_phase key

Step 2 — Register in runner:
File: backend/progress/runner.py, function _execute_job_logic()
Add dispatch block following the exact pattern of existing claims

Step 3 — Add to claim index:
File: reports/scientific_claim_index.md
Add section with: claim_id, domain, job_kind (in backticks), V&V thresholds,
reproduction command, use case examples

Step 4 — Update canonical state:
File: reports/canonical_state.md
Add claim_id to current_claims_list pipe-separated value

Step 5 — Write tests:
File: tests/<domain>/test_<claim_id_lower>.py
Required: test pass case, test fail case, test adversarial edge case,
test mtr_phase key present, test determinism (same seed → same result)

Step 6 — Verify:
python scripts/steward_audit.py → STEWARD AUDIT: PASS
python -m pytest tests/ -q → 595 passed
python scripts/deep_verify.py → ALL 13 TESTS PASSED

---

## Active claims and their locations

| Claim | File | Test |
|-------|------|------|
| MTR-1 | backend/progress/mtr1_calibration.py | tests/materials/ |
| MTR-2 | backend/progress/mtr2_thermal_conductivity.py | tests/materials/ |
| MTR-3 | backend/progress/mtr3_thermal_multilayer.py | tests/materials/ |
| SYSID-01 | backend/progress/sysid1_arx_calibration.py | tests/systems/ |
| DATA-PIPE-01 | backend/progress/datapipe1_quality_certificate.py | tests/data/ |
| DRIFT-01 | backend/progress/drift_monitor.py | tests/steward/ |
| ML_BENCH-01 | backend/progress/mlbench1_accuracy_certificate.py | tests/ml/ |
| DT-FEM-01 | backend/progress/dtfem1_displacement_verification.py | tests/digital_twin/ |
| ML_BENCH-02 | backend/progress/mlbench2_regression_certificate.py | tests/ml/ |
| ML_BENCH-03 | backend/progress/mlbench3_timeseries_certificate.py | tests/ml/ |
| PHARMA-01 | backend/progress/pharma1_admet_certificate.py | tests/ml/ |
| FINRISK-01 | backend/progress/finrisk1_var_certificate.py | tests/ml/ |
| DT-SENSOR-01 | backend/progress/dtsensor1_iot_certificate.py | tests/digital_twin/ |
| DT-CALIB-LOOP-01 | backend/progress/dtcalib1_convergence_certificate.py | tests/digital_twin/ |
| AGENT-DRIFT-01 | backend/progress/agent_drift_monitor.py | tests/steward/ |
| MTR-4 | backend/progress/mtr4_titanium_calibration.py | tests/materials/ |
| MTR-5 | backend/progress/mtr5_steel_calibration.py | tests/materials/ |
| MTR-6 | backend/progress/mtr6_copper_conductivity.py | tests/materials/ |

---

## Acceptance commands (run before any commit)

python scripts/steward_audit.py
python -m pytest tests/ -q
python demos/open_data_demo_01/run_demo.py
grep -r "tamper-proof\|GPT-5\|19x\|VacuumGenesis\|Infinity Protocol" docs/ scripts/ backend/ tests/
# → must return empty

# Full proof-not-trust (13 tests including bypass attack + Cross-Claim Chain + Ed25519 + Temporal):
python scripts/deep_verify.py
# → ALL 13 TESTS PASSED

All must pass.

---

## Architecture in one paragraph

Job runs via runner.run_job() → produces run_artifact.json (with execution_trace + trace_root_hash)
+ ledger_snapshot.jsonl → evidence_index maps artifacts to claims → steward_submission_pack bundles
everything → mg.py verify runs five independent layers:
  Layer 1: SHA-256 integrity (file modification)
  Layer 2: semantic (job_snapshot present, canary_mode correct, payload.kind matches)
  Layer 3: step chain (trace_root_hash == final execution step hash)
  Layer 4: bundle signing (HMAC-SHA256 or Ed25519 signature verification)
  Layer 5: temporal commitment (NIST Beacon pre-commitment proves WHEN signed)
→ PASS or FAIL with specific layer and reason.
For physical domains: anchor_hash embeds upstream trace_root_hash into downstream Step Chain
(MTR-1 → DT-FEM-01 → DRIFT-01 cryptographically linked end-to-end).
Steward_audit enforces bidirectional coverage: runner kinds == claim_index kinds == canonical_state.
Protocol specification: docs/PROTOCOL.md. Architecture: docs/ARCHITECTURE.md.
