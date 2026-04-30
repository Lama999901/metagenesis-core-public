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
- **Title:** Boost coverage to 65% — mg_sign.py and mg_temporal.py
- **Status:** DONE (2026-03-19)
- **Priority:** P1
- **Output:** tests/steward/test_coverage_boost.py
- **Description:** Read reports/COVERAGE_REPORT_20260319.md, identify top 10 highest-value uncovered functions in mg_sign.py and mg_temporal.py, write actual test code covering them.

### TASK-016
- **Title:** Zenodo DOI preparation
- **Status:** DONE (2026-03-19)
- **Priority:** P2
- **Output:** .zenodo.json
- **Description:** Read system_manifest.json and paper.md, generate .zenodo.json metadata file with all required fields: title, creators, description, keywords, license, version, doi placeholder.

### TASK-017
- **Title:** SoftwareX submission plan
- **Status:** DONE (2026-03-19)
- **Priority:** P2
- **Output:** docs/SOFTWAREX_PLAN.md
- **Description:** Read paper.md, analyze differences between JOSS and SoftwareX format requirements, create docs/SOFTWAREX_PLAN.md with exact changes needed for SoftwareX submission.

### TASK-018
- **Title:** Client outreach analysis
- **Status:** DONE (2026-03-19)
- **Priority:** P3
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read COMMERCIAL.md and EVOLUTION_LOG.md for outreach contact patterns. Analyze which contacts have not replied. Propose 3 best follow-up messages with specific value propositions.

### TASK-019
- **Title:** Coverage audit for MTR-4, MTR-5, MTR-6
- **Status:** DONE (2026-03-29)
- **Priority:** P1
- **Output:** reports/AGENT_REPORT_20260329.md
- **Description:** Audit test coverage for MTR-4 (Ti E=114GPa), MTR-5 (SS316L E=193GPa), MTR-6 (Cu k=401 W/mK). Count test functions. Verify physical anchor thresholds. Propose adversarial tests if missing.

### TASK-020
- **Title:** Update claim dependency graph for MTR-4/5/6
- **Status:** DONE (2026-03-29)
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_20260329.md
- **Description:** Update dependency graph to include MTR-4/5/6. Check if downstream claims should reference new anchors.

### TASK-021
- **Title:** Verify scientific_claim_index.md has MTR-4/5/6 entries
- **Status:** DONE (2026-03-29)
- **Priority:** P1
- **Output:** reports/scientific_claim_index.md
- **Description:** Check MTR-4 (rel_err<=0.01), MTR-5 (rel_err<=0.01), MTR-6 (rel_err<=0.02) in scientific_claim_index.md. Fix if missing.

### TASK-022
- **Title:** Fix stale CONTEXT_SNAPSHOT.md, llms.txt, AGENTS.md
- **Status:** DONE (2026-03-31)
- **Priority:** P1
- **Output:** CONTEXT_SNAPSHOT.md, llms.txt, AGENTS.md
- **Description:** Update all three files to v0.8.0 state: 608 tests, 20 claims, 18 agent checks, GitHub Release v0.8.0, add PHYS-01/02 to claims table. AGENTS.md Step 6: 595->608. Read system_manifest.json for ground truth.

### TASK-023
- **Title:** Update UPDATE_PROTOCOL.md v1.0 to v1.1
- **Status:** DONE (2026-04-02)
- **Priority:** P1
- **Output:** UPDATE_PROTOCOL.md
- **Description:** Change version marker from 'v1.0 -- 2026-03-16' to 'v1.1 -- 2026-03-30'. Add rule in section НОВЫЕ ТЕСТЫ: 'При изменении test count -> в ТОМ ЖЕ PR обновить check_stale_docs.py required strings для всех файлов ссылающихся на старое число.'

### TASK-024
- **Title:** Fix ppa/README_PPA.md missing 608 tests reference
- **Status:** DONE (2026-04-02)
- **Priority:** P2
- **Output:** ppa/README_PPA.md
- **Description:** check_stale_docs.py requires '601 tests' and '8 innovations' in README_PPA.md. Add a Current State section at the bottom: 'Current verification state: 608 tests, 20 claims, 8 innovations, v0.8.0'. Keep all historical data intact.

### TASK-025
- **Title:** Audit PHYS-01/02 test coverage
- **Status:** DONE (2026-04-02)
- **Priority:** P2
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Check tests/physics/ directory. Count test functions for PHYS-01 and PHYS-02. Verify SI 2019 exact constants documented in README and paper.md. Verify physical anchor hierarchy is correct in docs.

### TASK-026
- **Title:** Prepare Wave-2 outreach drafts for Chollet, LMArena, Percy Liang
- **Status:** DONE (2026-04-02)
- **Priority:** P3
- **Output:** reports/AGENT_REPORT_YYYYMMDD.md
- **Description:** Read CONTEXT_SNAPSHOT.md outreach tracker. Draft three personalized emails with PHYS-01/02 angle: kB and NA are SI 2019 exact constants, zero uncertainty -- strongest possible physical anchor. Chollet: ARC Prize benchmark integrity. LMArena: Leaderboard Illusion paper angle. Percy Liang: HELM verification angle.

### TASK-027
- **Title:** Full Technical Truth Audit — verify every claimed capability word for word
- **Status:** DONE (2026-04-02)
- **Priority:** P1
- **Output:** reports/AUDIT_TRUTH_20260401.md
- **Description:** Comprehensive end-to-end audit. Every claim in README.md, CLAUDE.md, system_manifest.json verified against actual code execution. Produce a formal audit report with git hash, timestamp, and PASS/FAIL for each item.

  Execute these checks IN ORDER and record every result:

  SECTION 1 — CORE INFRASTRUCTURE
  1.1 Run: python scripts/steward_audit.py → must output "STEWARD AUDIT: PASS"
  1.2 Run: python -m pytest tests/ -q --tb=short → count passed tests, record exact number
  1.3 Run: python scripts/deep_verify.py → must output "ALL 13 TESTS PASSED"
  1.4 Run: python scripts/agent_evolution.py --summary → must output "ALL 20 CHECKS PASSED"
  1.5 Run: python scripts/agent_pr_creator.py --summary → must output "No auto-pr needed"
  1.6 Run: python scripts/check_stale_docs.py --strict → must exit 0

  SECTION 2 — ALL 20 CLAIMS PRODUCE PASS AT DOCUMENTED THRESHOLDS
  For each claim, import the module and call its run function with default params.
  Verify result["result"]["pass"] is True AND rel_err (or equivalent) is within threshold.
  Record: claim_id | threshold | actual_value | PASS/FAIL

  Claims to verify:
  - MTR-1: rel_err <= 0.01 vs E=70GPa
  - MTR-2: rel_err <= 0.02
  - MTR-3: rel_err_k <= 0.03
  - MTR-4: rel_err <= 0.01 vs E=114GPa (Ti-6Al-4V, NIST)
  - MTR-5: rel_err <= 0.01 vs E=193GPa (SS316L, NIST)
  - MTR-6: rel_err <= 0.02 vs k=401 W/(m·K) (Cu, NIST)
  - PHYS-01: rel_err <= 1e-9 vs kB=1.380649e-23 J/K (SI 2019, exact) — CRITICAL: must be near zero
  - PHYS-02: rel_err <= 1e-8 vs NA=6.02214076e23 mol-1 (SI 2019, exact) — CRITICAL: must be near zero
  - SYSID-01: rel_err_a <= 0.03, rel_err_b <= 0.03
  - DATA-PIPE-01: pass=True
  - DRIFT-01: drift_pct <= 5.0
  - ML_BENCH-01: abs(actual_acc - claimed_acc) <= 0.02
  - ML_BENCH-02: abs(actual_rmse - claimed_rmse) <= 0.02
  - ML_BENCH-03: abs(actual_mape - claimed_mape) <= 0.02
  - DT-FEM-01: rel_err <= 0.02
  - DT-SENSOR-01: pass=True
  - DT-CALIB-LOOP-01: drift decreasing, final <= threshold
  - PHARMA-01: abs(predicted - claimed) <= tolerance
  - FINRISK-01: abs(actual_var - claimed_var) <= tolerance
  - AGENT-DRIFT-01: composite_drift <= 20.0

  SECTION 3 — 5 VERIFICATION LAYERS — EACH INDEPENDENTLY CATCHES ITS ATTACK
  Run each CERT test suite individually and record PASS/FAIL:
  3.1 python -m pytest tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py -v
  3.2 python -m pytest tests/steward/test_cert03_step_chain_verify.py -v
  3.3 python -m pytest tests/steward/test_cert04_anchor_hash_verify.py -v
  3.4 python -m pytest tests/steward/test_cert05_adversarial_gauntlet.py -v
  3.5 python -m pytest tests/steward/test_cert06_real_world_scenarios.py -v
  3.6 python -m pytest tests/steward/test_cert07_bundle_signing.py -v
  3.7 python -m pytest tests/steward/test_cert08_reproducibility.py -v
  3.8 python -m pytest tests/steward/test_cert09_ed25519_attacks.py -v
  3.9 python -m pytest tests/steward/test_cert10_temporal_attacks.py -v
  3.10 python -m pytest tests/steward/test_cert11_coordinated_attack.py -v
  3.11 python -m pytest tests/steward/test_cert12_encoding_attacks.py -v
  3.12 python -m pytest tests/steward/test_cert_5layer_independence.py -v
  Record: CERT | tests_count | PASS/FAIL

  SECTION 4 — PHYSICAL ANCHOR CHAIN END-TO-END
  4.1 Run MTR-1 with seed=42, E_true=70e9. Record trace_root_hash as anchor1.
  4.2 Run DT-FEM-01 with anchor_hash=anchor1. Verify trace_root_hash differs from no-anchor run.
  4.3 Run DRIFT-01 with anchor_hash from DT-FEM-01. Verify chain is cryptographically linked.
  4.4 Verify: python scripts/mg.py verify-chain --help exists (CLI command present)
  4.5 Run PHYS-01 with T=300.0. Record actual rel_err. Must be < 1e-12 (effectively zero).
  4.6 Run PHYS-02. Record actual rel_err. Must be < 1e-10 (effectively zero).

  SECTION 5 — GOVERNANCE SYSTEM
  5.1 Verify canonical_state.md lists exactly 20 claims — count them
  5.2 Verify scientific_claim_index.md has exactly 20 claim sections
  5.3 Verify runner.py dispatches exactly 20 job_kinds — count dispatch blocks
  5.4 Verify steward_audit bidirectional: claims == implementations == runner

  SECTION 6 — AGENT SYSTEM
  6.1 Verify agent_learn.py recall runs without error, shows session count >= 58
  6.2 Verify .agent_memory/patterns.json exists and has >= 15 patterns
  6.3 Verify agent_pr_creator.py is real (>100 lines), not stub
  6.4 Verify agent_evolution.py has exactly 20 check functions

  SECTION 7 — SITE vs CODE CONSISTENCY
  7.1 Read index.html: verify "608" appears in test count positions
  7.2 Read index.html: verify "20" appears in claims count
  7.3 Read system_manifest.json: verify test_count == actual pytest count
  7.4 Read README.md: verify "The open standard for verifiable computation" is subtitle
  7.5 Read README.md: verify Mechanicus Parallel table is NOT present

  OUTPUT FORMAT for reports/AUDIT_TRUTH_20260401.md:
  # MetaGenesis Core — Technical Truth Audit
  Date: [date]
  Git hash: [git rev-parse HEAD]
  Version: v0.8.0

  ## Executive Summary
  TOTAL CHECKS: N
  PASSED: N
  FAILED: N (list each failure with exact error)

  ## Section 1: Core Infrastructure
  [table: check | result | output]

  ## Section 2: All 20 Claims at Documented Thresholds
  [table: claim | threshold | actual_value | result]

  ## Section 3: Adversarial Proof Suite
  [table: cert | tests | result]

  ## Section 4: Physical Anchor Chain
  [table: check | result]

  ## Section 5: Governance System
  [table: check | result]

  ## Section 6: Agent System
  [table: check | result]

  ## Section 7: Site vs Code
  [table: check | result]

  ## Verdict
  If ALL checks PASS: "AUDIT PASS — All claimed capabilities verified word for word."
  If ANY check FAILS: "AUDIT PARTIAL — [N] failures require attention: [list]"

  CRITICAL: Do NOT summarize or skip. Run every check. Record every result.
  If a check fails, record the exact error and continue to next check.
  This audit is the formal proof that the protocol does what it claims.

### TASK-028
- **Title:** Memory synthesis — agent_learn.py synthesize command + strategic memory
- **Status:** DONE (2026-04-12)
- **Priority:** P1
- **Output:** .agent_memory/strategic_memory.json, project_trajectory.json, resolved_patterns.json, security_learnings.json, verification_stats.json
- **Description:** Add synthesize command to agent_learn.py. Process accumulated sessions and resolve ghost patterns into resolved_patterns.json. Create strategic_memory.json with north star, regulatory urgency, what-works. Create project_trajectory.json (511 to 2407 test evolution). Add strategic context to recall output.

### TASK-029
- **Title:** World-class documentation — VISION, PHILOSOPHICAL_FOUNDATION, EVOLUTIONARY_ARCHITECTURE, REGULATORY_GAPS
- **Status:** DONE (2026-04-12)
- **Priority:** P1
- **Output:** docs/VISION.md, docs/PHILOSOPHICAL_FOUNDATION.md, docs/EVOLUTIONARY_ARCHITECTURE.md, docs/REGULATORY_GAPS.md
- **Description:** Create four deep documents: VISION.md (civilizational scope of verification gap), PHILOSOPHICAL_FOUNDATION.md (epistemological foundation — proof not trust), EVOLUTIONARY_ARCHITECTURE.md (protocol that verifies itself — 4 levels), REGULATORY_GAPS.md (FDA Q2 2026, EU AI Act Aug 2026, Basel III assessment, SI 2019 expansion opportunities).

### TASK-030
- **Title:** Repository hygiene — README SDK/Action, ROADMAP 4-level vision, SDK 3 examples, known_faults FAULT_007-011
- **Status:** DONE (2026-04-12)
- **Priority:** P1
- **Output:** README.md, docs/ROADMAP.md, docs/SDK.md, reports/known_faults.yaml, llms.txt, scripts/check_stale_docs.py
- **Description:** Add SDK 3-line example and GitHub Action to README. Rewrite ROADMAP.md as 4-level vision (Protocol to Universal). Add 3 real-world examples to SDK.md. Add FAULT_007 (supply chain), FAULT_008 (social engineering), FAULT_009 (SI exact), FAULT_010 (cp1252 encoding), FAULT_011 (CRLF/LF hash). Update llms.txt with DOI, SDK, Action refs. Add watchlist entries for all new docs.

### TASK-031
- **Title:** First paying client $299
- **Status:** PENDING
- **Priority:** P1
- **Description:** Target: ML/pharma/finance team needing verifiable computational artifacts. See COMMERCIAL.md for pipeline. $299 per verification bundle. Contact: yehor@metagenesis-core.dev. Unlocks: v1.0.0 final release.

### TASK-032
- **Title:** Wave-2 outreach — Chollet, LMArena, Percy Liang
- **Status:** PENDING
- **Priority:** P1
- **Description:** Wave-2 outreach to benchmark integrity community. Drafts in reports/WAVE2_OUTREACH_DRAFTS.md. Send ONLY from yehor@metagenesis-core.dev via Zoho.

### TASK-033
- **Title:** Check Zoho SPAM every session — protocol rule
- **Status:** PENDING
- **Priority:** P1
- **Description:** Outreach replies land in Zoho SPAM. Non-negotiable: check at every session start. Add to CLAUDE.md session checklist. This is not optional.

### TASK-034
- **Title:** Fix site footer JOSS claim
- **Status:** PENDING
- **Priority:** P2
- **Description:** index.html says "JOSS paper submitted March 2026". Reality: rejected, resubmit Sep 2026. Fix to: "JOSS submission planned Sep 2026" or "JOSS resubmission Sep 2026".

### TASK-035
- **Title:** JOSS resubmission Sep 2026
- **Status:** PENDING
- **Priority:** P2
- **Description:** Prerequisites met: 6+ months public history, DOI 10.5281/zenodo.19521091 minted. Update paper.md for v1.0.0-rc1 state (2407 tests, 20 claims, 5 layers, 8 innovations). Verify paper.bib references current. Submit to JOSS Sep 2026.

### TASK-036
- **Title:** Patent attorney — non-provisional filing
- **Status:** PENDING
- **Priority:** P2
- **Description:** PPA #63/996,819 filed 2026-03-05. Non-provisional deadline: 2027-03-05. Budget: $3K-8K. Start attorney search Q3 2026. Need patent attorney experienced in software/protocol patents. Key innovations: 5-layer independence proof, physical anchor chain, semantic verification layer.
