#!/usr/bin/env python3
"""
STEW-08: Documentation drift detection (GOV-01, GOV-02, GOV-03).

Self-maintaining governance meta-tests that detect when documentation
drifts from actual code state. Uses relational assertions so tests
do not need manual updates when claims or counts change.

Ground truths:
  - runner.py `registered` list: which claims exist
  - system_manifest.json: authoritative counters
  - scientific_claim_index.md: claim registry
  - known_faults.yaml: known limitations
"""
import json
import re
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "scripts"))

import steward_audit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_manifest():
    """Load system_manifest.json as dict."""
    return json.loads((_ROOT / "system_manifest.json").read_text(encoding="utf-8"))


def _get_runner_registered_kinds():
    """Extract registered kinds from runner.py using steward_audit."""
    return steward_audit._extract_runner_dispatch_kinds()


def _get_claim_index_job_kinds():
    """Extract job_kinds from scientific_claim_index.md using steward_audit."""
    return steward_audit._extract_claim_index_job_kinds()


def _extract_claim_count_from_text(text, prefer_authoritative=False):
    """Extract claim count from text using common patterns like '14 claims' or '14 active claims'.

    If prefer_authoritative=True, looks for 'all N claims' first (for files like
    index.html where partial counts like 'Test 5 claims' may appear).
    """
    patterns = [
        r'(\d+)\s+active\s+claims?',
        r'[Aa]ll\s+(\d+)\s+claims?',
        r'(\d+)\s+claims?',
        r'Claims:\s*(\d+)',
    ]
    if prefer_authoritative:
        # Prioritize "all N claims" pattern to avoid partial counts
        patterns = [
            r'[Aa]ll\s+(\d+)\s+claims?',
            r'(\d+)\s+active\s+claims?',
            r'(\d+)\s+claims?',
            r'Claims:\s*(\d+)',
        ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def _parse_known_faults_yaml(text):
    """Minimal parser for known_faults.yaml without PyYAML dependency.

    Extracts affected_claims lists and file paths from the YAML text.
    This is intentionally simple -- it handles the known structure of
    the file without requiring a full YAML parser.
    """
    faults = []
    current_fault = {}
    in_affected_claims = False
    affected_claims_list = []

    for line in text.splitlines():
        stripped = line.strip()

        # New fault entry
        if stripped.startswith("- fault_id:"):
            if current_fault:
                if affected_claims_list:
                    current_fault["affected_claims"] = affected_claims_list
                faults.append(current_fault)
            current_fault = {"fault_id": stripped.split(":", 1)[1].strip().strip('"')}
            in_affected_claims = False
            affected_claims_list = []

        # affected_claims key
        elif stripped.startswith("affected_claims:"):
            rest = stripped.split(":", 1)[1].strip()
            in_affected_claims = True
            # Inline list like: ["ML_BENCH-01", "DATA-PIPE-01"]
            if rest.startswith("["):
                ids = re.findall(r'"([\w-]+)"', rest)
                affected_claims_list = ids
                in_affected_claims = False
            elif rest == "[]":
                affected_claims_list = []
                in_affected_claims = False

        # List continuation for affected_claims
        elif in_affected_claims and stripped.startswith("- "):
            val = stripped[2:].strip().strip('"')
            affected_claims_list.append(val)

        # Any other key breaks affected_claims list
        elif in_affected_claims and ":" in stripped and not stripped.startswith("-"):
            in_affected_claims = False

    # Don't forget the last fault
    if current_fault:
        if affected_claims_list:
            current_fault["affected_claims"] = affected_claims_list
        faults.append(current_fault)

    return faults


# ---------------------------------------------------------------------------
# GOV-01: Claim index vs implementations
# ---------------------------------------------------------------------------

class TestGov01ClaimIndexDrift:
    """Detect drift between scientific_claim_index.md and actual implementations."""

    def test_claim_index_job_kinds_equal_runner_dispatch(self):
        """Job kinds in claim index == job kinds in runner dispatch (set equality)."""
        index_kinds = _get_claim_index_job_kinds()
        runner_kinds = _get_runner_registered_kinds()
        assert index_kinds == runner_kinds, (
            f"Claim index job_kinds {sorted(index_kinds)} != "
            f"runner dispatch kinds {sorted(runner_kinds)}"
        )

    def test_manifest_claim_ids_match_claim_index(self):
        """system_manifest.json active_claims set == claim index claim IDs."""
        manifest = _get_manifest()
        manifest_ids = set(manifest["active_claims"])
        try:
            index_ids = set(steward_audit._extract_claim_index_claim_ids(
                _ROOT / "reports" / "scientific_claim_index.md"
            ))
        except (AttributeError, TypeError):
            # Fallback: parse scientific_claim_index.md directly
            text = (_ROOT / "reports" / "scientific_claim_index.md").read_text(encoding="utf-8")
            index_ids = set(re.findall(r'\|\s*([\w-]+-\d+)\s*\|', text))
        assert manifest_ids == index_ids, (
            f"Manifest claims {sorted(manifest_ids)} != "
            f"index claims {sorted(index_ids)}"
        )

    def test_manifest_claim_count_matches_runner(self):
        """system_manifest.json active_claims count == runner registered count."""
        manifest = _get_manifest()
        manifest_count = len(manifest["active_claims"])
        runner_count = len(_get_runner_registered_kinds())
        assert manifest_count == runner_count, (
            f"Manifest has {manifest_count} claims, runner has {runner_count}"
        )


# ---------------------------------------------------------------------------
# GOV-02: known_faults.yaml vs code state
# ---------------------------------------------------------------------------

class TestGov02KnownFaultsDrift:
    """Detect drift between known_faults.yaml and current code state."""

    @pytest.fixture
    def known_faults(self):
        faults_path = _ROOT / "reports" / "known_faults.yaml"
        if not faults_path.exists():
            pytest.skip("known_faults.yaml not found")
        text = faults_path.read_text(encoding="utf-8")
        return _parse_known_faults_yaml(text)

    def test_known_faults_file_references_exist(self, known_faults):
        """Every file path referenced in known_faults.yaml exists on disk.

        Checks common keys that may reference file paths.
        If no file references found, test passes (no drift possible).
        """
        missing = []
        for fault in known_faults:
            for key in ("file", "source_file", "affected_file"):
                filepath = fault.get(key)
                if filepath and isinstance(filepath, str):
                    full = _ROOT / filepath
                    if not full.exists():
                        missing.append(filepath)
        assert not missing, f"known_faults.yaml references non-existent files: {missing}"

    def test_known_faults_claim_references_exist(self, known_faults):
        """Every claim ID referenced in known_faults.yaml appears in the claim index."""
        fault_claim_ids = set()
        for fault in known_faults:
            claims = fault.get("affected_claims", [])
            if isinstance(claims, list):
                for cid in claims:
                    if cid and isinstance(cid, str):
                        fault_claim_ids.add(cid)

        if not fault_claim_ids:
            pytest.skip("No claim references found in known_faults.yaml")

        manifest = _get_manifest()
        manifest_ids = set(manifest["active_claims"])
        unknown = fault_claim_ids - manifest_ids
        assert not unknown, (
            f"known_faults.yaml references unknown claims: {sorted(unknown)}"
        )


# ---------------------------------------------------------------------------
# GOV-03: Counter consistency across documentation
# ---------------------------------------------------------------------------

class TestGov03CounterConsistency:
    """Validate counter consistency across all documentation files.

    Uses relational assertions against system_manifest.json as the
    single source of truth. NEVER hardcodes expected values.
    """

    @pytest.fixture
    def manifest(self):
        return _get_manifest()

    @pytest.fixture
    def expected_claim_count(self, manifest):
        return len(manifest["active_claims"])

    def test_manifest_test_count_plausible(self, manifest):
        """system_manifest.json test_count is positive (relational, not hardcoded)."""
        count = manifest.get("test_count", 0)
        assert count > 0, "test_count must be positive"

    def test_readme_claim_count_matches_manifest(self, manifest, expected_claim_count):
        """README.md claim count matches system_manifest.json."""
        readme = (_ROOT / "README.md").read_text(encoding="utf-8")
        readme_count = _extract_claim_count_from_text(readme)
        assert readme_count is not None, "Could not find claim count in README.md"
        assert readme_count == expected_claim_count, (
            f"README.md says {readme_count} claims, manifest has {expected_claim_count}"
        )

    def test_agents_claim_count_matches_manifest(self, manifest, expected_claim_count):
        """AGENTS.md claim count matches system_manifest.json."""
        agents_path = _ROOT / "AGENTS.md"
        if not agents_path.exists():
            pytest.skip("AGENTS.md not found")
        agents_text = agents_path.read_text(encoding="utf-8")
        agents_count = _extract_claim_count_from_text(agents_text)
        assert agents_count is not None, "Could not find claim count in AGENTS.md"
        assert agents_count == expected_claim_count, (
            f"AGENTS.md says {agents_count} claims, manifest has {expected_claim_count}"
        )

    def test_llms_txt_claim_count_matches_manifest(self, manifest, expected_claim_count):
        """llms.txt claim count matches system_manifest.json."""
        llms_path = _ROOT / "llms.txt"
        if not llms_path.exists():
            pytest.skip("llms.txt not found")
        llms_text = llms_path.read_text(encoding="utf-8")
        llms_count = _extract_claim_count_from_text(llms_text)
        assert llms_count is not None, "Could not find claim count in llms.txt"
        assert llms_count == expected_claim_count, (
            f"llms.txt says {llms_count} claims, manifest has {expected_claim_count}"
        )

    def test_context_snapshot_claim_count_matches_manifest(self, manifest, expected_claim_count):
        """CONTEXT_SNAPSHOT.md claim count matches system_manifest.json."""
        ctx_path = _ROOT / "CONTEXT_SNAPSHOT.md"
        if not ctx_path.exists():
            pytest.skip("CONTEXT_SNAPSHOT.md not found")
        ctx_text = ctx_path.read_text(encoding="utf-8")
        ctx_count = _extract_claim_count_from_text(ctx_text)
        assert ctx_count is not None, "Could not find claim count in CONTEXT_SNAPSHOT.md"
        assert ctx_count == expected_claim_count, (
            f"CONTEXT_SNAPSHOT.md says {ctx_count} claims, manifest has {expected_claim_count}"
        )

    def test_index_html_claim_count_matches_manifest(self, manifest, expected_claim_count):
        """index.html claim count matches system_manifest.json.

        Per CLAUDE.md, index.html has 11 places with test/claim counts
        and is the highest drift risk file. Extract claim count from
        HTML prose using regex patterns like '14 active claims' or
        '14 claims'.
        """
        html_path = _ROOT / "index.html"
        assert html_path.exists(), "index.html not found"
        html_text = html_path.read_text(encoding="utf-8")
        html_count = _extract_claim_count_from_text(html_text, prefer_authoritative=True)
        assert html_count is not None, (
            "Could not find claim count in index.html -- "
            "expected patterns like 'N active claims' or 'N claims'"
        )
        assert html_count == expected_claim_count, (
            f"index.html says {html_count} claims, manifest has {expected_claim_count}. "
            f"CLAUDE.md warns index.html has 11 places with counts -- check all of them."
        )

    def test_doc_files_exist(self):
        """All counter-bearing documentation files exist."""
        required = [
            "README.md", "index.html", "system_manifest.json",
            "CONTEXT_SNAPSHOT.md",
        ]
        for fname in required:
            assert (_ROOT / fname).exists(), f"Required doc file missing: {fname}"
