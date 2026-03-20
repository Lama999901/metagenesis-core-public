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
- **Status:** DONE (2026-03-19)
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** SYSID-01 was identified as weakest-coverage claim in TASK-001. Write 3 adversarial test scenarios: (1) step chain hash tamper, (2) semantic field stripping, (3) threshold boundary injection. Read sysid1_arx_calibration.py to extract exact thresholds and field names.

### TASK-007
- **Title:** Map claim dependency graph
- **Status:** DONE (2026-03-19)
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Analyze all 14 claim files in backend/progress/ to build a dependency graph. Find which claims reference other claims (e.g., DRIFT-01 depends on MTR-1, DT-CALIB-LOOP-01 depends on DRIFT-01). Output adjacency list and identify isolated claims with no dependencies.

### TASK-008
- **Title:** Temporal verification layer audit
- **Status:** DONE (2026-03-19)
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read scripts/mg_temporal.py and tests/steward/test_cert10*. Audit: (1) which NIST Beacon features are used, (2) what attack vectors CERT-10 covers, (3) propose 2 new temporal attack scenarios not yet tested (e.g., timezone manipulation, leap second edge case).

### TASK-009
- **Title:** Bundle size optimization analysis
- **Status:** DONE (2026-03-19)
- **Priority:** P3
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Analyze a typical pack bundle output. Measure sizes of pack_manifest.json, evidence files, and signature files. Identify which components dominate bundle size. Propose compression or deduplication strategies without breaking SHA-256 integrity verification.

### TASK-010
- **Title:** Cross-layer attack surface analysis
- **Status:** DONE (2026-03-19)
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** For each of the 5 verification layers, enumerate the exact attack vectors tested by CERT-02 through CERT-12. Build a matrix: layers (rows) x CERT tests (columns). Find any layer that has fewer than 2 dedicated attack tests. Propose gap-closing tests.

### TASK-011
- **Title:** Write adversarial test: SYSID-01 Layer 2 semantic stripping
- **Status:** DONE (2026-03-19)
- **Priority:** P1
- **Output:** tests/steward/test_cert_adv_sysid01_semantic.py
- **Description:** Generate test file that builds a SYSID-01 pack using _make_sem_pack pattern, then strips required semantic fields (mtr_phase, execution_trace, inputs, result) one at a time. Each test asserts _verify_semantic() returns FAIL. Read sysid1_arx_calibration.py for exact field names and test_cert02 for _make_sem_pack pattern.

### TASK-012
- **Title:** Write adversarial test: Layer 3 + Layer 5 multi-vector attack
- **Status:** DONE (2026-03-19)
- **Priority:** P1
- **Output:** tests/steward/test_cert_adv_multichain.py
- **Description:** Generate test file combining step chain tamper (Layer 3) with temporal replay (Layer 5). Scenario: attacker modifies execution_trace hashes AND replays old temporal_commitment.json. Prove both layers catch independently. Read test_cert11 for multi-vector pattern and test_cert10 for temporal helpers.

### TASK-013
- **Title:** Write adversarial test: Layer 1 + Layer 4 file mod + wrong key signing
- **Status:** DONE (2026-03-19)
- **Priority:** P2
- **Output:** tests/steward/test_cert_adv_sign_integrity.py
- **Description:** Generate test file: (1) modify evidence file content, update SHA-256 in manifest (Layer 1 bypass), then verify Layer 4 catches because signature no longer matches. (2) Re-sign with wrong key, verify signature check fails. Read test_cert09 for Ed25519 patterns and test_cert07 for signing patterns.

### TASK-014
- **Title:** Write adversarial test: Layer 5 pure temporal isolation
- **Status:** DONE (2026-03-19)
- **Priority:** P2
- **Output:** tests/steward/test_cert_adv_temporal_pure.py
- **Description:** Generate test file with 4 pure temporal attacks that do NOT involve other layers: (1) truncated beacon value, (2) empty timestamp string, (3) swapped pre_commitment fields between two bundles, (4) temporal_commitment.json with valid structure but all-zero hashes. Read test_cert10 for temporal API usage.

### TASK-015
- **Title:** Boost coverage to 60% -- identify top uncovered functions, write test code
- **Status:** PENDING
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read reports/COVERAGE_REPORT_20260319.md, identify the top uncovered functions in mg_sign.py and mg_temporal.py (both are core verification scripts with low coverage), and generate actual pytest test code targeting cmd_keygen, cmd_sign, cmd_verify, cmd_temporal, verify_bundle_signature in mg_sign.py plus create_temporal_commitment, verify_temporal_commitment in mg_temporal.py.

### TASK-016
- **Title:** Zenodo DOI preparation -- generate .zenodo.json
- **Status:** PENDING
- **Priority:** P2
- **Output:** .zenodo.json
- **Description:** Read system_manifest.json and paper.md to extract metadata (title, authors, description, keywords, license, version). Generate a valid .zenodo.json file for automated DOI minting on next GitHub release.

### TASK-017
- **Title:** SoftwareX submission plan -- analyze JOSS to SoftwareX diff
- **Status:** PENDING
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read paper.md and compare JOSS format requirements against SoftwareX Original Software Publication format. Identify sections that need rewriting, additional content needed (impact statement, illustrative examples), and estimate effort in hours.

### TASK-018
- **Title:** First client outreach analysis
- **Status:** PENDING
- **Priority:** P3
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read EVOLUTION_LOG.md and any COMMERCIAL.md or business-related files in the repo. Analyze the protocol's readiness for a first paying client ($299 tier). Identify missing features, documentation gaps, and propose a 3-step outreach plan targeting ML teams that need reproducibility auditing.
