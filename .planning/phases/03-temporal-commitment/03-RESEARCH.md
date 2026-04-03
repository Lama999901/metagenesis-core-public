# Phase 3: Temporal Commitment - Research

**Researched:** 2026-03-18
**Domain:** NIST Randomness Beacon 2.0 integration, temporal proof cryptography, offline verification
**Confidence:** HIGH

## Summary

Phase 3 adds Layer 5 (Temporal Commitment) to MetaGenesis Core's verification stack. The core mechanism is straightforward: at sign time, fetch the latest NIST Randomness Beacon 2.0 pulse, compute a pre-commitment hash of the bundle's root_hash, then bind both together with the beacon value via SHA-256. This creates a cryptographic proof of WHEN a bundle was signed that is independently verifiable offline.

The NIST Beacon 2.0 API is live and operational (confirmed via direct fetch on 2026-03-18). It emits 512-bit random values every 60 seconds at `https://beacon.nist.gov/beacon/2.0/chain/last/pulse/last`. The response is JSON with well-documented fields. All required cryptographic operations (SHA-256, string concatenation) are already available in Python stdlib. The HTTP fetch uses `urllib.request` -- no external dependencies needed.

The main implementation risk is network reliability (the beacon may be temporarily unreachable), which is fully mitigated by the decided graceful degradation pattern. The pre-commitment scheme (hash-then-bind) is a standard cryptographic pattern that requires careful ordering but no novel algorithms.

**Primary recommendation:** Implement as a new `mg_temporal.py` module with functions callable from both `mg_sign.py` (auto-create after signing) and standalone CLI. Keep temporal data in `temporal_commitment.json` separate from `bundle_signature.json` to enforce Layer 5 independence.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Primary source: NIST Randomness Beacon 2.0 API (`/pulse/last` endpoint)
- Fallback: local ISO timestamp when beacon unreachable
- Fetch latest pulse at sign time (one HTTP call via `urllib.request`)
- 5-second network timeout before falling back to local timestamp
- Capture three fields from beacon response: `outputValue` (512-bit random), `timeStamp`, and pulse URI
- stdlib-only: use `urllib.request` for HTTP, no external dependencies
- Separate `temporal_commitment.json` file in bundle directory (NOT in bundle_signature.json)
- Layer 5 is independent of Layer 4 -- separate files enforce this
- Version field: `"temporal-nist-v1"` following established pattern (hmac-sha256-v1, ed25519-v1)
- Cryptographic binding: `SHA-256(root_hash + beacon_value + timestamp)` -- simple concatenation hash
- Both `pre_commitment_hash` and `temporal_binding` stored in the file for full auditability
- Created automatically during `mg_sign.py sign` AND available as standalone `mg_sign.py temporal` subcommand
- Two-phase hash-then-bind pattern for pre-commitment (TEMP-06)
- `pre_commitment_hash = SHA-256(root_hash)` BEFORE fetching beacon
- `temporal_binding = SHA-256(pre_commitment_hash + beacon_value + timestamp)`
- When beacon unreachable: write `temporal_commitment.json` with local ISO timestamp, beacon fields null, `"beacon_status": "unavailable"`
- Default: warn to stderr and continue (exit 0); `--strict` flag: fail with exit 1
- Verification is fully offline -- NEVER makes network calls during verify
- Verification checks: (1) pre_commitment_hash = SHA-256(root_hash), (2) temporal_binding = SHA-256(pre_commitment_hash + beacon_value + timestamp)
- Independent of Layers 1-4

### Claude's Discretion
- Internal module structure (new file vs extending mg_sign.py)
- Exact JSON field names in temporal_commitment.json (beyond the decided fields)
- Error message wording for beacon failures
- How to structure the standalone `temporal` subcommand CLI arguments

### Deferred Ideas (OUT OF SCOPE)
- Cross-claim temporal chain (temporal DAG) -- TEMP-V2-01, deferred to v0.5.0
- RFC 3161 TSA as alternative temporal authority -- TEMP-V2-02, deferred to v0.5.0
- Temporal chain explorer CLI -- TEMP-V2-03, deferred to v0.5.0
- Online verification mode (--online flag to cross-check beacon pulse against NIST) -- future enhancement
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TEMP-01 | NIST Beacon pulse capture at bundle sign time via urllib.request | NIST Beacon 2.0 API confirmed operational; endpoint, response format, and field names documented |
| TEMP-02 | Cryptographic binding -- SHA-256(root_hash + beacon_value + beacon_timestamp) | Standard SHA-256 concatenation hash; hashlib already in use throughout codebase |
| TEMP-03 | Graceful degradation -- temporal layer returns "not available" when beacon unreachable | urllib.request timeout + try/except pattern; degraded JSON structure documented |
| TEMP-04 | Layer 5 independent verification -- checks temporal commitment without depending on Layers 1-4 | Separate temporal_commitment.json file; verify function takes only pack_dir and reads only that file + manifest root_hash |
| TEMP-05 | Offline verification of temporal data -- checks embedded structure, no network calls | Verification recalculates SHA-256 bindings from embedded data only; no imports of urllib in verify path |
| TEMP-06 | Pre-commitment hash scheme -- prove bundle existed before beacon pulse | Two-phase: SHA-256(root_hash) computed before beacon fetch, then SHA-256(pre_commitment + beacon_value + timestamp) after |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| hashlib (stdlib) | Python 3.11+ | SHA-256 for all hash operations | Already used throughout codebase |
| urllib.request (stdlib) | Python 3.11+ | HTTP GET to NIST Beacon API | Locked decision: stdlib-only, no requests/httpx |
| json (stdlib) | Python 3.11+ | Parse beacon JSON response, write temporal_commitment.json | Already used throughout codebase |
| datetime (stdlib) | Python 3.11+ | ISO timestamp for fallback mode | Standard UTC timestamp generation |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock (stdlib) | Python 3.11+ | Mock urllib.request in tests | All temporal tests must mock network calls |
| pathlib (stdlib) | Python 3.11+ | File path handling | Consistent with existing codebase pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| urllib.request | requests | Not allowed: stdlib-only constraint |
| Local timestamp fallback | No fallback (strict only) | Bad UX: signing would fail without network |

**Installation:**
```bash
# No installation needed -- all stdlib
```

## Architecture Patterns

### Recommended Module Structure

**Recommendation (Claude's Discretion):** Create a NEW `scripts/mg_temporal.py` module rather than extending `mg_sign.py`.

Rationale:
- Layer 5 is explicitly independent of Layer 4 -- separate modules enforce this at code level
- `mg_sign.py` is already 450 lines handling HMAC + Ed25519 dual-algorithm signing
- Temporal logic (beacon fetch, pre-commitment, binding) is a distinct concern
- `mg_sign.py` can import and call `mg_temporal.py` functions for auto-creation after signing
- Standalone `temporal` subcommand can be added to `mg_sign.py` CLI while logic lives in `mg_temporal.py`

```
scripts/
  mg_temporal.py       # NEW -- temporal commitment logic (Innovation #7)
  mg_sign.py           # MODIFIED -- import mg_temporal, call after sign, add temporal subcommand
  mg.py                # MODIFIED -- add Layer 5 check in verify flow (minimal)
```

### Pattern 1: Two-Phase Commit (Pre-commitment + Binding)
**What:** Compute pre_commitment_hash BEFORE fetching beacon, then bind with beacon value AFTER
**When to use:** Every temporal commitment creation
**Example:**
```python
import hashlib

def create_temporal_commitment(root_hash: str, beacon_timeout: int = 5) -> dict:
    # Phase 1: Pre-commitment (before knowing beacon value)
    pre_commitment_hash = hashlib.sha256(root_hash.encode("utf-8")).hexdigest()

    # Phase 2: Fetch beacon and bind
    beacon = _fetch_beacon_pulse(timeout=beacon_timeout)

    if beacon is not None:
        concat = pre_commitment_hash + beacon["outputValue"] + beacon["timeStamp"]
        temporal_binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()
        return {
            "version": "temporal-nist-v1",
            "root_hash": root_hash,
            "pre_commitment_hash": pre_commitment_hash,
            "beacon_output_value": beacon["outputValue"],
            "beacon_timestamp": beacon["timeStamp"],
            "beacon_pulse_uri": beacon["uri"],
            "beacon_status": "available",
            "temporal_binding": temporal_binding,
        }
    else:
        # Graceful degradation
        return {
            "version": "temporal-nist-v1",
            "root_hash": root_hash,
            "pre_commitment_hash": pre_commitment_hash,
            "beacon_output_value": None,
            "beacon_timestamp": None,
            "beacon_pulse_uri": None,
            "beacon_status": "unavailable",
            "local_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "temporal_binding": None,
        }
```

### Pattern 2: Offline Verification (No Network)
**What:** Verify temporal commitment using only embedded data
**When to use:** Every temporal verification call
**Example:**
```python
def verify_temporal_commitment(pack_dir: Path) -> tuple[bool, str]:
    """Verify Layer 5 temporal commitment. Fully offline."""
    tc_path = pack_dir / "temporal_commitment.json"
    if not tc_path.exists():
        return True, "Temporal: no temporal commitment present (Layer 5 skipped)"

    tc = json.loads(tc_path.read_text(encoding="utf-8"))

    # Get root_hash from manifest
    manifest = json.loads((pack_dir / "pack_manifest.json").read_text(encoding="utf-8"))
    root_hash = manifest["root_hash"]

    # Check 1: pre_commitment_hash matches root_hash
    expected_pre = hashlib.sha256(root_hash.encode("utf-8")).hexdigest()
    if tc["pre_commitment_hash"] != expected_pre:
        return False, "Temporal: pre_commitment_hash does not match root_hash"

    # Check 2: temporal_binding (only if beacon was available)
    if tc["beacon_status"] == "unavailable":
        return True, "Temporal: local timestamp only (no beacon proof)"

    concat = tc["pre_commitment_hash"] + tc["beacon_output_value"] + tc["beacon_timestamp"]
    expected_binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    if tc["temporal_binding"] != expected_binding:
        return False, "Temporal: temporal_binding hash mismatch"

    return True, "Temporal: VALID (beacon-backed)"
```

### Pattern 3: (ok, message) Return Tuple
**What:** All verification functions return `(bool, str)` tuple
**When to use:** Consistent with `verify_bundle_signature()` in mg_sign.py and `_verify_pack()` in mg.py
**Example:** See Pattern 2 above -- same convention.

### Anti-Patterns to Avoid
- **Making network calls during verification:** TEMP-05 explicitly forbids this. The verify function must NEVER import urllib or make HTTP requests.
- **Storing temporal data inside bundle_signature.json:** Layer 5 must be independent of Layer 4 at the file level.
- **Using the beacon's `localRandomValue` instead of `outputValue`:** The `outputValue` is the final hash of all inputs and is the canonical beacon value. `localRandomValue` is just one input to it.
- **Fetching beacon before computing pre-commitment:** The ordering is critical for the pre-commitment proof. `SHA-256(root_hash)` MUST be computed before the HTTP call to the beacon.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP timeout handling | Custom socket-level timeout | `urllib.request.urlopen(url, timeout=5)` | stdlib handles TCP + SSL timeout correctly |
| UTC timestamp | Manual timezone math | `datetime.datetime.now(datetime.timezone.utc).isoformat()` | Avoids timezone bugs |
| JSON response parsing | Manual string parsing | `json.loads(response.read().decode("utf-8"))` | Already the codebase pattern |
| Hash concatenation | Binary concatenation | String concatenation then encode to UTF-8 | Matches the decided `SHA-256(root_hash + beacon_value + timestamp)` pattern |

**Key insight:** Everything needed is already in Python stdlib. The complexity is in the ordering and flow control, not the primitives.

## Common Pitfalls

### Pitfall 1: Beacon Response Nesting
**What goes wrong:** The NIST Beacon 2.0 response wraps the pulse in a `"pulse"` object: `{"pulse": {...fields...}}`
**Why it happens:** Easy to assume flat JSON when reading docs
**How to avoid:** Always access `response_json["pulse"]["outputValue"]`, not `response_json["outputValue"]`
**Warning signs:** KeyError on `outputValue` during integration testing

### Pitfall 2: Beacon outputValue Length
**What goes wrong:** Assuming `outputValue` is 64 hex chars (256-bit) when it is actually 128 hex chars (512-bit)
**Why it happens:** SHA-256 outputs 64 hex chars, easy to confuse with beacon's 512-bit output
**How to avoid:** Do NOT validate outputValue length as 64 chars. The beacon provides a 512-bit (128 hex char) value.
**Warning signs:** Validation failures on real beacon data

### Pitfall 3: String Encoding for Hash Concatenation
**What goes wrong:** Mixing bytes and strings in the concatenation before SHA-256
**Why it happens:** Some values are hex strings, some are ISO timestamps
**How to avoid:** Concatenate as plain strings first, then `.encode("utf-8")` once for SHA-256 input. The decision says "simple concatenation hash" -- keep it as string concatenation.
**Warning signs:** Different hashes on different platforms

### Pitfall 4: Beacon Downtime During Tests
**What goes wrong:** Tests fail intermittently because they hit the real NIST Beacon
**Why it happens:** Not mocking network calls in test suite
**How to avoid:** ALL tests must mock `urllib.request.urlopen`. Create a fixture that returns a realistic beacon pulse JSON. Never hit the real beacon in CI.
**Warning signs:** Flaky tests, CI failures on network-isolated runners

### Pitfall 5: Forgetting --strict Flag in Argparse
**What goes wrong:** The `--strict` flag for enforcing beacon availability is not wired up
**Why it happens:** Easy to implement the default path and forget the strict exit-1 path
**How to avoid:** Test both paths explicitly: default (warn + continue) and strict (fail)
**Warning signs:** Missing test coverage for strict mode

### Pitfall 6: Temporal Verification Reading root_hash from Wrong Source
**What goes wrong:** Verification reads root_hash from temporal_commitment.json instead of pack_manifest.json
**Why it happens:** root_hash is stored in both files
**How to avoid:** ALWAYS read root_hash from `pack_manifest.json` (the authoritative source), then compare against what temporal_commitment.json claims. This catches the case where an attacker modifies the temporal file's root_hash field.
**Warning signs:** Temporal verification passes when it should fail on tampered bundles

## Code Examples

### NIST Beacon Fetch with Timeout
```python
import json
import urllib.request
import urllib.error

BEACON_URL = "https://beacon.nist.gov/beacon/2.0/chain/last/pulse/last"

def _fetch_beacon_pulse(timeout: int = 5) -> dict | None:
    """Fetch latest NIST Beacon 2.0 pulse. Returns None on any failure."""
    try:
        req = urllib.request.Request(BEACON_URL, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pulse = data["pulse"]
            return {
                "outputValue": pulse["outputValue"],
                "timeStamp": pulse["timeStamp"],
                "uri": pulse["uri"],
            }
    except (urllib.error.URLError, OSError, KeyError, json.JSONDecodeError):
        return None
```
Source: Verified against live NIST Beacon 2.0 API response (2026-03-18)

### temporal_commitment.json Schema (Full Beacon)
```json
{
  "version": "temporal-nist-v1",
  "root_hash": "abc123...64chars",
  "pre_commitment_hash": "def456...64chars",
  "beacon_output_value": "789abc...128chars",
  "beacon_timestamp": "2026-03-18T01:21:00.000Z",
  "beacon_pulse_uri": "https://beacon.nist.gov/beacon/2.0/chain/2/pulse/1704488",
  "beacon_status": "available",
  "temporal_binding": "fed987...64chars"
}
```

### temporal_commitment.json Schema (Degraded / No Beacon)
```json
{
  "version": "temporal-nist-v1",
  "root_hash": "abc123...64chars",
  "pre_commitment_hash": "def456...64chars",
  "beacon_output_value": null,
  "beacon_timestamp": null,
  "beacon_pulse_uri": null,
  "beacon_status": "unavailable",
  "local_timestamp": "2026-03-18T01:22:00+00:00",
  "temporal_binding": null
}
```

### Test Fixture: Mock Beacon Response
```python
MOCK_BEACON_PULSE = {
    "pulse": {
        "outputValue": "a" * 128,  # 512-bit hex
        "timeStamp": "2026-03-18T00:00:00.000Z",
        "uri": "https://beacon.nist.gov/beacon/2.0/chain/2/pulse/1234567",
    }
}

@pytest.fixture
def mock_beacon(monkeypatch):
    """Mock NIST Beacon to return predictable pulse."""
    import io
    def fake_urlopen(req, timeout=None):
        body = json.dumps(MOCK_BEACON_PULSE).encode("utf-8")
        resp = io.BytesIO(body)
        resp.read = resp.read  # already has read()
        return resp
    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NIST Beacon 1.0 (XML) | NIST Beacon 2.0 (JSON) | ~2019 | JSON response, chained pulses, 60-second interval |
| No pre-commitment | Hash-then-bind pre-commitment | Standard practice | Proves data existed before beacon value known |
| Trusted timestamps (RFC 3161) | NIST Beacon (no TSA needed) | Beacon is simpler | No certificate authority, no fees, publicly auditable |

**Deprecated/outdated:**
- NIST Beacon 1.0 API: Still accessible but superseded by 2.0. Use 2.0 endpoints only.
- `beacon.nist.gov/rest/record/last` (v1.0 endpoint): Deprecated. Use `beacon.nist.gov/beacon/2.0/chain/last/pulse/last`.

## Open Questions

1. **Beacon pulse field `outputValue` exact hex length**
   - What we know: Documentation says 512-bit, confirmed 128 hex chars in live response
   - What's unclear: Whether the beacon ever returns shorter values (e.g., on error pulses)
   - Recommendation: Accept any non-empty hex string rather than enforcing exact length

2. **Integration with mg.py verify flow**
   - What we know: `_verify_pack()` handles Layers 1-3. Layer 4 is in mg_sign.py.
   - What's unclear: Whether temporal check should be called from mg.py's verify command or only from mg_sign.py's verify command
   - Recommendation: Add to mg_sign.py verify (Layer 4+5 together), and optionally to mg.py as a lightweight check. Minimal changes to mg.py per sealed-file caution.

3. **Behavior when temporal_commitment.json is absent**
   - What we know: Bundles signed before Phase 3 won't have this file
   - What's unclear: Should absence be PASS (backward compat) or INFO message?
   - Recommendation: PASS with advisory note ("no temporal commitment present"). This maintains backward compatibility with existing bundles.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.1 |
| Config file | tests/ directory with conftest |
| Quick run command | `python -m pytest tests/steward/test_temporal.py -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEMP-01 | Beacon pulse fetch returns outputValue, timeStamp, uri | unit | `python -m pytest tests/steward/test_temporal.py::test_beacon_fetch -x` | No -- Wave 0 |
| TEMP-02 | Cryptographic binding SHA-256(root_hash + beacon + ts) matches | unit | `python -m pytest tests/steward/test_temporal.py::test_temporal_binding -x` | No -- Wave 0 |
| TEMP-03 | Degraded mode writes null beacon fields + local timestamp | unit | `python -m pytest tests/steward/test_temporal.py::test_graceful_degradation -x` | No -- Wave 0 |
| TEMP-04 | Verify temporal works without Layers 1-4 passing | unit | `python -m pytest tests/steward/test_temporal.py::test_layer5_independence -x` | No -- Wave 0 |
| TEMP-05 | Verify never makes network calls | unit | `python -m pytest tests/steward/test_temporal.py::test_offline_verification -x` | No -- Wave 0 |
| TEMP-06 | Pre-commitment hash computed before beacon fetch | unit | `python -m pytest tests/steward/test_temporal.py::test_precommitment_scheme -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/steward/test_temporal.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/steward/test_temporal.py` -- covers TEMP-01 through TEMP-06
- [ ] Mock beacon fixture (in test file or conftest) -- shared across all temporal tests
- [ ] No framework install needed -- pytest already present

## Sources

### Primary (HIGH confidence)
- NIST Beacon 2.0 live API response -- fetched 2026-03-18, confirmed JSON structure with `pulse` wrapper object, fields `outputValue` (128 hex), `timeStamp` (ISO 8601), `uri`
- `scripts/mg_sign.py` -- existing signing module, read in full, confirmed integration points
- `scripts/mg.py` -- existing verifier CLI, read first 100 lines, confirmed `_verify_pack()` pattern
- `tests/steward/test_signing_upgrade.py` -- existing test patterns, confirmed `_make_bundle()` helper and `(ok, message)` assertions

### Secondary (MEDIUM confidence)
- NIST Beacon 2.0 official project page: https://csrc.nist.gov/projects/interoperable-randomness-beacons/beacon-20
- NIST Beacon API endpoints verified via live fetch and documentation cross-reference

### Tertiary (LOW confidence)
- Beacon uptime/reliability -- no SLA documented by NIST. The graceful degradation pattern fully mitigates this concern.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all stdlib, no version concerns, already used in codebase
- Architecture: HIGH -- follows established patterns (separate module, `(ok, msg)` returns, JSON artifacts with version field)
- Pitfalls: HIGH -- verified beacon response format against live API, confirmed field nesting and value lengths
- NIST Beacon availability: MEDIUM -- API is live and responding, but no formal SLA exists (mitigated by graceful degradation)

**Research date:** 2026-03-18
**Valid until:** 2026-04-18 (stable domain -- NIST Beacon 2.0 has been operational since ~2019)
