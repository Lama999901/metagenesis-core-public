# MetaGenesis Core

Computational results are hard to verify independently. Re-running requires
the original environment. Trusting reported numbers means reproducibility
is never actually checked. Reviewers accept results they cannot audit.

MetaGenesis Core is a verification protocol layer that solves this.
It packages any computational result into a self-contained evidence bundle
that a third party can verify offline — one command, no GPU, no access
to your code or environment.

## The core problem it solves

When a paper reports "our method reduces error by 33%", there is currently
no standard way for a reviewer or collaborator to check that number
independently without:

- Re-running the full pipeline (requires your environment, data, compute)
- Trusting the reported result (no independent check possible)

MetaGenesis Core produces a verification bundle that anyone can run:

```bash
python scripts/mg.py verify --pack /path/to/bundle
```

Output: `PASS` or `FAIL` with a specific reason.

## Why integrity checks alone are not enough

Most systems stop at SHA-256 file hashes. MetaGenesis Core adds a
semantic verification layer on top.

An adversary can:
1. Remove evidence content from a bundle
2. Recompute all SHA-256 hashes to restore integrity
3. Submit a bundle that passes integrity checks

Standard integrity verification: **PASS** (hashes match)
MetaGenesis semantic verification: **FAIL** (job_snapshot missing)

This is proven by an adversarial test that ships with the repo.

## Calibration anchors and drift detection

Verified results become trusted anchor points. DRIFT-01 compares any
new computation against a verified baseline — drift beyond threshold
signals that something has changed and correction may be required.

Without verified anchors, you cannot know what your simulation is
drifting from.

```
Verified result (MTR-1: E = 70 GPa) → trusted anchor
New computation: E = 76 GPa → drift = 8.6% → correction_required: True
```

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

No API keys. No network. No account. Works on any machine with Python 3.11+.

## Active verified claims

| Claim | Domain | What it verifies |
|-------|--------|-----------------|
| MTR-1 | Young's modulus calibration | Elastic modulus from stress-strain data |
| MTR-2 | Thermal paste conductivity | Thermal conductivity calibration |
| MTR-3 | Multilayer thermal contact | Two-parameter thermal contact model |
| SYSID-01 | ARX model calibration | System identification from time-series |
| DATA-PIPE-01 | Data pipeline quality | Dataset schema and range certificate |
| DRIFT-01 | Calibration drift monitor | Deviation from verified anchor baseline |

## Governance: what makes this trustworthy

Every claim in the registry must have a corresponding implementation.
Every implementation must have a corresponding registered claim.
This is enforced automatically on every pull request — not by human review.

```bash
python scripts/steward_audit.py
```

```
STEWARD AUDIT: PASS
  canonical_state claims: ['MTR-1', 'MTR-2', 'MTR-3', 'SYSID-01', 'DATA-PIPE-01', 'DRIFT-01']
  claim_index claims: ['MTR-1', 'MTR-2', 'MTR-3', 'DATA-PIPE-01', 'SYSID-01', 'DRIFT-01']
  canonical sync: PASS
```

Any asymmetry — a claim without implementation, or implementation without
a registered claim — fails the audit and blocks the merge.

## Run the full test suite

```bash
python -m pytest tests/steward tests/materials -q
# 49 passed
```

Includes adversarial tamper detection test:

```bash
python -m pytest tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py -v
# 2 passed — including test_semantic_negative_missing_job_snapshot
```

## Who this is for

**Researchers** publishing computational results who want reviewers to
be able to independently verify specific claims without re-running
the full pipeline.

**Teams** running ML models or calibration pipelines who need to know
when new results drift from a verified baseline.

**Anyone** who needs to hand off a computational result to a third party
with proof that the result is what it claims to be.

## Patent status

USPTO Provisional Patent Application filed: 2026-03-05
Application #: 63/996,819
Inventor: Yehor Bazhynov

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT

---

*No invented features. Every claim traceable to passing tests.*
*steward_audit PASS. test_cert02 adversarial tamper PASS.*
