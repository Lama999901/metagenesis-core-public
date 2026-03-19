---

> **DRAFT v2.1** — Working draft for non-provisional application.
> Filing deadline: 2027-03-05 (12 months from PPA #63/996,819).
> PPA filing basis (FROZEN): see ppa/CLAIMS_DRAFT.md — do NOT edit that file.
> This document covers ALL claims and innovations for non-provisional filing.
> Updated: 2026-03-18 | v0.5.0 | 14 claims | 511 tests | 8 innovations

# MetaGenesis Core — Claims Draft v2
## For Non-Provisional Application (pre-2027-03-05)

---

## Status — All 14 Active Claims

| Claim | Domain | Threshold | Physical Anchor | Tests |
|-------|--------|-----------|-----------------|-------|
| MTR-1 | Materials Science | rel_err <= 0.01 | E=70GPa (aluminum) | tests/materials/ |
| MTR-2 | Materials Science | rel_err <= 0.02 | Thermal conductivity | tests/materials/ |
| MTR-3 | Materials Science | rel_err_k <= 0.03 | Multilayer contact | tests/materials/ |
| SYSID-01 | System Identification | rel_err <= 0.03 | — | tests/systems/ |
| DATA-PIPE-01 | Data Pipelines | schema+range | — | tests/data/ |
| DRIFT-01 | Calibration Monitoring | drift <= 5% | MTR-1 anchor | tests/steward/ |
| ML_BENCH-01 | ML/AI | delta_acc <= 0.02 | — | tests/ml/ |
| DT-FEM-01 | Digital Twin | rel_err <= 0.02 | MTR-1 anchor | tests/digital_twin/ |
| ML_BENCH-02 | ML/AI | delta_RMSE <= 0.02 | — | tests/ml/ |
| ML_BENCH-03 | ML/AI | delta_MAPE <= 0.02 | — | tests/ml/ |
| PHARMA-01 | Pharma/Biotech | delta_prop <= tol | — | tests/ml/ |
| FINRISK-01 | Financial Risk | delta_VaR <= tol | — | tests/ml/ |
| DT-SENSOR-01 | Digital Twin (IoT) | schema+range+temporal | — | tests/digital_twin/ |
| DT-CALIB-LOOP-01 | Digital Twin | drift decreasing | DRIFT-01 anchor | tests/digital_twin/ |

**Cross-Claim Chain:** MTR-1 -> DT-FEM-01 -> DRIFT-01 -> DT-CALIB-LOOP-01
Each claim embeds `anchor_hash` of upstream claim's `trace_root_hash`.

**Physical anchor traceability (distinct from tamper-evident provenance):**
Only MTR-1/2/3, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01 have physical anchors.
All 14 claims have tamper-evident provenance via 5-layer verification.

---

## 8 Patent Innovations

### Innovation 1 — Bidirectional Governance Coverage (PPA)
Every registered claim must have an implementation AND tests. Every test must correspond to a registered claim. Enforced by `scripts/steward_audit.py`.
- Files: `scripts/steward_audit.py`, `reports/canonical_state.md`, `reports/scientific_claim_index.md`

### Innovation 2 — Step Chain Execution Trace (PPA)
4-step cryptographic hash chain within each computation: init_params -> compute -> metrics -> threshold_check. Each step hashes previous step's output. Tampering any step invalidates `trace_root_hash`.
- Files: Every `backend/progress/*.py` claim implementation

### Innovation 3 — Semantic Verification Layer (PPA)
Independent verification layer that checks `job_snapshot` presence, `payload.kind` matching, `canary_mode` correctness. Catches evidence stripping attacks that SHA-256 alone misses.
- Files: `scripts/mg.py` (`_verify_semantic()`)

### Innovation 4 — Dual-Mode Canary Pipeline (PPA)
Every claim runs in both synthetic (deterministic from seed) and real data modes. Canary flag prevents synthetic results from being presented as real measurements.
- Files: `backend/progress/runner.py`

### Innovation 5 — Cross-Claim Cryptographic Chain (Post-PPA)
Verifiable provenance path from physically measured constant through calibration, FEM simulation, and drift monitoring. Each claim embeds `anchor_hash` of upstream claim's `trace_root_hash`. Tampering any link invalidates all downstream claims.
- Files: `backend/progress/drift_monitor.py`, `backend/progress/dtfem1_displacement_verification.py`, `backend/progress/dtcalib1_convergence_certificate.py`
- Proof: `tests/steward/test_cross_claim_chain.py`, `tests/steward/test_cert04_cross_claim_chain.py`

### Innovation 6 — HMAC Bundle Signing (Post-PPA)
Symmetric key signing of bundle manifest. Produces `signed_root_hash` that catches unauthorized bundle creators. Supports shared-key workflows where verifier and creator share a secret.
- Files: `scripts/mg_sign.py` (HMAC mode)
- Proof: `tests/steward/test_cert07_bundle_signing.py`

### Innovation 7 — Ed25519 Asymmetric Signing (Post-PPA)
Asymmetric cryptographic signing using Ed25519 key pairs. Creator signs with private key; any verifier can check with public key. Catches unauthorized submissions without shared secrets.
- Files: `scripts/mg_sign.py` (Ed25519 mode), `scripts/mg_ed25519.py`
- Proof: `tests/steward/test_cert09_ed25519_attacks.py`, `tests/steward/test_ed25519.py`

### Innovation 8 — NIST Beacon Temporal Commitment (Post-PPA)
Anchors bundle timestamp to NIST Randomness Beacon 2.0 pulse. Bundle includes beacon value at creation time; verifier confirms value existed at claimed timestamp. Catches backdated bundles.
- Files: `scripts/mg_temporal.py`
- Proof: `tests/steward/test_cert10_temporal_attacks.py`, `tests/steward/test_temporal.py`

---

## 5-Layer Verification Independence

Each layer catches attacks the other four miss (proven by CERT-11):

| Layer | Catches | File |
|-------|---------|------|
| Layer 1 — SHA-256 Integrity | file modified after manifest | `scripts/mg.py` |
| Layer 2 — Semantic Invariants | evidence stripped, null values | `scripts/mg.py` (`_verify_semantic()`) |
| Layer 3 — Step Chain | inputs changed, steps reordered | execution_trace in each claim |
| Layer 4 — Bundle Signing | unauthorized creator (Ed25519+HMAC) | `scripts/mg_sign.py` |
| Layer 5 — Temporal Commitment | backdated bundle | `scripts/mg_temporal.py` |

**Flagship proof:** `tests/steward/test_cert11_coordinated_attack.py` — coordinated multi-vector attack proves each layer independently necessary.

---

## Adversarial Proof Suite (12 CERT files)

| CERT | Proves |
|------|--------|
| CERT-02 | Layer 2 semantic bypass detection |
| CERT-03 | Layer 3 step chain tamper detection |
| CERT-04 | Cross-claim chain integrity |
| CERT-05 | 5-attack gauntlet (3 layers each necessary) |
| CERT-06 | 5 real-world attack scenarios |
| CERT-07 | 13 bundle signing tests (HMAC + Ed25519) |
| CERT-08 | 10 reproducibility proofs (hash equality) |
| CERT-09 | Ed25519 attack scenarios (Layer 4) |
| CERT-10 | Temporal commitment attacks (Layer 5) |
| CERT-11 | Coordinated multi-vector — 5-layer independence |
| CERT-12 | Encoding attacks (BOM, null bytes, homoglyphs) |
| 5-layer independence | Full independence matrix |

---

## Acceptance Commands (run before non-provisional filing)

```bash
python scripts/steward_audit.py
# -> STEWARD AUDIT: PASS

python -m pytest tests/ -q
# -> 511 passed

python scripts/deep_verify.py
# -> ALL 13 TESTS PASSED

python scripts/check_stale_docs.py --strict
# -> All critical documentation is current

python scripts/agent_evolution.py --summary
# -> ALL 10 CHECKS PASSED
```

---

*Claims Draft v2.1. Authority: working draft for non-provisional application.*
*Deadline: 2027-03-05. Inventor: Yehor Bazhynov.*
*PPA basis: USPTO #63/996,819, filed 2026-03-05.*
*FROZEN PPA document: ppa/CLAIMS_DRAFT.md (do not modify).*
*Current state: v0.5.0 — 14 claims, 511 tests, 8 innovations, 5 verification layers.*
