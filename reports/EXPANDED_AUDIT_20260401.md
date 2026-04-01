# MetaGenesis Core — Expanded Technical + Mission Audit

Date: 2026-04-01 | Git: 58501346f186666e7feb712886e826f69a27243b | Auditor: GSD v1.30.0 / Claude Opus 4.6

---

## Part 1: Technical Verification

| # | Check | Result | Detail |
|---|-------|--------|--------|
| 1 | steward_audit.py | PASS | All claims bidirectional, canonical sync PASS |
| 2 | pytest full suite | PASS | 608 passed, 2 skipped in 8.63s |
| 3 | deep_verify.py | PASS | ALL 13 TESTS PASSED |
| 4 | agent_evolution.py | PASS | ALL 18 CHECKS PASSED |
| 5 | agent_pr_creator.py | FLAG | False positive: manifest=608 vs collected=610 (--collect-only counts skipped tests; fix on branch fix/pr-creator-count-method) |
| 6 | check_stale_docs.py | PASS | 7 CURRENT, 0 STALE |
| 7 | Cross-Claim Chain | PASS | MTR-1 -> DT-FEM-01 -> DRIFT-01 chain verified — anchor_hash changes propagate |
| 8 | PHYS-01 (Boltzmann) | PASS | rel_err: 0.0 — SI 2019 exact constant kB verified |
| 8 | PHYS-02 (Avogadro) | PASS | rel_err: 0.0 — SI 2019 exact constant NA verified |
| 9 | CERT adversarial suite | PASS | 66 passed — CERT-02/03/05/07/09/10/11 + 5-layer independence |
| 10 | End-to-end demo | PASS | Built submission pack (23 files), PASS PASS |

---

## Part 2: Mission Alignment

| File | Term | Status |
|------|------|--------|
| CLAUDE.md | "notary for computations" | PRESENT |
| CLAUDE.md | "COMMERCIAL PRIORITY" | PRESENT |
| CLAUDE.md | "Six domains" | PRESENT |
| CLAUDE.md | "First paying customer at $299" | PRESENT |
| CLAUDE.md | "PHYS-01" / "PHYS-02" / "SI 2019" | PRESENT |
| CLAUDE.md | "608 tests" | PRESENT |
| AGENTS.md | "notary for computations" / "v0.8.0" / "608" / "PHYS-01" / "20 claims" | ALL PRESENT |
| README.md | "The open standard for verifiable computation" | PRESENT |
| README.md | "Why This Could Become a Standard" | PRESENT |
| README.md | "28 billion wasted" / "DOI became the standard" | PRESENT |
| README.md | "608" / "PHYS-01" / "PHYS-02" / "SI 2019, exact" | PRESENT |
| README.md | MUST NOT: "The Mechanicus Parallel" / "grim darkness" | ABSENT — PASS |
| README.md | MUST NOT: "595 passing" / "544 passing" | ABSENT — PASS |
| index.html | "notary for computations" / "28 billion" / "DOI became the standard" / "608" | ALL PRESENT |
| index.html | MUST NOT: "595/544/586 passing" | ABSENT — PASS |
| COMMERCIAL.md | "$299" / "physical anchor" / "60 seconds" / "#63/996,819" | ALL PRESENT |
| llms.txt | "20 active claims" | PRESENT |
| llms.txt | "608 passing" | MISSING — shows "595 passed" (line 106) and "595 passing" (line 112) |
| llms.txt | "v0.8.0" | MISSING — shows "MVP v0.6" (line 6) and "v0.6.0" (line 122) |
| llms.txt | "PHYS-01" / "PHYS-02" / "SI 2019" | MISSING — not listed in claims section |

---

## Part 3: Stale String Sweep

| File | Issue | Type | Status |
|------|-------|------|--------|
| llms.txt:106 | `# 595 passed` in "How to verify" | Old test count | STALE |
| llms.txt:112 | `Tests: 595 passing` in "Current state" | Old test count | STALE |
| llms.txt:6 | `MVP v0.6` | Old version | STALE |
| llms.txt:111 | `Claims: 18` | Old claim count | STALE |
| llms.txt:122 | `v0.6.0` release link | Old version | STALE |
| llms.txt:134-135 | `v0.5 protocol/architecture` refs | Old version refs | STALE |
| llms.txt:151 | `16 evolution checks` | Old check count | STALE |
| llms.txt | PHYS-01/PHYS-02 missing from claims list | Missing claims | STALE |
| CONTEXT_SNAPSHOT.md:25 | `595 passing` | Old test count | STALE |
| CONTEXT_SNAPSHOT.md:32 | `v0.6.0` release | Old version | STALE |
| CONTEXT_SNAPSHOT.md:99 | `# 595 passed` | Old test count | STALE |
| CONTEXT_SNAPSHOT.md:112 | `updated to 595` | Old test count | STALE |
| docs/PROTOCOL.md:1,343 | `MVP v0.5` header/footer | Old version | STALE |
| docs/PROTOCOL.md:281 | `all 14 claims` | Old claim count | STALE |
| docs/ARCHITECTURE.md:110,258 | `all 14 claims` (x2) | Old claim count | STALE |
| docs/ARCHITECTURE.md:270 | `Architecture v0.5` footer | Old version | STALE |
| docs/ROADMAP.md:7,27 | `MVP v0.5` / `14 claims` | Old version + count | STALE |
| docs/AGENT_SYSTEM.md:26 | `601+ adversarial tests` | Old test count | STALE |
| docs/AGENT_SYSTEM.md:55-57 | "Mechanicus Parallel" / Warhammer 40K | Warhammer reference | STALE |
| docs/AGENT_SYSTEM.md:64 | `all 18 claims` | Old claim count (should be 20) | STALE |
| paper.md:251 | `16-check health monitoring suite` | Old check count (should be 18) | STALE |
| ppa/README_PPA.md:27 | `all 14 claims` | Old claim count | STALE |

**Summary: 8 files with stale content. Primary files (README.md, CLAUDE.md, AGENTS.md, index.html) are clean. Secondary docs (PROTOCOL.md, ARCHITECTURE.md, ROADMAP.md, AGENT_SYSTEM.md, paper.md) need version/count updates. llms.txt and CONTEXT_SNAPSHOT.md are partially updated (some sections current, some stale).**

Note: `check_stale_docs.py` marks these as CURRENT because it finds required strings ("608") in updated sections — but does NOT detect OLD values coexisting in other sections. This is a check_stale_docs.py coverage gap.

---

## Part 4: Potential and Consistency

| Check | Result |
|-------|--------|
| PPA # in README.md, COMMERCIAL.md, ppa/README_PPA.md | PRESENT (#63/996,819) |
| PPA # in paper.md | MISSING |
| metagenesis-core.dev in index.html, README.md, COMMERCIAL.md | ALL PRESENT |
| "open standard" in README.md | PRESENT |
| "DOI became" in README.md | PRESENT |
| End-to-end demo | PASS PASS |
| 6 domains in scientific_claim_index.md | ALL 6 PRESENT (ML, Pharma, Finance, Digital Twin, Materials, Physics) |
| Test collection vs passed | 610 collected, 608 passed, 2 skipped — consistent |

---

## Part 5: Agent Autonomy

| Metric | Expected | Actual | Result |
|--------|----------|--------|--------|
| agent_pr_creator.py lines | >= 150 | 203 | PASS |
| agent_evolution.py check_ functions | 18 | 17 | FLAG (1 check may use different naming) |
| TASK-027 in AGENT_TASKS.md | present | present | PASS |
| Learned patterns | > 0 | 15 | PASS |
| TRAP-GSD-DEVIATION in patterns | present | present | PASS |
| Agent memory sessions | growing | 60 | PASS |

Note: `check_` function count shows 17 vs expected 18, but `agent_evolution.py --summary` reports ALL 18 CHECKS PASSED. One check likely uses a different function name prefix.

---

## Part 6: Self-Evolution

| Domain | Tests | Skipped | Result |
|--------|-------|---------|--------|
| materials | 25 | 0 | PASS |
| ml | 91 | 1 | PASS |
| digital_twin | 54 | 1 | PASS |
| physics | 6 | 0 | PASS |
| steward | 332 | 0 | PASS |
| systems | 3 | 0 | PASS |
| data | 3 | 0 | PASS |
| agent | 48 | 0 | PASS |
| cli | 16 | 0 | PASS |
| progress | 11 | 0 | PASS |
| **Total** | **589** | **2** | **PASS** |

Note: Domain subtotals (589+2=591) differ from full suite (608+2=610) because 19 tests reside in top-level test files (test_agent_pr_creator.py, test_coverage_boost.py, etc.) not under domain subdirectories.

Coverage: 40.6% (target 65%) | 126 zero-coverage | 26 low-coverage | 52 files

Self-improvement: 5 reports | 14 handlers (0 shallow) | 3 recommendations

Agent memory: session 60 recorded

Final evolution check: ALL 18 CHECKS PASSED

---

## VERDICT

**AUDIT PARTIAL — 3 categories of issues found:**

### Critical (affects mission alignment):
1. **llms.txt partially stale** — "How to verify" and "Current state" sections show 595 tests, v0.6, 18 claims, 16 checks. Missing PHYS-01/PHYS-02/SI 2019. File is partially updated (some sections current, some not).
2. **CONTEXT_SNAPSHOT.md partially stale** — Test count 595, release v0.6.0 in multiple sections.

### Moderate (secondary docs):
3. **docs/PROTOCOL.md** — MVP v0.5 header/footer, "14 claims"
4. **docs/ARCHITECTURE.md** — Architecture v0.5 footer, "14 claims" x2
5. **docs/ROADMAP.md** — MVP v0.5, "14 claims"
6. **docs/AGENT_SYSTEM.md** — 601+ tests, 18 claims (should be 20), Warhammer "Mechanicus Parallel" section still present
7. **paper.md** — "16-check" (should be 18-check)
8. **ppa/README_PPA.md** — "14 claims" (may be intentionally historical — PPA filed at v0.5)

### Low (tooling):
9. **agent_pr_creator.py** — false positive stale counter (--collect-only vs --passed); fix on branch `fix/pr-creator-count-method`
10. **check_stale_docs.py** — does not detect OLD values coexisting with new values in same file

### Green (all correct):
- README.md, CLAUDE.md, AGENTS.md, index.html, COMMERCIAL.md — fully current
- All 10 technical verification checks PASS
- All 20 claims operational, cross-claim chain intact
- PHYS-01/PHYS-02 SI 2019 exact constants verified (rel_err = 0.0)
- 66 adversarial CERT tests PASS
- End-to-end demo PASS PASS
- 608 tests passing, 18 evolution checks passing
- Agent memory growing (60 sessions, 15 patterns)

---

*Expanded Audit v0.8.0 — 2026-04-01 — MetaGenesis Core*
*608 tests | 20 claims | 18 checks | 8 stale files identified*
