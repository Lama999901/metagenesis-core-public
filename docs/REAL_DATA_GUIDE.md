# Real Data Guide — Getting Your First Verification Bundle

> How to get a tamper-evident verification bundle for YOUR computational results.
> No GPU. No model access. No special environment. 60 seconds to verify.

---

## What you need

A CSV file with your results. That's it.

MetaGenesis Core reads your file, verifies your claim, packages everything
into a self-contained bundle with your dataset's SHA-256 fingerprint baked in.
Any third party runs one command to verify — offline, forever.

---

## Supported claim types (real data mode)

### ML_BENCH-01 — Classification accuracy

**Your file format:**
```
y_true,y_pred
1,1
0,0
1,0
...
```

- `y_true` — ground truth labels (integers: 0 or 1)
- `y_pred` — your model's predictions (integers: 0 or 1)
- Minimum 10 rows required

**What gets verified:**
`|actual_accuracy - claimed_accuracy| ≤ tolerance`

**Example claim:** "Our model achieves 94.2% accuracy on the held-out test set."

---

### DT-FEM-01 — FEM / simulation vs physical measurement

**Your file format:**
```
fem_value,measured_value,quantity
12.10,12.00,displacement_mm
85.20,84.00,temperature_celsius
...
```

- `fem_value` — output from your FEM solver (ANSYS, FEniCS, OpenFOAM, COMSOL, custom)
- `measured_value` — physical lab measurement for the same quantity
- `quantity` — name of the physical quantity (informational, optional)

**What gets verified:**
`max(|fem_value - measured_value| / |measured_value|) ≤ rel_err_threshold`

**Example claim:** "Our FEM solver matches lab measurements within 2% relative error."

---

## Step 1 — Request a Free Pilot

Send your CSV to: **yehor@metagenesis-core.dev**

Include:
- Your CSV file (attached)
- What you're claiming (e.g. "94.2% accuracy", "within 2% FEM error")
- Your tolerance (default: 0.02 for both claim types)

You'll receive your bundle within 48 hours.

---

## Step 2 — Verify your bundle

When you receive `bundle.zip`, run:

```bash
git clone https://github.com/Lama999901/metagenesis-core-public
cd metagenesis-core-public
pip install -r requirements.txt
python scripts/mg.py verify --pack /path/to/bundle.zip
```

Expected output:
```
manifest_ok: True
semantic_ok: True
VERIFY: PASS
```

That's it. Your result is now independently verifiable by anyone, offline.

---

## What the bundle contains

```
bundle/
  pack_manifest.json        — SHA-256 of every file + root_hash
  evidence_index.json       — maps claim IDs to artifact paths
  evidence/
    ML_BENCH-01/
      normal/
        run_artifact.json   — your result + dataset fingerprint
        ledger_snapshot.jsonl — audit ledger entry
```

Inside `run_artifact.json`:
```json
{
  "mtr_phase": "ML_BENCH-01",
  "inputs": {
    "dataset_relpath": "your_file.csv",
    "dataset": {
      "sha256": "abc123...",    ← SHA-256 of YOUR CSV
      "bytes": 4521,
      "rows": 1000
    },
    "claimed_accuracy": 0.942,
    "accuracy_tolerance": 0.02
  },
  "result": {
    "actual_accuracy": 0.944,
    "claimed_accuracy": 0.942,
    "absolute_error": 0.002,
    "tolerance": 0.02,
    "pass": true,
    ...
  }
}
```

The SHA-256 in the bundle is the cryptographic fingerprint of your exact CSV.
If anyone modifies the results → SHA-256 won't match → FAIL.

---

## Three verification layers

```
Layer 1 — Integrity
  SHA-256 of every file in the bundle + root_hash
  Catches: any file modified after packaging

Layer 2 — Semantic
  job_snapshot present, payload.kind correct, canary_mode consistent
  Catches: evidence stripped, hashes recomputed (integrity passes, semantic fails)
  PROOF: test_cert02 adversarial test running in CI

Layer 3 — Dataset fingerprint (real data mode)
  SHA-256 of your CSV baked into the bundle
  Catches: swapped dataset, modified predictions, wrong file
```

---

## Pricing

| Service | Price | What you get |
|---------|-------|--------------|
| Free Pilot | $0 | 1 bundle, your use case, no strings |
| Single Bundle | $299 | 1 bundle for any claim type |
| Pipeline Integration | $2,000–5,000 | Verification in your CI/CD pipeline |
| Ongoing | $500–2,000/month | Continuous certification |

**Payment:** bank transfer · crypto (BTC / ETH / USDC) · invoice
**Contact:** yehor@metagenesis-core.dev — response within 24 hours

---

## FAQ

**Q: Does Yehor see my model or training data?**
A: No. You only send predictions (y_true, y_pred). The model stays with you.

**Q: What if my CSV has different column names?**
A: Current version requires `y_true`/`y_pred` for ML and `fem_value`/`measured_value` for FEM.
   Contact us to add your specific format — new claim types can be added in days.

**Q: Can I verify the bundle on an air-gapped machine?**
A: Yes. The bundle is fully self-contained. No network, no API, no cloud.

**Q: What if I need a different claim type (regression, time series, pharma)?**
A: We have 20 claim types. Email us with your use case.

---

## Technical reference

- Protocol spec: `docs/PROTOCOL.md`
- Claim index: `reports/scientific_claim_index.md`
- Known limitations: `reports/known_faults.yaml`
- Security policy: `SECURITY.md`

---

*Real Data Guide v0.8 — 2026-03-30 — MetaGenesis Core — 20 claims, 601 tests*
