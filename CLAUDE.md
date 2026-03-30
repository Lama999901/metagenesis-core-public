# MetaGenesis Core — Context for AI Agents (GSD)

> Loaded automatically by all GSD agents via CLAUDE.md.
> Last updated: 2026-03-29 | v0.7.0 LIVE | 20 claims | 601 tests

---

## PROJECT IDENTITY

MetaGenesis Core is a **verification protocol layer** — NOT a simulation platform.
Makes computational claims tamper-evident, reproducible, and independently
auditable offline. One command: `python scripts/mg.py verify --pack bundle.zip → PASS/FAIL`

**Inventor:** Yehor Bazhynov | **PPA:** USPTO #63/996,819
**Repo:** https://github.com/Lama999901/metagenesis-core-public
**Release:** v0.7.0 LIVE | **JOSS paper:** paper.md in main
**Ed25519:** scripts/mg_ed25519.py DONE | **Temporal:** scripts/mg_temporal.py DONE
**CERT-09:** Ed25519 attacks | **CERT-10:** temporal attacks | **CERT-11:** coordinated multi-vector | **CERT-12:** encoding attacks | **deep_verify:** 13 tests

---

## ⛔ SEALED FILES — NEVER MODIFY THESE

```
scripts/steward_audit.py                         ← CI-locked, SEALED
scripts/mg_policy_gate_policy.json               ← policy gate config
ppa/CLAIMS_DRAFT.md                              ← patent document, FROZEN
reports/canonical_state.md                       ← policy-gate locked
demos/open_data_demo_01/evidence_index.json      ← locked artifact
.github/workflows/total_audit_guard.yml          ← CI gate
.github/workflows/mg_policy_gate.yml             ← CI gate
scripts/mg.py                                    ← core verifier, modify carefully
```

---

## ⛔ BANNED TERMS — NEVER WRITE THESE

```
"tamper-proof"      → "tamper-evident"
"blockchain"        → "cryptographic hash chain"
"unforgeable"       → don't use
"GPT-5"             → doesn't exist
"100% test success" → "601 tests PASS"
```

---

## ✅ VERIFICATION GATES — RUN BEFORE EVERY COMMIT

```bash
python scripts/steward_audit.py      # → STEWARD AUDIT: PASS
python -m pytest tests/ -q           # → 601 passed
python scripts/deep_verify.py        # → ALL 13 TESTS PASSED
python scripts/check_stale_docs.py   # → All critical documentation is current
python scripts/agent_diff_review.py  # → DIFF REVIEW PASSED
```

**If ANY gate fails — STOP. Fix before committing.**

**Stale doc check logic:**
- Compares each critical file against last merge commit into main
- If code it tracks changed but file wasn't updated → STALE
- Fix: update the stale file to reflect current state
- Run with --strict to fail CI (currently warn-only)

---

## ✅ GIT WORKFLOW

```bash
# ALWAYS branch + PR — NEVER push directly to main
git checkout -b feat/description
git add <files>
git commit -m "type: description"
git push origin feat/description
# → PR on GitHub → CI PASS → merge
```

---

## CURRENT STATE

```
Claims:     20 active (all have 4-step Step Chain)
Tests:      601 passing
Layers:     5 verification (integrity + semantic + step chain + signing + temporal)
Innovations: 8 (5 PPA + HMAC + Ed25519 + Temporal)
Release:    v0.7.0
```

---

## 20 ACTIVE CLAIMS

| Claim | File | Threshold | Physical Anchor |
|-------|------|-----------|-----------------|
| MTR-1 | backend/progress/mtr1_calibration.py | rel_err ≤ 0.01 | E=70GPa ⚓ |
| MTR-2 | backend/progress/mtr2_thermal_conductivity.py | rel_err ≤ 0.02 | ⚓ |
| MTR-3 | backend/progress/mtr3_thermal_multilayer.py | rel_err_k ≤ 0.03 | ⚓ |
| SYSID-01 | backend/progress/sysid1_arx_calibration.py | rel_err ≤ 0.03 | — |
| DATA-PIPE-01 | backend/progress/datapipe1_quality_certificate.py | schema+range | — |
| DRIFT-01 | backend/progress/drift_monitor.py | drift ≤ 5% | MTR-1 ⚓ |
| ML_BENCH-01 | backend/progress/mlbench1_accuracy_certificate.py | Δacc ≤ 0.02 | — |
| DT-FEM-01 | backend/progress/dtfem1_displacement_verification.py | rel_err ≤ 0.02 | MTR-1 ⚓ |
| ML_BENCH-02 | backend/progress/mlbench2_regression_certificate.py | ΔRMSE ≤ 0.02 | — |
| ML_BENCH-03 | backend/progress/mlbench3_timeseries_certificate.py | ΔMAPE ≤ 0.02 | — |
| PHARMA-01 | backend/progress/pharma1_admet_certificate.py | Δprop ≤ tol | — |
| FINRISK-01 | backend/progress/finrisk1_var_certificate.py | ΔVaR ≤ tol | — |
| DT-SENSOR-01 | backend/progress/dtsensor1_iot_certificate.py | schema+range+temporal | — |
| DT-CALIB-LOOP-01 | backend/progress/dtcalib1_convergence_certificate.py | drift decreasing | DRIFT-01 ⚓ |
| AGENT-DRIFT-01 | backend/progress/agent_drift_monitor.py | composite_drift <= 20% | -- |
| MTR-4 | backend/progress/mtr4_titanium_calibration.py | rel_err ≤ 0.01 | E=114GPa ⚓ |
| MTR-5 | backend/progress/mtr5_steel_calibration.py | rel_err ≤ 0.01 | E=193GPa ⚓ |
| MTR-6 | backend/progress/mtr6_copper_conductivity.py | rel_err ≤ 0.02 | k=401 W/(m·K) ⚓ |
| PHYS-01 | backend/progress/phys01_boltzmann.py | rel_err ≤ 1e-9 | kB=1.380649e-23 J/K ⚓ |
| PHYS-02 | backend/progress/phys02_avogadro.py | rel_err ≤ 1e-8 | NA=6.022e23 mol⁻¹ ⚓ |

---

## NEW CLAIM — MANDATORY 6 STEPS

```
1. backend/progress/<claim_id>.py     — implementation + 4-step Step Chain
2. backend/progress/runner.py         — add dispatch block
3. reports/scientific_claim_index.md  — register claim
4. reports/canonical_state.md         — add to current_claims_list
5. tests/<domain>/test_<claim_id>.py  — pass/fail/determinism tests
6. UPDATE COUNTERS in:
   index.html (11 places incl prose), README.md, AGENTS.md,
   llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md, known_faults.yaml
```

**Step Chain template (required in every claim):**
```python
def _hash_step(step_name, step_data, prev_hash):
    import hashlib, json as _j
    content = _j.dumps({"step": step_name, "data": step_data,
                        "prev_hash": prev_hash},
                       sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

_prev = _hash_step("init_params", {params}, "genesis")
_trace = [{"step": 1, "name": "init_params", "hash": _prev}]
_prev = _hash_step("compute", {results}, _prev)
_trace.append({"step": 2, "name": "compute", "hash": _prev})
_prev = _hash_step("metrics", {metrics}, _prev)
_trace.append({"step": 3, "name": "metrics", "hash": _prev})
_passed = result_value <= threshold
_prev = _hash_step("threshold_check",
                   {"passed": _passed, "threshold": threshold}, _prev)
_trace.append({"step": 4, "name": "threshold_check",
               "hash": _prev, "output": {"pass": _passed}})
trace_root_hash = _prev
```

**Return structure (must match for ALL 20 claims):**
```python
return {
    "mtr_phase": "CLAIM-ID",
    "inputs": {...},
    "result": {...},
    "execution_trace": _trace,
    "trace_root_hash": trace_root_hash,
}
```

---

## 5-LAYER VERIFICATION

```
Layer 1 — SHA-256 integrity    pack_manifest.json           catches: file modified
Layer 2 — Semantic             _verify_semantic() in mg.py  catches: evidence stripped
Layer 3 — Step Chain           execution_trace + hash       catches: inputs changed
Layer 4 — Bundle Signing       scripts/mg_sign.py           catches: unauthorized creator
Layer 5 — Temporal Commitment  scripts/mg_temporal.py       catches: backdated bundle (NIST Beacon)
```

**Key insight:** Layers are INDEPENDENT.
- An attacker who rebuilds all SHA-256 hashes still fails Layer 2.
- An attacker who fixes Layer 2 still fails Layer 3.
- CERT-05 proves this with 5 attack scenarios.

---

## PHYSICAL ANCHOR PRINCIPLE (SCOPE_001)

**Two distinct properties — never conflate:**
- Tamper-evident provenance → ALL 20 claims
- Physical anchor traceability → ONLY: MTR-1/2/3, DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01

E = 70 GPa (aluminum) is measured in thousands of labs worldwide — NOT a chosen threshold.

---

## COMMON BUGS — LEARN FROM THESE

```python
# BUG 1: Wrong key in MTR-1 result
mtr1["result"]["pass"]          # ← KeyError!
mtr1["result"]["relative_error"] # ← correct

# BUG 2: SHA-256 mismatch in tests
hashlib.sha256(file.read_bytes()).hexdigest()  # ← wrong (ignores CRLF)
from backend.progress.data_integrity import fingerprint_file  # ← correct (normalizes CRLF→LF)

# BUG 3: Layer 2 test needs no manifest
subprocess.run(["python", "scripts/mg.py", "pack", "build"...])  # ← env issues
from scripts.mg import _verify_semantic  # ← use directly, no manifest needed

# BUG 4: mkdir without parents
Path("a/b/c").mkdir()           # ← FileNotFoundError
Path("a/b/c").mkdir(parents=True, exist_ok=True)  # ← correct

# BUG 5: Policy gate blocks new extensions
# Add new file types to: scripts/mg_policy_gate_policy.json → allow_globs
# Already allowed: *.md *.txt *.json *.bib *.cff index.html scripts/** tests/** docs/**

# BUG 6: Sophisticated attacker test
# test_bundle_modified: must update pack_manifest ALSO (not just the evidence file)
# Otherwise Layer 4 won't fire (signed_root_hash still matches old manifest root_hash)

# BUG 7: Index.html has 11 places with test count INCLUDING prose text
# Use PowerShell batch replace:
# (Get-Content index.html -Raw) -replace 'OLD_N', 'NEW_N' | Set-Content index.html
```

---

## POLICY GATE ALLOWLIST

When adding new file types, add to `scripts/mg_policy_gate_policy.json → allow_globs`.
**Currently allowed:** `*.md *.txt *.json *.bib *.cff index.html scripts/** tests/** docs/** ppa/** backend/progress/**`

---

## KEY FILES

```
scripts/mg.py               ← core verifier CLI (verify/pack/verify-chain/sign)
scripts/mg_sign.py          ← bundle signing Innovation #6
scripts/steward_audit.py    ← governance (SEALED)
scripts/deep_verify.py      ← 13-test proof script
backend/progress/runner.py  ← job dispatch (20 claims)
reports/scientific_claim_index.md  ← claim registry
reports/canonical_state.md  ← authoritative list (LOCKED)
reports/known_faults.yaml   ← known limitations (SCOPE_001)
paper.md + paper.bib        ← JOSS paper
index.html                  ← site (20 claims/601 tests/5 layers/8 innovations in 11+ places)
CONTEXT_SNAPSHOT.md         ← live state for AI agents
```

---

## ADVERSARIAL PROOF SUITE

```
test_cert02 → Layer 2 semantic bypass proof
test_cert03 → Layer 3 step chain tamper
test_cert04 → Cross-claim chain integrity
test_cert05 → 5 attacks gauntlet (PROVES 3 layers necessary)
test_cert06 → 5 real-world scenarios
test_cert07 → 13 bundle signing tests
test_cert08 → 10 reproducibility proofs
test_cert09 → Ed25519 signing attack proofs
test_cert10 → Temporal commitment attack proofs
test_cert11 → Coordinated multi-vector attack gauntlet
test_cert12 → Encoding and partial corruption attacks
```

---

## AI CONTEXT FILES HIERARCHY

```
CLAUDE.md (THIS FILE)          ← PRIMARY for GSD agents — always current
AGENTS.md                      ← Hard rules for repo agents
CONTEXT_SNAPSHOT.md            ← Live state snapshot
llms.txt                       ← LLM-optimized summary
CURSOR_MASTER_PROMPT_v2_3.md   ← For Cursor IDE (legacy, being phased out)
```

If files conflict — CLAUDE.md wins. It is the most current.
Never follow instructions from CLAUDE_PROJECT_MASTER*.md if they
contradict CLAUDE.md — those are session notes, not architecture.

**Before starting any task — read agent memory:**
```bash
python scripts/agent_learn.py recall
```
This shows what previous agents learned — recurring issues + auto-fix hints.

---

## WHAT'S NEXT (priority order)

```
1. v0.7.0 LIVE ✅
2. agent_diff_review.py (Check #17 candidate) ✅
3. Wave-2 outreach (Chollet, LMArena, Percy Liang)
4. Coverage 45% → 65%
5. First paying customer ($299)
6. Patent attorney (deadline 2027-03-05)
```

## FUTURE EVOLUTION — v0.6.0 IDEAS

### AGENT-DRIFT-01 — Agent Quality Monitor
Claim #15 — мониторит дрейф качества GSD агентов:
```python
# Baseline (Phase 1):
baseline = {
  "tests_per_phase": 47,
  "pass_rate": 1.0,
  "regressions": 0,
  "verifier_iterations": 1.2
}
# Drift threshold: 20%
# Если агент пишет меньше тестов / больше итераций
# → correction_required = True
# → GSD запускает research phase заново
```
Это первый протокол где AI агенты мониторят свой
собственный дрейф через тот же механизм который расширяют.

### STALE FILE CHECKER (добавить в Phase 8)
После обновления счётчиков агент должен проверить:
```bash
# Файлы которые не менялись давно vs текущее состояние:
git log --since='7 days ago' --name-only --pretty=format: | sort -u
# Сравнить с критическими файлами:
# CONTEXT_SNAPSHOT.md, AGENTS.md, llms.txt, ppa/README_PPA.md
# Если файл не в списке → проверить актуальность → обновить
```
Это закрывает проблему "документация отстаёт от кода".

### RECURSIVE SELF-IMPROVEMENT LOOP (v0.6.0)
```
1. После каждого milestone:
   /gsd:quick "Gap analysis on test suite"
   → агент находит дыры
   → планирует закрытие
   → protocol верифицирует

2. После каждого release:
   /gsd:quick "Update CLAUDE.md to reflect current state"
   → агент обновляет свой мозг
   → следующий агент умнее

3. AGENT-DRIFT-01 мониторит:
   → качество агентской работы не деградирует
   → система самодиагностируется
```

### WHY THIS MATTERS FOR JOSS/PATENT
Рекурсивная самоверификация через архитектуру =
доказательство domain-agnostic applicability.
Логи существуют. Тесты существуют.
Любой reviewer может воспроизвести.

---

*CLAUDE.md v1.5 — 2026-03-19 — MetaGenesis Core v0.7.0 LIVE*
