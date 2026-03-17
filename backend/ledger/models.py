#!/usr/bin/env python3
"""
Ledger Entry Models - Minimal Traceability Schema (Pure Stdlib)

Purpose: Dataclass models for append-only ledger entries
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
Implementation: Pure Python stdlib (no external dependencies)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from datetime import datetime
import re


def validate_sha256(sha256_hash: str) -> str:
    """Validate and normalize SHA-256 hash.
    
    Args:
        sha256_hash: Hash string to validate
        
    Returns:
        Normalized lowercase hash
        
    Raises:
        ValueError: If hash format invalid
    """
    if not sha256_hash or not isinstance(sha256_hash, str):
        raise ValueError("SHA-256 hash must be non-empty string")
    
    if not re.match(r'^[a-fA-F0-9]{64}$', sha256_hash):
        raise ValueError(f"Invalid SHA-256 hash format: {sha256_hash} (must be 64 hex chars)")
    
    return sha256_hash.lower()


def validate_iso8601(timestamp: str) -> str:
    """Validate ISO8601 timestamp format.
    
    Args:
        timestamp: ISO8601 timestamp string
        
    Returns:
        Original timestamp if valid
        
    Raises:
        ValueError: If timestamp invalid
    """
    if not timestamp or not isinstance(timestamp, str):
        raise ValueError("Timestamp must be non-empty string")
    
    try:
        # Parse ISO8601 (handle 'Z' timezone)
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return timestamp
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid ISO8601 timestamp: {timestamp} ({e})")


@dataclass
class ArtifactReference:
    """Reference to a file artifact with hash verification."""
    
    path: str
    sha256: str
    optional: bool = False
    note: Optional[str] = None
    
    def __post_init__(self):
        """Validate fields after initialization."""
        # Validate path
        if not self.path or not self.path.strip():
            raise ValueError("Artifact path cannot be empty")
        self.path = self.path.strip()
        
        # Validate and normalize SHA-256
        self.sha256 = validate_sha256(self.sha256)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class LedgerEntry:
    """Append-only ledger entry for phase execution traceability."""
    
    trace_id: str
    created_at: str
    phase: int
    actor: str
    action: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[ArtifactReference] = field(default_factory=list)
    legal_sig_refs: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate fields after initialization."""
        # Validate trace_id
        if not self.trace_id or not self.trace_id.strip():
            raise ValueError("trace_id cannot be empty")
        self.trace_id = self.trace_id.strip()
        
        # Validate ISO8601 timestamp
        self.created_at = validate_iso8601(self.created_at)
        
        # Validate phase range
        if not isinstance(self.phase, int):
            raise ValueError(f"phase must be integer, got {type(self.phase)}")
        if self.phase < 0 or self.phase > 999:
            raise ValueError(f"phase must be 0-999, got {self.phase}")
        
        # Validate actor
        if not self.actor or not self.actor.strip():
            raise ValueError("actor cannot be empty")
        self.actor = self.actor.strip()
        
        # Validate action
        if not self.action or not self.action.strip():
            raise ValueError("action cannot be empty")
        self.action = self.action.strip()
        
        # Validate artifacts (if provided as dicts, convert to ArtifactReference)
        if self.artifacts:
            validated_artifacts = []
            for artifact in self.artifacts:
                if isinstance(artifact, dict):
                    validated_artifacts.append(ArtifactReference(**artifact))
                elif isinstance(artifact, ArtifactReference):
                    validated_artifacts.append(artifact)
                else:
                    raise ValueError(f"Invalid artifact type: {type(artifact)}")
            self.artifacts = validated_artifacts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            'trace_id': self.trace_id,
            'created_at': self.created_at,
            'phase': self.phase,
            'actor': self.actor,
            'action': self.action,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'artifacts': [a.to_dict() if hasattr(a, 'to_dict') else asdict(a) for a in self.artifacts],
            'legal_sig_refs': self.legal_sig_refs,
            'meta': self.meta
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LedgerEntry':
        """Create LedgerEntry from dictionary.
        
        Args:
            data: Dictionary with entry data
            
        Returns:
            LedgerEntry instance
        """
        # Convert artifact dicts to ArtifactReference objects
        artifacts = data.get('artifacts', [])
        if artifacts:
            artifact_objs = []
            for a in artifacts:
                if isinstance(a, dict):
                    artifact_objs.append(ArtifactReference(**a))
                else:
                    artifact_objs.append(a)
            data['artifacts'] = artifact_objs
        
        return cls(**data)
