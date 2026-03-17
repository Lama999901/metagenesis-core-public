"""DT-SENSOR-01 Tests — IoT Sensor Integrity Certificate."""
import pytest
from backend.progress.dtsensor1_iot_certificate import run_certificate, JOB_KIND, SENSOR_SCHEMAS


class TestJobKind:
    def test_job_kind(self):
        assert JOB_KIND == "dtsensor1_iot_certificate"


class TestSensorSchemas:
    def test_all_schemas_present(self):
        for s in ["temperature_celsius", "pressure_pa", "displacement_mm", "strain_microstrain", "voltage_v"]:
            assert s in SENSOR_SCHEMAS


class TestRunCertificate:
    def test_clean_stream_passes(self):
        r = run_certificate(seed=42, sensor_type="temperature_celsius", n_readings=100, anomaly_rate=0.0)
        assert r["result"]["pass"] is True
        assert r["mtr_phase"] == "DT-SENSOR-01"

    def test_anomaly_stream_fails(self):
        r = run_certificate(seed=42, sensor_type="temperature_celsius", n_readings=100, anomaly_rate=1.0)
        assert r["result"]["pass"] is False
        assert r["result"]["issues_count"] > 0

    def test_all_five_sensor_types(self):
        for st in SENSOR_SCHEMAS:
            r = run_certificate(seed=42, sensor_type=st, n_readings=50, anomaly_rate=0.0)
            assert r["result"]["pass"] is True

    def test_stream_sha256_present(self):
        r = run_certificate(seed=42, sensor_type="pressure_pa", n_readings=50)
        sha = r["result"]["stream_sha256"]
        assert isinstance(sha, str) and len(sha) == 64

    def test_deterministic(self):
        r1 = run_certificate(seed=42, sensor_type="displacement_mm", n_readings=100)
        r2 = run_certificate(seed=42, sensor_type="displacement_mm", n_readings=100)
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_step_chain(self):
        r = run_certificate(seed=42, sensor_type="temperature_celsius", n_readings=100)
        assert len(r["execution_trace"]) == 4
        assert r["trace_root_hash"] == r["execution_trace"][-1]["hash"]

    def test_anchor_changes_trace(self):
        r1 = run_certificate(seed=42, sensor_type="temperature_celsius", n_readings=100)
        r2 = run_certificate(seed=42, sensor_type="temperature_celsius", n_readings=100, anchor_hash="a" * 64)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]

    def test_invalid_sensor_raises(self):
        with pytest.raises(ValueError):
            run_certificate(sensor_type="unknown_sensor")

    def test_too_few_readings_raises(self):
        with pytest.raises(ValueError):
            run_certificate(n_readings=5)
