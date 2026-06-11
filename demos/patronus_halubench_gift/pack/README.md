# Patronus HaluBench — MetaGenesis gift bundle

A verifiable, offline gift bundle that seals a deterministic 50-sample slice of
the public **PatronusAI/HaluBench** dataset with a SHA-256 and a verifiable
manifest. Built as an outreach artifact: a prospect can independently confirm,
offline, that this exact dataset snapshot has not been modified.

## 3-command offline quickstart

```bash
# 1. Build: assemble the pack from the sealed 50-sample slice
python demos/patronus_halubench_gift/build_gift_bundle.py

# 2. Verify: confirm the bundle matches its manifest (integrity), offline
python scripts/mg.py verify --pack demos/patronus_halubench_gift/pack

# 3. Inspect: read the sealed file list and root_hash
python -c "import json;print(json.dumps(json.load(open('demos/patronus_halubench_gift/pack/pack_manifest.json'))['files'],indent=2))"
```

All three steps are fully offline: the build reuses the cached real snapshot in
`data/halubench_slice.json` when it exists (it is committed to this repo). Only
a fresh fetch — when no cached slice exists — requires network access to the
HuggingFace datasets-server (stdlib `urllib`, no extra dependencies). If
HuggingFace is unreachable in that case, the build script prints a clear blocker
line and exits non-zero **without writing a fabricated slice**.

## The sealed slice

- **Dataset:** `PatronusAI/HaluBench` (public), split `test`, rows 0-49.
- **Sealed snapshot SHA-256:**
  `15ae5edbb633bf27856f6fd8281fc15ba53b08271403d77eb982d2ab29b41654`
  (`data/halubench_slice.json`)
- **Composition disclosure:** the slice is the *first 50 rows* of the split,
  chosen for determinism, not representativeness. The split is not shuffled, so
  all 50 rows happen to come from the DROP subset and all carry label `FAIL`.
  A representative sample would require shuffling, which would sacrifice the
  trivially reproducible "rows 0-49" definition.
- **Proof-of-time:** the pack carries a temporal commitment
  (`pack/temporal_commitment.json`) binding its `root_hash` to a NIST
  Randomness Beacon pulse — evidence the bundle existed no later than that
  pulse's timestamp (anti-backdating, Layer 5).

## What this proves

- The exact 50-sample dataset snapshot is sealed with a SHA-256 and a verifiable
  `pack_manifest.json`.
- The bundle is tamper-evident: any change to a sealed file breaks the manifest
  integrity check via the cryptographic hash chain.
- The snapshot is independently verifiable offline with a single command — no
  trust in the bundle's creator is required to confirm the files match the
  manifest.

## What this does NOT prove

- It does **not** prove Patronus's published 87.4% Lynx-70B figure is correct —
  that number is REFERENCED from docs.patronus.ai, not recomputed here.
- It does **not** prove the dataset is contamination-free.
- It does **not** audit Patronus's inference pipeline. There is no inference in
  this bundle and no `y_pred` is fabricated — it seals a dataset snapshot only.
- Integrity is not authenticity: this bundle is unsigned, so it carries no
  provenance proof. Run `mg sign verify` separately for authenticity. See
  `docs/SECURITY_MODEL.md` for the integrity-vs-authenticity distinction.

The referenced Lynx-70B figure and its public source are recorded in
`data/referenced_figure.md`.
