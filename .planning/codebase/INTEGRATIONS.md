# External Integrations

**Analysis Date:** 2026-03-16

## APIs & External Services

**None detected.**

MetaGenesis Core is designed as a **fully offline verification system** with zero external service dependencies. The codebase contains:
- No HTTP client imports (`requests`, `urllib`)
- No API SDK imports
- No calls to external services
- No API keys, tokens, or credentials

This is intentional: verification must work air-gapped, with no network access required or possible.

## Data Storage

**Databases:**
- None in use
- No database drivers detected (`sqlite3`, `psycopg2`, `mysqlclient`, `pymongo`)
- All state stored as files in repository

**File Storage:**
- Local filesystem only
  - Evidence artifacts: `reports/progress_runs/` (JSON trace files)
  - Ledger: `reports/ledger_v1.jsonl` (append-only, POSIX file-locked)
  - Job store: In-memory only (`backend/progress/store.py` - no persistence)
  - Verification packs: ZIP files with JSON manifests

**Caching:**
- None - all computation deterministic and reproducible (no cache needed)

## Authentication & Identity

**Auth Provider:**
- None - no user/identity system

**Key Storage:**
- Bundle signing uses HMAC-SHA256 or Ed25519
- Signing key stored as JSON (caller responsible for securing)
- Key location determined at runtime (no default location)
- Optional Ed25519 mode requires `cryptography` package (not in base requirements)

## Monitoring & Observability

**Error Tracking:**
- None detected - no Sentry, Bugsnag, or similar

**Logs:**
- Stdlib `logging` module only (`import logging` throughout)
- Log level configurable but not exposed via CLI (defaults to WARNING)
- Example: `logger.info("Ledger entry appended: {entry.trace_id}")`

## CI/CD & Deployment

**Hosting:**
- GitHub (repository: https://github.com/Lama999901/metagenesis-core-public)
- Static site: https://metagenesis-core.dev (external host, not in scope of this codebase)

**CI Pipeline:**
- GitHub Actions (`.github/workflows/`)
  - Trigger: PR to main, push to main
  - Python 3.11 installed fresh for each run
  - Steps: checkout → setup Python → pip install → steward audit → pytest
  - No secrets detected in workflows (FORCE_JAVASCRIPT_ACTIONS_TO_NODE24 is node.js version pin)

## Environment Configuration

**Required env vars:**
- `MG_PROGRESS_ARTIFACT_DIR` - Path where claim jobs write artifacts (fallback to `reports/progress_runs/` if unset)
- No other environment variables detected

**No secrets in configuration:**
- `.env` files not present (checked `.gitignore`, no `.env*` pattern)
- No API keys, tokens, or credentials in codebase
- Signing key file is user-supplied at runtime (never committed)

## Webhooks & Callbacks

**Incoming:**
- None - verification is a single CLI command, no server component

**Outgoing:**
- None detected

## Git Hooks

**Pre-commit/Push:**
- Not detected (no `.git/hooks/` configuration in codebase)
- Enforcement via GitHub Actions (policy gate on PR)

## Verification Bundle Format

Bundles are ZIP files containing:
```
bundle.zip
├── pack_manifest.json       # Layer 1: file integrity (SHA-256 hashes + root_hash)
├── evidence_index.json      # Layer 2: semantic validation (job_kinds, paths, modes)
├── claims/                  # Layer 3: step chain evidence
│   ├── MTR-1/
│   │   ├── normal/
│   │   │   ├── run_artifact.json
│   │   │   └── ledger.jsonl
│   │   └── canary/
│   └── ML_BENCH-01/
└── bundle_signature.json    # Layer 4: bundle signing (HMAC-SHA256 or Ed25519)
```

Format is pure JSON + JSONL — no custom binary format, fully auditable.

## Data Flow (No External Integrations)

```
User claims computation
        ↓
backend/progress/<claim_id>.py executes claim logic
        ↓
Outputs: run_artifact.json (normal mode), ledger.jsonl (all modes)
        ↓
Packager: steward_submission_pack.py reads artifacts
        ↓
Computes: pack_manifest.json (integrity), evidence_index.json (semantic)
        ↓
Optional: Bundle signing (mg_sign.py) adds signature
        ↓
ZIP bundle ready for distribution
        ↓
Verifier: mg.py verify reads ZIP, checks 4 layers offline
        ↓
Result: PASS or FAIL (deterministic, no external calls)
```

## Standards & Specifications

**Cryptographic:**
- SHA-256 (FIPS 180-4) - All hashes
- HMAC-SHA256 (RFC 2104) - Bundle signing (default)
- Ed25519 (RFC 8032) - Bundle signing (optional, requires `cryptography` package)

**File Formats:**
- JSON (RFC 8259) - Manifests, evidence, ledger entries
- JSON Lines (RFC 7464 variant) - Ledger append-only format (one JSON per line)
- ZIP (PKWARE) - Bundle container

**No vendor lock-in:**
- All formats open, auditable, reproducible
- No proprietary codecs, file formats, or protocols
- Verifier is pure Python, no compiled binaries

---

*Integration audit: 2026-03-16 | Fully offline | Zero external dependencies*
