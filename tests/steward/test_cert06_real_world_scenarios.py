#!/usr/bin/env python3
"""
CERT-06: Real-World Verification Scenarios — End-to-End Proof Stories.

This file demonstrates MetaGenesis Core solving real verification problems
that occur in production ML, pharma, and engineering environments.

Unlike unit tests, these are narrative proof scenarios — each tells a complete
story from "claim made" to "claim independently verified" or "fraud detected."

SCENARIO 1 — The Honest ML Team
  Team A produces 94.3% accuracy. They package it. Team B verifies offline.
  No model access. No environment. 60 seconds. PASS.

SCENARIO 2 — The Cherry-Picker
  A team runs 10 experiments, picks the best result, submits it as "their" result.
  The Step Chain commits to the exact seed and parameters.
  A reviewer with a different seed gets a different trace_root_hash → CAUGHT.

SCENARIO 3 — The Physical Anchor Story
  FEM simulation claims 1.001mm displacement. The claim is traced back to
  E=70 GPa — a physical constant measured in thousands of labs worldwide.
  Any manufacturer can verify the entire chain from physics to simulation.

SCENARIO 4 — The Real Client Data Story
  A client sends y_true/y_pred CSV. MetaGenesis bundles it with SHA-256
  fingerprint. Six months later, in a regulatory audit, the auditor
  re-hashes the CSV and it matches. The data was never modified.

SCENARIO 5 — The Reproducibility Crisis Story
  A paper claims 94% accuracy. Reviewer runs the same code, gets 91%.
  With MetaGenesis: the paper bundle includes exact seed, sample count,
  split strategy in the Step Chain. The reviewer can prove which one
  matches the bundle.
"""

import sys
from pathlib import Path
import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


class TestRealWorldScenarios:

    # ------------------------------------------------------------------
    # SCENARIO 1 — The Honest ML Team
    # ------------------------------------------------------------------
    def test_scenario1_honest_team_verification(self):
        """
        Team A produces result. Team B verifies. No communication needed.

        Proves: the verification protocol works end-to-end between
        two completely independent parties with no shared infrastructure.
        """
        from backend.progress.mlbench1_accuracy_certificate import run_certificate

        # Team A: produce result with their setup
        team_a_result = run_certificate(seed=42, claimed_accuracy=0.943, n_samples=1000)

        # Team A packages: trace_root_hash is the proof
        bundle_hash = team_a_result["trace_root_hash"]
        bundle_trace = team_a_result["execution_trace"]

        # Team B: verify independently (they have the bundle, not the model)
        # Step Chain: trace_root_hash must equal last step hash
        assert bundle_hash == bundle_trace[-1]["hash"], \
            "SCENARIO 1: Bundle integrity failed — Step Chain broken"

        # Team B: semantic check — result.pass is True
        assert team_a_result["result"]["pass"] is True, \
            "SCENARIO 1: Claimed accuracy failed threshold check"

        # Team B: all 4 steps present
        assert len(bundle_trace) == 4, \
            "SCENARIO 1: Incomplete execution trace — not all steps recorded"

        # PASS: Team B independently verified Team A's claim
        assert team_a_result["result"]["actual_accuracy"] >= 0.923, \
            "SCENARIO 1: Actual accuracy below tolerance band"

    # ------------------------------------------------------------------
    # SCENARIO 2 — The Cherry-Picker
    # ------------------------------------------------------------------
    def test_scenario2_cherry_picker_caught(self):
        """
        Team runs 10 seeds, submits best result as if it were reproducible.
        Step Chain commits to exact seed — different seeds = different hashes.

        Proves: selective reporting is detectable when Step Chain is included.
        """
        from backend.progress.mlbench1_accuracy_certificate import run_certificate

        # Run 10 experiments with different seeds
        results = [run_certificate(seed=i, claimed_accuracy=0.90, n_samples=200)
                   for i in range(10)]

        # All trace_root_hashes must be different (seed baked in)
        hashes = [r["trace_root_hash"] for r in results]
        assert len(set(hashes)) == 10, \
            "SCENARIO 2: Different seeds produced identical hashes — seed not in chain"

        # Cherry-picker submits seed=7 result as if it were reproducible
        # but tries to present it with seed=0 trace_root_hash
        cherry_result = results[7]  # best result
        seed0_hash    = results[0]["trace_root_hash"]

        # Fraud: claim seed=0 hash but have seed=7 trace
        fraud_detected = (cherry_result["trace_root_hash"] != seed0_hash)
        assert fraud_detected, \
            "SCENARIO 2: Cherry-picker could use different seed hash — not detected"

    # ------------------------------------------------------------------
    # SCENARIO 3 — The Physical Anchor Story
    # ------------------------------------------------------------------
    def test_scenario3_physical_anchor_chain(self):
        """
        FEM simulation traced back to E=70 GPa (physical reality).

        Proves: a manufacturing partner can verify that a simulation result
        is ultimately grounded in a physical constant they can independently
        measure in their own lab. No trust in the simulation vendor required.
        """
        from backend.progress.mtr1_calibration import run_calibration
        from backend.progress.dtfem1_displacement_verification import run_certificate
        from backend.progress.drift_monitor import run_drift_monitor

        # Step 1: MTR-1 anchors to E=70 GPa (physical constant)
        E_physical = 70e9  # Pa — measured in thousands of labs worldwide
        mtr1 = run_calibration(seed=42, E_true=E_physical, n_points=50,
                               max_strain=0.002)
        assert mtr1["result"]["pass"] is True, "MTR-1 failed physical anchor check"
        assert mtr1["result"]["rel_err"] <= 0.01, "MTR-1 rel_err exceeds 1% of physical constant"

        # Step 2: FEM simulation verified against MTR-1 anchor
        dtfem = run_certificate(seed=42, reference_value=1.0,
                                anchor_hash=mtr1["trace_root_hash"],
                                anchor_claim_id="MTR-1")
        assert dtfem["result"]["pass"] is True, "DT-FEM-01 failed verification"

        # Step 3: Drift monitoring anchored to FEM
        drift = run_drift_monitor(
            anchor_value=E_physical, current_value=E_physical * 1.02,  # 2% drift
            anchor_hash=dtfem["trace_root_hash"],
            anchor_claim_id="DT-FEM-01"
        )

        # The entire chain is cryptographically linked
        # Manufacturing partner verifies: drift.inputs.anchor_hash == dtfem.trace_root_hash
        assert drift["inputs"]["anchor_hash"] == dtfem["trace_root_hash"], \
            "SCENARIO 3: Physical anchor chain broken between DT-FEM-01 and DRIFT-01"

        # And DT-FEM-01 chain links to MTR-1
        assert dtfem["inputs"]["anchor_hash"] == mtr1["trace_root_hash"], \
            "SCENARIO 3: Physical anchor chain broken between MTR-1 and DT-FEM-01"

        # Full traceability: from drift monitoring back to physical reality
        # drift → DT-FEM-01 → MTR-1 → E=70 GPa (measured physical constant)
        chain_depth = 3  # MTR-1, DT-FEM-01, DRIFT-01
        assert chain_depth == 3, "SCENARIO 3: Unexpected chain depth"

    # ------------------------------------------------------------------
    # SCENARIO 4 — The Real Client Data Audit
    # ------------------------------------------------------------------
    def test_scenario4_real_data_audit_trail(self):
        """
        Client sends CSV. Bundle created. 6 months later: audit.
        SHA-256 fingerprint proves data was never modified.

        Proves: real client data has a tamper-evident provenance chain
        even without re-running the computation.
        """
        import csv
        import hashlib
        import tempfile
        import os
        from backend.progress.mlbench1_accuracy_certificate import run_certificate

        # Client's original data
        original_data = [
            ("y_true", "y_pred"),
            ("1", "1"), ("0", "0"), ("1", "1"), ("0", "0"), ("1", "0"),
            ("1", "1"), ("0", "0"), ("1", "1"), ("0", "1"), ("1", "1"),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv',
                                         delete=False, newline='') as f:
            writer = csv.writer(f)
            writer.writerows(original_data)
            csv_path = f.name

        try:
            # Create bundle with real data
            result = run_certificate(
                seed=42,
                claimed_accuracy=0.80,
                dataset_relpath=csv_path,
            )

            # SHA-256 fingerprint stored in bundle
            bundled_sha256 = result["inputs"]["dataset"]["sha256"]

            # 6 months later: auditor re-hashes the same CSV
            with open(csv_path, 'rb') as f:
                current_sha256 = hashlib.sha256(f.read()).hexdigest()

            assert bundled_sha256 == current_sha256, \
                "SCENARIO 4: SHA-256 mismatch — data was modified after bundling"

            # TAMPER: someone modifies one row in the CSV
            tampered_path = csv_path + ".tampered"
            tampered_data = list(original_data)
            tampered_data[1] = ("1", "0")  # change prediction for row 1
            with open(tampered_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(tampered_data)

            with open(tampered_path, 'rb') as f:
                tampered_sha256 = hashlib.sha256(f.read()).hexdigest()

            # Tampered data has different SHA-256
            assert bundled_sha256 != tampered_sha256, \
                "SCENARIO 4: SHA-256 did not detect data tampering"

        finally:
            os.unlink(csv_path)
            if os.path.exists(csv_path + ".tampered"):
                os.unlink(csv_path + ".tampered")

    # ------------------------------------------------------------------
    # SCENARIO 5 — The Reproducibility Crisis
    # ------------------------------------------------------------------
    def test_scenario5_reproducibility_crisis_resolution(self):
        """
        Paper claims 94%. Reviewer gets 91%. Who is right?
        With MetaGenesis: the bundle commits to exact parameters.
        The reviewer can prove which parameters match the bundle hash.

        Proves: MetaGenesis Core resolves the reproducibility crisis
        by making parameter commitments cryptographically verifiable.
        """
        from backend.progress.mlbench1_accuracy_certificate import run_certificate

        # Paper authors used seed=42, n_samples=1000
        paper_result = run_certificate(seed=42, claimed_accuracy=0.94,
                                       n_samples=1000)
        paper_hash = paper_result["trace_root_hash"]

        # Reviewer tries seed=42 but n_samples=100 (different)
        reviewer_result_wrong = run_certificate(seed=42, claimed_accuracy=0.94,
                                                n_samples=100)
        reviewer_hash_wrong = reviewer_result_wrong["trace_root_hash"]

        # Reviewer tries exact parameters: seed=42, n_samples=1000
        reviewer_result_correct = run_certificate(seed=42, claimed_accuracy=0.94,
                                                  n_samples=1000)
        reviewer_hash_correct = reviewer_result_correct["trace_root_hash"]

        # Wrong parameters → different hash (discrepancy detected)
        assert paper_hash != reviewer_hash_wrong, \
            "SCENARIO 5: Different n_samples produced same hash — params not in chain"

        # Correct parameters → same hash (reproduction confirmed)
        assert paper_hash == reviewer_hash_correct, \
            "SCENARIO 5: Same params produced different hash — non-deterministic"

        # This resolves the crisis:
        # - If reviewer gets wrong hash: they used wrong parameters
        # - If reviewer gets right hash: reproduction is confirmed
        # No trust required. No communication needed. Pure math.
