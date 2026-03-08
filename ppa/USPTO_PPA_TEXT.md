# MetaGenesis Core — USPTO Provisional Patent Application
# Inventor: Yehor Bazhynov
# Filing type: Pro Se Provisional Patent Application (PPA)
# Date prepared: 2026-03-04
# Authority: steward_audit.py PASS + test_cert02 PASS + 49 tests PASS

---

## TITLE OF INVENTION

Governance-Enforced Verification Infrastructure for Computational Scientific Claims
with Tamper-Evident Evidence Bundles and Dual-Mode Canary Execution

---

## BACKGROUND OF THE INVENTION

### Field of the Invention

The present invention relates to software systems for verification and governance
of computational scientific claims, and more particularly to systems that enforce
bidirectional coverage between claim registries and executable implementations,
produce tamper-evident evidence bundles with semantic verification layers,
enforce immutability of evidence anchors through policy-gate mechanisms,
and provide dual-mode canary execution pipelines for non-authoritative
health monitoring of computational verification infrastructure.

### Description of Related Art

Existing approaches to scientific reproducibility rely on one or more of the
following methods, each with significant limitations:

**Reproducible build systems** (e.g., Nix, Bazel, Docker) reproduce software
environments but do not verify that computational claims — such as numerical
thresholds, calibration results, or domain-specific invariants — are satisfied
by the execution. These systems guarantee that the same binary runs, not that
the binary produces scientifically valid results meeting specified criteria.

**Audit trail frameworks** (e.g., SOC 2, 21 CFR Part 11) define process-level
requirements for documentation and review but rely on human auditors and do not
provide machine-verifiable, code-enforced guarantees. Compliance is certified
periodically, not continuously enforced on every code change.

**Continuous integration and delivery systems** (e.g., GitHub Actions, Jenkins)
gate software merges on test passage but do not enforce that every executable
implementation corresponds to a registered scientific claim, or that every
registered claim has a corresponding executable implementation. These systems
test that code runs correctly, not that claims are complete and bidirectionally
covered.

**Cryptographic hash chains** (e.g., git, Certificate Transparency) provide
integrity guarantees over sequences of commits or certificates but do not
perform semantic verification of evidence content. An adversary with write
access can remove semantic content from an evidence artifact, recompute all
cryptographic hashes to restore integrity, and produce a bundle that passes
integrity checks while failing to contain the required scientific evidence.

**Prior art summary:** No existing system combines (1) governance-enforced
bidirectional claim coverage, (2) semantic tamper detection that survives
hash recomputation, (3) policy-gate-enforced immutability of evidence anchors
without key custody requirements, and (4) dual-mode canary execution that
isolates authority designation to metadata without duplicating computational
logic. The present invention addresses this gap.

---

## SUMMARY OF THE INVENTION

The present invention provides a governance-enforced verification infrastructure
for computational scientific claims. The system makes computational claims
tamper-evident, reproducible, and independently auditable by any third party
operating offline, without requiring trust in any single party.

The invention comprises four independently patentable innovations that operate
as a unified claim lifecycle system:

**First**, a Governance-Enforced Bidirectional Claim Coverage System enforces,
on every pull request through continuous integration, that every computational
claim registered in a claim registry has a corresponding executable
implementation in a runner dispatch table, and every executable implementation
in the runner dispatch table has a corresponding registered claim. This
bidirectional invariant is enforced automatically without human review, by
a steward auditor (scripts/steward_audit.py, function
_claim_coverage_bidirectional()) that performs static analysis of the runner
source code to extract dispatched job kinds without executing the runner.
No claim can be registered without an implementation; no implementation can
exist without a registered claim.

**Second**, a Tamper-Evident Evidence Bundle with Semantic Verification Layer
produces and verifies computational evidence bundles through two independent
verification layers. The integrity layer recomputes SHA-256 hashes and a
root_hash over all bundle files, detecting any file modification. The semantic
layer independently verifies that required keys (job_snapshot, trace_id,
canary_mode) are present in run artifacts and that domain-specific invariants
are satisfied. Critically, the semantic layer detects tampering that survives
the integrity layer: an adversary who removes semantic content from a run
artifact and recomputes all SHA-256 hashes and root_hash to restore integrity
will cause integrity verification to pass but semantic verification to fail,
producing a non-zero exit code and identifying the violated invariant.
This property is proven by an adversarial test
(tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py,
function test_semantic_negative_missing_job_snapshot_fails_verify()).

**Third**, a Policy-Gate-Enforced Immutable Evidence Anchor System enforces
immutability of computational evidence artifacts through a continuous
integration gate that blocks any pull request modifying files matching
locked path patterns, regardless of the nature of the change. The policy
configuration (scripts/mg_policy_gate_policy.json) defines locked paths
and an allowlist of permitted modification patterns, creating an asymmetric
access control structure where evidence artifacts, once locked, cannot be
modified through any pull request workflow, while development of new claims
and verification logic continues unrestricted. This immutability guarantee
does not require cryptographic key custody or external trusted timestamping
services.

**Fourth**, a Dual-Mode Canary Execution Pipeline executes computational
verification jobs in one of two authority modes through a single interface
(backend/progress/runner.py, function run_job(job_id, canary_mode=False)).
Normal mode produces authoritative evidence with ledger actor
"scheduler_v1" and action "job_completed". Canary mode produces
non-authoritative evidence with ledger actor "scheduler_v1_canary"
and action "job_completed_canary". Both modes execute identical
computational logic, isolating the authority distinction to metadata only.
A semantic verifier checks that the canary_mode flag in each run artifact
matches the expected authority designation for its bundle slot, rejecting
bundles where the authority designation does not match. This enables
continuous verification health monitoring without contaminating the
authoritative evidence record.

The four innovations together form a complete claim lifecycle system:
claims are registered with bidirectional coverage enforcement, executed
in normal and canary modes through the dual-mode pipeline, packaged
into tamper-evident bundles with semantic verification, and anchored
as immutable evidence through the policy gate mechanism.

---

## ABSTRACT

A governance-enforced verification infrastructure for computational scientific
claims comprises four innovations. First, a steward auditor enforces
bidirectional claim coverage by automatically verifying, on every pull request,
that every registered claim has a corresponding executable implementation and
every executable implementation has a registered claim, using static analysis
without executing the runner. Second, a tamper-evident evidence bundle system
produces submission packs with two independent verification layers: an integrity
layer using SHA-256 hashes and a root hash, and a semantic layer that detects
tampering surviving hash recomputation by verifying required keys and
domain-specific invariants in run artifacts. Third, a policy-gate enforcer
blocks any pull request modifying locked evidence artifact paths, providing
immutability guarantees without cryptographic key custody or external
timestamping. Fourth, a dual-mode canary pipeline executes identical
computational logic in normal (authoritative) or canary (non-authoritative)
mode, isolating authority designation to ledger metadata, enabling continuous
health monitoring without contaminating the authoritative evidence record.
All four innovations are proven by passing adversarial tests and continuous
integration gates on each code change.

---

## BRIEF DESCRIPTION OF THE DRAWINGS

**Figure 1** — Proof Loop Architecture: Job Run → Runner (normal/canary mode)
→ Run Artifact + Ledger Snapshot → Evidence Index → Submission Pack
→ Integrity Verification (SHA-256 + root_hash) → Semantic Verification
→ PASS or FAIL with specific reason.

**Figure 2** — Bidirectional Claim Coverage Invariant: Claim Registry
↔ Runner Dispatch Table, enforced by steward auditor on every CI run.

**Figure 3** — Semantic Tamper Detection: Adversary removes job_snapshot,
recomputes manifest (integrity: PASS), semantic check detects missing key
(semantic: FAIL, exit non-zero).

**Figure 4** — Dual-Mode Execution: Single run_job() interface →
normal mode (scheduler_v1, job_completed, canary_mode=false) OR
canary mode (scheduler_v1_canary, job_completed_canary, canary_mode=true),
identical _execute_job_logic() for both.

---

## DETAILED DESCRIPTION OF THE PREFERRED EMBODIMENT

### 1. System Overview

MetaGenesis Core is a verification protocol layer, not a simulation platform
or AI coordination system. Its purpose is to make computational scientific
claims tamper-evident, reproducible, and independently auditable offline.

The system operates on five active scientific claims at filing
(MTR-1, MTR-2, MTR-3, SYSID-01, DATA-PIPE-01); additional claims
(DRIFT-01, ML_BENCH-01) were added post-filing and will be included
in the non-provisional application. These claims are representative
examples; the governance infrastructure is domain-agnostic.
They span materials science (Young's modulus calibration, thermal
conductivity, multilayer thermal contact), systems identification (ARX model
calibration), data pipeline quality certification, and calibration drift
monitoring.

### 2. Bidirectional Claim Coverage (Claim 1)

The claim registry (reports/scientific_claim_index.md) stores for each
claim identifier a job_kind string and verification thresholds.

The runner dispatch table (backend/progress/runner.py,
function _execute_job_logic()) maps job_kind strings to deterministic
calibration functions. Job kinds are registered by importing JOB_KIND
constants from domain modules:
- mtr1_youngs_modulus_calibration (backend/progress/mtr1_calibration.py)
- mtr2_thermal_paste_conductivity_calibration (backend/progress/mtr2_thermal_conductivity.py)
- mtr3_thermal_multilayer_contact_calibration (backend/progress/mtr3_thermal_multilayer.py)
- sysid1_arx_calibration (backend/progress/sysid1_arx_calibration.py)
- datapipe1_quality_certificate (backend/progress/datapipe1_quality_certificate.py)
- drift_calibration_monitor (backend/progress/drift_monitor.py)

The steward auditor (scripts/steward_audit.py) extracts runner job kinds
by static analysis of import statements matching the pattern
"from backend.progress.<module> import JOB_KIND", resolves each JOB_KIND
constant from the imported module, and compares the resulting set against
job kinds extracted from the claim registry. Any asymmetry fails the audit.

The canonical state record (reports/canonical_state.md) stores the
authoritative list of active claim identifiers. The auditor additionally
enforces that this list equals the claim registry claim list.

The CI gate (.github/workflows/mg_policy_gate.yml) executes the steward
auditor on every pull request, blocking merge on any violation.

### 3. Tamper-Evident Bundle with Semantic Verification (Claim 2)

Each job execution produces two artifacts:
- Run artifact JSON (reports/progress_runs/): contains job_snapshot,
  trace_id, canary_mode flag, and domain result under job_snapshot.result
- Ledger snapshot JSONL (reports/ledger_snapshots/): append-only record
  keyed by trace_id

The submission pack builder (scripts/steward_submission_pack.py) assembles
these artifacts into a pack with:
- pack_manifest.json: SHA-256 hash and byte count per file, plus root_hash
  computed as SHA-256 over the UTF-8 encoding of sorted "relpath:sha256" lines
- evidence_index.json: maps each claim_id to normal and canary bundle paths

Verification (scripts/mg.py, functions _verify_pack() and _verify_semantic())
performs two independent checks:
- Integrity: recompute all SHA-256 hashes and root_hash; fail on any mismatch
- Semantic: parse each run artifact and verify presence of trace_id,
  job_snapshot, canary_mode; verify job_snapshot.result contains mtr_phase;
  verify payload.kind matches evidence_index job_kind; verify canary_mode
  flag matches bundle slot; optionally verify dataset SHA-256 format and
  uncertainty envelope validity

The adversarial proof (test_cert02): remove job_snapshot from a run artifact,
recompute all SHA-256 hashes and root_hash so integrity passes → semantic
verification fails with non-zero exit and identifies missing key.

### 4. Policy-Gate Immutable Evidence Anchors (Claim 3)

The policy configuration (scripts/mg_policy_gate_policy.json) defines:
- locked_paths: glob patterns for permanently sealed files; currently
  empty (no paths locked in public repo).
  The enforcement mechanism is active and validated by the policy gate
  test suite; the locked_paths list is populated when specific evidence
  artifacts are designated as sealed in a deployment context, providing
  immutability guarantees without key custody or external timestamping.
- allow_globs: glob patterns for permitted modifications including
  scripts/**, tests/**, backend/progress/**, reports/*.md,
  reports/*.yaml, ppa/**, docs/**, *.md, *.json

The policy gate enforcer (scripts/mg_policy_gate.py) runs on every pull
request, computing changed file paths via git diff and rejecting any path
matching a locked_path pattern regardless of change nature, while requiring
every changed path to match at least one allow_glob pattern.

This creates an asymmetric access control structure: evidence artifacts
once locked are immutable through the PR workflow, while new claim
development continues unrestricted. No key custody or external
timestamping service is required.

### 5. Dual-Mode Canary Pipeline (Claim 4)

The single execution interface run_job(job_id, canary_mode=False) in
backend/progress/runner.py accepts a boolean parameter that controls
authority designation without affecting computational logic.

Normal mode (canary_mode=False):
- Ledger actor: "scheduler_v1"
- Ledger action: "job_completed"
- Run artifact canary_mode field: false
- Evidence authority: AUTHORITATIVE

Canary mode (canary_mode=True):
- Ledger actor: "scheduler_v1_canary"
- Ledger action: "job_completed_canary"
- Run artifact canary_mode field: true
- Evidence authority: NON-AUTHORITATIVE

Both modes call the same _execute_job_logic() function. The semantic
verifier checks that canary_mode in the run artifact matches the expected
mode for the bundle slot (normal slot expects false, canary slot expects true).

This enables continuous health monitoring: canary runs detect infrastructure
failures without contaminating the authoritative evidence record used for
claim verification.

---

## CLAIMS (reference to CLAIMS_DRAFT.md)

See ppa/CLAIMS_DRAFT.md for the full set of 4 independent claims and
8 dependent claims with complete claim language.

---

## DEPOSIT OF BIOLOGICAL MATERIAL

Not applicable.

---

## SEQUENCE LISTING

Not applicable.

---

*Prepared by: Yehor Bazhynov (Inventor, Pro Se)*
*Based on: verified codebase, steward_audit PASS 2026-03-03,*
*test_cert02 adversarial tamper PASS, 49 tests PASS*
*No invented features. Every section traceable to passing tests.*
