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

**Layer 4 — Bundle Signing (HMAC-SHA256 + Ed25519)**
Detects unauthorized bundle creator even when layers 1–3 all pass.
Dual-algorithm: HMAC-SHA256 for shared-secret workflows, Ed25519
for asymmetric third-party auditor verification.
Proven: `tests/steward/test_cert07_bundle_signing.py` + `tests/steward/test_cert09_ed25519_attacks.py`

**Layer 5 — Temporal Commitment (NIST Randomness Beacon)**
Detects backdated bundles — proves WHEN a bundle was signed.
Pre-commitment scheme: SHA-256(root_hash) committed before beacon
value fetched, binding = SHA-256(pre_commitment + beacon_value).
Proven: `tests/steward/test_cert10_temporal_attacks.py`

**5-Layer Independence**
CERT-11 proves each layer catches attacks the other four miss.
CERT-12 proves encoding attack resistance (BOM, null bytes, homoglyphs).
Proven: `tests/steward/test_cert11_*` + `tests/steward/test_cert12_*`

## Attack classes and which layer catches them

| Attack Class | Description | Caught By | Proof |
|---|---|---|---|
| File modification | Any byte changed in bundle after packaging | Layer 1 (Integrity) | CERT-01 |
| Evidence stripping | Remove evidence, recompute all SHA-256 hashes | Layer 2 (Semantic) | CERT-02 |
| Input manipulation | Change computation inputs (e.g., accuracy 0.94 to 0.95) | Layer 3 (Step Chain) | CERT-03 |
| Step reordering | Execute computation steps in different order | Layer 3 (Step Chain) | CERT-03 |
| Cross-domain substitution | Submit ML bundle as pharma claim | Layer 2 (Semantic) | CERT-05 |
| Canary laundering | Present non-authoritative run as authoritative | Layer 2 (Semantic) | CERT-05 |
| Anchor chain reversal | Skip intermediate claim in physical chain | Layer 3 (Step Chain) | CERT-05 |
| Unauthorized creator | Attacker builds valid bundle without signing key | Layer 4 (Signing) | CERT-07, CERT-09 |
| Key type confusion | Use HMAC key for Ed25519 or vice versa | Layer 4 (Signing) | CERT-09 |
| Backdating | Claim bundle was created at earlier time | Layer 5 (Temporal) | CERT-10 |
| Beacon manipulation | Tamper with NIST Beacon pre-commitment | Layer 5 (Temporal) | CERT-10 |
| Coordinated multi-vector | Combine attacks across multiple layers | All 5 layers (independence) | CERT-11 |
| Encoding attacks | BOM injection, null bytes, homoglyphs, truncated JSON | Layers 1-3 | CERT-12 |

Every attack class has a corresponding adversarial test that runs in CI on every merge. These are not theoretical -- they are executable proofs.

## Threat model assumptions

The protocol is tamper-evident under these assumptions:

| Assumption | What happens if violated | Mitigation |
|---|---|---|
| Verifier software is unmodified | PASS/FAIL results are meaningless | Verifier is open-source (MIT), deterministic, auditable |
| SHA-256 collision resistance holds | Layers 1 and 3 can be bypassed | Hash algorithm is upgradable without protocol change |
| Signing key is secret | Layer 4 can be bypassed (Layers 1-3 still catch content tampering) | Key rotation, Ed25519 asymmetric option |
| NIST Beacon is available | Temporal commitment degrades to local timestamp | Graceful degradation is documented behavior |

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

## Full protocol specification

For the complete verification algorithm, bundle structure, and claim lifecycle, see [docs/PROTOCOL.md](docs/PROTOCOL.md).

## Reporting security issues

If you find a way to construct a bundle that passes verification but contains incorrect or missing evidence, please report it responsibly:

**Email:** yehor@metagenesis-core.dev

**Include:**
- Reproduction steps (ideally a script or modified bundle)
- What verification reported (PASS when it should FAIL, or vice versa)
- Which layer you believe should have caught the attack
- What the bundle actually contained vs. what it claimed

**Response time:** Within 48 hours.

All verified vulnerabilities will be documented in `reports/known_faults.yaml` and fixed in the next release.
