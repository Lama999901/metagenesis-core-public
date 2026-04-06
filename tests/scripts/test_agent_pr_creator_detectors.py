#!/usr/bin/env python3
"""Coverage tests for agent_pr_creator.py detect_stale_counters, detect_manifest_sync, main."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_pr_creator  # noqa: E402


# ---------------------------------------------------------------------------
# detect_stale_counters() tests
# ---------------------------------------------------------------------------

class TestDetectStaleCounters:
    """Tests for detect_stale_counters() function."""

    def test_returns_not_stale_when_counts_match(self, tmp_path):
        """detect_stale_counters() returns stale=False when manifest matches actual."""
        manifest = {"test_count": 1634, "version": "0.9.0"}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "1634 passed, 2 skipped in 45.3s"

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc):
            result = agent_pr_creator.detect_stale_counters(dry_run=True)

        assert result["stale"] is False
        assert result["manifest_count"] == 1634
        assert result["actual_count"] == 1634

    def test_returns_stale_when_counts_differ(self, tmp_path):
        """detect_stale_counters() returns stale=True when manifest != actual."""
        manifest = {"test_count": 1634, "version": "0.9.0"}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "1700 passed, 2 skipped in 50.1s"

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc):
            result = agent_pr_creator.detect_stale_counters(dry_run=True)

        assert result["stale"] is True
        assert result["manifest_count"] == 1634
        assert result["actual_count"] == 1700

    def test_dry_run_does_not_call_auto_fix(self, tmp_path):
        """detect_stale_counters(dry_run=True) does not call _auto_fix_stale_counter."""
        manifest = {"test_count": 1634, "version": "0.9.0"}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "1700 passed"

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc), \
             patch.object(agent_pr_creator, "_auto_fix_stale_counter") as mock_fix:
            agent_pr_creator.detect_stale_counters(dry_run=True)

        mock_fix.assert_not_called()

    def test_actual_count_zero_means_not_stale(self, tmp_path):
        """detect_stale_counters() treats 0 actual count as not stale (pytest didn't run)."""
        manifest = {"test_count": 1634, "version": "0.9.0"}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "no tests ran"

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc):
            result = agent_pr_creator.detect_stale_counters(dry_run=True)

        assert result["stale"] is False
        assert result["actual_count"] == 0


# ---------------------------------------------------------------------------
# detect_manifest_sync() tests
# ---------------------------------------------------------------------------

class TestDetectManifestSync:
    """Tests for detect_manifest_sync() function."""

    def test_synced_when_versions_match(self, tmp_path):
        """detect_manifest_sync() returns synced=True when manifest version matches git tag."""
        manifest = {"version": "0.9.0", "test_count": 1634}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "v0.9.0"
        mock_proc.returncode = 0

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc):
            result = agent_pr_creator.detect_manifest_sync()

        assert result["synced"] is True
        assert result["manifest_version"] == "0.9.0"
        assert result["tag_version"] == "0.9.0"

    def test_not_synced_when_versions_differ(self, tmp_path):
        """detect_manifest_sync() returns synced=False when versions differ."""
        manifest = {"version": "0.9.0", "test_count": 1634}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = "v0.8.0"
        mock_proc.returncode = 0

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc):
            result = agent_pr_creator.detect_manifest_sync()

        assert result["synced"] is False
        assert result["tag_version"] == "0.8.0"

    def test_no_tags_returns_unknown(self, tmp_path):
        """detect_manifest_sync() returns 'unknown' tag when git has no tags."""
        manifest = {"version": "0.9.0", "test_count": 1634}
        manifest_path = tmp_path / "system_manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        mock_proc = MagicMock()
        mock_proc.stdout = ""
        mock_proc.returncode = 128

        with patch.object(agent_pr_creator, "REPO_ROOT", tmp_path), \
             patch("subprocess.run", return_value=mock_proc):
            result = agent_pr_creator.detect_manifest_sync()

        assert result["tag_version"] == "unknown"


# ---------------------------------------------------------------------------
# main() tests
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for main() output."""

    def test_main_no_auto_pr_needed(self, capsys):
        """main() prints 'No auto-pr needed' when all detectors pass."""
        stale_result = {"stale": False, "manifest_count": 2063, "actual_count": 2063}
        sync_result = {"synced": True, "manifest_version": "0.9.0", "tag_version": "0.9.0"}

        with patch.object(agent_pr_creator, "detect_stale_counters", return_value=stale_result), \
             patch.object(agent_pr_creator, "detect_forbidden_terms", return_value=[]), \
             patch.object(agent_pr_creator, "detect_manifest_sync", return_value=sync_result), \
             patch.object(agent_pr_creator, "detect_coverage_drop", return_value=None), \
             patch.object(agent_pr_creator, "detect_pilot_queue_stale", return_value=[]), \
             patch("sys.argv", ["agent_pr_creator.py", "--summary"]):
            result = agent_pr_creator.main()

        assert result == 0
        captured = capsys.readouterr()
        assert "No auto-pr needed" in captured.out
