"""
MetaGenesis Core SDK — Programmatic Verification Protocol
==========================================================

Single-file, zero-dependency SDK that wraps the MetaGenesis Core verification
protocol. All methods delegate to existing scripts via subprocess — no
reimplementation. Works on Python 3.11+, Windows + Linux + Mac.

Usage:
    from sdk.metagenesis import MetaGenesisClient

    client = MetaGenesisClient()
    result = client.verify("path/to/bundle")
    print(result.passed)        # True/False
    print(result.layers)        # {"integrity": True, "semantic": True, ...}
    print(result.reason)        # "PASS" or failure reason

PPA: USPTO #63/996,819 | Inventor: Yehor Bazhynov
Protocol: MetaGenesis Verification Protocol (MVP) v0.9
"""

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

__version__ = "0.9.0"

# Resolve repo root relative to this file
_SDK_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SDK_DIR.parent


@dataclass
class VerificationResult:
    """Result of a bundle verification."""

    passed: bool
    layers: dict = field(default_factory=dict)
    reason: str = ""
    bundle_path: str = ""
    timestamp: str = ""
    claim_id: Optional[str] = None
    trace_root_hash: Optional[str] = None


class MetaGenesisClient:
    """Client for the MetaGenesis verification protocol.

    All operations wrap existing CLI scripts — no reimplementation.
    Stdlib only, zero external dependencies.

    Args:
        repo_root: Path to the metagenesis-core-public repository root.
                   Defaults to the parent of the sdk/ directory.
    """

    def __init__(self, repo_root: Optional[Path] = None):
        self._root = Path(repo_root) if repo_root else _REPO_ROOT
        self._scripts = self._root / "scripts"
        self._standalone = self._scripts / "mg_verify_standalone.py"
        self._mg = self._scripts / "mg.py"
        self._mg_sign = self._scripts / "mg_sign.py"
        self._mg_receipt = self._scripts / "mg_receipt.py"

    # ------------------------------------------------------------------
    # verify: Run 5-layer verification on a bundle
    # ------------------------------------------------------------------

    def verify(self, bundle_path: str) -> VerificationResult:
        """Verify a bundle through all 5 verification layers.

        Uses mg_verify_standalone.py (zero-dependency, offline).

        Args:
            bundle_path: Path to the bundle directory.

        Returns:
            VerificationResult with layer-by-layer results.
        """
        bundle_dir = Path(bundle_path).resolve()
        if not bundle_dir.is_dir():
            return VerificationResult(
                passed=False,
                reason=f"Bundle directory not found: {bundle_dir}",
                bundle_path=str(bundle_dir),
                timestamp=_now_iso(),
            )

        # Try direct import first (faster, no subprocess overhead)
        try:
            return self._verify_direct(bundle_dir)
        except Exception:
            pass

        # Fallback: subprocess with --json
        return self._verify_subprocess(bundle_dir)

    def _verify_direct(self, bundle_dir: Path) -> VerificationResult:
        """Verify by importing mg_verify_standalone directly."""
        # Add repo root to path temporarily
        root_str = str(self._root)
        added = root_str not in sys.path
        if added:
            sys.path.insert(0, root_str)
        try:
            from scripts.mg_verify_standalone import verify_bundle
            all_passed, results = verify_bundle(bundle_dir)
        finally:
            if added and root_str in sys.path:
                sys.path.remove(root_str)

        layers = {}
        reason_parts = []
        for name, ok, detail in results:
            layer_key = _layer_name_to_key(name)
            layers[layer_key] = ok
            if not ok:
                reason_parts.append(f"{name}: {detail}")

        # Extract claim info
        claim_id = None
        trace_root = None
        evidence_path = bundle_dir / "evidence.json"
        if evidence_path.exists():
            try:
                ev = json.loads(evidence_path.read_text(encoding="utf-8"))
                claim_id = ev.get("mtr_phase")
                trace_root = ev.get("trace_root_hash")
            except (json.JSONDecodeError, OSError):
                pass

        return VerificationResult(
            passed=all_passed,
            layers=layers,
            reason="PASS" if all_passed else "; ".join(reason_parts),
            bundle_path=str(bundle_dir),
            timestamp=_now_iso(),
            claim_id=claim_id,
            trace_root_hash=trace_root,
        )

    def _verify_subprocess(self, bundle_dir: Path) -> VerificationResult:
        """Verify via subprocess (fallback when direct import fails)."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as tmp:
            json_path = tmp.name

        try:
            proc = subprocess.run(
                [sys.executable, str(self._standalone), str(bundle_dir),
                 "--json", json_path],
                capture_output=True,
                text=True,
                timeout=120,
            )

            report_path = Path(json_path)
            if report_path.exists():
                report = json.loads(report_path.read_text(encoding="utf-8"))
            else:
                return VerificationResult(
                    passed=False,
                    reason=f"Verifier produced no output: {proc.stderr.strip()}",
                    bundle_path=str(bundle_dir),
                    timestamp=_now_iso(),
                )
        except subprocess.TimeoutExpired:
            return VerificationResult(
                passed=False,
                reason="Verification timed out (120s)",
                bundle_path=str(bundle_dir),
                timestamp=_now_iso(),
            )
        except Exception as exc:
            return VerificationResult(
                passed=False,
                reason=f"Verification failed: {exc}",
                bundle_path=str(bundle_dir),
                timestamp=_now_iso(),
            )
        finally:
            Path(json_path).unlink(missing_ok=True)

        all_passed = report.get("result") == "PASS"
        layers = {}
        for layer in report.get("layers", []):
            key = _layer_name_to_key(layer.get("name", ""))
            layers[key] = layer.get("status") == "pass"

        return VerificationResult(
            passed=all_passed,
            layers=layers,
            reason="PASS" if all_passed else report.get("result", "FAIL"),
            bundle_path=str(bundle_dir),
            timestamp=report.get("timestamp", _now_iso()),
        )

    # ------------------------------------------------------------------
    # pack: Build a verification bundle from a job result
    # ------------------------------------------------------------------

    def pack(self, job_result: dict, output_dir: str) -> str:
        """Pack a job result into a verification bundle.

        Creates a bundle directory with pack_manifest.json, evidence files,
        and integrity hashes. The bundle can then be verified offline.

        Args:
            job_result: Dictionary with mtr_phase, inputs, result,
                       execution_trace, trace_root_hash.
            output_dir: Directory where the bundle will be created.

        Returns:
            Path to the created bundle directory.

        Raises:
            ValueError: If job_result is missing required keys.
            RuntimeError: If packing fails.
        """
        for key in ("mtr_phase", "inputs", "result",
                     "execution_trace", "trace_root_hash"):
            if key not in job_result:
                raise ValueError(f"job_result missing required key: {key}")

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        # Write evidence.json
        evidence_path = out / "evidence.json"
        evidence_path.write_text(
            json.dumps(job_result, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        # Build pack_manifest.json
        files_list = []
        for fpath in sorted(out.rglob("*")):
            if fpath.is_file() and fpath.name != "pack_manifest.json":
                relpath = fpath.relative_to(out).as_posix()
                sha = hashlib.sha256(fpath.read_bytes()).hexdigest()
                files_list.append({"relpath": relpath, "sha256": sha})

        lines = "\n".join(
            f"{e['relpath']}:{e['sha256']}"
            for e in sorted(files_list, key=lambda x: x["relpath"])
        )
        root_hash = hashlib.sha256(lines.encode("utf-8")).hexdigest()

        manifest = {
            "protocol_version": 1,
            "created": _now_iso(),
            "files": files_list,
            "root_hash": root_hash,
        }
        manifest_path = out / "pack_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        return str(out)

    # ------------------------------------------------------------------
    # sign: Sign a bundle with Ed25519 or HMAC-SHA256
    # ------------------------------------------------------------------

    def sign(self, bundle_path: str, key_path: str) -> str:
        """Sign a bundle using a signing key.

        Delegates to `python scripts/mg.py sign bundle --pack <bundle> --key <key>`.

        Args:
            bundle_path: Path to the bundle directory.
            key_path: Path to the signing key (.json).

        Returns:
            Key fingerprint used for signing.

        Raises:
            RuntimeError: If signing fails.
        """
        proc = subprocess.run(
            [sys.executable, str(self._mg), "sign", "bundle",
             "--pack", str(bundle_path), "--key", str(key_path)],
            capture_output=True,
            text=True,
            cwd=str(self._root),
            timeout=60,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"Signing failed (exit {proc.returncode}): {proc.stderr.strip()}"
            )
        # Parse fingerprint from output
        for line in proc.stdout.splitlines():
            if "key_fingerprint" in line:
                return line.split(":", 1)[1].strip()
        return proc.stdout.strip()

    # ------------------------------------------------------------------
    # verify_chain: Verify cross-claim chain integrity
    # ------------------------------------------------------------------

    def verify_chain(self, bundle_a: str, bundle_b: str) -> VerificationResult:
        """Verify a cross-claim chain between two bundles.

        The downstream bundle's anchor_hash must match the upstream bundle's
        trace_root_hash. Both bundles are individually verified first.

        Args:
            bundle_a: Path to upstream bundle.
            bundle_b: Path to downstream bundle.

        Returns:
            VerificationResult for the chain verification.
        """
        import tempfile

        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as tmp:
            json_path = tmp.name

        try:
            proc = subprocess.run(
                [sys.executable, str(self._mg), "verify-chain",
                 str(bundle_a), str(bundle_b), "--json", json_path],
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=120,
            )

            report_path = Path(json_path)
            if report_path.exists():
                report = json.loads(report_path.read_text(encoding="utf-8"))
            else:
                report = {}
        except subprocess.TimeoutExpired:
            return VerificationResult(
                passed=False,
                reason="Chain verification timed out (120s)",
                bundle_path=f"{bundle_a} -> {bundle_b}",
                timestamp=_now_iso(),
            )
        except Exception as exc:
            return VerificationResult(
                passed=False,
                reason=f"Chain verification failed: {exc}",
                bundle_path=f"{bundle_a} -> {bundle_b}",
                timestamp=_now_iso(),
            )
        finally:
            Path(json_path).unlink(missing_ok=True)

        passed = proc.returncode == 0
        return VerificationResult(
            passed=passed,
            layers={"chain": passed},
            reason="CHAIN PASS" if passed else proc.stdout.strip(),
            bundle_path=f"{bundle_a} -> {bundle_b}",
            timestamp=_now_iso(),
        )

    # ------------------------------------------------------------------
    # receipt: Generate human-readable verification receipt
    # ------------------------------------------------------------------

    def receipt(self, bundle_path: str) -> str:
        """Generate a human-readable verification receipt.

        Args:
            bundle_path: Path to the bundle directory.

        Returns:
            Receipt text string.

        Raises:
            RuntimeError: If receipt generation fails.
        """
        # Use standalone verifier with --receipt flag
        proc = subprocess.run(
            [sys.executable, str(self._standalone), str(bundle_path),
             "--receipt"],
            capture_output=True,
            text=True,
            cwd=str(self._root),
            timeout=60,
        )
        if proc.returncode != 0 and "FAIL" not in proc.stdout:
            raise RuntimeError(
                f"Receipt generation failed: {proc.stderr.strip()}"
            )
        return proc.stdout


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _layer_name_to_key(name: str) -> str:
    """Convert layer display name to dict key.

    'Layer 1 -- SHA-256 Integrity' -> 'integrity'
    """
    mapping = {
        "layer 1": "integrity",
        "layer 2": "semantic",
        "layer 3": "step_chain",
        "layer 4": "signature",
        "layer 5": "temporal",
    }
    lower = name.lower()
    for prefix, key in mapping.items():
        if lower.startswith(prefix):
            return key
    return lower.replace(" ", "_").replace("-", "_")
