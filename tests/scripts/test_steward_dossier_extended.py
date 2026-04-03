#!/usr/bin/env python3
"""Extended coverage tests for scripts/steward_dossier.py -- 10 tests."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from steward_dossier import _read, _parse_claim_sections, _dossier_content, build_dossiers


# -- _read ---------------------------------------------------------------------

class TestRead:
    def test_returns_string(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("hello world", encoding="utf-8")
        result = _read(f)
        assert isinstance(result, str)
        assert result == "hello world"

    def test_reads_utf8(self, tmp_path):
        f = tmp_path / "unicode.md"
        f.write_text("alpha beta gamma", encoding="utf-8")
        result = _read(f)
        assert "alpha" in result


# -- _parse_claim_sections extended --------------------------------------------

class TestParseClaimSectionsExtended:
    def test_empty_returns_empty(self):
        assert _parse_claim_sections("") == []

    def test_one_claim_extracted(self):
        text = """# Index

## MTR-1 Aluminum

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **job_kind** | materials |
"""
        result = _parse_claim_sections(text)
        assert len(result) == 1
        assert result[0]["claim_id"] == "MTR-1"

    def test_extracts_job_kind(self):
        text = """## PHYS-01

| Field | Value |
|-------|--------|
| **claim_id** | PHYS-01 |
| **job_kind** | physics |
"""
        result = _parse_claim_sections(text)
        assert result[0]["job_kind"] == "physics"

    def test_multiple_claims(self):
        text = """## A

| Field | Value |
|-------|--------|
| **claim_id** | CLAIM-A |

## B

| Field | Value |
|-------|--------|
| **claim_id** | CLAIM-B |
"""
        result = _parse_claim_sections(text)
        assert len(result) == 2
        ids = {c["claim_id"] for c in result}
        assert "CLAIM-A" in ids
        assert "CLAIM-B" in ids


# -- _dossier_content extended -------------------------------------------------

class TestDossierContentExtended:
    def test_has_heading(self):
        claim = {"claim_id": "MTR-1", "job_kind": "materials"}
        content = _dossier_content(claim)
        assert content.startswith("# Claim Dossier:")

    def test_has_table(self):
        claim = {"claim_id": "MTR-1", "job_kind": "materials"}
        content = _dossier_content(claim)
        assert "| Field | Value |" in content

    def test_includes_claim_id_in_table(self):
        claim = {"claim_id": "PHYS-02", "job_kind": "physics"}
        content = _dossier_content(claim)
        assert "PHYS-02" in content


# -- build_dossiers extended ---------------------------------------------------

class TestBuildDossiersExtended:
    def test_missing_index_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            build_dossiers(tmp_path / "out", index_path=tmp_path / "missing.md")

    def test_returns_list_of_paths(self, tmp_path):
        idx = tmp_path / "index.md"
        idx.write_text("""## A

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **job_kind** | materials |

## B

| Field | Value |
|-------|--------|
| **claim_id** | PHYS-01 |
| **job_kind** | physics |
""", encoding="utf-8")
        out = tmp_path / "dossiers"
        result = build_dossiers(out, index_path=idx)
        assert isinstance(result, list)
        assert all(isinstance(p, Path) for p in result)
        assert len(result) == 2
        for p in result:
            assert p.exists()
