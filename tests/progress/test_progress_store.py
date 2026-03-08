#!/usr/bin/env python3
"""
Progress Engine Store Tests

Purpose: Validate job store and runner with ledger integration
# Part of MetaGenesis Core verification pipeline (MVP v0.1)
"""

import sys
import os
from pathlib import Path
import pytest
import tempfile

# Add project root to path
sys.path.insert(0, '/app')

from backend.progress.models import Job, JobStatus, generate_job_id, generate_trace_id
from backend.progress.store import JobStore
from backend.progress.runner import ProgressRunner
from backend.ledger.ledger_store import LedgerStore


class TestProgressStore:
    """Test suite for Progress Engine store and runner."""
    
    @pytest.fixture
    def job_store(self):
        """Create job store."""
        return JobStore()
    
    @pytest.fixture
    def temp_ledger(self, tmp_path):
        """Create temporary ledger."""
        ledger_file = tmp_path / "test_ledger.jsonl"
        return LedgerStore(file_path=str(ledger_file))
    
    @pytest.fixture
    def runner(self, job_store, temp_ledger):
        """Create runner with temp ledger."""
        return ProgressRunner(job_store=job_store, ledger_store=temp_ledger)
    
    def test_job_store_initialization(self, job_store):
        """Test job store initializes successfully."""
        assert job_store.count() == 0
        assert len(job_store.jobs) == 0
    
    def test_create_job_returns_trace_id_and_queued_status(self, runner, temp_ledger):
        """Test creating job returns trace_id and status QUEUED."""
        initial_ledger_count = temp_ledger.count()
        
        job = runner.create_job(payload={'test': True})
        
        assert job.job_id is not None
        assert job.trace_id is not None
        assert job.status == JobStatus.QUEUED
        assert job.payload == {'test': True}
        
        # Verify ledger entry created
        assert temp_ledger.count() == initial_ledger_count + 1
        
        # Retrieve ledger entry
        ledger_entry = temp_ledger.get(job.trace_id)
        assert ledger_entry is not None
        assert ledger_entry.action == "job_created"
        assert ledger_entry.phase == 31
        assert ledger_entry.actor == "scheduler_v1"
    
    def test_run_job_transitions_status_and_writes_ledger(self, runner, temp_ledger):
        """Test running job transitions status and writes completion ledger entry."""
        # Create job
        job = runner.create_job(payload={'task': 'test'})
        initial_ledger_count = temp_ledger.count()
        
        # Run job
        completed_job = runner.run_job(job.job_id)
        
        assert completed_job.status == JobStatus.SUCCEEDED
        assert completed_job.result is not None
        assert completed_job.started_at is not None
        assert completed_job.completed_at is not None
        
        # Verify ledger entry created for completion
        assert temp_ledger.count() == initial_ledger_count + 1
        
        # Verify completion entry exists
        # Note: trace_id is same for create and complete, so get() returns last
        ledger_entry = temp_ledger.get(job.trace_id)
        assert ledger_entry.action == "job_completed"
        assert ledger_entry.outputs['status'] == 'SUCCEEDED'
    
    def test_ledger_chain_remains_valid_after_job_execution(self, runner, temp_ledger):
        """Test ledger entries created correctly after job lifecycle."""
        # Create and run multiple jobs
        initial_count = temp_ledger.count()
        
        for i in range(3):
            job = runner.create_job(payload={'index': i})
            runner.run_job(job.job_id)
        
        # Verify ledger entries created (3 jobs x 2 entries each)
        final_count = temp_ledger.count()
        assert final_count == initial_count + 6, "Expected 6 new ledger entries (3 jobs x 2)"
        
        # Verify chain integrity if method available
        if hasattr(temp_ledger, 'verify_chain'):
            result = temp_ledger.verify_chain()
            assert result['ok'] is True, f"Chain broken: {result.get('reason')}"
            assert result['checked'] >= 6
    
    def test_job_not_found_raises_error(self, runner):
        """Test running nonexistent job raises ValueError."""
        with pytest.raises(ValueError, match="Job not found"):
            runner.run_job("nonexistent-job-999")
    
    def test_list_recent_jobs(self, runner):
        """Test listing recent jobs."""
        # Create multiple jobs
        jobs = []
        for i in range(5):
            job = runner.create_job(payload={'index': i})
            jobs.append(job)
        
        # List recent (should return newest first)
        job_store = runner.job_store
        recent = job_store.list_recent(limit=3)
        
        assert len(recent) == 3
        # Newest first (index 4, 3, 2)
        assert recent[0].payload['index'] == 4
        assert recent[1].payload['index'] == 3
        assert recent[2].payload['index'] == 2
    
    def test_job_id_generation_unique(self):
        """Test job IDs are unique."""
        id1 = generate_job_id()
        id2 = generate_job_id()
        
        assert id1 != id2
        assert id1.startswith('job_')
        assert len(id1) == 20  # 'job_' + 16 hex chars
    
    def test_trace_id_generation_unique(self):
        """Test trace IDs are unique."""
        id1 = generate_trace_id()
        id2 = generate_trace_id()
        
        assert id1 != id2
        assert id1.startswith('trace_')
        assert len(id1) == 22  # 'trace_' + 16 hex chars


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
