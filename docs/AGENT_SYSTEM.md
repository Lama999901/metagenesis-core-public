# MetaGenesis Agent System -- Autonomous Verification Architecture

> The Machine Spirit maintains itself through three levels of divine autonomy.

## Overview

MetaGenesis Core uses a 3-level autonomous agent architecture where AI agents
monitor, verify, and improve the verification protocol through the same
cryptographic mechanisms they extend.

## Level 1: GOVERNANCE (Inquisitorial)

Scripts: steward_audit.py, mg_policy_gate.py, check_stale_docs.py
Purpose: Enforce immutable rules. SEALED files, banned terms, policy gates.
Autonomy: Zero -- these scripts NEVER change. They are the constitution.

Key properties:
- steward_audit.py is CI-locked and SEALED
- Policy gate allowlist controls what files can be added
- Stale docs checker with CONTENT_CHECKS enforces version string currency

## Level 2: VERIFICATION (Omnissiah's Will)

Scripts: mg.py, mg_sign.py, mg_ed25519.py, mg_temporal.py, deep_verify.py
Purpose: 5-layer verification of computational claims.
Autonomy: Low -- verified against 608+ adversarial tests before any change.

Layers:
1. SHA-256 integrity (pack_manifest.json)
2. Semantic validation (_verify_semantic)
3. Step chain (execution_trace hash chain)
4. Bundle signing (Ed25519)
5. Temporal commitment (NIST Beacon)

## Level 3: EVOLUTION (Mechanicus Forge)

Scripts: agent_evolution.py (19 checks), agent_research.py (task queue),
         agent_coverage.py (Genetor), agent_evolve_self.py (recursive),
         agent_signals.py (external), agent_chronicle.py (history),
         agent_learn.py (memory), agent_drift_monitor.py (AGENT-DRIFT-01),
         agent_pr_creator.py (Level 3 autonomous PR)

Purpose: Self-monitoring, self-improvement, drift detection.
Autonomy: High -- agents generate tasks, execute research, detect gaps.

### Recursive Self-Verification Loop

1. agent_evolution.py runs 19 checks after every merge
2. agent_coverage.py identifies untested code paths
3. agent_research.py auto-generates tasks from coverage gaps
4. Tasks execute: write tests, audit code, produce reports
5. AGENT-DRIFT-01 monitors agent quality drift (composite threshold <= 20%)
6. If drift detected: correction_required triggers re-research

### Recursive Self-Verification

The key insight: agents that extend the protocol are monitored BY the protocol.
AGENT-DRIFT-01 uses the same step chain mechanism as all 20 claims.

## Claim Coverage

All 20 active claims verified through 4-step hash chains:
MTR-1, MTR-2, MTR-3, MTR-4, MTR-5, MTR-6,
SYSID-01, DATA-PIPE-01, DRIFT-01,
ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03,
PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01,
AGENT-DRIFT-01, PHYS-01, PHYS-02

## File Map

| Script | Level | Role |
|--------|-------|------|
| steward_audit.py | 1 | Governance enforcement |
| mg_policy_gate.py | 1 | File policy gate |
| check_stale_docs.py | 1 | Documentation currency |
| mg.py | 2 | Core 5-layer verifier |
| mg_sign.py | 2 | Bundle signing |
| mg_ed25519.py | 2 | Ed25519 operations |
| mg_temporal.py | 2 | Temporal commitment |
| deep_verify.py | 2 | 13-test proof script |
| agent_evolution.py | 3 | 19-check health monitor |
| agent_research.py | 3 | Task queue + execution |
| agent_coverage.py | 3 | Code coverage analysis |
| agent_evolve_self.py | 3 | Recursive improvement |
| agent_signals.py | 3 | External signal intake |
| agent_chronicle.py | 3 | Historical record |
| agent_learn.py | 3 | Pattern memory |
| agent_drift_monitor.py | 3 | Agent quality drift |
| agent_pr_creator.py | 3 | Autonomous PR creation |

---

*docs/AGENT_SYSTEM.md -- v0.8.0 -- MetaGenesis Core*
