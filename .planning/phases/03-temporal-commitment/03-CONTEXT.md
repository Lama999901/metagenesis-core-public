# Phase 3: Temporal Commitment - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Embed a temporal commitment proving WHEN a bundle was signed, as an independent Layer 5 that works offline and degrades gracefully. Uses NIST Randomness Beacon 2.0 as the temporal authority with local timestamp fallback. Includes a pre-commitment scheme to prove bundle existence before the beacon pulse. Verification is fully offline.

</domain>

<decisions>
## Implementation Decisions

### NIST Beacon integration
- Primary source: NIST Randomness Beacon 2.0 API (`/pulse/last` endpoint)
- Fallback: local ISO timestamp when beacon unreachable
- Fetch latest pulse at sign time (one HTTP call via `urllib.request`)
- 5-second network timeout before falling back to local timestamp
- Capture three fields from beacon response: `outputValue` (512-bit random), `timeStamp`, and pulse URI
- stdlib-only: use `urllib.request` for HTTP, no external dependencies

### Temporal data embedding
- Separate `temporal_commitment.json` file in bundle directory (NOT in bundle_signature.json)
- Layer 5 is independent of Layer 4 — separate files enforce this
- Version field: `"temporal-nist-v1"` following established pattern (hmac-sha256-v1, ed25519-v1)
- Cryptographic binding: `SHA-256(root_hash + beacon_value + timestamp)` — simple concatenation hash
- Both `pre_commitment_hash` and `temporal_binding` stored in the file for full auditability
- Created automatically during `mg_sign.py sign` AND available as standalone `mg_sign.py temporal` subcommand

### Pre-commitment scheme (TEMP-06)
- Two-phase hash-then-bind pattern:
  - Phase 1: Compute `pre_commitment_hash = SHA-256(root_hash)` BEFORE fetching beacon
  - Phase 2: Fetch beacon, then `temporal_binding = SHA-256(pre_commitment_hash + beacon_value + timestamp)`
- `pre_commitment_hash` proves the root_hash existed before the beacon value was known
- Both hashes stored in `temporal_commitment.json` for independent verification
- CLI output shows the flow transparently: "Pre-commitment: [hash]\nFetching beacon...\nTemporal commitment: [binding]"

### Graceful degradation
- When beacon unreachable: write `temporal_commitment.json` with local ISO timestamp, `pre_commitment_hash` (still valid), beacon fields set to null, `"beacon_status": "unavailable"`
- Default behavior: warn to stderr ("WARNING: NIST Beacon unreachable -- temporal commitment using local timestamp only") and continue (exit 0)
- `--strict` flag: fail with exit 1 when beacon unavailable (for CI pipelines that enforce beacon availability)
- Verification of degraded bundles: PASS with advisory note ("Temporal: local timestamp only (no beacon proof)")

### Verification behavior
- Fully offline — NEVER makes network calls during verify (TEMP-05)
- Checks embedded data structure and cryptographic binding only
- Verifies: (1) pre_commitment_hash = SHA-256(root_hash), (2) temporal_binding = SHA-256(pre_commitment_hash + beacon_value + timestamp)
- Independent of Layers 1-4 (TEMP-04) — temporal verification does not depend on manifest, semantic, or step chain checks

### Claude's Discretion
- Internal module structure (new file vs extending mg_sign.py)
- Exact JSON field names in temporal_commitment.json (beyond the decided fields)
- Error message wording for beacon failures
- How to structure the standalone `temporal` subcommand CLI arguments

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing signing infrastructure
- `scripts/mg_sign.py` -- Current signing module. `sign_bundle()` writes `bundle_signature.json`. Temporal data goes in a SEPARATE file (`temporal_commitment.json`), not here. The `sign` command will auto-create temporal commitment after signing.
- `scripts/mg.py` -- Core verifier CLI. Layer 5 verification to be added here or via mg_sign.py. `_verify_pack()` handles Layers 1-3.
- `scripts/mg_ed25519.py` -- Ed25519 implementation (Phase 1). Not directly used by temporal, but signing flow triggers temporal after Ed25519/HMAC sign.

### Requirements
- `.planning/REQUIREMENTS.md` -- TEMP-01 through TEMP-06 define all temporal commitment requirements

### Project constraints
- `CLAUDE.md` -- Sealed files list, banned terms, verification gates, stdlib-only constraint

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/mg_sign.py:sign_bundle()` -- Signs bundle and writes `bundle_signature.json`. Temporal hook goes after this function completes.
- `scripts/mg_sign.py:load_key()` -- Already handles dual-algorithm key loading. May need to be accessible for temporal CLI.
- `hashlib.sha256` -- Used throughout codebase for all hash operations.
- `urllib.request` -- stdlib HTTP client, suitable for beacon API calls.

### Established Patterns
- JSON artifact files with `version` field as format discriminator (hmac-sha256-v1, ed25519-v1 -> temporal-nist-v1)
- `(ok, message)` tuple returns for verification functions
- Lazy imports for optional functionality (Ed25519 imports in mg_sign.py)
- CLI uses argparse subcommands pattern

### Integration Points
- `mg_sign.py sign` command -- needs to call temporal commitment creation after signing
- `mg_sign.py` CLI -- needs new `temporal` subcommand for standalone use
- `mg.py verify` or `mg_sign.py verify` -- needs Layer 5 temporal check
- `bundle_signature.json` -- NOT modified; temporal data lives in separate `temporal_commitment.json`

</code_context>

<specifics>
## Specific Ideas

- `temporal_commitment.json` as a separate file enforces Layer 5 independence from Layer 4 (signing) at the file level
- Pre-commitment hash proves bundle existed before beacon pulse -- this is the key innovation (Innovation #7)
- The `--strict` flag gives CI pipelines control over whether beacon availability is required
- Transparent CLI output during sign ("Pre-commitment: ... Fetching beacon... Temporal commitment: ...") gives users visibility into the two-phase process

</specifics>

<deferred>
## Deferred Ideas

- Cross-claim temporal chain (temporal DAG) -- TEMP-V2-01, deferred to v0.5.0
- RFC 3161 TSA as alternative temporal authority -- TEMP-V2-02, deferred to v0.5.0
- Temporal chain explorer CLI -- TEMP-V2-03, deferred to v0.5.0
- Online verification mode (--online flag to cross-check beacon pulse against NIST) -- future enhancement

</deferred>

---

*Phase: 03-temporal-commitment*
*Context gathered: 2026-03-17*
