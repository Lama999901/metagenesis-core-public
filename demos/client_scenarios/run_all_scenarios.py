#!/usr/bin/env python3
"""
Master runner: execute all 4 client scenario demos and report results.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SCENARIOS = [
    ("01", "NeuralBench AI", "ML/AI", "ML_BENCH-01", "01_ai_benchmark"),
    ("02", "PsiThera", "Pharma/FDA", "PHARMA-01", "02_pharma"),
    ("03", "QuantRisk Capital", "Finance", "FINRISK-01", "03_finance"),
    ("04", "AeroSim Engineering", "Digital Twin", "DT-FEM-01", "04_digital_twin"),
]


def main() -> int:
    results = []
    for num, client, domain, claim, folder in SCENARIOS:
        script = REPO_ROOT / "demos" / "client_scenarios" / folder / "run_scenario.py"
        proc = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        passed = proc.returncode == 0
        results.append((num, client, domain, claim, passed))
        status = "PASS" if passed else "FAIL"
        print(f"  [{num}] {client}: {status}")

    # Print results table
    print()
    print("+" + "-" * 4 + "+" + "-" * 23 + "+" + "-" * 15 + "+" + "-" * 14 + "+" + "-" * 6 + "+")
    print("| #  | Client                | Domain        | Claim        |      |")
    print("+" + "-" * 4 + "+" + "-" * 23 + "+" + "-" * 15 + "+" + "-" * 14 + "+" + "-" * 6 + "+")
    for num, client, domain, claim, passed in results:
        s = "PASS" if passed else "FAIL"
        print(f"| {num} | {client:<21} | {domain:<13} | {claim:<12} | {s} |")
    print("+" + "-" * 4 + "+" + "-" * 23 + "+" + "-" * 15 + "+" + "-" * 14 + "+" + "-" * 6 + "+")

    pass_count = sum(1 for _, _, _, _, p in results if p)
    total = len(results)
    print(f"\n  {pass_count}/{total} PASS -- One protocol. Four domains. One command.")

    return 0 if pass_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
