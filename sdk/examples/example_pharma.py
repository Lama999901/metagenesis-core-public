"""Verify a pharma ADMET prediction with MetaGenesis Core."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sdk.metagenesis import MetaGenesisClient

client = MetaGenesisClient()
result = client.verify("path/to/admet_prediction_bundle")

print(f"Passed: {result.passed}")
print(f"Claim:  {result.claim_id}")
print(f"Layers: {result.layers}")
