# Security

## What this system guarantees

MetaGenesis Core provides tamper-evident verification of
computational claims. It does not guarantee correctness of
the underlying algorithms — only that the evidence bundle
contains what it claims to contain and has not been modified.

Specifically:

**Layer 1 — Integrity** (SHA-256 + root_hash)
Detects any modification to files in the bundle after the
manifest was generated. If a file changes, the hash fails.

**Layer 2 — Semantic**
Detects removal or modification of required evidence content
even when an adversary recomputes all integrity hashes.
An attacker who removes job_snapshot and recomputes all
SHA-256 hashes still fails semantic verification.
Proven: `tests/steward/test_cert02_*::test_semantic_negative_missing_job_snapshot_fails_verify`

**Layer 3 — Step Chain**
Detects computation inputs changed or steps reordered, even when
layers 1 and 2 both pass. Every execution produces a 4-step
cryptographic hash chain. trace_root_hash commits to the entire
execution sequence. Tampering any step breaks the chain.
Proven: `tests/steward/test_cert03_step_chain_verify.py::test_tampered_trace_root_hash_fails`

**Cross-Claim Cryptographic Chain**
For physical domains (MTR-1 → DT-FEM-01 → DRIFT-01), each claim's
trace_root_hash is embedded as anchor_hash in the next claim's Step Chain.
The full chain from physical measurement to simulation output is
cryptographically verifiable end-to-end.
Proven: `tests/steward/test_cross_claim_chain.py::test_full_chain_is_cryptographically_linked`

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
