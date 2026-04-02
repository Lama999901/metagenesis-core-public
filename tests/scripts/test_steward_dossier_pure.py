"""Tests for scripts/steward_dossier.py -- pure parsing + file I/O (15 tests)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pytest
from steward_dossier import _parse_claim_sections, _dossier_content, build_dossiers

# ---------------------------------------------------------------------------
# Sample markdown for testing
# ---------------------------------------------------------------------------
SINGLE_CLAIM = """\
# Claims Index

## MTR-1 Aluminum Calibration

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **job_kind** | materials |
| **reproduction** | deterministic |
| **V&V thresholds** | rel_err <= 0.01 |
| **notes: canary vs normal** | normal |
"""

MULTI_CLAIMS = """\
# Claims Index

## MTR-1 Aluminum

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **job_kind** | materials |

## PHYS-01 Boltzmann

| Field | Value |
|-------|--------|
| **claim_id** | PHYS-01 |
| **job_kind** | physics |
"""

NO_CLAIM_ID = """\
## Some Section

| Field | Value |
|-------|--------|
| **description** | no claim_id here |
"""


# ---- _parse_claim_sections ---------------------------------------------------

class TestParseClaimSections:
    def test_empty_text(self):
        assert _parse_claim_sections("") == []

    def test_single_claim(self):
        result = _parse_claim_sections(SINGLE_CLAIM)
        assert len(result) == 1
        assert result[0]["claim_id"] == "MTR-1"

    def test_multiple_claims(self):
        result = _parse_claim_sections(MULTI_CLAIMS)
        assert len(result) == 2
        ids = [c["claim_id"] for c in result]
        assert "MTR-1" in ids
        assert "PHYS-01" in ids

    def test_no_claim_id_skipped(self):
        result = _parse_claim_sections(NO_CLAIM_ID)
        assert result == []

    def test_extracts_job_kind(self):
        result = _parse_claim_sections(SINGLE_CLAIM)
        assert result[0]["job_kind"] == "materials"

    def test_returns_list(self):
        result = _parse_claim_sections(SINGLE_CLAIM)
        assert isinstance(result, list)
        assert isinstance(result[0], dict)


# ---- _dossier_content --------------------------------------------------------

class TestDossierContent:
    def _claim(self, **overrides):
        base = {"claim_id": "MTR-1", "job_kind": "materials", "reproduction": "det"}
        base.update(overrides)
        return base

    def test_contains_claim_id(self):
        text = _dossier_content(self._claim())
        assert "MTR-1" in text

    def test_is_string(self):
        assert isinstance(_dossier_content(self._claim()), str)

    def test_has_table(self):
        text = _dossier_content(self._claim())
        assert "| Field | Value |" in text

    def test_missing_fields_no_crash(self):
        text = _dossier_content({"claim_id": "X"})
        assert "X" in text

    def test_job_kind_in_output(self):
        text = _dossier_content(self._claim(job_kind="physics"))
        assert "physics" in text


# ---- build_dossiers (file I/O) -----------------------------------------------

class TestBuildDossiers:
    def test_creates_files(self, tmp_path):
        idx = tmp_path / "index.md"
        idx.write_text(SINGLE_CLAIM, encoding="utf-8")
        out = tmp_path / "out"
        paths = build_dossiers(out, index_path=idx)
        assert len(paths) == 1
        assert paths[0].exists()

    def test_returns_paths(self, tmp_path):
        idx = tmp_path / "index.md"
        idx.write_text(MULTI_CLAIMS, encoding="utf-8")
        out = tmp_path / "out"
        paths = build_dossiers(out, index_path=idx)
        assert len(paths) == 2
        assert all(isinstance(p, Path) for p in paths)

    def test_raises_no_index(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            build_dossiers(tmp_path / "out", index_path=tmp_path / "missing.md")

    def test_creates_output_dir(self, tmp_path):
        idx = tmp_path / "index.md"
        idx.write_text(SINGLE_CLAIM, encoding="utf-8")
        out = tmp_path / "nested" / "dir"
        build_dossiers(out, index_path=idx)
        assert out.is_dir()
