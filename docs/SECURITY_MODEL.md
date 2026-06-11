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

### 4. Smuggling limitation — manifest-absent files are not flagged

`mg verify` checks every file **listed in** `pack_manifest.json`, but it does not
currently fail on extra files that are present in the pack directory yet absent
from the manifest. A file added to the pack but never listed in the manifest is
neither hashed nor flagged, so verify can report PASS with an unlisted file
present (a smuggling vector). This is disclosed as **FAULT_012** in
`reports/known_faults.yaml` and confirmed adversarially in
`tests/steward/test_security_findings.py` (a strict-xfail tripwire plus a
companion test pinning the current behavior).

The **planned fix** is to enumerate the pack directory and reject any non-manifest
file that is not listed. Until that ships, treat the manifest as the authoritative
file set and reject packs from untrusted builders — verify what the manifest
commits to, and do not assume the manifest covers every byte on disk.

---

For the full registry of known limitations and their dispositions, see
`reports/known_faults.yaml`.
