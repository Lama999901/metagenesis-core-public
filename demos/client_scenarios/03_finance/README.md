# QuantRisk Capital — Basel III Model Validation

## The $1.65 billion compliance problem

SR 11-7 (Federal Reserve, 2011): every bank model requires "effective challenge."

Average bank: 175 models. Validation: 1-30 weeks each. Cost: $50K-$500K per model.

MRM market: $1.65B in 2024. Projected $3.85B by 2033.

ECB TRIM (2016-2021): 200 on-site investigations, 5,800 deficiencies, 30% high severity.
Result: EUR 275 billion increase in risk-weighted assets.

Five years of manual reviews — because model outputs could not be independently verified.

SR 11-7 requires documentation "so a knowledgeable third party can recreate
the model without access to the model development code."

London Whale (JPMorgan 2012): VaR model changed to halve loss estimates.
300+ limit breaches. Loss: $6.2B. Fine: $920M.

Machine-verifiable bundle would have caught the manipulation on day one.

## QuantRisk Capital's problem

QuantRisk's VaR model produces daily risk estimates for a $2B portfolio.

The Fed examiner asks: "Prove this VaR output came from the documented computation —
without re-running your proprietary model."

Today: narrative validation reports. PDF prose. Trust us.

MetaGenesis Core: verifiable bundle. No model access. 60 seconds.

## Run it

```bash
python demos/client_scenarios/03_finance/run_scenario.py
# SCENARIO 3 PASS: QuantRisk Capital — VaR model claim verified (Basel III SR 11-7)

python scripts/mg.py verify --pack demos/client_scenarios/03_finance/bundle/
# VERIFY: PASS
```

Free pilot: yehor@metagenesis-core.dev | Price: $299
