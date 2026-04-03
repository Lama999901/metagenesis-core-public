---
phase: quick
plan: 260330-uyi
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/agent_pr_creator.py
  - tests/test_agent_pr_creator.py
autonomous: true
requirements: [QUICK-TASK]

must_haves:
  truths:
    - "Running with --summary prints detected issues without creating branches or PRs"
    - "Running with --dry-run prints detected issues without creating branches or PRs"
    - "Stale counter detection compares system_manifest.json test_count against actual pytest collection count"
    - "Forbidden term detection scans docs/ scripts/ backend/ README.md index.html using safe_contexts exclusions"
    - "Manifest sync detection compares system_manifest.json version against latest git tag"
    - "When all checks pass, prints 'No auto-pr needed -- system current'"
    - "Script uses only stdlib, no external dependencies"
    - "Script is Windows-safe (subprocess.DEVNULL, utf-8 encoding)"
  artifacts:
    - path: "scripts/agent_pr_creator.py"
      provides: "Level 3 autonomous PR creator agent with 3 detectors"
      min_lines: 120
    - path: "tests/test_agent_pr_creator.py"
      provides: "Unit tests for all 3 detectors"
      min_lines: 40
  key_links:
    - from: "scripts/agent_pr_creator.py"
      to: "system_manifest.json"
      via: "json.load for test_count and version fields"
      pattern: "json\\.load.*system_manifest"
    - from: "scripts/agent_pr_creator.py"
      to: "pytest"
      via: "subprocess to collect test count"
      pattern: "pytest.*--collect-only"
---

<objective>
Replace the 24-line stub scripts/agent_pr_creator.py with a real Level 3 agent (~150 lines, stdlib only, Windows-safe) that has three detectors: stale counter detection, forbidden term detection, and manifest sync detection. Add tests.

Purpose: Enable autonomous detection of stale counters, forbidden terms, and manifest version mismatches so the agent system can self-diagnose and auto-fix where safe.
Output: Working agent_pr_creator.py with tests.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/agent_pr_creator.py (current stub — replace entirely)
@system_manifest.json (source of test_count and version fields)
@scripts/agent_evolution.py lines 149-205 (reference for forbidden terms check_forbidden() pattern including safe_contexts list)
</context>

<interfaces>
<!-- From system_manifest.json: -->
Keys used by detectors:
- "test_count": 601 (integer)
- "version": "0.8.0" (string)

<!-- From agent_evolution.py lines 149-205: -->
Forbidden terms list and safe_contexts to replicate:
```python
terms = ["tamper-proof", "GPT-5", "unforgeable", "blockchain", "100% test success"]
dirs = ["docs/", "scripts/", "backend/", "index.html", "README.md"]
safe_contexts = ["NOT blockchain", "NOT tamper-proof", "not blockchain",
                 "not tamper-proof", "Not blockchain", "Not tamper-proof",
                 "say \"tamper-evident\"", "tamper-evident",
                 "BANNED", "never say", "Never say", "never write", "Never write",
                 "→", "don't use"]
```
Self-exclusion: skip files containing "agent_pr_creator" or "deep_verify" or "agent_evolution" in path.
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Implement real agent_pr_creator.py with 3 detectors and tests</name>
  <files>scripts/agent_pr_creator.py, tests/test_agent_pr_creator.py</files>
  <behavior>
    - detect_stale_counters(): reads system_manifest.json test_count, runs `python -m pytest tests/ --collect-only -q` via subprocess, compares counts. Returns dict with "stale" bool, "manifest_count" int, "actual_count" int. In --dry-run/--summary mode, prints finding but does NOT create branch/commit/push.
    - detect_stale_counters() auto-fix mode (no --summary/--dry-run): if mismatch, creates branch `auto-fix/stale-counter-YYYYMMDD`, updates system_manifest.json test_count, commits and pushes.
    - detect_forbidden_terms(): scans docs/ scripts/ backend/ README.md index.html for banned terms, excludes lines with safe_contexts. Returns list of findings. NEVER auto-fixes (human must fix). Skips own file, deep_verify, agent_evolution.
    - detect_manifest_sync(): reads system_manifest.json version, runs `git describe --tags --abbrev=0` for latest tag, compares. Returns dict with "synced" bool. Advisory only, prints warning if mismatch.
    - main() with --summary and --dry-run flags (both equivalent): runs all 3 detectors, prints results, exits 0.
    - main() without flags: runs all 3 detectors, auto-fixes stale counters if found, prints 'No auto-pr needed -- system current' if all clean.
    - All subprocess calls use subprocess.DEVNULL for stderr (Windows-safe, no shell redirection).
    - All file reads use encoding='utf-8', errors='ignore'.
  </behavior>
  <action>
    1. Write tests/test_agent_pr_creator.py FIRST with tests for:
       - test_detect_stale_counters_clean (mock subprocess to return matching count)
       - test_detect_stale_counters_mismatch (mock subprocess to return different count)
       - test_detect_forbidden_terms_clean (mock file reads with no violations)
       - test_detect_forbidden_terms_with_safe_context (ensure safe contexts are skipped)
       - test_detect_manifest_sync_match (mock git tag matching version)
       - test_main_summary_mode (ensure --summary prints but does not branch)
       Use unittest.mock to patch subprocess.run and Path.read_text.

    2. Run tests — confirm RED (ImportError since functions don't exist yet).

    3. Replace scripts/agent_pr_creator.py entirely. Structure:
       - REPO_ROOT = Path(__file__).resolve().parent.parent
       - detect_stale_counters(dry_run=False) -> dict
         - Load system_manifest.json with json.load, get test_count
         - Run subprocess.run(["python", "-m", "pytest", "tests/", "--collect-only", "-q"], capture_output=True, text=True, cwd=str(REPO_ROOT), stderr=subprocess.DEVNULL)
         - Parse last line of stdout for "N tests collected" or count lines not starting with "<"
         - Actually: parse stdout — look for line matching r"(\d+) tests? collected"
         - Compare. If mismatch and not dry_run: create branch, update manifest, commit, push using subprocess git calls.
         - Return {"stale": bool, "manifest_count": int, "actual_count": int}

       - detect_forbidden_terms() -> list[str]
         - Same terms and safe_contexts as agent_evolution.py (see interfaces block above)
         - Walk dirs, read files, check term.lower() in line.lower(), skip safe_contexts
         - Skip files with "agent_pr_creator" or "deep_verify" or "agent_evolution" in path
         - Return list of "'{term}' in {filepath}" strings

       - detect_manifest_sync() -> dict
         - Load version from system_manifest.json
         - Run git describe --tags --abbrev=0, strip "v" prefix if present
         - Compare. Return {"synced": bool, "manifest_version": str, "tag_version": str}

       - main():
         - Parse sys.argv for --summary or --dry-run
         - Run all 3 detectors
         - Print results
         - If not dry_run and stale counters found: auto-fix already handled inside detect_stale_counters
         - If all clean: print "No auto-pr needed -- system current"
         - Return 0

    4. Run tests — confirm GREEN.

    Keep script under ~150-170 lines. Use only stdlib (pathlib, json, subprocess, sys, re, datetime).
    Do NOT use grep shell command — use pure Python file scanning (Windows-safe).
    Use subprocess.DEVNULL for stderr on all subprocess calls.
    Use encoding='utf-8', errors='ignore' for all file reads.
  </action>
  <verify>
    <automated>python -m pytest tests/test_agent_pr_creator.py -x -q</automated>
  </verify>
  <done>
    - scripts/agent_pr_creator.py is 120+ lines with 3 working detectors
    - tests/test_agent_pr_creator.py passes with 6+ tests
    - `python scripts/agent_pr_creator.py --summary` runs without error and prints status
    - Script uses only stdlib, is Windows-safe
  </done>
</task>

<task type="auto">
  <name>Task 2: Smoke test and verify gates</name>
  <files>scripts/agent_pr_creator.py</files>
  <action>
    1. Run `python scripts/agent_pr_creator.py --summary` and verify it prints detector results and exits 0.
    2. Run `python scripts/agent_pr_creator.py --dry-run` and verify same behavior as --summary.
    3. Run the full test suite to ensure no regressions: `python -m pytest tests/ -q --tb=short`
    4. Run `python scripts/steward_audit.py` to verify STEWARD AUDIT: PASS.
    5. Run `python scripts/agent_diff_review.py` to verify DIFF REVIEW PASSED.
    6. If all gates pass, commit on branch fix/agent-pr-creator-real and push.
  </action>
  <verify>
    <automated>python scripts/agent_pr_creator.py --summary && python -m pytest tests/ -q --tb=short</automated>
  </verify>
  <done>
    - agent_pr_creator.py --summary runs cleanly, prints detector output
    - All 601+ tests pass (no regressions)
    - Steward audit passes
    - Changes committed on fix/agent-pr-creator-real and pushed
  </done>
</task>

</tasks>

<verification>
- `python scripts/agent_pr_creator.py --summary` exits 0, prints detector results
- `python -m pytest tests/test_agent_pr_creator.py -x -q` passes
- `python -m pytest tests/ -q` shows 601+ tests pass
- `python scripts/steward_audit.py` shows STEWARD AUDIT: PASS
</verification>

<success_criteria>
- Stub replaced with real ~150-line agent with 3 detectors
- All detectors work: stale counters, forbidden terms, manifest sync
- --summary/--dry-run mode prints without side effects
- Windows-safe (subprocess.DEVNULL, utf-8 encoding, no shell commands)
- Stdlib only, no external dependencies
- All existing tests still pass
- Committed and pushed on fix/agent-pr-creator-real
</success_criteria>

<output>
After completion, create `.planning/quick/260330-uyi-replace-stub-agent-pr-creator-py-with-re/260330-uyi-SUMMARY.md`
</output>
