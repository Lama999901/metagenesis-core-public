"""Verify a FEM simulation result with MetaGenesis Core."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
result = client.verify("path/to/fem_simulation_bundle")

print(f"Passed:     {result.passed}")
print(f"Trace root: {result.trace_root_hash}")
print(f"Layers:     {result.layers}")
