#!/usr/bin/env python3
"""
TEST: Cross-Claim Cryptographic Chain Verification.

Tests that anchor_hash from one claim can be embedded in the next,
creating a cryptographically verifiable chain:

  MTR-1 → DT-FEM-01 → DRIFT-01 → DT-CALIB-LOOP-01

Each claim's trace_root_hash commits to the upstream claim's trace_root_hash.
Tampering any link in the chain invalidates all downstream hashes.

15 tests covering: chain formation, tamper detection, backward compatibility,
full 4-hop chain (CASCADE-01), failure propagation (CASCADE-02),
tamper at any position (CASCADE-03).
"""
import hashlib
import json
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


class TestFullAnchorChain:
    """
    Full 4-hop anchor chain tests:
    MTR-1 -> DT-FEM-01 -> DRIFT-01 -> DT-CALIB-LOOP-01

    CASCADE-01: Full chain formation and hash uniqueness.
    CASCADE-02: Failure propagation and _verify_chain detection.
    CASCADE-03: Tamper at any hop position.

    9 tests.
    """

    def _run_mtr1(self, seed=42):
        from backend.progress.mtr1_calibration import run_calibration
        return run_calibration(seed=seed, E_true=70e9, n_points=50, max_strain=0.002)

    def _run_dtfem(self, anchor_hash=None, seed=42):
        from backend.progress.dtfem1_displacement_verification import run_certificate
        kwargs = dict(seed=seed, reference_value=1.0, rel_err_threshold=0.02)
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

    def _run_dtcalib(self, anchor_hash=None):
        from backend.progress.dtcalib1_convergence_certificate import run_certificate
        kwargs = dict(seed=42, n_iterations=10, initial_drift_pct=20.0,
                      convergence_rate=0.4, convergence_threshold=2.0, noise_scale=0.1,
                      twin_id="TWIN-001")
        if anchor_hash is not None:
            kwargs["anchor_hash"] = anchor_hash
            kwargs["anchor_claim_id"] = "DRIFT-01"
        return run_certificate(**kwargs)

    def _run_full_chain(self, mtr1_seed=42, dtfem_seed=42):
        mtr1 = self._run_mtr1(seed=mtr1_seed)
        dtfem = self._run_dtfem(anchor_hash=mtr1["trace_root_hash"], seed=dtfem_seed)
        drift = self._run_drift(anchor_hash=dtfem["trace_root_hash"])
        dtcalib = self._run_dtcalib(anchor_hash=drift["trace_root_hash"])
        return mtr1, dtfem, drift, dtcalib

    # ------------------------------------------------------------------
    # CASCADE-01: Full 4-hop chain
    # ------------------------------------------------------------------
    def test_a_full_4hop_chain_all_hashes_differ(self):
        """All four trace_root_hashes in the full chain are distinct."""
        mtr1, dtfem, drift, dtcalib = self._run_full_chain()
        hashes = [
            mtr1["trace_root_hash"],
            dtfem["trace_root_hash"],
            drift["trace_root_hash"],
            dtcalib["trace_root_hash"],
        ]
        assert len(set(hashes)) == 4, \
            f"Expected 4 unique hashes, got {len(set(hashes))}: {hashes}"

    def test_b_dtcalib_anchor_hash_stored_in_inputs(self):
        """DT-CALIB-LOOP-01 has anchor_hash and anchor_claim_id='DRIFT-01' in inputs."""
        _, _, drift, dtcalib = self._run_full_chain()
        assert dtcalib["inputs"].get("anchor_hash") == drift["trace_root_hash"], \
            "DT-CALIB-LOOP-01 must store DRIFT-01 trace_root_hash as anchor_hash"
        assert dtcalib["inputs"].get("anchor_claim_id") == "DRIFT-01", \
            "anchor_claim_id must be 'DRIFT-01'"

    # ------------------------------------------------------------------
    # CASCADE-02: Failure propagation
    # ------------------------------------------------------------------
    def test_c_upstream_tamper_propagates_through_all_hops(self):
        """
        Changing MTR-1 seed from 42 to 99 produces different hashes
        at every downstream hop in the 4-hop chain.
        """
        mtr1_a, dtfem_a, drift_a, dtcalib_a = self._run_full_chain(mtr1_seed=42)
        mtr1_b, dtfem_b, drift_b, dtcalib_b = self._run_full_chain(mtr1_seed=99)

        assert mtr1_a["trace_root_hash"] != mtr1_b["trace_root_hash"], \
            "MTR-1 hashes must differ with different seeds"
        assert dtfem_a["trace_root_hash"] != dtfem_b["trace_root_hash"], \
            "DT-FEM-01 hashes must differ when upstream anchor changes"
        assert drift_a["trace_root_hash"] != drift_b["trace_root_hash"], \
            "DRIFT-01 hashes must differ when upstream anchor changes"
        assert dtcalib_a["trace_root_hash"] != dtcalib_b["trace_root_hash"], \
            "DT-CALIB-LOOP-01 hashes must differ when upstream anchor changes"

    def test_d_dtcalib_trace_differs_with_anchor(self):
        """DT-CALIB-LOOP-01 with vs without anchor_hash produces different trace_root_hash."""
        dtcalib_no_anchor = self._run_dtcalib(anchor_hash=None)
        _, _, drift, _ = self._run_full_chain()
        dtcalib_with_anchor = self._run_dtcalib(anchor_hash=drift["trace_root_hash"])

        assert dtcalib_no_anchor["trace_root_hash"] != dtcalib_with_anchor["trace_root_hash"], \
            "anchor_hash must change DT-CALIB-LOOP-01 trace_root_hash"

    def test_e_verify_chain_reports_break(self, tmp_path):
        """
        _verify_chain() detects tampered anchor_hash in a 2-pack chain.
        Pack A = MTR-1, Pack B = DT-FEM-01 with fake anchor_hash.
        """
        from scripts.mg import _verify_chain

        mtr1 = self._run_mtr1()
        dtfem = self._run_dtfem(anchor_hash="f" * 64, seed=42)  # fake anchor

        # -- Build Pack A (MTR-1) --
        pack_a = tmp_path / "pack_a"
        pack_a.mkdir()
        ev_a = pack_a / "evidence" / "MTR-1" / "normal"
        ev_a.mkdir(parents=True)

        domain_a = {
            "mtr_phase": "MTR-1",
            "inputs": mtr1["inputs"],
            "result": mtr1["result"],
            "execution_trace": mtr1["execution_trace"],
            "trace_root_hash": mtr1["trace_root_hash"],
        }
        run_a = {
            "w6_phase": "W6-A5", "kind": "success",
            "job_id": "job-mtr1-001", "trace_id": "trace-mtr1-001",
            "canary_mode": False,
            "job_snapshot": {
                "job_id": "job-mtr1-001", "status": "SUCCEEDED",
                "payload": {"kind": "mtr1_calibration"},
                "result": domain_a,
            },
            "ledger_action": "job_completed",
            "persisted_at": "2026-03-18T00:00:00Z",
        }
        (ev_a / "run_artifact.json").write_text(
            json.dumps(run_a), encoding="utf-8")
        (ev_a / "ledger_snapshot.jsonl").write_text(
            json.dumps({"trace_id": "trace-mtr1-001", "action": "job_completed",
                        "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
            encoding="utf-8")

        idx_a = {
            "MTR-1": {
                "job_kind": "mtr1_calibration",
                "normal": {
                    "run_relpath": "evidence/MTR-1/normal/run_artifact.json",
                    "ledger_relpath": "evidence/MTR-1/normal/ledger_snapshot.jsonl",
                },
            }
        }
        (pack_a / "evidence_index.json").write_text(
            json.dumps(idx_a), encoding="utf-8")

        # Build pack_manifest.json for Pack A
        self._write_manifest(pack_a)

        # -- Build Pack B (DT-FEM-01 with tampered anchor) --
        pack_b = tmp_path / "pack_b"
        pack_b.mkdir()
        ev_b = pack_b / "evidence" / "DT-FEM-01" / "normal"
        ev_b.mkdir(parents=True)

        domain_b = {
            "mtr_phase": "DT-FEM-01",
            "inputs": dtfem["inputs"],
            "result": dtfem["result"],
            "execution_trace": dtfem["execution_trace"],
            "trace_root_hash": dtfem["trace_root_hash"],
        }
        run_b = {
            "w6_phase": "W6-A5", "kind": "success",
            "job_id": "job-dtfem-001", "trace_id": "trace-dtfem-001",
            "canary_mode": False,
            "job_snapshot": {
                "job_id": "job-dtfem-001", "status": "SUCCEEDED",
                "payload": {"kind": "dtfem1_displacement_verification"},
                "result": domain_b,
            },
            "ledger_action": "job_completed",
            "persisted_at": "2026-03-18T00:00:00Z",
        }
        (ev_b / "run_artifact.json").write_text(
            json.dumps(run_b), encoding="utf-8")
        (ev_b / "ledger_snapshot.jsonl").write_text(
            json.dumps({"trace_id": "trace-dtfem-001", "action": "job_completed",
                        "actor": "scheduler_v1", "meta": {"canary_mode": False}}) + "\n",
            encoding="utf-8")

        idx_b = {
            "DT-FEM-01": {
                "job_kind": "dtfem1_displacement_verification",
                "normal": {
                    "run_relpath": "evidence/DT-FEM-01/normal/run_artifact.json",
                    "ledger_relpath": "evidence/DT-FEM-01/normal/ledger_snapshot.jsonl",
                },
            }
        }
        (pack_b / "evidence_index.json").write_text(
            json.dumps(idx_b), encoding="utf-8")

        self._write_manifest(pack_b)

        # Verify chain detects the tampered anchor
        ok, msg, _report = _verify_chain([pack_a, pack_b])
        assert ok is False, "Chain verification must detect tampered anchor"
        assert any(kw in msg.lower() for kw in ("anchor", "mismatch", "chain")), \
            f"Message should reference chain break, got: {msg}"

    @staticmethod
    def _write_manifest(pack_dir):
        """Build pack_manifest.json with correct SHA-256 hashes."""
        files_list = []
        for p in sorted(pack_dir.rglob("*")):
            if not p.is_file() or p.name == "pack_manifest.json":
                continue
            relpath = str(p.relative_to(pack_dir)).replace("\\", "/")
            raw = p.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            files_list.append({"relpath": relpath, "sha256": sha, "bytes": len(raw)})

        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(files_list, key=lambda x: x["relpath"])
        )
        root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()
        manifest = {
            "pack_version": "1",
            "protocol_version": 1,
            "files": files_list,
            "root_hash": root_hash,
        }
        (pack_dir / "pack_manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # CASCADE-03: Tamper at any hop position
    # ------------------------------------------------------------------
    def test_f_tamper_hop1_mtr1_to_dtfem(self):
        """Fake anchor at hop 1 (MTR-1->DT-FEM-01) changes DT-FEM-01 hash."""
        _, dtfem_legit, _, _ = self._run_full_chain()
        dtfem_tampered = self._run_dtfem(anchor_hash="f" * 64)
        assert dtfem_legit["trace_root_hash"] != dtfem_tampered["trace_root_hash"], \
            "Tampered hop 1 must produce different DT-FEM-01 hash"

    def test_g_tamper_hop2_dtfem_to_drift(self):
        """Fake anchor at hop 2 (DT-FEM-01->DRIFT-01) changes DRIFT-01 hash."""
        _, _, drift_legit, _ = self._run_full_chain()
        drift_tampered = self._run_drift(anchor_hash="f" * 64)
        assert drift_legit["trace_root_hash"] != drift_tampered["trace_root_hash"], \
            "Tampered hop 2 must produce different DRIFT-01 hash"

    def test_h_tamper_hop3_drift_to_dtcalib(self):
        """Fake anchor at hop 3 (DRIFT-01->DT-CALIB-LOOP-01) changes DT-CALIB-LOOP-01 hash."""
        _, _, _, dtcalib_legit = self._run_full_chain()
        dtcalib_tampered = self._run_dtcalib(anchor_hash="f" * 64)
        assert dtcalib_legit["trace_root_hash"] != dtcalib_tampered["trace_root_hash"], \
            "Tampered hop 3 must produce different DT-CALIB-LOOP-01 hash"

    def test_i_middle_swap_dtfem_seed99(self):
        """
        Substituting DT-FEM-01 (seed=99 instead of seed=42) with same MTR-1
        anchor produces different DT-FEM-01 trace_root_hash.
        """
        mtr1 = self._run_mtr1(seed=42)
        anchor = mtr1["trace_root_hash"]

        dtfem_42 = self._run_dtfem(anchor_hash=anchor, seed=42)
        dtfem_99 = self._run_dtfem(anchor_hash=anchor, seed=99)

        assert dtfem_42["trace_root_hash"] != dtfem_99["trace_root_hash"], \
            "Middle swap (seed=99) must produce different trace_root_hash"
