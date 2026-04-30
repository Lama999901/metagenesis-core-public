# Innovation 10: Federated Verification Registry with Cryptographic Provenance

**Status:** Architectural design (v4.0.0 vision)
**Patent claim:** Federated Verification Registry (FVR)
**Filing target:** Non-provisional patent application by 2027-03-05
**Motivation:** Multiple independent instances of the verification protocol must be able to contribute observations to shared learning without trust in any central party.

---

## 1. Problem statement

A single-instance verification protocol — even one whose own learning layer is verified per Innovation 9 — protects one deployment's record. The protocol's value scales with network effects: multiple independent instances (clients, organisations, research groups, regulators) producing verifications across overlapping domains. Without a federated contribution mechanism, each instance is isolated. Lessons cannot benefit other instances without some trust assumption — usually in a central operator who aggregates and re-publishes.

Naive aggregation requires a central authority that can be compromised, disappear, censor contributions, or selectively re-order history. Distributed-ledger approaches add consensus complexity inappropriate for verification semantics: there is no double-spend problem to solve here, no contention over a scarce resource, no need for byzantine agreement on a global state. What is needed is **provable origin** for each contribution — a cryptographic guarantee that "this observation came from instance X, was signed at time T, has payload hash H" — without any consensus mechanism imposed on the contribution itself.

---

## 2. Architectural principle

A registry that aggregates verified observations from multiple independent instances, where each contribution is cryptographically tied to its instance identity, such that:

1. **Origin of every contribution is provable** — by anyone reading the registry, with no central authority required.
2. **Aggregation does not require trust in the central operator** — the operator can refuse contributions only on signature/format failure, not on content.
3. **Each instance's local Innovation 9 chain remains authoritative for its own data** — the registry is a propagation layer, not a replacement.
4. **Public-safe contributions** — sanitised observations join shared learning surface; private/proprietary content stays local.
5. **Opt-in, opt-out, no consensus** — instances choose which registries to contribute to and can stop at any time without affecting their local operations.

The registry is **not** a database of verified truth. It is a coordination layer for cryptographically attested observations that downstream consumers can independently evaluate.

---

## 3. Three-component architecture

### Component A — Instance Identity Layer

Each protocol instance generates an Ed25519 identity keypair on first run (separate from any per-bundle signing key, to allow instance identity to persist across key rotations of operational keys). The public key is registered with a chosen registry endpoint. Instance ID = SHA-256 of the public key. Self-sovereign — no central key issuance, no certificate authority.

The identity keypair is created and persisted by `mg_register_identity.py` (to be implemented in v4.0.0 Phase 1). Loss of the private key invalidates the identity — a new identity is created and old contributions remain attributed to the previous identity (which is correct: those observations were signed under that key, which the operator no longer controls).

### Component B — Contribution Format

Sanitised observations wrapped in a signed envelope:

```json
{
  "instance_id": "<SHA-256 of public key>",
  "contribution_type": "pattern" | "finding" | "verification" | "metric",
  "payload": "<sanitised JSON, no PII or proprietary content>",
  "timestamp": "<ISO 8601>",
  "payload_hash": "<SHA-256 of canonical payload>",
  "signature": "<Ed25519 over instance_id || payload_hash || timestamp>",
  "prev_contribution_sig": "<signature of this instance's previous contribution, or null for first>"
}
```

Sanitisation rules enforced by `mg_contribute.py` (extending the existing script) before submission. The default ruleset rejects any payload containing the standard PII patterns, any path components matching the locked-files list, and any content matching the project's banned-terms denylist. Operators may add additional rules but cannot loosen the defaults below the protocol minimum.

### Component C — Aggregation Registry

An append-only registry that accepts signed contributions, validates signatures, deduplicates by `payload_hash`, indexes by `instance_id` and `contribution_type`. The registry itself runs a local Innovation 9 chain over its own contribution log — so the registry's own integrity is verifiable by the same standard as the protocol's per-instance learning.

The registry **does not**:

- Issue identities (each instance is self-sovereign).
- Censor contributions on content (rejection only on signature, format, or sanitisation-rule failure).
- Reach consensus on contribution validity (each contribution stands on its own provenance).
- Run verification computations (purely a coordination layer).

The registry **can**:

- Be operated by anyone (decentralised by deployment, not by consensus).
- Be replicated across operators (multiple registries; instances choose where to contribute).
- Be queried by anyone for aggregate statistics over signed contributions.
- Be audited end-to-end via its Innovation 9 chain.

---

## 4. Sample use cases

### Use case 1: Cross-organisational pattern sharing

Three biotech research groups using MetaGenesis Core for FDA submissions detect the same data-quality issue independently. With FVR, the second and third detections cite the first contribution's `payload_hash` — accelerating field learning without requiring any group to share proprietary data. Each contribution is cryptographically tied to its origin instance; each group can evaluate the others' patterns on their own merits.

### Use case 2: Recursive AI evolution substrate

Multiple AI evolution instances (recursive self-improvement systems running the protocol) each produce claims about their own evolution steps — what they changed, why, what gates passed. FVR aggregates these into a verifiable evolutionary record: each step is cryptographically attested to its origin instance, evolution lineage is reconstructable, and a downstream evaluator can verify any step's provenance without trusting the central registry operator.

This is the substrate Innovation 9 + Innovation 10 jointly enable for higher autonomy. Innovation 9 ensures each instance's learning is verifiable internally; Innovation 10 ensures the instance-to-instance contribution flow is verifiable across the network.

### Use case 3: Regulatory audit trail aggregation

A regulator (e.g., FDA reviewing AI medical-device submissions across 50 vendors) requires a pooled audit trail without forcing vendors to share confidential data. FVR provides aggregation of sanitised verification metadata — instance identity, contribution timestamp, signed payload hash, contribution type — without exposing underlying claim payloads. The regulator queries the registry for cross-vendor patterns; vendors keep their bundles private.

---

## 5. Implementation plan (v4.0.0)

**Phase 1 — Single-instance reference implementation** (~3–4 weeks for MVP):

- `mg_register_identity.py` — keypair generation, registration with chosen registry.
- `mg_contribute.py` extension — current text-only sanitiser extended to envelope format.
- `mg_registry_server.py` — minimal Flask / FastAPI registry, single-node, append-only log with Innovation 9 chain.
- Tests for round-trip submission and retrieval; signature validation; deduplication; sanitisation rule enforcement.

**Phase 2 — Multi-instance demo** (~1–2 weeks):

- Spin up 3 separate instance configs (different identity keypairs).
- Each contributes to a shared registry.
- Demonstrate cross-instance pattern reference: instance B cites instance A's contribution by `payload_hash`, signs its own contribution, registry validates and aggregates.

**Phase 3 — Production-ready** (~3–4 weeks):

- Replication protocol between registries (one registry pulls signed contributions from another; signatures are end-to-end verifiable, so registry-to-registry trust is not required).
- Public query API for aggregate statistics over a registry's contribution log.
- Operator documentation: how to host a registry, sanitisation policy customisation, replication peer setup.

Total: ~7–10 weeks across three phases, parallelisable in places.

---

## 6. Patent claim language (draft — to be finalised with attorney)

> A federated registry system for aggregating verified computational observations from multiple independent verification-protocol instances, comprising:
>
> (a) self-sovereign instance identity via asymmetric keypair, with an instance identifier derived from a hash of the public key, no central key-issuance authority being required;
>
> (b) a contribution format wrapping sanitised observations in cryptographically signed envelopes that bind each contribution to its instance identity and to the instance's previous contribution, forming a per-instance verification chain;
>
> (c) an append-only registry that validates signatures and deduplicates contributions by payload hash without requiring trust in instance operators and without imposing a consensus mechanism on contribution validity;
>
> (d) registry self-integrity via the verification chain mechanism applied to the registry's own contribution log, such that the registry operator's record-keeping is itself verifiable by any party reading the registry;
>
> wherein each contribution's provenance is independently verifiable by any party reading the registry without requiring trust in any central authority; and
>
> wherein the registry operates without consensus mechanism, without requiring trust in central authority for contribution validity, and without restricting the set of permitted instance operators.

---

## 7. Anti-pattern: what this is NOT

This is **NOT** a chain-of-blocks distributed ledger. There is no proof of work, no proof of stake, no consensus mechanism, no token, no mining, no global state agreement. The registry is an append-only log with cryptographic provenance — closer to a signed git tree replicated across operators than to distributed-ledger technology. There is no contention over a scarce resource, so there is no consensus problem to solve.

This is **NOT** a permissioned system. Anyone can run an instance. Anyone can run a registry. Anyone can query a registry. Registries differ only by which contributors trust them enough to submit and which consumers query them. Trust is per-relationship, not granted by any central authority.

This is **NOT** a token system or cryptocurrency. There are no fungible assets, no economic incentives encoded in the protocol, no "gas" or transaction fees mandated by the architecture. Adoption incentives are external — regulatory compliance value, peer-learning value, network-effect value — not internal to the registry mechanism.

This is **NOT** an automatic truth aggregator. The registry attests *that contribution X was signed by instance Y at time T with payload hash H* — not that the underlying observation is correct. Verification of the observation itself remains the consumer's responsibility, supported by Innovation 9's per-instance verification chain.

---

## 8. Threats addressed

- **Centralised censorship** — registry replication across independent operators allows alternatives. An instance whose contributions are rejected by one registry can submit to another.
- **Identity spoofing** — Ed25519 signatures cryptographically bind contributions to the instance keypair; a forger would need the private key.
- **Replay attacks** — `prev_contribution_sig` chaining detects replays of earlier contributions from the same instance; replays from other instances are detected by signature mismatch.
- **Sybil flooding without value** — registries can rate-limit per-instance; contribution value is per-payload (cited by hash), not per-instance count, so creating many sybil identities yields no proportional benefit.
- **Malicious registry operator silently dropping contributions** — instances can detect drops by monitoring their own contribution-chain inclusion in the registry's published index, and migrate to another registry if drops are detected.

## 9. Threats NOT addressed (out of scope)

- **Pure observational fraud** (an instance lies about what it observed) — addressed only by cross-instance corroboration over time, not by FVR alone. The registry attests provenance, not truth.
- **Registry operator acting maliciously beyond drops** (e.g., publishing fabricated contributions under fake identities) — addressed by the requirement that fake contributions need a valid Ed25519 signature against a registered public key; the operator cannot forge contributions without controlling the corresponding private key.
- **Long-term archival** (registries may go offline, lose data) — addressed by replication policy at the operator level; the protocol does not mandate any specific archival cadence.
- **Privacy of payload contents** — sanitisation rules are operator-configured; the protocol minimum is enforced but operators may need to add domain-specific rules (e.g., HIPAA, GDPR-specific PII patterns).

---

## 10. Network effects

The value of FVR scales superlinearly with instance count:

- 1 instance: trivial — equivalent to a local log.
- 10 instances: useful for pattern triangulation across organisations.
- 100 instances: regulatory-relevant aggregate evidence; cross-domain pattern discovery.
- 1,000+ instances: foundational substrate for AI evolution coordination, recursive self-improvement audit trails, and cross-organisational verification networks.

Each instance contributes incrementally; growth is organic, not mandated. There is no critical mass threshold below which the system fails — a single contributor and a single registry already produce value (verifiable signed log of the contributor's observations).

---

## 11. Composition with Innovation 9

Innovation 9 (Self-Verifying Recursive Learning Layer) and Innovation 10 (Federated Verification Registry) are **architecturally independent but synergistic**. Innovation 9 can ship without Innovation 10 (an instance verifies its own learning; useful in isolation). Innovation 10 can ship without Innovation 9 (a registry aggregates signed contributions; useful for cross-instance coordination). The combination is the foundation for higher-autonomy operations:

- Innovation 9 ensures **per-instance integrity** — each instance's learning is verifiable internally.
- Innovation 10 ensures **inter-instance coordination integrity** — contributions across instances are verifiably attributed.
- Together, they form the **integrity substrate** required for any future recursive self-improvement layer where multiple instances co-evolve and audit each other's evolution.

This composition is the technical realisation of "proof, not trust" at network scale.

---

## 12. References

- `docs/INNOVATION_09_SELF_VERIFYING_LEARNING.md` — Innovation 9 (companion architectural document)
- `reports/EVOLUTION_PROPOSALS_v3_2.md` — PROP-007, PROP-008 (loss-event-as-case-study and roadmap-vision proposals that mention FVR)
- `scripts/mg_contribute.py` — Phase 1 starting point (existing text-only contribution path)
- `EVOLUTION_LOG.md` — 2026-04-28 entry (motivating context for both Innovations)

---

## 13. Status tracking

- [x] Architectural design (this document) — committed 2026-04-28
- [ ] `mg_register_identity.py` — Phase 1 implementation (v4.0.0)
- [ ] `mg_contribute.py` envelope extension — Phase 1
- [ ] `mg_registry_server.py` reference implementation — Phase 1
- [ ] Multi-instance demo — Phase 2
- [ ] Replication protocol between registries — Phase 3
- [ ] Public query API — Phase 3
- [ ] Operator documentation — Phase 3
- [ ] Patent claim language finalised with attorney
- [ ] Non-provisional filing inclusion (deadline 2027-03-05)
