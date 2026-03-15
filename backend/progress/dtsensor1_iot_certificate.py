#!/usr/bin/env python3
"""
DT-SENSOR-01 — IoT Sensor Data Integrity Certificate.
Verifies sensor data stream integrity:
  - Schema validation (required fields present)
  - Range checks (values within physical bounds)
  - Temporal consistency (monotonic timestamps)
  - SHA-256 fingerprint of the data stream
Produces tamper-evident evidence bundle for IoT/Digital Twin pipelines.
"""
import random
import hashlib
import json
from typing import Dict, Any, List, Optional

JOB_KIND = "dtsensor1_iot_certificate"
ALGORITHM_VERSION = "v1"
METHOD = "sensor_schema_range_temporal_verify"

SENSOR_SCHEMAS = {
    "temperature_celsius": {"min": -273.15, "max": 2000.0, "unit": "°C"},
    "pressure_pa": {"min": 0.0, "max": 1e8, "unit": "Pa"},
    "displacement_mm": {"min": -1e6, "max": 1e6, "unit": "mm"},
    "strain_microstrain": {"min": -50000, "max": 50000, "unit": "με"},
    "voltage_v": {"min": -1000.0, "max": 1000.0, "unit": "V"},
}


def _generate_sensor_stream(seed, n_readings, sensor_type, anomaly_rate):
    rng = random.Random(seed)
    schema = SENSOR_SCHEMAS[sensor_type]
    mid = (schema["min"] + schema["max"]) / 2
    spread = (schema["max"] - schema["min"]) * 0.1
    readings = []
    for i in range(n_readings):
        value = rng.gauss(mid, spread * 0.1)
        if rng.random() < anomaly_rate:
            value = schema["max"] * 2  # out of range
        readings.append({
            "t": i * 100,  # ms timestamps, monotonic
            "v": round(value, 6),
            "sensor_id": f"{sensor_type}_{i % 3}",
        })
    return readings


def _validate_stream(readings, sensor_type):
    schema = SENSOR_SCHEMAS[sensor_type]
    issues = []
    prev_t = None
    for i, r in enumerate(readings):
        if "t" not in r or "v" not in r or "sensor_id" not in r:
            issues.append(f"row {i}: missing required field")
        elif not (schema["min"] <= r["v"] <= schema["max"]):
            issues.append(f"row {i}: value {r['v']} out of range [{schema['min']}, {schema['max']}]")
        elif prev_t is not None and r["t"] <= prev_t:
            issues.append(f"row {i}: timestamp not monotonic")
        prev_t = r.get("t")
    return issues


def _fingerprint_stream(readings):
    content = json.dumps(readings, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _hash_step(step_name, step_data, prev_hash):
    import hashlib as _h
    import json as _j
    content = _j.dumps({"step": step_name, "data": step_data, "prev_hash": prev_hash}, sort_keys=True, separators=(",", ":"))
    return _h.sha256(content.encode("utf-8")).hexdigest()


def run_certificate(
    seed: int = 42,
    sensor_type: str = "temperature_celsius",
    n_readings: int = 100,
    anomaly_rate: float = 0.0,
    device_id: str = "SENSOR-001",
    anchor_hash: Optional[str] = None,
    anchor_claim_id: str = "MTR-1",
) -> Dict[str, Any]:
    if sensor_type not in SENSOR_SCHEMAS:
        raise ValueError(f"sensor_type must be one of: {list(SENSOR_SCHEMAS)}")
    if n_readings < 10:
        raise ValueError("n_readings must be >= 10")
    if not 0.0 <= anomaly_rate <= 1.0:
        raise ValueError("anomaly_rate must be in [0, 1]")

    readings = _generate_sensor_stream(seed, n_readings, sensor_type, anomaly_rate)
    issues = _validate_stream(readings, sensor_type)
    stream_sha256 = _fingerprint_stream(readings)
    passed = len(issues) == 0

    p = _hash_step("init_params", {
        "seed": seed,
        "sensor_type": sensor_type,
        "n_readings": n_readings,
        "anomaly_rate": anomaly_rate,
        "device_id": device_id,
        "anchor_hash": anchor_hash or "none",
    }, "genesis")
    trace = [{"step": 1, "name": "init_params", "hash": p}]

    p = _hash_step("generate_stream", {"n_readings": n_readings, "seed": seed, "stream_sha256": stream_sha256[:16]}, p)
    trace.append({"step": 2, "name": "generate_stream", "hash": p, "output": {"n_readings": n_readings, "sha256_prefix": stream_sha256[:16]}})

    p = _hash_step("validate_stream", {"issues_count": len(issues), "schema": SENSOR_SCHEMAS[sensor_type]}, p)
    trace.append({"step": 3, "name": "validate_stream", "hash": p, "output": {"issues_count": len(issues)}})

    p = _hash_step("threshold_check", {"passed": passed, "issues_count": len(issues)}, p)
    trace.append({"step": 4, "name": "threshold_check", "hash": p, "output": {"pass": passed}})

    return {
        "mtr_phase": "DT-SENSOR-01",
        "algorithm_version": ALGORITHM_VERSION,
        "method": METHOD,
        "inputs": {
            "seed": seed,
            "sensor_type": sensor_type,
            "n_readings": n_readings,
            "anomaly_rate": anomaly_rate,
            "device_id": device_id,
            "schema": SENSOR_SCHEMAS[sensor_type],
            "anchor_hash": anchor_hash,
            "anchor_claim_id": anchor_claim_id if anchor_hash else None,
        },
        "result": {
            "pass": passed,
            "issues": issues[:20],
            "issues_count": len(issues),
            "n_readings": n_readings,
            "stream_sha256": stream_sha256,
            "sensor_type": sensor_type,
            "device_id": device_id,
        },
        "execution_trace": trace,
        "trace_root_hash": p,
        "status": "SUCCEEDED",
    }
