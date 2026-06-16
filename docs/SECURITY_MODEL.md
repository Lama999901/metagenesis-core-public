# MetaGenesis Core — Security Model

This document states what MetaGenesis Core proves, what it does not prove, and
the honest limits of each verification layer. It is written for a client or an
independent auditor who needs to trust a verification result before relying on
it. Honest disclosure beats a false PASS.

For the complete fault registry, see `reports/known_faults.yaml`.

## Threat model & honest limits

MetaGenesis Core is a notary for computations: it makes a computational claim
tamper-evident, reproducible, and independently auditable offline. It does this
in five independent layers (integrity, semantic, step chain, signing, temporal).
Each layer answers a different question, and each has a precise scope. The
sections below describe the limits that matter most when deciding how far to
trust a bundle.

### 1. Integrity is not authenticity — they are two distinct steps

There are two separate questions, answered by two separate commands:

- **Integrity** — *does the bundle match its manifest?*
  `python scripts/mg.py verify --pack <dir>` recomputes the SHA-256 of every
  file listed in `pack_manifest.json` and checks the `root_hash`. A PASS proves
  the bundle's files are exactly the bytes the manifest commits to.

- **Authenticity** — *who created the bundle?*
  `python scripts/mg.py sign verify --pack <dir>` (the `mg sign verify` step)
  checks the Ed25519 signature over the bundle. A PASS proves the bundle was
  produced by the holder of a known signing key.

These are independent. An **unsigned bundle can pass integrity yet have unknown
provenance** — the files are internally consistent, but nothing proves who built
them. Integrity alone is not provenance. Both matter: integrity tells you the
bundle was not modified after it was sealed; authenticity tells you the seal came
from a party you recognize. When provenance matters (regulatory submission,
third-party audit), require both steps, not just `verify`.

### 2. Ed25519 is a pure-Python RFC 8032 reference implementation

The signing layer uses a pure-Python implementation of Ed25519 (RFC 8032),
validated against all five RFC 8032 test vectors. Two honest properties of this
choice:

- It is **not constant-time**. A constant-time implementation resists an attacker
  who can measure the timing of operations on a secret key.
- Why this is acceptable here: **signing is offline and signer-side**. The signing
  key never leaves the machine that controls it, and there is no remote timing
  oracle against a secret you hold. The threat that constant-time code defends
  against does not apply to this workflow.

A libsodium-backed signing path is a possible future option if constant-time
signing is ever required (for example, signing on shared infrastructure). We
state this plainly rather than overclaiming: the current implementation is a
reference implementation, correct against the standard's vectors, and adequate
for offline signer-side use.

### 3. Receipt timestamp is the local clock, not proof-of-time

When you run `verify --receipt <out.json>`, the receipt contains a
`verification_timestamp` field. This value is the **verifier's LOCAL clock**
(`datetime.now(timezone.utc)` in `scripts/mg.py`). It is **informational only**
and is trivially settable by whoever runs `verify` — it is not cryptographic
proof of when anything happened.

Proof-of-time is a **separate layer**: the temporal commitment layer
(`scripts/mg_temporal.py`), which binds a bundle to a NIST Randomness Beacon
pulse. That layer is what actually resists backdating, because the beacon value
cannot be predicted before its publication time. Do not mistake the receipt
timestamp for proof-of-time. If you need to prove *when* a bundle existed, rely
on the temporal commitment layer, not the receipt's `verification_timestamp`.

### 4. Smuggling detection — manifest-absent files are rejected (FAULT_012 RESOLVED)

`mg verify` checks every file **listed in** `pack_manifest.json` and, since the
FAULT_012 fix, also enumerates the pack directory and **fails** on any extra file
present on disk that is absent from the manifest. A file added to the pack but
never listed in the manifest is therefore detected and rejected (verify returns
rc != 0), closing the earlier smuggling vector where verify could report PASS with
an unlisted file present.

The enumeration is recursive and matches on the root-relative path, so a file
smuggled into a subdirectory is rejected too. Exactly three verification
meta-files are written outside the manifest and are excluded by name at the pack
root: `pack_manifest.json` (the manifest itself), `bundle_signature.json` (written
post-build by `mg sign`), and `temporal_commitment.json` (written post-build by
the temporal layer). This is disclosed as **FAULT_012 (RESOLVED)** in
`reports/known_faults.yaml` and confirmed adversarially in
`tests/steward/test_security_findings.py`, which asserts that both a root-level and
a nested smuggled file drive verification to a non-zero return code.

---

For the full registry of known limitations and their dispositions, see
`reports/known_faults.yaml`.
