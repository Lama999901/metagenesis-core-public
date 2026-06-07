#!/usr/bin/env python3
"""Mock-based coverage tests for scripts/agent_evolution.py -- 35 tests."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agent_evolution as ae  # noqa: E402


# -- check_steward -----------------------------------------------------------

class TestCheckSteward:
    def test_check_steward_pass(self):
        with patch("agent_evolution.run", return_value=("STEWARD AUDIT: PASS", 0)):
            assert ae.check_steward() is True

    def test_check_steward_fail(self):
        with patch("agent_evolution.run", return_value=("FAIL coverage", 1)):
            assert ae.check_steward() is False


# -- check_tests --------------------------------------------------------------

class TestCheckTests:
    def test_check_tests_pass(self):
        with patch("agent_evolution.run", return_value=("966 passed in 12.3s", 0)):
            ok, count = ae.check_tests()
            assert ok is True
            assert count == 966

    def test_check_tests_fail(self):
        with patch("agent_evolution.run", return_value=("FAILED 2 errors", 1)):
            ok, count = ae.check_tests()
            assert ok is False

    def test_check_tests_zero_count_no_match(self):
        with patch("agent_evolution.run", return_value=("no tests ran", 0)):
            ok, count = ae.check_tests()
            assert ok is True
            assert count == 0


# -- check_deep_verify --------------------------------------------------------

class TestCheckDeepVerify:
    def test_check_deep_verify_pass(self):
        with patch("agent_evolution.run", return_value=("ALL 13 TESTS PASSED", 0)):
            assert ae.check_deep_verify() is True

    def test_check_deep_verify_fail(self):
        with patch("agent_evolution.run", return_value=("TEST FAILED", 1)):
            assert ae.check_deep_verify() is False


# -- check_stale_docs ---------------------------------------------------------

class TestCheckStaleDocs:
    def test_check_stale_docs_pass(self):
        with patch("agent_evolution.run",
                    return_value=("All critical documentation is current", 0)):
            ok, stale = ae.check_stale_docs()
            assert ok is True
            assert stale == []

    def test_check_stale_docs_fail_with_stale_markers(self):
        output = "check_stale_docs result\n\u274c STALE: README.md has 734"
        with patch("agent_evolution.run", return_value=(output, 1)):
            ok, stale = ae.check_stale_docs()
            assert ok is False

    def test_check_stale_docs_pass_no_markers(self):
        with patch("agent_evolution.run", return_value=("Docs check OK", 1)):
            ok, stale = ae.check_stale_docs()
            assert ok is True
            assert stale == []


# -- check_manifest -----------------------------------------------------------

class TestCheckManifest:
    def test_check_manifest_pass(self, tmp_path):
        manifest = {
            "test_count": 966,
            "version": "0.8.0",
            "active_claims": ["c"] * 20,
        }
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(966) is True

    def test_check_manifest_fail_count_mismatch(self, tmp_path):
        manifest = {
            "test_count": 900,
            "version": "0.8.0",
            "active_claims": ["c"] * 20,
        }
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(966) is False

    def test_check_manifest_fail_wrong_claim_count(self, tmp_path):
        manifest = {
            "test_count": 966,
            "version": "0.8.0",
            "active_claims": ["c"] * 15,
        }
        (tmp_path / "system_manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(966) is False

    def test_check_manifest_missing_file(self, tmp_path):
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(966) is False


# -- check_forbidden ----------------------------------------------------------

class TestCheckForbidden:
    def test_check_forbidden_pass_empty_repo(self, tmp_path):
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("", 1)):
            assert ae.check_forbidden() is True

    def test_check_forbidden_real_hit(self, tmp_path):
        """A file with a banned term not in safe context should fail."""
        (tmp_path / "README.md").write_text(
            "Our system is tamper-" + "proof and secure.\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("", 1)):
            assert ae.check_forbidden() is False

    def test_check_forbidden_safe_context(self, tmp_path):
        """A banned term in a BANNED context line should pass."""
        (tmp_path / "README.md").write_text(
            'BANNED: never say "tamper-' + 'proof"\n', encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("", 1)):
            assert ae.check_forbidden() is True


# -- check_claude_md ----------------------------------------------------------

class TestCheckClaudeMd:
    def test_check_claude_md_pass(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "966 tests\nv1.0.0-rc1 version\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(966) is True

    def test_check_claude_md_fail_missing_count(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "v1.0.0-rc1 but no test count here\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(966) is False

    def test_check_claude_md_fail_merge_conflict(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "<<<<<<< HEAD\n966 tests\nv1.0.0-rc1\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(966) is False

    def test_check_claude_md_missing_file(self, tmp_path):
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(966) is False


# -- check_watchlist -----------------------------------------------------------

class TestCheckWatchlist:
    def test_check_watchlist_pass_all_watched(self):
        with patch("agent_evolution.run",
                    return_value=("53/53 files watched (0 unwatched)", 0)):
            assert ae.check_watchlist() is True

    def test_check_watchlist_pass_some_unwatched(self):
        with patch("agent_evolution.run",
                    return_value=("50/53 files watched (3 unwatched)", 0)):
            assert ae.check_watchlist() is True


# -- check_branch_sync --------------------------------------------------------

class TestCheckBranchSync:
    def test_check_branch_sync_pass(self):
        with patch("agent_evolution.run", side_effect=[("", 0), ("0", 0)]):
            assert ae.check_branch_sync() is True

    def test_check_branch_sync_fail_behind(self):
        with patch("agent_evolution.run", side_effect=[("", 0), ("3", 0)]):
            assert ae.check_branch_sync() is False


# -- check_coverage ------------------------------------------------------------

class TestCheckCoverage:
    def test_check_coverage_pass(self):
        with patch("agent_evolution.run",
                    return_value=("Coverage 81.0% | 50 zero-cov | 53 files", 0)):
            assert ae.check_coverage() is True

    def test_check_coverage_advisory(self):
        with patch("agent_evolution.run", return_value=("Coverage 47.0%", 1)):
            assert ae.check_coverage() is True

    def test_check_coverage_below_threshold(self):
        with patch("agent_evolution.run",
                    return_value=("Coverage 40.0% below minimum", 0)):
            assert ae.check_coverage() is False


# -- check_self_improvement ----------------------------------------------------

class TestCheckSelfImprovement:
    def test_check_self_improvement_pass(self):
        with patch("agent_evolution.run",
                    return_value=("3 reports | 1 rec", 0)):
            assert ae.check_self_improvement() is True


# -- check_signals -------------------------------------------------------------

class TestCheckSignals:
    def test_check_signals_pass(self):
        with patch("agent_evolution.run",
                    return_value=("stars:5 forks:1", 0)):
            assert ae.check_signals() is True


# -- check_chronicle -----------------------------------------------------------

class TestCheckChronicle:
    def test_check_chronicle_pass(self):
        with patch("agent_evolution.run",
                    return_value=("Chronicle recorded", 0)):
            assert ae.check_chronicle() is True


# -- check_pr_review -----------------------------------------------------------

class TestCheckPrReview:
    def test_check_pr_review_no_changes(self):
        with patch("agent_evolution.run", return_value=("", 0)):
            assert ae.check_pr_review() is True

    def test_check_pr_review_all_tested(self):
        with patch("agent_evolution.run",
                    side_effect=[("scripts/mg.py\n", 0), ("tests/test_mg.py\n", 0)]):
            assert ae.check_pr_review() is True


# -- check_impact --------------------------------------------------------------

class TestCheckImpact:
    def test_check_impact_pass(self):
        with patch("agent_evolution.run",
                    return_value=("Impact: 0 MISSING", 0)):
            assert ae.check_impact() is True


# -- check_diff_review ---------------------------------------------------------

class TestCheckDiffReview:
    def test_check_diff_review_pass(self):
        with patch("agent_evolution.run",
                    return_value=("DIFF_PASS | 2 files", 0)):
            assert ae.check_diff_review() is True

    def test_check_diff_review_fail(self):
        with patch("agent_evolution.run",
                    return_value=("DIFF_FAIL | 1 issue", 1)):
            assert ae.check_diff_review() is False


# -- check_auto_pr -------------------------------------------------------------

class TestCheckAutoPr:
    def test_check_auto_pr_clean(self):
        with patch("agent_evolution.run",
                    return_value=("No auto-pr needed -- system current", 0)):
            assert ae.check_auto_pr() is True

    def test_check_auto_pr_advisory(self):
        with patch("agent_evolution.run",
                    return_value=("Auto-fixable: stale count", 1)):
            assert ae.check_auto_pr() is True


# -- check_semantic_audit ------------------------------------------------------

class TestCheckSemanticAudit:
    def test_check_semantic_audit_pass(self):
        with patch("agent_evolution.run",
                    return_value=("ALL 6 CHECKS PASS", 0)):
            assert ae.check_semantic_audit() is True

    def test_check_semantic_audit_fail(self):
        with patch("agent_evolution.run",
                    return_value=("SEMANTIC_FAIL", 1)):
            assert ae.check_semantic_audit() is False


# -- run_gap_analysis ----------------------------------------------------------

class TestRunGapAnalysis:
    def test_run_gap_analysis_returns_list(self, tmp_path):
        # Create test dirs that the function checks
        tests_dir = tmp_path / "tests"
        for domain in ["steward", "materials", "ml", "systems",
                        "data", "digital_twin", "pharma", "finance"]:
            d = tests_dir / domain
            d.mkdir(parents=True, exist_ok=True)
            (d / "test_placeholder.py").write_text("# test", encoding="utf-8")

        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("0", 0)):
            result = ae.run_gap_analysis(100)
        assert isinstance(result, list)


# -- check_client_contributions ------------------------------------------------

class TestCheckClientContributions:
    def test_no_contrib_dir(self, tmp_path):
        """Missing directory is advisory, returns True."""
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_client_contributions() is True

    def test_empty_contrib_dir(self, tmp_path):
        contrib_dir = tmp_path / "reports" / "client_contributions"
        contrib_dir.mkdir(parents=True)
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_client_contributions() is True

    def test_contrib_with_reviewed_files(self, tmp_path):
        contrib_dir = tmp_path / "reports" / "client_contributions"
        contrib_dir.mkdir(parents=True)
        data = {
            "timestamp": "2026-04-10T00:00:00Z",
            "value_score": 8,
            "domain": "ml",
        }
        (contrib_dir / "contrib_001.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_client_contributions() is True

    def test_contrib_with_unreviewed_files(self, tmp_path):
        contrib_dir = tmp_path / "reports" / "client_contributions"
        contrib_dir.mkdir(parents=True)
        for i in range(12):
            data = {
                "timestamp": "2026-04-01T00:00:00Z",
                "value_score": None,
                "domain": "ml",
            }
            (contrib_dir / f"contrib_{i:03d}.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            # Should still return True (advisory only) but warn
            assert ae.check_client_contributions() is True

    def test_contrib_with_corrupt_file(self, tmp_path):
        contrib_dir = tmp_path / "reports" / "client_contributions"
        contrib_dir.mkdir(parents=True)
        (contrib_dir / "contrib_001.json").write_text("not json!", encoding="utf-8")
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_client_contributions() is True


# -- ANTI-CHEAT PROOF: check_forbidden must still catch real prose -------------
# Every banned literal below is assembled from fragments so this test FILE never
# contains a raw banned token (the repo forbidden-terms scan would otherwise trip
# on the test source itself, and check_stale_docs would flag it).

# Banned literals built at runtime (never written whole in source):
_BANNED_TAMPER = "tamper-" + "proof"
_BANNED_CHAIN = "block" + "chain"


class TestForbiddenCatchesProse:
    """Proves Task 3 hardening did NOT gut detection (anti-cheat §0)."""

    def test_real_prose_banned_term_is_caught(self, tmp_path):
        # Plain prose (no safe-context marker) with a real banned term must FAIL.
        (tmp_path / "README.md").write_text(
            "This system is " + _BANNED_TAMPER + " and reliable.\n",
            encoding="utf-8",
        )
        # Neutralize the grep dir-branch so only the is_file README.md path runs.
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("", 1)):
            assert ae.check_forbidden() is False

    def test_real_prose_banned_term_in_docs_dir_is_caught(self, tmp_path):
        # Prove the grep dir-branch genuinely flags a real prose hit (not skipped).
        docs = tmp_path / "docs"
        docs.mkdir()
        bad = docs / "MARKETING.md"
        bad.write_text(
            "Our protocol is " + _BANNED_CHAIN + "-based and modern.\n",
            encoding="utf-8",
        )
        # Simulate grep -rl returning this real (non-skipped) doc file.
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("docs/MARKETING.md", 0)):
            assert ae.check_forbidden() is False

    def test_denylist_table_row_is_safe(self, tmp_path):
        # A banned-terms TABLE row (denylist meta-context) must NOT be flagged.
        (tmp_path / "README.md").write_text(
            '| "' + _BANNED_CHAIN + '" | "cryptographic hash chain" |\n',
            encoding="utf-8",
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("", 1)):
            assert ae.check_forbidden() is True

    def test_arrow_safe_context_is_safe(self, tmp_path):
        # A "→" mapping line (banned → replacement) must NOT be flagged.
        (tmp_path / "README.md").write_text(
            '"' + _BANNED_TAMPER + '" → "tamper-evident"\n',
            encoding="utf-8",
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run", return_value=("", 1)):
            assert ae.check_forbidden() is True

    def test_pycache_binary_path_is_skipped(self, tmp_path):
        # A compiled __pycache__/*.pyc path reported by grep must be skipped,
        # never producing a false positive — even if it "contains" a banned term.
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run",
                    return_value=("scripts/__pycache__/foo.cpython-311.pyc", 0)):
            assert ae.check_forbidden() is True

    def test_denylist_definer_source_is_skipped(self, tmp_path):
        # The denylist-DEFINING sources (e.g. check_stale_docs.py) must be skipped:
        # their presence IS the denylist, not heresy.
        with patch("agent_evolution.REPO_ROOT", tmp_path), \
             patch("agent_evolution.run",
                    return_value=("scripts/check_stale_docs.py", 0)):
            assert ae.check_forbidden() is True


# -- PLATFORM TOLERANCE: manifest count (exact OR +KNOWN_WIN32_SKIPS) ----------


class TestManifestTolerance:
    """Proves Task 4 tolerance is exactly ±KNOWN_WIN32_SKIPS, not a wildcard."""

    def _write_manifest(self, tmp_path, count):
        (tmp_path / "system_manifest.json").write_text(
            json.dumps({
                "test_count": count,
                "version": "1.0.0-rc1",
                "active_claims": ["c"] * 20,
            }),
            encoding="utf-8",
        )

    def test_manifest_exact_match_passes(self, tmp_path):
        self._write_manifest(tmp_path, 2410)
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(2410) is True

    def test_manifest_tolerated_by_one_passes(self, tmp_path):
        # Windows runtime: manifest (canonical) == actual + 1 skip.
        self._write_manifest(tmp_path, 2410)
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(2410 - ae.KNOWN_WIN32_SKIPS) is True

    def test_manifest_off_by_five_fails(self, tmp_path):
        # Genuinely wrong count must still FAIL (anti-cheat: tolerance is bounded).
        self._write_manifest(tmp_path, 2410)
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_manifest(2410 - 5) is False


# -- PLATFORM TOLERANCE: CLAUDE.md count --------------------------------------


class TestClaudeMdTolerance:
    """Proves Task 4 CLAUDE.md tolerance is exactly ±KNOWN_WIN32_SKIPS."""

    def test_claude_md_exact_passes(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text(
            "2410 tests\nv1.0.0-rc1\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(2410) is True

    def test_claude_md_tolerated_by_one_passes(self, tmp_path):
        # CLAUDE.md mentions only canonical (2410); Windows actual is 2409.
        (tmp_path / "CLAUDE.md").write_text(
            "2410 tests\nv1.0.0-rc1\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(2410 - ae.KNOWN_WIN32_SKIPS) is True

    def test_claude_md_off_by_five_fails(self, tmp_path):
        # Mentions neither actual nor actual+1 → must FAIL.
        (tmp_path / "CLAUDE.md").write_text(
            "1234 tests\nv1.0.0-rc1\n", encoding="utf-8"
        )
        with patch("agent_evolution.REPO_ROOT", tmp_path):
            assert ae.check_claude_md(2410 - 5) is False
