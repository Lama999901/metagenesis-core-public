# Agent Research Tasks

Auto-processed by `scripts/agent_research.py`. First PENDING task gets executed each run.

## Tasks

### TASK-001
- **Title:** Audit test coverage per all 14 claims
- **Status:** DONE (2026-03-18)
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** For each of the 14 active claims (MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01), count test files and test functions. Find the claim with weakest coverage. Propose 3 new adversarial tests.

### TASK-002
- **Title:** Design claim 15 AGENT-DRIFT-01
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Design AGENT-DRIFT-01 with job_kind, threshold, step chain structure, physical anchor decision, and estimate implementation hours.

### TASK-003
- **Title:** Audit index.html and stale docs for v0.5.0
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Run check_stale_docs --strict and audit index.html for v0.5.0/JOSS/Ed25519/NLnet/Agent Evolution references. List exact line fixes needed.

### TASK-004
- **Title:** Predict JOSS reviewer questions
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read paper.md, identify 5 likely JOSS reviewer questions with prepared answers.

### TASK-005
- **Title:** Draft integration API sketch
- **Status:** PENDING
- **Priority:** P3
- **Output:** docs/INTEGRATION_GUIDE.md
- **Description:** Draft MLflow/DVC/WandB integration API sketch for docs/INTEGRATION_GUIDE.md.
