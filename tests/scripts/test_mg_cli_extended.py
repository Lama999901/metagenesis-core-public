#!/usr/bin/env python3
"""Extended CLI coverage tests for scripts/mg.py -- 25 tests.

Targets cmd_pack_verify, cmd_verify_chain, cmd_bench_run, cmd_claim_run_mtr1,
_cmd_sign_keygen, _cmd_sign_bundle, _cmd_sign_verify, and main() argparse.
mg.py is SEALED -- only tests, no modifications.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import mg


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_verify_pack_result(ok, msg="PASS", report=None):
    """Return a (_verify_pack) style tuple."""
    return (ok, msg, report or {})


# ---------------------------------------------------------------------------
# 1-5: cmd_pack_verify
# ---------------------------------------------------------------------------

class TestCmdPackVerify:
    def test_pass_returns_zero(self):
        args = SimpleNamespace(input=Path("dummy"))
        with patch.object(mg, "_verify_pack", return_value=(True, "PASS", {})):
            assert mg.cmd_pack_verify(args) == 0

    def test_fail_returns_one(self):
        args = SimpleNamespace(input=Path("dummy"))
        with patch.object(mg, "_verify_pack", return_value=(False, "FAIL", {})):
            assert mg.cmd_pack_verify(args) == 1

    def test_prints_message(self, capsys):
        args = SimpleNamespace(input=Path("dummy"))
        with patch.object(mg, "_verify_pack", return_value=(True, "ALL GOOD", {})):
            mg.cmd_pack_verify(args)
        assert "ALL GOOD" in capsys.readouterr().out

    def test_passes_input_path(self):
        args = SimpleNamespace(input=Path("/my/bundle"))
        with patch.object(mg, "_verify_pack", return_value=(True, "PASS", {})) as mock_vp:
            mg.cmd_pack_verify(args)
            mock_vp.assert_called_once_with(Path("/my/bundle"))

    def test_fail_message_printed(self, capsys):
        args = SimpleNamespace(input=Path("dummy"))
        with patch.object(mg, "_verify_pack", return_value=(False, "SHA256 mismatch", {})):
            rc = mg.cmd_pack_verify(args)
        assert rc == 1
        assert "SHA256 mismatch" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# 6-10: cmd_verify_chain
# ---------------------------------------------------------------------------

class TestCmdVerifyChain:
    def test_pass_returns_zero(self):
        args = SimpleNamespace(packs=[Path("a"), Path("b")], json=None)
        with patch.object(mg, "_verify_chain", return_value=(True, "CHAIN PASS", {"errors": []})):
            assert mg.cmd_verify_chain(args) == 0

    def test_fail_returns_one(self):
        args = SimpleNamespace(packs=[Path("a"), Path("b")], json=None)
        with patch.object(mg, "_verify_chain", return_value=(False, "CHAIN BROKEN", {"errors": ["err1"]})):
            assert mg.cmd_verify_chain(args) == 1

    def test_json_output_written(self, tmp_path):
        json_out = tmp_path / "report.json"
        args = SimpleNamespace(packs=[Path("a"), Path("b")], json=str(json_out))
        report = {"errors": [], "chain_length": 2}
        with patch.object(mg, "_verify_chain", return_value=(True, "CHAIN PASS", report)):
            mg.cmd_verify_chain(args)
        data = json.loads(json_out.read_text(encoding="utf-8"))
        assert data["chain_length"] == 2

    def test_prints_errors_on_failure(self, capsys):
        args = SimpleNamespace(packs=[Path("a"), Path("b")], json=None)
        with patch.object(mg, "_verify_chain", return_value=(False, "FAIL", {"errors": ["bad link"]})):
            mg.cmd_verify_chain(args)
        out = capsys.readouterr().out
        assert "bad link" in out

    def test_json_creates_parent_dirs(self, tmp_path):
        json_out = tmp_path / "sub" / "dir" / "report.json"
        args = SimpleNamespace(packs=[Path("a"), Path("b")], json=str(json_out))
        with patch.object(mg, "_verify_chain", return_value=(True, "OK", {"errors": []})):
            mg.cmd_verify_chain(args)
        assert json_out.exists()


# ---------------------------------------------------------------------------
# 11-15: cmd_bench_run
# ---------------------------------------------------------------------------

class TestCmdBenchRun:
    def test_basic_invocation(self):
        args = SimpleNamespace(
            output="out_dir", reports="rep_dir", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "_run", return_value=0) as mock_run:
            rc = mg.cmd_bench_run(args)
        assert rc == 0
        cmd = mock_run.call_args[0][0]
        assert "--output-dir" in cmd
        assert "out_dir" in cmd
        assert "--mode" in cmd
        assert "both" in cmd

    def test_dataset_relpath(self):
        args = SimpleNamespace(
            output="o", reports="r", mode="normal",
            dataset_relpath="data/train.csv", elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "_run", return_value=0) as mock_run:
            mg.cmd_bench_run(args)
        cmd = mock_run.call_args[0][0]
        assert "--dataset-relpath" in cmd
        assert "data/train.csv" in cmd

    def test_elastic_strain_max(self):
        args = SimpleNamespace(
            output="o", reports="r", mode="normal",
            dataset_relpath=None, elastic_strain_max=0.05,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "_run", return_value=0) as mock_run:
            mg.cmd_bench_run(args)
        cmd = mock_run.call_args[0][0]
        assert "--elastic-strain-max" in cmd
        assert "0.05" in cmd

    def test_uq_params(self):
        args = SimpleNamespace(
            output="o", reports="r", mode="canary",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=100, uq_seed=42,
        )
        with patch.object(mg, "_run", return_value=0) as mock_run:
            mg.cmd_bench_run(args)
        cmd = mock_run.call_args[0][0]
        assert "--uq-samples" in cmd
        assert "100" in cmd
        assert "--uq-seed" in cmd
        assert "42" in cmd

    def test_nonzero_return(self):
        args = SimpleNamespace(
            output="o", reports="r", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "_run", return_value=1):
            assert mg.cmd_bench_run(args) == 1


# ---------------------------------------------------------------------------
# 16-20: cmd_claim_run_mtr1
# ---------------------------------------------------------------------------

class TestCmdClaimRunMtr1:
    def test_bench_failure_returns_early(self):
        args = SimpleNamespace(
            output="o", reports="r", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "cmd_bench_run", return_value=1):
            assert mg.cmd_claim_run_mtr1(args) == 1

    def test_missing_summary_returns_one(self, tmp_path):
        args = SimpleNamespace(
            output=str(tmp_path), reports="r", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "cmd_bench_run", return_value=0):
            assert mg.cmd_claim_run_mtr1(args) == 1

    def test_success_prints_metagenesis(self, tmp_path, capsys):
        summary = {"metagenesis": {"claim": "MTR-1", "pass": True}}
        (tmp_path / "bench01_summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )
        args = SimpleNamespace(
            output=str(tmp_path), reports="r", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "cmd_bench_run", return_value=0):
            rc = mg.cmd_claim_run_mtr1(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert "MTR-1" in out

    def test_empty_metagenesis(self, tmp_path, capsys):
        summary = {"metagenesis": {}}
        (tmp_path / "bench01_summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )
        args = SimpleNamespace(
            output=str(tmp_path), reports="r", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "cmd_bench_run", return_value=0):
            rc = mg.cmd_claim_run_mtr1(args)
        assert rc == 0

    def test_returns_zero_on_success(self, tmp_path):
        summary = {"metagenesis": {"claim": "MTR-1"}}
        (tmp_path / "bench01_summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )
        args = SimpleNamespace(
            output=str(tmp_path), reports="r", mode="both",
            dataset_relpath=None, elastic_strain_max=None,
            uq_samples=None, uq_seed=None,
        )
        with patch.object(mg, "cmd_bench_run", return_value=0):
            assert mg.cmd_claim_run_mtr1(args) == 0


# ---------------------------------------------------------------------------
# 21-25: main() argparse
# ---------------------------------------------------------------------------

class TestMgMain:
    def test_steward_audit_subcommand(self):
        with patch("sys.argv", ["mg", "steward", "audit"]):
            with patch.object(mg, "cmd_steward_audit", return_value=0) as mock_fn:
                rc = mg.main()
        assert rc == 0
        mock_fn.assert_called_once()

    def test_pack_verify_subcommand(self):
        with patch("sys.argv", ["mg", "pack", "verify", "--pack", "/tmp/b"]):
            with patch.object(mg, "_verify_pack", return_value=(True, "PASS", {})):
                rc = mg.main()
        assert rc == 0

    def test_verify_top_subcommand(self):
        with patch("sys.argv", ["mg", "verify", "--pack", "/tmp/b"]):
            with patch.object(mg, "_verify_pack", return_value=(True, "PASS", {})):
                rc = mg.main()
        assert rc == 0

    def test_verify_chain_subcommand(self):
        with patch("sys.argv", ["mg", "verify-chain", "/tmp/a", "/tmp/b"]):
            with patch.object(mg, "_verify_chain", return_value=(True, "CHAIN PASS", {"errors": []})):
                rc = mg.main()
        assert rc == 0

    def test_no_subcommand_exits(self):
        with patch("sys.argv", ["mg"]):
            with pytest.raises(SystemExit):
                mg.main()
