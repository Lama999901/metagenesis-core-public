# MetaGenesis Core -- Client Quick Start

## What you get

Your computational result -- ML accuracy, calibration output, risk model,
regulatory submission -- becomes independently verifiable by any third party.

One command. No model access required. No environment required. 60 seconds.

The verification bundle is **tamper-evident** across 5 independent layers:
SHA-256 integrity, semantic verification, cryptographic step chain,
bundle signing (HMAC-SHA256 / Ed25519), and temporal commitment (NIST Beacon).

## Try it now

```bash
python scripts/mg_client.py --demo
```

This runs a complete ML benchmark verification: generates data, computes
a claim, packages it into a signed bundle, and verifies all 5 layers.

Expected output: **PASS** for each layer.

## Your data

Prepare a JSON file with your parameters. Example for ML:

```json
{
  "claimed_accuracy": 0.94,
  "accuracy_tolerance": 0.02,
  "n_samples": 500,
  "seed": 42
}
```

Then run:

```bash
python scripts/mg_client.py --domain ml --data your_results.json
```

Supported domains:

| Domain | Claim | What it verifies |
|--------|-------|------------------|
| `ml` | ML_BENCH-01 | Classification accuracy within tolerance |
| `pharma` | PHARMA-01 | ADMET prediction (FDA 21 CFR Part 11) |
| `finance` | FINRISK-01 | Value at Risk (Basel III) |
| `materials` | MTR-1 | Young's modulus calibration (E=70GPa Al) |
| `digital_twin` | DT-FEM-01 | FEM displacement vs physical reference |

### Verify an existing bundle

```bash
python scripts/mg_client.py --verify path/to/bundle/
```

## Contact

Free pilot: yehor@metagenesis-core.dev | $299 per bundle
