#!/usr/bin/env python3
"""Dedicated tests for check_stale_docs() main orchestration flow.

Targets the STALE/CURRENT/OK classification loop (lines 409-440),
strict mode interaction, content+git staleness interplay, and
missing-file handling. 8 tests covering gaps identified in COV-01.
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_stale_docs as csd


def _patch_git(merge_sha, changed_files, merge_msg="merge (1 day ago)"):
    """Return context managers that mock git helpers."""
    return (
        patch.object(csd, "get_last_merge_commit", return_value=merge_sha),
        patch.object(csd, "get_files_changed_since", return_value=set(changed_files)),
        patch.object(csd, "run", return_value=merge_msg),
    )


class TestCheckStaleDocsMainFlow:
    """Tests for the main check_stale_docs() orchestration function."""

    def test_stale_when_tracked_code_changed_but_doc_not(self, tmp_path, capsys):
        """Doc is STALE when code it tracks changed but doc itself did not."""
        # Create the doc file so it's not MISSING
        (tmp_path / "AGENTS.md").write_text("1634 tests v1.0.0-rc1 20 claims 19 agent checks", encoding="utf-8")

        small_critical = {
            "AGENTS.md": {
                "tracks": ["scripts/"],
                "description": "Hard rules",
            },
        }
        small_content = {}

        p1, p2, p3 = _patch_git("abc123", ["scripts/mg.py"])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=False)

        out = capsys.readouterr().out
        assert "STALE" in out
        assert result is False  # stale files exist

    def test_current_when_doc_in_changed_set(self, tmp_path, capsys):
        """Doc is CURRENT when it appears in the changed files set."""
        (tmp_path / "AGENTS.md").write_text("1634 tests v1.0.0-rc1 20 claims 19 agent checks", encoding="utf-8")

        small_critical = {
            "AGENTS.md": {
                "tracks": ["scripts/"],
                "description": "Hard rules",
            },
        }
        small_content = {}

        # Both the doc AND tracked code changed
        p1, p2, p3 = _patch_git("abc123", ["AGENTS.md", "scripts/mg.py"])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=False)

        out = capsys.readouterr().out
        assert "CURRENT" in out
        assert result is True  # no stale, no content issues

    def test_ok_when_neither_doc_nor_code_changed(self, tmp_path, capsys):
        """Doc is OK when neither it nor its tracked code changed."""
        (tmp_path / "AGENTS.md").write_text("1634 tests v1.0.0-rc1 20 claims 19 agent checks", encoding="utf-8")

        small_critical = {
            "AGENTS.md": {
                "tracks": ["scripts/"],
                "description": "Hard rules",
            },
        }
        small_content = {}

        # Nothing changed
        p1, p2, p3 = _patch_git("abc123", [])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=False)

        out = capsys.readouterr().out
        assert "OK" in out
        assert result is True

    def test_missing_doc_file_handled_gracefully(self, tmp_path, capsys):
        """MISSING doc file does not crash -- prints warning."""
        # Do NOT create AGENTS.md on disk
        small_critical = {
            "AGENTS.md": {
                "tracks": ["scripts/"],
                "description": "Hard rules",
            },
        }
        small_content = {}

        p1, p2, p3 = _patch_git("abc123", ["scripts/mg.py"])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=False)

        out = capsys.readouterr().out
        assert "MISSING" in out
        assert result is True  # missing is not stale

    def test_strict_returns_false_when_stale(self, tmp_path, capsys):
        """strict=True returns False when stale files exist."""
        (tmp_path / "AGENTS.md").write_text("1634 tests v1.0.0-rc1 20 claims 19 agent checks", encoding="utf-8")

        small_critical = {
            "AGENTS.md": {
                "tracks": ["scripts/"],
                "description": "Hard rules",
            },
        }
        small_content = {}

        p1, p2, p3 = _patch_git("abc123", ["scripts/mg.py"])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=True)

        assert result is False

    def test_strict_false_returns_false_when_content_stale(self, tmp_path, capsys):
        """Even without strict, content issues cause False return."""
        # File has banned content
        (tmp_path / "llms.txt").write_text("old 595 passing content", encoding="utf-8")

        small_critical = {}
        small_content = {
            "llms.txt": {
                "banned": ["595 passing"],
                "required": [],
            },
        }

        p1, p2, p3 = _patch_git("abc123", [])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=False)

        assert result is False  # all_clean is False

    def test_returns_true_when_everything_clean(self, tmp_path, capsys):
        """Returns True when no stale, no content issues."""
        (tmp_path / "AGENTS.md").write_text("1634 tests v1.0.0-rc1 20 claims 19 agent checks", encoding="utf-8")

        small_critical = {
            "AGENTS.md": {
                "tracks": ["scripts/"],
                "description": "Hard rules",
            },
        }
        # Content check passes (file has required, no banned)
        small_content = {
            "AGENTS.md": {
                "banned": [],
                "required": ["1634"],
            },
        }

        p1, p2, p3 = _patch_git("abc123", ["AGENTS.md"])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=True)

        assert result is True

    def test_content_validation_runs_independently_of_git(self, tmp_path, capsys):
        """Content staleness is detected even when no git changes exist."""
        # File exists but has banned content
        (tmp_path / "llms.txt").write_text("old 595 passing content", encoding="utf-8")

        small_critical = {}
        small_content = {
            "llms.txt": {
                "banned": ["595 passing"],
                "required": [],
            },
        }

        # No files changed at all
        p1, p2, p3 = _patch_git("abc123", [])
        with p1, p2, p3, \
             patch.object(csd, "REPO_ROOT", tmp_path), \
             patch.object(csd, "CRITICAL_FILES", small_critical), \
             patch.object(csd, "CONTENT_CHECKS", small_content):
            result = csd.check_stale_docs(strict=False)

        out = capsys.readouterr().out
        assert "CONTENT" in out
        assert result is False
