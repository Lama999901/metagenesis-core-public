"""Verify an ML benchmark result with MetaGenesis Core."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
result = client.verify("path/to/ml_benchmark_bundle")

print(f"Passed: {result.passed}")
print(f"Layers: {result.layers}")
print(f"Reason: {result.reason}")
