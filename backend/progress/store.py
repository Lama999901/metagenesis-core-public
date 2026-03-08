#!/usr/bin/env python3
"""
Progress Engine Store - In-Memory Job Storage

Purpose: Simple in-memory job store for v1 (no persistence)
# Part of MetaGenesis Core verification pipeline (MVP v0.1)
Implementation: Dict + list for deterministic ordering
"""

from typing import Dict, List, Optional
import logging

from .models import Job, JobStatus

logger = logging.getLogger(__name__)


class JobStore:
    """In-memory job storage with ordering."""
    
    def __init__(self):
        """Initialize job store."""
        self.jobs: Dict[str, Job] = {}
        self.job_order: List[str] = []  # Maintains insertion order
        logger.info("JobStore initialized (in-memory)")
    
    def create(self, job: Job) -> Job:
        """Store a new job.
        
        Args:
            job: Job to store
            
        Returns:
            Stored job
        """
        if job.job_id in self.jobs:
            logger.warning(f"Job {job.job_id} already exists, updating")
        else:
            self.job_order.append(job.job_id)
        
        self.jobs[job.job_id] = job
        logger.info(f"Job created: {job.job_id} (trace={job.trace_id})")
        return job
    
    def get(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job if found, None otherwise
        """
        return self.jobs.get(job_id)
    
    def update(self, job: Job) -> Job:
        """Update existing job.
        
        Args:
            job: Updated job
            
        Returns:
            Updated job
        """
        self.jobs[job.job_id] = job
        logger.info(f"Job updated: {job.job_id} (status={job.status.value})")
        return job
    
    def list_recent(self, limit: int = 50) -> List[Job]:
        """List recent jobs (newest first).
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs (newest first)
        """
        # Get last N job IDs
        recent_ids = self.job_order[-limit:] if len(self.job_order) > limit else self.job_order
        
        # Return jobs in reverse order (newest first)
        return [self.jobs[job_id] for job_id in reversed(recent_ids) if job_id in self.jobs]
    
    def count(self) -> int:
        """Count total jobs.
        
        Returns:
            Total number of jobs
        """
        return len(self.jobs)
