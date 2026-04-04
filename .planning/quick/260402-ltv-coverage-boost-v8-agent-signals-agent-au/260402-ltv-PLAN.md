---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/scripts/test_agent_signals_pure.py
  - tests/scripts/test_agent_audit_pure.py
  - tests/scripts/test_agent_chronicle_pure.py
  - tests/scripts/test_agent_evolve_self_pure.py
  - scripts/check_stale_docs.py
  - system_manifest.json
  - CLAUDE.md
  - CONTEXT_SNAPSHOT.md
  - llms.txt
  - AGENTS.md
  - README.md
  - index.html
autonomous: true
requirements: [coverage-boost-v8]

must_haves:
  truths:
    - "75+ new tests pass across 2 new + 2 extended test files"
    - "All counters updated from 1050 to new total"
    - "python -m pytest tests/ -q passes with new count"
    - "python scripts/check_stale_docs.py passes with updated rules"
  artifacts:
    - path: "tests/scripts/test_agent_signals_pure.py"
      provides: "20 tests for agent_signals.py pure functions"
    - path: "tests/scripts/test_agent_audit_pure.py"
      provides: "20 tests for agent_audit.py edge cases and deeper function coverage"
    - path: "tests/scripts/test_agent_chronicle_pure.py"
      provides: "Extended from 18 to 33 tests for agent_chronicle.py"
    - path: "tests/scripts/test_agent_evolve_self_pure.py"
      provides: "Extended from 20 to 40 tests for agent_evolve_self.py"
  key_links:
    - from: "tests/scripts/test_agent_signals_pure.py"
      to: "scripts/agent_signals.py"
      via: "import + mock urllib/filesystem"
    - from: "tests/scripts/test_agent_audit_pure.py"
      to: "scripts/agent_audit.py"
      via: "import + mock REPO_ROOT with tmp_path"
    - from: "tests/scripts/test_agent_chronicle_pure.py"
      to: "scripts/agent_chronicle.py"
      via: "import + mock REPO_ROOT with tmp_path"
    - from: "tests/scripts/test_agent_evolve_self_pure.py"
      to: "scripts/agent_evolve_self.py"
      via: "import + mock REPO_ROOT with tmp_path"
---

<objective>
Coverage boost v8: Add 75+ tests covering agent_signals.py, agent_audit.py (deeper edge cases), agent_chronicle.py (extend), and agent_evolve_self.py (extend). Then sync all counters from 1050 to the new total.

Purpose: Increase test coverage of agent infrastructure scripts toward the 65% coverage target.
Output: 2 new test files + 2 extended test files, updated counters across all docs.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/agent_signals.py
@scripts/agent_audit.py
@scripts/agent_chronicle.py
@scripts/agent_evolve_self.py
@tests/scripts/test_agent_audit_coverage.py
@tests/scripts/test_agent_chronicle_pure.py
@tests/scripts/test_agent_evolve_self_pure.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create 2 new test files + extend 2 existing test files (75+ tests)</name>
  <files>
    tests/scripts/test_agent_signals_pure.py
    tests/scripts/test_agent_audit_pure.py
    tests/scripts/test_agent_chronicle_pure.py
    tests/scripts/test_agent_evolve_self_pure.py
  </files>
  <action>
Create 2 NEW test files and extend 2 EXISTING test files. All tests use tmp_path + mock REPO_ROOT pattern (no real filesystem). Use `from unittest.mock import patch` and `pytest` fixtures. Import modules via sys.path insertion from REPO_ROOT/scripts.

NOTE: test_agent_chronicle_pure.py (18 tests) and test_agent_evolve_self_pure.py (20 tests) ALREADY EXIST. Append new test classes/functions to the END of each file. Do NOT duplicate existing test names. Read each file first to understand existing coverage.

NOTE: test_agent_audit_coverage.py (30 tests) already covers basic happy paths for agent_audit.py check functions. The new test_agent_audit_pure.py must focus on EDGE CASES, error paths, and untested helper logic. No overlap.

**File 1 — tests/scripts/test_agent_signals_pure.py (NEW, 20 tests):**

Target functions: fetch_github_stats, count_memory_sessions, count_tasks, read_manifest

TestFetchGithubStats (5 tests):
- test_returns_dict_on_success: mock urlopen to return JSON with stargazers_count=10, forks_count=2, open_issues_count=3, pushed_at="2026-01-01T00:00:00Z". Assert keys stars/forks/open_issues/pushed_at in result.
- test_returns_error_on_urlerror: mock urlopen to raise urllib.error.URLError("timeout"). Assert result contains "error" key.
- test_returns_error_on_httperror: mock urlopen to raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None). Assert "error" key.
- test_returns_error_on_oserror: mock urlopen to raise OSError("network down"). Assert "error" key.
- test_returns_error_on_json_decode: mock urlopen.read() to return b"not json". Assert "error" key.

TestCountMemorySessions (4 tests):
- test_zero_when_no_dir: patch REPO_ROOT to tmp_path (no .agent_memory). Assert returns 0.
- test_counts_json_files: create tmp_path/.agent_memory/ with 3 .json files. Assert returns 3.
- test_ignores_non_json: create .agent_memory/ with 1 .json + 1 .txt. Assert returns 1.
- test_empty_dir: create .agent_memory/ empty. Assert returns 0.

TestCountTasks (5 tests):
- test_zero_when_no_file: patch REPO_ROOT, no AGENT_TASKS.md. Assert (0, 0).
- test_counts_pending_and_done: write file with 3 "Status: PENDING" and 2 "Status: DONE" lines. Assert (3, 2).
- test_ignores_other_lines: file with "Status: RUNNING" and normal text. Assert (0, 0).
- test_case_sensitive: "Status: pending" (lowercase) should NOT count. Assert (0, 0).
- test_mixed_content: file with headers, bullets, and 1 PENDING + 1 DONE. Assert (1, 1).

TestReadManifest (6 tests):
- test_reads_version_and_count: write system_manifest.json with version="0.8.0", test_count=1050. Assert ("0.8.0", 1050).
- test_unknown_when_missing: no manifest file. Assert ("unknown", 0).
- test_missing_version_key: manifest with only test_count. Assert ("unknown", N).
- test_missing_test_count_key: manifest with only version. Assert ("v", 0).
- test_zero_test_count: manifest with test_count=0. Assert (version, 0).
- test_extra_keys_ignored: manifest with extra fields. Assert correct version and count.

**File 2 — tests/scripts/test_agent_audit_pure.py (NEW, 20 tests):**

Target: edge cases for load_config, load_manifest, build_jobkind_to_file_map, get_job_kind_for_claim, find_test_files_for_claim, check_physical_anchors, check_innovations, check_demo_scenarios, check_triple_sync, check_patent_integrity. Avoid overlap with existing test_agent_audit_coverage.py.

TestLoadConfigEdge (2 tests):
- test_invalid_json_returns_none_or_raises: write malformed JSON to audit_config.json. Expect json.JSONDecodeError.
- test_empty_config_returns_empty_dict: write "{}" to config. Assert result == {}.

TestLoadManifestEdge (2 tests):
- test_invalid_json_raises: write malformed JSON to system_manifest.json. Expect json.JSONDecodeError.
- test_empty_manifest_returns_empty_dict: write "{}". Assert result == {}.

TestBuildJobkindMapEdge (3 tests):
- test_skips_files_without_job_kind: create .py files in backend/progress/ without JOB_KIND. Assert empty dict.
- test_single_quotes_job_kind: file with JOB_KIND = 'mtr1_calibration'. Assert found.
- test_double_quotes_job_kind: file with JOB_KIND = "mtr1_calibration". Assert found.

TestGetJobKindForClaim (3 tests):
- test_returns_none_for_unknown_claim: call with "FAKE-99" and empty index content. Assert None.
- test_extracts_from_markdown: provide index content with "## MTR-1\njob_kind: `mtr1_calibration`". Assert "mtr1_calibration".
- test_case_insensitive_job_kind_label: provide "## MTR-1\nJob_Kind: `mtr1_calibration`". Assert "mtr1_calibration".

TestFindTestFilesEdge (3 tests):
- test_no_tests_dir: patch REPO_ROOT to tmp_path with no tests/. Assert empty list.
- test_matches_by_content: create test file that mentions claim ID inside but not in filename. Assert found.
- test_counts_test_functions: create test file with 3 `def test_` functions. Assert count=3 in result tuple.

TestCheckInnovationsEdge (3 tests):
- test_missing_innovation_test_file: config maps innovation to nonexistent file. With mocked manifest returning 8 innovations. Assert returns False.
- test_zero_test_functions: config maps to file that exists but has no `def test_` functions. Assert returns False.
- test_innovation_not_in_config_is_advisory: manifest has innovation not in config map. Assert still returns True (advisory only).

TestCheckDemoScenariosEdge (2 tests):
- test_no_demos_dir: patch REPO_ROOT to tmp_path with no demos/client_scenarios/. Assert returns False.
- test_scenario_missing_verify_report: create demo dir with run_scenario.py but no VERIFY_REPORT.json. Assert returns False.

TestCheckPatentEdge (2 tests):
- test_missing_faults_file: config with patent section, manifest with ppa_number matching, innovations=8, but no known_faults.yaml. Assert returns False.
- test_deadline_passed: set ppa_filed to "2024-01-01" (>1 year ago). Assert returns False.

**File 3 — tests/scripts/test_agent_chronicle_pure.py (EXTEND +15 tests, append to existing 18):**

Read existing file first. Add these new test classes at the END:

TestReadManifestExtended (3 tests):
- test_returns_version_key: manifest with version="1.0.0". Assert result["version"] == "1.0.0".
- test_returns_active_claims: manifest with active_claims=["MTR-1"]. Assert key present.
- test_returns_verified_innovations: manifest with verified_innovations=["X"]. Assert key present.

TestReadClaimDomainsExtended (4 tests):
- test_empty_file: write empty string to scientific_claim_index.md. Assert returns [].
- test_no_domain_row: "## MTR-1\nSome text" with no **domain** row. Assert claim found with empty domain.
- test_multiple_claims_with_domains: two claim sections each with domain rows. Assert 2 tuples returned.
- test_heading_must_be_h2: "### MTR-1" (h3) should NOT match. Assert returns [].

TestCountTasksExtended (3 tests):
- test_only_done: file with only "Status: DONE" lines. Assert pending=0, done=N.
- test_only_pending: file with only "Status: PENDING" lines. Assert pending=N, done=0.
- test_empty_file: write empty file. Assert (0, 0).

TestFindPreviousChronicleExtended (5 tests):
- test_picks_latest_by_sort: create CHRONICLE_a.md and CHRONICLE_z.md. Assert picks CHRONICLE_z.md (reverse sort).
- test_extracts_claims_count: chronicle with "Claims: 15". Assert prev["claims"] == 15.
- test_extracts_tests_count: chronicle with "Tests: 500". Assert prev["tests"] == 500.
- test_extracts_innovations_count: chronicle with "Innovations: 8". Assert prev["innovations"] == 8.
- test_missing_numbers_not_in_dict: chronicle with no Claims/Tests/Innovations lines. Assert "claims" not in prev.

**File 4 — tests/scripts/test_agent_evolve_self_pure.py (EXTEND +20 tests, append to existing 20):**

Read existing file first. Add these new test classes at the END:

TestParseReportDateExtended (4 tests):
- test_extracts_from_middle_of_filename: "WEEKLY_REPORT_20260319_v2.md". Assert date 2026-03-19.
- test_multiple_date_groups_takes_first: "REPORT_20260101_20260202.md". Assert 2026-01-01.
- test_returns_none_for_no_digits: "README.md". Assert None.
- test_returns_none_for_short_digits: "report_123.md". Assert None.

TestAnalyzeReportsExtended (4 tests):
- test_empty_reports_dir: patch REPO_ROOT to tmp_path with empty reports/. Assert returns [].
- test_extracts_headers: write report with "## Section A\n### Sub B". Assert headers found.
- test_extracts_task_ids: write report with "TASK-001 and TASK-002". Assert task_ids has both.
- test_extracts_file_paths: write report with "`scripts/foo.py`". Assert files_mentioned includes it.

TestAnalyzePatternsExtended (5 tests):
- test_no_memory_dir: patch REPO_ROOT to tmp_path. Assert ([], []).
- test_invalid_json: write garbage to .agent_memory/patterns.json. Assert ([], []).
- test_all_with_hints: all patterns have fix_hint. Assert unaddressed is [].
- test_count_one_with_no_hint: pattern with count=1, no hint. Assert NOT in unaddressed (threshold is 2).
- test_first_seen_last_seen_preserved: pattern with first_seen and last_seen. Assert present in all_patterns.

TestAnalyzeHandlersExtended (4 tests):
- test_no_research_file: patch REPO_ROOT to tmp_path. Assert returns [].
- test_complex_handler: write file with execute_task_001 spanning 250 lines. Assert verdict="COMPLEX".
- test_multiple_handlers: write file with 2 handlers of different sizes. Assert 2 entries returned.
- test_handler_start_line: write file, check start field is correct (1-indexed).

TestCheckReportFrequencyExtended (3 tests):
- test_single_report: list with 1 report with date. Assert "insufficient data".
- test_all_none_dates: list with reports where date=None. Assert "insufficient data".
- test_exactly_7_day_gap: two reports 7 days apart. Assert "healthy" (not WARNING, since >7 triggers).
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -m pytest tests/scripts/test_agent_signals_pure.py tests/scripts/test_agent_audit_pure.py tests/scripts/test_agent_chronicle_pure.py tests/scripts/test_agent_evolve_self_pure.py -v --tb=short 2>&1 | tail -20</automated>
  </verify>
  <done>75+ new tests pass. Total test functions: test_agent_signals_pure=20, test_agent_audit_pure=20, test_agent_chronicle_pure=33, test_agent_evolve_self_pure=40.</done>
</task>

<task type="auto">
  <name>Task 2: Counter sync 1050 to NEW_COUNT</name>
  <files>
    system_manifest.json
    scripts/check_stale_docs.py
    CLAUDE.md
    CONTEXT_SNAPSHOT.md
    llms.txt
    AGENTS.md
    README.md
    index.html
  </files>
  <action>
After Task 1 tests pass, determine the new total test count:
```bash
python -m pytest tests/ -q 2>&1 | tail -3
```

Then update ALL counters from 1050 to NEW_COUNT:

1. system_manifest.json: update "test_count" value
2. scripts/check_stale_docs.py: update ALL required_strings entries that contain "1050" to NEW_COUNT. CRITICAL: also update the test count in the CONTENT_CHECKS dict for any file that references test count. Search for "1050" and replace all occurrences.
3. CLAUDE.md: replace "1050 tests" with "NEW_COUNT tests" and update the test count in the header comment line and any other occurrences. Search all "1050" occurrences.
4. CONTEXT_SNAPSHOT.md: replace all "1050" with NEW_COUNT
5. llms.txt: replace all "1050" with NEW_COUNT
6. AGENTS.md: replace all "1050" with NEW_COUNT
7. README.md: replace all "1050" with NEW_COUNT (badge and prose)
8. index.html: replace all "1050" with NEW_COUNT. NOTE: index.html has 11 places with test count INCLUDING prose text. Use a global search-replace.

IMPORTANT (UPDATE_PROTOCOL v1.1): check_stale_docs.py required strings MUST be updated in the SAME commit as the docs, or 13 files will report false PASS.

Branch: feat/coverage-boost-v8. Create branch before committing. Commit, push, create PR.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -m pytest tests/ -q 2>&1 | tail -3 && python scripts/check_stale_docs.py 2>&1 | tail -5 && python scripts/steward_audit.py 2>&1 | tail -3</automated>
  </verify>
  <done>All counters updated from 1050 to NEW_COUNT. check_stale_docs.py PASS. steward_audit.py PASS. Branch feat/coverage-boost-v8 pushed with PR created.</done>
</task>

</tasks>

<verification>
1. `python -m pytest tests/ -q` passes with NEW_COUNT total
2. `python scripts/check_stale_docs.py` reports PASS
3. `python scripts/steward_audit.py` reports STEWARD AUDIT: PASS
4. `python scripts/deep_verify.py` reports ALL 13 TESTS PASSED
5. No "1050" remains in any counter file
</verification>

<success_criteria>
- 75+ new tests created and passing
- All project counters synchronized to new total
- All CI gates pass (steward_audit, check_stale_docs, deep_verify)
- PR created on feat/coverage-boost-v8 branch
</success_criteria>

<output>
After completion, create `.planning/quick/260402-ltv-coverage-boost-v8-agent-signals-agent-au/260402-ltv-SUMMARY.md`
</output>
