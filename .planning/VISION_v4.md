# MetaGenesis Core — Evolution Map

## 4 Levels

### LEVEL 1 — NOW (v0.9.0)

CLI verification tool. Physical anchor chain. 2012 adversarial tests. 20 claims across 8 domains. 5 independent verification layers. 20 autonomous checks. Patent pending.

**What exists:** `python scripts/mg.py verify --pack bundle.zip` — PASS or FAIL in 60 seconds, offline, any machine.

**Trigger to Level 2:** First paying client ($299) + first external endorsement (academic citation, conference mention, or integration partner).

---

### LEVEL 2 — v3.0.0: Client-Ready Protocol

Guided onboarding. REST API. Human-readable receipts. 60-second response kits for every contact. Any person goes from zero to verified bundle in under 10 minutes.

**What gets built:** mg_onboard.py, mg_api.py (FastAPI), mg_receipt.py (auditor-readable), docs/QUICKSTART.md, docs/CLIENT_SCENARIOS.md.

**Trigger to Level 3:** 5 paying clients across 2 verticals (e.g., ML + pharma, or finance + materials).

---

### LEVEL 3 — Future: Autonomous Verification Agent

The system communicates with clients directly. Bundles get DOIs. Public registry of verified computations. Automated re-verification on schedule.

**What gets built:** Public bundle registry. DOI minting per verification. Scheduled re-verification (drift detection over time). Client-facing dashboard. Automated response and follow-up.

**Trigger to Level 4:** 100+ bundles verified, institutional adoption (university lab, pharma company, or financial institution as repeat customer).

---

### LEVEL 4 — Horizon: Verified Science Infrastructure

Global standard for computational verification. kB = 1.380649e-23 J/K does not change. NA = 6.02214076e23 mol-1 does not change. The physical anchor chain holds forever.

**What this looks like:** NeurIPS requires verification bundles at submission. FDA accepts MetaGenesis receipts as audit artifacts. Basel III auditors verify VaR models offline. Carbon credit models carry cryptographic proof.

---

## Hidden Killer Application: Calibration Drift

Compare a bundle today with a bundle from one year ago. Same system, same claim, different result. MetaGenesis catches it automatically.

**Why this matters:**
- Medical AI: model accuracy degrades silently as population shifts
- Industrial sensors: calibration drifts between maintenance cycles
- Financial models: risk parameters drift under market regime changes
- Digital twins: simulation diverges from physical system over time

**No tool does this today.** Drift detection across time with cryptographic proof is a category, not a feature. The infrastructure already exists (DRIFT-01, DT-CALIB-LOOP-01, verify-chain). It needs packaging and positioning.

---

## Do Not Build Until a Client Asks

| Feature | Why not now |
|---------|-----------|
| Multi-party verification | No demand signal. One verifier is sufficient for v1-v3. |
| Public blockchain anchoring | Adds complexity, zero client value over NIST Beacon. |
| Cross-org provenance network | Requires multiple orgs. Can't build alone. |
| Hosted SaaS / web UI dashboard | CLI-first is the right abstraction. Dashboard without users = waste. |
| OAuth / user accounts | Local-only REST API needs no auth. |

Building without signal = waste. Every feature here becomes obvious the moment a client asks for it. Until then, it's speculation.

---

*Written: 2026-04-04*
*Next review: after first paying client or Level 2 trigger*
