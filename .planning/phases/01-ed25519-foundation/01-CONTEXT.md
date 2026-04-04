# Phase 1: Ed25519 Foundation - Context

**Gathered:** 2026-03-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement a pure-Python Ed25519 module (RFC 8032 Section 5.1) with key generation CLI and self-test capability. Prove cryptographic correctness via all RFC 8032 Section 7.1 test vectors before any integration with bundle signing. Bundle signing integration is Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Module placement
- New file `scripts/mg_ed25519.py` — standalone, next to `mg_sign.py`
- Self-contained: Ed25519 math, key generation, sign, verify all in one module
- `mg_sign.py` will import from it in Phase 2 (not this phase)

### Self-test mode
- Running `python scripts/mg_ed25519.py` directly executes all RFC 8032 Section 7.1 test vectors and prints PASS/FAIL
- ALSO add pytest tests in `tests/` directory for CI integration
- Both modes must pass — self-test is the quick validation, pytest is the CI gate

### Key file format
- Same JSON structure as existing HMAC keys: `{version, ..., fingerprint, note}`
- Version field: `"ed25519-v1"` (existing HMAC uses `"hmac-sha256-v1"`)
- Fields: `version`, `private_key_hex`, `public_key_hex`, `fingerprint`, `note`
- Store BOTH private and public key in the key file — avoids recomputation, makes public key export trivial
- Fingerprint: SHA-256 of public key (safe to share)
- Version field is what drives algorithm dispatch in Phase 2

### CLI interface
- Phase 1: `mg_ed25519.py` has its own standalone CLI with keygen subcommand
- Phase 2: `mg_sign.py keygen --algorithm ed25519` integrates it
- Both entry points will work — `mg_ed25519.py` for standalone, `mg_sign.py` for unified signing
- keygen auto-generates two files: `key.json` (full private+public) and `key.pub.json` (public only for sharing with auditors)
- No separate export subcommand needed — public key file created at keygen time

### RFC 8032 scope
- Ed25519 only (Section 5.1) — no Ed25519ph (prehash) or Ed25519ctx (context)
- Basic Ed25519 is sufficient for signing root hashes (64-byte hex strings)
- All test vectors from RFC 8032 Section 7.1 — the gold standard for correctness
- No fuzzing or custom edge cases beyond RFC vectors in Phase 1

### Claude's Discretion
- Internal module structure (helper functions, class vs functions)
- Elliptic curve arithmetic implementation details
- Error message wording
- Exact test output format (as long as PASS/FAIL is clear)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing signing infrastructure
- `scripts/mg_sign.py` — Current HMAC signing module. Ed25519 key format must parallel the HMAC key format (version, fingerprint fields). Phase 2 will integrate mg_ed25519.py here.
- `scripts/mg.py` — Core verifier CLI. NOT modified in Phase 1. Minimal changes in Phase 2.

### Cryptographic specification
- RFC 8032 Section 5.1 — Ed25519 algorithm specification (sign, verify, key generation)
- RFC 8032 Section 7.1 — Ed25519 test vectors (all must pass)

### Project constraints
- `CLAUDE.md` — Sealed files list, banned terms, verification gates, coding conventions
- `.planning/research/STACK.md` — Pure-Python Ed25519 approach, stdlib-only rationale
- `.planning/research/PITFALLS.md` — Ed25519 correctness risks, downgrade attack prevention

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/mg_sign.py`: Key file JSON format pattern (`version`, `key_hex`, `fingerprint`, `note`) — Ed25519 keys follow the same shape
- `scripts/mg_sign.py`: CLI pattern using `argparse` subcommands (`cmd_keygen`, `cmd_sign`, `cmd_verify`)
- `hashlib.sha256` and `hashlib.sha512` — stdlib, already used throughout codebase

### Established Patterns
- All crypto modules are in `scripts/` directory (mg.py, mg_sign.py)
- `KEY_VERSION = "hmac-sha256-v1"` — version constant at module level, used for format detection
- `SIGNATURE_VERSION = "hmac-sha256-v1"` — signature file version for bundle_signature.json
- Key files are JSON with `version` field as the discriminator
- Functions return `(ok, message)` tuples for verification results

### Integration Points
- Phase 2 will have `mg_sign.py` import from `mg_ed25519.py` — module must expose clean public API
- Key generation must produce JSON files compatible with `load_key()` pattern in mg_sign.py
- Policy gate allowlist already includes `scripts/**` — new file needs no policy changes

</code_context>

<specifics>
## Specific Ideas

- Ed25519 key file automatically generates companion `.pub.json` file at keygen time — no separate export step
- Self-test mode when running `python scripts/mg_ed25519.py` directly mirrors how `python scripts/deep_verify.py` runs proof tests
- Version field `"ed25519-v1"` parallels existing `"hmac-sha256-v1"` — this is the discriminator for Phase 2 auto-detection

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-ed25519-foundation*
*Context gathered: 2026-03-17*
