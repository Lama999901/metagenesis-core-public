#!/usr/bin/env python3
"""Coverage tests for scripts/agent_signals.py -- 20 tests."""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_signals


# -- fetch_github_stats -------------------------------------------------------

class TestFetchGithubStats:
    def test_returns_dict_on_success(self):
        mock_data = json.dumps({
            "stargazers_count": 10,
            "forks_count": 2,
            "open_issues_count": 3,
            "pushed_at": "2026-01-01T00:00:00Z",
        }).encode("utf-8")
        mock_resp = MagicMock()
        mock_resp.read.return_value = mock_data
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("agent_signals.urllib.request.urlopen", return_value=mock_resp):
            result = agent_signals.fetch_github_stats()
        assert result["stars"] == 10
        assert result["forks"] == 2
        assert result["open_issues"] == 3
        assert result["pushed_at"] == "2026-01-01T00:00:00Z"

    def test_returns_error_on_urlerror(self):
        import urllib.error
        with patch("agent_signals.urllib.request.urlopen",
                   side_effect=urllib.error.URLError("timeout")):
            result = agent_signals.fetch_github_stats()
        assert "error" in result

    def test_returns_error_on_httperror(self):
        import urllib.error
        with patch("agent_signals.urllib.request.urlopen",
                   side_effect=urllib.error.HTTPError(
                       "http://x", 403, "Forbidden", {}, None)):
            result = agent_signals.fetch_github_stats()
        assert "error" in result

    def test_returns_error_on_oserror(self):
        with patch("agent_signals.urllib.request.urlopen",
                   side_effect=OSError("network down")):
            result = agent_signals.fetch_github_stats()
        assert "error" in result

    def test_returns_error_on_json_decode(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"not json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("agent_signals.urllib.request.urlopen", return_value=mock_resp):
            result = agent_signals.fetch_github_stats()
        assert "error" in result


# -- count_memory_sessions ----------------------------------------------------

class TestCountMemorySessions:
    def test_zero_when_no_dir(self, tmp_path):
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_memory_sessions() == 0

    def test_counts_json_files(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        for i in range(3):
            (mem / f"session_{i}.json").write_text("{}", encoding="utf-8")
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_memory_sessions() == 3

    def test_ignores_non_json(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        (mem / "session_1.json").write_text("{}", encoding="utf-8")
        (mem / "notes.txt").write_text("text", encoding="utf-8")
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_memory_sessions() == 1

    def test_empty_dir(self, tmp_path):
        mem = tmp_path / ".agent_memory"
        mem.mkdir()
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_memory_sessions() == 0


# -- count_tasks --------------------------------------------------------------

class TestCountTasks:
    def test_zero_when_no_file(self, tmp_path):
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_tasks() == (0, 0)

    def test_counts_pending_and_done(self, tmp_path):
        content = (
            "Task A\nStatus: PENDING\n"
            "Task B\nStatus: PENDING\n"
            "Task C\nStatus: PENDING\n"
            "Task D\nStatus: DONE\n"
            "Task E\nStatus: DONE\n"
        )
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_tasks() == (3, 2)

    def test_ignores_other_lines(self, tmp_path):
        content = "Status: RUNNING\nJust normal text\n"
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_tasks() == (0, 0)

    def test_case_sensitive(self, tmp_path):
        content = "Status: pending\nStatus: done\n"
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_tasks() == (0, 0)

    def test_mixed_content(self, tmp_path):
        content = "# Header\n- bullet\nStatus: PENDING\nmore text\nStatus: DONE\n"
        (tmp_path / "AGENT_TASKS.md").write_text(content, encoding="utf-8")
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.count_tasks() == (1, 1)


# -- read_manifest ------------------------------------------------------------

class TestReadManifest:
    def test_reads_version_and_count(self, tmp_path):
        data = {"version": "0.8.0", "test_count": 1050}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.read_manifest() == ("0.8.0", 1050)

    def test_unknown_when_missing(self, tmp_path):
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.read_manifest() == ("unknown", 0)

    def test_missing_version_key(self, tmp_path):
        data = {"test_count": 500}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_signals.REPO_ROOT", tmp_path):
            v, tc = agent_signals.read_manifest()
        assert v == "unknown"
        assert tc == 500

    def test_missing_test_count_key(self, tmp_path):
        data = {"version": "1.0"}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_signals.REPO_ROOT", tmp_path):
            v, tc = agent_signals.read_manifest()
        assert v == "1.0"
        assert tc == 0

    def test_zero_test_count(self, tmp_path):
        data = {"version": "1.0", "test_count": 0}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_signals.REPO_ROOT", tmp_path):
            v, tc = agent_signals.read_manifest()
        assert tc == 0

    def test_extra_keys_ignored(self, tmp_path):
        data = {"version": "2.0", "test_count": 500, "extra": "stuff"}
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_signals.REPO_ROOT", tmp_path):
            assert agent_signals.read_manifest() == ("2.0", 500)
