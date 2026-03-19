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
- **Status:** DONE (2026-03-18)
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Design AGENT-DRIFT-01 with job_kind, threshold, step chain structure, physical anchor decision, and estimate implementation hours.

### TASK-003
- **Title:** Audit index.html and stale docs for v0.5.0
- **Status:** DONE (2026-03-18)
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Run check_stale_docs --strict and audit index.html for v0.5.0/JOSS/Ed25519/NLnet/Agent Evolution references. List exact line fixes needed.

### TASK-004
- **Title:** Predict JOSS reviewer questions
- **Status:** DONE (2026-03-18)
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read paper.md, identify 5 likely JOSS reviewer questions with prepared answers.

### TASK-005
- **Title:** Draft integration API sketch
- **Status:** DONE (2026-03-18)
- **Priority:** P3
- **Output:** docs/INTEGRATION_GUIDE.md
- **Description:** Draft MLflow/DVC/WandB integration API sketch for docs/INTEGRATION_GUIDE.md.

### TASK-006
- **Title:** Adversarial tests for SYSID-01 (weakest coverage claim)
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** SYSID-01 was identified as weakest-coverage claim in TASK-001. Write 3 adversarial test scenarios: (1) step chain hash tamper, (2) semantic field stripping, (3) threshold boundary injection. Read sysid1_arx_calibration.py to extract exact thresholds and field names.

### TASK-007
- **Title:** Map claim dependency graph
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Analyze all 14 claim files in backend/progress/ to build a dependency graph. Find which claims reference other claims (e.g., DRIFT-01 depends on MTR-1, DT-CALIB-LOOP-01 depends on DRIFT-01). Output adjacency list and identify isolated claims with no dependencies.

### TASK-008
- **Title:** Temporal verification layer audit
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read scripts/mg_temporal.py and tests/steward/test_cert10*. Audit: (1) which NIST Beacon features are used, (2) what attack vectors CERT-10 covers, (3) propose 2 new temporal attack scenarios not yet tested (e.g., timezone manipulation, leap second edge case).

### TASK-009
- **Title:** Bundle size optimization analysis
- **Status:** PENDING
- **Priority:** P3
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Analyze a typical pack bundle output. Measure sizes of pack_manifest.json, evidence files, and signature files. Identify which components dominate bundle size. Propose compression or deduplication strategies without breaking SHA-256 integrity verification.

### TASK-010
- **Title:** Cross-layer attack surface analysis
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** For each of the 5 verification layers, enumerate the exact attack vectors tested by CERT-02 through CERT-12. Build a matrix: layers (rows) x CERT tests (columns). Find any layer that has fewer than 2 dedicated attack tests. Propose gap-closing tests.
