# MetaGenesis Core — Evolution Roadmap

Four levels of evolution. Each builds on the last.
Each has a first client that proves the value.

---

## Level 1 — PROTOCOL (v1.0.0, exists now)

Any computation verified in 60 seconds.
Physical anchor in SI 2019 exact constants.
1753+ tests. Offline. No trust required.

**What it does:**
- 5-layer verification (integrity, semantic, step chain, signing, temporal)
- 20 active claims across 8 computational domains
- Physical anchor chain from kB/NA to simulation outputs
- Standalone verifier: one Python file, zero dependencies

**Minimum viable pilot:** Client submits CSV, receives verified bundle + receipt.
**First client:** Any organization producing computational results that require independent verification. Target: $299 per bundle.
**Academic publication:** JOSS paper (paper.md) — resubmit September 2026 after 6 months public history.
**Duration:** Shipped. Ongoing refinement.

---

## Level 2 — REGISTRY (v2.0, next milestone target)

Global database of verified computations with public access.
Every verified bundle gets a persistent DOI via Zenodo.
Scientists publish not just a PDF — but the bundle alongside it.

**What it does:**
- `scripts/agent_registry.py` — submit verified bundle, receive DOI
- `reports/registry_index.json` — local index of all submitted bundles
- Zenodo API integration for persistent, citable identifiers
- Public search endpoint: "Was this computation verified by MetaGenesis?"

**Minimum viable pilot:** Research lab submits 3 verified bundles, receives DOIs, cites them in a paper.
**First client:** Computational science lab that needs verifiable, citable results (target: 3 computational journals adopting the standard).
**Academic publication:** Paper on "Cryptographic Verification as a Standard for Computational Reproducibility" — target Nature Methods or similar.
**Estimated duration:** 3-4 months after v2.0.0 ships.

**Technical path:**
```
Verified bundle → agent_registry.py → Zenodo API → DOI minted
                                    → registry_index.json updated
                                    → Public lookup: DOI → verification status
```

---

## Level 3 — AGENT ECONOMY (v3.0)

Autonomous agents verify each other's outputs.
AI model produces result → Verification agent checks via MetaGenesis → Archive agent stores bundle permanently.
The protocol becomes the trust layer between autonomous systems.

**What it does:**
- `scripts/agent_network.py` — inter-agent verification protocol
- Standardized format: `{agent_id, claim_id, bundle_path, verification_status, timestamp}`
- Agent-to-agent trust chain: Agent A verifies Agent B's output, Agent C verifies A's verification
- Dispute resolution: when two agents disagree, the physical anchor chain decides

**Minimum viable pilot:** Two AI agents running different ML models, each verifying the other's benchmark results via MetaGenesis. Neither trusts the other. Both trust the protocol.
**First client:** AI lab deploying agents at scale that need auditable inter-agent trust (e.g., multi-model ensemble systems).
**Academic publication:** Paper on "Cryptographic Trust Layers for Multi-Agent AI Systems" — target NeurIPS or AAAI.
**Estimated duration:** 6-8 months after v3.0 ships.

**Technical path:**
```
Agent A produces ML result → creates bundle
Agent B runs: mg_verify_standalone.py bundle/ → PASS/FAIL
Agent B signs verification with own Ed25519 key
Result: two independent cryptographic attestations of the same computation
```

---

## Level 4 — SELF-EVOLUTION (v4.0)

The protocol verifies its own development process.
Every code change to MetaGenesis passes through MetaGenesis.
The system that certifies others is itself certified — recursively.

**What it does:**
- `agent_evolution_council.py` proposes improvements (built in v2.0.0)
- Protocol verifies the proposal is safe: "Will this change break existing verification chains?"
- Best proposals merge autonomously with cryptographic proof of safety
- Every merged PR includes a verification bundle proving the change was tested
- Self-audit (built in v2.0.0) ensures no core script was tampered with

**Minimum viable pilot:** One autonomous merge — agent proposes improvement, protocol verifies it won't break anything, merge happens with cryptographic proof attached to the PR.
**First client:** Any organization requiring auditable AI governance — "How do you know your AI system's code changes are safe?"
**Academic publication:** Paper on "Self-Verifying Software Systems: When the Auditor Audits Itself" — target IEEE S&P or USENIX Security.
**Estimated duration:** 12+ months after v4.0 ships.

**Technical path:**
```
agent_evolution_council.py → PROP-001
mg_self_audit.py → baseline verified
pytest → all tests pass
mg.py verify → proposal bundle PASS
autonomous merge with verification receipt attached
```

---

## The Long Game

Each level makes the protocol harder to dispute:

| Level | What it proves | Who trusts it |
|-------|---------------|---------------|
| Protocol | This computation was not tampered with | One client |
| Registry | This computation has a permanent, citable record | Journals |
| Agent Economy | Autonomous systems can trust each other's outputs | AI labs |
| Self-Evolution | The verification system itself is verified | Everyone |

The physical anchor is the foundation that makes all four levels possible.
kB = 1.380649e-23 J/K. Defined in 2019. Will never change.
Build on that, and the protocol outlasts everything else.

---

*ROADMAP_VISION v1.0 — 2026-04-04*
*MetaGenesis Core | Inventor: Yehor Bazhynov | PPA #63/996,819*
