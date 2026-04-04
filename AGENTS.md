# AGENTS.md — Rules for AI Agents Working in This Repo

> v0.9.0 | 20 claims | 1750 tests | 19 agent checks
> This file tells Cursor, Claude, Copilot, and any AI agent the rules of this repo.
> Read CLAUDE.md first — it is always more current and wins all conflicts.

---

## MISSION IN ONE SENTENCE

MetaGenesis Core is a **notary for computations** — we certify that a computer
produced exactly this result, at exactly this time, in exactly this way.
Without access to the computer. Without trusting anyone. In 60 seconds.

The first paying customer ($299) is the top commercial priority.
Every change must serve credibility, adoption, or client conversion.

---

## HOW TO FULLY ORIENT YOURSELF (read in order)

```
1. CLAUDE.md             ← PRIMARY: mission, traps, technical rules — READ FIRST
2. AGENTS.md             ← this file: hard rules, claim procedure
3. README.md             ← architecture, claims, quickstart
4. llms.txt              ← LLM-optimized repo summary
5. reports/canonical_state.md    ← verified claim list (LOCKED)
6. reports/scientific_claim_index.md  ← all 20 claims with thresholds
7. reports/known_faults.yaml     ← known limitations, do not overclaim
8. docs/PROTOCOL.md      ← full protocol specification
```

Before any task: `python scripts/agent_learn.py recall`

---

## What this repo is

MetaGenesis Core is an open verification protocol layer.
It implements the MetaGenesis Verification Protocol (MVP) v0.9.
It makes computational claims tamper-evident, reproducible, and
independently auditable offline by any third party.

It is NOT a simulation platform.
It is NOT an AI coordination system.
It IS a governance + evidence + verification pipeline.
It IS patent pending (USPTO #63/996,819).

---

## Hard rules — never violate these

**1. Never invent implementations.**
If a file, function, or test does not exist in the repo, say:
"Not found in current project context. Please add: <path>"
Do not generate placeholder code and claim it is real.

**2. steward_audit must PASS after every change.**
```bash
python scripts/steward_audit.py
# → STEWARD AUDIT: PASS (required before any merge)
```

**3. Never use forbidden language.**
```
FORBIDDEN → CORRECT
"tamper-proof" → "tamper-evident"
"blockchain" → "cryptographic hash chain"
"unforgeable" → don't use
"GPT-5" → doesn't exist
"100% test success" → "1750 tests PASS"
"595 tests" / "601 tests" → "1750 tests"
"v0.6" / "v0.7" → "v0.9.0"
```

**4. Never add a claim without ALL components (use GSD).**
A claim requires:
  a) backend/progress/<claim_id>.py with 4-step Step Chain
  b) backend/progress/runner.py dispatch block
  c) reports/scientific_claim_index.md entry
  d) reports/canonical_state.md current_claims_list update
  e) tests/<domain>/test_<claim_id>.py (pass/fail/determinism)
  f) Counter update everywhere + check_stale_docs.py (UPDATE_PROTOCOL v1.1)

**5. Never touch sealed files.**
```
reports/canonical_state.md       ← policy-gate locked
reports/known_faults.yaml        ← never remove/downgrade entries
scripts/steward_audit.py         ← SEALED
scripts/mg_policy_gate_policy.json ← SEALED
ppa/CLAIMS_DRAFT.md              ← FROZEN (USPTO)
.github/workflows/               ← CI gates, add only
```

**6. Separate FACTS from ASSUMPTIONS.**
Every technical claim must reference: file path + function name.
If not sure something exists — say so explicitly.

**7. Always use GSD for claims/agents/counters.**
Manual edits without GSD = invisible tails in check_stale_docs.py rules.

---

## How to add a new claim (always via GSD)

```
/gsd:quick "Add claim <CLAIM-ID> following ALL 6 steps from UPDATE_PROTOCOL.md..."
```

Manual procedure (only if GSD unavailable):

Step 1 — Implementation: backend/progress/<claim_id_lower>.py
  Required: JOB_KIND constant, 4-step Step Chain, return dict with mtr_phase key

Step 2 — Runner dispatch: backend/progress/runner.py → _execute_job_logic()

Step 3 — Claim index: reports/scientific_claim_index.md
  Add: claim_id, domain, job_kind, V&V thresholds, reproduction command

Step 4 — Canonical state: reports/canonical_state.md → current_claims_list

Step 5 — Tests: tests/<domain>/test_<claim_id_lower>.py
  Required: pass case, fail case, adversarial edge, mtr_phase key, determinism

Step 6 — Update ALL counters AND check_stale_docs.py required strings (same PR):
```bash
python scripts/steward_audit.py  # → STEWARD AUDIT: PASS
python -m pytest tests/ -q       # → 1750 passed
python scripts/deep_verify.py    # → ALL 13 TESTS PASSED
python scripts/agent_pr_creator.py --summary  # → No auto-pr needed
```

---

## Active claims and their locations

| Claim | File | Domain | Test |
|-------|------|--------|------|
| MTR-1 | backend/progress/mtr1_calibration.py | Materials (Al E=70GPa) | tests/materials/ |
| MTR-2 | backend/progress/mtr2_thermal_conductivity.py | Materials (thermal) | tests/materials/ |
| MTR-3 | backend/progress/mtr3_thermal_multilayer.py | Materials (multilayer) | tests/materials/ |
| MTR-4 | backend/progress/mtr4_titanium_calibration.py | Materials (Ti E=114GPa) | tests/materials/ |
| MTR-5 | backend/progress/mtr5_steel_calibration.py | Materials (SS E=193GPa) | tests/materials/ |
| MTR-6 | backend/progress/mtr6_copper_conductivity.py | Materials (Cu k=401) | tests/materials/ |
| PHYS-01 | backend/progress/phys01_boltzmann.py | Physics (kB SI2019) | tests/physics/ |
| PHYS-02 | backend/progress/phys02_avogadro.py | Physics (NA SI2019) | tests/physics/ |
| SYSID-01 | backend/progress/sysid1_arx_calibration.py | System ID | tests/systems/ |
| DATA-PIPE-01 | backend/progress/datapipe1_quality_certificate.py | Data Pipelines | tests/data/ |
| DRIFT-01 | backend/progress/drift_monitor.py | Drift Monitoring | tests/steward/ |
| ML_BENCH-01 | backend/progress/mlbench1_accuracy_certificate.py | ML Classification | tests/ml/ |
| ML_BENCH-02 | backend/progress/mlbench2_regression_certificate.py | ML Regression | tests/ml/ |
| ML_BENCH-03 | backend/progress/mlbench3_timeseries_certificate.py | ML Time-Series | tests/ml/ |
| DT-FEM-01 | backend/progress/dtfem1_displacement_verification.py | Digital Twin FEM | tests/digital_twin/ |
| DT-SENSOR-01 | backend/progress/dtsensor1_iot_certificate.py | Digital Twin IoT | tests/digital_twin/ |
| DT-CALIB-LOOP-01 | backend/progress/dtcalib1_convergence_certificate.py | Digital Twin Calib | tests/digital_twin/ |
| PHARMA-01 | backend/progress/pharma1_admet_certificate.py | Pharma ADMET | tests/ml/ |
| FINRISK-01 | backend/progress/finrisk1_var_certificate.py | Finance VaR | tests/ml/ |
| AGENT-DRIFT-01 | backend/progress/agent_drift_monitor.py | Agent Quality | tests/agent/ |

---

## Acceptance commands (run before any commit)

```bash
python scripts/steward_audit.py      # → STEWARD AUDIT: PASS
python -m pytest tests/ -q           # → 1750 passed
python scripts/deep_verify.py        # → ALL 13 TESTS PASSED
python scripts/agent_pr_creator.py --summary  # → No auto-pr needed
grep -r "tamper-proof\|GPT-5\|19x\|VacuumGenesis\|blockchain" docs/ scripts/ backend/ tests/
# → empty
```

---

## Architecture in one paragraph

Job runs via runner.run_job() → produces run_artifact.json (execution_trace +
trace_root_hash) + ledger_snapshot.jsonl → evidence_index maps artifacts to
claims → steward_submission_pack bundles everything → mg.py verify runs five
independent layers: (1) SHA-256 integrity, (2) semantic verification,
(3) step chain hash chain, (4) bundle signing Ed25519/HMAC,
(5) temporal commitment NIST Beacon → PASS or FAIL with specific reason.
Physical chain: MTR-1 → DT-FEM-01 → DRIFT-01 cryptographically linked via anchor_hash.
Steward_audit enforces bidirectional coverage on every PR.
agent_evolution.py runs 18 Mechanicus checks after every merge.
agent_pr_creator.py autonomously creates PRs for detected issues.
