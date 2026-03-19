# MetaGenesis Core — Update Protocol
> Version 1.1 — 2026-03-18
> Mandatory checklist for every significant change.
> Goal: repo, site, docs, and Project Knowledge always in sync.

---

## PRINCIPLE

Every significant change touches multiple layers simultaneously.
Not updating all layers = a tail that accumulates and breaks trust.

**Significant change** = any of:
- New claim added
- Tests added/changed (counter changes)
- New verification layer
- New patentable innovation
- Payment method / pricing change
- New domain or vertical
- Significant outreach (≥5 emails)
- New public release
- Protocol architecture change

---

## CHECKLISTS BY CHANGE TYPE

---

### 📦 NEW CLAIM

```
[ ] backend/progress/<claim_id>.py — implementation
[ ] runner.py — dispatch added
[ ] reports/scientific_claim_index.md — section added
[ ] reports/canonical_state.md — claim_id in current_claims_list

[ ] UPDATE NUMBERS EVERYWHERE:
    [ ] system_manifest.json → active_claims + test_count
    [ ] index.html → N claims (hero badge + claims grid + pricing)
    [ ] README.md → badges + claims table + verification state
    [ ] AGENTS.md → acceptance commands test count
    [ ] llms.txt → active claims list + current state counts
    [ ] CONTEXT_SNAPSHOT.md → verified state table
    [ ] ppa/README_PPA.md → post-filing additions table
    [ ] CURSOR_MASTER_PROMPT_v2_X.md → BLOCK E file map

[ ] TESTS:
    [ ] tests/<domain>/test_<claim_id>.py — min: pass, fail, runner
    [ ] python scripts/steward_audit.py → PASS
    [ ] python -m pytest tests/ -q → all passed
    [ ] python scripts/deep_verify.py → ALL 13 PASSED

[ ] PROJECT KNOWLEDGE UPDATE:
    [ ] EVOLUTION_LOG.md → CURRENT STATE + SESSION LOG
    [ ] CLAUDE_PROJECT_MASTER → claims table + numbers
    [ ] NEXT_CHAT_PRIMER → pending tasks
```

**Grep before commit:**
```powershell
Select-String "OLD_N claims" index.html, README.md, llms.txt, CONTEXT_SNAPSHOT.md
```

---

### 🧪 NEW TESTS (no new claim)

```
[ ] system_manifest.json → test_count update
[ ] reports/known_faults.yaml → # Last updated date
[ ] README.md → badge + verification state count
[ ] AGENTS.md → Step 6 Verify count
[ ] llms.txt → How to verify + current state
[ ] index.html → all locations (see below)
[ ] CURSOR_MASTER_PROMPT_v2_X.md → acceptance commands

[ ] INDEX.HTML — 9 LOCATIONS WITH TEST COUNT:
    footer nav:        MIT · N tests · AUDIT PASS
    hero hv:           <span class="hv">N</span> tests
    hero badge:        <span class="hbproof-val cy">N</span>
    ticker ×2:         <span class="tn">N</span>
    stats counter:     <span id="cn2">N</span>
    psi-label:         N tests — CI passing
    osi-num:           <div class="osi-num">N</div>
    terminal:          N passed
    pricing:           N tests including adversarial proof
    JS counter:        ct(document.getElementById('cn2'),N,1500)
    origin prose:      N passing tests  ← EASY TO MISS

[ ] python scripts/deep_verify.py → ALL 13 PASSED

[ ] PROJECT KNOWLEDGE:
    [ ] EVOLUTION_LOG.md → CURRENT STATE tests count
    [ ] CLAUDE_PROJECT_MASTER → numbers table
    [ ] AUDIT_PROTOCOL → CURRENT STATE
```

**LESSON:** grep for OLD_NUMBER including prose text, not only HTML tags.

**Grep before commit:**
```powershell
Select-String "OLD_NUMBER" index.html, README.md, AGENTS.md, llms.txt, system_manifest.json | `
  Where-Object {$_.Line -notmatch "rgba\(0,255,223|&#223;|'0,255,223'"}
# Must return empty
```

---

### 🌐 REAL DATA MODE (for new claim)

```
[ ] backend/progress/<claim>.py → dataset_relpath parameter
[ ] backend/progress/data_integrity.py → fingerprint_file used
[ ] tests/fixtures/<claim>_pass.csv — correct data
[ ] tests/fixtures/<claim>_fail.csv — data with error
[ ] tests/<domain>/test_<claim>_realdata.py — tests:
    - pass dataset → result.pass True
    - fail dataset → result.pass False
    - dataset fingerprint in inputs.dataset.sha256
    - different CSVs → different sha256
    - missing file → ValueError
    - no execution_trace in real data mode
[ ] tests/cli/test_real_data_e2e.py → add e2e test for new claim
[ ] docs/REAL_DATA_GUIDE.md → add CSV format for new claim

[ ] CURSOR_MASTER_PROMPT_v2_X.md → BLOCK L update (csv formats)

[ ] PROJECT KNOWLEDGE:
    [ ] CLAUDE_PROJECT_MASTER → Real Data Mode table (✅ column)
    [ ] EVOLUTION_LOG → VERIFIED ARCHITECTURE
```

---

### 💰 PAYMENT METHOD CHANGE

```
[ ] index.html → pricing section + hero buttons
[ ] COMMERCIAL.md → pricing table + payment methods
[ ] llms.txt → current state payment line
[ ] CONTEXT_SNAPSHOT.md → payment line
[ ] docs/REAL_DATA_GUIDE.md → pricing table

[ ] PROJECT KNOWLEDGE:
    [ ] CLAUDE_PROJECT_MASTER → pricing section
    [ ] DECISION_LOG → DEC-XXX explaining why
```

---

### 📣 SIGNIFICANT OUTREACH (≥5 emails)

```
[ ] CONTEXT_SNAPSHOT.md → outreach tracker table
[ ] llms.txt → outreach sent line in current state

[ ] PROJECT KNOWLEDGE:
    [ ] EVOLUTION_LOG → full outreach tracker
    [ ] CLAUDE_PROJECT_MASTER → outreach tracker section
    [ ] NEXT_CHAT_PRIMER → if awaiting replies → in 🔴 section
```

---

### 🚀 NEW PUBLIC RELEASE (vX.Y.Z)

```
[ ] GitHub Release created with tag
[ ] README.md → Protocol badge updated
[ ] llms.txt → github_release line
[ ] CONTEXT_SNAPSHOT.md → GitHub Release line
[ ] system_manifest.json → version field
[ ] index.html → if version shown on site

[ ] PROJECT KNOWLEDGE:
    [ ] EVOLUTION_LOG → SESSION LOG row
    [ ] CLAUDE_PROJECT_MASTER → HISTORY table
```

---

### 🏗️ ARCHITECTURE CHANGE

```
[ ] docs/PROTOCOL.md → update specification
[ ] docs/ARCHITECTURE.md → update diagrams
[ ] README.md → architecture section
[ ] llms.txt → What this repo does
[ ] AGENTS.md → Architecture in one paragraph
[ ] CONTEXT_SNAPSHOT.md → innovations / layers

[ ] PROJECT KNOWLEDGE:
    [ ] DECISION_LOG → DEC-XXX new decision (REQUIRED)
    [ ] EVOLUTION_LOG → VERIFIED ARCHITECTURE
    [ ] CLAUDE_PROJECT_MASTER → innovations + layers
```

---

## LESSONS: HOW TAILS APPEAR

| When | What was missed | Consequence |
|------|----------------|-------------|
| 2026-03-15 | 6 new claims → didn't update 12+ locations | Numbers mismatched everywhere |
| 2026-03-16 | Real data tests (+47) → manifest not updated | system_manifest.json lagged |
| 2026-03-16 | Real data tests → index.html not updated in same PR | Required separate PR |
| 2026-03-16 | JobStatus.value == "succeeded" | CI failed — case sensitivity |
| 2026-03-17 | Origin section prose "223 passing tests" not updated | grep missed prose text |
| 2026-03-14 | Step Chain claimed before verifying code | Overclaim |

**Rule:** When adding tests — update numbers everywhere IN THE SAME PR.
Not "later in batch" — in that exact commit.

---

## VERIFICATION COMMANDS BEFORE MERGE

```bash
# 1. Governance
python scripts/steward_audit.py
# → STEWARD AUDIT: PASS

# 2. All tests
python -m pytest tests/ -q
# → N passed

# 3. Full verification
python scripts/deep_verify.py
# → ALL 13 TESTS PASSED

# 4. No forbidden terms
grep -r "tamper-proof\|GPT-5\|19x\|blockchain\|unforgeable" scripts/ backend/ tests/
# → empty

# 5. Numbers in sync (PowerShell)
Select-String "OLD_NUMBER" index.html, README.md, llms.txt, system_manifest.json | `
  Where-Object {$_.Line -notmatch "rgba\(0,255,223|&#223;|'0,255,223'"}
# → empty
```

---

## PROJECT KNOWLEDGE — HOW TO UPDATE

**What to update and when:**

| File | Update when |
|------|-------------|
| `EVOLUTION_LOG.md` | After every significant session |
| `NEXT_CHAT_PRIMER.md` | When priorities change |
| `CLAUDE_PROJECT_MASTER_vX.md` | New claims, numbers, outreach |
| `AUDIT_PROTOCOL.md` | New lessons or new places to check |
| `DECISION_LOG.md` | Every non-trivial architectural decision |
| `CURSOR_MASTER_PROMPT_v2_X.md` | New rules, traps, real data |

**Process:**
```
1. Download file from repo (or create in Claude)
2. Update content
3. Delete old version from Project Knowledge
4. Upload new version
```

---

*UPDATE_PROTOCOL v1.1 — 2026-03-18 — MetaGenesis Core*
*Update when new change types appear*

---

## NEW CHANGE TYPES ADDED IN v1.1

### 🔒 NEW VERIFICATION LAYER

```
[ ] scripts/mg_<layer>.py — implementation
[ ] scripts/mg.py — integrate into verify pipeline
[ ] tests/steward/test_cert<N>_*.py — adversarial proof
[ ] docs/PROTOCOL.md — add layer description + update count
[ ] docs/ARCHITECTURE.md — update layer count + attack hierarchy
[ ] README.md — update layers count + attack table
[ ] SECURITY.md — add layer section
[ ] CONTRIBUTING.md — update layer count
[ ] CITATION.cff — update layer count
[ ] CLAUDE.md — update 5-LAYER VERIFICATION section
[ ] index.html — update layer count everywhere
[ ] demos/open_data_demo_01/README.md — update layer count
[ ] UPDATE_PROTOCOL.md — this file
```

### 💡 NEW INNOVATION (patent)

```
[ ] ppa/README_PPA.md — add to post-filing table
[ ] COMMERCIAL.md — update innovation count
[ ] README.md — add innovation section
[ ] CLAUDE.md — update innovations count
[ ] system_manifest.json — add to verified_innovations
[ ] paper.md — update innovation count + description
[ ] CURSOR_MASTER_PROMPT_v2_X.md — BLOCK A current state
```

---

## ⚠️ CRITICAL: FILES AGENTS HISTORICALLY MISS

These files contain version strings but are NOT touched often.
They require CONTENT-BASED checking (not git-based).
`check_stale_docs.py --strict` blocks merge if banned strings found.

```
UPDATE_PROTOCOL.md        ← deep_verify count, version
CURSOR_MASTER_PROMPT_*.md ← current state block (511 tests)
SECURITY.md               ← layer count (three/four)
COMMERCIAL.md             ← innovation count (5/6/7)
CITATION.cff              ← version, date, layer count
ppa/README_PPA.md         ← test count, innovation count
demos/*/README.md         ← layer count
docs/PROTOCOL.md          ← version, layer count
docs/ARCHITECTURE.md      ← version, test count
docs/ROADMAP.md           ← version, test count
known_faults.yaml         ← test count
```
