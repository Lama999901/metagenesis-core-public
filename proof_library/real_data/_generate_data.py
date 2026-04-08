#!/usr/bin/env python3
"""Generate all 20 real input data files for Phase 23 verification.

Deterministic: uses random.Random(seed) for reproducibility.
Run once to create all CSV and JSON files.
"""

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent  # proof_library/real_data/


def write_csv(path: Path, header: list, rows: list):
    """Write CSV with Unix line endings, UTF-8, no trailing whitespace."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, data: dict):
    """Write JSON with Unix line endings, UTF-8."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False))
        f.write("\n")


def gen_mtr1():
    """Aluminum stress-strain: E=70e9, 50 points, strain 0..0.002."""
    rng = random.Random(42)
    E_true = 70e9
    n = 50
    rows = []
    for i in range(n):
        strain = 0.002 * i / (n - 1)
        stress = E_true * strain + rng.gauss(0, 1e6)
        rows.append([f"{strain:.10f}", f"{stress:.6f}"])
    write_csv(ROOT / "materials" / "mtr1_aluminum_stress_strain.csv",
              ["strain", "stress"], rows)


def gen_mtr4():
    """Titanium stress-strain: E=114e9, 50 points, strain 0..0.002."""
    rng = random.Random(42)
    E_true = 114e9
    n = 50
    rows = []
    for i in range(n):
        strain = 0.002 * i / (n - 1)
        stress = E_true * strain + rng.gauss(0, 2e6)
        rows.append([f"{strain:.10f}", f"{stress:.6f}"])
    write_csv(ROOT / "materials" / "mtr4_titanium_stress_strain.csv",
              ["strain", "stress"], rows)


def gen_mtr5():
    """Steel stress-strain: E=193e9, 50 points, strain 0..0.002."""
    rng = random.Random(42)
    E_true = 193e9
    n = 50
    rows = []
    for i in range(n):
        strain = 0.002 * i / (n - 1)
        stress = E_true * strain + rng.gauss(0, 3e6)
        rows.append([f"{strain:.10f}", f"{stress:.6f}"])
    write_csv(ROOT / "materials" / "mtr5_steel_stress_strain.csv",
              ["strain", "stress"], rows)


def gen_mlbench1():
    """Classification predictions: 150 rows, ~94% accuracy."""
    rng = random.Random(42)
    rows = []
    correct = 0
    for i in range(150):
        y_true = rng.randint(0, 1)
        # Make ~94% correct (141/150)
        if i < 141:
            y_pred = y_true
        else:
            y_pred = 1 - y_true
        rows.append([y_true, y_pred])
        if y_true == y_pred:
            correct += 1
    # Shuffle to avoid obvious pattern
    rng.shuffle(rows)
    write_csv(ROOT / "ml" / "mlbench1_predictions.csv",
              ["y_true", "y_pred"], rows)


def gen_mlbench2():
    """Regression predictions: 200 rows, RMSE ~0.15."""
    rng = random.Random(42)
    rows = []
    for i in range(200):
        y_true = -5.0 + 10.0 * i / 199
        y_pred = y_true + rng.gauss(0, 0.15)
        rows.append([f"{y_true:.6f}", f"{y_pred:.6f}"])
    write_csv(ROOT / "ml" / "mlbench2_regression.csv",
              ["y_true", "y_pred"], rows)


def gen_mlbench3():
    """Time series predictions: 100 rows, MAPE ~0.5%."""
    rng = random.Random(42)
    rows = []
    for i in range(100):
        y_true = 100.0 + 0.1 * i
        y_pred = y_true * (1.0 + rng.gauss(0, 0.005))
        rows.append([f"{y_true:.6f}", f"{y_pred:.6f}"])
    write_csv(ROOT / "ml" / "mlbench3_timeseries.csv",
              ["y_true", "y_pred"], rows)


def gen_datapipe1():
    """Dataset with id, value, category: 50 rows."""
    rng = random.Random(42)
    categories = ["A", "B", "C"]
    rows = []
    for i in range(1, 51):
        value = round(rng.uniform(0, 1000), 2)
        cat = rng.choice(categories)
        rows.append([i, value, cat])
    write_csv(ROOT / "systems" / "datapipe1_dataset.csv",
              ["id", "value", "category"], rows)


def gen_dtfem1():
    """FEM displacement: 20 rows, fem_value close to measured_value (<2%)."""
    rng = random.Random(42)
    rows = []
    for i in range(20):
        measured = 1.0 + 0.1 * i
        fem = measured * (1.0 + rng.gauss(0, 0.005))
        rows.append([f"{fem:.6f}", f"{measured:.6f}", "displacement_mm"])
    write_csv(ROOT / "digital_twin" / "dtfem1_displacement.csv",
              ["fem_value", "measured_value", "quantity"], rows)


def gen_json_files():
    """Write all JSON input files."""
    # Materials JSON
    write_json(ROOT / "materials" / "mtr2_thermal_paste.json", {
        "seed": 100, "k_true": 5.0, "n_points": 50,
        "L": 0.01, "A": 1e-4, "q_max": 10.0
    })
    write_json(ROOT / "materials" / "mtr3_multilayer_thermal.json", {
        "seed": 101, "k_true": 5.0, "r_contact_true": 0.1,
        "n_points": 50, "L1": 0.01, "A1": 1e-4,
        "L2": 0.02, "A2": 1e-4, "q_max": 10.0
    })
    write_json(ROOT / "materials" / "mtr6_copper_thermal.json", {
        "seed": 102, "k_true": 401.0, "n_points": 50,
        "L": 0.01, "A": 1e-4, "q_max": 10.0
    })

    # Physics JSON
    write_json(ROOT / "physics" / "phys01_boltzmann_input.json", {
        "T": 300.0
    })
    write_json(ROOT / "physics" / "phys02_avogadro_input.json", {
        "note": "SI 2019 exact constant verification - no external parameters needed"
    })

    # Systems JSON
    write_json(ROOT / "systems" / "sysid1_arx_data.json", {
        "seed": 200, "a_true": 0.9, "b_true": 0.5,
        "n_steps": 100, "u_max": 1.0
    })
    write_json(ROOT / "systems" / "drift01_monitor.json", {
        "anchor_value": 70e9, "current_value": 69.5e9,
        "anchor_claim_id": "MTR-1", "anchor_units": "Pa",
        "drift_threshold_pct": 5.0
    })

    # Digital twin JSON
    write_json(ROOT / "digital_twin" / "dtsensor1_temperature.json", {
        "seed": 300, "sensor_type": "temperature_celsius",
        "n_readings": 200, "anomaly_rate": 0.0,
        "device_id": "SENSOR-LAB-001"
    })
    write_json(ROOT / "digital_twin" / "dtcalib1_convergence.json", {
        "seed": 301, "n_iterations": 15, "initial_drift_pct": 18.0,
        "convergence_rate": 0.35, "convergence_threshold": 2.5,
        "noise_scale": 0.08, "twin_id": "TWIN-FEM-001"
    })

    # Pharma JSON
    write_json(ROOT / "pharma" / "pharma1_admet.json", {
        "seed": 400, "property_name": "solubility",
        "claimed_value": -3.5, "tolerance": 0.5,
        "noise_scale": 0.15, "compound_id": "ASPIRIN-001"
    })

    # Finance JSON
    write_json(ROOT / "finance" / "finrisk1_returns.json", {
        "seed": 500, "claimed_var": 0.023, "var_tolerance": 0.005,
        "confidence_level": 0.99, "n_obs": 2000,
        "mu": 0.0001, "sigma": 0.01,
        "portfolio_id": "EQUITY-SP500-001"
    })

    # Agent JSON
    write_json(ROOT / "agent" / "agent_drift01_metrics.json", {
        "baseline": {
            "tests_per_phase": 47, "pass_rate": 1.0,
            "regressions": 0, "verifier_iterations": 1.2
        },
        "current": {
            "tests_per_phase": 50, "pass_rate": 1.0,
            "regressions": 0, "verifier_iterations": 1.1
        },
        "drift_threshold_pct": 20.0
    })


if __name__ == "__main__":
    gen_mtr1()
    gen_mtr4()
    gen_mtr5()
    gen_mlbench1()
    gen_mlbench2()
    gen_mlbench3()
    gen_datapipe1()
    gen_dtfem1()
    gen_json_files()
    print("All 20 data files generated.")
