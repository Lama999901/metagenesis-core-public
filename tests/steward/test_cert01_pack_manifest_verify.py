#!/usr/bin/env python3
"""
CERT-01 Pack manifest and verify tests.

Pack must include pack_manifest.json; mg pack verify must PASS for valid pack
and FAIL when a file is tampered.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
MG_SCRIPT = REPO_ROOT / "scripts" / "mg.py"


def _run_mg(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(MG_SCRIPT)] + list(args),
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


class TestCert01PackManifestVerify:
    """CERT-01: pack manifest and verify."""

    def test_manifest_exists_with_expected_keys(self, tmp_path):
        r = _run_mg("pack", "build", "--output", str(tmp_path / "pack"))
        assert r.returncode == 0
        manifest_path = tmp_path / "pack" / "pack_manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert "pack_version" in data
        assert "protocol_version" in data
        assert "files" in data
        assert "root_hash" in data
        assert isinstance(data["files"], list)
        assert len(data["files"]) >= 1
        for f in data["files"]:
            assert "relpath" in f
            assert "sha256" in f
            assert "bytes" in f
            assert ".." not in f["relpath"]
            assert not f["relpath"].startswith("/")

    def test_verify_passes_for_valid_pack(self, tmp_path):
        pack_dir = tmp_path / "pack"
        _run_mg("pack", "build", "--output", str(pack_dir))
        r = _run_mg("pack", "verify", "--pack", str(pack_dir))
        assert r.returncode == 0
        assert "PASS" in r.stdout

    def test_verify_fails_when_file_tampered(self, tmp_path):
        pack_dir = tmp_path / "pack"
        _run_mg("pack", "build", "--output", str(pack_dir))
        overview = pack_dir / "overview.md"
        assert overview.exists()
        overview.write_bytes(overview.read_bytes() + b"\n")
        r = _run_mg("pack", "verify", "--pack", str(pack_dir))
        assert r.returncode != 0
        assert "mismatch" in r.stdout.lower()
