"""
Tests for scripts/mg_self_audit.py -- Protocol Self-Audit (Recursive Integrity Verifier)
========================================================================================
Covers: tamper detection, signature validation, --update workflow,
missing baseline, missing core file, --init, baseline structure,
all 8 scripts listed, edge cases.
"""

import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Import the module under test
sys.path.insert(0, str(SCRIPTS_DIR))
import mg_self_audit
import mg_ed25519


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_baseline(tmp_path, monkeypatch):
    """Set up a temporary baseline environment."""
    # Create fake script files
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    for name in ["mg.py", "steward_audit.py", "agent_evolution.py",
                  "check_stale_docs.py", "mg_ed25519.py", "mg_sign.py",
                  "mg_client.py", "agent_pilot.py"]:
        (scripts_dir / name).write_text(f"# fake {name}\nprint('hello')\n", encoding="utf-8")

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    # Generate a key pair
    private_seed, public_key = mg_ed25519.generate_keypair()
    key_data = {
        "version": "ed25519-v1",
        "private_key_hex": private_seed.hex(),
        "public_key_hex": public_key.hex(),
        "fingerprint": hashlib.sha256(public_key).hexdigest(),
    }
    key_path = tmp_path / "signing_key.json"
    key_path.write_text(json.dumps(key_data, indent=2), encoding="utf-8")

    # Patch module-level constants
    monkeypatch.setattr(mg_self_audit, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(mg_self_audit, "BASELINE_PATH", reports_dir / "core_integrity.json")
    monkeypatch.setattr(mg_self_audit, "KEY_PATH", key_path)

    return tmp_path


@pytest.fixture
def initialized_baseline(tmp_baseline):
    """Create an initialized baseline."""
    rc = mg_self_audit.cmd_init()
    assert rc == 0
    return tmp_baseline


# ── Test 1: --init creates valid baseline ────────────────────────────────────

def test_init_creates_baseline(tmp_baseline):
    """SELF-01: --init creates reports/core_integrity.json with valid structure."""
    rc = mg_self_audit.cmd_init()
    assert rc == 0

    baseline_path = tmp_baseline / "reports" / "core_integrity.json"
    assert baseline_path.exists()

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert baseline["version"] == "1.0"
    assert "created" in baseline
    assert "updated" in baseline
    assert "scripts" in baseline
    assert "signature" in baseline
    assert "public_key" in baseline


# ── Test 2: Baseline JSON structure validation ───────────────────────────────

def test_baseline_structure(initialized_baseline):
    """Baseline has correct JSON schema with all required fields."""
    baseline_path = initialized_baseline / "reports" / "core_integrity.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    # Check all required top-level keys
    required = {"version", "created", "updated", "scripts", "signature", "public_key"}
    assert required.issubset(set(baseline.keys()))

    # Each script entry has hash and size
    for rel_path, entry in baseline["scripts"].items():
        assert "hash" in entry, f"Missing hash for {rel_path}"
        assert "size" in entry, f"Missing size for {rel_path}"
        assert isinstance(entry["hash"], str)
        assert isinstance(entry["size"], int)
        assert len(entry["hash"]) == 64  # SHA-256 hex digest


# ── Test 3: All 8 scripts listed ────────────────────────────────────────────

def test_all_eight_scripts_listed(initialized_baseline):
    """All 8 core scripts appear in the baseline."""
    baseline_path = initialized_baseline / "reports" / "core_integrity.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    expected = set(mg_self_audit.CORE_SCRIPTS)
    actual = set(baseline["scripts"].keys())
    assert expected == actual, f"Mismatch: expected {expected}, got {actual}"
    assert len(actual) == 8


# ── Test 4: Verify PASS when no changes ─────────────────────────────────────

def test_verify_pass_no_changes(initialized_baseline, capsys):
    """Verify mode returns 0 and PASS when nothing changed."""
    rc = mg_self_audit.cmd_verify()
    assert rc == 0
    out = capsys.readouterr().out
    assert "SELF-AUDIT PASS" in out
    assert "8 scripts verified" in out


# ── Test 5: Tamper detection (modify script -> FAIL) ────────────────────────

def test_tamper_detection(initialized_baseline, capsys):
    """SELF-02: Modifying a core script is detected as FAIL."""
    # Tamper with mg.py
    mg_path = initialized_baseline / "scripts" / "mg.py"
    mg_path.write_text("# TAMPERED CONTENT\nprint('hacked')\n", encoding="utf-8")

    rc = mg_self_audit.cmd_verify()
    assert rc == 1
    out = capsys.readouterr().out
    assert "SELF-AUDIT FAIL" in out
    assert "scripts/mg.py" in out
    assert "hash mismatch" in out
    assert "Expected:" in out
    assert "Found:" in out


# ── Test 6: Signature validation (break sig -> FAIL) ────────────────────────

def test_broken_signature_fails(initialized_baseline, capsys):
    """Breaking the Ed25519 signature causes verification to fail."""
    baseline_path = initialized_baseline / "reports" / "core_integrity.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    # Corrupt the signature
    sig = baseline["signature"]
    # Flip some characters
    corrupted = sig[:10] + "0" * 10 + sig[20:]
    baseline["signature"] = corrupted
    baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")

    rc = mg_self_audit.cmd_verify()
    assert rc == 1
    out = capsys.readouterr().out
    assert "SELF-AUDIT FAIL" in out
    assert "signature invalid" in out


# ── Test 7: Missing baseline -> advisory warning, exit 0 ────────────────────

def test_missing_baseline_advisory(tmp_baseline, capsys):
    """SELF-04: Missing baseline prints advisory and exits 0."""
    # Don't create baseline -- just verify
    rc = mg_self_audit.cmd_verify()
    assert rc == 0
    out = capsys.readouterr().out
    assert "ADVISORY" in out
    assert "no baseline found" in out


# ── Test 8: Missing core file -> ALERT ──────────────────────────────────────

def test_missing_core_file_alert(initialized_baseline, capsys):
    """Missing core script after baseline creation causes ALERT and FAIL."""
    # Delete one script
    (initialized_baseline / "scripts" / "mg_sign.py").unlink()

    rc = mg_self_audit.cmd_verify()
    assert rc == 1
    out = capsys.readouterr().out
    assert "ALERT" in out
    assert "mg_sign.py" in out


# ── Test 9: --update workflow (mock input for confirmation) ──────────────────

def test_update_with_confirmation(initialized_baseline, capsys):
    """SELF-03: --update re-baselines after user confirms 'y'."""
    # Modify a script
    mg_path = initialized_baseline / "scripts" / "mg.py"
    mg_path.write_text("# Updated content v2\nprint('updated')\n", encoding="utf-8")

    # Mock input to return 'y'
    with patch("builtins.input", return_value="y"):
        rc = mg_self_audit.cmd_update()
    assert rc == 0
    out = capsys.readouterr().out
    assert "UPDATE" in out

    # Now verify should pass
    rc2 = mg_self_audit.cmd_verify()
    assert rc2 == 0


# ── Test 10: --update cancelled ──────────────────────────────────────────────

def test_update_cancelled(initialized_baseline, capsys):
    """--update aborts if user says 'n'."""
    mg_path = initialized_baseline / "scripts" / "mg.py"
    mg_path.write_text("# Changed\n", encoding="utf-8")

    with patch("builtins.input", return_value="n"):
        rc = mg_self_audit.cmd_update()
    assert rc == 0
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


# ── Test 11: --update with no changes ────────────────────────────────────────

def test_update_no_changes(initialized_baseline, capsys):
    """--update with no changes reports baseline is current."""
    rc = mg_self_audit.cmd_update()
    assert rc == 0
    out = capsys.readouterr().out
    assert "current" in out.lower() or "No changes" in out


# ── Test 12: --update with no baseline ───────────────────────────────────────

def test_update_no_baseline(tmp_baseline, capsys):
    """--update without existing baseline suggests --init."""
    rc = mg_self_audit.cmd_update()
    assert rc == 1
    out = capsys.readouterr().out
    assert "--init" in out


# ── Test 13: JSON output mode ────────────────────────────────────────────────

def test_json_output_pass(initialized_baseline, capsys):
    """--json flag outputs valid JSON on PASS."""
    class Args:
        json_output = True
    rc = mg_self_audit.cmd_verify(Args())
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "PASS"
    assert data["scripts_verified"] == 8
    assert data["mismatches"] == []
    assert data["missing"] == []


# ── Test 14: JSON output on FAIL ─────────────────────────────────────────────

def test_json_output_fail(initialized_baseline, capsys):
    """--json flag outputs valid JSON on FAIL."""
    (initialized_baseline / "scripts" / "mg.py").write_text("# tampered\n", encoding="utf-8")

    class Args:
        json_output = True
    rc = mg_self_audit.cmd_verify(Args())
    assert rc == 1
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["status"] == "FAIL"
    assert len(data["mismatches"]) >= 1
    assert data["mismatches"][0]["file"] == "scripts/mg.py"


# ── Test 15: Edge case -- empty script file ──────────────────────────────────

def test_empty_file_hashing(initialized_baseline):
    """An empty script file produces a valid hash (not a crash)."""
    (initialized_baseline / "scripts" / "mg.py").write_text("", encoding="utf-8")

    # Re-init should succeed (empty file is still hashable)
    rc = mg_self_audit.cmd_init()
    assert rc == 0

    baseline_path = initialized_baseline / "reports" / "core_integrity.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    entry = baseline["scripts"]["scripts/mg.py"]
    assert entry["hash"] == hashlib.sha256(b"").hexdigest()
    assert entry["size"] == 0


# ── Test 16: Edge case -- binary content in file ─────────────────────────────

def test_binary_content_hashing(initialized_baseline):
    """A file with binary content is still hashed correctly."""
    (initialized_baseline / "scripts" / "mg.py").write_bytes(b"\x00\x01\x02\xff\xfe")

    rc = mg_self_audit.cmd_init()
    assert rc == 0

    baseline_path = initialized_baseline / "reports" / "core_integrity.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    entry = baseline["scripts"]["scripts/mg.py"]
    expected = hashlib.sha256(b"\x00\x01\x02\xff\xfe").hexdigest()
    assert entry["hash"] == expected


# ── Test 17: CRLF canonicalization ───────────────────────────────────────────

def test_crlf_canonicalization(initialized_baseline):
    """CRLF and LF produce identical hashes (BUG 2 prevention)."""
    content_lf = b"line1\nline2\nline3\n"
    content_crlf = b"line1\r\nline2\r\nline3\r\n"

    # Hash both through the module's function
    p = initialized_baseline / "scripts" / "mg.py"

    p.write_bytes(content_lf)
    hash_lf, size_lf = mg_self_audit._hash_file(p)

    p.write_bytes(content_crlf)
    hash_crlf, size_crlf = mg_self_audit._hash_file(p)

    assert hash_lf == hash_crlf, "CRLF and LF should produce identical hashes"
    assert size_lf == size_crlf, "Sizes should match after canonicalization"


# ── Test 18: Init with missing core script ───────────────────────────────────

def test_init_missing_script(tmp_baseline, capsys):
    """--init fails if a core script is missing."""
    (tmp_baseline / "scripts" / "agent_pilot.py").unlink()

    rc = mg_self_audit.cmd_init()
    assert rc == 1
    out = capsys.readouterr().out
    assert "ALERT" in out
    assert "agent_pilot.py" in out


# ── Test 19: Invalid baseline structure ──────────────────────────────────────

def test_invalid_baseline_structure(initialized_baseline, capsys):
    """Baseline with missing keys is detected as FAIL."""
    baseline_path = initialized_baseline / "reports" / "core_integrity.json"
    # Write a minimal invalid baseline
    baseline_path.write_text(json.dumps({"version": "1.0"}), encoding="utf-8")

    rc = mg_self_audit.cmd_verify()
    assert rc == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "invalid structure" in out


# ── Test 20: --update with EOFError (non-interactive) ────────────────────────

def test_update_eof_error(initialized_baseline, capsys):
    """--update handles EOFError gracefully (e.g., piped input)."""
    (initialized_baseline / "scripts" / "mg.py").write_text("# changed\n", encoding="utf-8")

    with patch("builtins.input", side_effect=EOFError):
        rc = mg_self_audit.cmd_update()
    assert rc == 1
    out = capsys.readouterr().out
    assert "Aborting" in out


# ── Test 21: CLI integration (subprocess) ────────────────────────────────────

def test_cli_integration():
    """Running mg_self_audit.py as a subprocess works."""
    # This tests the actual CLI -- advisory mode since baseline may not exist
    # in a clean test environment. We just check it doesn't crash.
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "mg_self_audit.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
        timeout=30,
    )
    # Should exit 0 (either PASS or ADVISORY)
    assert result.returncode == 0
