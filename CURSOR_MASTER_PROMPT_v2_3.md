# MetaGenesis Core — Cursor Master Prompt v2.3
**Version:** 2.3 | **Date:** 2026-03-16
**Usage:** Template for EVERY Cursor prompt

---

## BLOCK A — INSERT AT THE START OF EVERY PROMPT (required)

```
CONTEXT: MetaGenesis Core — verification protocol layer for computational claims.
PPA #63/996,819. Repo: https://github.com/Lama999901/metagenesis-core-public

NEVER TOUCH these files under any circumstances:
  - scripts/steward_audit.py         ← SEALED (CI-locked)
  - scripts/mg.py
  - scripts/mg_policy_gate_policy.json
  - tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py
  - ppa/CLAIMS_DRAFT.md
  - .github/workflows/ (add only, never delete)

BANNED TERMS — never write these anywhere:
  "tamper-proof" / "GPT-5" / "19x performance" / "VacuumGenesisEngine"
  "unforgeable" / "100% test success" / "500+ modules" / "Infinity Protocol"
  "blockchain" (use: "cryptographic hash chain" / "Step Chain Verification")
  Instead use: "tamper-evident under trusted verifier assumptions"

CURRENT STATE:
  14 claims / 271 tests / 3 verification layers / MVP v0.2
  steward_audit: PASS / deep_verify: ALL 10 TESTS PASSED
```

---

## BLOCK B — TEMPLATE FOR index.html CHANGES

```
Make exactly N changes to index.html. Nothing else.
DO NOT touch any Python files, CSS, or JavaScript.

CHANGE 1
Find exactly:
  <exact line from file>
Replace with:
  <new line>

Verify after:
  grep "keyword" index.html  → must return N results
```

**IMPORTANT RULES for index.html:**
- Always read file BEFORE editing — fresh read, never from cache
- Exact strings — Cursor does find/replace character-by-character
- External links → `target="_blank"`
- Links to claim files: `https://github.com/Lama999901/metagenesis-core-public/blob/main/`
- Do not touch CSS classes or JS

---

## BLOCK C — TEMPLATE FOR PYTHON/DOCS CHANGES

```
Fix exactly these N issues. Nothing else.

ISSUE 1 — <description>
FILE: <path>
  Find:    <old line>
  Replace: <new line>

DO NOT TOUCH:
  - scripts/steward_audit.py
  - scripts/mg.py
  - scripts/mg_policy_gate_policy.json
  - tests/steward/test_cert02_*
  - ppa/CLAIMS_DRAFT.md

After all changes:
  python scripts/steward_audit.py   # → STEWARD AUDIT: PASS
  python -m pytest tests/ -q        # → 271 passed (or more)
  python scripts/deep_verify.py     # → ALL 10 TESTS PASSED
```

---

## BLOCK D — TEMPLATE FOR NEW CLAIM (6 steps)

```
Add a new verification claim. Follow ALL 6 steps exactly.

CLAIM: <CLAIM_ID>
DOMAIN: <domain>
JOB_KIND: <job_kind_string>
THRESHOLD: <metric> ≤ <value>

STEP 1 — Implementation
CREATE: backend/progress/<claim_id_lower>.py
  - JOB_KIND = "<job_kind_string>"
  - ALGORITHM_VERSION = "v1"
  - def run_<claim>() → dict with mtr_phase key
  - execution_trace + trace_root_hash (Step Chain — 4 steps)
  - Stdlib only, deterministic with seed

STEP 2 — Runner dispatch
FILE: backend/progress/runner.py
  Add dispatch block for job_kind == "<job_kind_string>"

STEP 3 — Claim index
FILE: reports/scientific_claim_index.md
  Add section with: claim_id, domain, job_kind (backticks), V&V thresholds

STEP 4 — Canonical state
FILE: reports/canonical_state.md
  Add <CLAIM_ID> to current_claims_list

STEP 5 — Tests (minimum 3)
CREATE: tests/<domain>/test_<claim_id_lower>.py
  - test_pass, test_fail, test_runner

STEP 6 — Update numbers IN THE SAME COMMIT
  index.html: N → N+1 claims
  system_manifest.json: add to active_claims + update test_count
  README.md, AGENTS.md, llms.txt: update counts

After:
  python scripts/steward_audit.py   → PASS
  python -m pytest tests/ -q        → all passed
  python scripts/deep_verify.py     → ALL 10 TESTS PASSED
```

---

## BLOCK E — CLAIM → FILE MAP

```
MTR-1        → backend/progress/mtr1_calibration.py
MTR-2        → backend/progress/mtr2_thermal_conductivity.py
MTR-3        → backend/progress/mtr3_thermal_multilayer.py
SYSID-01     → backend/progress/sysid1_arx_calibration.py
DATA-PIPE-01 → backend/progress/datapipe1_quality_certificate.py
DRIFT-01     → backend/progress/drift_monitor.py
ML_BENCH-01  → backend/progress/mlbench1_accuracy_certificate.py  ← real data ✅
DT-FEM-01    → backend/progress/dtfem1_displacement_verification.py ← real data ✅
ML_BENCH-02  → backend/progress/mlbench2_regression_certificate.py
ML_BENCH-03  → backend/progress/mlbench3_timeseries_certificate.py
PHARMA-01    → backend/progress/pharma1_admet_certificate.py
FINRISK-01   → backend/progress/finrisk1_var_certificate.py
DT-SENSOR-01 → backend/progress/dtsensor1_iot_certificate.py
DT-CALIB-LOOP-01 → backend/progress/dtcalib1_convergence_certificate.py
```

BASE URL: `https://github.com/Lama999901/metagenesis-core-public/blob/main/`

---

## BLOCK F — SITE CSS VARIABLES

```css
--ink:#04081a  --c:#00e5ff  --ok:#00ff99  --err:#ff4060
--txt:#eef7fb  --fd:'Unbounded'  --fm:'IBM Plex Mono'
```
**Formspree ID:** `xlgpdwop`
**Payment:** email yehor@metagenesis-core.dev (bank transfer / crypto / invoice)

---

## BLOCK G — SITE STRUCTURE

```
<nav>     Protocol | Claims | Verticals | For You | Verify | Free Pilot | GitHub
#hero     — 14 claims, 271 tests, AUDIT: PASS
#protocol — "Not a tool. A standard." — 4 innovations + Step Chain
#claims   — 14 claim cards with links
#verticals — 6 verticals
#crisis   — reproducibility crisis stats
#compare  — comparison table (MetaGenesis vs MLflow vs DVC vs Trust PDF)
#regulatory — "Three Deadlines" (EU AI Act / FDA / Basel)
#pricing  — OSS / Free Pilot / Bundle $299 / Enterprise
#faq      — 5 questions
#segments — 4 tabs (ML/AI, Pharma, Finance, Research)
#verifier — Live Verifier
#pilot    — Free Pilot Form (Formspree: xlgpdwop)
.cband    — CTA
<footer>
```

**Hero badge:** `14 active claims | 271 tests | PASS | patent pending`

---

## BLOCK H — SITE VERIFICATION AFTER CHANGES

```powershell
# Numbers in index.html
Select-String "271" index.html | `
  Where-Object {$_.Line -notmatch "rgba\(0,255,223|&#223;|'0,255,223'"}

# JavaScript check in browser
const sections = ['protocol','claims','verticals','crisis','compare',
  'regulatory','pricing','faq','segments','verifier','pilot']
  .map(id => id+':'+(document.getElementById(id)?'OK':'MISSING')).join(' | ')
const broken = Array.from(document.querySelectorAll('a[href^="#"]'))
  .filter(a => {const id=a.getAttribute('href').substring(1); return id&&!document.getElementById(id);})
  .map(a => a.getAttribute('href')).join(',') || 'none'
sections + '\nBROKEN: ' + broken
```

---

## BLOCK I — GIT WORKFLOW

```powershell
# 1. Always new branch
git checkout -b fix/description

# 2. Make changes

# 3. Check numbers before commit
Select-String "OLD_NUMBER" index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md, system_manifest.json | `
  Where-Object {$_.Line -notmatch "rgba\(0,255,223|&#223;|'0,255,223'"}

# 4. Run tests
python scripts/steward_audit.py    # → PASS
python -m pytest tests/ -q         # → all passed
python scripts/deep_verify.py      # → ALL 10 TESTS PASSED

# 5. Commit and push
git add <files>
git commit -m "type: description"
git push origin fix/description
# → PR → CI PASS → merge → Vercel auto-deploy
```

**TRAP:** main is protected — direct push blocked. Always branch + PR.

---

## BLOCK J — COMMON PROBLEMS

| Problem | Solution |
|---------|---------|
| edit_file can't find string | Read file BEFORE editing — never from cache |
| steward_audit → FAIL | New claim not in canonical_state or runner |
| Numbers don't match | grep all files before commit |
| Push rejected | git stash → pull --no-rebase → stash pop → push |
| Windows cp1252 emoji | io.TextIOWrapper encoding='utf-8' |
| write_file on large file | Only edit_file with exact strings |

---

## BLOCK K — locked_paths (current)

**`scripts/mg_policy_gate_policy.json` has 3 locked_paths:**
```
reports/canonical_state.md
demos/open_data_demo_01/evidence_index.json
scripts/steward_audit.py
```

---

## BLOCK L — REAL DATA MODE (added 2026-03-16)

### What is real data mode

Two claim types support client real data verification:
```
ML_BENCH-01  → mlbench1_accuracy_certificate.py  (parameter: dataset_relpath)
DT-FEM-01    → dtfem1_displacement_verification.py (parameter: dataset_relpath)
```

If `dataset_relpath` is set — synthetic mode is disabled, data is read from client CSV.

### CSV formats

**ML_BENCH-01** — classification:
```
y_true,y_pred
1,1
0,0
```
Minimum 10 rows. Integer values 0/1.

**DT-FEM-01** — FEM vs physical measurements:
```
fem_value,measured_value,quantity
12.10,12.00,displacement_mm
```
Column `quantity` is optional.

### Runner payload for real data

```python
# ML_BENCH-01
payload = {
    "kind": "mlbench1_accuracy_certificate",
    "claimed_accuracy": 0.942,
    "accuracy_tolerance": 0.02,
    "dataset_relpath": "reports/client_data/client_predictions.csv",
}

# DT-FEM-01
payload = {
    "kind": "dtfem1_displacement_verification",
    "rel_err_threshold": 0.02,
    "dataset_relpath": "reports/client_data/client_fem_results.csv",
}
```

### Test fixtures

```
tests/fixtures/ml_bench01_pass.csv    — 100 rows, 90% accuracy → PASS
tests/fixtures/ml_bench01_fail.csv    — 100 rows, ~60% accuracy → FAIL
tests/fixtures/ml_bench01_minimal.csv — 10 rows → PASS
tests/fixtures/dtfem01_pass.csv       — 5 rows, all rel_err < 2% → PASS
tests/fixtures/dtfem01_fail.csv       — 5 rows, 1 row 20% error → FAIL
```

### Real data mode vs synthetic mode

| | Synthetic | Real data |
|---|---|---|
| `execution_trace` | ✅ yes | ❌ no |
| `trace_root_hash` | ✅ yes | ❌ no |
| `inputs.dataset.sha256` | ❌ no | ✅ yes |
| Tamper evidence | Step Chain | Dataset SHA-256 |

### Acceptance commands

```bash
python -m pytest tests/ml/test_mlbench01_realdata.py -v
python -m pytest tests/digital_twin/test_dtfem01_realdata.py -v
python -m pytest tests/cli/test_real_data_e2e.py -v
python scripts/deep_verify.py  # → ALL 10 TESTS PASSED
```

**Full guide:** `docs/REAL_DATA_GUIDE.md`

---

## BLOCK M — KNOWN TRAPS

```
TRAP-01: ZIP folder ≠ git repo
  Only: C:\Users\999ye\Downloads\metagenesis-core-public\

TRAP-03: Numbers in 9+ locations in index.html
  ALWAYS grep BEFORE commit — including prose text, not only HTML tags

TRAP-08: Gmail instead of Zoho
  All outreach only from yehor@metagenesis-core.dev

TRAP-13: Direct push to main → blocked
  Always branch + PR

TRAP-14: Windows cp1252 emoji
  io.TextIOWrapper encoding='utf-8'

TRAP-NEW-06: write_file on large file → overwrites with whitespace
  Only edit_file with exact strings

TRAP-NEW-07: Email without verification → bounce
  Always verify via person's website before creating draft

TRAP-NEW-08: edit_file from cache → string not found
  Read file fresh BEFORE every edit

TRAP-NEW-09: JobStatus enum comparison
  NOT: status.value == "succeeded"
  YES: status == JobStatus.SUCCEEDED
```

---

*CURSOR_MASTER_PROMPT v2.3 — 2026-03-16 — MetaGenesis Core*
*Changes: all text translated to English, test count updated to 271*
