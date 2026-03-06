# MetaGenesis Core — PPA Preflight Package v2

**Scope:** Verification Core (backend/progress/, scripts/, tests/)
**Protocol:** docs/DETERMINISTIC_CLAIM_PROTOCOL_v1_0.md
**Steward:** python scripts/steward_audit.py → PASS (2026-03-03)

Previous version (v1.0) described phases 1-42 and
non-existent features. This version describes only what
exists in code and passes tests.

---

## What This PPA Covers

```
MetaGenesis Core is a verification-grade computational
discipline framework: an infrastructure layer that turns
computational claims into tamper-evident, reproducible,
governance-enforced evidence bundles.

NOT claimed: simulation engines, AI coordination,
surveillance, quantum fields, molecular assembly.

CLAIMED: the governance + evidence + verification pipeline
that makes any computational claim independently verifiable.
```

---

## Package Contents

| File | Purpose | Based on |
|------|---------|----------|
| `CLAIMS_DRAFT.md` | 4 independent + 8 dependent claims | Verified code only |
| `EVIDENCE_INDEX.md` | Claim-to-code-to-test mapping | steward_audit PASS |
| `README_PPA.md` | This file | Current |
| `SYSTEM_ARCHIVE.docx` | Technical documentation (legacy, not part of claims) | — |
| `FIGURES/` | Architecture diagrams | See below |

---

## Core Architecture (what is patented)

```
PROOF LOOP (docs/ARCHITECTURE_OVERVIEW.md):

  Job Run
    ↓
  Runner (backend/progress/runner.py)
    ↓ normal mode          ↓ canary mode
  run_artifact.json      run_artifact.json
  (canary_mode=false)    (canary_mode=true)
  ledger_snapshot.jsonl  ledger_snapshot.jsonl
    ↓
  Evidence Index (backend/progress/evidence_index.py)
    ↓
  Submission Pack (scripts/steward_submission_pack.py)
    pack_manifest.json    ← integrity layer
    evidence_index.json   ← claim mapping
    evidence/<ID>/        ← per-claim bundles
    ↓
  mg verify (scripts/mg.py)
    integrity check (SHA-256 + root_hash)
    semantic check (job_snapshot present, kind matches, canary flag correct)
    ↓
  PASS or FAIL with specific reason
```

---

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
python -m pytest tests/steward tests/materials -q
# Expected: 49 passed
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
□ steward_audit.py → PASS
□ test_cert02 → PASS (both normal + tamper tests)
□ python -m pytest tests/steward tests/materials -q → 49 passed
□ All 6 claims reproducible via python -m pytest

Pre-filing (documentation):
□ CLAIMS_DRAFT.md — V2 (code-backed, no invented features)
□ EVIDENCE_INDEX.md — V2 (real test paths, no fake SHA)
□ SYSTEM_ARCHIVE.docx — legacy only, not part of claims (no action required)
□ README.md — remove "GPT-5", "19x without baseline", "symbiotic AI"

Pre-filing (legal):
□ Confirm grace period window (repo was public < 12 months ago)
□ Patent attorney review of Claims 1-4
□ Confirm inventor name and assignment
□ File via USPTO EFS-Web as Provisional Patent Application
```

---

## Key Protocol Documents

```
docs/DETERMINISTIC_CLAIM_PROTOCOL_v1_0.md
  → Defines: claim, job_kind, trace_id, canary, evidence artifact,
    ledger snapshot, governance rules, canonical sync invariant,
    conformance test suite

docs/ARCHITECTURE_OVERVIEW.md  
  → Proof loop diagram (Mermaid)
  → Claim lifecycle diagram: Open→Implement→Validate→Register→Package→Submit

reports/scientific_claim_index.md
  → Canonical claim registry: claim_id, job_kind, V&V thresholds,
    reproduction command, evidence fields

reports/canonical_state.md
  → Authoritative project state snapshot
  → current_claims_list: MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01, DRIFT-01
```

---

*PPA README v2. Scope: verification core only.
No invented features. Every section traceable to passing tests.*
