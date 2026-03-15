#!/usr/bin/env python3
"""
TEST: Cross-Claim Cryptographic Chain Verification.

Tests that anchor_hash from one claim can be embedded in the next,
creating a cryptographically verifiable chain:

  MTR-1 → DT-FEM-01 → DRIFT-01

Each claim's trace_root_hash commits to the upstream claim's trace_root_hash.
Tampering any link in the chain invalidates all downstream hashes.

6 tests covering: chain formation, tamper detection, backward compatibility.
"""
import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class TestCrossClaimChain:

    def _run_mtr1(self):
        from backend.progress.mtr1_calibration import run_calibration
        return run_calibration(seed=42, E_true=70e9, n_points=50, max_strain=0.002)

    def _run_dtfem(self, anchor_hash=None):
        from backend.progress.dtfem1_displacement_verification import run_certificate
        kwargs = dict(seed=42, reference_value=1.0, rel_err_threshold=0.02)
        if anchor_hash is not None:
            kwargs["anchor_hash"] = anchor_hash
            kwargs["anchor_claim_id"] = "MTR-1"
        return run_certificate(**kwargs)

    def _run_drift(self, anchor_hash=None):
        from backend.progress.drift_monitor import run_drift_monitor
        kwargs = dict(anchor_value=70e9, current_value=70e9, drift_threshold_pct=5.0)
        if anchor_hash is not None:
            kwargs["anchor_hash"] = anchor_hash
            kwargs["anchor_claim_id"] = "DT-FEM-01"
        return run_drift_monitor(**kwargs)

    # ------------------------------------------------------------------
    # Test 1: anchor_hash changes DT-FEM-01 trace_root_hash
    # ------------------------------------------------------------------
    def test_dtfem_trace_differs_with_anchor(self):
        """
        DT-FEM-01 with anchor_hash produces different trace_root_hash
        than without anchor_hash. Proves anchor is included in chain.
        """
        mtr1 = self._run_mtr1()
        anchor = mtr1["trace_root_hash"]

        dtfem_no_anchor = self._run_dtfem(anchor_hash=None)
        dtfem_with_anchor = self._run_dtfem(anchor_hash=anchor)

        assert dtfem_no_anchor["trace_root_hash"] != dtfem_with_anchor["trace_root_hash"], \
            "anchor_hash must change trace_root_hash"

    # ------------------------------------------------------------------
    # Test 2: anchor_hash stored in DT-FEM-01 inputs
    # ------------------------------------------------------------------
    def test_dtfem_anchor_hash_in_inputs(self):
        """
        anchor_hash is stored in DT-FEM-01 inputs dict for bundle verification.
        """
        mtr1 = self._run_mtr1()
        anchor = mtr1["trace_root_hash"]

        dtfem = self._run_dtfem(anchor_hash=anchor)

        assert dtfem["inputs"].get("anchor_hash") == anchor, \
            "anchor_hash must be present in inputs"
        assert dtfem["inputs"].get("anchor_claim_id") == "MTR-1", \
            "anchor_claim_id must be 'MTR-1'"

    # ------------------------------------------------------------------
    # Test 3: DRIFT-01 anchor_hash changes trace_root_hash
    # ------------------------------------------------------------------
    def test_drift_trace_differs_with_anchor(self):
        """
        DRIFT-01 with anchor_hash produces different trace_root_hash.
        """
        mtr1 = self._run_mtr1()
        dtfem = self._run_dtfem(anchor_hash=mtr1["trace_root_hash"])
        anchor = dtfem["trace_root_hash"]

        drift_no_anchor = self._run_drift(anchor_hash=None)
        drift_with_anchor = self._run_drift(anchor_hash=anchor)

        assert drift_no_anchor["trace_root_hash"] != drift_with_anchor["trace_root_hash"], \
            "anchor_hash must change DRIFT-01 trace_root_hash"

    # ------------------------------------------------------------------
    # Test 4: Full chain MTR-1 → DT-FEM-01 → DRIFT-01 is linked
    # ------------------------------------------------------------------
    def test_full_chain_is_cryptographically_linked(self):
        """
        Full chain: DRIFT-01's trace_root_hash cryptographically commits
        to DT-FEM-01 which commits to MTR-1.

        Any change to MTR-1's inputs → different MTR-1 trace_root_hash
        → different DT-FEM-01 trace_root_hash (anchor changed)
        → different DRIFT-01 trace_root_hash (anchor changed)
        """
        # Chain with seed=42
        from backend.progress.mtr1_calibration import run_calibration
        from backend.progress.dtfem1_displacement_verification import run_certificate
        from backend.progress.drift_monitor import run_drift_monitor

        mtr1_a = run_calibration(seed=42, E_true=70e9, n_points=50, max_strain=0.002)
        dtfem_a = run_certificate(seed=42, reference_value=1.0,
                                   anchor_hash=mtr1_a["trace_root_hash"],
                                   anchor_claim_id="MTR-1")
        drift_a = run_drift_monitor(anchor_value=70e9, current_value=70e9,
                                     anchor_hash=dtfem_a["trace_root_hash"],
                                     anchor_claim_id="DT-FEM-01")

        # Chain with seed=99 (different MTR-1)
        mtr1_b = run_calibration(seed=99, E_true=70e9, n_points=50, max_strain=0.002)
        dtfem_b = run_certificate(seed=42, reference_value=1.0,
                                   anchor_hash=mtr1_b["trace_root_hash"],
                                   anchor_claim_id="MTR-1")
        drift_b = run_drift_monitor(anchor_value=70e9, current_value=70e9,
                                     anchor_hash=dtfem_b["trace_root_hash"],
                                     anchor_claim_id="DT-FEM-01")

        # MTR-1 hashes differ (different seeds)
        assert mtr1_a["trace_root_hash"] != mtr1_b["trace_root_hash"]
        # DT-FEM-01 hashes differ (anchors differ)
        assert dtfem_a["trace_root_hash"] != dtfem_b["trace_root_hash"]
        # DRIFT-01 hashes differ (anchors differ)
        assert drift_a["trace_root_hash"] != drift_b["trace_root_hash"]

    # ------------------------------------------------------------------
    # Test 5: Tamper detection — wrong anchor_hash propagates
    # ------------------------------------------------------------------
    def test_tampered_anchor_hash_changes_chain(self):
        """
        Substituting a fake anchor_hash produces a different trace_root_hash.
        An attacker cannot swap the upstream claim without detection.
        """
        mtr1 = self._run_mtr1()
        real_anchor = mtr1["trace_root_hash"]
        fake_anchor = "f" * 64  # plausible-looking fake hash

        dtfem_real = self._run_dtfem(anchor_hash=real_anchor)
        dtfem_fake = self._run_dtfem(anchor_hash=fake_anchor)

        assert dtfem_real["trace_root_hash"] != dtfem_fake["trace_root_hash"], \
            "Fake anchor must produce different trace_root_hash"

    # ------------------------------------------------------------------
    # Test 6: Backward compatibility — no anchor_hash still works
    # ------------------------------------------------------------------
    def test_no_anchor_hash_backward_compatible(self):
        """
        Claims without anchor_hash still produce valid execution_trace
        and trace_root_hash. Existing bundles are not broken.
        """
        dtfem = self._run_dtfem(anchor_hash=None)
        drift = self._run_drift(anchor_hash=None)

        assert "execution_trace" in dtfem
        assert "trace_root_hash" in dtfem
        assert len(dtfem["execution_trace"]) == 4

        assert "execution_trace" in drift
        assert "trace_root_hash" in drift
        assert len(drift["execution_trace"]) == 4

        # No anchor_hash in inputs when not provided
        assert dtfem["inputs"].get("anchor_hash") is None
        assert drift["inputs"].get("anchor_hash") is None
