# Innovation 9: Self-Verifying Recursive Learning Layer

**Status:** Architectural design (v3.2.0 implementation target)
**Patent claim:** AGENT-LEARNING-01 (planned 21st claim)
**Filing target:** Non-provisional patent application by 2027-03-05
**Motivation:** 2026-04-28 Agent Memory Data Loss Event (see `EVOLUTION_LOG.md`, PR #283 commit `ec72d0b`, PR #284 commit `70954f0`)

---

## 1. Problem statement

The MetaGenesis Core verification protocol applies five-layer cryptographic verification (integrity, semantic, step chain, bundle signing, temporal commitment) to external computational claim bundles. The protocol's central thesis is **proof, not trust**: every claim must be independently verifiable by an auditor with no special access.

The protocol's own learning record — `.agent_memory/knowledge_base.json`, `resolved_patterns.json`, observer outputs across the eight files documented in `docs/EVOLUTIONARY_ARCHITECTURE.md` §3 — has historically been outside the protocol's verification scope. The directory is gitignored (`.gitignore:97`), the entries are unsigned, the chain has no integrity attestation, and the file family has no append-only enforcement.

Consequence: the protocol could verify its inputs but not itself. Loss, modification, or corruption of the learning record was silent and undetectable. The 2026-04-28 data loss event is the empirical realisation of this structural gap. ~125 session entries spanning 2026-03-18 → 2026-04-16 were lost from a single working-copy cleanup; recovery investigation across eleven independent paths (three in PR #283, eight in PR #284) yielded zero bytes.

A verification protocol whose own learning artefact is outside its verification scope is incomplete by its own standard. Innovation 9 closes the gap.

---

## 2. Architectural principle

**The same verification chain that protects external computational claims must apply recursively to the protocol's own learning record.** The protocol verifies itself by the same standard it applies to others. No new verification primitive is introduced; the existing 5-layer chain is recursively self-applied.

This is structural, not procedural. The protocol does not adopt a new policy that "we'll be careful with `.agent_memory/`." It binds the existing cryptographic verification to the learning record so that a future loss is detectable, the integrity is attested, and the rebuild has a verifiable baseline.

---

## 3. Five layers applied to the learning record

### Layer 1 — Integrity (SHA-256 root hash)

Each session entry written by `agent_learn.py observe` includes a SHA-256 hash over its canonical JSON representation. The KB tail-pointer is the hash of the most recent entry. Any modification to a previous entry invalidates the chain from that point forward; any deletion creates a hash-mismatch at the next entry that referenced the deleted hash. Tampering becomes mechanically detectable.

### Layer 2 — Semantic verification

Schema validation per session entry. Required fields:
- `session_id` (UUID, unique across the chain)
- `timestamp` (ISO 8601, monotonic non-decreasing across the chain)
- `observer_outputs` (object — gate results)
- `prev_entry_hash` (SHA-256 of previous entry, or `null` for genesis)
- `entry_signature` (Ed25519 over canonical payload)
- `source` (enum: `curated` | `observed` | `synthesized`)
- `version_at_observation` (string — protocol version when entry was written)

Semantic invariants:
- `source` field is mandatory and must be one of the enum values.
- `timestamp` of entry N must be > timestamp of entry N-1.
- `session_id` must be unique across the entire chain.
- `prev_entry_hash` must equal SHA-256 of entry N-1's canonical form.

Schema and invariant violations are rejected at write time and detected at verification time.

### Layer 3 — Step chain (4-step execution trace per observe call)

Each `agent_learn.py observe` invocation produces a four-step trace, mirroring the existing Step Chain Verification primitive used for external claims:

1. **Load** — read previous tail entry from `knowledge_base.json`; verify its signature and chain link.
2. **Validate** — check schema and semantic invariants of the new payload (Layer 2).
3. **Hash + sign** — compute new entry's SHA-256, sign canonical payload with Ed25519 key, embed `prev_entry_hash`.
4. **Append + verify** — append to KB; immediately re-verify the chain end-to-end before returning.

The 4-step trace hash is committed as part of the entry metadata. Tampering with the trace itself breaks the chain in the same way any other tampering does.

### Layer 4 — Bundle signing (Ed25519)

Per-session **verification receipt** artefact written to `proof_library/session_receipts/<UTC-timestamp>_<sha-prefix>.json`, signed with the project Ed25519 key (the same key family as `mg_sign.py` and `mg_ed25519.py`). Receipts are independent of `knowledge_base.json` — they survive even if the KB itself is lost. A reviewer asking "show me what session 47 actually did" reads the receipt directly; KB integrity is corroborating evidence, not the only evidence.

Receipts directory is committed to the repo (gitignored only for size control, but PROP-004 daily snapshots address the size argument by compressing snapshots).

### Layer 5 — Temporal commitment (NIST Beacon)

**Optional, weekly cadence.** A weekly aggregate snapshot of the KB tail-hash is committed alongside the latest NIST Randomness Beacon timestamp. This proves *when* the cumulative learning state was attested — it cannot be retrofitted.

Optional because the temporal commitment is most valuable in adversarial settings (proving the KB existed in a specific state at a specific time to defeat backdating claims). For the routine integrity-protection use case, Layers 1–4 are sufficient.

---

## 4. Verification mechanism — new claim AGENT-LEARNING-01

A new scientific claim is added to the protocol's claim registry:

- **Claim ID:** AGENT-LEARNING-01
- **JOB_KIND:** `agent_learning_verification_certificate`
- **Implementation file:** `backend/progress/agent_learning_monitor.py` (to be created in v3.2.0)
- **V&V threshold:** `schema_valid AND chain_intact AND signatures_valid AND mtime_within_7_days AND no_duplicate_session_id AND timestamp_monotonic`

A new `agent_evolution.py` check #23, `check_kb_chain_integrity`, invokes AGENT-LEARNING-01 verification on every CI run. FAIL on any chain element broken, signature invalid, schema violation, or duplicate `session_id`. The check moves the gate count from 22 to 23.

A complementary check #24, `check_kb_append_only` (PROP-002), validates that the current KB entries are a strict superset of the previous CI run's snapshot — modifications and deletions to historical entries are detected even if the chain itself is intact.

---

## 5. Implementation plan (v3.2.0)

Per `reports/EVOLUTION_PROPOSALS_v3_2.md`:

| Proposal | Scope | Effort |
|---|---|---|
| PROP-001 | Cryptographic baseline (Ed25519 signing per session entry) | ~2 days |
| PROP-002 | Append-only enforcement (check #24, prev-snapshot diff) | ~1 day |
| PROP-003 | Per-session receipts (`mg_session_receipt.py`) | ~1.5 days |
| PROP-004 | Daily KB snapshots committed to `docs/memory_snapshots/` | ~1 day |
| PROP-005 | Pattern signed-chain (`patterns.json` / `resolved_patterns.json` hardening) | ~1.5 days |

Total: ~5–7 days of focused work, sequential execution. PROP-006 (external backup) and PROP-010 (semantic_audit fix for the 4 client demos) are independent and can run in parallel.

---

## 6. Patent claim language (draft — to be finalised with attorney)

> A method for self-applying cryptographic verification to a verification protocol's own operational learning record, comprising:
>
> (a) integrity hashing of each learning entry to produce a content digest, the digest being included in the subsequent entry to form a one-way verification chain;
>
> (b) semantic validation of entry schema and invariants, including monotonic timestamp ordering and unique session identifiers, applied at both write time and verification time;
>
> (c) execution trace generation comprising at least four steps — load-and-verify, schema-validate, hash-and-sign, append-and-reverify — with a digest of the trace bound to the entry;
>
> (d) digital signing of per-session verification receipts with an asymmetric private key, the receipts being persisted independently of the learning record itself;
>
> (e) optional temporal commitment via an external randomness beacon, binding the cumulative learning state to a public timestamp;
>
> wherein the verification mechanism applied to the learning record is structurally identical to the mechanism applied by the protocol to external computational claims; and
>
> wherein loss, modification, or corruption of the learning record becomes mechanically detectable by the same verification chain that the protocol applies to external evidence, without requiring trust in any operator of the learning system.

---

## 7. Anti-pattern: what this is NOT

This is **NOT** a chain-of-blocks distributed ledger. There is no consensus mechanism, no proof of work, no proof of stake, no token, no mining, no peer-to-peer broadcast. The chain is a single-author append-only log with cryptographic verification — closer in form to a signed git commit history than to distributed-ledger technology. The architectural goal is integrity attestation under a trusted-author model, not byzantine fault tolerance.

This is **NOT** autonomous self-modification. The verification mechanism detects tampering of the learning record; it does not authorise self-modifying code. Governance remains human-gated. Level 4 autonomy ("the system modifies its own check rules without review") is intentionally absent per `docs/EVOLUTIONARY_ARCHITECTURE.md` §2.4 — and Innovation 9 does not change that.

This is **NOT** post-quantum secure. Ed25519 is the current-generation choice. Migration to a post-quantum signature scheme (e.g., CRYSTALS-Dilithium, ML-DSA) is on a separate roadmap (FAULT_004 in `reports/known_faults.yaml`) and applies uniformly to all protocol layers, not just to AGENT-LEARNING-01.

This is **NOT** retroactive. The 125 session entries lost on 2026-04-28 cannot be reconstructed and signed under this scheme. The chain begins at the next observe-run after AGENT-LEARNING-01 lands. Pre-AGENT-LEARNING-01 history is recovered from the surviving sources documented in `EVOLUTION_LOG.md`'s 2026-04-28 entry — and the loss event itself is recorded as the genesis-context of why the chain begins where it does.

---

## 8. Threats addressed

- **Silent learning loss** (e.g., 2026-04-28 event) — detected via chain break, missing tail pointer, or absent signed receipts.
- **Adversarial modification of curated patterns** — detected via signature invalidation on the modified entry.
- **Forged session entries inserted out-of-band** — detected via missing valid signature against the project public key.
- **Replay of historical entries** — detected via unique `session_id` enforcement and `prev_entry_hash` chaining (replays would produce duplicate IDs or break the chain link).
- **Reorder of entries** — detected via `timestamp` monotonicity invariant and chained `prev_entry_hash` (any reorder breaks the chain).

## 9. Threats NOT addressed (out of scope)

- **Compromised verifier machine** (FAULT_005) — if the project Ed25519 private key is compromised, the attacker can forge new entries that the verification chain accepts. Key custody is a separate problem; this innovation assumes key integrity.
- **Algorithmic correctness of underlying observations** (FAULT_006) — the chain attests to *what was recorded*, not to whether the gates that produced the observations were themselves correct.
- **Pre-image / collision attacks on SHA-256** — current cryptographic baseline assumption; addressed by post-quantum migration when feasible.
- **Erasure of the entire learning record between snapshots** — the chain has no defence against complete deletion of every artefact in one operation. PROP-004 (daily snapshots committed to repo) and PROP-006 (external backup) are the operational compensations; neither lives inside Innovation 9 itself.

---

## 10. References

- `reports/AGENT_LEARN_FULL_AUDIT_2026_04_28.md` (PR #283, commit `ec72d0b`)
- `reports/AGENT_LEARN_DEEPER_VALIDATION_2026_04_28.md` (PR #284, commit `70954f0`)
- `reports/EVOLUTION_PROPOSALS_v3_2.md` — PROP-001, PROP-002, PROP-003, PROP-004, PROP-005
- `EVOLUTION_LOG.md` — 2026-04-28 entry (motivating event)
- `docs/PROTOCOL.md` — existing 5-layer protocol specification
- `docs/EVOLUTIONARY_ARCHITECTURE.md` §2 (the four-level governance structure that AGENT-LEARNING-01 sits inside) and §3 (the memory-system files this innovation protects)
- `scripts/agent_learn.py`, `scripts/mg_ed25519.py`, `scripts/mg_sign.py`, `scripts/mg_temporal.py` (existing primitives that AGENT-LEARNING-01 composes)

---

## 11. Status tracking

- [x] Architectural design (this document) — committed 2026-04-28
- [ ] PROP-001 — Ed25519 signing per session entry
- [ ] PROP-002 — append-only enforcement (check #24)
- [ ] PROP-003 — per-session verification receipts
- [ ] PROP-004 — daily KB snapshots in `docs/memory_snapshots/`
- [ ] PROP-005 — pattern signed-chain
- [ ] `agent_evolution.py` check #23 (`check_kb_chain_integrity`) — wired in
- [ ] AGENT-LEARNING-01 claim added to canonical claim registry
- [ ] Patent claim language finalised with attorney (Q3 2026 engagement target per `AGENT_TASKS.md` TASK-036)
- [ ] Non-provisional filing inclusion (deadline 2027-03-05)
