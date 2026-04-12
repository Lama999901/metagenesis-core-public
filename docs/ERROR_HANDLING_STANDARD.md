# MetaGenesis Core -- Error Handling Standard (v1.0.0-rc1)

---

## Step Chain Pattern (4-step cryptographic hash chain)

Every claim implementation must produce a 4-step execution trace.
Each step hashes its data chained to the previous step's hash.

```python
def _hash_step(step_name, step_data, prev_hash):
    import hashlib, json as _j
    content = _j.dumps({"step": step_name, "data": step_data,
                        "prev_hash": prev_hash},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

**Steps (fixed order, always 4):**

| Step | Name | Data |
|------|------|------|
| 1 | init_params | Input parameters, seed, thresholds, dataset fingerprint |
| 2 | compute | Raw computation results |
| 3 | metrics | Derived metrics (rel_err, accuracy, RMSE, etc.) |
| 4 | threshold_check | Pass/fail decision and threshold used |

The final step's hash becomes `trace_root_hash`.

---

## Return Structure (all 20 claims)

```python
return {
    "mtr_phase": "CLAIM-ID",       # e.g. "MTR-1", "ML_BENCH-01"
    "inputs": {                     # what went in
        "seed": 42,
        "dataset": {"sha256": "...", "relpath": "..."},
        "anchor_hash": "..."        # only for anchored claims
    },
    "result": {                     # what came out
        "pass": True,
        "relative_error": 0.005,    # claim-specific metric
        "threshold": 0.01
    },
    "execution_trace": [            # 4-step hash chain
        {"step": 1, "name": "init_params", "hash": "<sha256>"},
        {"step": 2, "name": "compute", "hash": "<sha256>"},
        {"step": 3, "name": "metrics", "hash": "<sha256>"},
        {"step": 4, "name": "threshold_check", "hash": "<sha256>",
         "output": {"pass": True}}
    ],
    "trace_root_hash": "<sha256>"   # == execution_trace[-1]["hash"]
}
```

---

## Error Propagation Through Verification Layers

**Layer 1 (Integrity):** If any file's SHA-256 does not match pack_manifest.json,
verification fails immediately with `"SHA256 mismatch: <relpath>"`.

**Layer 2 (Semantic):** Checks structural validity of evidence artifacts.
Failures include: missing `job_snapshot`, wrong `payload.kind`, incorrect
`canary_mode`, missing `mtr_phase`. Each returns a specific error string.

**Layer 3 (Step Chain):** Validates execution_trace structure:
- Must have exactly 4 steps numbered [1, 2, 3, 4]
- Each step hash must be valid 64-char lowercase hex
- `trace_root_hash` must equal `execution_trace[-1]["hash"]`
- Mismatch produces: `"Step Chain broken -- trace_root_hash does not match"`

**Layer 4 (Signing):** Signature verification failure returns unauthorized
creator error. A stolen key still cannot bypass Layers 1-3 content checks.

**Layer 5 (Temporal):** Beacon commitment mismatch indicates backdating.
Degrades gracefully to "skip" when NIST Beacon is unavailable.

---

## Error Handling in Claim Implementations

- `ValueError` for invalid inputs (too few samples, missing dataset, bad parameters)
- No exceptions for computation failures -- failures are encoded in the result:
  `"pass": False` with the specific metric that exceeded the threshold
- Dataset loading errors raise `ValueError` with descriptive message
- All errors are deterministic: same inputs always produce the same error

---

## Verification Exit Codes

| Code | Meaning |
|------|---------|
| 0 | PASS -- all layers verified |
| 1 | FAIL -- specific layer failed (reason in stdout) |

The verifier never silently swallows errors. Every FAIL includes which
layer failed and why.

---

*Error Handling Standard v1.0.0-rc1 -- MetaGenesis Core*
