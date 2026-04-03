---
phase: quick-260319-nwt
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/progress/agent_drift_monitor.py
  - backend/progress/runner.py
  - reports/scientific_claim_index.md
  - reports/canonical_state.md
  - tests/agent/test_agent_drift01.py
  - tests/agent/__init__.py
  - index.html
  - README.md
  - CLAUDE.md
  - AGENTS.md
  - CONTEXT_SNAPSHOT.md
  - llms.txt
  - system_manifest.json
  - reports/scientific_claim_index.md
  - CONTRIBUTING.md
  - paper.md
  - UPDATE_PROTOCOL.md
  - EVOLUTION_LOG.md
autonomous: true
requirements: [AGENT-DRIFT-01, COUNTER-SYNC-v060]
must_haves:
  truths:
    - "run_agent_drift_monitor() returns valid result with mtr_phase='AGENT-DRIFT-01'"
    - "Composite drift <= 20% means PASS, > 20% means FAIL"
    - "runner.py dispatches agent_drift_monitor job kind"
    - "6 tests pass: pass, fail-35%, determinism, step-chain-tamper, semantic-stripping, boundary-20%"
    - "All counters updated: 14->15 claims, 526->532 tests, v0.5.0->v0.6.0"
  artifacts:
    - path: "backend/progress/agent_drift_monitor.py"
      provides: "AGENT-DRIFT-01 claim implementation"
      exports: ["JOB_KIND", "run_agent_drift_monitor"]
    - path: "tests/agent/test_agent_drift01.py"
      provides: "6 tests for AGENT-DRIFT-01"
      min_lines: 80
  key_links:
    - from: "backend/progress/runner.py"
      to: "backend/progress/agent_drift_monitor.py"
      via: "import and dispatch block"
      pattern: "agent_drift_monitor"
    - from: "tests/agent/test_agent_drift01.py"
      to: "backend/progress/agent_drift_monitor.py"
      via: "import run_agent_drift_monitor"
      pattern: "from backend.progress.agent_drift_monitor import"
---

<objective>
Implement Claim #15 AGENT-DRIFT-01 following the mandatory 6-step new claim procedure, then update all counters for v0.6.0 release.

Purpose: AGENT-DRIFT-01 monitors AI agent quality drift by comparing current agent metrics (tests_per_phase, pass_rate, regressions, verifier_iterations) against a verified baseline. Composite drift beyond 20% signals correction is required. This is the first claim where AI agents monitor their own quality through the same verification protocol they extend.

Output: Working claim with 6 tests, registered in all docs, all counters synced to 15 claims / 532 tests / v0.6.0.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@CLAUDE.md (6-step procedure, step chain template, return structure, banned terms)
@backend/progress/drift_monitor.py (structural template - closest existing claim)
@backend/progress/runner.py (dispatch logic - add new block at end before registered list)
@reports/scientific_claim_index.md (registration format)
@reports/canonical_state.md (claims list)
@tests/steward/test_drift01_calibration_anchor.py (test pattern reference)

<interfaces>
<!-- From drift_monitor.py - the structural pattern to follow -->
```python
# Every claim module exports:
JOB_KIND = "agent_drift_monitor"  # unique job kind string

def run_agent_drift_monitor(...) -> Dict[str, Any]:
    # Returns:
    # {
    #   "mtr_phase": "AGENT-DRIFT-01",
    #   "inputs": {...},
    #   "result": {...},
    #   "status": "SUCCEEDED",
    #   "execution_trace": [4 steps],
    #   "trace_root_hash": sha256_hex_string
    # }
```

<!-- From runner.py - dispatch pattern -->
```python
# Each claim block in _execute_job_logic follows this pattern:
from backend.progress.module import JOB_KIND as X_KIND, run_fn as run_x
if payload.get("kind") == X_KIND:
    p = payload
    return run_x(param1=type(p.get("param1", default)), ...)
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement AGENT-DRIFT-01 claim + register (Steps 1-4)</name>
  <files>
    backend/progress/agent_drift_monitor.py
    backend/progress/runner.py
    reports/scientific_claim_index.md
    reports/canonical_state.md
  </files>
  <action>
**Step 1: Create backend/progress/agent_drift_monitor.py**

Model structure on drift_monitor.py. The claim measures agent quality drift across 4 metrics.

Module constants:
```python
JOB_KIND = "agent_drift_monitor"
ALGORITHM_VERSION = "v1"
METHOD = "weighted_composite_drift"
DEFAULT_DRIFT_THRESHOLD_PCT = 20.0
```

Create `compute_agent_drift(baseline: dict, current: dict, weights: dict = None) -> dict`:
- baseline and current each have keys: tests_per_phase (float), pass_rate (float 0-1), regressions (int), verifier_iterations (float)
- Default weights: {"tests_per_phase": 0.3, "pass_rate": 0.3, "regressions": 0.2, "verifier_iterations": 0.2}
- For each metric, compute per_metric_drift_pct = abs(current - baseline) / max(abs(baseline), 1e-9) * 100.0
  - Special case for regressions: baseline is 0, so drift = current_regressions * 100.0 (each regression = 100% drift unit); if baseline > 0, use standard formula
  - Special case for pass_rate: if baseline is 1.0, drift = (1.0 - current) * 100.0 (direct percentage point loss * 100 to convert to percent scale matching other metrics). Actually simpler: just use abs(current - baseline) / max(abs(baseline), 1e-9) * 100.0 for all, but for regressions with baseline=0, use abs(current - 0) / 1.0 * 100 = current * 100 (i.e., denominator becomes 1 when baseline is 0)
- composite_drift_pct = sum(weight_i * per_metric_drift_pct_i) for all metrics, rounded to 6 decimal places
- drift_detected = composite_drift_pct > threshold (strict >)
- Return dict with: baseline, current, weights, per_metric_drift, composite_drift_pct, drift_threshold_pct, drift_detected, correction_required (= drift_detected)

Create `run_agent_drift_monitor(baseline: dict, current: dict, weights: dict = None, drift_threshold_pct: float = DEFAULT_DRIFT_THRESHOLD_PCT) -> dict`:
- Validate baseline and current are dicts with required keys
- Validate drift_threshold_pct > 0
- Call compute_agent_drift
- Build 4-step chain using EXACT template from CLAUDE.md:
  - Step 1 "init_params": hash of {"baseline": baseline, "current": current, "drift_threshold_pct": drift_threshold_pct}, prev="genesis"
  - Step 2 "compute": hash of {"composite_drift_pct": result_composite, "per_metric_drift": per_metric_dict}, prev=step1
  - Step 3 "metrics": hash of {"composite_drift_pct": result_composite, "drift_detected": bool}, prev=step2
  - Step 4 "threshold_check": hash of {"passed": not drift_detected, "threshold": drift_threshold_pct}, prev=step3 -- note "passed" means within threshold
- Return exact structure:
```python
{
    "mtr_phase": "AGENT-DRIFT-01",
    "algorithm_version": ALGORITHM_VERSION,
    "method": METHOD,
    "inputs": {
        "baseline": baseline,
        "current": current,
        "weights": weights_used,
        "drift_threshold_pct": drift_threshold_pct,
    },
    "result": drift_result,  # from compute_agent_drift
    "status": "SUCCEEDED",
    "execution_trace": _trace,
    "trace_root_hash": trace_root_hash,
}
```

No numpy. No external deps. Stdlib only. No banned terms.

**Step 2: Add dispatch to runner.py**

Add a new dispatch block BEFORE the `registered = [...]` line at the bottom of `_execute_job_logic`. Follow the exact pattern of the DRIFT-01 block. Also add AGENT_DRIFT01_KIND to the `registered` list.

Note: runner.py has duplicate imports (SYSID1_KIND, DATAPIPE1_KIND, DRIFT01_KIND, MLBENCH1_KIND, DTFEM1_KIND imported at top AND again inline). Do NOT clean up duplicates -- that risks breaking things. Just add the new block cleanly.

```python
from backend.progress.agent_drift_monitor import JOB_KIND as AGENT_DRIFT01_KIND, run_agent_drift_monitor as run_agent_drift01
if payload.get("kind") == AGENT_DRIFT01_KIND:
    p = payload
    baseline = {
        "tests_per_phase": float(p.get("baseline_tests_per_phase", 47)),
        "pass_rate": float(p.get("baseline_pass_rate", 1.0)),
        "regressions": int(p.get("baseline_regressions", 0)),
        "verifier_iterations": float(p.get("baseline_verifier_iterations", 1.2)),
    }
    current = {
        "tests_per_phase": float(p.get("current_tests_per_phase", 47)),
        "pass_rate": float(p.get("current_pass_rate", 1.0)),
        "regressions": int(p.get("current_regressions", 0)),
        "verifier_iterations": float(p.get("current_verifier_iterations", 1.2)),
    }
    return run_agent_drift01(
        baseline=baseline,
        current=current,
        drift_threshold_pct=float(p.get("drift_threshold_pct", 20.0)),
    )
```

Add AGENT_DRIFT01_KIND to the registered list at the end.

**Step 3: Register in scientific_claim_index.md**

Add a new section before the "Protocol Capabilities" section, following the exact format of DRIFT-01 entry:

```markdown
## AGENT-DRIFT-01

| Field | Value |
|-------|--------|
| **claim_id** | AGENT-DRIFT-01 |
| **domain** | Agent Quality / Recursive Self-Verification |
| **job_kind** | `agent_drift_monitor` |
| **reproduction** | `python -m pytest tests/agent/test_agent_drift01.py -v` |
| **evidence_fields** | Result lives under `job_snapshot.result`. Contains `mtr_phase` (AGENT-DRIFT-01), `inputs` (baseline, current, weights, drift_threshold_pct), `result` (composite_drift_pct, per_metric_drift, drift_detected, correction_required). |
| **V&V thresholds** | `composite_drift_pct <= 20.0`. `drift_detected` False when within threshold. |
| **notes (canary vs normal)** | Same as all other claims: runs in normal or canary mode. |
```

Update the footer line: 14 claims -> 15 claims.

**Step 4: Add to canonical_state.md**

Add AGENT-DRIFT-01 to the end of the `current_claims_list` pipe-separated line.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -c "from backend.progress.agent_drift_monitor import run_agent_drift_monitor, JOB_KIND; r = run_agent_drift_monitor(baseline={'tests_per_phase':47,'pass_rate':1.0,'regressions':0,'verifier_iterations':1.2}, current={'tests_per_phase':47,'pass_rate':1.0,'regressions':0,'verifier_iterations':1.2}); assert r['mtr_phase']=='AGENT-DRIFT-01'; assert r['result']['drift_detected']==False; assert len(r['execution_trace'])==4; print('CLAIM OK')"</automated>
  </verify>
  <done>
    - agent_drift_monitor.py exists with JOB_KIND='agent_drift_monitor' and run_agent_drift_monitor()
    - 4-step chain produces trace_root_hash
    - runner.py dispatches agent_drift_monitor kind
    - Claim registered in scientific_claim_index.md and canonical_state.md
  </done>
</task>

<task type="auto">
  <name>Task 2: Create tests/agent/test_agent_drift01.py (6 tests)</name>
  <files>
    tests/agent/__init__.py
    tests/agent/test_agent_drift01.py
  </files>
  <action>
Create `tests/agent/__init__.py` (empty file).

Create `tests/agent/test_agent_drift01.py` with exactly 6 tests. Follow the pattern from test_drift01_calibration_anchor.py.

```python
"""
AGENT-DRIFT-01 Tests -- Agent Quality Drift Monitor
6 tests: pass, fail (35% drift), determinism, step chain tamper,
semantic stripping, boundary (exactly 20%).
"""
import pytest
import copy
from backend.progress.agent_drift_monitor import (
    run_agent_drift_monitor,
    compute_agent_drift,
    JOB_KIND,
    DEFAULT_DRIFT_THRESHOLD_PCT,
)
```

**BASELINE constant** used across tests:
```python
BASELINE = {
    "tests_per_phase": 47,
    "pass_rate": 1.0,
    "regressions": 0,
    "verifier_iterations": 1.2,
}
```

**Test 1: test_pass_no_drift** -- current == baseline, composite_drift_pct == 0, drift_detected is False, mtr_phase == "AGENT-DRIFT-01", status == "SUCCEEDED", len(execution_trace) == 4, trace_root_hash is a 64-char hex string.

**Test 2: test_fail_high_drift** -- current with significantly degraded metrics: tests_per_phase=30, pass_rate=0.85, regressions=3, verifier_iterations=2.0. Composite drift should be well above 20%. Assert drift_detected is True, correction_required is True.

**Test 3: test_determinism** -- Run twice with identical inputs, assert trace_root_hash is identical both times. Run with slightly different current values, assert trace_root_hash differs.

**Test 4: test_step_chain_tamper_detection** -- Run normally, get result. Tamper with execution_trace by modifying step 2's hash (change one character). Then recompute what step 3's hash SHOULD be given step 2's original hash. Assert the tampered step 2 hash != the original step 2 hash. This proves the chain is linked -- changing any step invalidates downstream hashes.

**Test 5: test_semantic_stripping** -- Run normally, get result. Assert "mtr_phase" key exists. Remove "mtr_phase" from result copy. Assert "mtr_phase" not in stripped result. Also assert result has "inputs" and "result" keys (semantic verifier requires these). Assert result["result"] contains "composite_drift_pct" and "drift_detected".

**Test 6: test_boundary_exactly_20pct** -- Construct current metrics that produce composite_drift_pct of exactly 20.0% (or as close as floating point allows). Since threshold uses strict > comparison, exactly 20.0 should NOT trigger drift_detected. Use carefully chosen values. Example approach: since default weights are 0.3, 0.3, 0.2, 0.2 and we need composite = 20.0, we can set all per-metric drifts to 20% uniformly. For tests_per_phase: baseline=47, current=47*1.2=56.4 (20% drift). For pass_rate: baseline=1.0, current=0.8 (20% drift since abs(0.8-1.0)/1.0*100=20). For regressions: baseline=0, special case, current would contribute current*100*weight. So set regressions baseline to some nonzero value, say baseline regressions=5, current=6 (20% drift). For verifier_iterations: baseline=1.2, current=1.44 (20% drift). Use custom baseline with regressions=5 to avoid the special case. Assert drift_detected is False (20.0 is NOT > 20.0).
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -m pytest tests/agent/test_agent_drift01.py -v</automated>
  </verify>
  <done>
    - tests/agent/ directory exists with __init__.py
    - 6 tests all pass
    - Tests cover: pass, fail, determinism, step chain integrity, semantic keys, boundary
  </done>
</task>

<task type="auto">
  <name>Task 3: Update all counters 14->15 claims, 526->532 tests, v0.5.0->v0.6.0, then verify + branch + commit + push</name>
  <files>
    index.html
    README.md
    CLAUDE.md
    AGENTS.md
    CONTEXT_SNAPSHOT.md
    llms.txt
    system_manifest.json
    CONTRIBUTING.md
    paper.md
    UPDATE_PROTOCOL.md
    EVOLUTION_LOG.md
  </files>
  <action>
**IMPORTANT: First run the full test suite to get the ACTUAL new test count.** The 6 new tests bring it from 526 to 532, but verify by running `python -m pytest tests/ -q --co` (collect only) to get the real count. Use that real count for all updates below.

**Counter updates across ALL files (skip .claude/worktrees/ and ppa/CLAIMS_DRAFT.md which is FROZEN):**

1. **Claims count: 14 -> 15** everywhere it appears
2. **Test count: 526 -> {actual count}** everywhere it appears
3. **Version: v0.5.0 -> v0.6.0** everywhere it appears (but NOT in git tags or historical references -- only current version references)

**File-by-file guidance:**

- **index.html**: Has 11+ places with counts including prose text. Use find-and-replace carefully. Update claims (14->15), tests (526->{N}), version (0.5.0->0.6.0). Check both numeric and prose mentions.
- **README.md**: Update claims, tests, version references.
- **CLAUDE.md**: Update "14 claims", "526 tests" (if present), "v0.5.0", the ACTIVE CLAIMS table (add AGENT-DRIFT-01 row), the CURRENT STATE block. Update the header line "v0.5.0 LIVE | 14 claims | 511 tests" -- note 511 is old, it should be the current count.
- **AGENTS.md**: Update claims/tests/version counters.
- **CONTEXT_SNAPSHOT.md**: Update all counters.
- **llms.txt**: Update all counters.
- **system_manifest.json**: Update version, claims count, test count.
- **CONTRIBUTING.md**: Update any counter references.
- **paper.md**: Update claims/tests if mentioned.
- **UPDATE_PROTOCOL.md**: Update if it has counters.
- **EVOLUTION_LOG.md**: Add v0.6.0 entry if appropriate; update counters.

Add AGENT-DRIFT-01 to the CLAUDE.md ACTIVE CLAIMS table:
```
| AGENT-DRIFT-01 | backend/progress/agent_drift_monitor.py | composite_drift <= 20% | -- |
```

**After all updates, run ALL verification gates:**
```bash
python scripts/steward_audit.py        # STEWARD AUDIT: PASS
python -m pytest tests/ -q             # all pass
python scripts/deep_verify.py          # ALL 13 TESTS PASSED
python scripts/check_stale_docs.py     # All critical documentation is current
```

**Then create branch, commit, push:**
```bash
git checkout -b feat/claim-15-v060
git add backend/progress/agent_drift_monitor.py tests/agent/ backend/progress/runner.py reports/scientific_claim_index.md reports/canonical_state.md index.html README.md CLAUDE.md AGENTS.md CONTEXT_SNAPSHOT.md llms.txt system_manifest.json CONTRIBUTING.md paper.md UPDATE_PROTOCOL.md EVOLUTION_LOG.md
git commit -m "feat: add Claim #15 AGENT-DRIFT-01 + bump to v0.6.0

- Implement agent quality drift monitor (4-step chain, 20% threshold)
- Register in runner.py, scientific_claim_index.md, canonical_state.md
- 6 tests: pass/fail/determinism/chain-tamper/semantic/boundary
- Update all counters: 15 claims, {N} tests, v0.6.0"
git push origin feat/claim-15-v060
```

If any verification gate fails, fix the issue before committing. Do NOT commit with failing gates.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python scripts/steward_audit.py && python -m pytest tests/ -q && python scripts/deep_verify.py</automated>
  </verify>
  <done>
    - All 4 verification gates pass (steward_audit, pytest, deep_verify, check_stale_docs)
    - feat/claim-15-v060 branch created and pushed
    - All counters show 15 claims, updated test count, v0.6.0
  </done>
</task>

</tasks>

<verification>
1. `python -c "from backend.progress.agent_drift_monitor import run_agent_drift_monitor; r = run_agent_drift_monitor(baseline={'tests_per_phase':47,'pass_rate':1.0,'regressions':0,'verifier_iterations':1.2}, current={'tests_per_phase':47,'pass_rate':1.0,'regressions':0,'verifier_iterations':1.2}); assert r['mtr_phase']=='AGENT-DRIFT-01' and len(r['execution_trace'])==4"` -- claim works
2. `python -m pytest tests/agent/test_agent_drift01.py -v` -- 6 tests pass
3. `python scripts/steward_audit.py` -- STEWARD AUDIT: PASS
4. `python -m pytest tests/ -q` -- all tests pass (including new 6)
5. `python scripts/deep_verify.py` -- ALL 13 TESTS PASSED
6. `git branch --show-current` -- feat/claim-15-v060
7. `grep "AGENT-DRIFT-01" reports/canonical_state.md` -- registered
8. `grep "15 claims" system_manifest.json` -- counter updated
</verification>

<success_criteria>
- AGENT-DRIFT-01 claim fully implemented with 4-step cryptographic chain
- Composite drift metric correctly computed from 4 weighted sub-metrics
- 6 tests pass covering pass/fail/determinism/chain-tamper/semantic/boundary
- Claim registered in runner.py, scientific_claim_index.md, canonical_state.md
- All counters updated to 15 claims, correct test count, v0.6.0
- All 4 verification gates pass
- Code committed to feat/claim-15-v060 and pushed
</success_criteria>

<output>
After completion, create `.planning/quick/260319-nwt-claim-15-agent-drift-01-v0-6-0-counter-s/260319-nwt-SUMMARY.md`
</output>
