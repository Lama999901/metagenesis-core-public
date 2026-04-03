#!/usr/bin/env python3
"""Extended coverage tests for backend/ledger/models.py -- 15 tests.

Targets from_dict, to_dict, edge cases for ArtifactReference and LedgerEntry.
"""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backend.ledger.models import (
    validate_sha256,
    validate_iso8601,
    ArtifactReference,
    LedgerEntry,
)

VALID_SHA = "a" * 64
VALID_TS = "2026-03-31T12:00:00+00:00"


def _base_entry(**overrides):
    """Minimal valid LedgerEntry kwargs."""
    base = dict(
        trace_id="test-001",
        created_at=VALID_TS,
        phase=1,
        actor="agent",
        action="verify",
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1-3: from_dict basic
# ---------------------------------------------------------------------------

class TestFromDictBasic:
    def test_basic_roundtrip(self):
        entry = LedgerEntry(**_base_entry())
        d = entry.to_dict()
        entry2 = LedgerEntry.from_dict(d)
        assert entry2.trace_id == "test-001"
        assert entry2.phase == 1

    def test_from_dict_with_artifacts(self):
        arts = [{"path": "file.txt", "sha256": VALID_SHA}]
        d = _base_entry(artifacts=arts)
        entry = LedgerEntry.from_dict(d)
        assert len(entry.artifacts) == 1
        assert entry.artifacts[0].path == "file.txt"

    def test_roundtrip_preserves_all_fields(self):
        entry = LedgerEntry(**_base_entry(
            inputs={"key": "val"},
            outputs={"res": 42},
            meta={"tag": "test"},
            legal_sig_refs=["ref1"],
        ))
        d = entry.to_dict()
        entry2 = LedgerEntry.from_dict(d)
        assert entry2.inputs == {"key": "val"}
        assert entry2.outputs == {"res": 42}
        assert entry2.meta == {"tag": "test"}
        assert entry2.legal_sig_refs == ["ref1"]


# ---------------------------------------------------------------------------
# 4-6: from_dict edge cases
# ---------------------------------------------------------------------------

class TestFromDictEdgeCases:
    def test_missing_optional_fields_uses_defaults(self):
        d = {
            "trace_id": "x",
            "created_at": VALID_TS,
            "phase": 0,
            "actor": "bot",
            "action": "scan",
        }
        entry = LedgerEntry.from_dict(d)
        assert entry.inputs == {}
        assert entry.artifacts == []
        assert entry.meta == {}

    def test_empty_artifacts_list(self):
        d = _base_entry(artifacts=[])
        entry = LedgerEntry.from_dict(d)
        assert entry.artifacts == []

    def test_artifacts_already_objects(self):
        ref = ArtifactReference(path="f.bin", sha256=VALID_SHA)
        d = _base_entry(artifacts=[ref])
        entry = LedgerEntry.from_dict(d)
        assert entry.artifacts[0].path == "f.bin"


# ---------------------------------------------------------------------------
# 7-9: ArtifactReference edge cases
# ---------------------------------------------------------------------------

class TestArtifactReferenceEdgeCases:
    def test_optional_flag(self):
        ref = ArtifactReference(path="opt.txt", sha256=VALID_SHA, optional=True)
        assert ref.optional is True

    def test_note_field(self):
        ref = ArtifactReference(path="n.txt", sha256=VALID_SHA, note="important")
        assert ref.note == "important"
        d = ref.to_dict()
        assert d["note"] == "important"

    def test_whitespace_path_stripped(self):
        ref = ArtifactReference(path="  spaced.txt  ", sha256=VALID_SHA)
        assert ref.path == "spaced.txt"


# ---------------------------------------------------------------------------
# 10-12: LedgerEntry validation edge cases
# ---------------------------------------------------------------------------

class TestLedgerEntryValidation:
    def test_phase_boundary_zero(self):
        entry = LedgerEntry(**_base_entry(phase=0))
        assert entry.phase == 0

    def test_phase_boundary_999(self):
        entry = LedgerEntry(**_base_entry(phase=999))
        assert entry.phase == 999

    def test_artifact_dict_auto_converts(self):
        entry = LedgerEntry(**_base_entry(
            artifacts=[{"path": "auto.txt", "sha256": VALID_SHA}]
        ))
        assert isinstance(entry.artifacts[0], ArtifactReference)
        assert entry.artifacts[0].path == "auto.txt"


# ---------------------------------------------------------------------------
# 13-15: to_dict tests
# ---------------------------------------------------------------------------

class TestToDict:
    def test_all_keys_present(self):
        entry = LedgerEntry(**_base_entry())
        d = entry.to_dict()
        expected_keys = {
            "trace_id", "created_at", "phase", "actor", "action",
            "inputs", "outputs", "artifacts", "legal_sig_refs", "meta",
        }
        assert set(d.keys()) == expected_keys

    def test_artifacts_serialized(self):
        entry = LedgerEntry(**_base_entry(
            artifacts=[{"path": "f.bin", "sha256": VALID_SHA}]
        ))
        d = entry.to_dict()
        assert isinstance(d["artifacts"], list)
        assert isinstance(d["artifacts"][0], dict)
        assert d["artifacts"][0]["path"] == "f.bin"

    def test_meta_preserved(self):
        entry = LedgerEntry(**_base_entry(meta={"env": "prod", "ver": 2}))
        d = entry.to_dict()
        assert d["meta"]["env"] == "prod"
        assert d["meta"]["ver"] == 2
