# MetaGenesis Verification Protocol (MVP) v0.9

## What this is

MVP is an open protocol specification for packaging computational claims
into independently verifiable evidence bundles.

A bundle created by any MVP-compliant implementation can be verified by
any MVP-compliant verifier — offline, without network access, without
trusting the bundle creator, without access to the original environment.

This is not experiment tracking. It is not logging. It is not monitoring.

It answers one question no existing tool answers:

> Can any third party verify this computational result independently —
> without access to the original model, data, or environment?

MVP answers: yes. In 60 seconds. Offline. With five independent verification
layers, each proven by an adversarial test.

---

## The problem this solves

Computational results are central to scientific publications, regulatory
submissions, commercial agreements, and AI product claims. There is no
standard for what "independently verifiable" means for a computational result.

The deeper problem: even when provenance exists, it proves only that a number
was produced consistently — not that it is grounded in physical reality. A
result that agrees with a physically measured constant (E = 70 GPa for aluminum,
measured independently in thousands of laboratories worldwide) carries
fundamentally different epistemic weight than a result that merely passes an
internally chosen threshold.

MVP addresses both:

1. **Tamper-evident provenance** — the bundle wasn't modified after generation
2. **Physical anchor traceability** — the computation agrees with physical reality
3. **Execution integrity** — the computation was performed in the claimed sequence

---

## Five verification layers

Each layer catches attacks that the previous layers miss.

### Layer 1 — Integrity (SHA-256)

Detects: any file modified after bundle generation.
How: SHA-256 hash of every file + root_hash over all hashes.
Bypassed by: removing evidence and recomputing hashes.

### Layer 2 — Semantic

Detects: evidence stripped, hashes recomputed (integrity says PASS, semantic says FAIL).
How: independently verifies required keys (`job_snapshot`, `payload.kind`, `canary_mode`).
Bypassed by: submitting a structurally valid artifact with modified computation inputs.

Proven by adversarial test:
```
tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py
::test_semantic_negative_missing_job_snapshot_fails_verify
```

### Layer 3 — Step Chain

Detects: computation inputs changed, steps reordered, steps skipped
         (layers 1 and 2 both say PASS, step chain says FAIL).
How: cryptographic hash chain over the execution sequence.

```
step 1: init_params       → hash_1 = SHA256(step1_data + "genesis")
step 2: compute           → hash_2 = SHA256(step2_data + hash_1)
step 3: metrics           → hash_3 = SHA256(step3_data + hash_2)
step 4: threshold_check   → trace_root_hash = SHA256(step4_data + hash_3)
```

`trace_root_hash` commits to the entire execution sequence. Change any input,
skip any step, reorder any step — `trace_root_hash` breaks.

Not blockchain. No network. No tokens. Same concept as git commits.
Works offline. No external dependencies.

Proven by adversarial test:
```
tests/steward/test_cert03_step_chain_verify.py
::TestStepChainVerification::test_tampered_trace_root_hash_fails
```

### Layer 4 — Bundle Signing (HMAC-SHA256 + Ed25519)

Detects: unauthorized bundle creator (layers 1–3 pass; layer 4 catches it).
How: HMAC-SHA256 (shared secret) or Ed25519 (asymmetric) signature over root_hash.
Proven by adversarial tests:
```
tests/steward/test_cert07_bundle_signing.py
tests/steward/test_cert09_ed25519_attacks.py
```

### Layer 5 — Temporal Commitment (NIST Randomness Beacon)

Detects: backdated bundles — proves WHEN a bundle was signed.
How: SHA-256(root_hash) committed before NIST Beacon pulse fetched,
then binding = SHA-256(pre_commitment + beacon_value).
Proven by adversarial tests:
```
tests/steward/test_cert10_temporal_attacks.py
```

All five layers run on every `mg.py verify --pack bundle.zip`.

---

## Physical Anchor Chain (Cross-Claim Cryptographic Chain)

For physical domains, individual claim verification is extended to
end-to-end chain verification.

Each claim's `trace_root_hash` can be embedded as `anchor_hash` in the
next claim's Step Chain. This cryptographically links the entire chain
from physical measurement to simulation output to drift monitoring:

```
Physical reality:  E = 70 GPa  (aluminum — measured in thousands of labs)
        ↓
MTR-1   trace_root_hash: "abc..."  (calibration against physical constant)
        ↓  anchor_hash="abc..." baked into DT-FEM-01 Step 1
DT-FEM-01  trace_root_hash: "def..."  (FEM output vs physical reference)
        ↓  anchor_hash="def..." baked into DRIFT-01 Step 1
DRIFT-01   trace_root_hash: "ghi..."  (drift against verified anchor)
```

DRIFT-01's `trace_root_hash` now cryptographically commits to the entire
chain from physical measurement to current simulation state.

Tampering any link breaks all downstream hashes.
Any third party verifies the full chain offline with one command.

Proven by:
```
tests/steward/test_cross_claim_chain.py
::TestCrossClaimChain::test_full_chain_is_cryptographically_linked
::TestCrossClaimChain::test_tampered_anchor_hash_changes_chain
```

---

## Bundle structure

An MVP-compliant bundle is a directory (or ZIP archive):

```
bundle/
  pack_manifest.json        ← Layer 1: SHA-256 integrity manifest
  evidence_index.json       ← claim mapping
  claims/
    dossier_<CLAIM_ID>.md   ← human-readable claim summary
  evidence/
    <CLAIM_ID>/
      normal/
        run_artifact.json   ← authoritative run result
        ledger_snapshot.jsonl
      canary/
        run_artifact.json   ← non-authoritative canary run
        ledger_snapshot.jsonl
```

---

## run_artifact.json

The evidence artifact produced by a single job run. Must contain:

```json
{
  "trace_id": "<uuid>",
  "canary_mode": false,
  "job_snapshot": {
    "payload": { "kind": "<job_kind>" },
    "result": {
      "mtr_phase": "<CLAIM_ID>",
      "inputs": { ... },
      "result": { "pass": true, ... },
      "execution_trace": [
        {"step": 1, "name": "init_params", "hash": "<sha256>"},
        {"step": 2, "name": "compute",     "hash": "<sha256>"},
        {"step": 3, "name": "metrics",     "hash": "<sha256>"},
        {"step": 4, "name": "threshold_check", "hash": "<sha256>"}
      ],
      "trace_root_hash": "<sha256 of final step>"
    }
  }
}
```

---

## Verification algorithm

```
INPUT: bundle path

STEP 1 — Integrity (Layer 1)
  Load pack_manifest.json
  For each file: compute SHA-256, compare to manifest
  Recompute root_hash, compare to manifest
  Any mismatch → FAIL("integrity: ...")

STEP 2 — Semantic (Layer 2)
  For each claim in evidence_index:
    Check job_snapshot present → FAIL if missing
    Check payload.kind matches job_kind → FAIL if wrong
    Check canary_mode == false → FAIL if wrong
    Check mtr_phase present in result → FAIL if missing

STEP 3 — Step Chain (Layer 3)
  If execution_trace present in result:
    Verify each step hash is valid 64-char lowercase hex
    Verify trace_root_hash == execution_trace[-1]["hash"]
    Any mismatch → FAIL("Step Chain broken — ...")

OUTPUT: PASS or FAIL with specific reason
```

---

## Governance invariant

Every registered claim must have a corresponding runner dispatch.
Every runner dispatch must have a registered claim.

```
runner dispatch kinds
    ↕  must be equal (bidirectional)
claim_index job_kinds
    ↕  must be equal (bidirectional)
canonical_state current_claims_list
```

Enforced automatically by `python scripts/steward_audit.py` on every PR.
Not by human review. Not periodically. On every merge.

---

## Claim lifecycle

To extend MVP to a new computational domain:

1. Implement: `backend/progress/<claim_id>.py` — `JOB_KIND` constant, `run_*()` function,
   4-step Step Chain producing `execution_trace` + `trace_root_hash`
2. Dispatch: add dispatch block in `runner._execute_job_logic()`
3. Register: add claim section in `reports/scientific_claim_index.md`
4. Anchor: add claim_id to `reports/canonical_state.md`
5. Test: pass / fail / adversarial / determinism / Step Chain integrity
6. Verify: `python scripts/steward_audit.py` → PASS

---

## Active claims and domains

| Claim | Domain | Threshold | Physical Anchor |
|-------|--------|-----------|-----------------|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | E = 70 GPa (aluminum) |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | Physical constant |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03` | Physical constant |
| SYSID-01 | System Identification | `rel_err_a/b ≤ 0.03` | — |
| DATA-PIPE-01 | Data Pipelines | schema pass · range pass | — |
| DRIFT-01 | Drift Monitoring | `drift ≤ 5.0%` | MTR-1 anchor |
| ML_BENCH-01 | ML — Classification | `\|Δacc\| ≤ 0.02` | — |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | MTR-1 anchor |
| ML_BENCH-02 | ML — Regression | `\|ΔRMSE\| ≤ 0.02` | — |
| ML_BENCH-03 | ML — Time-Series | `\|ΔMAPE\| ≤ 0.02` | — |
| PHARMA-01 | Pharma — ADMET | `\|Δprop\| ≤ tolerance` | — |
| FINRISK-01 | Finance — VaR | `\|ΔVaR\| ≤ tolerance` | — |
| DT-SENSOR-01 | IoT — Sensor Integrity | schema + range + temporal | — |
| DT-CALIB-LOOP-01 | Digital Twin — Convergence | drift_pct decreasing | DRIFT-01 anchor |
| AGENT-DRIFT-01 | Agent Quality — Self-Verification | `composite_drift <= 20%` | — |
| MTR-4 | Materials — Titanium Ti-6Al-4V | `rel_err ≤ 0.01` | E = 114 GPa |
| MTR-5 | Materials — Stainless Steel SS316L | `rel_err ≤ 0.01` | E = 193 GPa |
| MTR-6 | Materials — Copper Conductivity | `rel_err ≤ 0.02` | k = 401 W/(m·K) |
| PHYS-01 | Fundamental Physics — Boltzmann | `rel_err ≤ 1e-9` | kB = 1.380649e-23 J/K (SI 2019 exact) |
| PHYS-02 | Fundamental Physics — Avogadro | `rel_err ≤ 1e-8` | NA = 6.022e23 mol⁻¹ (SI 2019 exact) |

Physical anchor applies to: MTR-1/2/3/4/5/6, PHYS-01/02, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01.
Tamper-evident provenance: all 20 claims (SCOPE_001).
Documented in `reports/known_faults.yaml` :: SCOPE_001.

---

## Language policy

**Use:** "tamper-evident under trusted verifier assumptions"

**Never use:** "tamper-proof", "impossible to forge", "unforgeable", "blockchain"

The protocol is tamper-evident — modifications are detectable under the
described threat model. A sufficiently sophisticated adversary with full
codebase access could construct a passing fake bundle. Known limitations
are in `reports/known_faults.yaml`.

Step Chain is a cryptographic hash chain — same concept as git commits or
Merkle trees. It is not a blockchain. It requires no network, no consensus,
no external dependencies.

---

## 8 innovations (USPTO PPA #63/996,819)

1. **Governance-Enforced Bidirectional Claim Coverage**
   `scripts/steward_audit.py :: _claim_coverage_bidirectional()`

2. **Tamper-Evident Bundle with Semantic Verification Layer**
   `scripts/mg.py :: _verify_pack() + _verify_semantic()`
   Proven: `tests/steward/test_cert02_*`

3. **Policy-Gate Immutable Evidence Anchors**
   `scripts/mg_policy_gate_policy.json` (locked_paths)
   `.github/workflows/mg_policy_gate.yml`

4. **Dual-Mode Canary Execution Pipeline**
   `backend/progress/runner.py :: run_job(canary_mode=True/False)`

5. **Step Chain + Cross-Claim Cryptographic Chain**
   `backend/progress/mlbench1_accuracy_certificate.py :: _hash_step()`
   Proven: `tests/steward/test_cert03_*` + `tests/steward/test_cross_claim_chain.py`

6. **Bundle Signing (HMAC-SHA256 + Ed25519)**
   `scripts/mg_sign.py` + `scripts/mg_ed25519.py`
   Proven: `tests/steward/test_cert07_*` + `tests/steward/test_cert09_*`

7. **Temporal Commitment (NIST Randomness Beacon)**
   `scripts/mg_temporal.py`
   Proven: `tests/steward/test_cert10_*`

8. **5-Layer Independence Proof**
   Each layer catches attacks the other four miss.
   Proven: `tests/steward/test_cert11_*` + `tests/steward/test_cert12_*`

Verify full chain end-to-end:
```bash
python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/
# → CHAIN PASS
```

---

*MetaGenesis Verification Protocol (MVP) v0.9 — 2026-03-31*
*Inventor: Yehor Bazhynov — USPTO PPA #63/996,819*
