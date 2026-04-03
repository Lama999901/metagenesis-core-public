# Phase 10: Coverage Hardening - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Test coverage reaches 90%+ by filling gaps in agent scripts. Current: 88% overall. deep_verify.py (0%) is excluded (untestable subprocess). Priority targets: check_stale_docs.py (no dedicated tests), agent_coverage.py run() (20%), agent_research.py (uncovered branches), agent_evolve_self.py (uncovered branches).

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure testing/infrastructure phase. Follow existing test patterns in tests/ directory. Use stdlib only.

Key facts from coverage report (2026-04-03):
- Overall: 87.7% (55 files, 7502 total lines, 919 uncovered)
- deep_verify.py: 0% (excluded — subprocess-based)
- agent_coverage.py run(): 20% covered
- agent_research.py main(): 44.4%
- check_stale_docs.py: 89% but no dedicated test file
- agent_evolve_self.py: 93% but analyze() needs coverage
- Target: 90%+ overall

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- tests/steward/ has 37 test files — established patterns
- tests/ has existing test_agent_*.py files for most agents
- conftest.py fixtures available

### Established Patterns
- Agent tests use monkeypatch and tmp_path
- CERT tests use dedicated test classes
- Coverage measured via pytest-cov

### Integration Points
- New test files must be in tests/ subdirectories
- check_stale_docs.py is a standalone script — test via subprocess or import

</code_context>

<specifics>
## Specific Ideas

Skip deep_verify.py load_module (untestable subprocess). Focus on scripts with lowest dedicated test coverage.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
