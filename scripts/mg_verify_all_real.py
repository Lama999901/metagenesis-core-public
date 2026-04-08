#!/usr/bin/env python3
"""
mg_verify_all_real.py -- Verify all 20 active claims with real external data.

Runs each claim through mg_claim_builder.build_claim(), producing signed bundles
in proof_library/bundles/. Idempotent: skips claims already verified in index.json.

Usage:
    python scripts/mg_verify_all_real.py          # run all 20
    python scripts/mg_verify_all_real.py --dry-run # show what would run
"""

import argparse
import io
import json
import sys
import time
from pathlib import Path

# Ensure repo root on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Force UTF-8 on Windows to avoid cp1252 encoding errors
# Guard under __name__ == "__main__" to avoid breaking pytest's capture mechanism
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from scripts.mg_claim_builder import build_claim, _load_index  # noqa: E402

# ---------------------------------------------------------------------------
# Registry of all 20 active claims
# ---------------------------------------------------------------------------

CLAIM_REGISTRY = [
    {
        "claim_id": "MTR-1",
        "label": "MTR-1_materials",
        "domain": "materials",
        "input_path": "proof_library/real_data/materials/mtr1_aluminum_stress_strain.csv",
    },
    {
        "claim_id": "MTR-2",
        "label": "MTR-2_materials",
        "domain": "materials",
        "input_path": "proof_library/real_data/materials/mtr2_thermal_paste.json",
    },
    {
        "claim_id": "MTR-3",
        "label": "MTR-3_materials",
        "domain": "materials",
        "input_path": "proof_library/real_data/materials/mtr3_multilayer_thermal.json",
    },
    {
        "claim_id": "MTR-4",
        "label": "MTR-4_materials",
        "domain": "materials",
        "input_path": "proof_library/real_data/materials/mtr4_titanium_stress_strain.csv",
    },
    {
        "claim_id": "MTR-5",
        "label": "MTR-5_materials",
        "domain": "materials",
        "input_path": "proof_library/real_data/materials/mtr5_steel_stress_strain.csv",
    },
    {
        "claim_id": "MTR-6",
        "label": "MTR-6_materials",
        "domain": "materials",
        "input_path": "proof_library/real_data/materials/mtr6_copper_thermal.json",
    },
    {
        "claim_id": "PHYS-01",
        "label": "PHYS-01_physics",
        "domain": "physics",
        "input_path": "proof_library/real_data/physics/phys01_boltzmann_input.json",
    },
    {
        "claim_id": "PHYS-02",
        "label": "PHYS-02_physics",
        "domain": "physics",
        "input_path": "proof_library/real_data/physics/phys02_avogadro_input.json",
    },
    {
        "claim_id": "ML_BENCH-01",
        "label": "ML_BENCH-01_ml",
        "domain": "ml",
        "input_path": "proof_library/real_data/ml/mlbench1_predictions.csv",
    },
    {
        "claim_id": "ML_BENCH-02",
        "label": "ML_BENCH-02_ml",
        "domain": "ml",
        "input_path": "proof_library/real_data/ml/mlbench2_regression.csv",
    },
    {
        "claim_id": "ML_BENCH-03",
        "label": "ML_BENCH-03_ml",
        "domain": "ml",
        "input_path": "proof_library/real_data/ml/mlbench3_timeseries.csv",
    },
    {
        "claim_id": "SYSID-01",
        "label": "SYSID-01_systems",
        "domain": "systems",
        "input_path": "proof_library/real_data/systems/sysid1_arx_data.json",
    },
    {
        "claim_id": "DATA-PIPE-01",
        "label": "DATA-PIPE-01_systems",
        "domain": "systems",
        "input_path": "proof_library/real_data/systems/datapipe1_dataset.csv",
    },
    {
        "claim_id": "DRIFT-01",
        "label": "DRIFT-01_systems",
        "domain": "systems",
        "input_path": "proof_library/real_data/systems/drift01_monitor.json",
    },
    {
        "claim_id": "DT-FEM-01",
        "label": "DT-FEM-01_digital_twin",
        "domain": "digital_twin",
        "input_path": "proof_library/real_data/digital_twin/dtfem1_displacement.csv",
    },
    {
        "claim_id": "DT-SENSOR-01",
        "label": "DT-SENSOR-01_digital_twin",
        "domain": "digital_twin",
        "input_path": "proof_library/real_data/digital_twin/dtsensor1_temperature.json",
    },
    {
        "claim_id": "DT-CALIB-LOOP-01",
        "label": "DT-CALIB-LOOP-01_digital_twin",
        "domain": "digital_twin",
        "input_path": "proof_library/real_data/digital_twin/dtcalib1_convergence.json",
    },
    {
        "claim_id": "PHARMA-01",
        "label": "PHARMA-01_pharma",
        "domain": "pharma",
        "input_path": "proof_library/real_data/pharma/pharma1_admet.json",
    },
    {
        "claim_id": "FINRISK-01",
        "label": "FINRISK-01_finance",
        "domain": "finance",
        "input_path": "proof_library/real_data/finance/finrisk1_returns.json",
    },
    {
        "claim_id": "AGENT-DRIFT-01",
        "label": "AGENT-DRIFT-01_agent",
        "domain": "agent",
        "input_path": "proof_library/real_data/agent/agent_drift01_metrics.json",
    },
]


def _already_verified(label: str, index: list) -> bool:
    """Check if a claim label already has a non-synthetic entry in index.json."""
    return any(
        e.get("id", "").startswith(label) and not e.get("is_synthetic", True)
        for e in index
    )


def run_all_real(dry_run: bool = False) -> dict:
    """Run all 20 claims through build_claim with is_synthetic=False.

    Returns dict with 'succeeded', 'failed', 'skipped' lists.
    """
    index = _load_index()
    succeeded = []
    failed = []
    skipped = []

    total = len(CLAIM_REGISTRY)
    print(f"\n{'='*60}")
    print(f"  mg_verify_all_real.py -- {total} claims to process")
    print(f"{'='*60}\n")

    for i, claim in enumerate(CLAIM_REGISTRY, 1):
        claim_id = claim["claim_id"]
        label = claim["label"]
        domain = claim["domain"]
        input_path = claim["input_path"]

        print(f"[{i:2d}/{total}] {claim_id} ({domain})")

        # Idempotency check
        if _already_verified(label, index):
            print(f"        SKIP -- already verified in index.json")
            skipped.append(claim_id)
            continue

        if dry_run:
            print(f"        DRY-RUN -- would run build_claim()")
            skipped.append(claim_id)
            continue

        # Build output path for run_single_claim.py
        output_dir = REPO_ROOT / "proof_library" / "real_data" / domain
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{claim_id}_output.json")

        # Script command using sys.executable for Windows compatibility
        script_cmd = (
            f"{sys.executable} scripts/run_single_claim.py"
            f" {claim_id} {input_path} {output_path}"
        )

        try:
            t0 = time.time()
            entry = build_claim(
                input_path=input_path,
                script_cmd=script_cmd,
                output_path=output_path,
                domain=domain,
                label=label,
                is_synthetic=False,
            )
            elapsed = time.time() - t0
            print(f"        OK -- {elapsed:.1f}s -- {entry['id']}")
            succeeded.append(claim_id)
            # Refresh index after each successful build
            index = _load_index()
        except Exception as exc:
            print(f"        FAILED -- {exc}")
            failed.append({"claim_id": claim_id, "error": str(exc)})

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    print(f"  Succeeded: {len(succeeded)}")
    print(f"  Skipped:   {len(skipped)}")
    print(f"  Failed:    {len(failed)}")
    if failed:
        print(f"\n  Failures:")
        for f in failed:
            print(f"    - {f['claim_id']}: {f['error']}")
    print()

    return {
        "succeeded": succeeded,
        "failed": failed,
        "skipped": skipped,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Verify all 20 active claims with real external data.",
        epilog="Produces signed bundles in proof_library/bundles/. Idempotent.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without executing",
    )
    args = parser.parse_args()

    result = run_all_real(dry_run=args.dry_run)

    if result["failed"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
