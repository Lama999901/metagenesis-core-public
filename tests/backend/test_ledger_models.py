"""Tests for backend/ledger/models.py -- dataclass validation (25 tests)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest
from backend.ledger.models import (
    validate_sha256,
    validate_iso8601,
    ArtifactReference,
    LedgerEntry,
)

VALID_SHA = "a" * 64
VALID_TS = "2026-03-31T12:00:00+00:00"


# ---- validate_sha256 --------------------------------------------------------

class TestValidateSha256:
    def test_valid_lowercase(self):
        assert validate_sha256("a" * 64) == "a" * 64

    def test_valid_uppercase_normalized(self):
        assert validate_sha256("A" * 64) == "a" * 64

    def test_mixed_case_normalized(self):
        h = "aAbBcCdD" * 8
        assert validate_sha256(h) == h.lower()

    def test_invalid_too_short(self):
        with pytest.raises(ValueError):
            validate_sha256("abc123")

    def test_invalid_too_long(self):
        with pytest.raises(ValueError):
            validate_sha256("a" * 65)

    def test_invalid_non_hex(self):
        with pytest.raises(ValueError):
            validate_sha256("g" * 64)

    def test_empty_string(self):
        with pytest.raises(ValueError):
            validate_sha256("")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_sha256(None)


# ---- validate_iso8601 --------------------------------------------------------

class TestValidateIso8601:
    def test_valid_with_offset(self):
        assert validate_iso8601("2026-03-31T12:00:00+00:00") == "2026-03-31T12:00:00+00:00"

    def test_valid_with_z(self):
        assert validate_iso8601("2026-03-31T12:00:00Z") == "2026-03-31T12:00:00Z"

    def test_valid_no_tz(self):
        assert validate_iso8601("2026-03-31T12:00:00") == "2026-03-31T12:00:00"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            validate_iso8601("not-a-date")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            validate_iso8601("")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            validate_iso8601(None)


# ---- ArtifactReference ------------------------------------------------------

class TestArtifactReference:
    def test_create_basic(self):
        a = ArtifactReference(path="file.txt", sha256=VALID_SHA)
        assert a.path == "file.txt"
        assert a.sha256 == VALID_SHA

    def test_strip_path(self):
        a = ArtifactReference(path="  file.txt  ", sha256=VALID_SHA)
        assert a.path == "file.txt"

    def test_normalize_sha(self):
        a = ArtifactReference(path="f.txt", sha256="A" * 64)
        assert a.sha256 == "a" * 64

    def test_empty_path_raises(self):
        with pytest.raises(ValueError):
            ArtifactReference(path="", sha256=VALID_SHA)

    def test_whitespace_path_raises(self):
        with pytest.raises(ValueError):
            ArtifactReference(path="   ", sha256=VALID_SHA)

    def test_bad_sha_raises(self):
        with pytest.raises(ValueError):
            ArtifactReference(path="f.txt", sha256="bad")

    def test_to_dict(self):
        a = ArtifactReference(path="f.txt", sha256=VALID_SHA, note="n")
        d = a.to_dict()
        assert d["path"] == "f.txt"
        assert d["sha256"] == VALID_SHA
        assert d["note"] == "n"
        assert d["optional"] is False


# ---- LedgerEntry -------------------------------------------------------------

class TestLedgerEntry:
    def _make(self, **overrides):
        defaults = dict(
            trace_id="t1",
            created_at=VALID_TS,
            phase=1,
            actor="test",
            action="run",
        )
        defaults.update(overrides)
        return LedgerEntry(**defaults)

    def test_create_minimal(self):
        e = self._make()
        assert e.trace_id == "t1"
        assert e.phase == 1

    def test_empty_trace_id_raises(self):
        with pytest.raises(ValueError):
            self._make(trace_id="")

    def test_bad_timestamp_raises(self):
        with pytest.raises(ValueError):
            self._make(created_at="nope")

    def test_phase_below_range(self):
        with pytest.raises(ValueError):
            self._make(phase=-1)

    def test_phase_above_range(self):
        with pytest.raises(ValueError):
            self._make(phase=1000)

    def test_to_dict_keys(self):
        d = self._make().to_dict()
        assert "trace_id" in d
        assert "created_at" in d
        assert "artifacts" in d
        assert isinstance(d["artifacts"], list)

    def test_from_dict_roundtrip(self):
        e1 = self._make(inputs={"x": 1}, outputs={"y": 2})
        d = e1.to_dict()
        e2 = LedgerEntry.from_dict(d)
        assert e2.trace_id == e1.trace_id
        assert e2.inputs == e1.inputs
        assert e2.outputs == e1.outputs
