#!/usr/bin/env python3
"""
Progress Engine Runner - Job Execution with Ledger Integration

Purpose: Execute jobs and emit ledger entries for traceability
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
Implementation: In-process runner with deterministic ledger events
"""

import sys
import os
import json
from pathlib import Path
import logging
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, '/app')

from backend.progress.models import Job, JobStatus, now_iso8601
from backend.progress.store import JobStore
from backend.ledger.models import LedgerEntry
from backend.ledger.ledger_store import LedgerStore

logger = logging.getLogger(__name__)


class ProgressRunner:
    """Job runner with ledger integration."""
    
    def __init__(self, job_store: JobStore, ledger_store: LedgerStore):
        self.job_store = job_store
        self.ledger_store = ledger_store
        logger.info("ProgressRunner initialized with ledger integration")
    
    def create_job(self, payload: Dict[str, Any] = None) -> Job:
        """Create new job and emit ledger entry."""
        from backend.progress.models import generate_job_id, generate_trace_id
        
        job = Job(
            job_id=generate_job_id(),
            trace_id=generate_trace_id(),
            created_at=now_iso8601(),
            status=JobStatus.QUEUED,
            payload=payload or {}
        )
        
        self.job_store.create(job)
        
        ledger_entry = LedgerEntry(
            trace_id=job.trace_id,
            created_at=job.created_at,
            phase=31,
            actor="scheduler_v1",
            action="job_created",
            inputs={
                'job_id': job.job_id,
                'payload': job.payload
            },
            outputs={},
            artifacts=[],
            legal_sig_refs=["metagenesis-core-ppa-63996819"],
            meta={'job_status': job.status.value}
        )
        
        self.ledger_store.append(ledger_entry)
        logger.info(f"Job created and logged: {job.job_id}")
        
        return job
    
    def run_job(self, job_id: str, canary_mode: bool = False) -> Job:
        """Execute job and emit completion ledger entry.
        
        Args:
            job_id: Job to execute
            canary_mode: If True, run is non-authoritative (canary).
        """
        job = self.job_store.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        if job.status == JobStatus.RUNNING:
            raise ValueError(f"Job already running: {job_id}")
        
        job.status = JobStatus.RUNNING
        job.started_at = now_iso8601()
        self.job_store.update(job)
        
        try:
            result = self._execute_job_logic(job)
            
            job.status = JobStatus.SUCCEEDED
            job.completed_at = now_iso8601()
            job.result = result
            self.job_store.update(job)
            
            action = "job_completed_canary" if canary_mode else "job_completed"
            actor = "scheduler_v1_canary" if canary_mode else "scheduler_v1"
            meta = {
                'job_status': job.status.value,
                'execution_time_ms': self._compute_execution_time(job),
                'canary_mode': canary_mode
            }
            ledger_entry = LedgerEntry(
                trace_id=job.trace_id,
                created_at=job.completed_at,
                phase=31,
                actor=actor,
                action=action,
                inputs={'job_id': job.job_id},
                outputs={
                    'status': job.status.value,
                    'result': job.result
                },
                artifacts=[],
                legal_sig_refs=["metagenesis-core-ppa-63996819"],
                meta=meta
            )
            
            self.ledger_store.append(ledger_entry)
            self._persist_evidence(job, ledger_entry, "success", canary_mode)
            logger.info(f"Job completed successfully: {job.job_id}")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.completed_at = now_iso8601()
            job.error = str(e)
            self.job_store.update(job)
            
            action = "job_failed_canary" if canary_mode else "job_failed"
            actor = "scheduler_v1_canary" if canary_mode else "scheduler_v1"
            meta = {'job_status': job.status.value, 'canary_mode': canary_mode}
            ledger_entry = LedgerEntry(
                trace_id=job.trace_id,
                created_at=job.completed_at,
                phase=31,
                actor=actor,
                action=action,
                inputs={'job_id': job.job_id},
                outputs={
                    'status': job.status.value,
                    'error': job.error
                },
                artifacts=[],
                legal_sig_refs=["metagenesis-core-ppa-63996819"],
                meta=meta
            )
            
            self.ledger_store.append(ledger_entry)
            self._persist_evidence(job, ledger_entry, "failure", canary_mode)
            logger.error(f"Job failed: {job.job_id} - {e}")
        
        return job
    
    def _persist_evidence(self, job: Job, ledger_entry: LedgerEntry, kind: str, canary_mode: bool) -> None:
        """Persist W6-A5 run artifact and ledger snapshot to artifact dir."""
        base = Path(os.getenv("MG_PROGRESS_ARTIFACT_DIR", "reports"))
        progress_runs_dir = base / "progress_runs"
        ledger_snapshots_dir = base / "ledger_snapshots"
        progress_runs_dir.mkdir(parents=True, exist_ok=True)
        ledger_snapshots_dir.mkdir(parents=True, exist_ok=True)
        
        persisted_at = now_iso8601()
        run_artifact = {
            "w6_phase": "W6-A5",
            "kind": kind,
            "job_id": job.job_id,
            "trace_id": job.trace_id,
            "canary_mode": canary_mode,
            "job_snapshot": job.to_dict(),
            "ledger_action": ledger_entry.action,
            "persisted_at": persisted_at
        }
        run_path = progress_runs_dir / f"job_{job.job_id}_trace_{job.trace_id}_{kind}.json"
        with open(run_path, 'w') as f:
            json.dump(run_artifact, f, indent=2)
        
        snapshot_line = {
            "trace_id": ledger_entry.trace_id,
            "action": ledger_entry.action,
            "actor": ledger_entry.actor,
            "meta": {"canary_mode": canary_mode}
        }
        snapshot_path = ledger_snapshots_dir / f"trace_{job.trace_id}.jsonl"
        with open(snapshot_path, 'a') as f:
            f.write(json.dumps(snapshot_line) + "\n")
    
    def _execute_job_logic(self, job: Job) -> Dict[str, Any]:
        """Dispatch job execution by payload.kind."""
        payload = job.payload or {}

        from backend.progress.mtr1_calibration import JOB_KIND as MTR1_KIND, run_calibration as run_mtr1
        from backend.progress.mtr2_thermal_conductivity import JOB_KIND as MTR2_KIND, run_calibration as run_mtr2
        from backend.progress.mtr3_thermal_multilayer import JOB_KIND as MTR3_KIND, run_calibration as run_mtr3
        from backend.progress.sysid1_arx_calibration import JOB_KIND as SYSID1_KIND
        from backend.progress.datapipe1_quality_certificate import JOB_KIND as DATAPIPE1_KIND
        from backend.progress.drift_monitor import JOB_KIND as DRIFT01_KIND
        from backend.progress.mlbench1_accuracy_certificate import JOB_KIND as MLBENCH1_KIND
        from backend.progress.dtfem1_displacement_verification import JOB_KIND as DTFEM1_KIND

        if payload.get("kind") == MTR1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                E_true=float(p.get("E_true", 200e9)),
                n_points=int(p.get("n_points", 50)),
                max_strain=float(p.get("max_strain", 0.002)),
                noise_scale=float(p["noise_scale"]) if p.get("noise_scale") is not None else None,
            )
            if p.get("dataset_relpath") is not None:
                kwargs["dataset_relpath"] = str(p["dataset_relpath"]).strip()
                kwargs["elastic_strain_max"] = float(p.get("elastic_strain_max", 0.002))
            if p.get("uq_samples") is not None:
                kwargs["uq_samples"] = int(p["uq_samples"])
                kwargs["uq_seed"] = int(p.get("uq_seed", p.get("seed", 42)))
            return run_mtr1(**kwargs)

        if payload.get("kind") == MTR2_KIND:
            return run_mtr2(
                seed=int(payload.get("seed", 42)),
                k_true=float(payload.get("k_true", 5.0)),
                n_points=int(payload.get("n_points", 50)),
                L=float(payload.get("L", 0.01)),
                A=float(payload.get("A", 1e-4)),
                q_max=float(payload.get("q_max", 10.0)),
                noise_scale=float(payload["noise_scale"]) if payload.get("noise_scale") is not None else None,
            )

        if payload.get("kind") == MTR3_KIND:
            p = payload
            return run_mtr3(
                seed=int(p.get("seed", 42)),
                k_true=float(p.get("k_true", 5.0)),
                r_contact_true=float(p.get("r_contact_true", 0.1)),
                n_points=int(p.get("n_points", 50)),
                L1=float(p.get("L1", 0.01)),
                A1=float(p.get("A1", 1e-4)),
                L2=float(p.get("L2", 0.02)),
                A2=float(p.get("A2", 1e-4)),
                q_max=float(p.get("q_max", 10.0)),
                noise_scale=float(p["noise_scale"]) if p.get("noise_scale") is not None else None,
            )

        from backend.progress.sysid1_arx_calibration import JOB_KIND as SYSID1_KIND, run_calibration as run_sysid1
        if payload.get("kind") == SYSID1_KIND:
            p = payload
            return run_sysid1(
                seed=int(p.get("seed", 42)),
                a_true=float(p.get("a_true", 0.9)),
                b_true=float(p.get("b_true", 0.5)),
                n_steps=int(p.get("n_steps", 50)),
                u_max=float(p.get("u_max", 1.0)),
                noise_scale=float(p["noise_scale"]) if p.get("noise_scale") is not None else None,
            )

        from backend.progress.datapipe1_quality_certificate import JOB_KIND as DATAPIPE1_KIND, run_certificate as run_datapipe1
        if payload.get("kind") == DATAPIPE1_KIND:
            p = payload
            return run_datapipe1(
                seed=int(p.get("seed", 42)),
                dataset_relpath=str(p.get("dataset_relpath", "")).strip(),
                required_columns=p.get("required_columns"),
                numeric_columns=p.get("numeric_columns"),
                ranges_json=str(p["ranges_json"]) if p.get("ranges_json") is not None else None,
            )

        from backend.progress.drift_monitor import JOB_KIND as DRIFT01_KIND, run_drift_monitor as run_drift01
        if payload.get("kind") == DRIFT01_KIND:
            p = payload
            return run_drift01(
                anchor_value=float(p.get("anchor_value", 70000000000.0)),
                current_value=float(p.get("current_value", 70000000000.0)),
                anchor_claim_id=str(p.get("anchor_claim_id", "MTR-1")),
                anchor_units=str(p.get("anchor_units", "Pa")),
                drift_threshold_pct=float(p.get("drift_threshold_pct", 5.0)),
            )

        from backend.progress.mlbench1_accuracy_certificate import JOB_KIND as MLBENCH1_KIND, run_certificate as run_mlbench1
        if payload.get("kind") == MLBENCH1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                claimed_accuracy=float(p.get("claimed_accuracy", 0.90)),
                accuracy_tolerance=float(p.get("accuracy_tolerance", 0.02)),
                n_samples=int(p.get("n_samples", 1000)),
                n_features=int(p.get("n_features", 10)),
                noise_scale=float(p["noise_scale"]) if p.get("noise_scale") is not None else None,
            )
            if p.get("dataset_relpath") is not None:
                kwargs["dataset_relpath"] = str(p["dataset_relpath"]).strip()
            return run_mlbench1(**kwargs)

        from backend.progress.dtfem1_displacement_verification import JOB_KIND as DTFEM1_KIND, run_certificate as run_dtfem1
        if payload.get("kind") == DTFEM1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                reference_value=float(p.get("reference_value", 1.0)),
                rel_err_threshold=float(p.get("rel_err_threshold", 0.02)),
                noise_scale=float(p.get("noise_scale", 0.005)),
                quantity=str(p.get("quantity", "displacement_mm")),
                units=str(p.get("units", "mm")),
            )
            if p.get("dataset_relpath") is not None:
                kwargs["dataset_relpath"] = str(p["dataset_relpath"]).strip()
            return run_dtfem1(**kwargs)

        from backend.progress.mlbench2_regression_certificate import JOB_KIND as MLBENCH2_KIND, run_certificate as run_mlbench2
        if payload.get("kind") == MLBENCH2_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                claimed_rmse=float(p.get("claimed_rmse", 0.10)),
                rmse_tolerance=float(p.get("rmse_tolerance", 0.02)),
                n_samples=int(p.get("n_samples", 1000)),
                n_features=int(p.get("n_features", 10)),
                noise_scale=float(p.get("noise_scale", 0.10)),
            )
            if p.get("dataset_relpath") is not None:
                kwargs["dataset_relpath"] = str(p["dataset_relpath"]).strip()
            if p.get("anchor_hash") is not None:
                kwargs["anchor_hash"] = str(p["anchor_hash"])
                kwargs["anchor_claim_id"] = str(p.get("anchor_claim_id", "ML_BENCH-01"))
            return run_mlbench2(**kwargs)

        from backend.progress.mlbench3_timeseries_certificate import JOB_KIND as MLBENCH3_KIND, run_certificate as run_mlbench3
        if payload.get("kind") == MLBENCH3_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                claimed_mape=float(p.get("claimed_mape", 0.05)),
                mape_tolerance=float(p.get("mape_tolerance", 0.02)),
                n_steps=int(p.get("n_steps", 200)),
                trend=float(p.get("trend", 1.0)),
                noise_scale=float(p.get("noise_scale", 5.0)),
            )
            if p.get("dataset_relpath"):
                kwargs["dataset_relpath"] = str(p["dataset_relpath"]).strip()
            if p.get("anchor_hash"):
                kwargs["anchor_hash"] = str(p["anchor_hash"])
                kwargs["anchor_claim_id"] = str(p.get("anchor_claim_id", "ML_BENCH-01"))
            return run_mlbench3(**kwargs)

        from backend.progress.pharma1_admet_certificate import JOB_KIND as PHARMA1_KIND, run_certificate as run_pharma1
        if payload.get("kind") == PHARMA1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                property_name=str(p.get("property_name", "solubility")),
                claimed_value=float(p.get("claimed_value", -3.5)),
                tolerance=float(p.get("tolerance", 0.5)),
                noise_scale=float(p.get("noise_scale", 0.2)),
                compound_id=str(p.get("compound_id", "COMPOUND-001")),
            )
            if p.get("anchor_hash"):
                kwargs["anchor_hash"] = str(p["anchor_hash"])
                kwargs["anchor_claim_id"] = str(p.get("anchor_claim_id", "DATA-PIPE-01"))
            return run_pharma1(**kwargs)

        from backend.progress.finrisk1_var_certificate import JOB_KIND as FINRISK1_KIND, run_certificate as run_finrisk1
        if payload.get("kind") == FINRISK1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                claimed_var=float(p.get("claimed_var", 0.02)),
                var_tolerance=float(p.get("var_tolerance", 0.005)),
                confidence_level=float(p.get("confidence_level", 0.99)),
                n_obs=int(p.get("n_obs", 1000)),
                mu=float(p.get("mu", 0.0)),
                sigma=float(p.get("sigma", 0.01)),
                portfolio_id=str(p.get("portfolio_id", "PORTFOLIO-001")),
            )
            if p.get("anchor_hash"):
                kwargs["anchor_hash"] = str(p["anchor_hash"])
                kwargs["anchor_claim_id"] = str(p.get("anchor_claim_id", "DATA-PIPE-01"))
            return run_finrisk1(**kwargs)

        from backend.progress.dtsensor1_iot_certificate import JOB_KIND as DTSENSOR1_KIND, run_certificate as run_dtsensor1
        if payload.get("kind") == DTSENSOR1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                sensor_type=str(p.get("sensor_type", "temperature_celsius")),
                n_readings=int(p.get("n_readings", 100)),
                anomaly_rate=float(p.get("anomaly_rate", 0.0)),
                device_id=str(p.get("device_id", "SENSOR-001")),
            )
            if p.get("anchor_hash"):
                kwargs["anchor_hash"] = str(p["anchor_hash"])
                kwargs["anchor_claim_id"] = str(p.get("anchor_claim_id", "MTR-1"))
            return run_dtsensor1(**kwargs)

        from backend.progress.dtcalib1_convergence_certificate import JOB_KIND as DTCALIB1_KIND, run_certificate as run_dtcalib1
        if payload.get("kind") == DTCALIB1_KIND:
            p = payload
            kwargs = dict(
                seed=int(p.get("seed", 42)),
                n_iterations=int(p.get("n_iterations", 10)),
                initial_drift_pct=float(p.get("initial_drift_pct", 20.0)),
                convergence_rate=float(p.get("convergence_rate", 0.4)),
                convergence_threshold=float(p.get("convergence_threshold", 2.0)),
                noise_scale=float(p.get("noise_scale", 0.1)),
                twin_id=str(p.get("twin_id", "TWIN-001")),
            )
            if p.get("anchor_hash"):
                kwargs["anchor_hash"] = str(p["anchor_hash"])
                kwargs["anchor_claim_id"] = str(p.get("anchor_claim_id", "DRIFT-01"))
            return run_dtcalib1(**kwargs)

        from backend.progress.agent_drift_monitor import JOB_KIND as AGENT_DRIFT01_KIND, run_agent_drift_monitor as run_agent_drift01
        if payload.get("kind") == AGENT_DRIFT01_KIND:
            p = payload
            baseline = {
                "tests_per_phase": float(p.get("baseline_tests_per_phase", 47)),
                "pass_rate": float(p.get("baseline_pass_rate", 1.0)),
                "regressions": int(p.get("baseline_regressions", 0)),
                "verifier_iterations": float(p.get("baseline_verifier_iterations", 1.2)),
            }
            current = {
                "tests_per_phase": float(p.get("current_tests_per_phase", 47)),
                "pass_rate": float(p.get("current_pass_rate", 1.0)),
                "regressions": int(p.get("current_regressions", 0)),
                "verifier_iterations": float(p.get("current_verifier_iterations", 1.2)),
            }
            return run_agent_drift01(
                baseline=baseline,
                current=current,
                drift_threshold_pct=float(p.get("drift_threshold_pct", 20.0)),
            )

        registered = [
            MTR1_KIND, MTR2_KIND, MTR3_KIND,
            SYSID1_KIND, DATAPIPE1_KIND, DRIFT01_KIND,
            MLBENCH1_KIND, DTFEM1_KIND, MLBENCH2_KIND, MLBENCH3_KIND,
            PHARMA1_KIND, FINRISK1_KIND, DTSENSOR1_KIND, DTCALIB1_KIND,
            AGENT_DRIFT01_KIND,
        ]
        raise ValueError(
            f"Unknown job kind: '{payload.get('kind')}'. "
            f"Registered kinds: {registered}"
        )
    
    def _compute_execution_time(self, job: Job) -> float:
        """Compute job execution time in milliseconds."""
        if not job.started_at or not job.completed_at:
            return 0.0
        try:
            from datetime import datetime
            start = datetime.fromisoformat(job.started_at.replace('Z', '+00:00'))
            end = datetime.fromisoformat(job.completed_at.replace('Z', '+00:00'))
            delta = (end - start).total_seconds() * 1000
            return round(delta, 2)
        except:
            return 0.0
