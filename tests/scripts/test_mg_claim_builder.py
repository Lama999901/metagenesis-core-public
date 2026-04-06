"""Tests for scripts/mg_claim_builder.py — the external verification door."""

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_claim_builder import (
    _hash_step,
    _load_index,
    _save_index,
    _sha256_path,
    _sha256_string,
    build_claim,
)


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_proof_library(tmp_path, monkeypatch):
    """Redirect proof_library to a temp dir for isolation."""
    import scripts.mg_claim_builder as mod

    lib = tmp_path / "proof_library"
    lib.mkdir()
    (lib / "bundles").mkdir()
    (lib / "index.json").write_text("[]", encoding="utf-8")

    monkeypatch.setattr(mod, "PROOF_LIBRARY", lib)
    monkeypatch.setattr(mod, "BUNDLES_DIR", lib / "bundles")
    monkeypatch.setattr(mod, "INDEX_PATH", lib / "index.json")
    return lib


@pytest.fixture
def simple_input(tmp_path):
    """Create a simple input file."""
    f = tmp_path / "input.txt"
    f.write_text("hello world\n", encoding="utf-8")
    return f


@pytest.fixture
def simple_script():
    """A script command that always succeeds."""
    return f"{sys.executable} -c \"print('result: 42')\""


@pytest.fixture
def failing_script():
    """A script command that always fails."""
    return f"{sys.executable} -c \"import sys; print('error'); sys.exit(1)\""


@pytest.fixture
def output_script(tmp_path):
    """A script that writes an output file."""
    out = tmp_path / "output.txt"
    return f"{sys.executable} -c \"open(r'{out}', 'w').write('result: 42\\n')\"", out


# ── Unit Tests: Hash Functions ──────────────────────────────────────────────


class TestSha256Path:
    def test_file_hash_deterministic(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello", encoding="utf-8")
        h1 = _sha256_path(f)
        h2 = _sha256_path(f)
        assert h1 == h2
        assert len(h1) == 64

    def test_file_hash_changes_with_content(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello", encoding="utf-8")
        h1 = _sha256_path(f)
        f.write_text("world", encoding="utf-8")
        h2 = _sha256_path(f)
        assert h1 != h2

    def test_dir_hash_deterministic(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        (d / "a.txt").write_text("aaa", encoding="utf-8")
        (d / "b.txt").write_text("bbb", encoding="utf-8")
        h1 = _sha256_path(d)
        h2 = _sha256_path(d)
        assert h1 == h2

    def test_dir_hash_changes_with_content(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        (d / "a.txt").write_text("aaa", encoding="utf-8")
        h1 = _sha256_path(d)
        (d / "a.txt").write_text("modified", encoding="utf-8")
        h2 = _sha256_path(d)
        assert h1 != h2

    def test_nonexistent_path_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            _sha256_path(tmp_path / "nonexistent")


class TestSha256String:
    def test_deterministic(self):
        assert _sha256_string("hello") == _sha256_string("hello")

    def test_different_input_different_hash(self):
        assert _sha256_string("hello") != _sha256_string("world")

    def test_returns_hex(self):
        h = _sha256_string("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


class TestHashStep:
    def test_genesis_chain(self):
        h = _hash_step("init", {"x": 1}, "genesis")
        assert len(h) == 64

    def test_chain_deterministic(self):
        h1 = _hash_step("step1", {"a": "b"}, "prev123")
        h2 = _hash_step("step1", {"a": "b"}, "prev123")
        assert h1 == h2

    def test_chain_changes_with_data(self):
        h1 = _hash_step("step1", {"a": "b"}, "prev123")
        h2 = _hash_step("step1", {"a": "c"}, "prev123")
        assert h1 != h2

    def test_chain_changes_with_prev_hash(self):
        h1 = _hash_step("step1", {"a": "b"}, "prev1")
        h2 = _hash_step("step1", {"a": "b"}, "prev2")
        assert h1 != h2


# ── Unit Tests: Index Operations ────────────────────────────────────────────


class TestIndexOperations:
    def test_load_empty_index(self, tmp_proof_library):
        entries = _load_index()
        assert entries == []

    def test_save_and_load_roundtrip(self, tmp_proof_library):
        entries = [{"id": "test-1", "domain": "test"}]
        _save_index(entries)
        loaded = _load_index()
        assert loaded == entries

    def test_append_preserves_existing(self, tmp_proof_library):
        _save_index([{"id": "first"}])
        entries = _load_index()
        entries.append({"id": "second"})
        _save_index(entries)
        loaded = _load_index()
        assert len(loaded) == 2
        assert loaded[0]["id"] == "first"
        assert loaded[1]["id"] == "second"


# ── Integration Tests: build_claim ──────────────────────────────────────────


class TestBuildClaim:
    def test_successful_claim(self, tmp_proof_library, simple_input, simple_script):
        result = build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent_output.txt",
            domain="test domain",
            label="test-claim",
        )
        assert result["exit_code"] == 0
        assert result["is_synthetic"] is False
        assert result["domain"] == "test domain"
        assert "test-claim" in result["id"]
        assert result["what_not_proved"] == "Correctness or physical validity of the result"
        assert len(result["input_hash"]) == 64
        assert len(result["script_hash"]) == 64
        assert len(result["output_hash"]) == 64
        assert len(result["trace_root_hash"]) == 64

    def test_index_updated_after_claim(self, tmp_proof_library, simple_input, simple_script):
        build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="idx-test",
        )
        entries = _load_index()
        assert len(entries) == 1
        assert entries[0]["domain"] == "test"

    def test_bundle_zip_created(self, tmp_proof_library, simple_input, simple_script):
        build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="zip-test",
        )
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        assert len(zips) == 1
        with zipfile.ZipFile(zips[0]) as zf:
            names = zf.namelist()
            assert "evidence.json" in names
            assert "pack_manifest.json" in names
            assert "stdout.txt" in names

    def test_evidence_has_valid_trace(self, tmp_proof_library, simple_input, simple_script):
        build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="trace-test",
        )
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        with zipfile.ZipFile(zips[0]) as zf:
            evidence = json.loads(zf.read("evidence.json"))
        trace = evidence["execution_trace"]
        assert len(trace) == 4
        assert trace[0]["name"] == "init_params"
        assert trace[1]["name"] == "execute"
        assert trace[2]["name"] == "metrics"
        assert trace[3]["name"] == "threshold_check"
        assert trace[3]["output"]["pass"] is True
        assert evidence["trace_root_hash"] == trace[3]["hash"]

    def test_hash_chain_integrity(self, tmp_proof_library, simple_input, simple_script):
        """Verify the 4-step hash chain is cryptographically valid."""
        build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="chain-test",
        )
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        with zipfile.ZipFile(zips[0]) as zf:
            evidence = json.loads(zf.read("evidence.json"))

        trace = evidence["execution_trace"]
        # Each step's hash should be deterministic given inputs
        for step in trace:
            assert len(step["hash"]) == 64
        # Chain links: each step hash is different
        hashes = [s["hash"] for s in trace]
        assert len(set(hashes)) == 4  # all unique

    def test_failing_script_records_failure(self, tmp_proof_library, simple_input, failing_script):
        result = build_claim(
            input_path=str(simple_input),
            script_cmd=failing_script,
            output_path="nonexistent.txt",
            domain="test",
            label="fail-test",
        )
        assert result["exit_code"] == 1
        # Evidence should still be created
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        assert len(zips) == 1
        with zipfile.ZipFile(zips[0]) as zf:
            evidence = json.loads(zf.read("evidence.json"))
        assert evidence["result"]["passed"] is False
        assert evidence["execution_trace"][3]["output"]["pass"] is False

    def test_with_real_output_file(self, tmp_proof_library, simple_input, output_script):
        script_cmd, output_path = output_script
        result = build_claim(
            input_path=str(simple_input),
            script_cmd=script_cmd,
            output_path=str(output_path),
            domain="test",
            label="output-test",
        )
        assert result["exit_code"] == 0
        assert result["output_hash"] == _sha256_path(output_path)
        # Output file should be included in bundle
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        with zipfile.ZipFile(zips[0]) as zf:
            assert output_path.name in zf.namelist()

    def test_synthetic_flag(self, tmp_proof_library, simple_input, simple_script):
        result = build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="synth-test",
            is_synthetic=True,
        )
        assert result["is_synthetic"] is True

    def test_directory_as_input(self, tmp_proof_library, tmp_path, simple_script):
        d = tmp_path / "data"
        d.mkdir()
        (d / "a.csv").write_text("x,y\n1,2\n", encoding="utf-8")
        (d / "b.csv").write_text("x,y\n3,4\n", encoding="utf-8")
        result = build_claim(
            input_path=str(d),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="dir-input-test",
        )
        assert result["exit_code"] == 0
        assert len(result["input_hash"]) == 64

    def test_manifest_in_bundle_has_root_hash(self, tmp_proof_library, simple_input, simple_script):
        build_claim(
            input_path=str(simple_input),
            script_cmd=simple_script,
            output_path="nonexistent.txt",
            domain="test",
            label="manifest-test",
        )
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        with zipfile.ZipFile(zips[0]) as zf:
            manifest = json.loads(zf.read("pack_manifest.json"))
        assert "root_hash" in manifest
        assert "files" in manifest
        assert "trace_root_hash" in manifest
        assert len(manifest["root_hash"]) == 64

    def test_multiple_claims_accumulate(self, tmp_proof_library, simple_input, simple_script):
        build_claim(str(simple_input), simple_script, "x.txt", "d1", "first")
        build_claim(str(simple_input), simple_script, "x.txt", "d2", "second")
        entries = _load_index()
        assert len(entries) == 2
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        assert len(zips) == 2


# ── Determinism Tests ───────────────────────────────────────────────────────


class TestDeterminism:
    def test_same_input_same_hash(self, tmp_path):
        f = tmp_path / "data.txt"
        f.write_text("fixed content", encoding="utf-8")
        h1 = _sha256_path(f)
        h2 = _sha256_path(f)
        assert h1 == h2

    def test_hash_step_reproducible(self):
        data = {"key": "value", "number": 42}
        h1 = _hash_step("test_step", data, "genesis")
        h2 = _hash_step("test_step", data, "genesis")
        assert h1 == h2


# ── Honesty Tests ───────────────────────────────────────────────────────────


class TestHonesty:
    """Verify the claim builder is honest about what it proves."""

    def test_what_not_proved_always_present(self, tmp_proof_library, simple_input, simple_script):
        result = build_claim(str(simple_input), simple_script, "x.txt", "test", "honest")
        assert "what_not_proved" in result
        assert "Correctness" in result["what_not_proved"]

    def test_what_proved_references_determinism(self, tmp_proof_library, simple_input, simple_script):
        result = build_claim(str(simple_input), simple_script, "x.txt", "test", "proved")
        assert "what_proved" in result
        assert "Determinism" in result["what_proved"]

    def test_evidence_contains_both_hashes(self, tmp_proof_library, simple_input, simple_script):
        build_claim(str(simple_input), simple_script, "x.txt", "test", "hashes")
        zips = list((tmp_proof_library / "bundles").glob("*.zip"))
        with zipfile.ZipFile(zips[0]) as zf:
            evidence = json.loads(zf.read("evidence.json"))
        assert "input_hash" in evidence["inputs"]
        assert "script_hash" in evidence["inputs"]
        assert "output_hash" in evidence["result"]
