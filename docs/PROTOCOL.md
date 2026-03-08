# MetaGenesis Verification Protocol (MVP) v0.1

## What this is

MVP is an open protocol specification for packaging computational claims
into independently verifiable evidence bundles.

A bundle created by any MVP-compliant implementation can be verified by
any MVP-compliant verifier — offline, without network access, without
trusting the bundle creator, without access to the original environment.

---

## Problem this solves

Computational results are increasingly central to scientific publications,
regulatory submissions, commercial agreements, and AI product claims.

There is no standard for what "independently verifiable" means for a
computational result. Every team invents its own provenance approach —
or does nothing.

MVP defines a minimal, concrete standard:

- What a verifiable bundle must contain
- What a compliant verifier must check
- What PASS and FAIL mean precisely
- What the verifier cannot be deceived by

---

## Bundle structure

An MVP-compliant bundle is a directory (or ZIP archive) with this structure:

```
bundle/
  pack_manifest.json        ← integrity layer
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

## pack_manifest.json

The integrity manifest. Contains SHA-256 hashes of every file in the bundle,
plus a root_hash computed over all file hashes.

```json
{
  "version": "1.0",
  "root_hash": "<sha256 of all file hashes concatenated>",
  "files": {
    "evidence/MTR-1/normal/run_artifact.json": "<sha256>",
    "evidence_index.json": "<sha256>"
  }
}
```

**Integrity check:** recompute all file hashes and root_hash, compare to manifest.
Any mismatch → FAIL.

---

## run_artifact.json

The evidence artifact produced by a single job run. Must contain:

```json
{
  "w6_phase": "W6-A5",
  "kind": "success",
  "job_id": "<uuid>",
  "trace_id": "<uuid>",
  "canary_mode": false,
  "job_snapshot": {
    "job_id": "...",
    "payload": { "kind": "<job_kind>" },
    "result": { "mtr_phase": "<CLAIM_ID>", ... },
    "status": "SUCCEEDED"
  },
  "ledger_action": "job_completed",
  "persisted_at": "<iso8601>"
}
```

**Semantic invariants a verifier must check:**

1. `job_snapshot` key must be present (not null, not empty)
2. `job_snapshot.payload.kind` must match the claim's registered `job_kind`
3. `canary_mode` must be `false` for authoritative evidence, `true` for canary
4. `ledger_action` must be `job_completed` (authoritative) or `job_completed_canary` (canary)
5. `job_snapshot.result.mtr_phase` must be present

---

## Verification algorithm

```
INPUT: bundle path

STEP 1 — Integrity check
  Load pack_manifest.json
  For each file in manifest:
    Compute SHA-256 of file content
    Compare to manifest hash
    If mismatch → FAIL("integrity: <file> hash mismatch")
  Recompute root_hash
  Compare to manifest root_hash
  If mismatch → FAIL("integrity: root_hash mismatch")

STEP 2 — Semantic check (runs even if integrity passes)
  For each claim in evidence_index:
    Load evidence/<CLAIM_ID>/normal/run_artifact.json
    Check job_snapshot present → if missing → FAIL("semantic: job_snapshot missing")
    Check payload.kind matches registered job_kind → if wrong → FAIL("semantic: kind mismatch")
    Check canary_mode == false → if true → FAIL("semantic: canary artifact used as authoritative")
    Check ledger_action == "job_completed" → if wrong → FAIL("semantic: wrong ledger action")

OUTPUT: PASS or FAIL with specific reason
```

---

## Why the semantic check exists

The integrity layer (SHA-256) is necessary but not sufficient.

**The bypass attack:**
An adversary can:
1. Remove `job_snapshot` from `run_artifact.json`
2. Recompute all SHA-256 hashes to match the modified file
3. Produce a bundle where integrity = PASS

Without the semantic layer, this attack succeeds silently.
With the semantic layer: integrity = PASS, semantic = FAIL.

This attack is proven and caught:
`tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`
`::test_semantic_negative_missing_job_snapshot_fails_verify`

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

Checked automatically by `python scripts/steward_audit.py` on every PR.

---

## Claim lifecycle (how to add a domain)

To extend MVP to a new computational domain:

1. Implement: `backend/progress/<claim_id>.py` with `JOB_KIND` constant and `run_*()` function
2. Dispatch: add dispatch block in `runner._execute_job_logic()`
3. Register: add claim section in `reports/scientific_claim_index.md`
4. Anchor: add claim_id to `reports/canonical_state.md` current_claims_list
5. Test: write tests in `tests/<domain>/` covering pass, fail, and adversarial cases
6. Verify: `python scripts/steward_audit.py` → PASS

---

## Current domains

| Domain | Claim IDs | Status |
|--------|-----------|--------|
| Materials science | MTR-1, MTR-2, MTR-3 | Active |
| System identification | SYSID-01 | Active |
| Data pipelines | DATA-PIPE-01 | Active |
| Drift monitoring | DRIFT-01 | Active |
| ML benchmarking | ML_BENCH-01 | Active |

---

## Language policy

This protocol uses precise language about what it guarantees:

**Use:** "tamper-evident under trusted verifier assumptions and semantic invariants"

**Never use:** claims of perfect or unfalsifiable security (e.g. impossible to forge, 100% secure). Prefer "tamper-evident" over absolute integrity wording.

The distinction is material. Tamper-evident means modifications are detectable
by the verification layer under the threat model described above. It does not
mean a sufficiently sophisticated adversary with full codebase access cannot
construct a passing fake bundle. Limitations are in `reports/known_faults.yaml`.

---

## Patent

USPTO PPA #63/996,819, filed 2026-03-05, inventor Yehor Bazhynov.
4 patentable innovations implement this protocol:
bidirectional claim coverage, semantic tamper detection,
policy-gate immutable anchors, dual-mode canary pipeline.
