#!/usr/bin/env python3
"""
Runner error path tests (ERR-01, ERR-02, ERR-03).

Tests that ProgressRunner handles bad input gracefully:
  - Unknown JOB_KIND -> clear ValueError with registered kinds
  - None/empty/wrong-type payload -> does not crash
  - Mid-computation exception -> FAILED status + error message
  - _hash_step with non-serializable inputs -> TypeError/ValueError (defense-in-depth)
"""
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.progress.runner import ProgressRunner
from backend.progress.models import Job, JobStatus


def _make_job(payload, job_id="test-err", trace_id="trace-err"):
    """Create a minimal Job for error path testing."""
    return Job(
        job_id=job_id,
        trace_id=trace_id,
        created_at="2026-01-01T00:00:00Z",
        status=JobStatus.RUNNING,
        payload=payload,
    )


def _make_runner():
    """Create ProgressRunner with mocked stores."""
    return ProgressRunner(MagicMock(), MagicMock())


class TestRunnerErrorPaths:
    """ERR-01: Unknown JOB_KIND error handling."""

    def test_unknown_job_kind_raises_value_error(self):
        runner = _make_runner()
        job = _make_job({"kind": "nonexistent_xyz_999"})
        with pytest.raises(ValueError, match="Unknown job kind"):
            runner._execute_job_logic(job)

    def test_unknown_job_kind_lists_registered(self):
        runner = _make_runner()
        job = _make_job({"kind": "nonexistent_xyz_999"})
        with pytest.raises(ValueError, match="Registered kinds"):
            runner._execute_job_logic(job)


class TestRunnerBadPayload:
    """ERR-03: None/empty/wrong-type input handling."""

    def test_none_payload_raises(self):
        runner = _make_runner()
        job = _make_job(None)
        with pytest.raises((ValueError, TypeError, AttributeError)):
            runner._execute_job_logic(job)

    def test_empty_payload_raises(self):
        runner = _make_runner()
        job = _make_job({})
        with pytest.raises(ValueError, match="Unknown job kind"):
            runner._execute_job_logic(job)

    def test_wrong_type_payload_raises(self):
        runner = _make_runner()
        job = _make_job("not_a_dict")
        with pytest.raises((ValueError, TypeError, AttributeError)):
            runner._execute_job_logic(job)

    def test_missing_kind_key_raises(self):
        runner = _make_runner()
        job = _make_job({"data": "something", "no_kind_here": True})
        with pytest.raises(ValueError, match="Unknown job kind"):
            runner._execute_job_logic(job)


class TestRunnerMidComputationException:
    """ERR-02: Mid-computation exception handling."""

    def test_mid_computation_exception_sets_failed(self):
        """run_job catches _execute_job_logic exceptions, sets FAILED status."""
        runner = _make_runner()
        # Configure mock job_store to return a proper Job
        job = _make_job({"kind": "mtr1_calibration"})
        job.status = JobStatus.QUEUED
        runner.job_store.get.return_value = job

        # Patch _execute_job_logic to raise
        with patch.object(runner, '_execute_job_logic',
                          side_effect=RuntimeError("simulated computation crash")):
            result = runner.run_job("test-err")

        assert result.status == JobStatus.FAILED
        assert "simulated computation crash" in result.error


class TestHashStepNonSerializable:
    """Defense-in-depth: _hash_step rejects non-JSON-serializable step_data.

    Per user decision: test _hash_step with datetime, set, and circular ref
    to verify it raises TypeError or ValueError (json.JSONEncodeError is a
    subclass of ValueError).

    Uses _hash_step from mlbench1_accuracy_certificate (module-level, importable).
    """

    @pytest.fixture
    def hash_step(self):
        from backend.progress.mlbench1_accuracy_certificate import _hash_step
        return _hash_step

    def test_hash_step_datetime_raises(self, hash_step):
        """datetime object is not JSON-serializable -> TypeError."""
        with pytest.raises(TypeError):
            hash_step("test_step", {"timestamp": datetime(2026, 1, 1)}, "genesis")

    def test_hash_step_set_raises(self, hash_step):
        """set object is not JSON-serializable -> TypeError."""
        with pytest.raises(TypeError):
            hash_step("test_step", {"tags": {"a", "b", "c"}}, "genesis")

    def test_hash_step_circular_ref_raises(self, hash_step):
        """Circular reference -> ValueError (json raises ValueError for circular refs)."""
        circular = {}
        circular["self"] = circular
        with pytest.raises(ValueError):
            hash_step("test_step", circular, "genesis")
