# Stack Research: Test Coverage Hardening (v0.5.0)

**Domain:** Adversarial test design, encoding attack testing, governance drift detection
**Researched:** 2026-03-17
**Confidence:** HIGH (stdlib-only constraint eliminates library choices; patterns derived from existing codebase)

## Executive Decision

**No new dependencies.** The entire v0.5.0 test coverage hardening uses pytest 8.4.1, Python 3.11 stdlib, and the existing project patterns. This document describes *pytest patterns and techniques*, not new packages.

## Recommended Stack

### Core Technologies (Unchanged)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| pytest | 8.4.1 (pinned) | Test framework | Already in use. `parametrize`, `tmp_path`, class-based grouping cover all needs. |
| Python stdlib | 3.11+ | Encoding attack generation, YAML/MD parsing, JSON manipulation | `codecs`, `re`, `json`, `os`, `pathlib` -- all needed for test payloads are stdlib. |
| hashlib (stdlib) | ships with 3.11 | SHA-256 hash chain recomputation in attack harnesses | Already used in test_cert05 and test_cert_5layer_independence for building attack bundles. |
| unittest.mock | ships with 3.11 | Mocking NIST Beacon in temporal attack tests | Already used in test_cert_5layer_independence.py (`from unittest.mock import patch`). |

### No New Dependencies Required

The project constraint is **stdlib only** (CLAUDE.md: "No new dependencies, even for test utilities"). Every technique below uses Python builtins.

## Pytest Patterns for v0.5.0 Test Gaps

### Pattern 1: `pytest.mark.parametrize` for Attack Matrices (CERT-11, P2)

The coordinated attack test (CERT-11) needs to test N attack vectors across M layers. Use stacked parametrize decorators to create an attack matrix without code duplication.

```python
import pytest

# Each attack vector: (description, layers_bypassed, layer_that_catches, setup_fn)
COORDINATED_ATTACKS = [
    pytest.param(
        "rebuild_l1_attack_l2",
        {"l1_bypass": True, "l2_attack": "strip_snapshot"},
        2,
        id="bypass-L1-fail-L2",
    ),
    pytest.param(
        "rebuild_l1l2_attack_l3",
        {"l1_bypass": True, "l2_bypass": True, "l3_attack": "forge_trace"},
        3,
        id="bypass-L1L2-fail-L3",
    ),
    pytest.param(
        "stolen_key_tamper_evidence",
        {"l4_bypass": True, "l1_attack": "modify_evidence"},
        1,
        id="stolen-key-L1-catches",
    ),
]

class TestCERT11CoordinatedAttack:
    @pytest.mark.parametrize("name,attack_config,caught_by_layer", COORDINATED_ATTACKS)
    def test_coordinated_attack_caught(self, tmp_path, name, attack_config, caught_by_layer):
        bundle = _make_full_5layer_bundle(tmp_path)
        _apply_attack(bundle, attack_config)
        result = _verify_all_layers(bundle)
        assert result.first_failure_layer == caught_by_layer
```

**Why this pattern:** The existing CERT-05 uses one method per attack (5 methods). CERT-11 has combinatorial attack scenarios -- parametrize scales better and produces clear test IDs in output (`PASSED test_cert11[bypass-L1-fail-L2]`).

**Confidence:** HIGH -- parametrize is heavily used in the existing test suite (seen in test_cert09, test_cert10).

### Pattern 2: `pytest.mark.parametrize` for Encoding Attacks (CERT-12, P5)

Encoding attacks require many small payloads. Define them as a data table, not as individual test methods.

```python
# Encoding attack payloads -- each is a (description, payload_bytes, expected_behavior)
ENCODING_ATTACKS = [
    pytest.param(
        b'\xef\xbb\xbf{"mtr_phase": "MTR-1"}',
        "bom_prefix",
        id="utf8-bom-prefix",
    ),
    pytest.param(
        b'{"mtr_phase": "MTR-1", "value": "\x00hidden"}',
        "null_byte_in_value",
        id="null-byte-in-json-value",
    ),
    pytest.param(
        b'{"mtr_phase": "MTR-1", "tra',  # truncated
        "truncated_json",
        id="truncated-json-mid-field",
    ),
    pytest.param(
        _make_homoglyph_payload("MTR-1"),  # Cyrillic 'a' in claim ID
        "homoglyph_claim_id",
        id="cyrillic-homoglyph-in-claim-id",
    ),
]

class TestCERT12EncodingAttacks:
    @pytest.mark.parametrize("payload,attack_type", ENCODING_ATTACKS)
    def test_encoding_attack_rejected(self, tmp_path, payload, attack_type):
        """Every encoding attack must be caught by at least one layer."""
        pack_dir = _build_pack_with_raw_payload(tmp_path, payload)
        ok, msg, _ = _verify_semantic(pack_dir, pack_dir / "evidence_index.json")
        assert not ok, f"Encoding attack '{attack_type}' was NOT detected"
```

**Why this pattern:** Encoding attacks are data-driven (many payloads, same assertion). The `id=` parameter gives readable test names. Adding new attacks is one line, not a new method.

### Pattern 3: Shared Bundle Builders via Module-Level Helpers (Not Fixtures)

The existing codebase uses module-level helper functions (e.g., `_make_minimal_pack` in test_cert05, `_make_full_5layer_bundle` in test_cert_5layer_independence). **Continue this pattern -- do NOT introduce conftest.py fixtures.**

Rationale:
- No conftest.py exists anywhere in the test tree currently
- Each test file is self-contained (imports helpers from the same file or from production code)
- Bundle builder helpers are specific to each CERT file's attack surface
- Adding conftest.py would change the test discovery behavior for all 391 existing tests

```python
# CORRECT: Module-level helper (existing pattern)
def _make_attack_bundle(tmp_path, attack_vector):
    """Build a bundle with a specific attack applied."""
    bundle = tmp_path / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    # ... build and tamper ...
    return bundle

# WRONG: Don't create conftest.py fixtures for this
# @pytest.fixture
# def attack_bundle(request, tmp_path):  # NO
```

**Confidence:** HIGH -- directly observed in 6+ existing test files.

### Pattern 4: Class-Based Test Grouping with Shared State (Step Chain Tests, P1)

The existing `test_step_chain_all_claims.py` uses one class per claim with a `_run_*` method. Extend this exact pattern for the 7 missing claims.

```python
class TestStepChainMLBENCH01:
    def _run_mlbench01(self):
        from backend.progress.mlbench1_accuracy_certificate import run_certificate
        return run_certificate(seed=42, claimed_accuracy=0.90, n_samples=100)

    def test_mlbench01_trace_present(self):
        result = self._run_mlbench01()
        _assert_trace_valid(result, "ML_BENCH-01")

    def test_mlbench01_trace_four_steps(self):
        result = self._run_mlbench01()
        assert len(result["execution_trace"]) == 4

    def test_mlbench01_trace_deterministic(self):
        r1 = self._run_mlbench01()
        r2 = self._run_mlbench01()
        assert r1["trace_root_hash"] == r2["trace_root_hash"]

    def test_mlbench01_trace_changes_with_input(self):
        from backend.progress.mlbench1_accuracy_certificate import run_certificate
        r1 = run_certificate(seed=42, claimed_accuracy=0.90, n_samples=100)
        r2 = run_certificate(seed=99, claimed_accuracy=0.90, n_samples=100)
        assert r1["trace_root_hash"] != r2["trace_root_hash"]
```

**Confidence:** HIGH -- exact template exists for 7 claims already in the file.

### Pattern 5: Cross-Reference Validation via Stdlib Parsing (P10 Governance)

For YAML/MD drift detection, use stdlib `re` for markdown table parsing and a minimal YAML parser for the simple known_faults.yaml structure.

**YAML parsing without PyYAML:** The `known_faults.yaml` has a flat structure. Parse it with `re` regex extraction, not a YAML library.

```python
import re

def _extract_claim_ids_from_yaml(yaml_path):
    """Extract affected_claims lists from known_faults.yaml using regex.

    This avoids a PyYAML dependency. Works because the YAML structure
    is simple and stable (flat list of fault entries with string arrays).
    """
    text = yaml_path.read_text(encoding="utf-8")
    # Match: affected_claims: ["CLAIM-1", "CLAIM-2"]
    matches = re.findall(r'affected_claims:\s*\[(.*?)\]', text, re.DOTALL)
    claims = set()
    for match in matches:
        for claim in re.findall(r'"([^"]+)"', match):
            claims.add(claim)
    return claims

def _extract_claims_from_claim_index_md(md_path):
    """Extract claim IDs from scientific_claim_index.md markdown table."""
    text = md_path.read_text(encoding="utf-8")
    # Match claim IDs in table rows: | CLAIM-ID | ... |
    claims = set()
    for line in text.splitlines():
        if "|" in line and not line.strip().startswith("|--"):
            cells = [c.strip() for c in line.split("|")]
            for cell in cells:
                if re.match(r'^[A-Z][A-Z_-]+-\d+$', cell):
                    claims.add(cell)
    return claims

def _extract_claim_ids_from_runner():
    """Extract JOB_KIND -> claim_id mappings from runner.py dispatch."""
    from backend.progress import runner
    import inspect
    source = inspect.getsource(runner.ProgressRunner._execute_job_logic)
    # Match: JOB_KIND as XXX_KIND patterns or direct string comparisons
    kinds = re.findall(r'JOB_KIND as (\w+)', source)
    return kinds
```

**Why regex over PyYAML:**
- PyYAML is NOT in requirements.txt
- The YAML files are simple (no anchors, no complex types)
- Regex extraction is deterministic and has zero dependency risk
- The test only needs to extract claim ID strings, not parse full YAML semantics

**Confidence:** HIGH -- the YAML/MD structure was directly inspected (known_faults.yaml is 48 lines, scientific_claim_index.md uses standard markdown tables).

### Pattern 6: Raw Bytes Writing for Encoding Attacks (P5)

For encoding attacks, write raw bytes (not strings) to evidence files. This is how to craft BOM, null byte, and truncated JSON attacks.

```python
def _build_pack_with_raw_evidence(tmp_path, raw_bytes, claim_id="ML_BENCH-01"):
    """Build a pack where run_artifact.json contains raw bytes (not valid JSON)."""
    pack_dir = tmp_path / "pack"
    ev_dir = pack_dir / "evidence" / claim_id / "normal"
    ev_dir.mkdir(parents=True, exist_ok=True)

    # Write RAW BYTES -- this is the attack surface
    (ev_dir / "run_artifact.json").write_bytes(raw_bytes)

    # Ledger must still be present for semantic check to reach the evidence
    (ev_dir / "ledger_snapshot.jsonl").write_text(
        '{"trace_id":"t","action":"job_completed","actor":"scheduler_v1","meta":{"canary_mode":false}}\n',
        encoding="utf-8"
    )

    # Evidence index points to the tampered file
    evidence_index = {
        claim_id: {
            "job_kind": "mlbench1_accuracy_certificate",
            "normal": {
                "run_relpath": f"evidence/{claim_id}/normal/run_artifact.json",
                "ledger_relpath": f"evidence/{claim_id}/normal/ledger_snapshot.jsonl",
            }
        }
    }
    (pack_dir / "evidence_index.json").write_text(
        json.dumps(evidence_index), encoding="utf-8"
    )
    return pack_dir
```

**Key technique:** `Path.write_bytes()` vs `Path.write_text()`. All encoding attacks MUST use `write_bytes()` to avoid Python's automatic encoding normalization.

### Pattern 7: Unicode Homoglyph Generation (Stdlib Only)

Generate homoglyph attacks using Python's built-in Unicode support. No `confusable-homoglyphs` package needed.

```python
# Common homoglyph pairs for claim ID spoofing
HOMOGLYPHS = {
    'a': '\u0430',  # Cyrillic 'a' (looks identical to Latin 'a')
    'e': '\u0435',  # Cyrillic 'e'
    'o': '\u043e',  # Cyrillic 'o'
    'p': '\u0440',  # Cyrillic 'p'
    'c': '\u0441',  # Cyrillic 'c'
    'M': '\u041c',  # Cyrillic 'M'
    'T': '\u0422',  # Cyrillic 'T'
    'R': '\u0420',  # Cyrillic 'R'
    '-': '\u2010',  # Hyphen (different from ASCII hyphen-minus)
    '1': '\u0661',  # Arabic-Indic digit one
}

def _make_homoglyph_claim_id(real_id, positions=None):
    """Replace characters in claim ID with visually identical homoglyphs.

    Example: "MTR-1" -> "\\u041cTR-1" (Cyrillic M instead of Latin M)
    These look identical in most fonts but are different bytes.
    """
    chars = list(real_id)
    if positions is None:
        positions = [0]  # Replace first character by default
    for pos in positions:
        if pos < len(chars) and chars[pos] in HOMOGLYPHS:
            chars[pos] = HOMOGLYPHS[chars[pos]]
    return ''.join(chars)
```

**Why this matters:** An attacker could submit evidence for "MTR-1" (with Cyrillic M) that looks identical to the real "MTR-1" but has a different claim ID hash. The semantic layer checks `mtr_phase` string equality -- homoglyphs would bypass visual inspection but should fail programmatic matching.

**Confidence:** HIGH -- Python's Unicode support is stdlib. The homoglyph characters are well-known (PEP 672 documents this concern).

## Supporting Libraries (No Changes)

| Library | Version | Purpose | v0.5.0 Usage |
|---------|---------|---------|--------------|
| pytest | 8.4.1 | Test framework | `parametrize`, `tmp_path`, class grouping, `pytest.param` with `id=` |
| numpy | >=1.21.0 | Claim computation | Not used for test harness -- only invoked indirectly via claim `run_*` functions |
| scipy | >=1.7.0 | Optimization | Not used for test harness |
| pandas | >=1.3.0 | Data manipulation | Not used for test harness |

## Installation

```bash
# No new packages. Zero dependency changes for v0.5.0.
pip install -r requirements.txt  # Unchanged from v0.4.0
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `re` regex for YAML/MD parsing (P10) | PyYAML (`pip install pyyaml`) | When YAML files become complex (anchors, custom types). Current known_faults.yaml is 48 lines with flat structure -- regex is sufficient and avoids a new dependency. |
| `pytest.mark.parametrize` for attack matrices | Hypothesis (property-based testing) | When attack surface is unbounded and you want fuzz testing. For v0.5.0, attacks are discrete and enumerable -- parametrize is clearer and more reproducible. |
| Module-level `_make_*` helpers | conftest.py shared fixtures | When >5 test files need the same builder. Currently each CERT file has its own builder tailored to its attack surface. Shared fixtures would couple test files. |
| `Path.write_bytes()` for encoding attacks | `codecs.open()` with explicit encoding | Never -- `write_bytes()` is more explicit for raw byte injection. `codecs.open()` adds unnecessary abstraction. |
| Inline homoglyph dict | `confusable-homoglyphs` package | Never for this project -- stdlib constraint. The 10 homoglyph pairs listed above cover all claim ID characters. |
| `re.findall` for claim extraction | `ast.literal_eval` for YAML arrays | Could use `ast.literal_eval` for `["CLAIM-1", "CLAIM-2"]` arrays. But regex is safer (no code execution risk) and handles the broader extraction task. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `conftest.py` fixtures | No conftest.py exists in test tree. Adding one changes pytest discovery for 391 tests. Each CERT file is self-contained by design. | Module-level `_make_*` helper functions (existing pattern). |
| `hypothesis` (property-based testing) | New dependency. Stdlib-only constraint. Also, adversarial attacks are finite and enumerable -- fuzz testing adds randomness where determinism is wanted. | `pytest.mark.parametrize` with explicit attack payloads. |
| `pytest-randomly` | Changes test execution order. Existing tests may have implicit ordering dependencies (alphabetical prefix convention). Risk of false failures. | Run tests in default order. Deterministic is a feature. |
| `pytest-xdist` | Parallel test execution. Not needed -- 450 tests run in <30 seconds. Parallelism adds complexity for zero practical benefit. | Sequential execution. |
| PyYAML | Not in requirements.txt. Adding it for one test file (P10 governance) is not justified. | `re` regex extraction for the simple YAML structures in this project. |
| `unittest.TestCase` subclassing | Mixes testing frameworks. Existing tests use bare pytest classes (no TestCase inheritance). `TestCase.assertEqual` is less readable than bare `assert`. | Bare `assert` with pytest introspection. |
| `subprocess` calls for layer verification | Slower, fragile, environment-dependent. Existing pattern imports `_verify_semantic` directly. | Direct function imports from `scripts/mg.py` (existing pattern in CERT-02, CERT-05). |

## Specific Pytest Features to Use

### `pytest.param` with `id=` for Readable Attack Names

```python
@pytest.mark.parametrize("attack", [
    pytest.param({"l1": "rebuild", "l2": "strip"}, id="rebuild-L1-strip-L2"),
    pytest.param({"l1": "rebuild", "l3": "forge"}, id="rebuild-L1-forge-L3"),
])
```

Output: `PASSED test_cert11[rebuild-L1-strip-L2]` -- immediately readable in CI logs.

### `pytest.raises` for Error Path Tests (P7)

```python
def test_unknown_job_kind_raises():
    runner = ProgressRunner(job_store, ledger_store)
    job = runner.create_job(payload={"kind": "nonexistent_job_kind"})
    with pytest.raises(ValueError, match="Unknown job kind"):
        runner.run_job(job.job_id)
```

### `tmp_path` for Isolated Bundle Manipulation

Already used in CERT-05, CERT-07, 5-layer independence. Each test gets a fresh temporary directory. No cleanup needed.

### Class-Based Grouping for Related Tests

Existing pattern: `TestAdversarialGauntlet`, `TestStepChainMTR1`, `TestCrossClaimChain`. Continue for:
- `TestCERT11CoordinatedAttack` (P2)
- `TestCERT12EncodingAttacks` (P5)
- `TestStepChainMLBENCH01` through `TestStepChainDTCALIB01` (P1)
- `TestGovernanceDrift` (P10)

## File Layout for New Tests

| Priority | File | Pattern | Tests (est.) |
|----------|------|---------|-------------|
| P1 | `tests/steward/test_step_chain_all_claims.py` (extend) | Class-per-claim, 4 tests each | +28 |
| P2 | `tests/steward/test_cert11_coordinated_attack.py` (new) | Parametrized attack matrix | ~8 |
| P3+P8 | `tests/steward/test_cross_claim_chain.py` (extend) | Method-per-scenario | +5 |
| P4 | `tests/steward/test_cert03_step_chain_verify.py` (extend) | Individual methods | +4 |
| P5 | `tests/steward/test_cert12_encoding_attacks.py` (new) | Parametrized payloads | ~10 |
| P6 | `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` (extend) | Individual methods | +6 |
| P7 | `tests/steward/test_runner_error_paths.py` (new) | `pytest.raises` | ~5 |
| P9 | `tests/steward/test_cert05_adversarial_gauntlet.py` (extend) | Add Attack 6 | +1 |
| P10 | `tests/steward/test_stew08_documentation_drift.py` (new) | Cross-reference assertions | ~5 |

**Estimated total: +72 tests (391 -> 463)**

## Version Compatibility

| Component | Compatible With | Notes |
|-----------|-----------------|-------|
| pytest 8.4.1 | `pytest.param`, `pytest.mark.parametrize`, `tmp_path` | All features used are stable since pytest 6.x. No version bump needed. |
| Python 3.11 `re` module | YAML/MD regex parsing | Full regex support. No third-party regex engine needed. |
| Python 3.11 Unicode | Homoglyph generation | All Cyrillic/Arabic codepoints available. `str.encode('utf-8')` handles correctly. |
| Python 3.11 `pathlib` | `write_bytes()` for encoding attacks | Available since Python 3.6. |
| Existing 391 tests | New test files | New files are additive. No modifications to existing test assertions. Extensions to existing files add methods, never modify existing methods. |

## Sources

- [Pytest parametrize documentation](https://docs.pytest.org/en/stable/example/parametrize.html) -- `pytest.param`, `id=`, stacked decorators (HIGH confidence)
- [Pytest how-to parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) -- indirect parametrize, marks (HIGH confidence)
- [PEP 672 - Unicode Security Considerations for Python](https://peps.python.org/pep-0672/) -- homoglyph attack vectors, Cyrillic confusables (HIGH confidence)
- [Python Unicode HOWTO](https://docs.python.org/3/howto/unicode.html) -- BOM handling, encoding (HIGH confidence)
- Existing codebase: `test_cert05_adversarial_gauntlet.py`, `test_step_chain_all_claims.py`, `test_cert_5layer_independence.py`, `test_cross_claim_chain.py` -- patterns directly observed (HIGH confidence)
- Existing codebase: `known_faults.yaml` (48 lines), `runner.py` (419 lines) -- structure directly inspected (HIGH confidence)

---
*Stack research for: MetaGenesis Core v0.5.0 test coverage hardening*
*Researched: 2026-03-17*
