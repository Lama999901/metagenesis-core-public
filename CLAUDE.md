# MetaGenesis Core — Context for AI Agents (GSD)

> Loaded automatically by all GSD agents via CLAUDE.md.
> Last updated: 2026-03-31 | v0.8.0 LIVE | 20 claims | 966 tests

---

## MISSION — WHY THIS EXISTS

**One sentence:** MetaGenesis Core is a notary for computations.

Like a notary certifies a document — we certify that a computer produced
exactly this result, at exactly this time, in exactly this way.
Without access to the computer. Without trusting anyone. In 60 seconds.

```bash
python scripts/mg.py verify --pack bundle.zip  →  PASS / FAIL
```

**The problem:** Every day billions of computations produce numbers that
everyone must simply *trust*. ML model says 94% accuracy — trust it.
FEM simulation says the part holds 10 tons — trust it.
Drug calculation passed — trust it. Risk model says all clear — trust it.
There is no standard of proof. MetaGenesis Core is that standard.

**Six domains. Six real pains. One protocol.**

| Domain | Pain | What we give |
|--------|------|--------------|
| ML / AI | Benchmark gaming. "94% accuracy" unverifiable | Cryptographic proof + timestamp. Impossible to backdate. |
| Pharma / Biotech | FDA 2025 requires verifiable AI artifacts for IND filing | Bundle = audit artifact. $299 vs $47M raise. |
| Finance | Basel III: independent VaR validation required | Regulator verifies offline. No model access needed. |
| Digital Twin | Calibration chain from physics to simulation — who proves accuracy? | Cryptographic chain from physical constant to result. |
| Science | 70% of results cannot be reproduced | Reproducibility as math, not words. Hash equality = proof. |
| Climate / ESG | Carbon credits backed by unverifiable models | Proof the model produced exactly this result on this data. |

**The physical anchor — what makes us unique:**
We anchor computation to physical reality itself.
```
kB = 1.380649e-23 J/K  (SI 2019, exact, zero uncertainty) → PHYS-01
NA = 6.02214076e23 mol-1 (SI 2019, exact, zero uncertainty) → PHYS-02
E  = 70 GPa aluminum   (NIST measured, ~1% uncertainty)   → MTR-1
    ↓ anchor_hash baked in
DT-FEM-01: FEM output vs physical reference → rel_err ≤ 2% → PASS
    ↓ anchor_hash baked in
DRIFT-01: deviation from anchor ≤ 5% → PASS
```
Change any link in the chain — the cryptographic hash breaks everywhere downstream.

**Diff correction — the hidden revolution:**
Not just "was this modified" but "what exactly changed, in which computation
step, and how did that change the result." Cryptographic diff between two
computation states. Useful for: model versioning, digital twin recalibration,
regulatory submission updates, climate model iterations.

---

## COMMERCIAL PRIORITY — WHAT MATTERS MOST

```
#1 PRIORITY: First paying customer at $299
             Every technical improvement must serve this goal.

Payment:     yehor@metagenesis-core.dev | Stripe link in COMMERCIAL.md
Free pilot:  metagenesis-core.dev/#pilot (Formspree xlgpdwop)
Pipeline:    Free pilot → bundle → Stripe → $299 → case study → next client

Wave-2 outreach PENDING: Chollet, LMArena, Percy Liang
Angle: kB/NA = SI 2019 exact constants = strongest verification anchor possible
```

**When agents make decisions, always ask:**
Does this action help a client trust MetaGenesis enough to pay $299?
If yes → do it. If no → deprioritize.
More tests are good. More complexity without client value is not.

---

## PROJECT IDENTITY

MetaGenesis Core is a **verification protocol layer** — NOT a simulation platform.
Makes computational claims tamper-evident, reproducible, and independently
auditable offline. One command: `python scripts/mg.py verify --pack bundle.zip → PASS/FAIL`

**Inventor:** Yehor Bazhynov | **PPA:** USPTO #63/996,819
**Repo:** https://github.com/Lama999901/metagenesis-core-public
**Site:** https://metagenesis-core.dev
**Release:** v0.8.0 LIVE | **JOSS paper:** paper.md in main (resubmit Sep 2026)
**Ed25519:** scripts/mg_ed25519.py DONE | **Temporal:** scripts/mg_temporal.py DONE
**CERT-09:** Ed25519 attacks | **CERT-10:** temporal attacks
**CERT-11:** coordinated multi-vector | **CERT-12:** encoding attacks
**deep_verify:** 13 tests

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
"100% test success" → "966 tests PASS"
any stale test count → always use current count from system_manifest.json
any stale version    → always use v0.8.0
```

---

## ✅ VERIFICATION GATES — RUN BEFORE EVERY COMMIT

```bash
python scripts/steward_audit.py      # → STEWARD AUDIT: PASS
python -m pytest tests/ -q           # → 966 passed
python scripts/deep_verify.py        # → ALL 13 TESTS PASSED
python scripts/check_stale_docs.py   # → All critical documentation is current
python scripts/agent_diff_review.py  # → DIFF REVIEW PASSED
python scripts/agent_pr_creator.py --summary  # → No auto-pr needed
```

**If ANY gate fails — STOP. Fix before committing.**

**CRITICAL TRAP — STALE RULES:** When test count changes, update
check_stale_docs.py required strings IN THE SAME PR. Otherwise rules
report false PASSes for up to 13 files. (UPDATE_PROTOCOL v1.1 rule)

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

## CURRENT STATE (v0.8.0)

```
Claims:      20 active (all have 4-step Step Chain)
Tests:       966 passing (2 skipped)
Layers:      5 verification (integrity + semantic + step chain + signing + temporal)
Innovations: 8 (5 PPA + HMAC + Ed25519 + Temporal)
Domains:     8 (materials, sysid, data, ml, digital_twin, pharma, finance, physics)
Checks:      19 Mechanicus (agent_evolution.py)
Release:     v0.8.0 LIVE
Coverage:    ~40% (target 65%)
agent_pr_creator: REAL (203 lines, 3 detectors) — catches stale counters automatically
```

---

## 20 ACTIVE CLAIMS

| Claim | File | Threshold | Physical Anchor |
|-------|------|-----------|-----------------|
| MTR-1 | backend/progress/mtr1_calibration.py | rel_err ≤ 0.01 | E=70GPa Al ⚓ |
| MTR-2 | backend/progress/mtr2_thermal_conductivity.py | rel_err ≤ 0.02 | ⚓ |
| MTR-3 | backend/progress/mtr3_thermal_multilayer.py | rel_err_k ≤ 0.03 | ⚓ |
| MTR-4 | backend/progress/mtr4_titanium_calibration.py | rel_err ≤ 0.01 | E=114GPa Ti ⚓ |
| MTR-5 | backend/progress/mtr5_steel_calibration.py | rel_err ≤ 0.01 | E=193GPa SS ⚓ |
| MTR-6 | backend/progress/mtr6_copper_conductivity.py | rel_err ≤ 0.02 | k=401 W/(m·K) ⚓ |
| PHYS-01 | backend/progress/phys01_boltzmann.py | rel_err ≤ 1e-9 | kB=1.380649e-23 J/K ⚓ SI2019 |
| PHYS-02 | backend/progress/phys02_avogadro.py | rel_err ≤ 1e-8 | NA=6.022e23 mol-1 ⚓ SI2019 |
| SYSID-01 | backend/progress/sysid1_arx_calibration.py | rel_err ≤ 0.03 | — |
| DATA-PIPE-01 | backend/progress/datapipe1_quality_certificate.py | schema+range | — |
| DRIFT-01 | backend/progress/drift_monitor.py | drift ≤ 5% | MTR-1 ⚓ |
| ML_BENCH-01 | backend/progress/mlbench1_accuracy_certificate.py | Δacc ≤ 0.02 | — |
| ML_BENCH-02 | backend/progress/mlbench2_regression_certificate.py | ΔRMSE ≤ 0.02 | — |
| ML_BENCH-03 | backend/progress/mlbench3_timeseries_certificate.py | ΔMAPE ≤ 0.02 | — |
| DT-FEM-01 | backend/progress/dtfem1_displacement_verification.py | rel_err ≤ 0.02 | MTR-1 ⚓ |
| DT-SENSOR-01 | backend/progress/dtsensor1_iot_certificate.py | schema+range+temporal | — |
| DT-CALIB-LOOP-01 | backend/progress/dtcalib1_convergence_certificate.py | drift decreasing | DRIFT-01 ⚓ |
| PHARMA-01 | backend/progress/pharma1_admet_certificate.py | Δprop ≤ tol | — |
| FINRISK-01 | backend/progress/finrisk1_var_certificate.py | ΔVaR ≤ tol | — |
| AGENT-DRIFT-01 | backend/progress/agent_drift_monitor.py | composite_drift ≤ 20% | — |

**Physical anchor hierarchy:**
- SI 2019 exact (zero uncertainty): PHYS-01 (kB), PHYS-02 (NA)
- NIST measured (~1% uncertainty): MTR-1/2/3/4/5/6
- Derived anchors: DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01 (inherit from MTR-1)
- Tamper-evident only (no physical constant): all others

---

## NEW CLAIM — MANDATORY 6 STEPS

```
1. backend/progress/<claim_id>.py     — implementation + 4-step Step Chain
2. backend/progress/runner.py         — add dispatch block
3. reports/scientific_claim_index.md  — register claim
4. reports/canonical_state.md         — add to current_claims_list
5. tests/<domain>/test_<claim_id>.py  — pass/fail/determinism tests
6. UPDATE COUNTERS in:
   index.html (11 places), README.md, AGENTS.md,
   llms.txt, system_manifest.json, CONTEXT_SNAPSHOT.md
   AND check_stale_docs.py required strings (UPDATE_PROTOCOL v1.1 rule)
```

**ALWAYS use GSD for new claims. Manual adds = invisible tails in check_stale_docs rules.**

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
Layer 2 — Semantic             _verify_semantic() in mg.py  catches: evidence stripped + hashes recomputed
Layer 3 — Step Chain           execution_trace + hash       catches: inputs changed, steps reordered
Layer 4 — Bundle Signing       scripts/mg_sign.py           catches: unauthorized bundle creator
Layer 5 — Temporal Commitment  scripts/mg_temporal.py       catches: backdated bundle (NIST Beacon)
```

**Key insight:** Layers are INDEPENDENT. CERT-11 proves each layer catches
attacks the other four miss. No subset of four is sufficient.

---

## PHYSICAL ANCHOR PRINCIPLE (SCOPE_001)

Two distinct properties — never conflate:
- **Tamper-evident provenance** ("was bundle modified?") → ALL 20 claims
- **Physical anchor traceability** ("does number agree with physical reality?") → ONLY anchored claims

Scope is documented in reports/known_faults.yaml :: SCOPE_001.
Do NOT claim physical anchor for ML, finance, pharma, sysid, sensor, agent claims.

---

## COMMON BUGS — LEARN FROM THESE

```python
# BUG 1: Wrong key in MTR-1 result
mtr1["result"]["pass"]           # ← KeyError!
mtr1["result"]["relative_error"] # ← correct

# BUG 2: SHA-256 mismatch in tests
hashlib.sha256(file.read_bytes()).hexdigest()  # ← wrong (ignores CRLF)
from backend.progress.data_integrity import fingerprint_file  # ← correct

# BUG 3: Windows redirect
2>/dev/null              # ← breaks on Windows
subprocess.DEVNULL       # ← correct

# BUG 4: Windows encoding
print(emoji)             # ← cp1252 crash
io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # ← correct

# BUG 5: mkdir without parents
Path("a/b/c").mkdir()                        # ← FileNotFoundError
Path("a/b/c").mkdir(parents=True, exist_ok=True)  # ← correct

# BUG 6: Index.html has 11 places with test count INCLUDING prose
# Use PowerShell batch replace:
# (Get-Content index.html -Raw) -replace 'OLD_N', 'NEW_N' | Set-Content index.html

# BUG 7: GSD "Deviation noted" = stub was created, not real file
# ALWAYS: copy_file_user_to_claude → bash verify after ANY GSD task
# Never trust GSD output alone. Read the actual file.

# BUG 8: Stale rules trap
# When test count changes, ALSO update check_stale_docs.py required strings
# in the SAME PR. Otherwise 13 files report false PASS.
```

---

## AGENT TRAPS — NEVER FALL INTO THESE

```
TRAP-GSD-DEVIATION:  GSD "Deviation noted" → read actual file IMMEDIATELY
TRAP-NO-GSD:         claims/agents/counters without GSD → invisible tails
TRAP-STALE-RULES:    test count change → update check_stale_docs.py in same PR
TRAP-BRANCH:         main is protected → always branch + PR
TRAP-WIN:            2>/dev/null → subprocess.DEVNULL
TRAP-ENCODING:       Unicode on Windows → io.TextIOWrapper(encoding='utf-8')
TRAP-SEC:            signing_key.json + EVOLUTION_LOG.md → NOT in repo
TRAP-01:             ZIP folder ≠ git repo → use metagenesis-core-public/
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
scripts/mg_ed25519.py       ← Ed25519 asymmetric signing Innovation #7
scripts/mg_temporal.py      ← NIST Beacon temporal commitment Innovation #8 (Layer 5)
scripts/steward_audit.py    ← governance (SEALED)
scripts/deep_verify.py      ← 13-test proof script
scripts/agent_evolution.py  ← 19 Mechanicus checks
scripts/agent_pr_creator.py ← Level 3 autonomous PR (203 lines, 3 detectors)
scripts/agent_learn.py      ← session memory (57 sessions, 15 patterns)
scripts/check_stale_docs.py ← documentation currency checker
backend/progress/runner.py  ← job dispatch (20 claims)
reports/scientific_claim_index.md  ← claim registry
reports/canonical_state.md  ← authoritative list (LOCKED)
reports/known_faults.yaml   ← known limitations (SCOPE_001 + ENV_001)
paper.md + paper.bib        ← JOSS paper (resubmit Sep 2026)
index.html                  ← site (966 tests/20 claims/5 layers/8 innovations)
CONTEXT_SNAPSHOT.md         ← live state for AI agents
```

---

## ADVERSARIAL PROOF SUITE

```
test_cert02 → Layer 2 semantic bypass proof (FLAGSHIP)
test_cert03 → Layer 3 step chain tamper
test_cert04 → Cross-claim chain integrity
test_cert05 → 5 attacks gauntlet (proves all layers necessary)
test_cert06 → 5 real-world scenarios
test_cert07 → 13 bundle signing tests
test_cert08 → 10 reproducibility proofs
test_cert09 → Ed25519 signing attack proofs
test_cert10 → Temporal commitment attack proofs
test_cert11 → Coordinated multi-vector (proves 5-layer independence)
test_cert12 → Encoding and partial corruption attacks
```

---

## AI CONTEXT FILES HIERARCHY

```
CLAUDE.md (THIS FILE)     ← PRIMARY for GSD agents — always current, wins all conflicts
AGENTS.md                 ← Hard rules for repo agents
CONTEXT_SNAPSHOT.md       ← Live state snapshot
llms.txt                  ← LLM-optimized repo summary
docs/AGENT_SYSTEM.md      ← Agent architecture (3 levels)
```

**Before starting any task — read agent memory:**
```bash
python scripts/agent_learn.py recall
```
This shows recurring issues + auto-fix hints from 57 sessions.

---

## WHAT'S NEXT (priority order)

```
1. First paying customer $299 ← TOP PRIORITY
   Free pilot → bundle → Stripe link → $299
   Contact: yehor@metagenesis-core.dev

2. Wave-2 outreach (TASK-026 — CI agents drafting)
   Chollet / LMArena / Percy Liang
   Angle: PHYS-01/02 SI 2019 exact constants = strongest verification anchor

3. Stale docs (TASK-022..025 — CI agents working on these)
   CONTEXT_SNAPSHOT.md, llms.txt, AGENTS.md, UPDATE_PROTOCOL v1.1

4. Zenodo DOI — 5 minutes at zenodo.org (for JOSS resubmit)

5. Coverage 40% → 65% (agent_research.py generates tasks automatically)

6. Patent attorney engagement (deadline 2027-03-05, non-provisional)

7. JOSS resubmission — Sep 2026 (6 months public history required)
```

---

*CLAUDE.md v2.0 — 2026-03-31 — MetaGenesis Core v0.8.0 LIVE*
*966 tests | 20 claims | 19 checks | Level 3 autonomous forge ACTIVE*
*Mission: notary for computations. First client = history.*
