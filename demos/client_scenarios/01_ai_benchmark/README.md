# NeuralBench AI — ML Benchmark Verification

## The scandal that changed everything

April 5, 2025: Meta released Llama 4 Maverick — it shot to 2nd place on LMArena.

48 hours later: researchers discovered Meta had submitted a privately tuned variant.
When LMArena added the real Maverick, it dropped to 32nd place.

Nathan Lambert (AI2): "Sneaky. The results are fake."

Yann LeCun confirmed to the Financial Times: "The results were fudged a little bit."

NeurIPS 2025 "The Leaderboard Illusion" (Singh et al., 2M battles, 243 models):

- Meta tested 27 private variants before publishing the 2nd-place result
- Top 2 providers received 19.2% and 20.4% of ALL Arena evaluation data
- Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure"

## NeuralBench AI's problem

NeuralBench AI runs LLM evaluations for AstraZeneca, BCG, and Microsoft.

SOC 2 Type II Processing Integrity requires:

  "Controls prevent unauthorized changes to analytic code and models"
  "Immutable audit logs of model accuracy and drift"

AstraZeneca's auditor asks: "You claim 94% accuracy. Prove it came from this
computation — without sharing the model or training data."

Today: dashboard screenshots. PDF reports. Trust us.

MetaGenesis Core: one bundle. One command. Cryptographic proof.

## Run it

```bash
python demos/client_scenarios/01_ai_benchmark/run_scenario.py
# SCENARIO 1 PASS: NeuralBench AI — 94% accuracy claim verified

python scripts/mg.py verify --pack demos/client_scenarios/01_ai_benchmark/bundle/
# VERIFY: PASS
```

## What PASS proves

The prediction CSV (150 rows, SHA-256 fingerprinted) was verified via ML_BENCH-01.
Claimed accuracy 94.0% matches actual 94.0% within tolerance 0.02.
5-layer tamper-evident bundle: change any prediction row — FAIL.

Free pilot: yehor@metagenesis-core.dev | Price: $299
