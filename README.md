# MetaGenesis Core🌐 **Site:** https://metagenesis-core.dev

[![Steward Audit Gate](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)
[![Protocol](https://img.shields.io/badge/Protocol-MVP%20v0.1-blueviolet.svg)](docs/PROTOCOL.md)

**Open verification protocol for computational claims.**

Any computational result — ML model accuracy, calibration output, data
pipeline certificate — packaged into a self-contained evidence bundle
that any third party verifies offline with one command.

```bash
python scripts/mg.py verify --pack /path/to/bundle
# PASS  or  FAIL: <specific reason>
```

No GPU. No access to your code or environment. No trust required.

---

## The problem

AI systems and computational pipelines produce claims every day:

> *"Our model achieves 94.3% accuracy."*
> *"This simulation result converges within 1% error."*
> *"The data pipeline passed all quality checks."*

There is no standard way to verify these claims independently. A reviewer,
regulator, or client must either re-run the full pipeline — which requires
your environment, data, and compute — or trust the reported number.

MetaGenesis Core solves this by turning any computational result into a
verifiable, tamper-evident evidence bundle.

---

## Why SHA-256 alone is not enough

Most systems stop at file hashes. MetaGenesis Core adds a semantic
verification layer on top.

**The bypass attack:**
1. Remove evidence content from a bundle (e.g. strip `job_snapshot`)
2. Recompute all SHA-256 hashes to restore integrity
3. Submit a bundle that passes standard integrity checks

```
Standard integrity check:   PASS  (hashes match — attack succeeds)
MetaGenesis semantic check: FAIL  (job_snapshot missing — attack caught)
```

This attack is proven and caught by an adversarial test that ships
with the repository.

Evidence: `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`
`::test_semantic_negative_missing_job_snapshot_fails_verify`

---

## Try it in 5 minutes

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt
python demos/open_data_demo_01/run_demo.py
```

Expected output:
```
PASS
PASS
```

No API keys. No network calls. Works on any machine with Python 3.11+.

---

## How it works

```
Your computation runs
        ↓
runner.run_job()  →  run_artifact.json + ledger_snapshot.jsonl
        ↓
Evidence bundle  (scripts/mg.py pack build)
  ├── pack_manifest.json   ← SHA-256 integrity layer
  ├── evidence_index.json  ← claim mapping
  └── evidence/<CLAIM>/
        ├── normal/run_artifact.json
        └── canary/run_artifact.json
        ↓
mg.py verify
  ├── integrity check  (SHA-256 + root_hash)
  └── semantic check   (job_snapshot present, kind matches, canary flag correct)
        ↓
     PASS or FAIL with specific reason
```

Full architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Active verified claims

| Claim | Domain | V&V threshold |
|-------|--------|--------------|
| MTR-1 | Young's modulus calibration | relative_error ≤ 0.01 |
| MTR-2 | Thermal paste conductivity | relative_error ≤ 0.02 |
| MTR-3 | Multilayer thermal contact | rel_err_k ≤ 0.03 |
| SYSID-01 | ARX model calibration | rel_err_a/b ≤ 0.03 |
| DATA-PIPE-01 | Data pipeline quality | schema + range pass |
| DRIFT-01 | Calibration drift monitor | threshold 5% |
| **ML_BENCH-01** | **ML model accuracy certificate** | **\|actual − claimed\| ≤ 0.02** |

All claims: [reports/scientific_claim_index.md](reports/scientific_claim_index.md)

---

## ML accuracy verification (new)

Any ML model that claims a specific accuracy can have that claim certified:

```bash
# Certify a model that claims 90% accuracy
python -m pytest tests/ml/test_mlbench01_accuracy_certificate.py -v
```

Two modes:

**Synthetic mode** — deterministic, reproducible, no data required:
```python
# Same seed → same result, always. On any machine.
result = run_certificate(seed=42, claimed_accuracy=0.90)
# result["result"]["pass"] → True or False
```

**Real data mode** — certify actual model predictions:
```python
# Your CSV with y_true / y_pred columns.
# Dataset is SHA-256 fingerprinted. Bundle is tamper-evident.
result = run_certificate(dataset_relpath="data/my_model_predictions.csv",
                         claimed_accuracy=0.94)
```

A reviewer runs `mg.py verify --pack bundle.zip` and gets PASS or FAIL.
No model access. No environment. No trust required.

---

## Calibration anchors and drift detection

Verified results become trusted anchor points. DRIFT-01 compares any
new computation against a verified baseline.

```
MTR-1 verified:  E = 70 GPa  →  trusted anchor
New computation: E = 76 GPa  →  drift = 8.6%  →  correction_required: True
```

Without verified anchors, you cannot know what your simulation is
drifting from.

---

## Governance

Every registered claim must have a corresponding implementation.
Every implementation must have a registered claim.
Enforced automatically on every pull request — not by human review.

```bash
python scripts/steward_audit.py
```

```
STEWARD AUDIT: PASS
  canonical_state claims: ['MTR-1', 'MTR-2', 'MTR-3', 'SYSID-01',
                           'DATA-PIPE-01', 'DRIFT-01', 'ML_BENCH-01']
  claim_index claims:     ['MTR-1', 'MTR-2', 'MTR-3', 'DATA-PIPE-01',
                           'SYSID-01', 'DRIFT-01', 'ML_BENCH-01']
  canonical sync: PASS
```

Any asymmetry — a claim without implementation, or an implementation
without a registered claim — blocks the merge.

---

## Run the test suite

```bash
python -m pytest tests/steward tests/materials tests/ml -q
```

Adversarial tamper detection:

```bash
python -m pytest tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py -v
# PASS — includes test_semantic_negative_missing_job_snapshot
```

---

## Who this is for

**ML teams** publishing benchmark results or handing off model performance
reports to clients, auditors, or regulators who need independent verification
without access to the model or training data.

**Researchers** publishing computational results who want reviewers to verify
specific claims without re-running the full pipeline.

**Regulated industries** (pharma, finance, carbon markets) where computational
results must be independently auditable for compliance.

**Any team** handing off a computational result to a third party who needs
tamper-evident proof the result is what it claims to be.

Use case details: [docs/USE_CASES.md](docs/USE_CASES.md)

---

## Protocol

MetaGenesis Core implements the MetaGenesis Verification Protocol (MVP) v0.1
— an open standard for packaging computational claims into independently
verifiable evidence bundles.

Protocol specification: [docs/PROTOCOL.md](docs/PROTOCOL.md)

---

## Roadmap

Planned domains: drug discovery (IC50 claims), carbon credit model outputs,
financial risk model validation, geospatial simulation results.

[docs/ROADMAP.md](docs/ROADMAP.md)

---

## Adding a new claim

See [docs/HOW_TO_ADD_CLAIM.md](docs/HOW_TO_ADD_CLAIM.md) for the
step-by-step claim lifecycle. Every claim requires:
implementation → runner dispatch → claim index entry → canonical state → tests.

---

## Patent

USPTO Provisional Patent Application filed: 2026-03-05
Application #: 63/996,819 — Inventor: Yehor Bazhynov

4 patentable innovations: bidirectional claim coverage, semantic tamper
detection, policy-gate immutable anchors, dual-mode canary pipeline.

---

## Commercial

MIT licensed. Free to use.

If you need a verification bundle built for your results, pipeline
integration, or ongoing verification infrastructure — see [COMMERCIAL.md](COMMERCIAL.md).

**Free pilot:** Send your computational result and get a verification
bundle at no charge. No strings attached.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT — see [LICENSE](LICENSE)

---

*steward_audit PASS · test_cert02 adversarial tamper PASS · no invented features*
