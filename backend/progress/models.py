#!/usr/bin/env python3
"""
Progress Engine Models - Job Lifecycle Management

Purpose: Dataclass models for job scheduling and execution
# Part of MetaGenesis Core verification pipeline (MVP v0.1)
Implementation: Pure stdlib with ledger integration
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid


class JobStatus(Enum):
    """Job execution status."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass
class Job:
    """Job execution record with traceability."""
    
    job_id: str
    trace_id: str
    created_at: str
    status: JobStatus
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate and normalize fields."""
        # Ensure status is enum
        if isinstance(self.status, str):
            self.status = JobStatus(self.status)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'job_id': self.job_id,
            'trace_id': self.trace_id,
            'created_at': self.created_at,
            'status': self.status.value,
            'payload': self.payload,
            'error': self.error,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'result': self.result
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create Job from dictionary."""
        return cls(**data)


def generate_job_id() -> str:
    """Generate unique job ID."""
    return f"job_{uuid.uuid4().hex[:16]}"


def generate_trace_id() -> str:
    """Generate unique trace ID for ledger."""
    return f"trace_{uuid.uuid4().hex[:16]}"


def now_iso8601() -> str:
    """Get current timestamp in ISO8601 format."""
    return datetime.now(timezone.utc).isoformat()
