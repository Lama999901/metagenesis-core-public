"""Tests for backend/ledger/ledger_store.py -- append-only JSONL (15 tests)."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

import pytest
from backend.ledger.models import LedgerEntry
from backend.ledger.ledger_store import LedgerStore

VALID_SHA = "a" * 64
VALID_TS = "2026-03-31T12:00:00+00:00"


def _entry(trace_id="t1", phase=1):
    return LedgerEntry(
        trace_id=trace_id,
        created_at=VALID_TS,
        phase=phase,
        actor="test",
        action="run",
    )


# ---- init --------------------------------------------------------------------

class TestLedgerStoreInit:
    def test_init_creates_file(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        assert fp.exists()

    def test_init_creates_parent_dirs(self, tmp_path):
        fp = tmp_path / "sub" / "dir" / "ledger.jsonl"
        store = LedgerStore(str(fp))
        assert fp.exists()


# ---- append ------------------------------------------------------------------

class TestLedgerStoreAppend:
    def test_append_writes_line(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry())
        lines = fp.read_text().strip().splitlines()
        assert len(lines) == 1

    def test_append_valid_json(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry())
        data = json.loads(fp.read_text().strip())
        assert data["trace_id"] == "t1"

    def test_append_multiple(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry("a"))
        store.append(_entry("b"))
        store.append(_entry("c"))
        assert store.count() == 3


# ---- get ---------------------------------------------------------------------

class TestLedgerStoreGet:
    def test_get_finds_entry(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry("x"))
        result = store.get("x")
        assert result is not None
        assert result.trace_id == "x"

    def test_get_not_found(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry("x"))
        assert store.get("missing") is None

    def test_get_last_occurrence(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry("x", phase=1))
        store.append(_entry("x", phase=2))
        result = store.get("x")
        assert result.phase == 2


# ---- count -------------------------------------------------------------------

class TestLedgerStoreCount:
    def test_count_empty(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        assert store.count() == 0

    def test_count_skips_invalid(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        store.append(_entry("a"))
        # Inject an invalid JSON line
        with open(fp, "a") as f:
            f.write("NOT JSON\n")
        store.append(_entry("b"))
        assert store.count() == 2


# ---- list_recent -------------------------------------------------------------

class TestLedgerStoreListRecent:
    def test_list_recent_order(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        for i in range(5):
            store.append(_entry(f"t{i}"))
        recent = store.list_recent(limit=3)
        assert len(recent) == 3
        # last 3 entries
        assert recent[0].trace_id == "t2"
        assert recent[2].trace_id == "t4"

    def test_list_recent_limit(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        for i in range(10):
            store.append(_entry(f"t{i}"))
        assert len(store.list_recent(limit=5)) == 5

    def test_list_recent_empty(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        assert store.list_recent() == []

    def test_roundtrip_via_store(self, tmp_path):
        fp = tmp_path / "ledger.jsonl"
        store = LedgerStore(str(fp))
        e = _entry("rt", phase=42)
        store.append(e)
        got = store.get("rt")
        assert got.trace_id == "rt"
        assert got.phase == 42
