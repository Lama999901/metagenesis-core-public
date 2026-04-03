# Technology Stack

**Analysis Date:** 2026-03-16

## Languages

**Primary:**
- Python 3.11+ - Core verification engine, CLI tools, claim computation, testing
- JSON - Configuration, manifests, evidence index, ledger entries
- Markdown - Documentation, claim registry, canonical state, phase registry

**Secondary:**
- HTML - Static site (`index.html` - 282KB, embedded dashboard)
- YAML - CI/CD workflows, known faults registry
- BibTeX - Academic citations (`paper.bib`)

## Runtime

**Environment:**
- Python 3.11 (validated in CI via `actions/setup-python@v5`)

**Package Manager:**
- pip (Python package installer)
- Lockfile: `requirements.txt` (present, no lock file like `Pipfile.lock`)

## Frameworks

**Core:**
- Pytest 8.4.1 - Unit and integration testing framework
- Pytest-cov 6.2.1 - Code coverage measurement

**Data Processing:**
- NumPy >= 1.21.0 - Numerical computing (calibration, FEM, ML benchmarks)
- SciPy >= 1.7.0 - Scientific computing (optimization, statistics)
- Pandas >= 1.3.0 - Data manipulation (pipelines, time series)

**Build/Dev:**
- No build framework detected (pure Python scripts, no setuptools/Poetry/Hatch)
- No dependency management tool (direct pip install from requirements.txt)

## Key Dependencies

**Critical:**
- `pytest` (8.4.1) - Test runner (295 tests must pass for steward audit)
- `numpy` (>=1.21.0) - Powers 14 claims across materials, digital twin, ML benchmarking domains
- `scipy` (>=1.7.0) - Optimization for calibration (MTR-1, MTR-2, MTR-3)
- `pandas` (>=1.3.0) - Time series and data pipeline verification

**Infrastructure:**
- None detected - no database drivers, no API clients, no external service SDKs

## Configuration

**Environment:**
- No `.env` file pattern detected
- Environment variable usage: `MG_PROGRESS_ARTIFACT_DIR` (passed at test runtime)
- No centralized config loader (args passed directly via CLI and function parameters)

**Build:**
- CI/CD via GitHub Actions (`.github/workflows/`)
  - `total_audit_guard.yml` - Runs steward audit on PR/push to main
  - `mg_policy_gate.yml` - File modification policy enforcement via `mg_policy_gate_policy.json`
- Python 3.11 installed in CI with pip upgrading first
- No Docker/containerization detected

## Platform Requirements

**Development:**
- Python 3.11+
- `pip` package manager
- POSIX shell (scripts use `#!/usr/bin/env python3`)
- POSIX file locking support (`fcntl` module) - optional, degrades gracefully on non-POSIX (Windows)

**Production:**
- Verification runs offline - no runtime environment needed beyond Python
- Package format: ZIP bundles (`.zip` files verified via `python scripts/mg.py verify --pack bundle.zip`)
- Signing requires optional cryptography package for Ed25519 mode (currently HMAC-SHA256 stdlib-only)

## No External Dependencies

**Explicitly avoided:**
- No network/HTTP clients (`requests` not in requirements)
- No database library (`sqlite3` is stdlib only, not used)
- No API SDKs (verification is fully offline)
- No LLM/AI framework (pure deterministic computation)
- No async runtime (synchronous execution)
- No logging framework (stdlib `logging` module only)

## Language-Specific Patterns

**Python:**
- Type hints used extensively (PEP 484 style)
- Dataclasses for models (`@dataclass` decorator in `backend/progress/models.py`, `backend/ledger/models.py`)
- Pure stdlib where possible (no external secrets management, no ORMs)
- Deterministic JSON serialization (`json.dumps(sort_keys=True, separators=(',', ':'))`)
- String normalization for cross-platform compatibility (CRLF→LF in `fingerprint_file()`)

## Verification Gates

All code must pass before commit:

```bash
python scripts/steward_audit.py   # Governance validation
python -m pytest tests/ -q        # 295 tests must pass
python scripts/deep_verify.py     # 10-test proof script
```

These gates ensure:
- No file type violations (checked in `mg_policy_gate.py`)
- Claim coverage bidirectional (claim index ↔ runner dispatch)
- All phase declarations valid (phase registry locked at phase 42)

---

*Stack analysis: 2026-03-16 | v0.3.0 | 14 active claims | 295 tests*
