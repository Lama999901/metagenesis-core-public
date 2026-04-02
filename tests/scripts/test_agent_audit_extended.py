#!/usr/bin/env python3
"""Extended coverage tests for scripts/agent_audit.py -- 20 tests.

Focuses on edge cases and error paths NOT covered by test_agent_audit_coverage.py.
"""

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_audit as aa


# -- load_config edge cases ---------------------------------------------------

class TestLoadConfigEdge:
    def test_invalid_json_raises(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "audit_config.json").write_text("{bad json", encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            with pytest.raises(json.JSONDecodeError):
                aa.load_config()

    def test_empty_config_returns_empty_dict(self, tmp_path):
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "audit_config.json").write_text("{}", encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.load_config()
        assert result == {}


# -- load_manifest edge cases -------------------------------------------------

class TestLoadManifestEdge:
    def test_invalid_json_raises(self, tmp_path):
        (tmp_path / "system_manifest.json").write_text("{bad", encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            with pytest.raises(json.JSONDecodeError):
                aa.load_manifest()

    def test_empty_manifest_returns_empty_dict(self, tmp_path):
        (tmp_path / "system_manifest.json").write_text("{}", encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.load_manifest()
        assert result == {}


# -- build_jobkind_to_file_map edge cases ------------------------------------

class TestBuildJobkindMapEdge:
    def test_skips_files_without_job_kind(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "utils.py").write_text("x = 1\n", encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.build_jobkind_to_file_map()
        assert result == {}

    def test_single_quotes_job_kind(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "mtr1.py").write_text("JOB_KIND = 'mtr1_calibration'\n", encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.build_jobkind_to_file_map()
        assert "mtr1_calibration" in result

    def test_double_quotes_job_kind(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "mtr2.py").write_text('JOB_KIND = "mtr2_thermal"\n', encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.build_jobkind_to_file_map()
        assert "mtr2_thermal" in result


# -- get_job_kind_for_claim edge cases ----------------------------------------

class TestGetJobKindForClaimEdge:
    def test_returns_none_for_unknown_claim(self):
        assert aa.get_job_kind_for_claim("FAKE-99", "") is None

    def test_extracts_from_markdown(self):
        content = "## MTR-1\nSome info job_kind: `mtr1_calibration`\n"
        assert aa.get_job_kind_for_claim("MTR-1", content) == "mtr1_calibration"

    def test_case_insensitive_job_kind_label(self):
        content = "## MTR-1\nSome info Job_Kind: `mtr1_calibration`\n"
        assert aa.get_job_kind_for_claim("MTR-1", content) == "mtr1_calibration"


# -- find_test_files_for_claim edge cases -------------------------------------

class TestFindTestFilesEdge:
    def test_no_tests_dir(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.find_test_files_for_claim("MTR-1", None)
        assert result == []

    def test_matches_by_content(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_general.py").write_text(
            '"""Tests for MTR-1."""\ndef test_mtr1_pass(): pass\n',
            encoding="utf-8",
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.find_test_files_for_claim("MTR-1", None)
        assert len(result) >= 1

    def test_counts_test_functions(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        content = "def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n"
        (tests / "test_mtr1.py").write_text(content, encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.find_test_files_for_claim("MTR-1", "mtr1_calibration")
        assert len(result) >= 1
        # result is list of (path, count) tuples
        assert result[0][1] == 3


# -- check_innovations edge cases --------------------------------------------

class TestCheckInnovationsEdge:
    def test_missing_innovation_test_file(self, tmp_path):
        manifest = {"verified_innovations": [f"inn_{i}" for i in range(8)]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        config = {"innovations_test_map": {"inn_0": "tests/nonexistent.py"}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_innovations(config)
        assert result is False

    def test_zero_test_functions(self, tmp_path):
        manifest = {"verified_innovations": [f"inn_{i}" for i in range(8)]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_inn.py").write_text("# no test functions\nx = 1\n", encoding="utf-8")
        config = {"innovations_test_map": {"inn_0": "tests/test_inn.py"}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_innovations(config)
        assert result is False

    def test_innovation_not_in_config_is_advisory(self, tmp_path):
        manifest = {"verified_innovations": [f"inn_{i}" for i in range(8)]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        # Empty innovations_test_map -- all are advisory (no mapping)
        config = {"innovations_test_map": {}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_innovations(config)
        # Advisory only = still True
        assert result is True


# -- check_demo_scenarios edge cases ------------------------------------------

class TestCheckDemoScenariosEdge:
    def test_no_demos_dir(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_demo_scenarios({})
        assert result is False

    def test_scenario_missing_verify_report(self, tmp_path):
        demo = tmp_path / "demos" / "client_scenarios" / "01_ml"
        demo.mkdir(parents=True)
        (demo / "run_scenario.py").write_text("pass", encoding="utf-8")
        # No VERIFY_REPORT.json
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_demo_scenarios({})
        assert result is False


# -- check_patent_integrity edge cases ----------------------------------------

class TestCheckPatentEdge:
    def test_missing_faults_file(self, tmp_path):
        data = {
            "ppa_number": "63/996,819",
            "ppa_filed": "2026-03-05",
            "verified_innovations": [f"i{i}" for i in range(8)],
        }
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        # No known_faults.yaml
        config = {"patent": {"ppa_number": "63/996,819",
                              "fail_days_before_deadline": 30,
                              "warn_days_before_deadline": 90}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_patent_integrity(config)
        assert result is False

    def test_deadline_passed(self, tmp_path):
        data = {
            "ppa_number": "63/996,819",
            "ppa_filed": "2024-01-01",  # >1 year ago
            "verified_innovations": [f"i{i}" for i in range(8)],
        }
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        reports = tmp_path / "reports"
        reports.mkdir()
        (reports / "known_faults.yaml").write_text(
            "SCOPE_001:\n  tamper-evident provenance\n", encoding="utf-8"
        )
        config = {"patent": {"ppa_number": "63/996,819",
                              "fail_days_before_deadline": 30,
                              "warn_days_before_deadline": 90}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = aa.check_patent_integrity(config)
        assert result is False
