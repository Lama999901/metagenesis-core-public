# Phase 9: Academic Infrastructure - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

MetaGenesis Core has complete academic citation infrastructure ready for Zenodo DOI minting and JOSS resubmission. Fix .zenodo.json stale test count (1321→1634), verify CITATION.cff currency, add DOI badge placeholder to README.md, and sync paper.md cross-references.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key facts:
- .zenodo.json exists but has stale test count (1321, should be 1634)
- CITATION.cff exists and looks current (v0.9.0, 1634 tests in abstract)
- README.md needs DOI badge placeholder (Zenodo deposit not yet created)
- paper.md cross-references need verification against current state
- DOI badge format: `[![DOI](https://zenodo.org/badge/DOI/...)](https://doi.org/...)`

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- .zenodo.json — Zenodo metadata file (needs test count fix)
- CITATION.cff — CFF citation file (v0.9.0, looks current)
- system_manifest.json — source of truth for counts

### Established Patterns
- Counter updates follow UPDATE_PROTOCOL v1.1 — check_stale_docs.py rules must match
- README.md already has badge section at top

### Integration Points
- check_stale_docs.py may need rules for .zenodo.json if not already tracked
- paper.md references test count, claim count, layer count, innovation count

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Follow Zenodo and CFF standards.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>
