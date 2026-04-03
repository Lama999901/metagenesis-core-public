# Coding Conventions

**Analysis Date:** 2026-03-16

## Naming Patterns

**Files:**
- Module files use snake_case: `mtr1_calibration.py`, `data_integrity.py`, `dtfem1_displacement_verification.py`
- Test files follow pattern `test_<domain>_<claim_id>.py`: `test_mtr1_youngs_modulus.py`, `test_dtfem01_displacement_verification.py`
- Claim implementation files match job kind slugs: `mlbench1_accuracy_certificate.py`, `drift_monitor.py`

**Functions:**
- Use snake_case for all function definitions: `generate_synthetic_data()`, `estimate_E_ols_origin()`, `run_calibration()`
- Private functions prefixed with underscore: `_seeded_noise()`, `_hash_step()`, `_normalize_evidence()`
- Public entry point functions named `run_<operation>`: `run_calibration()`, `run_certificate()`

**Variables:**
- Use snake_case for all local variables and parameters: `E_true`, `max_strain`, `noise_scale`, `job_id`, `trace_id`
- Constants use SCREAMING_SNAKE_CASE at module level: `JOB_KIND`, `ALGORITHM_VERSION`, `METHOD`, `REPO_ROOT`
- Private module attributes prefixed with underscore: `_ROOT`, `_prev`, `_trace`, `_passed_sc`

**Types:**
- Enum classes follow PascalCase: `JobStatus`, `LedgerEntry`
- Type hints use full module paths where needed: `Dict[str, Any]`, `List[float]`, `Optional[str]`
- Dataclass models follow PascalCase: `Job`, `LedgerStore`, `JobStore`, `ProgressRunner`

## Code Style

**Formatting:**
- Python 3.6+ style (f-strings, type hints)
- Line length: No strict limit enforced, but most lines stay under 100 chars
- Indentation: 4 spaces throughout
- No external formatter (black/autopep8) required
- Consistent quote style: double quotes preferred (`"string"`)

**Linting:**
- No external linter configuration detected (no `.flake8`, `.pylintrc`, or `pyproject.toml`)
- Style is enforced through code review and steward_audit script
- steward_audit checks file allowlist and policy compliance, not style

**Shebang:**
- All Python scripts begin with `#!/usr/bin/env python3` at line 1
- Module docstring immediately follows
- Encoding declaration not used (default UTF-8 assumed)

## Import Organization

**Order:**
1. Shebang and module docstring
2. Standard library imports (`import sys`, `import os`, `from pathlib import Path`)
3. Built-in imports (`import json`, `import hashlib`, `import csv`, `from typing import ...`)
4. Relative imports (`.models`, `.store`, `.data_integrity`)

**Examples:**
```python
#!/usr/bin/env python3
"""Module docstring describing purpose and context."""

import csv
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from backend.progress.data_integrity import fingerprint_file
from backend.progress.models import Job
```

**Path Handling:**
- Use `Path(__file__).resolve()` to get script location: `REPO_ROOT = Path(__file__).resolve().parent.parent.parent`
- Store root paths as module constants for importing from anywhere
- Relative imports from backend: `from backend.progress.runner import ProgressRunner`
- sys.path manipulation only when necessary for test imports

## Error Handling

**Patterns:**
- Raise `ValueError` for invalid input parameters: `raise ValueError(f"max_strain must be positive")`
- Include descriptive messages with context: `raise ValueError(f"Dataset not found: {dataset_relpath}")`
- Catch specific exceptions: `except (KeyError, ValueError): continue` in CSV parsing
- Try-except around file operations and JSON parsing with descriptive error messages
- No bare `except` clauses; always specify exception type

**Validation:**
- Validate inputs at function start before expensive operations: `if n_points < 2: raise ValueError(...)`
- Check for None/empty before operations: `if n == 0: return 0.0`
- Division by zero prevention: `if sum_ee == 0: return 0.0`
- Boundary checks with <= or >= operators: `if s <= elastic_strain_max: strain.append(s)`

## Logging

**Framework:** Python stdlib `logging` module

**Patterns:**
- Create module-level logger: `logger = logging.getLogger(__name__)`
- Log at INFO level for normal operations: `logger.info(f"Job created and logged: {job.job_id}")`
- Log at WARNING level for non-fatal issues: `logger.warning(f"Job {job.job_id} already exists, updating")`
- Include context in log messages (IDs, statuses): `f"Job updated: {job.job_id} (status={job.status.value})"`
- Initialize with info messages: `logger.info("ProgressRunner initialized with ledger integration")`

**Examples from code:**
```python
logger = logging.getLogger(__name__)
logger.info(f"Job created: {job.job_id} (trace={job.trace_id})")
logger.warning(f"Job {job.job_id} already exists, updating")
logger.info(f"Job updated: {job.job_id} (status={job.status.value})")
```

## Comments

**When to Comment:**
- Algorithm explanations in docstrings: `"E_hat = sum(strain_i * stress_i) / sum(strain_i^2)."`
- Step chain verification sections explicitly marked: `# --- Step Chain Verification ---` and `# --- End Step Chain ---`
- Complex calculations with formula references
- Important constraints or assumptions: `"avoid division by zero in OLS"`
- Not for obvious code: `x += 1  # Don't say "increment x"`

**Docstring Format:**
- Module docstrings at top (lines 2-6): Purpose, brief description
- Function docstrings: One-line purpose, parameters (if complex), return type/description
- Docstrings use triple double quotes: `"""..."""`

**Examples:**
```python
"""
MTR-1 Young's Modulus Calibration - OLS through origin.

Purpose: Deterministic calibration workload for Progress Engine evidence.
Synthetic mode or dataset-backed (DATA-01 fingerprint). No heavy deps (stdlib only).
"""

def estimate_E_ols_origin(strain: List[float], stress: List[float]) -> float:
    """E_hat = sum(strain_i * stress_i) / sum(strain_i^2)."""

def _load_stress_strain_csv(path: Path, elastic_strain_max: float) -> Tuple[List[float], List[float]]:
    """Load CSV with headers strain, stress; return points with strain <= elastic_strain_max."""
```

## Function Design

**Size:**
- Most utility functions stay under 30 lines (`estimate_E_ols_origin`, `compute_rmse`)
- Main orchestration functions may be 100+ lines (`run_calibration`, `run_certificate`)
- Helper prefixed with underscore when function is internal to module

**Parameters:**
- Use explicit keyword arguments in function signatures
- Avoid positional-only; use named parameters for clarity
- Optional parameters use default values: `noise_scale: float = None`, `canary_mode: bool = False`
- Type hints on all parameters and return type: `def run_calibration(seed: int, E_true: float) -> Dict[str, Any]`

**Return Values:**
- Always return structured dictionaries with consistent keys: `{"mtr_phase": "MTR-1", "inputs": {...}, "result": {...}}`
- Top-level dict includes: `mtr_phase`, `inputs`, `result`, `execution_trace`, `trace_root_hash`
- Keep return structure consistent across all 14 claims for semantic verification

**Examples:**
```python
def run_calibration(
    seed: int,
    E_true: float,
    n_points: int = 50,
    max_strain: float = 0.002,
    noise_scale: float = None,
    dataset_relpath: Optional[str] = None,
    elastic_strain_max: float = 0.002,
    uq_samples: Optional[int] = None,
    uq_seed: Optional[int] = None,
) -> Dict[str, Any]:
    """Run MTR-1 calibration. If dataset_relpath is set, load CSV; otherwise use synthetic data."""
```

## Module Design

**Exports:**
- Each claim module exports: `JOB_KIND` constant, `run_<operation>` function, sometimes `ALGORITHM_VERSION`
- Private functions and constants not exported (prefix with underscore)
- Modules import from sibling modules: `from backend.progress.data_integrity import fingerprint_file`

**Barrel Files:**
- Not used in this codebase; each module imports directly from implementation files
- `backend/__init__.py` and `backend/progress/__init__.py` are empty (only contain `"""..."""`)

**Module-level Constants:**
- Define at top of file after imports:
```python
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JOB_KIND = "mtr1_youngs_modulus_calibration"
ALGORITHM_VERSION = "v1"
METHOD = "ols_origin"
```

---

*Convention analysis: 2026-03-16*
