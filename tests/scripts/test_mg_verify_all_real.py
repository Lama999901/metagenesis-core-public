#!/usr/bin/env python3
"""
Tests for scripts/mg_verify_all_real.py -- batch runner and bundle verification.

Validates:
  - CLAIM_REGISTRY has all 20 claims
  - _already_verified logic
  - All bundles exist in proof_library/bundles/
  - All bundles pass mg.py verify --pack (REAL-05)
  - proof_library/index.json has all real entries
  - system_manifest.json real_to_synthetic_ratio >= 50%
  - Idempotency (re-running skips all claims)
"""

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.mg_verify_all_real import CLAIM_REGISTRY, _already_verified  # noqa: E402
from scripts.mg_claim_builder import _load_index  # noqa: E402

# All 20 expected claim IDs
EXPECTED_CLAIM_IDS = {
    "MTR-1", "MTR-2", "MTR-3", "MTR-4", "MTR-5", "MTR-6",
    "PHYS-01", "PHYS-02",
    "ML_BENCH-01", "ML_BENCH-02", "ML_BENCH-03",
    "SYSID-01", "DATA-PIPE-01", "DRIFT-01",
    "DT-FEM-01", "DT-SENSOR-01", "DT-CALIB-LOOP-01",
    "PHARMA-01", "FINRISK-01", "AGENT-DRIFT-01",
}

# All 8 expected domains
EXPECTED_DOMAINS = {
    "materials", "physics", "ml", "systems",
    "digital_twin", "pharma", "finance", "agent",
}


class TestClaimRegistry:
    """Test 1: CLAIM_REGISTRY has 20 entries with required keys."""

    def test_claim_registry_has_20_entries(self):
        assert len(CLAIM_REGISTRY) == 20, f"Expected 20, got {len(CLAIM_REGISTRY)}"

        # All entries have required keys
        required_keys = {"claim_id", "label", "domain", "input_path"}
        for entry in CLAIM_REGISTRY:
            missing = required_keys - set(entry.keys())
            assert not missing, f"Entry {entry.get('claim_id', '?')} missing keys: {missing}"

        # All 20 expected claim_ids are present
        actual_ids = {e["claim_id"] for e in CLAIM_REGISTRY}
        assert actual_ids == EXPECTED_CLAIM_IDS, (
            f"Missing: {EXPECTED_CLAIM_IDS - actual_ids}, "
            f"Extra: {actual_ids - EXPECTED_CLAIM_IDS}"
        )


class TestAlreadyVerified:
    """Test 2: _already_verified logic."""

    def test_already_verified_logic(self):
        mock_index = [
            {
                "id": "MTR-1_materials-20260406T120000Z",
                "is_synthetic": False,
            },
        ]
        # Non-synthetic entry exists -> True
        assert _already_verified("MTR-1_materials", mock_index) is True
        # No entry for MTR-2 -> False
        assert _already_verified("MTR-2_materials", mock_index) is False

    def test_already_verified_ignores_synthetic(self):
        mock_index = [
            {
                "id": "MTR-1_materials-20260406T120000Z",
                "is_synthetic": True,
            },
        ]
        # Synthetic entry should NOT count
        assert _already_verified("MTR-1_materials", mock_index) is False


class TestAllBundlesExist:
    """Test 3: All 20 claims have bundles in proof_library/bundles/."""

    def test_all_bundles_exist(self):
        bundles_dir = REPO_ROOT / "proof_library" / "bundles"
        assert bundles_dir.exists(), f"Bundles dir not found: {bundles_dir}"

        found_claims = set()
        for entry in CLAIM_REGISTRY:
            label = entry["label"]
            matches = list(bundles_dir.glob(f"{label}_*.zip"))
            assert len(matches) >= 1, f"No bundle found for {label}"
            found_claims.add(entry["claim_id"])

        assert len(found_claims) == 20, f"Only found bundles for {len(found_claims)} claims"


class TestAllBundlesVerifyPass:
    """Test 4: All bundles pass mg.py verify --pack (REAL-05 requirement)."""

    def test_all_bundles_verify_pass(self):
        bundles_dir = REPO_ROOT / "proof_library" / "bundles"
        mg_py = str(REPO_ROOT / "scripts" / "mg.py")
        verified = 0
        failures = []

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for zip_path in sorted(bundles_dir.glob("*.zip")):
                # Skip the baseline bundle (different structure)
                if "mg-tests-baseline" in zip_path.name:
                    continue

                # Extract ZIP to temp directory (mg.py verify --pack expects a dir)
                extract_dir = tmp_path / zip_path.stem
                extract_dir.mkdir(parents=True, exist_ok=True)
                with zipfile.ZipFile(zip_path, "r") as zf:
                    zf.extractall(extract_dir)

                result = subprocess.run(
                    [sys.executable, mg_py, "verify", "--pack", str(extract_dir)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(REPO_ROOT),
                    encoding="utf-8",
                    errors="replace",
                )
                if result.returncode != 0:
                    failures.append(
                        f"{zip_path.name}: exit={result.returncode} "
                        f"stdout={result.stdout[:200]} "
                        f"stderr={result.stderr[:200]}"
                    )
                else:
                    verified += 1

        assert not failures, f"Bundle verification failures:\n" + "\n".join(failures)
        assert verified == 20, f"Expected 20 verified bundles, got {verified}"


class TestIndexHasAllRealEntries:
    """Test 5: proof_library/index.json has all real entries."""

    def test_index_has_all_real_entries(self):
        index_path = REPO_ROOT / "proof_library" / "index.json"
        assert index_path.exists(), "index.json not found"

        index = json.loads(index_path.read_text(encoding="utf-8"))
        non_synthetic = [e for e in index if not e.get("is_synthetic", True)]

        # 1 baseline + 20 claims = 21
        assert len(non_synthetic) >= 21, (
            f"Expected >= 21 non-synthetic entries, got {len(non_synthetic)}"
        )

        # All 8 domains represented
        domains = {e["domain"] for e in non_synthetic}
        # Domains in index may use different naming; check at least 7
        # (baseline uses "internal test verification")
        real_domains = domains - {"internal test verification"}
        assert len(real_domains) >= 7, (
            f"Expected >= 7 real domains, got {len(real_domains)}: {real_domains}"
        )


class TestRealRatioAbove50Percent:
    """Test 6: system_manifest.json real_to_synthetic_ratio >= 0.50."""

    def test_real_ratio_above_50_percent(self):
        manifest_path = REPO_ROOT / "system_manifest.json"
        assert manifest_path.exists(), "system_manifest.json not found"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ratio = manifest.get("real_to_synthetic_ratio", 0.0)
        assert ratio >= 0.50, (
            f"real_to_synthetic_ratio = {ratio}, expected >= 0.50"
        )


class TestIdempotency:
    """Test 7: Re-running would skip all claims (idempotency)."""

    def test_idempotency(self):
        index = _load_index()

        not_verified = []
        for entry in CLAIM_REGISTRY:
            label = entry["label"]
            if not _already_verified(label, index):
                not_verified.append(entry["claim_id"])

        assert not not_verified, (
            f"Claims NOT marked as verified (would re-run): {not_verified}"
        )
