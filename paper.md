---
title: 'MetaGenesis Core: A Governance-Enforced Verification Protocol for Computational Scientific Claims'
tags:
  - Python
  - reproducibility
  - verification
  - scientific computing
  - machine learning
  - computational science
  - evidence bundles
  - provenance
authors:
  - name: Yehor Bazhynov
    orcid: 0009-0006-6292-4892
    affiliation: 1
affiliations:
  - name: Independent Researcher, Langley, BC, Canada
    index: 1
date: 18 March 2026
bibliography: paper.bib
---

# Summary

MetaGenesis Core is an open-source verification protocol that packages
computational results into tamper-evident, independently auditable evidence
bundles. Any third party can verify a bundle offline, without access to the
original model, data, or environment, in under 60 seconds:

```bash
python scripts/mg.py verify --pack bundle.zip
# → PASS  or  FAIL: <specific reason and layer>
```

The protocol implements five independent verification layers, each proven
by dedicated adversarial tests:

- **Layer 1 — SHA-256 integrity**: detects any file modified after bundle generation
- **Layer 2 — Semantic verification**: detects evidence stripped and hashes recomputed
  (Layer 1 passes; Layer 2 catches it)
- **Layer 3 — Step Chain**: detects computation inputs changed or steps reordered
  (Layers 1 and 2 pass; Layer 3 catches it)
- **Layer 4 — Bundle Signing**: detects unauthorized bundle creator via HMAC-SHA256
  or Ed25519 asymmetric signatures (Layers 1–3 pass; Layer 4 catches it)
- **Layer 5 — Temporal Commitment**: detects backdated bundles via NIST Randomness
  Beacon 2.0 pre-commitment scheme (Layers 1–4 pass; Layer 5 catches it)

For physical domains, individual claim verification extends to a
**Cross-Claim Cryptographic Chain** — a verifiable provenance path from
a physically measured constant (E = 70 GPa for aluminum, independently
measured in thousands of laboratories worldwide) through calibration, FEM
simulation, and drift monitoring. Each link is cryptographically committed;
tampering any link invalidates all downstream hashes.

The protocol ships with 20 active verification claims across 8 domains
(materials science, ML/AI, system identification, data pipelines, digital
twin, pharma/biotech, and financial risk), 1753 adversarial tests, and
governance enforcement that prevents any registered claim from existing
without a corresponding implementation — and vice versa.

# Statement of Need

## The verification gap

A Nature survey of 1,576 researchers found that over 70% had failed to
reproduce another scientist's results [@baker2016reproducibility]. Kapoor
and Narayanan documented data leakage silently inflating accuracy in 294
ML papers across 17 scientific disciplines [@kapoor2023leakage]. The
"Leaderboard Illusion" paper (NeurIPS 2025) documented systematic benchmark
gaming in major AI evaluations [@raji2025illusion].

The core problem is not malfeasance — it is the absence of a standard for
what "independently verifiable" means for a computational result. Publishing
code makes reproduction *possible* for those with the right environment.
It does not provide proof that a specific number was produced by a specific
computation.

## Why existing tools do not solve this

Experiment tracking systems (MLflow [@chen2020mlflow], Weights & Biases,
DVC) record provenance metadata but do not produce machine-verifiable
evidence. A reviewer must trust that the logged metadata was not modified.
Reproducible build systems (Nix, Docker) guarantee that the same binary
runs but do not verify that the binary produces scientifically valid results
meeting specified criteria. Cryptographic hash chains (git, Certificate
Transparency) provide integrity over file sequences but do not perform
semantic verification of evidence content.

No existing open tool answers the question a reviewer, regulator, or
commercial partner needs answered:

> *Can I verify this specific computational claim independently — without
> access to the original model, data, or environment — and get a binary
> PASS or FAIL with a specific reason?*

## The bypass attack

The inadequacy of SHA-256 alone is not theoretical. An adversary who knows
only integrity verification is used can remove all evidence from a bundle,
recompute every SHA-256 hash to restore integrity, and submit a bundle
that passes Layer 1 while containing no scientific content. This attack
is implemented and proven in `tests/steward/test_cert02_*::test_semantic_negative_missing_job_snapshot_fails_verify`.
Layer 2 (semantic verification) catches it. Layer 1 does not.

A second class of attacks — changing computation inputs while keeping
bundle structure intact — passes both Layer 1 and Layer 2 but is caught
by Layer 3 (Step Chain). This is implemented and proven in
`tests/steward/test_cert03_step_chain_verify.py`.

The full adversarial proof suite (CERT-05) documents five distinct attack
scenarios, each caught by a different layer, with a composite test
explicitly proving all three integrity layers are necessary [@bazhynov2026cert05].
Two additional layers — bundle signing (Layer 4, Innovation #6) and temporal
commitment (Layer 5, Innovation #7) — extend the protocol to answer WHO
created a bundle and WHEN it was signed. Layer 4 supports dual-algorithm
signing: HMAC-SHA256 for shared-secret workflows and Ed25519 for third-party
auditor verification with asymmetric keys. Layer 5 uses a NIST Randomness
Beacon 2.0 pre-commitment scheme: `SHA-256(root_hash)` is computed before
the beacon value is fetched, preventing backdating. The 5-layer independence
proof (`tests/steward/test_cert_5layer_independence.py`) demonstrates that
each layer catches attacks the other four miss.

# Technical Design

## Evidence bundle

A bundle is a directory (or ZIP archive) containing:

- `pack_manifest.json`: SHA-256 hash of every file plus a root hash computed
  as SHA-256 over sorted `relpath:sha256` lines
- `evidence_index.json`: mapping from claim identifiers to evidence bundle slots
- `evidence/<CLAIM_ID>/normal/run_artifact.json`: authoritative execution result
- `evidence/<CLAIM_ID>/canary/run_artifact.json`: non-authoritative health check

The `run_artifact.json` contains the execution result, inputs summary,
an `execution_trace` (4-step cryptographic hash chain), and a
`trace_root_hash` committing to the entire execution sequence.

## Step Chain verification

Every claim execution produces a 4-step cryptographic hash chain:

```
step 1: init_params    → h₁ = SHA256(step1_data ‖ "genesis")
step 2: compute        → h₂ = SHA256(step2_data ‖ h₁)
step 3: metrics        → h₃ = SHA256(step3_data ‖ h₂)
step 4: threshold_check → trace_root_hash = SHA256(step4_data ‖ h₃)
```

`trace_root_hash` is a cryptographic commitment to the entire execution
sequence. Changing any input, skipping any step, or reordering steps
invalidates the hash. This is the same principle as git commits — each
commit hashes its parent — applied to computation sequences. No network,
no consensus, no external dependencies. Implemented in the Python standard
library.

## Physical Anchor Principle

A distinction is maintained between two properties:

- **Tamper-evident provenance** ("was the bundle modified?"): applies to
  all 20 claims
- **Physical anchor traceability** ("does the number agree with physical
  reality?"): applies only to claims anchored to independently measured
  physical constants

MTR-1 verifies that a Young's modulus calibration agrees with
E = 70 GPa for aluminum — a value measured independently in thousands of
laboratories worldwide, not a threshold chosen by the protocol.
This carries fundamentally different epistemic weight than a claim that
a number falls within an arbitrarily chosen range.

The Cross-Claim Chain extends this to end-to-end physical traceability:

```
E = 70 GPa (physical reality)
    ↓  MTR-1: rel_err ≤ 1% vs. physical constant → PASS
    ↓  anchor_hash baked into DT-FEM-01 Step 1
DT-FEM-01: FEM output vs. reference → rel_err ≤ 2% → PASS
    ↓  anchor_hash baked into DRIFT-01 Step 1
DRIFT-01: drift vs. anchor ≤ 5% → PASS
```

`DRIFT-01.trace_root_hash` cryptographically commits to the entire chain
from physical measurement to current simulation state. Verified with one
command: `python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/`.

## Governance invariant

A steward auditor (`scripts/steward_audit.py`) enforces on every pull
request that:

1. Every registered claim has a corresponding runner dispatch (no
   undocumented implementations)
2. Every runner dispatch has a registered claim (no unimplemented claims)
3. The canonical state record is identical to the claim registry

This bidirectional invariant is enforced by static analysis of the runner
source code — without executing it — so no undocumented implementation
can exist in the codebase. Enforcement is continuous: on every merge,
not periodically.

## Reproducibility as a cryptographic property

A key contribution of this work is formalizing computational reproducibility
as a cryptographic property rather than a qualitative assessment. Two
independent runs of the same computation with the same parameters produce
the same `trace_root_hash`. This is not "similar results" — it is
cryptographic identity. Hash equality constitutes reproducibility proof;
hash inequality indicates a discrepancy, and the step-level trace identifies
which step diverged.

This property is proven across all 20 claims in
`tests/steward/test_cert08_reproducibility.py`, including parameter
sensitivity (different parameters → different hash, making selective
seed reporting detectable) and cross-claim chain determinism.

# Active Claims and Domains

| Claim | Domain | Threshold | Physical Anchor |
|-------|--------|-----------|-----------------|
| MTR-1 | Materials — Young's Modulus | `rel_err ≤ 0.01` | E = 70 GPa ⚓ |
| MTR-2 | Materials — Thermal Conductivity | `rel_err ≤ 0.02` | Physical constant ⚓ |
| MTR-3 | Materials — Multilayer Contact | `rel_err_k ≤ 0.03` | Physical constant ⚓ |
| SYSID-01 | System Identification | `rel_err ≤ 0.03` | — |
| DATA-PIPE-01 | Data Pipelines | schema + range PASS | — |
| DRIFT-01 | Drift Monitoring | `drift ≤ 5.0%` | MTR-1 ⚓ |
| ML\_BENCH-01 | ML Classification | `\|Δacc\| ≤ 0.02` | — |
| DT-FEM-01 | Digital Twin / FEM | `rel_err ≤ 0.02` | MTR-1 ⚓ |
| ML\_BENCH-02 | ML Regression | `\|ΔRMSE\| ≤ 0.02` | — |
| ML\_BENCH-03 | ML Time-Series | `\|ΔMAPE\| ≤ 0.02` | — |
| PHARMA-01 | Pharma ADMET | `\|Δprop\| ≤ tol` | — |
| FINRISK-01 | Finance VaR | `\|ΔVaR\| ≤ tol` | — |
| DT-SENSOR-01 | IoT Sensor Integrity | schema + range + temporal | — |
| DT-CALIB-LOOP-01 | Calibration Convergence | drift decreasing | DRIFT-01 ⚓ |
| AGENT-DRIFT-01 | Agent Quality — Self-Verification | `composite_drift <= 20%` | — |
| MTR-4 | Materials — Titanium Modulus | `rel_err ≤ 0.01` | E = 114 GPa ⚓ |
| MTR-5 | Materials — Steel Modulus | `rel_err ≤ 0.01` | E = 193 GPa ⚓ |
| MTR-6 | Materials — Copper Conductivity | `rel_err ≤ 0.02` | k = 401 W/(m·K) ⚓ |
| PHYS-01 | Fundamental Physics — Boltzmann | `rel_err ≤ 1e-9` | kB = 1.380649e-23 J/K ⚓ |
| PHYS-02 | Fundamental Physics — Avogadro | `rel_err ≤ 1e-8` | NA = 6.02214076e23 mol⁻¹ ⚓ |

Physical anchor traceability (⚓) is scoped to claims with known physical
constants. For ML and financial claims, the protocol provides tamper-evident
provenance only. This distinction is formalized in `reports/known_faults.yaml :: SCOPE_001`.

# Agent Evolution System

MetaGenesis Core ships with an embedded agent governance system that enforces
documentation consistency automatically. Anyone who clones the repository
receives an 18-check health monitoring suite (`scripts/agent_evolution.py`),
post-phase validation hooks, and a cumulative learning system
(`scripts/agent_learn.py`) that records recurring patterns and auto-fix hints
across sessions.

The system includes:

- **Agent Evolution Runner** — 16 automated checks covering steward audit,
  test suite, deep verification, stale documentation, manifest consistency,
  forbidden terms, coverage gaps, CLAUDE.md freshness, watchlist coverage,
  and branch synchronization.
- **Agent Learning** — session-to-session memory that surfaces recurring
  issues and stores auto-fix hints, so the same mistake is never debugged
  twice.
- **Watchlist Scanner** (`scripts/auto_watchlist_scan.py`) — detects
  documentation files that exist outside the validation watchlist, preventing
  silent documentation drift.

This is itself a demonstration of the protocol's domain-agnostic
applicability: the same governance-enforcement principle that prevents
undocumented computational claims from existing also prevents undocumented
documentation drift. The recursive structure — agents extend the protocol,
the protocol verifies the agents — provides a concrete example of
self-referential verification that scales with project complexity.

# Known Limitations

MetaGenesis Core is tamper-evident, not tamper-proof. A sufficiently
sophisticated adversary with full codebase access and key material could
construct a passing bundle. The protocol is designed to make such an attack
orders of magnitude more difficult than simply reporting a false number —
not to make it theoretically impossible. Known limitations are documented
in `reports/known_faults.yaml`.

The protocol verifies that a computation was run as specified. It does not
verify that the algorithm is correct, that training data is unbiased, or
that experimental design is free from p-hacking. These are complementary
concerns addressed by other work [@gundersen2021fundamental].

# Related Work

lm-eval [@biderman2024lessons] provides reproducible orchestration of
language model evaluations. MetaGenesis Core addresses the complementary
problem: verifiable evidence that a specific evaluation was run with
specific data at a specific time, without requiring access to the evaluation
environment.

The ML Reproducibility Checklist [@pineau2021improving], now mandated at
NeurIPS, ICML, and ICLR, defines requirements for reproducible research.
MetaGenesis Core automates compliance with the computational verification
component of this checklist into an executable, machine-verifiable artifact.

DVC [@kuprieiev2023dvc] and MLflow [@chen2020mlflow] track experiment
provenance. MetaGenesis Core produces independently verifiable evidence
from that provenance — a verifier does not need access to the tracking
system to confirm the claim.

# State of the Field

Several tools address aspects of computational reproducibility. MLflow
[@chen2020mlflow] tracks experiments and model versions. DVC [@kuprieiev2023dvc] versions
datasets and pipelines. lm-eval [@biderman2024lessons] standardizes language model
benchmarks. Weights & Biases provides collaborative experiment dashboards.

Container-based approaches complement these tracking tools. ReproZip
[@chirigati2016reprozip] captures system-level dependencies into a
self-contained package that can be replayed on any machine. Binder
[@jupyter2018binder] wraps repositories into executable cloud environments,
enabling one-click reproduction of notebooks. These tools solve the
environment problem — ensuring the same code runs in the same context —
but do not produce cryptographic evidence that a specific computation
met a specific verification threshold.

These tools excel at tracking — recording what was run, when, and with
which parameters. However, none produces a self-contained, machine-verifiable
evidence bundle that a third party can audit offline without access to the
original tracking infrastructure. A researcher receiving an MLflow run ID
must trust that the tracking server has not been modified; a DVC-managed
pipeline requires access to the original remote storage.

MetaGenesis Core fills this gap. It packages computational results into
cryptographically committed bundles where each verification layer catches
attacks the other four miss. The result is auditable evidence, not auditable
logs — a bundle either passes five independent verification checks or it
does not, regardless of who runs the verifier or where.

# Research Impact Statement

MetaGenesis Core is designed for anyone who publishes computational claims
and needs verifiable proof that those claims were produced honestly:

- **ML researchers** facing reproducibility requirements from venues
  adopting stricter artifact evaluation (NeurIPS, ICML, AAAI).
- **Pharmaceutical teams** navigating FDA guidance on AI/ML in drug
  development, where audit trails for computational predictions are
  increasingly expected.
- **Financial institutions** subject to Basel III model risk management
  requirements, where independent validation of risk model outputs is
  mandatory.
- **Digital twin operators** who must demonstrate that simulation outputs
  trace back to calibrated physical measurements.
- **Any researcher** who wants to move beyond "trust me, I ran the code"
  toward "here is the cryptographic proof that I ran the code and got
  these results."

# AI Usage Disclosure

Claude (Anthropic) was used as the primary development tool throughout
this project: architecture decisions, code implementation, patent
application drafting, and documentation. All AI-generated outputs were
verified by the author through the project's own adversarial test suite
(1753 tests), steward audit, and 13-test deep verification script.
Quality was ensured by governance-enforced bidirectional coverage — every
claim must have tests and every test must correspond to a claim — and
5-layer tamper-evident verification where each layer catches attacks the
other four miss. The recursive self-verification structure means the
protocol that verifies computational claims also verifies the agent that
helped build it.

# Acknowledgements

This work was developed independently, without institutional funding.
The reproducibility crisis documented by Baker [-@baker2016reproducibility],
Kapoor and Narayanan [-@kapoor2023leakage], and Pineau et al.
[-@pineau2021improving] provided the precise problem statement.
The protocol was built to solve it.

# References
