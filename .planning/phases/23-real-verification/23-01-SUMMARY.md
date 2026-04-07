---
phase: 23-real-verification
plan: 01
subsystem: verification
tags: [real-data, proof-library, claim-dispatch, csv, json]

# Dependency graph
requires:
  - phase: none
    provides: existing 20 claim implementations in backend/progress/
provides:
  - 20 real input data files organized by domain in proof_library/real_data/
  - run_single_claim.py dispatcher for all 20 claims
affects: [23-02-PLAN (batch runner), 23-03-PLAN (tests)]

# Tech tracking
tech-stack:
  added: []
  patterns: [deterministic CSV generation with seed=42, domain-organized data layout]

key-files:
  created:
    - proof_library/real_data/materials/mtr1_aluminum_stress_strain.csv
    - proof_library/real_data/materials/mtr4_titanium_stress_strain.csv
    - proof_library/real_data/materials/mtr5_steel_stress_strain.csv
    - proof_library/real_data/ml/mlbench1_predictions.csv
    - proof_library/real_data/ml/mlbench2_regression.csv
    - proof_library/real_data/ml/mlbench3_timeseries.csv
    - proof_library/real_data/systems/datapipe1_dataset.csv
    - proof_library/real_data/digital_twin/dtfem1_displacement.csv
    - proof_library/real_data/physics/phys01_boltzmann_input.json
    - proof_library/real_data/agent/agent_drift01_metrics.json
    - scripts/run_single_claim.py
    - proof_library/real_data/_generate_data.py
  modified: []

key-decisions:
  - "Used random.Random(42) for deterministic CSV generation -- reproducible data"
  - "run_single_claim.py uses direct import dispatch (not subprocess) for speed"

patterns-established:
  - "Domain-organized data: proof_library/real_data/{domain}/{claim_file}"
  - "CSV claims pass dataset_relpath; JSON claims unpack kwargs"

requirements-completed: [REAL-03]

# Metrics
duration: 3min
completed: 2026-04-07
---

# Phase 23 Plan 01: Real Input Data and Claim Dispatcher Summary

**20 domain-realistic input data files across 8 domains plus run_single_claim.py dispatcher handling all 20 claim IDs**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-07T05:20:11Z
- **Completed:** 2026-04-07T05:23:29Z
- **Tasks:** 2/2
- **Files modified:** 22

## Accomplishments
- Created 20 real input data files organized by domain (materials, physics, ml, systems, digital_twin, pharma, finance, agent)
- Built deterministic CSV generator (_generate_data.py) with seed=42 for reproducible stress-strain, prediction, and displacement data
- Created run_single_claim.py (203 lines) dispatching all 20 claim IDs to correct backend/progress functions
- Verified PHYS-01 end-to-end: input JSON -> run_verification -> output JSON with execution_trace and pass=True

## Task Commits

Each task was committed atomically:

1. **Task 1: Create 20 real input data files organized by domain** - `0ea6e2a` (feat)
2. **Task 2: Create run_single_claim.py helper script** - `b42cc34` (feat)

## Files Created/Modified
- `proof_library/real_data/materials/mtr1_aluminum_stress_strain.csv` - 50-point aluminum tensile test (E=70 GPa)
- `proof_library/real_data/materials/mtr4_titanium_stress_strain.csv` - 50-point titanium tensile test (E=114 GPa)
- `proof_library/real_data/materials/mtr5_steel_stress_strain.csv` - 50-point steel tensile test (E=193 GPa)
- `proof_library/real_data/materials/mtr2_thermal_paste.json` - Thermal paste calibration params
- `proof_library/real_data/materials/mtr3_multilayer_thermal.json` - Multilayer thermal params
- `proof_library/real_data/materials/mtr6_copper_thermal.json` - Copper conductivity params
- `proof_library/real_data/physics/phys01_boltzmann_input.json` - Temperature input T=300 K
- `proof_library/real_data/physics/phys02_avogadro_input.json` - SI 2019 constant verification
- `proof_library/real_data/ml/mlbench1_predictions.csv` - 150 classification predictions (~94% accuracy)
- `proof_library/real_data/ml/mlbench2_regression.csv` - 200 regression predictions (RMSE ~0.15)
- `proof_library/real_data/ml/mlbench3_timeseries.csv` - 100 timeseries predictions (MAPE ~0.5%)
- `proof_library/real_data/systems/sysid1_arx_data.json` - ARX system identification params
- `proof_library/real_data/systems/datapipe1_dataset.csv` - 50-row dataset with id, value, category
- `proof_library/real_data/systems/drift01_monitor.json` - Drift monitor: MTR-1 anchor at 70 GPa
- `proof_library/real_data/digital_twin/dtfem1_displacement.csv` - 20-row FEM displacement comparison
- `proof_library/real_data/digital_twin/dtsensor1_temperature.json` - IoT temperature sensor params
- `proof_library/real_data/digital_twin/dtcalib1_convergence.json` - Calibration convergence params
- `proof_library/real_data/pharma/pharma1_admet.json` - ADMET solubility for aspirin
- `proof_library/real_data/finance/finrisk1_returns.json` - VaR parameters for equity portfolio
- `proof_library/real_data/agent/agent_drift01_metrics.json` - Agent drift baseline vs current
- `scripts/run_single_claim.py` - Single-claim dispatcher (203 lines, 20 imports)
- `proof_library/real_data/_generate_data.py` - Deterministic CSV data generator

## Decisions Made
- Used `random.Random(42)` seed for all generated CSVs -- ensures deterministic, reproducible data
- run_single_claim.py dispatches via direct Python import (not subprocess) for speed and simplicity
- CSV-based claims receive `dataset_relpath` parameter; JSON-based claims unpack all keys as kwargs

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 20 input data files ready for batch runner (Plan 02)
- run_single_claim.py tested and verified with PHYS-01, MTR-1, DRIFT-01
- Plan 02 can use run_single_claim.py as the --script command for mg_claim_builder.py

---
*Phase: 23-real-verification*
*Completed: 2026-04-07*
