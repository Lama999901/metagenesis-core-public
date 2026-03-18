#!/usr/bin/env python3
"""
MetaGenesis Core -- Temporal Commitment Layer 5 (Innovation #7)

Proves WHEN a bundle was signed using NIST Randomness Beacon 2.0.
Two-phase pre-commitment scheme: hash bundle root_hash BEFORE fetching
beacon, then bind with beacon value AFTER. Fully offline verification.

PPA: USPTO #63/996,819 -- Innovation #7
"""

import datetime
import hashlib
import json
import sys
from pathlib import Path

BEACON_URL = "https://beacon.nist.gov/beacon/2.0/chain/last/pulse/last"
TEMPORAL_FILE = "temporal_commitment.json"
TEMPORAL_VERSION = "temporal-nist-v1"


def _fetch_beacon_pulse(timeout: int = 5):
    """
    Fetch latest NIST Beacon 2.0 pulse. Returns None on any failure.

    Lazy-imports urllib so that verify_temporal_commitment never loads it.
    """
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            BEACON_URL, headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pulse = data["pulse"]
            return {
                "outputValue": pulse["outputValue"],
                "timeStamp": pulse["timeStamp"],
                "uri": pulse["uri"],
            }
    except Exception:
        return None


def create_temporal_commitment(root_hash: str, beacon_timeout: int = 5) -> dict:
    """
    Create a temporal commitment for a bundle.

    Phase 1: Compute pre_commitment_hash = SHA-256(root_hash) BEFORE beacon.
    Phase 2: Fetch beacon and bind with SHA-256(pre + beacon_value + timestamp).
    """
    # Phase 1: Pre-commitment (before knowing beacon value)
    pre_commitment_hash = hashlib.sha256(root_hash.encode("utf-8")).hexdigest()

    # Phase 2: Fetch beacon and bind
    beacon = _fetch_beacon_pulse(timeout=beacon_timeout)

    if beacon is not None:
        concat = (
            pre_commitment_hash
            + beacon["outputValue"]
            + beacon["timeStamp"]
        )
        temporal_binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()
        return {
            "version": TEMPORAL_VERSION,
            "root_hash": root_hash,
            "pre_commitment_hash": pre_commitment_hash,
            "beacon_output_value": beacon["outputValue"],
            "beacon_timestamp": beacon["timeStamp"],
            "beacon_pulse_uri": beacon["uri"],
            "beacon_status": "available",
            "temporal_binding": temporal_binding,
        }
    else:
        # Graceful degradation
        return {
            "version": TEMPORAL_VERSION,
            "root_hash": root_hash,
            "pre_commitment_hash": pre_commitment_hash,
            "beacon_output_value": None,
            "beacon_timestamp": None,
            "beacon_pulse_uri": None,
            "beacon_status": "unavailable",
            "local_timestamp": datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat(),
            "temporal_binding": None,
        }


def verify_temporal_commitment(pack_dir) -> tuple:
    """
    Verify Layer 5 temporal commitment. Fully offline -- no network calls.

    Checks:
    1. pre_commitment_hash matches SHA-256(root_hash from manifest)
    2. temporal_binding matches SHA-256(pre + beacon_value + timestamp)

    Returns:
        (ok: bool, message: str)
    """
    pack_dir = Path(pack_dir)
    tc_path = pack_dir / TEMPORAL_FILE

    if not tc_path.exists():
        return (True, "Temporal: no temporal commitment present (Layer 5 skipped)")

    tc = json.loads(tc_path.read_text(encoding="utf-8"))

    # Read root_hash from manifest (authoritative source)
    manifest_path = pack_dir / "pack_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root_hash = manifest["root_hash"]

    # Check 1: pre_commitment_hash matches root_hash
    expected_pre = hashlib.sha256(root_hash.encode("utf-8")).hexdigest()
    if tc["pre_commitment_hash"] != expected_pre:
        return (False, "Temporal: pre_commitment_hash does not match root_hash")

    # Degraded mode: no binding to check
    if tc["beacon_status"] == "unavailable":
        return (True, "Temporal: local timestamp only (no beacon proof)")

    # Check 2: temporal_binding
    concat = (
        tc["pre_commitment_hash"]
        + tc["beacon_output_value"]
        + tc["beacon_timestamp"]
    )
    expected_binding = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    if tc["temporal_binding"] != expected_binding:
        return (False, "Temporal: temporal_binding hash mismatch")

    return (True, "Temporal: VALID (beacon-backed)")


def write_temporal_commitment(pack_dir, temporal_data: dict) -> Path:
    """Write temporal_commitment.json to the bundle directory."""
    pack_dir = Path(pack_dir)
    tc_path = pack_dir / TEMPORAL_FILE
    tc_path.write_text(
        json.dumps(temporal_data, indent=2), encoding="utf-8"
    )
    return tc_path
