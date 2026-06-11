#!/usr/bin/env python3
"""Build a verifiable Patronus HaluBench gift bundle.

This seals a deterministic 50-sample slice of the PUBLIC PatronusAI/HaluBench
dataset into a tamper-evident, independently verifiable MetaGenesis pack.

Honest scope: this bundle seals a DATASET SNAPSHOT only. There is no inference
here and no y_pred is fabricated. The published Lynx-70B figure is REFERENCED
from docs.patronus.ai, not recomputed. See README.md for the full
proves / does-NOT-prove block.

Network: the slice is fetched over the HuggingFace datasets-server rows endpoint
using only the standard library (urllib). If HuggingFace is unreachable, this
script prints a clear blocker line and exits non-zero WITHOUT writing a
fabricated slice.
"""

import hashlib
import io
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# Windows hygiene: UTF-8 stdout wrapper so non-ASCII never crashes on cp1252.
sys.stdout = io.TextIOWrapper(
    sys.stdout.buffer, encoding="utf-8", errors="replace"
)

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MG_SCRIPT = REPO_ROOT / "scripts" / "mg.py"

DATA_DIR = HERE / "data"
PACK_DIR = HERE / "pack"

DATASET = "PatronusAI/HaluBench"
CONFIG = "default"
SPLIT = "test"
SLICE_LEN = 50
ROWS_URL = (
    "https://datasets-server.huggingface.co/rows"
    f"?dataset={DATASET}&config={CONFIG}&split={SPLIT}&offset=0&length={SLICE_LEN}"
)

# Patronus's PUBLISHED Lynx-70B figure — REFERENCED, NOT recomputed here.
REFERENCED_FIGURE = "87.4"
REFERENCED_SOURCE = "https://docs.patronus.ai"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_slice() -> list:
    """Fetch the first SLICE_LEN rows of the fixed split. Deterministic.

    Returns the list of row objects. Raises on any network failure so the
    caller can emit a blocker and exit non-zero without fabricating data.
    """
    req = urllib.request.Request(
        ROWS_URL, headers={"User-Agent": "metagenesis-gift-bundle/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    rows = payload.get("rows", [])
    if not rows:
        raise RuntimeError("HuggingFace returned no rows for the requested slice")
    # Deterministic: first SLICE_LEN rows of the fixed split, in returned order.
    return rows[:SLICE_LEN]


def write_referenced_figure() -> Path:
    note = DATA_DIR / "referenced_figure.md"
    note.write_text(
        "# Referenced figure (NOT recomputed by MetaGenesis)\n\n"
        f"Patronus's published Lynx-70B overall figure: {REFERENCED_FIGURE}% "
        "on HaluBench.\n\n"
        f"Public source: {REFERENCED_SOURCE}\n\n"
        "MetaGenesis Core did NOT recompute this number. This bundle seals a\n"
        "50-sample dataset snapshot only; the figure above is cited as published\n"
        "reference context, not a verified result.\n",
        encoding="utf-8",
    )
    return note


def build_pack(slice_path: Path) -> Path:
    """Assemble a manifest-only pack with the 4-key schema and return PACK_DIR."""
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    # Files that go into the pack (copied by relpath into the pack dir).
    sources = {
        "README.md": HERE / "README.md",
        "halubench_slice.json": slice_path,
        "referenced_figure.md": DATA_DIR / "referenced_figure.md",
    }

    files_entries = []
    for relpath, src in sorted(sources.items()):
        dst = PACK_DIR / relpath
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        files_entries.append(
            {
                "relpath": relpath,
                "sha256": _sha256_file(dst),
                "bytes": dst.stat().st_size,
            }
        )

    # root_hash recipe: sha256( "\n".join(sorted("relpath:sha256")) )
    lines = "\n".join(
        f"{e['relpath']}:{e['sha256']}"
        for e in sorted(files_entries, key=lambda x: x["relpath"])
    )
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "pack_version": "1",
        "protocol_version": 1,
        "files": files_entries,
        "root_hash": root_hash,
    }
    (PACK_DIR / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return PACK_DIR


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fetch the deterministic slice (network step).
    try:
        rows = fetch_slice()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, RuntimeError) as e:
        print(
            "BLOCKER: HuggingFace datasets-server unreachable — "
            "no dataset slice written, no data fabricated. "
            f"Reason: {e}"
        )
        return 1

    # 2. Save the slice deterministically (sort_keys for a stable hash).
    slice_path = DATA_DIR / "halubench_slice.json"
    slice_doc = {
        "dataset": DATASET,
        "config": CONFIG,
        "split": SPLIT,
        "offset": 0,
        "length": len(rows),
        "rows": rows,
    }
    slice_path.write_text(
        json.dumps(slice_doc, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    slice_sha = _sha256_file(slice_path)
    print(f"Wrote {len(rows)}-sample slice: {slice_path}")
    print(f"halubench_slice.json SHA-256: {slice_sha}")

    # 3. Referenced (not recomputed) figure note.
    write_referenced_figure()

    # 4. Assemble pack and verify.
    pack_dir = build_pack(slice_path)
    print(f"Built pack: {pack_dir}")

    r = subprocess.run(
        [sys.executable, str(MG_SCRIPT), "verify", "--pack", str(pack_dir)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    print(r.stdout.strip())
    if r.returncode != 0:
        print("BLOCKER: mg verify did not PASS on the built pack.")
        print(r.stderr.strip())
        return 1
    print("Gift bundle verified PASS.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
