#!/usr/bin/env python3
"""
PHYS-01 Boltzmann Constant Thermodynamics Verification - Tests.

Purpose: pass/fail/determinism proof for kB = 1.380649e-23 J/K (SI 2019).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.progress.phys01_boltzmann import run_verification, BOLTZMANN_K


class TestPhys01Boltzmann:
    """PHYS-01 Boltzmann constant verification: pass, fail, determinism."""

    def test_pass(self):
        """Default T=300.0 should pass with rel_err <= 1e-9."""
        out = run_verification(T=300.0)
        assert out["mtr_phase"] == "PHYS-01"
        assert out["result"]["pass"] is True
        assert out["result"]["rel_err"] <= 1e-9
        assert "execution_trace" in out
        assert "trace_root_hash" in out

    def test_fail(self):
        """Patching BOLTZMANN_K to wrong value should fail."""
        with patch("backend.progress.phys01_boltzmann.BOLTZMANN_K", 1.0e-23):
            out = run_verification(T=300.0)
        assert out["result"]["pass"] is False

    def test_determinism(self):
        """Two runs with same input must produce same trace_root_hash."""
        out1 = run_verification(T=300.0)
        out2 = run_verification(T=300.0)
        assert out1["trace_root_hash"] == out2["trace_root_hash"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
