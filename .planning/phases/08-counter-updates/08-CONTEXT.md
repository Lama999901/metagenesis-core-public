# Phase 8: Counter Updates - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Update all documentation counters to reflect the final v0.5.0 test count (currently 511), bump version strings from v0.4.0 to v0.5.0 across all files, and overhaul index.html site content to reflect v0.5.0 capabilities (Layer 5, CERT-11/12, updated feature matrix). Two plans: 08-01 counter/version propagation across docs, 08-02 index.html content overhaul.

</domain>

<decisions>
## Implementation Decisions

### Version Bump
- Bump version from v0.4.0 to v0.5.0 everywhere: system_manifest.json, index.html, README.md, CONTEXT_SNAPSHOT.md, llms.txt, CLAUDE.md
- This is the v0.5.0 Coverage Hardening milestone — version bump is part of completion

### Counter Discovery & Propagation
- Update system_manifest.json `test_count` first (run pytest to get exact count)
- Then propagate that count from system_manifest.json to all other files as single source of truth
- Files to update: index.html (multiple places), README.md, AGENTS.md, llms.txt, CONTEXT_SNAPSHOT.md, CLAUDE.md

### CLAUDE.md Updates
- Update all stale counters: "389 tests" → final count, "295 passing" → final count
- Update version references: "v0.3.0" → "v0.5.0" where appropriate
- CLAUDE.md is primary AI context file — accuracy prevents downstream agent confusion

### Stale Counter Cleanup
- index.html line 1756 "270 tests" → update to final count (not historical, just stale)
- All occurrences of old counts (389, 295, 270) across all documentation files must be updated

### index.html Content Overhaul (Plan 08-02)
- Hero badge: 511 tests, v0.5.0, 5 layers, CERT-11
- Protocol section: add Layer 5 Temporal Commitment
- Crisis section: add CERT-11 row (coordinated multi-vector attack → CAUGHT)
- Crisis section: add CERT-12 row (encoding attacks → CAUGHT)
- Compare section: update feature matrix
- Stats: 511 tests, 5 layers, 12 CERT files, 14 claims

### Validation
- Run check_stale_docs.py and fix ALL stale files found
- GOV-03 governance meta-tests from Phase 5 must pass with updated counters (no drift detected)

### Claude's Discretion
- Exact wording for new CERT-11/12 rows in crisis section
- How to present Layer 5 in protocol section (follows existing Layer 1-4 pattern)
- Feature matrix column/row additions for compare section
- Whether to update deep_verify test count references (currently "13 TESTS")

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Counter Sources of Truth
- `system_manifest.json` — Machine-readable counters, authoritative for test_count and version
- `tests/steward/test_stew08_documentation_drift.py` — GOV-03 governance meta-test that validates counter consistency

### Files Requiring Counter Updates
- `index.html` — 11+ places with test counts, version, layer counts (see CLAUDE.md §COMMON BUGS #7)
- `README.md` — Test count references
- `AGENTS.md` — Deep verify test count references
- `llms.txt` — Test count and version references
- `CONTEXT_SNAPSHOT.md` — Test count, version references
- `CLAUDE.md` — Test counts (389, 295), version (v0.3.0)

### Site Content References
- `index.html` — Protocol section (Layers 1-4), Crisis section (CERT rows), Compare section (feature matrix), Stats section
- `scripts/mg_temporal.py` — Layer 5 implementation details for site content
- `tests/steward/test_cert11_coordinated_attack.py` — CERT-11 thesis for crisis section row
- `tests/steward/test_cert12_encoding_attacks.py` — CERT-12 thesis for crisis section row

### Architecture
- `CLAUDE.md` §4-LAYER VERIFICATION — Layer descriptions (extend to 5 for site)
- `CLAUDE.md` §COMMON BUGS #7 — PowerShell batch replace pattern for index.html

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `test_stew08_documentation_drift.py`: GOV-03 meta-test — validates counters match system_manifest.json. Run after updates to verify consistency.
- `system_manifest.json`: Single source of truth for test_count, active_claims, version
- CLAUDE.md §COMMON BUGS #7: PowerShell batch replace pattern for index.html mass updates

### Established Patterns
- Counter updates use PowerShell: `(Get-Content index.html -Raw) -replace 'OLD_N', 'NEW_N' | Set-Content index.html`
- system_manifest.json updated first, then propagated to docs
- GOV-03 meta-test uses relational assertions against system_manifest.json (Phase 5 decision)

### Integration Points
- GOV-03 meta-test in test_stew08_documentation_drift.py validates counter consistency post-update
- Steward audit (`python scripts/steward_audit.py`) must still PASS after all changes
- Policy gate allowlist already covers all target file types (*.md, *.json, index.html)

</code_context>

<specifics>
## Specific Ideas

- Run pytest first to get exact count, write to system_manifest.json, then propagate everywhere
- Use PowerShell batch replace for index.html (11 places) per CLAUDE.md bug #7
- CERT-11 crisis row: "Coordinated multi-vector attack across 5 layers → CAUGHT by remaining independent layers"
- CERT-12 crisis row: "Encoding attacks (BOM, null bytes, homoglyphs, truncated JSON) → CAUGHT"
- Layer 5 in protocol section follows existing Layer 1-4 format: "Layer 5 — Temporal Commitment / scripts/mg_temporal.py / catches: backdated bundle"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-counter-updates*
*Context gathered: 2026-03-17*
