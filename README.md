# MetaGenesis Core

[![Steward Audit Gate](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml/badge.svg)](https://github.com/Lama999901/metagenesis-core-public/actions/workflows/total_audit_guard.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Patent Pending](https://img.shields.io/badge/Patent-Pending%20%2363%2F996%2C819-orange.svg)](ppa/README_PPA.md)

**Verification protocol layer for computational scientific claims.**

Any computational result — calibration, model output, data certificate —
can be packaged into a self-contained evidence bundle that a third party
verifies offline with one command.

```bash
python scripts/mg.py verify --pack /path/to/bundle
# PASS  or  FAIL: <specific reason>
```

No GPU. No access to your code or environment. No trust required.

---

## The problem

When a paper or team reports a computational result, there is no standard
way for a reviewer or collaborator to check it independently without:

- Re-running the full pipeline (requires your environment, data, compute)
- Trusting the reported number (no independent check possible)

MetaGenesis Core solves this by turning any result into a verifiable bundle.

---

## Why SHA-256 alone is not enough

Most systems stop at file hashes. MetaGenesis Core adds a semantic
verification layer on top.

An adversary can:
1. Remove evidence content from a bundle
2. Recompute all SHA-256 hashes to restore integrity
3. Submit a bundle that passes standard integrity checks

```
Standard integrity check:   PASS  (hashes match)
MetaGenesis semantic check: FAIL  (job_snapshot missing)
```

This attack is proven and caught by an adversarial test that ships
with the repository.

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
Evidence bundle (scripts/mg.py pack build)
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

## Calibration anchors and drift detection

Verified results become trusted anchor points. DRIFT-01 compares any
new computation against a verified baseline.

```
MTR-1 verified:  E = 70 GPa  →  trusted anchor
New computation: E = 76 GPa  →  drift = 8.6%  →  correction_required: True
```

Threshold: 5%. Without verified anchors, you cannot know what your
simulation is drifting from.

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

All claims: [reports/scientific_claim_index.md](reports/scientific_claim_index.md)

---

## Governance

Every registered claim must have a corresponding implementation.
Every implementation must have a registered claim.
This is enforced automatically on every pull request — not by human review.

```bash
python scripts/steward_audit.py
```

```
STEWARD AUDIT: PASS
  canonical_state claims: ['MTR-1', 'MTR-2', 'MTR-3', 'SYSID-01', 'DATA-PIPE-01', 'DRIFT-01']
  claim_index claims:     ['MTR-1', 'MTR-2', 'MTR-3', 'DATA-PIPE-01', 'SYSID-01', 'DRIFT-01']
  canonical sync: PASS
```

Any asymmetry — a claim without implementation, or an implementation
without a registered claim — blocks the merge.

---

## Run the test suite

```bash
python -m pytest tests/steward tests/materials -q
# 49 passed
```

Adversarial tamper detection test:

```bash
python -m pytest tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py -v
# 2 passed — includes test_semantic_negative_missing_job_snapshot
```

---

## Who this is for

**Researchers** publishing computational results who want reviewers to
verify specific claims without re-running the full pipeline.

**Teams** running ML models or calibration pipelines who need to detect
when new results drift from a verified baseline.

**Anyone** handing off a computational result to a third party who needs
proof the result is what it claims to be.

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

**Free pilot:** send your computational result and I will build
a verification bundle at no charge.

Contact: yehorbazhynov@gmail.com

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT — see [LICENSE](LICENSE)

---

*steward_audit PASS · test_cert02 adversarial tamper PASS · no invented features*
