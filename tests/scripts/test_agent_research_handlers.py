#!/usr/bin/env python3
"""Coverage tests for agent_research.py task handlers -- 20 tests.

Targets execute_task dispatch + execute_task_001 through _014 handlers,
weekly_report(), and main(). All handlers do heavy I/O so we mock
REPO_ROOT and run() throughout.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_research as ar


def _make_task(task_id="TASK-001"):
    """Create a minimal task dict for dispatch."""
    return {
        "id": task_id,
        "title": "Test task",
        "status": "PENDING",
        "priority": "P1",
        "output": "reports/test.md",
        "description": "Test description",
    }


def _setup_repo(tmp_path):
    """Create minimal repo structure needed by handlers."""
    # tests/ dir with a test file
    tests_dir = tmp_path / "tests" / "steward"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_cert02_pack_includes_evidence_and_semantic_verify.py").write_text(
        "def test_example(): pass\n", encoding="utf-8"
    )
    (tests_dir / "test_cert03_step_chain_verify.py").write_text(
        "def test_step(): pass\n", encoding="utf-8"
    )
    (tests_dir / "test_cert09_ed25519_attacks.py").write_text(
        "def test_ed(): pass\n", encoding="utf-8"
    )
    (tests_dir / "test_cert10_temporal_attacks.py").write_text(
        '"""Attack A -- replay"""\ndef test_temporal(): pass\n', encoding="utf-8"
    )
    (tests_dir / "test_cert11_coordinated_attack.py").write_text(
        "def test_coord(): pass\n", encoding="utf-8"
    )

    # backend/progress with claim files
    progress_dir = tmp_path / "backend" / "progress"
    progress_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "mtr1_calibration.py", "mtr2_thermal_conductivity.py",
        "mtr3_thermal_multilayer.py", "sysid1_arx_calibration.py",
        "datapipe1_quality_certificate.py", "drift_monitor.py",
        "mlbench1_accuracy_certificate.py", "dtfem1_displacement_verification.py",
        "mlbench2_regression_certificate.py", "mlbench3_timeseries_certificate.py",
        "pharma1_admet_certificate.py", "finrisk1_var_certificate.py",
        "dtsensor1_iot_certificate.py", "dtcalib1_convergence_certificate.py",
        "runner.py",
    ]:
        content = (
            'JOB_KIND = "test_kind"\n'
            'ALGORITHM_VERSION = "v1"\n'
            'METHOD = "test_method"\n'
            'def _hash_step(s,d,p): pass\n'
            'threshold = 0.03\n'
        )
        (progress_dir / name).write_text(content, encoding="utf-8")

    # scripts/
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    (scripts_dir / "mg.py").write_text(
        'add_parser("steward")\nadd_parser("pack")\n', encoding="utf-8"
    )
    (scripts_dir / "mg_temporal.py").write_text(
        'def create_temporal_commitment(root): pass\n'
        'def verify_temporal_commitment(bundle): pass\n',
        encoding="utf-8",
    )

    # Key docs
    (tmp_path / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    (tmp_path / "paper.md").write_text(
        "# Paper\n## Active Claims\n## AI Usage\nword " * 50, encoding="utf-8"
    )
    (tmp_path / "paper.bib").write_text(
        '@article{test2026,\n  title={Test},\n}\n', encoding="utf-8"
    )
    (tmp_path / "index.html").write_text(
        '<html>511 tests PASS 14 claims 5 layers 8 innovations v0.5.0</html>',
        encoding="utf-8",
    )
    (tmp_path / "system_manifest.json").write_text(
        json.dumps({"version": "0.8.0", "test_count": 1273}), encoding="utf-8"
    )
    (tmp_path / "AGENT_TASKS.md").write_text(
        "# Agent Tasks\n\n### TASK-001\n- **Title:** Test\n- **Status:** PENDING\n"
        "- **Priority:** P1\n- **Output:** x\n- **Description:** x\n",
        encoding="utf-8",
    )

    # .agent_memory for weekly_report
    mem_dir = tmp_path / ".agent_memory"
    mem_dir.mkdir(exist_ok=True)
    (mem_dir / "patterns.json").write_text(
        json.dumps({"stale": {"count": 3, "fix_hint": "fix it"}}), encoding="utf-8"
    )

    # reports dir
    (tmp_path / "reports").mkdir(exist_ok=True)

    return tmp_path


def _mock_run(output="", returncode=0):
    """Return a mock for ar.run that returns (output, returncode)."""
    return lambda *a, **kw: (output, returncode)


# -- execute_task dispatch ---------------------------------------------------

class TestExecuteTaskDispatch:
    def test_known_handler_returns_string(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run("PASS", 0)):
            result = ar.execute_task(_make_task("TASK-001"))
        assert isinstance(result, str)

    def test_unknown_handler(self):
        result = ar.execute_task(_make_task("TASK-999"))
        assert "No handler for TASK-999" in result

    def test_returns_string_type(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task(_make_task("TASK-002"))
        assert isinstance(result, str)


# -- execute_task_001 (audit test coverage) ----------------------------------

class TestExecuteTask001:
    def test_runs_without_error(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_001()
        assert isinstance(result, str)
        assert "Coverage" in result or "Claim" in result or "claim" in result.lower()

    def test_mentions_weakest_claim(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_001()
        assert "Weakest" in result


# -- execute_task_002 through _005 ------------------------------------------

class TestExecuteTask002To005:
    def test_task_002_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_002()
        assert isinstance(result, str)

    def test_task_003_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run("All critical documentation is current", 0)):
            result = ar.execute_task_003()
        assert isinstance(result, str)

    def test_task_004_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_004()
        assert isinstance(result, str)

    def test_task_005_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_005()
        assert isinstance(result, str)


# -- execute_task_006 through _010 ------------------------------------------

class TestExecuteTask006To010:
    def test_task_006_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_006()
        assert isinstance(result, str)

    def test_task_007_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_007()
        assert isinstance(result, str)

    def test_task_008_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_008()
        assert isinstance(result, str)

    def test_task_009_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_009()
        assert isinstance(result, str)

    def test_task_010_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_010()
        assert isinstance(result, str)


# -- execute_task_011 through _014 ------------------------------------------

class TestExecuteTask011To014:
    def test_task_011_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_011()
        assert isinstance(result, str)
        # Handler writes a test file -- verify it was created
        assert (repo / "tests" / "steward" / "test_cert_adv_sysid01_semantic.py").exists()

    def test_task_012_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_012()
        assert isinstance(result, str)
        assert (repo / "tests" / "steward" / "test_cert_adv_multichain.py").exists()

    def test_task_013_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_013()
        assert isinstance(result, str)

    def test_task_014_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()):
            result = ar.execute_task_014()
        assert isinstance(result, str)
        assert (repo / "tests" / "steward" / "test_cert_adv_temporal_pure.py").exists()


# -- weekly_report + main ---------------------------------------------------

class TestWeeklyReportAndMain:
    def test_weekly_report_runs(self, tmp_path):
        repo = _setup_repo(tmp_path)
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run("19/19 CHECKS PASS", 0)):
            result = ar.weekly_report()
        assert result.exists()
        assert "WEEKLY_REPORT" in result.name

    def test_main_no_pending(self, tmp_path):
        repo = _setup_repo(tmp_path)
        tasks_file = repo / "AGENT_TASKS.md"
        tasks_file.write_text(
            "# Tasks\n\n### TASK-001\n- **Title:** Done\n- **Status:** DONE\n"
            "- **Priority:** P1\n- **Output:** x\n- **Description:** x\n",
            encoding="utf-8",
        )
        with patch.object(ar, "REPO_ROOT", repo), \
             patch.object(ar, "run", _mock_run()), \
             pytest.raises(SystemExit) as exc_info:
            ar.main()
        assert exc_info.value.code == 0
