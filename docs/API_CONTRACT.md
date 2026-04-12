# MetaGenesis Core -- API Contract (v1.0.0-rc1)

CLI entry point: `python scripts/mg.py <group> <command> [options]`

---

## Commands

### verify --pack PATH

Verify a bundle with all 5 layers. Primary command for third-party auditors.

```bash
python scripts/mg.py verify --pack bundle_dir/
python scripts/mg.py verify --pack bundle_dir/ --json report.json
python scripts/mg.py verify --pack bundle_dir/ --receipt receipt.json
```

**Exit codes:** 0 = PASS, 1 = FAIL
**Output:** "PASS" or failure reason to stdout.
**Options:**
- `--json / -j PATH` -- write machine-readable JSON report
- `--receipt PATH` -- write verification receipt (proof verification was performed)

### verify-chain PACK1 PACK2 [PACK3 ...]

Verify a Cross-Claim Chain. Bundles must be ordered upstream to downstream.

```bash
python scripts/mg.py verify-chain bundle_mtr1/ bundle_dtfem/ bundle_drift/
```

**Exit codes:** 0 = CHAIN PASS, 1 = CHAIN FAIL
**Options:** `--json / -j PATH` -- write chain verification report

### pack build --output PATH

Build a submission pack (evidence bundle).

```bash
python scripts/mg.py pack build --output dist/bundle/
python scripts/mg.py pack build --output dist/bundle/ --include-evidence
```

**Options:**
- `--output / -o PATH` (required) -- output directory
- `--index PATH` -- custom evidence index
- `--include-evidence` -- include full evidence artifacts
- `--source-reports-dir PATH` -- custom reports directory

### sign keygen --out PATH

Generate a signing key for Layer 4 bundle signing.

```bash
python scripts/mg.py sign keygen --out keys/signing_key.json
python scripts/mg.py sign keygen --out keys/signing_key.json --type hmac
```

**Options:** `--type / -t [ed25519|hmac]` (default: ed25519)

### sign bundle --pack PATH --key PATH

Sign a bundle with a signing key.

### sign verify --pack PATH [--key PATH | --fingerprint FP]

Verify a bundle signature. Use `--key` for HMAC, `--fingerprint` for Ed25519.

---

## Bundle Structure (pack_manifest.json)

```json
{
  "protocol_version": 1,
  "root_hash": "<sha256 over all file hashes>",
  "files": [
    {
      "relpath": "evidence/MTR-1/normal/run_artifact.json",
      "sha256": "<sha256 of file bytes>"
    }
  ]
}
```

**Root hash computation:** SHA-256 of concatenated `"relpath:sha256\n"` lines, sorted by relpath.

**Minimum protocol version:** 1. Bundles with lower version are rejected (rollback protection).

---

## run_artifact.json (per-claim evidence)

```json
{
  "trace_id": "<uuid>",
  "canary_mode": false,
  "job_snapshot": {
    "payload": { "kind": "<job_kind>" },
    "result": {
      "mtr_phase": "<CLAIM_ID>",
      "inputs": { },
      "result": { "pass": true },
      "execution_trace": [
        {"step": 1, "name": "init_params", "hash": "<sha256>"},
        {"step": 2, "name": "compute", "hash": "<sha256>"},
        {"step": 3, "name": "metrics", "hash": "<sha256>"},
        {"step": 4, "name": "threshold_check", "hash": "<sha256>"}
      ],
      "trace_root_hash": "<sha256 of step 4>"
    }
  }
}
```

---

## Verification Layers (checked by verify)

| Layer | What | Catches |
|-------|------|---------|
| 1 | SHA-256 integrity | File modified after bundle generation |
| 2 | Semantic | Evidence stripped and hashes recomputed |
| 3 | Step Chain | Inputs changed, steps reordered or skipped |
| 4 | Bundle Signing | Unauthorized bundle creator |
| 5 | Temporal Commitment | Backdated bundle (NIST Beacon) |

---

## JSON Report Structure (--json output)

```json
{
  "version": "v1",
  "pack_root_hash": "<sha256>",
  "manifest_ok": true,
  "semantic_ok": true,
  "temporal_ok": true,
  "checks": [
    {"name": "manifest_exists", "status": "pass"},
    {"name": "manifest_valid", "status": "pass"},
    {"name": "manifest_structure", "status": "pass"},
    {"name": "protocol_version", "status": "pass"},
    {"name": "manifest_integrity", "status": "pass"},
    {"name": "semantic_evidence", "status": "pass"},
    {"name": "temporal_commitment", "status": "pass|skip"}
  ],
  "errors": []
}
```

**Status values:** "pass", "fail", "skip" (layer not available or not applicable).

---

*API Contract v1.0.0-rc1 -- MetaGenesis Core*
