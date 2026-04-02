"""Tests for scripts/agent_audit.py — 25 tests covering helpers and checks."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_audit


# ── load_config ─────────────────────────────────────────────────────────────

class TestLoadConfig:
    def test_returns_dict_when_file_exists(self, tmp_path):
        cfg = {"physical_anchor_constants": {}}
        (tmp_path / "reports").mkdir()
        (tmp_path / "reports" / "audit_config.json").write_text(
            json.dumps(cfg), encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.load_config()
        assert isinstance(result, dict)
        assert "physical_anchor_constants" in result

    def test_returns_none_when_missing(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.load_config()
        assert result is None


# ── load_manifest ───────────────────────────────────────────────────────────

class TestLoadManifest:
    def test_returns_dict_when_file_exists(self, tmp_path):
        data = {"version": "0.8.0", "test_count": 608}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.load_manifest()
        assert result["version"] == "0.8.0"

    def test_returns_empty_dict_when_missing(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.load_manifest()
        assert result == {}


# ── build_jobkind_to_file_map ───────────────────────────────────────────────

class TestBuildJobkindToFileMap:
    def test_finds_job_kind(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "mtr1_calibration.py").write_text(
            'JOB_KIND = "mtr1_calibration"\n', encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.build_jobkind_to_file_map()
        assert "mtr1_calibration" in result

    def test_empty_when_no_dir(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.build_jobkind_to_file_map()
        assert result == {}

    def test_multiple_files(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "a.py").write_text('JOB_KIND = "alpha"\n', encoding="utf-8")
        (prog / "b.py").write_text('JOB_KIND = "beta"\n', encoding="utf-8")
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.build_jobkind_to_file_map()
        assert len(result) == 2
        assert "alpha" in result
        assert "beta" in result


# ── get_job_kind_for_claim ──────────────────────────────────────────────────

class TestGetJobKindForClaim:
    def test_extracts_job_kind(self):
        content = "## MTR-1\nSome text job_kind: `mtr1_calibration`\n"
        assert agent_audit.get_job_kind_for_claim("MTR-1", content) == "mtr1_calibration"

    def test_returns_none_when_missing(self):
        assert agent_audit.get_job_kind_for_claim("MTR-99", "no match here") is None


# ── find_test_files_for_claim ───────────────────────────────────────────────

class TestFindTestFilesForClaim:
    def test_finds_matching_test(self, tmp_path):
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_mtr1.py").write_text(
            "def test_pass(): pass\n", encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.find_test_files_for_claim("MTR-1", "mtr1_calibration")
        assert len(result) >= 1

    def test_empty_when_no_tests_dir(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.find_test_files_for_claim("MTR-1", None)
        assert result == []


# ── check_innovations ───────────────────────────────────────────────────────

class TestCheckInnovations:
    def test_true_when_all_present(self, tmp_path):
        innovations = [f"inn_{i}" for i in range(8)]
        manifest = {"verified_innovations": innovations}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        test_file = tmp_path / "tests" / "test_inn.py"
        test_file.parent.mkdir(parents=True)
        test_file.write_text("def test_a(): pass\n", encoding="utf-8")

        inn_map = {inn: "tests/test_inn.py" for inn in innovations}
        config = {"innovations_test_map": inn_map}

        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_innovations(config)
        assert result is True

    def test_false_when_test_missing(self, tmp_path):
        manifest = {"verified_innovations": ["inn_0"] * 8}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        config = {"innovations_test_map": {"inn_0": "tests/nonexistent.py"}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_innovations(config)
        assert result is False


# ── check_demo_scenarios ────────────────────────────────────────────────────

class TestCheckDemoScenarios:
    def test_false_when_no_dir(self, tmp_path):
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_demo_scenarios({})
        assert result is False

    def test_true_when_valid_scenario(self, tmp_path):
        demo = tmp_path / "demos" / "client_scenarios" / "01_ml"
        demo.mkdir(parents=True)
        (demo / "run_scenario.py").write_text("pass", encoding="utf-8")
        report = {"manifest_ok": True, "semantic_ok": True, "errors": []}
        (demo / "VERIFY_REPORT.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        (demo / "README.md").write_text("FDA compliance demo", encoding="utf-8")

        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_demo_scenarios({})
        assert result is True

    def test_false_when_verify_fails(self, tmp_path):
        demo = tmp_path / "demos" / "client_scenarios" / "01_ml"
        demo.mkdir(parents=True)
        (demo / "run_scenario.py").write_text("pass", encoding="utf-8")
        report = {"manifest_ok": False, "semantic_ok": True, "errors": []}
        (demo / "VERIFY_REPORT.json").write_text(
            json.dumps(report), encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_demo_scenarios({})
        assert result is False


# ── check_triple_sync ───────────────────────────────────────────────────────

class TestCheckTripleSync:
    def test_true_when_synced(self, tmp_path):
        manifest = {"version": "v0.8.0", "test_count": 608}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (tmp_path / "README.md").write_text(
            "We have 608 tests passing. Version v0.8.0.", encoding="utf-8"
        )
        (tmp_path / "index.html").write_text(
            '<span id="cn2">608</span>', encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_triple_sync()
        assert result is True

    def test_false_when_mismatch(self, tmp_path):
        manifest = {"version": "v0.8.0", "test_count": 608}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (tmp_path / "README.md").write_text(
            "We have 500 tests passing. Version v0.8.0.", encoding="utf-8"
        )
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_triple_sync()
        assert result is False


# ── check_patent_integrity ──────────────────────────────────────────────────

class TestCheckPatentIntegrity:
    def _setup_manifest(self, tmp_path, **overrides):
        data = {
            "ppa_number": "63/996,819",
            "ppa_filed": "2026-03-05",
            "verified_innovations": [f"i{i}" for i in range(8)],
        }
        data.update(overrides)
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        faults = tmp_path / "reports"
        faults.mkdir(parents=True, exist_ok=True)
        (faults / "known_faults.yaml").write_text(
            "SCOPE_001:\n  tamper-evident provenance\n", encoding="utf-8"
        )
        return data

    def test_true_when_valid(self, tmp_path):
        self._setup_manifest(tmp_path)
        config = {"patent": {"ppa_number": "63/996,819",
                              "fail_days_before_deadline": 30,
                              "warn_days_before_deadline": 90}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_patent_integrity(config)
        assert result is True

    def test_false_wrong_ppa(self, tmp_path):
        self._setup_manifest(tmp_path)
        config = {"patent": {"ppa_number": "WRONG"}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_patent_integrity(config)
        assert result is False

    def test_false_wrong_innovations_count(self, tmp_path):
        self._setup_manifest(tmp_path, verified_innovations=["only_one"])
        config = {"patent": {"ppa_number": "63/996,819",
                              "fail_days_before_deadline": 30,
                              "warn_days_before_deadline": 90}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_patent_integrity(config)
        assert result is False

    def test_false_no_faults_file(self, tmp_path):
        data = {
            "ppa_number": "63/996,819",
            "ppa_filed": "2026-03-05",
            "verified_innovations": [f"i{i}" for i in range(8)],
        }
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        config = {"patent": {"ppa_number": "63/996,819",
                              "fail_days_before_deadline": 30,
                              "warn_days_before_deadline": 90}}
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_patent_integrity(config)
        assert result is False


# ── check_physical_anchors ──────────────────────────────────────────────────

class TestCheckPhysicalAnchors:
    def test_true_when_constant_matches(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "phys01_boltzmann.py").write_text(
            'JOB_KIND = "phys01_boltzmann"\nBOLTZMANN_K = 1.380649e-23\n',
            encoding="utf-8",
        )
        manifest = {"active_claims": ["PHYS-01"]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (tmp_path / "tests" / "steward").mkdir(parents=True)
        (tmp_path / "tests" / "steward" / "test_cross_claim_chain.py").write_text(
            "def test_chain(): pass\n", encoding="utf-8"
        )
        config = {
            "physical_anchor_constants": {
                "PHYS-01": {
                    "file": "backend/progress/phys01_boltzmann.py",
                    "constant_name": "BOLTZMANN_K",
                    "expected_value": 1.380649e-23,
                    "tolerance": 1e-30,
                    "anchor_type": "SI 2019 exact",
                }
            }
        }
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_physical_anchors(config)
        assert result is True

    def test_false_file_not_found(self, tmp_path):
        (tmp_path / "system_manifest.json").write_text(
            json.dumps({"active_claims": []}), encoding="utf-8"
        )
        (tmp_path / "tests" / "steward").mkdir(parents=True)
        (tmp_path / "tests" / "steward" / "test_cross_claim_chain.py").write_text(
            "def test_chain(): pass\n", encoding="utf-8"
        )
        config = {
            "physical_anchor_constants": {
                "PHYS-01": {
                    "file": "backend/progress/nonexistent.py",
                    "constant_name": "BOLTZMANN_K",
                    "expected_value": 1.380649e-23,
                    "tolerance": 1e-30,
                    "anchor_type": "SI 2019 exact",
                }
            }
        }
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_physical_anchors(config)
        assert result is False

    def test_false_wrong_constant(self, tmp_path):
        prog = tmp_path / "backend" / "progress"
        prog.mkdir(parents=True)
        (prog / "phys01_boltzmann.py").write_text(
            'JOB_KIND = "phys01_boltzmann"\nBOLTZMANN_K = 9.99e-23\n',
            encoding="utf-8",
        )
        manifest = {"active_claims": ["PHYS-01"]}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (tmp_path / "tests" / "steward").mkdir(parents=True)
        (tmp_path / "tests" / "steward" / "test_cross_claim_chain.py").write_text(
            "def test_chain(): pass\n", encoding="utf-8"
        )
        config = {
            "physical_anchor_constants": {
                "PHYS-01": {
                    "file": "backend/progress/phys01_boltzmann.py",
                    "constant_name": "BOLTZMANN_K",
                    "expected_value": 1.380649e-23,
                    "tolerance": 1e-30,
                    "anchor_type": "SI 2019 exact",
                }
            }
        }
        with patch("agent_audit.REPO_ROOT", tmp_path):
            result = agent_audit.check_physical_anchors(config)
        assert result is False
