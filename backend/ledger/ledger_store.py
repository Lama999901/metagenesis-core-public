#!/usr/bin/env python3
"""
Ledger Store - Append-Only JSONL Storage (Pure Stdlib)

Purpose: Persistent storage for ledger entries with deterministic writes
# Part of MetaGenesis Core verification pipeline (MVP v0.2)
Storage Format: JSON Lines (one entry per line)
Implementation: Pure Python stdlib with portable file locking
"""

import json
import os
import platform
from pathlib import Path
from typing import Optional, List
import logging

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
    logging.warning("fcntl not available (non-POSIX system) - file locking disabled")

from .models import LedgerEntry

logger = logging.getLogger(__name__)


class LedgerStore:
    """Append-only ledger storage with optional file locking."""
    
    def __init__(self, file_path: str = "reports/ledger_v1.jsonl"):
        """Initialize ledger store.
        
        Args:
            file_path: Path to JSONL ledger file
        """
        self.file_path = Path(file_path)
        self.use_locking = HAS_FCNTL
        self._ensure_file_exists()
        
        if not self.use_locking:
            logger.warning(
                f"File locking unavailable on {platform.system()} - "
                "ledger is single-process safe only"
            )
        
        logger.info(f"LedgerStore initialized: {self.file_path} (locking={'enabled' if self.use_locking else 'disabled'})")
    
    def _ensure_file_exists(self):
        """Ensure ledger file and parent directories exist."""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self.file_path.touch()
            logger.info(f"Created ledger file: {self.file_path}")
    
    def append(self, entry: LedgerEntry) -> None:
        """Append entry to ledger with optional file locking.
        
        Args:
            entry: LedgerEntry to append
            
        Raises:
            IOError: If file write fails
        """
        try:
            # Convert to dict and serialize deterministically
            entry_dict = entry.to_dict()
            entry_json = json.dumps(entry_dict, sort_keys=True, separators=(',', ':'))
            
            # Append with optional file lock
            with open(self.file_path, 'a') as f:
                if self.use_locking:
                    try:
                        # Acquire exclusive lock (POSIX only)
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        f.write(entry_json + '\n')
                        f.flush()
                        os.fsync(f.fileno())  # Ensure written to disk
                    finally:
                        # Release lock
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                else:
                    # No locking - single-process safe only
                    f.write(entry_json + '\n')
                    f.flush()
            
            logger.info(f"Ledger entry appended: {entry.trace_id}")
            
        except Exception as e:
            logger.error(f"Failed to append ledger entry: {e}")
            raise
    
    def get(self, trace_id: str) -> Optional[LedgerEntry]:
        """Retrieve entry by trace_id (returns last occurrence).
        
        Args:
            trace_id: Trace identifier to search for
            
        Returns:
            LedgerEntry if found, None otherwise
        """
        if not self.file_path.exists():
            return None
        
        try:
            # Read file and search for last matching entry
            last_match = None
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry_dict = json.loads(line)
                        if entry_dict.get('trace_id') == trace_id:
                            last_match = LedgerEntry.from_dict(entry_dict)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping invalid ledger line: {e}")
                        continue
            
            return last_match
            
        except Exception as e:
            logger.error(f"Failed to read ledger: {e}")
            return None
    
    def list_recent(self, limit: int = 50) -> List[LedgerEntry]:
        """List recent ledger entries (newest first).
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of LedgerEntry objects (newest first)
        """
        if not self.file_path.exists():
            return []
        
        try:
            entries = []
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        entry_dict = json.loads(line)
                        entries.append(LedgerEntry.from_dict(entry_dict))
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping invalid ledger line: {e}")
                        continue
            
            # Return newest first (last entries in file)
            return entries[-limit:] if len(entries) > limit else entries
            
        except Exception as e:
            logger.error(f"Failed to list ledger entries: {e}")
            return []
    
    def count(self) -> int:
        """Count total ledger entries.
        
        Returns:
            Total number of valid entries in ledger
        """
        if not self.file_path.exists():
            return 0
        
        try:
            count = 0
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            json.loads(line)
                            count += 1
                        except json.JSONDecodeError:
                            continue
            return count
            
        except Exception as e:
            logger.error(f"Failed to count ledger entries: {e}")
            return 0
