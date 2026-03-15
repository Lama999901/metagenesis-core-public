# Verify computational claims in 5 minutes — no network required

This demo runs the existing MTR-1 pipeline on an open dataset, generates evidence (normal + canary), builds a tamper-evident pack, and verifies it. All steps are offline.

---

## 3-command quickstart

From the **repository root** (the directory that contains `demos/`):

```bash
cd demos/open_data_demo_01
python run_demo.py
```

If you cloned the repo and have Python available, that is all. No API keys, no network.

---

## What PASS means

- The open dataset in `data/` was loaded.
- The existing runner produced **normal** and **canary** evidence for MTR-1 (Young’s modulus calibration).
- The submission pack was built with that evidence.
- Verification passed: the pack manifest is consistent (file hashes match) and the evidence bundles satisfy the semantic checks (trace_id, job_snapshot, canary_mode, payload.kind, etc.).

So: the computational claim (MTR-1) was run on real open data, and the resulting pack is **tamper-evident**: any change to files or hashes is detected by verify.

---

## What FAIL means

- **Dataset not found** — `data/strain_stress_open.csv` is missing or path is wrong; run from repo root or fix the path.
- **Pack build failed** — Evidence dir or pack output path problem; check that you ran from repo root.
- **Pack verify failed** — Either the manifest hashes do not match the files (integrity), or the evidence bundles do not meet the required shape (semantic). The script prints the reason; you can also open `VERIFY_REPORT.json` and read the `errors` array.

---

## What this proves

- You can **reproduce** the claim (MTR-1) on an open dataset with a single command.
- The pack is **tamper-evident** across three independent layers:
  - **Layer 1 (SHA-256 integrity):** any file change breaks the manifest root_hash.
  - **Layer 2 (semantic):** stripping job_snapshot and recomputing all hashes still fails — semantic check catches it.
  - **Layer 3 (Step Chain):** execution_trace + trace_root_hash commit to the exact computation sequence. Changing any input breaks trace_root_hash.
- The run_artifact.json contains `execution_trace` (4 steps) and `trace_root_hash` — inspect it with any JSON viewer.

---

## What this does NOT prove

- It does **not** prove that the underlying model or algorithm is correct; only that the pipeline ran and produced evidence in the expected format.
- It does **not** prove that the dataset is representative of any real-world population; it is a minimal open sample for demo use.
- It does **not** guarantee that no vulnerability exists in the verification logic; it shows that the current checks behave as designed for this run.
