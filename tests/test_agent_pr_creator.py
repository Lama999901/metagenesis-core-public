"""Tests for scripts/agent_pr_creator.py -- Level 3 autonomous PR creator."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_pr_creator as apc


class TestDetectStaleCounters(unittest.TestCase):
    """Test stale counter detection against system_manifest.json."""

    @patch("agent_pr_creator.subprocess.run")
    @patch("builtins.open", mock_open(read_data='{"test_count": 601}'))
    def test_detect_stale_counters_clean(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="601 passed, 2 skipped in 5.00s\n", returncode=0
        )
        result = apc.detect_stale_counters(dry_run=True)
        self.assertFalse(result["stale"])
        self.assertEqual(result["manifest_count"], 601)
        self.assertEqual(result["actual_count"], 601)

    @patch("agent_pr_creator.subprocess.run")
    @patch("builtins.open", mock_open(read_data='{"test_count": 601}'))
    def test_detect_stale_counters_mismatch(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="610 passed in 5.00s\n", returncode=0
        )
        result = apc.detect_stale_counters(dry_run=True)
        self.assertTrue(result["stale"])
        self.assertEqual(result["manifest_count"], 601)
        self.assertEqual(result["actual_count"], 610)


class TestDetectForbiddenTerms(unittest.TestCase):
    """Test forbidden term detection with safe_contexts."""

    @patch("agent_pr_creator.Path.is_file", return_value=True)
    @patch("agent_pr_creator.Path.exists", return_value=True)
    @patch("agent_pr_creator.Path.read_text", return_value="clean content\nno issues here\n")
    def test_detect_forbidden_terms_clean(self, mock_read, mock_exists, mock_isfile):
        result = apc.detect_forbidden_terms()
        self.assertEqual(result, [])

    @patch("agent_pr_creator.Path.is_file", return_value=True)
    @patch("agent_pr_creator.Path.exists", return_value=True)
    @patch("agent_pr_creator.Path.read_text",
           return_value='BANNED TERMS: never write "tamper-' + 'proof" -> say "tamper-evident"\n')
    def test_detect_forbidden_terms_with_safe_context(self, mock_read, mock_exists, mock_isfile):
        result = apc.detect_forbidden_terms()
        self.assertEqual(result, [])


class TestDetectManifestSync(unittest.TestCase):
    """Test manifest version vs git tag comparison."""

    @patch("agent_pr_creator.subprocess.run")
    @patch("builtins.open", mock_open(read_data='{"version": "0.8.0"}'))
    def test_detect_manifest_sync_match(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="v0.8.0\n", returncode=0
        )
        result = apc.detect_manifest_sync()
        self.assertTrue(result["synced"])

    @patch("agent_pr_creator.subprocess.run")
    @patch("builtins.open", mock_open(read_data='{"version": "0.8.0"}'))
    def test_detect_manifest_sync_mismatch(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="v0.7.0\n", returncode=0
        )
        result = apc.detect_manifest_sync()
        self.assertFalse(result["synced"])


class TestMainSummaryMode(unittest.TestCase):
    """Test that --summary mode prints but does not create branches."""

    @patch("agent_pr_creator.detect_manifest_sync",
           return_value={"synced": True, "manifest_version": "0.8.0", "tag_version": "0.8.0"})
    @patch("agent_pr_creator.detect_forbidden_terms", return_value=[])
    @patch("agent_pr_creator.detect_stale_counters",
           return_value={"stale": False, "manifest_count": 601, "actual_count": 601})
    def test_main_summary_mode(self, mock_stale, mock_forbidden, mock_sync):
        with patch("sys.argv", ["agent_pr_creator.py", "--summary"]):
            code = apc.main()
        self.assertEqual(code, 0)
        # Ensure detect_stale_counters was called with dry_run=True
        mock_stale.assert_called_once_with(dry_run=True)


if __name__ == "__main__":
    unittest.main()
