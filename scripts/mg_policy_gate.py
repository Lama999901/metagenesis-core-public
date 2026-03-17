#!/usr/bin/env python3
"""
MetaGenesis Policy Gate

Enforces repository access policies to protect locked phases and critical artifacts.
Pure Python stdlib implementation for maximum portability.

# Part of MetaGenesis Core verification pipeline (MVP v0.2)
Purpose: Prevent unauthorized modifications to locked phases
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from fnmatch import fnmatch
from typing import List, Dict, Any, Set, Tuple


class PolicyViolation(Exception):
    """Raised when policy is violated."""
    pass


class PolicyGate:
    """Policy enforcement engine for MetaGenesis Core repository."""
    
    def __init__(self, policy_path: str):
        """Initialize policy gate with configuration."""
        self.policy_path = policy_path
        self.policy = self._load_policy()
        self.violations: List[str] = []
        
    def _load_policy(self) -> Dict[str, Any]:
        """Load policy configuration from JSON file."""
        try:
            with open(self.policy_path, 'r') as f:
                policy = json.load(f)
            
            # Validate required fields
            required_fields = ['version', 'locked_paths', 'allow_globs']
            for field in required_fields:
                if field not in policy:
                    raise ValueError(f"Missing required field: {field}")
            
            return policy
            
        except FileNotFoundError:
            print(f"ERROR: Policy file not found: {self.policy_path}", file=sys.stderr)
            sys.exit(3)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in policy file: {e}", file=sys.stderr)
            sys.exit(3)
        except Exception as e:
            print(f"ERROR: Failed to load policy: {e}", file=sys.stderr)
            sys.exit(3)
    
    def get_changed_files_git(self, base_ref: str, head_ref: str) -> List[str]:
        """Get list of changed files between two git refs."""
        try:
            # Run git diff to get changed files
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'{base_ref}...{head_ref}'],
                capture_output=True,
                text=True,
                check=True
            )
            
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            return files
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Git diff failed: {e.stderr}", file=sys.stderr)
            sys.exit(3)
        except Exception as e:
            print(f"ERROR: Failed to get changed files: {e}", file=sys.stderr)
            sys.exit(3)
    
    def get_changed_files_list(self, files_str: str) -> List[str]:
        """Parse comma-separated file list."""
        return [f.strip() for f in files_str.split(',') if f.strip()]
    
    def matches_pattern(self, filepath: str, pattern: str) -> bool:
        """Check if filepath matches glob pattern."""
        # Support both direct match and directory prefix match
        if fnmatch(filepath, pattern):
            return True
        # Check if file is under a directory pattern (e.g., backend/vision/** matches backend/vision/ingest.py)
        if pattern.endswith('/**'):
            prefix = pattern[:-3]  # Remove /**
            if filepath.startswith(prefix + '/'):
                return True
        return False
    
    def check_locked_paths(self, files: List[str]) -> List[Tuple[str, str]]:
        """Check if any files are in locked paths (HARD BLOCK)."""
        violations = []
        locked_patterns = self.policy.get('locked_paths', [])
        
        for filepath in files:
            for pattern in locked_patterns:
                if self.matches_pattern(filepath, pattern):
                    violations.append((filepath, pattern))
                    break  # One violation per file is enough
        
        return violations
    
    def check_allowlist(self, files: List[str]) -> List[str]:
        """Check if all files match at least one allow pattern."""
        violations = []
        allow_patterns = self.policy.get('allow_globs', [])
        
        for filepath in files:
            # Check if file matches any allow pattern
            allowed = False
            for pattern in allow_patterns:
                if self.matches_pattern(filepath, pattern):
                    allowed = True
                    break
            
            if not allowed:
                violations.append(filepath)
        
        return violations
    
    def enforce(self, files: List[str]) -> bool:
        """Enforce policy on list of files. Returns True if passed."""
        if not files:
            print("INFO: No files changed, policy gate passed.")
            return True
        
        print(f"\n{'='*80}")
        print("MetaGenesis Policy Gate")
        print(f"{'='*80}")
        print(f"Policy Version: {self.policy.get('version', 'unknown')}")
        print(f"Changed Files: {len(files)}")
        print(f"{'='*80}\n")
        
        # Check locked paths (HARD BLOCK)
        locked_violations = self.check_locked_paths(files)
        
        # Check allowlist
        allowlist_violations = self.check_allowlist(files)
        
        # Report results
        print("CHANGED FILES:")
        for f in files:
            print(f"  - {f}")
        print()
        
        # Report locked path violations
        if locked_violations:
            print("❌ LOCKED PATH VIOLATIONS (HARD BLOCK):")
            for filepath, pattern in locked_violations:
                print(f"  ✗ {filepath}")
                print(f"    Matched locked pattern: {pattern}")
            print()
        
        # Report allowlist violations
        if allowlist_violations:
            print("❌ ALLOWLIST VIOLATIONS:")
            for filepath in allowlist_violations:
                print(f"  ✗ {filepath}")
                print(f"    Does not match any allowed pattern")
            print()
            print("ALLOWED PATTERNS:")
            for pattern in self.policy.get('allow_globs', []):
                print(f"  - {pattern}")
            print()
        
        # Determine overall result
        has_violations = bool(locked_violations or allowlist_violations)
        
        if has_violations:
            print(f"{'='*80}")
            print("POLICY GATE: ❌ FAILED")
            print(f"{'='*80}")
            print(f"Locked path violations: {len(locked_violations)}")
            print(f"Allowlist violations: {len(allowlist_violations)}")
            print("\nREASON: Policy violations detected. See details above.")
            print("\nTO FIX:")
            if locked_violations:
                print("  1. Do NOT modify locked phase artifacts")
                print("  2. Review locked_paths in policy configuration")
            if allowlist_violations:
                print("  3. Ensure changes are in allowed directories")
                print("  4. Update policy if new directories need access")
            print()
            return False
        else:
            print(f"{'='*80}")
            print("POLICY GATE: ✅ PASSED")
            print(f"{'='*80}")
            print("All changed files comply with repository policy.")
            print()
            return True


def main():
    """Main entry point for policy gate CLI."""
    parser = argparse.ArgumentParser(
        description='MetaGenesis Policy Gate - Repository access control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check PR changes
  %(prog)s --policy policy.json --base origin/main --head HEAD
  
  # Check specific files (unit testing)
  %(prog)s --policy policy.json --files "file1.py,file2.md"
  
  # Use default policy location
  %(prog)s --base origin/main --head HEAD
'''
    )
    
    parser.add_argument(
        '--policy',
        default='scripts/mg_policy_gate_policy.json',
        help='Path to policy configuration JSON (default: scripts/mg_policy_gate_policy.json)'
    )
    
    # Git mode
    parser.add_argument(
        '--base',
        help='Base git ref for comparison (e.g., origin/main)'
    )
    parser.add_argument(
        '--head',
        help='Head git ref for comparison (e.g., HEAD)'
    )
    
    # File list mode (for testing)
    parser.add_argument(
        '--files',
        help='Comma-separated list of files to check (alternative to git mode)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.files:
        if args.base or args.head:
            print("ERROR: Cannot use --files with --base/--head", file=sys.stderr)
            sys.exit(3)
    else:
        if not (args.base and args.head):
            print("ERROR: Must provide either --files OR both --base and --head", file=sys.stderr)
            sys.exit(3)
    
    # Initialize policy gate
    gate = PolicyGate(args.policy)
    
    # Get changed files
    if args.files:
        changed_files = gate.get_changed_files_list(args.files)
    else:
        changed_files = gate.get_changed_files_git(args.base, args.head)
    
    # Enforce policy
    passed = gate.enforce(changed_files)
    
    # Exit with appropriate code
    if passed:
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
