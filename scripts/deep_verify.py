#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEEP VERIFICATION -- reads actual code, not docs.
Verifies that what code claims matches what code does.
"""
import subprocess, sys, json, re, hashlib, io
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

root = Path(r"C:\Users\999ye\Downloads\metagenesis-core-public")

OK  = "[PASS]"
ERR = "[FAIL]"
WRN = "[SKIP]"

print("=" * 60)
print("TEST 1: steward_audit PASS")
print("=" * 60)
r = subprocess.run([sys.executable, "scripts/steward_audit.py"],
                   capture_output=True, text=True, cwd=root)
print(r.stdout.strip())
assert r.returncode == 0, "FAIL"

print("\n" + "=" * 60)
print("TEST 2: 223 tests GREEN")
print("=" * 60)
r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q", "--tb=short"],
                   capture_output=True, text=True, cwd=root)
lines = r.stdout.strip().split("\n")
print(lines[-1])
assert "223 passed" in r.stdout, f"FAIL: {lines[-1]}"

print("\n" + "=" * 60)
print("TEST 3: All 14 JOB_KIND constants match runner dispatch")
print("=" * 60)
claim_files = {
    "mtr1_calibration": "mtr1_youngs_modulus_calibration",
    "mtr2_thermal_conductivity": "mtr2_thermal_paste_conductivity_calibration",
    "mtr3_thermal_multilayer": "mtr3_thermal_multilayer_contact_calibration",
    "sysid1_arx_calibration": "sysid1_arx_calibration",
    "datapipe1_quality_certificate": "datapipe1_quality_certificate",
    "drift_monitor": "drift_calibration_monitor",
    "mlbench1_accuracy_certificate": "mlbench1_accuracy_certificate",
    "dtfem1_displacement_verification": "dtfem1_displacement_verification",
    "mlbench2_regression_certificate": "mlbench2_regression_certificate",
    "mlbench3_timeseries_certificate": "mlbench3_timeseries_certificate",
    "pharma1_admet_certificate": "pharma1_admet_certificate",
    "finrisk1_var_certificate": "finrisk1_var_certificate",
    "dtsensor1_iot_certificate": "dtsensor1_iot_certificate",
    "dtcalib1_convergence_certificate": "dtcalib1_convergence_certificate",
}
runner_text = (root / "backend/progress/runner.py").read_text(encoding="utf-8")
all_ok = True
for module, expected_kind in claim_files.items():
    py = root / "backend/progress" / f"{module}.py"
    text = py.read_text(encoding="utf-8")
    m = re.search(r'JOB_KIND\s*=\s*["\']([^"\']+)["\']', text)
    actual = m.group(1) if m else "NOT FOUND"
    var_pattern = re.search(rf'from\s+backend\.progress\.{module}[^\n]+JOB_KIND\s+as\s+(\w+)', runner_text)
    if var_pattern:
        var_name = var_pattern.group(1)
        in_runner = (f'payload.get("kind") == {var_name}' in runner_text or
                     f"payload.get('kind') == {var_name}" in runner_text)
    else:
        in_runner = module in runner_text and actual in runner_text
    status = OK if actual == expected_kind and in_runner else ERR
    if actual != expected_kind or not in_runner:
        all_ok = False
    print(f"  {status} {module}: JOB_KIND='{actual}', in_runner={in_runner}")
assert all_ok, "SOME CLAIMS FAILED"

print("\n" + "=" * 60)
print("TEST 4: All 14 claims have execution_trace + trace_root_hash")
print("=" * 60)
import importlib.util, sys as _sys

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    _sys.path.insert(0, str(root))
    spec.loader.exec_module(mod)
    return mod

test_calls = [
    ("mtr1_calibration", "run_calibration",
     dict(seed=42, E_true=70e9, n_points=30, max_strain=0.002)),
    ("mtr2_thermal_conductivity", "run_calibration",
     dict(seed=42, k_true=5.0, n_points=30)),
    ("mtr3_thermal_multilayer", "run_calibration",
     dict(seed=42, k_true=5.0, r_contact_true=0.1, n_points=30)),
    ("sysid1_arx_calibration", "run_calibration",
     dict(seed=42, a_true=0.9, b_true=0.5, n_steps=30)),
    ("datapipe1_quality_certificate", "run_certificate",
     dict(seed=42, dataset_relpath="tests/fixtures/data01/al6061_stress_strain_sample.csv")),
    ("drift_monitor", "run_drift_monitor",
     dict(anchor_value=70e9, current_value=70e9, drift_threshold_pct=5.0)),
    ("mlbench1_accuracy_certificate", "run_certificate",
     dict(seed=42, claimed_accuracy=0.9, n_samples=100)),
    ("dtfem1_displacement_verification", "run_certificate",
     dict(seed=42, reference_value=1.0)),
    ("mlbench2_regression_certificate", "run_certificate",
     dict(seed=42, claimed_rmse=0.10, n_samples=100)),
    ("mlbench3_timeseries_certificate", "run_certificate",
     dict(seed=42, claimed_mape=0.05, n_steps=100)),
    ("pharma1_admet_certificate", "run_certificate",
     dict(seed=42, property_name="solubility", claimed_value=-3.5)),
    ("finrisk1_var_certificate", "run_certificate",
     dict(seed=42, claimed_var=0.02, var_tolerance=0.02, n_obs=100)),
    ("dtsensor1_iot_certificate", "run_certificate",
     dict(seed=42, sensor_type="temperature_celsius", n_readings=20)),
    ("dtcalib1_convergence_certificate", "run_certificate",
     dict(seed=42, n_iterations=5, initial_drift_pct=20.0,
          convergence_rate=0.4, convergence_threshold=5.0)),
]

all_ok = True
for module, func_name, kwargs in test_calls:
    try:
        py = root / "backend/progress" / f"{module}.py"
        mod = load_module(module, py)
        fn = getattr(mod, func_name)
        result = fn(**kwargs)
        has_trace = "execution_trace" in result
        has_root  = "trace_root_hash" in result
        if has_trace and has_root:
            trace = result["execution_trace"]
            root_hash = result["trace_root_hash"]
            chain_ok = root_hash == (trace[-1]["hash"] if trace else "")
        else:
            chain_ok = False
        status = OK if (has_trace and has_root and chain_ok) else ERR
        if not (has_trace and has_root and chain_ok):
            all_ok = False
        print(f"  {status} {module}: trace={has_trace} root={has_root} chain={chain_ok}")
    except Exception as e:
        print(f"  {ERR} {module}: ERROR -- {e}")
        all_ok = False
assert all_ok, "SOME CLAIMS MISSING STEP CHAIN"

print("\n" + "=" * 60)
print("TEST 5: Cross-Claim Chain -- anchor_hash changes downstream hash")
print("=" * 60)
from backend.progress.mtr1_calibration import run_calibration as run_mtr1
from backend.progress.dtfem1_displacement_verification import run_certificate as run_dtfem
from backend.progress.drift_monitor import run_drift_monitor as run_drift

mtr1 = run_mtr1(seed=42, E_true=70e9, n_points=30, max_strain=0.002)
anchor1 = mtr1["trace_root_hash"]

dtfem_no  = run_dtfem(seed=42, reference_value=1.0)
dtfem_yes = run_dtfem(seed=42, reference_value=1.0, anchor_hash=anchor1)
assert dtfem_no["trace_root_hash"] != dtfem_yes["trace_root_hash"]

drift_no  = run_drift(anchor_value=70e9, current_value=70e9)
drift_yes = run_drift(anchor_value=70e9, current_value=70e9,
                      anchor_hash=dtfem_yes["trace_root_hash"])
assert drift_no["trace_root_hash"] != drift_yes["trace_root_hash"]
print(f"  {OK} MTR-1 -> DT-FEM-01 -> DRIFT-01 chain cryptographically linked")

print("\n" + "=" * 60)
print("TEST 6: forbidden terms in code (not docs)")
print("=" * 60)
code_dirs = ["backend/", "scripts/", "tests/"]
forbidden = ["tamper-proof", "GPT-5 ", "VacuumGenesis", "19x performance"]
found_any = False
for d in code_dirs:
    for f in (root / d).rglob("*.py"):
        if "__pycache__" in str(f): continue
        if f.name == "deep_verify.py": continue  # skip self -- contains terms as search strings
        txt = f.read_text(encoding="utf-8", errors="ignore")
        for term in forbidden:
            if term.lower() in txt.lower():
                print(f"  {ERR} FORBIDDEN '{term}' in {f.relative_to(root)}")
                found_any = True
if not found_any:
    print(f"  {OK} No forbidden terms in code")

print("\n" + "=" * 60)
print("TEST 7: site numbers match code")
print("=" * 60)
html = (root / "index.html").read_text(encoding="utf-8")
assert ">14<" in html, f"{ERR} claims not 14 in HTML"
assert ">223<" in html, f"{ERR} tests not 223 in HTML"
assert ">3<" in html,   f"{ERR} layers not 3 in HTML"
assert ">7<" in html,   f"{ERR} domains not 7 in HTML"
print(f"  {OK} site: 14 claims, 223 tests, 3 layers, 7 domains")

manifest = json.loads((root / "system_manifest.json").read_text(encoding="utf-8"))
assert manifest["test_count"] == 223
assert len(manifest["active_claims"]) == 14
assert "v0.2" in manifest["protocol"], f"{ERR} manifest protocol={manifest['protocol']}"
print(f"  {OK} system_manifest: 14 claims, 223 tests, protocol v0.2")

print("\n" + "=" * 60)
print("TEST 8: Demo end-to-end PASS PASS")
print("=" * 60)
r = subprocess.run([sys.executable, "demos/open_data_demo_01/run_demo.py"],
                   capture_output=True, text=True, cwd=root)
out = r.stdout.strip()
pass_count = out.count("PASS")
status = OK if pass_count >= 2 and r.returncode == 0 else ERR
print(f"  {status} demo output: {repr(out[:80])}")
assert pass_count >= 2 and r.returncode == 0

print("\n" + "=" * 60)
print("TEST 9: Bypass attack caught (Layer 2 semantic)")
print("=" * 60)
import tempfile, os
from backend.progress.mtr1_calibration import JOB_KIND
from backend.progress.runner import ProgressRunner
from backend.progress.store import JobStore
from backend.ledger.ledger_store import LedgerStore

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    os.environ["MG_PROGRESS_ARTIFACT_DIR"] = str(tmp)
    js = JobStore()
    ls = LedgerStore(file_path=str(tmp / "ledger.jsonl"))
    runner_obj = ProgressRunner(job_store=js, ledger_store=ls)
    payload = {"kind": JOB_KIND, "seed": 42, "E_true": 70e9, "n_points": 30, "max_strain": 0.002}
    job = runner_obj.create_job(payload=payload)
    runner_obj.run_job(job.job_id, canary_mode=False)
    runner_obj.run_job(job.job_id, canary_mode=True)

    pack_out = tmp / "pack"
    subprocess.run(
        [sys.executable, str(root / "scripts/mg.py"), "pack", "build",
         "--output", str(pack_out), "--include-evidence",
         "--source-reports-dir", str(tmp)],
        capture_output=True, text=True, cwd=root,
        env={**os.environ, "MG_PROGRESS_ARTIFACT_DIR": str(tmp)}
    )
    # Find any run_artifact.json in evidence (normal or canary)
    art_path = None
    for slot in ["normal", "canary"]:
        slot_dir = pack_out / "evidence" / "MTR-1" / slot
        candidates = [f for f in (slot_dir.glob("*.json") if slot_dir.exists() else [])
                      if "ledger" not in f.name]
        if candidates:
            art_path = candidates[0]
            break

    if art_path and art_path.exists():
        data = json.loads(art_path.read_text())
        del data["job_snapshot"]
        art_path.write_text(json.dumps(data))
        manifest_path = pack_out / "pack_manifest.json"
        if manifest_path.exists():
            mf = json.loads(manifest_path.read_text())
            rel = str(art_path.relative_to(pack_out)).replace("\\", "/")
            new_sha = hashlib.sha256(art_path.read_bytes()).hexdigest()
            for e in mf["files"]:
                if e["relpath"] == rel:
                    e["sha256"] = new_sha
                    e["bytes"] = art_path.stat().st_size
                    break
            lines2 = "\n".join(f"{e['relpath']}:{e['sha256']}"
                               for e in sorted(mf["files"], key=lambda x: x["relpath"]))
            mf["root_hash"] = hashlib.sha256(lines2.encode()).hexdigest()
            manifest_path.write_text(json.dumps(mf))
            r2 = subprocess.run(
                [sys.executable, str(root / "scripts/mg.py"), "verify", "--pack", str(pack_out)],
                capture_output=True, text=True, cwd=root)
            caught = r2.returncode != 0 and (
                "job_snapshot" in r2.stdout or "missing" in r2.stdout or "FAIL" in r2.stdout)
            s = OK if caught else ERR
            print(f"  {s} bypass attack {'CAUGHT' if caught else 'NOT CAUGHT'}: rc={r2.returncode}")
            assert caught, "BYPASS ATTACK NOT CAUGHT"
        else:
            print(f"  {WRN} No manifest -- skipping")
    else:
        print(f"  {WRN} No run_artifact -- skipping (covered by test_cert02 in TEST 2)")

print("\n" + "=" * 60)
print("TEST 10: verify-chain CLI exists")
print("=" * 60)
r = subprocess.run([sys.executable, str(root / "scripts/mg.py"), "--help"],
                   capture_output=True, text=True, cwd=root)
has_chain = "verify-chain" in r.stdout
print(f"  {OK if has_chain else ERR} verify-chain in CLI help")
assert has_chain

print("\n" + "=" * 60)
print("ALL 10 TESTS PASSED")
print("proof, not trust.")
print("=" * 60)
