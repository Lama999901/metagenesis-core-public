# Security

## What this system guarantees

MetaGenesis Core provides tamper-evident verification of
computational claims. It does not guarantee correctness of
the underlying algorithms — only that the evidence bundle
contains what it claims to contain and has not been modified.

Specifically:

**Integrity layer** (SHA-256 + root_hash)
Detects any modification to files in the bundle after the
manifest was generated. If a file changes, the hash fails.

**Semantic layer**
Detects removal or modification of required evidence content
even when an adversary recomputes all integrity hashes.
An attacker who removes job_snapshot and recomputes all
SHA-256 hashes still fails semantic verification.

This is proven by an adversarial test that ships with the repo:
`tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`
`::test_semantic_negative_missing_job_snapshot_fails_verify`

## What this system does NOT guarantee

- Correctness of the algorithm that produced the result
- That input data is representative or unbiased
- That the verification logic itself has no vulnerabilities
- That a sufficiently sophisticated adversary with full access
  to the codebase cannot construct a passing fake bundle

These limitations are documented in `reports/known_faults.yaml`.

## Language policy

This system is described as "tamper-evident" — not "tamper-proof".
The distinction is intentional and material.

Tamper-evident means: modifications are detectable by the
verification layer under the threat model described above.
It does not mean modifications are impossible.

## Reporting issues

If you find a way to construct a bundle that passes verification
but contains incorrect or missing evidence, please report it:

yehor@metagenesis-core.dev

Include: reproduction steps, what verification reported,
what the bundle actually contained.
