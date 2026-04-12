# MetaGenesis Core SDK

Programmatic access to the MetaGenesis verification protocol.
Zero dependencies. Works offline. Python 3.11+.

## Quick Start

```python
from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
result = client.verify("path/to/bundle")
print(result.passed)  # True or False
```

## Installation

No installation needed. Clone the repo and import:

```bash
git clone https://github.com/Lama999901/metagenesis-core-public.git
cd metagenesis-core-public
python -c "from sdk.metagenesis import MetaGenesisClient; print('OK')"
```

## Full API Reference

### `MetaGenesisClient(repo_root=None)`

Create a client instance. Defaults to the repository root.

```python
client = MetaGenesisClient()
# or with explicit path:
client = MetaGenesisClient(repo_root="/path/to/metagenesis-core-public")
```

### `client.verify(bundle_path) -> VerificationResult`

Run all 5 verification layers on a bundle:

| Layer | What it catches |
|-------|-----------------|
| 1 -- SHA-256 Integrity | File modified after packing |
| 2 -- Semantic | Evidence stripped + hashes recomputed |
| 3 -- Step Chain | Inputs changed, steps reordered |
| 4 -- Bundle Signature | Unauthorized bundle creator |
| 5 -- Temporal Commitment | Backdated bundle (NIST Beacon) |

```python
result = client.verify("bundle/")
result.passed        # bool
result.layers        # {"integrity": True, "semantic": True, ...}
result.reason        # "PASS" or failure description
result.bundle_path   # str
result.timestamp     # ISO 8601 UTC
result.claim_id      # e.g. "MTR-1" (if present)
result.trace_root_hash  # SHA-256 hash of computation chain
```

### `client.pack(job_result, output_dir) -> str`

Pack a job result into a verifiable bundle:

```python
job_result = {
    "mtr_phase": "ML_BENCH-01",
    "inputs": {"dataset": {"name": "test.csv", "sha256": "abc..."}},
    "result": {"actual_accuracy": 0.94, "pass": True},
    "execution_trace": [...],  # 4-step hash chain
    "trace_root_hash": "def...",
}
bundle_path = client.pack(job_result, "output/my_bundle")
```

### `client.sign(bundle_path, key_path) -> str`

Sign a bundle with Ed25519 or HMAC-SHA256:

```python
fingerprint = client.sign("bundle/", "signing_key.json")
```

Generate a key first:
```bash
python scripts/mg.py sign keygen --out signing_key.json --type ed25519
```

### `client.verify_chain(bundle_a, bundle_b) -> VerificationResult`

Verify a cross-claim chain between two bundles:

```python
result = client.verify_chain("mtr1_bundle/", "dtfem_bundle/")
# Checks: dtfem.anchor_hash == mtr1.trace_root_hash
```

### `client.receipt(bundle_path) -> str`

Generate a human-readable verification receipt:

```python
text = client.receipt("bundle/")
print(text)
# --------------------------------------------------
# METAGENESIS CORE -- VERIFICATION RECEIPT
# --------------------------------------------------
# Verified:  2026-04-11 16:00:00 UTC
# Bundle:    bundle
# Claim:     MTR-1
# Anchor:    E = 70 GPa (aluminum, NIST measured)
# ...
```

### `VerificationResult`

Dataclass returned by `verify()` and `verify_chain()`:

| Field | Type | Description |
|-------|------|-------------|
| `passed` | `bool` | All layers passed |
| `layers` | `dict` | Layer name -> True/False |
| `reason` | `str` | "PASS" or failure reason |
| `bundle_path` | `str` | Path to verified bundle |
| `timestamp` | `str` | ISO 8601 UTC timestamp |
| `claim_id` | `str\|None` | Claim identifier |
| `trace_root_hash` | `str\|None` | Computation chain hash |

## GitHub Action Usage

Any repository can verify MetaGenesis bundles in CI/CD:

```yaml
- uses: Lama999901/metagenesis-core-public/.github/actions/verify-bundle@main
  with:
    bundle_path: ./results/bundle
```

Full example:

```yaml
name: Verify Results
on: [push]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run computation
        run: python compute.py --output results/bundle

      - name: Verify bundle
        id: verify
        uses: Lama999901/metagenesis-core-public/.github/actions/verify-bundle@main
        with:
          bundle_path: ./results/bundle

      - name: Use results
        run: |
          echo "Passed: ${{ steps.verify.outputs.passed }}"
          echo "Layers: ${{ steps.verify.outputs.layers_json }}"
```

### Action Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `bundle_path` | Yes | — | Path to bundle directory |
| `fail_on_fail` | No | `true` | Fail step on verification failure |
| `python_version` | No | `3.11` | Python version to use |

### Action Outputs

| Output | Description |
|--------|-------------|
| `passed` | `true` or `false` |
| `reason` | Result reason string |
| `layers_json` | JSON object with per-layer results |
| `receipt` | Human-readable verification receipt |

## Integration Patterns

### CI/CD Pipeline

```yaml
# Verify every commit's computation results
- name: Verify
  uses: Lama999901/metagenesis-core-public/.github/actions/verify-bundle@main
  with:
    bundle_path: ./output/bundle
    fail_on_fail: true
```

### Jupyter Notebook

```python
from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()

# After your computation...
bundle = client.pack(job_result, "output/bundle")
result = client.verify(bundle)

# Display in notebook
print(f"Verification: {'PASS' if result.passed else 'FAIL'}")
for layer, ok in result.layers.items():
    print(f"  {layer}: {'PASS' if ok else 'FAIL'}")
```

### FastAPI Endpoint

```python
from fastapi import FastAPI
from sdk.metagenesis import MetaGenesisClient

app = FastAPI()
client = MetaGenesisClient()

@app.post("/verify")
async def verify_bundle(bundle_path: str):
    result = client.verify(bundle_path)
    return {
        "passed": result.passed,
        "layers": result.layers,
        "reason": result.reason,
    }
```

### CLI Wrapper

```bash
# Direct verification
python scripts/mg_verify_standalone.py bundle/ --receipt

# SDK-based
python -c "
from sdk.metagenesis import MetaGenesisClient
r = MetaGenesisClient().verify('bundle/')
print('PASS' if r.passed else 'FAIL')
"
```

## Comparison with Alternatives

| Feature | MetaGenesis | checksums | Sigstore | Blockchain |
|---------|-------------|-----------|----------|------------|
| Offline verification | Yes | Yes | No | No |
| Zero dependencies | Yes | Yes | No | No |
| Computation proof | 5 layers | 1 layer | 1 layer | 1 layer |
| Step chain | Yes | No | No | No |
| Physical anchors | Yes | No | No | No |
| Temporal proof | NIST Beacon | No | Yes | Yes |
| Cross-claim chains | Yes | No | No | No |
| Cost | Free / $299 | Free | Free | Gas fees |

---

Protocol: MetaGenesis Verification Protocol (MVP) v1.0
PPA: USPTO #63/996,819 | Inventor: Yehor Bazhynov
https://metagenesis-core.dev
