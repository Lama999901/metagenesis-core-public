# Patronus HaluBench — MetaGenesis gift bundle

A verifiable, offline gift bundle that seals a deterministic 50-sample slice of
the public **PatronusAI/HaluBench** dataset with a SHA-256 and a verifiable
manifest. Built as an outreach artifact: a prospect can independently confirm,
offline, that this exact dataset snapshot has not been modified.

## 3-command offline quickstart

```bash
# 1. Build: fetch the deterministic 50-sample slice and assemble the pack
python demos/patronus_halubench_gift/build_gift_bundle.py

# 2. Verify: confirm the bundle matches its manifest (integrity), offline
python scripts/mg.py verify --pack demos/patronus_halubench_gift/pack

# 3. Inspect: read the sealed file list and root_hash
python -c "import json;print(json.dumps(json.load(open('demos/patronus_halubench_gift/pack/pack_manifest.json'))['files'],indent=2))"
```

Step 1 requires network access to the HuggingFace datasets-server (stdlib
`urllib`, no extra dependencies). If HuggingFace is unreachable, the build script
prints a clear blocker line and exits non-zero **without writing a fabricated
slice**. Steps 2 and 3 are fully offline once the pack exists.

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
