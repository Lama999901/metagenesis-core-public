---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/scripts/test_agent_evolution_mocked.py
  - tests/scripts/test_agent_research_pure.py
  - tests/scripts/test_agent_coverage_pure.py
  - scripts/check_stale_docs.py
  - system_manifest.json
  - CLAUDE.md
  - CONTEXT_SNAPSHOT.md
  - llms.txt
  - AGENTS.md
  - README.md
  - index.html
autonomous: true
requirements: [coverage-boost-v7]

must_haves:
  truths:
    - "75 new tests pass across 3 new test files"
    - "All counters updated from 966 to new total"
    - "python -m pytest tests/ -q passes with new count"
    - "python scripts/check_stale_docs.py passes with updated rules"
  artifacts:
    - path: "tests/scripts/test_agent_evolution_mocked.py"
      provides: "35 tests for agent_evolution.py check functions"
    - path: "tests/scripts/test_agent_research_pure.py"
      provides: "20 tests for agent_research.py pure functions"
    - path: "tests/scripts/test_agent_coverage_pure.py"
      provides: "20 tests for agent_coverage.py pure functions"
  key_links:
    - from: "tests/scripts/test_agent_evolution_mocked.py"
      to: "scripts/agent_evolution.py"
      via: "import + mock subprocess calls"
    - from: "tests/scripts/test_agent_research_pure.py"
      to: "scripts/agent_research.py"
      via: "import + pure function testing"
    - from: "tests/scripts/test_agent_coverage_pure.py"
      to: "scripts/agent_coverage.py"
      via: "import + pure function testing"
---

<objective>
Coverage boost v7: Add 75 tests for agent_evolution.py, agent_research.py, and agent_coverage.py, then sync all counters.

Purpose: Increase test coverage of the agent infrastructure scripts that currently have zero test coverage.
Output: 3 new test files, updated counters across all docs.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/agent_evolution.py
@scripts/agent_research.py
@scripts/agent_coverage.py
@tests/scripts/test_agent_chronicle_pure.py (pattern reference)

<interfaces>
<!-- agent_evolution.py: 19 check functions + run_gap_analysis + main -->
<!-- Each check function calls subprocess via run() and returns True/False -->
<!-- check_stale_docs() returns (bool, list) -->
<!-- check_tests() returns (bool, int) -->
<!-- check_manifest(actual_test_count) takes int, returns bool -->
<!-- check_claude_md(actual_count) takes int, returns bool -->
<!-- check_forbidden() scans files for banned terms, returns bool -->
<!-- run_gap_analysis(test_count) returns list of gap strings -->
<!-- check_coverage() parses coverage output, returns bool -->
<!-- check_pr_review() checks git diff for untested files, returns bool -->

<!-- agent_research.py pure functions: -->
<!-- parse_tasks(content: str) -> list[dict] with keys: id, title, status, priority, output, description -->
<!-- find_first_pending(tasks: list[dict]) -> dict | None -->
<!-- mark_task_done(task_id: str, tasks_path: Path) -> None (writes file) -->
<!-- generate_tasks(tasks_path: Path) -> int (count added) -->
<!-- generate_coverage_tasks(tasks_path: Path) -> int (count added) -->

<!-- agent_coverage.py pure functions: -->
<!-- extract_functions(filepath: Path) -> list[dict] with keys: name, start, end, indent -->
<!-- get_function_coverage(functions, missing_lines, executed_lines) -> list[dict] -->
<!-- load_pending_tasks() -> list[str] (pending task titles) -->
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create 3 test files (75 tests total)</name>
  <files>tests/scripts/test_agent_evolution_mocked.py, tests/scripts/test_agent_research_pure.py, tests/scripts/test_agent_coverage_pure.py</files>
  <action>
Create 3 test files following the pattern in tests/scripts/test_agent_chronicle_pure.py (import via sys.path, use tmp_path, mock subprocess/REPO_ROOT).

**File 1: tests/scripts/test_agent_evolution_mocked.py (35 tests)**

Mock `agent_evolution.run()` to return controlled (stdout, returncode) tuples. Mock REPO_ROOT to tmp_path where needed. Group tests by check function:

- TestCheckSteward (2 tests): pass (returncode=0, "PASS" in stdout), fail (returncode=1)
- TestCheckTests (3 tests): pass with count extraction ("5 passed"), fail (returncode=1), zero count when no match
- TestCheckDeepVerify (2 tests): pass ("ALL" + "PASSED" in stdout), fail
- TestCheckStaleDocs (3 tests): pass ("All critical documentation is current"), fail with STALE lines, no STALE but nonzero returncode
- TestCheckManifest (4 tests): pass (manifest test_count matches actual, 20 claims), fail mismatch test_count, fail wrong claims count, file missing
- TestCheckForbidden (3 tests): clean files, file with "tamper-proof" (real hit), file with "tamper-proof" in safe context line containing "BANNED" (should pass)
- TestCheckClaudeMd (4 tests): pass (contains count + "v0.8.0"), missing count, missing version, merge conflict markers
- TestCheckCoverage (3 tests): pass above threshold, fail below threshold, tool failure (returncode != 0 returns True)
- TestCheckBranchSync (2 tests): up to date (run returns "0"), behind (run returns "5")
- TestCheckPrReview (2 tests): no changes (run returns ""), changed py with test ref found
- TestCheckWatchlist (2 tests): pass with "5/5 files watched (0 unwatched)", pass with no match pattern
- TestRunGapAnalysis (3 tests): all dirs exist with test files (no gaps), missing dir with cross-domain match, missing dir no cross-domain (gap returned)
- TestCheckAutoPr (2 tests): pass ("no auto-pr needed"), pass on nonzero code with advisory

For check functions that call `run()`: use `@patch("agent_evolution.run")`. For those that read files via REPO_ROOT: use `@patch("agent_evolution.REPO_ROOT", tmp_path)`. For check_forbidden which does both: mock run() for grep calls AND patch REPO_ROOT with tmp_path containing test files.

For run_gap_analysis: patch REPO_ROOT to tmp_path, create tests/ subdirs with test_*.py files to simulate domains.

**File 2: tests/scripts/test_agent_research_pure.py (20 tests)**

Test pure parsing/utility functions. No subprocess mocking needed for most.

- TestParseTasks (5 tests):
  - empty string returns []
  - single task block parsed correctly (all 6 fields)
  - multiple tasks returns correct count
  - missing fields get empty string
  - preamble text before first ### is ignored

- TestFindFirstPending (3 tests):
  - returns first PENDING task
  - returns None when all DONE
  - returns None on empty list

- TestMarkTaskDone (3 tests):
  - replaces PENDING with DONE (date) for correct task_id
  - does not modify other tasks
  - works with multiple tasks in file

- TestGenerateTasks (5 tests): (uses tmp_path for both patterns.json and AGENT_TASKS.md)
  - returns 0 when patterns.json missing
  - returns 0 when no patterns have count >= 2
  - adds task for pattern with count >= 2 and no fix_hint
  - skips pattern already in content (key[:40] present)
  - returns correct count of added tasks
  Patch REPO_ROOT for .agent_memory path.

- TestGenerateCoverageTasks (4 tests): (uses tmp_path for COVERAGE_REPORT and AGENT_TASKS.md)
  - returns 0 when no reports exist
  - returns 0 when no Zero-Coverage section
  - adds tasks for files with >= 2 uncovered functions
  - excludes infrastructure scripts (agent_*, steward_audit, etc.)
  Patch REPO_ROOT for reports/ and AGENT_TASKS.md paths.

**File 3: tests/scripts/test_agent_coverage_pure.py (20 tests)**

- TestExtractFunctions (7 tests):
  - empty file returns []
  - single top-level def extracted (name, start, end, indent=0)
  - nested def (indent > 0) extracted
  - multiple defs: end of first = start of second
  - class method extracted with correct indent
  - file with syntax errors: graceful (returns what it can)
  - nonexistent file returns []

- TestGetFunctionCoverage (8 tests):
  - empty functions list returns []
  - fully covered function: 100% coverage
  - fully missing function: 0% coverage
  - partial coverage: correct percentage
  - function with no code lines in executed/missing: skipped
  - multiple functions: each computed independently
  - edge case: single-line function
  - missing_lines and executed_lines overlap handling

- TestLoadPendingTasks (5 tests): (patch REPO_ROOT to tmp_path)
  - returns [] when AGENT_TASKS.md missing
  - returns [] when no PENDING tasks
  - returns titles of PENDING tasks only
  - ignores DONE tasks
  - handles multiple PENDING tasks

For extract_functions: create tmp_path Python files with known content.
For get_function_coverage: pass synthetic lists directly (no file I/O).
For load_pending_tasks: write AGENT_TASKS.md to tmp_path with known content.

**Common patterns across all files:**
- Use `sys.path.insert(0, str(REPO_ROOT / "scripts"))` to import
- Use `from unittest.mock import patch, MagicMock`
- Use `tmp_path` fixture for file operations
- Patch REPO_ROOT to tmp_path where functions read files
- Every test must assert a specific value, not just "no exception"
  </action>
  <verify>
    <automated>python -m pytest tests/scripts/test_agent_evolution_mocked.py tests/scripts/test_agent_research_pure.py tests/scripts/test_agent_coverage_pure.py -v --tb=short 2>&1 | tail -20</automated>
  </verify>
  <done>75 new tests pass. No existing tests broken.</done>
</task>

<task type="auto">
  <name>Task 2: Counter sync 966 to new total</name>
  <files>system_manifest.json, scripts/check_stale_docs.py, CLAUDE.md, CONTEXT_SNAPSHOT.md, llms.txt, AGENTS.md, README.md, index.html</files>
  <action>
After Task 1 tests pass, run `python -m pytest tests/ -q --tb=no` to get the exact new count (should be 966 + 75 = 1041).

Update the test count from 966 to NEW_COUNT in all files per UPDATE_PROTOCOL v1.1:

1. **system_manifest.json**: update `"test_count"` value
2. **scripts/check_stale_docs.py**: update ALL required_strings entries that contain "966" to new count. This is CRITICAL -- stale rules trap.
3. **CLAUDE.md**: replace "906 tests" with "NEW_COUNT tests" (note: CLAUDE.md may still say 906 from last major update; search for both 906 and 966)
4. **CONTEXT_SNAPSHOT.md**: update test count references
5. **llms.txt**: update test count references
6. **AGENTS.md**: update test count references
7. **README.md**: update test count in badge and text
8. **index.html**: update ALL instances (there are 11 places per BUG 6). Use find-and-replace for both the number in prose and in data attributes.

Search for BOTH "906" and "966" in all files since some may not have been updated from the v6 boost.

Run `python scripts/check_stale_docs.py` to verify no stale references remain.
Run `python scripts/steward_audit.py` to verify governance passes.
  </action>
  <verify>
    <automated>python -m pytest tests/ -q --tb=no && python scripts/check_stale_docs.py && python scripts/steward_audit.py</automated>
  </verify>
  <done>All counters show new test count. check_stale_docs.py passes. steward_audit.py passes. Full pytest suite passes with new count.</done>
</task>

</tasks>

<verification>
- `python -m pytest tests/ -q --tb=no` passes with 1041+ tests
- `python scripts/check_stale_docs.py` reports all docs current
- `python scripts/steward_audit.py` reports PASS
- `python scripts/deep_verify.py` reports ALL 13 TESTS PASSED
</verification>

<success_criteria>
- 75 new tests added across 3 files in tests/scripts/
- All counters synchronized to new total
- All verification gates pass
</success_criteria>

<output>
After completion, create `.planning/quick/260401-uln-coverage-boost-v7-agent-evolution-agent-/260401-uln-SUMMARY.md`
</output>
