# MetaGenesis Core — PPA Filing Record

## Filed: 2026-03-05 — PPA #63/996,819

**This section reflects what was physically submitted to the USPTO.**

- **4 patentable innovations** (the actual patent subject matter — unchanged)
- **5 example claims at filing**: MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01
  *(claims are illustrative examples; the 4 innovations are domain-agnostic)*
- **Test basis at filing**: 39 tests (17 steward + 22 domain)
- **Inventor**: Yehor Bazhynov
- **Deadline for non-provisional**: 2027-03-05

---

## Post-Filing Additions (NOT in PPA #63/996,819)

These were added after the PPA filing date and will be included
in the non-provisional application.

| Addition | Date added | Status |
|----------|-----------|--------|
| DRIFT-01 claim | post 2026-03-05 | To include in non-provisional |
| ML_BENCH-01 claim | post 2026-03-05 | To include in non-provisional |
| DT-FEM-01 claim | 2026-03-11 | To include in non-provisional |
| Tests 40–282 | post 2026-03-05 | Additional coverage (incl. CERT-05 gauntlet + CERT-06 scenarios) |
| Step Chain Verification (all 14 claims) | 2026-03-14 | 4-step cryptographic execution trace + trace_root_hash |
| Cross-Claim Cryptographic Chain | 2026-03-15 | anchor_hash MTR-1→DT-FEM-01→DRIFT-01 |
| ML_BENCH-02 (regression) | 2026-03-15 | RMSE, MAE, R² |
| ML_BENCH-03 (time-series) | 2026-03-15 | MAPE |
| PHARMA-01 (ADMET) | 2026-03-15 | FDA 21 CFR Part 11 alignment |
| FINRISK-01 (VaR) | 2026-03-15 | Basel III/IV alignment |
| DT-SENSOR-01 (IoT) | 2026-03-15 | Sensor data integrity |
| DT-CALIB-LOOP-01 (convergence) | 2026-03-15 | Calibration convergence |
| anchor_hash validation in verifier | 2026-03-15 | mg.py verify-chain CLI |
| Innovation #6: Bundle Signing (HMAC-SHA256) | 2026-03-17 | mg_sign.py — closes unauthorized bundle creation attack |
| Innovation #7: Ed25519 Asymmetric Signing | 2026-03-18 | mg_ed25519.py — pure Python RFC 8032, asymmetric key verification |
| Innovation #8: Temporal Commitment (NIST Beacon) | 2026-03-18 | mg_temporal.py — Layer 5, proves WHEN bundle was signed |
| 5-Layer Independence Proof (CERT-11/12) | 2026-03-18 | test_cert11 + test_cert12 — each layer catches attacks others miss |
| Agent Evolution System | 2026-03-18 | agent_learn.py + agent_evolution.py + check_stale_docs.py |
| MTR-4 (Titanium Ti-6Al-4V) | 2026-03-29 | Physical anchor E=114 GPa (NIST) |
| MTR-5 (Stainless Steel SS316L) | 2026-03-29 | Physical anchor E=193 GPa (NIST) |
| MTR-6 (Copper Conductivity) | 2026-03-29 | Physical anchor k=401 W/(m·K) (NIST) |

**Current state (2026-03-29):** 20 claims, 1273 tests, 5 layers, 8 innovations.
Live state: reports/canonical_state.md

---

## 4 Patentable Innovations (Filed — Unchanged)

## The 4 Independent Claims (summary)

**Claim 1 — Bidirectional Claim Coverage**
```
steward_audit.py enforces at every PR:
  runner dispatch kinds == scientific_claim_index job_kinds
  canonical_state claims == claim_index claims
No claim without implementation. No implementation without claim.
```

**Claim 2 — Semantic Tamper Detection**
```
mg verify catches tampering that survives SHA-256:
  attacker removes job_snapshot, recomputes all hashes
  integrity: PASS (hashes match)
  semantic:  FAIL (job_snapshot missing)
Proven by: test_cert02...::test_semantic_negative_missing_job_snapshot
```

**Claim 3 — Policy-Gate Immutable Evidence Anchors**
```
mg_policy_gate_policy.json locks evidence artifacts via CI.
Any PR touching locked_paths is blocked before merge.
No key custody. No external timestamping required.
```

**Claim 4 — Dual-Mode Canary Pipeline**
```
run_job(canary_mode=True/False)
Same computation, different authority metadata.
Enables continuous health verification without
contaminating authoritative evidence record.
```

---

## How to Verify This Package

### Step 1 — Governance
```bash
python scripts/steward_audit.py
# Expected: STEWARD AUDIT: PASS
```

### Step 2 — Adversarial proof
```bash
python -m pytest tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py -v
# Expected: 2 passed (including tamper detection test)
```

### Step 3 — Full verification core
```bash
python -m pytest tests/steward tests/materials tests/ml tests/systems tests/data -q
# Expected: all passed
```

### Step 4 — End-to-end pack
```bash
python scripts/mg.py steward audit
python scripts/mg.py pack build -o /tmp/ppa_pack --include-evidence \
  --source-reports-dir reports
python scripts/mg.py verify --pack /tmp/ppa_pack
# Expected: PASS
```

---

## Filing Checklist

```
Pre-filing (technical):
[x] steward_audit.py → PASS
[x] test_cert02 → PASS (both normal + tamper tests)
[x] python -m pytest tests/steward tests/materials tests/ml tests/systems tests/data -q → all passed
[x] All 7 claims reproducible via python -m pytest

Pre-filing (documentation):
[x] CLAIMS_DRAFT.md — V2 (code-backed, no invented features)
[x] EVIDENCE_INDEX.md — V2 (real test paths, no fake SHA)
[x] SYSTEM_ARCHIVE.docx — legacy only, not part of claims (no action required)
[x] README.md — verified clean (no banned terms per CONTRIBUTING)

Pre-filing (legal):
[ ] Confirm grace period window (repo was public < 12 months ago)
[ ] Patent attorney review of Claims 1-4
[ ] Confirm inventor name and assignment
[ ] File via USPTO EFS-Web as Provisional Patent Application
```

---

## Key Protocol Documents

```
docs/ARCHITECTURE.md
  → Proof loop diagram
  → Governance loop diagram
  → Calibration anchor and drift example
  → ML accuracy certification flow

reports/scientific_claim_index.md
  → Canonical claim registry: claim_id, job_kind, V&V thresholds,
    reproduction command, evidence fields

reports/canonical_state.md
  → Authoritative project state snapshot
  → current_claims_list: MTR-1, MTR-2, MTR-3, SYSID-01,
                          DATA-PIPE-01, DRIFT-01, ML_BENCH-01, DT-FEM-01,
                          ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01,
                          DT-SENSOR-01, DT-CALIB-LOOP-01
```

---

*PPA README v2.1. Scope: verification core only.
No invented features. Every section traceable to passing tests.*
