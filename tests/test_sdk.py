"""
Tests for MetaGenesis Core SDK.

Tests the SDK wrapper (sdk/metagenesis.py) against the verification protocol.
Uses real bundles from demos/ when available, and synthetic test bundles
for edge cases.
"""

import hashlib
import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sdk.metagenesis import MetaGenesisClient, VerificationResult, _layer_name_to_key


# ---- Fixtures ----------------------------------------------------------------

@pytest.fixture
def client():
    """SDK client pointed at repo root."""
    return MetaGenesisClient(repo_root=REPO_ROOT)


@pytest.fixture
def valid_bundle(tmp_path):
    """Create a minimal valid bundle for testing."""
    bundle_dir = tmp_path / "test_bundle"
    bundle_dir.mkdir()

    # Create a minimal evidence.json with 4-step chain
    def _hash_step(step_name, step_data, prev_hash):
        content = json.dumps(
            {"step": step_name, "data": step_data, "prev_hash": prev_hash},
            sort_keys=True, separators=(",", ":"),
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    prev = _hash_step("init_params", {"E": 70e9}, "genesis")
    trace = [{"step": 1, "name": "init_params", "hash": prev}]
    prev = _hash_step("compute", {"displacement": 0.001}, prev)
    trace.append({"step": 2, "name": "compute", "hash": prev})
    prev = _hash_step("metrics", {"rel_err": 0.005}, prev)
    trace.append({"step": 3, "name": "metrics", "hash": prev})
    prev = _hash_step("threshold_check", {"passed": True, "threshold": 0.01}, prev)
    trace.append({"step": 4, "name": "threshold_check", "hash": prev, "output": {"pass": True}})

    evidence = {
        "mtr_phase": "MTR-1",
        "inputs": {"E_ref": 70e9},
        "result": {"relative_error": 0.005, "pass": True},
        "execution_trace": trace,
        "trace_root_hash": prev,
    }
    evidence_path = bundle_dir / "evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")

    # Build manifest
    files_list = []
    for fpath in sorted(bundle_dir.rglob("*")):
        if fpath.is_file() and fpath.name != "pack_manifest.json":
            relpath = fpath.relative_to(bundle_dir).as_posix()
            sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
            files_list.append({"relpath": relpath, "sha256": sha})

    lines = "\n".join(f"{e['relpath']}:{e['sha256']}" for e in sorted(files_list, key=lambda x: x["relpath"]))
    root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

    manifest = {
        "protocol_version": 1,
        "files": files_list,
        "root_hash": root_hash,
    }
    (bundle_dir / "pack_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    return bundle_dir


@pytest.fixture
def tampered_bundle(valid_bundle):
    """Create a bundle with tampered evidence."""
    evidence_path = valid_bundle / "evidence.json"
    data = json.loads(evidence_path.read_text(encoding="utf-8"))
    data["result"]["relative_error"] = 0.999  # Tamper
    evidence_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return valid_bundle


# ---- Test: VerificationResult ------------------------------------------------

class TestVerificationResult:
    def test_dataclass_fields(self):
        r = VerificationResult(passed=True, reason="PASS")
        assert r.passed is True
        assert r.reason == "PASS"
        assert r.layers == {}
        assert r.bundle_path == ""
        assert r.timestamp == ""
        assert r.claim_id is None
        assert r.trace_root_hash is None

    def test_with_all_fields(self):
        r = VerificationResult(
            passed=False,
            layers={"integrity": True, "semantic": False},
            reason="Semantic check failed",
            bundle_path="/tmp/bundle",
            timestamp="2026-04-11T00:00:00+00:00",
            claim_id="MTR-1",
            trace_root_hash="abc123",
        )
        assert r.passed is False
        assert r.layers["integrity"] is True
        assert r.claim_id == "MTR-1"


# ---- Test: MetaGenesisClient ------------------------------------------------

class TestClientInit:
    def test_default_root(self):
        c = MetaGenesisClient()
        assert c._root.exists()
        assert (c._root / "scripts" / "mg.py").exists()

    def test_explicit_root(self):
        c = MetaGenesisClient(repo_root=REPO_ROOT)
        assert c._root == REPO_ROOT

    def test_scripts_exist(self, client):
        assert client._standalone.exists()
        assert client._mg.exists()


# ---- Test: verify -----------------------------------------------------------

class TestVerify:
    def test_verify_valid_bundle(self, client, valid_bundle):
        result = client.verify(str(valid_bundle))
        assert result.passed is True
        assert result.reason == "PASS"
        assert "integrity" in result.layers
        assert result.layers["integrity"] is True
        assert result.bundle_path == str(valid_bundle)
        assert result.timestamp != ""

    def test_verify_extracts_claim_id(self, client, valid_bundle):
        result = client.verify(str(valid_bundle))
        assert result.claim_id == "MTR-1"

    def test_verify_extracts_trace_root(self, client, valid_bundle):
        result = client.verify(str(valid_bundle))
        assert result.trace_root_hash is not None
        assert len(result.trace_root_hash) == 64

    def test_verify_tampered_fails(self, client, tampered_bundle):
        result = client.verify(str(tampered_bundle))
        assert result.passed is False
        assert "integrity" in result.layers or "FAIL" in result.reason

    def test_verify_nonexistent_path(self, client, tmp_path):
        result = client.verify(str(tmp_path / "nonexistent"))
        assert result.passed is False
        assert "not found" in result.reason

    def test_verify_empty_dir(self, client, tmp_path):
        empty = tmp_path / "empty_bundle"
        empty.mkdir()
        result = client.verify(str(empty))
        assert result.passed is False

    def test_verify_missing_manifest(self, client, tmp_path):
        bundle = tmp_path / "no_manifest"
        bundle.mkdir()
        (bundle / "evidence.json").write_text("{}", encoding="utf-8")
        result = client.verify(str(bundle))
        assert result.passed is False


# ---- Test: pack -------------------------------------------------------------

class TestPack:
    def _make_job_result(self):
        """Create a valid job result dict."""
        def _hash_step(step_name, step_data, prev_hash):
            content = json.dumps(
                {"step": step_name, "data": step_data, "prev_hash": prev_hash},
                sort_keys=True, separators=(",", ":"),
            )
            return hashlib.sha256(content.encode("utf-8")).hexdigest()

        prev = _hash_step("init_params", {"x": 1}, "genesis")
        trace = [{"step": 1, "name": "init_params", "hash": prev}]
        prev = _hash_step("compute", {"y": 2}, prev)
        trace.append({"step": 2, "name": "compute", "hash": prev})
        prev = _hash_step("metrics", {"z": 3}, prev)
        trace.append({"step": 3, "name": "metrics", "hash": prev})
        prev = _hash_step("threshold_check", {"passed": True}, prev)
        trace.append({"step": 4, "name": "threshold_check", "hash": prev})

        return {
            "mtr_phase": "TEST-01",
            "inputs": {"x": 1},
            "result": {"y": 2, "pass": True},
            "execution_trace": trace,
            "trace_root_hash": prev,
        }

    def test_pack_creates_bundle(self, client, tmp_path):
        job = self._make_job_result()
        bundle_path = client.pack(job, str(tmp_path / "packed"))
        assert Path(bundle_path).is_dir()
        assert (Path(bundle_path) / "pack_manifest.json").exists()
        assert (Path(bundle_path) / "evidence.json").exists()

    def test_packed_bundle_verifies(self, client, tmp_path):
        job = self._make_job_result()
        bundle_path = client.pack(job, str(tmp_path / "packed"))
        result = client.verify(bundle_path)
        assert result.passed is True

    def test_pack_missing_key_raises(self, client, tmp_path):
        with pytest.raises(ValueError, match="missing required key"):
            client.pack({"mtr_phase": "X"}, str(tmp_path / "bad"))

    def test_pack_manifest_has_root_hash(self, client, tmp_path):
        job = self._make_job_result()
        bundle_path = client.pack(job, str(tmp_path / "packed"))
        manifest = json.loads((Path(bundle_path) / "pack_manifest.json").read_text(encoding="utf-8"))
        assert "root_hash" in manifest
        assert len(manifest["root_hash"]) == 64

    def test_pack_manifest_has_protocol_version(self, client, tmp_path):
        job = self._make_job_result()
        bundle_path = client.pack(job, str(tmp_path / "packed"))
        manifest = json.loads((Path(bundle_path) / "pack_manifest.json").read_text(encoding="utf-8"))
        assert manifest["protocol_version"] == 1


# ---- Test: Layer name mapping ------------------------------------------------

class TestLayerNameMapping:
    def test_layer_1(self):
        assert _layer_name_to_key("Layer 1 -- SHA-256 Integrity") == "integrity"

    def test_layer_2(self):
        assert _layer_name_to_key("Layer 2 -- Semantic Verification") == "semantic"

    def test_layer_3(self):
        assert _layer_name_to_key("Layer 3 -- Step Chain") == "step_chain"

    def test_layer_4(self):
        assert _layer_name_to_key("Layer 4 -- Bundle Signature") == "signature"

    def test_layer_5(self):
        assert _layer_name_to_key("Layer 5 -- Temporal Commitment") == "temporal"

    def test_unknown_layer(self):
        assert _layer_name_to_key("Unknown") == "unknown"


# ---- Test: Round-trip (pack -> verify) ---------------------------------------

class TestRoundTrip:
    def test_pack_then_verify(self, client, tmp_path):
        """End-to-end: pack a result, then verify the bundle."""
        def _hash_step(step_name, step_data, prev_hash):
            content = json.dumps(
                {"step": step_name, "data": step_data, "prev_hash": prev_hash},
                sort_keys=True, separators=(",", ":"),
            )
            return hashlib.sha256(content.encode("utf-8")).hexdigest()

        prev = _hash_step("init_params", {"accuracy": 0.94}, "genesis")
        trace = [{"step": 1, "name": "init_params", "hash": prev}]
        prev = _hash_step("compute", {"predicted": [1, 0, 1]}, prev)
        trace.append({"step": 2, "name": "compute", "hash": prev})
        prev = _hash_step("metrics", {"accuracy": 0.94}, prev)
        trace.append({"step": 3, "name": "metrics", "hash": prev})
        prev = _hash_step("threshold_check", {"passed": True, "threshold": 0.02}, prev)
        trace.append({"step": 4, "name": "threshold_check", "hash": prev})

        job = {
            "mtr_phase": "ML_BENCH-01",
            "inputs": {"dataset": {"name": "test.csv"}},
            "result": {"actual_accuracy": 0.94, "pass": True},
            "execution_trace": trace,
            "trace_root_hash": prev,
        }

        bundle = client.pack(job, str(tmp_path / "ml_bundle"))
        result = client.verify(bundle)
        assert result.passed is True
        assert result.layers.get("integrity") is True
        assert result.layers.get("step_chain") is True

    def test_tamper_after_pack_detected(self, client, tmp_path):
        """Pack, tamper with evidence, verify detects it."""
        def _hash_step(step_name, step_data, prev_hash):
            content = json.dumps(
                {"step": step_name, "data": step_data, "prev_hash": prev_hash},
                sort_keys=True, separators=(",", ":"),
            )
            return hashlib.sha256(content.encode("utf-8")).hexdigest()

        prev = _hash_step("init_params", {"x": 1}, "genesis")
        trace = [{"step": 1, "name": "init_params", "hash": prev}]
        prev = _hash_step("compute", {"y": 2}, prev)
        trace.append({"step": 2, "name": "compute", "hash": prev})
        prev = _hash_step("metrics", {"z": 3}, prev)
        trace.append({"step": 3, "name": "metrics", "hash": prev})
        prev = _hash_step("threshold_check", {"passed": True}, prev)
        trace.append({"step": 4, "name": "threshold_check", "hash": prev})

        job = {
            "mtr_phase": "TEST-01",
            "inputs": {"x": 1},
            "result": {"y": 2, "pass": True},
            "execution_trace": trace,
            "trace_root_hash": prev,
        }

        bundle = client.pack(job, str(tmp_path / "tamper_test"))

        # Tamper with evidence
        ev_path = Path(bundle) / "evidence.json"
        data = json.loads(ev_path.read_text(encoding="utf-8"))
        data["result"]["y"] = 999
        ev_path.write_text(json.dumps(data), encoding="utf-8")

        result = client.verify(bundle)
        assert result.passed is False
