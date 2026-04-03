#!/usr/bin/env python3
"""Extended CLI coverage tests for scripts/mg_sign.py -- 15 tests.

Targets cmd_keygen, cmd_sign, cmd_verify, cmd_temporal, and main() argparse.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import mg_sign


# ---------------------------------------------------------------------------
# 1-3: cmd_keygen
# ---------------------------------------------------------------------------

class TestCmdKeygen:
    def test_hmac_keygen_writes_file(self, tmp_path, capsys):
        out = tmp_path / "key.json"
        args = SimpleNamespace(out=str(out), type="hmac")
        rc = mg_sign.cmd_keygen(args)
        assert rc == 0
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["version"] == "hmac-sha256-v1"
        assert "key_hex" in data
        assert "fingerprint" in data
        assert "Signing key generated" in capsys.readouterr().out

    def test_ed25519_keygen_writes_keypair(self, tmp_path, capsys):
        out = tmp_path / "ed_key.json"
        args = SimpleNamespace(out=str(out), type="ed25519")
        rc = mg_sign.cmd_keygen(args)
        assert rc == 0
        assert out.exists()
        pub_path = tmp_path / "ed_key.pub.json"
        assert pub_path.exists()
        out_text = capsys.readouterr().out
        assert "Ed25519 signing key" in out_text
        assert "Fingerprint" in out_text

    def test_keygen_default_type_is_hmac(self, tmp_path):
        out = tmp_path / "default_key.json"
        args = SimpleNamespace(out=str(out))  # no type attr
        rc = mg_sign.cmd_keygen(args)
        assert rc == 0
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["version"] == "hmac-sha256-v1"


# ---------------------------------------------------------------------------
# 4-6: cmd_sign
# ---------------------------------------------------------------------------

class TestCmdSign:
    def test_sign_success(self, tmp_path, capsys):
        # Create minimal bundle + key
        pack_dir = tmp_path / "bundle"
        pack_dir.mkdir()
        manifest = {
            "files": [],
            "root_hash": "a" * 64,
            "protocol_version": 1,
        }
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        key = mg_sign.generate_key()
        key_path = tmp_path / "key.json"
        key_path.write_text(json.dumps(key), encoding="utf-8")

        args = SimpleNamespace(pack=str(pack_dir), key=str(key_path), strict=False)
        mock_tc = MagicMock(side_effect=Exception("no beacon"))
        mock_wtc = MagicMock()
        with patch.dict("sys.modules", {
            "scripts.mg_temporal": MagicMock(
                create_temporal_commitment=mock_tc,
                write_temporal_commitment=mock_wtc,
            )
        }):
            rc = mg_sign.cmd_sign(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "signed" in out.lower() or "SIGNED" in out

    def test_sign_missing_bundle_returns_one(self, tmp_path, capsys):
        args = SimpleNamespace(
            pack=str(tmp_path / "nonexistent"), key="key.json", strict=False
        )
        rc = mg_sign.cmd_sign(args)
        assert rc == 1

    def test_sign_invalid_key_returns_one(self, tmp_path, capsys):
        pack_dir = tmp_path / "bundle"
        pack_dir.mkdir()
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps({"files": [], "root_hash": "a" * 64, "protocol_version": 1}),
            encoding="utf-8",
        )
        bad_key = tmp_path / "bad.json"
        bad_key.write_text('{"version": "unknown"}', encoding="utf-8")
        args = SimpleNamespace(pack=str(pack_dir), key=str(bad_key), strict=False)
        rc = mg_sign.cmd_sign(args)
        assert rc == 1


# ---------------------------------------------------------------------------
# 7-9: cmd_verify
# ---------------------------------------------------------------------------

class TestCmdVerify:
    def _make_signed_bundle(self, tmp_path):
        """Create a signed bundle for testing."""
        pack_dir = tmp_path / "bundle"
        pack_dir.mkdir()
        manifest = {
            "files": [],
            "root_hash": "a" * 64,
            "protocol_version": 1,
        }
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        key = mg_sign.generate_key()
        key_path = tmp_path / "key.json"
        key_path.write_text(json.dumps(key), encoding="utf-8")
        mg_sign.sign_bundle(pack_dir, key_path)
        return pack_dir, key_path, key

    def test_verify_valid_signature(self, tmp_path, capsys):
        pack_dir, key_path, _ = self._make_signed_bundle(tmp_path)
        args = SimpleNamespace(
            pack=str(pack_dir), key=str(key_path), fingerprint=None
        )
        mock_mod = MagicMock(verify_temporal_commitment=MagicMock(return_value=(True, "OK")))
        with patch.dict("sys.modules", {"scripts.mg_temporal": mock_mod}):
            rc = mg_sign.cmd_verify(args)
        assert rc == 0

    def test_verify_fingerprint_only(self, tmp_path, capsys):
        pack_dir, _, key = self._make_signed_bundle(tmp_path)
        args = SimpleNamespace(
            pack=str(pack_dir), key=None,
            fingerprint=key["fingerprint"]
        )
        mock_mod = MagicMock(verify_temporal_commitment=MagicMock(return_value=(True, "OK")))
        with patch.dict("sys.modules", {"scripts.mg_temporal": mock_mod}):
            rc = mg_sign.cmd_verify(args)
        assert rc == 0

    def test_verify_no_signature_returns_one(self, tmp_path, capsys):
        pack_dir = tmp_path / "bare"
        pack_dir.mkdir()
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps({"files": [], "root_hash": "b" * 64, "protocol_version": 1}),
            encoding="utf-8",
        )
        args = SimpleNamespace(pack=str(pack_dir), key=None, fingerprint=None)
        rc = mg_sign.cmd_verify(args)
        assert rc == 1


# ---------------------------------------------------------------------------
# 10-12: cmd_temporal
# ---------------------------------------------------------------------------

class TestCmdTemporal:
    def test_temporal_success(self, tmp_path, capsys):
        pack_dir = tmp_path / "bundle"
        pack_dir.mkdir()
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps({"root_hash": "c" * 64, "protocol_version": 1}),
            encoding="utf-8",
        )
        fake_tc = {
            "beacon_status": "available",
            "temporal_binding": "bind123",
            "beacon_timestamp": "2026-04-01T00:00:00Z",
        }
        mock_mod = MagicMock(
            create_temporal_commitment=MagicMock(return_value=fake_tc),
            write_temporal_commitment=MagicMock(return_value=pack_dir / "tc.json"),
        )
        with patch.dict("sys.modules", {"scripts.mg_temporal": mock_mod}):
            args = SimpleNamespace(pack=str(pack_dir), strict=False)
            rc = mg_sign.cmd_temporal(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "bind123" in out

    def test_temporal_no_manifest(self, tmp_path, capsys):
        args = SimpleNamespace(pack=str(tmp_path), strict=False)
        rc = mg_sign.cmd_temporal(args)
        assert rc == 1

    def test_temporal_beacon_unavailable_strict(self, tmp_path, capsys):
        pack_dir = tmp_path / "bundle"
        pack_dir.mkdir()
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps({"root_hash": "d" * 64, "protocol_version": 1}),
            encoding="utf-8",
        )
        fake_tc = {
            "beacon_status": "unavailable",
            "local_timestamp": "2026-04-01T00:00:00Z",
        }
        mock_mod = MagicMock(
            create_temporal_commitment=MagicMock(return_value=fake_tc),
            write_temporal_commitment=MagicMock(return_value=pack_dir / "tc.json"),
        )
        with patch.dict("sys.modules", {"scripts.mg_temporal": mock_mod}):
            args = SimpleNamespace(pack=str(pack_dir), strict=True)
            rc = mg_sign.cmd_temporal(args)
        assert rc == 1


# ---------------------------------------------------------------------------
# 13-15: main() argparse
# ---------------------------------------------------------------------------

class TestMgSignMain:
    def test_keygen_subcommand(self, tmp_path):
        out = tmp_path / "k.json"
        with patch("sys.argv", ["mg_sign", "keygen", "--out", str(out)]):
            rc = mg_sign.main()
        assert rc == 0
        assert out.exists()

    def test_no_subcommand_exits(self):
        with patch("sys.argv", ["mg_sign"]):
            with pytest.raises(SystemExit):
                mg_sign.main()

    def test_sign_subcommand_calls_cmd_sign(self):
        with patch("sys.argv", ["mg_sign", "sign", "--pack", "/tmp/b", "--key", "/tmp/k"]):
            with patch.object(mg_sign, "cmd_sign", return_value=0) as mock_fn:
                rc = mg_sign.main()
        assert rc == 0
        mock_fn.assert_called_once()
