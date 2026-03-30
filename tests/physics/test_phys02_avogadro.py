#!/usr/bin/env python3
"""
PHYS-02 Avogadro Constant Chemistry Verification - Tests.

Purpose: pass/fail/determinism proof for NA = 6.02214076e23 mol^-1 (SI 2019).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.progress.phys02_avogadro import run_verification, AVOGADRO_N


class TestPhys02Avogadro:
    """PHYS-02 Avogadro constant verification: pass, fail, determinism."""

    def test_pass(self):
        """Default run should pass with rel_err <= 1e-8."""
        out = run_verification()
        assert out["mtr_phase"] == "PHYS-02"
        assert out["result"]["pass"] is True
        assert out["result"]["rel_err"] <= 1e-8
        assert "execution_trace" in out
        assert "trace_root_hash" in out

    def test_fail(self):
        """Patching AVOGADRO_N to wrong value should fail."""
        with patch("backend.progress.phys02_avogadro.AVOGADRO_N", 1.0e23):
            out = run_verification()
        assert out["result"]["pass"] is False

    def test_determinism(self):
        """Two runs must produce same trace_root_hash."""
        out1 = run_verification()
        out2 = run_verification()
        assert out1["trace_root_hash"] == out2["trace_root_hash"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
