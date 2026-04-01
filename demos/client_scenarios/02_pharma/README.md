# PsiThera — FDA AI Credibility Framework

## The regulatory deadline

January 6, 2025: FDA published its first AI framework for drugs and biologics.

January 14, 2026: FDA and EMA jointly published 10 guiding principles. Both aligned.

Final guidance expected Q2 2026. 500+ drug submissions with AI reviewed since 2016.

The 7-step credibility framework. Step 6 requires:

"Documentation sufficiently detailed for FDA inspection — including deviations from plan."

Commissioner Califf: "With appropriate safeguards, AI has transformative potential."

Translation: without them, IND submissions get rejected.

## PsiThera's problem

PsiThera ($47.5M Series A, December 2025) uses QUAISAR — quantum chemistry + ML.

Every ADMET output going into an IND filing is a claim FDA will scrutinize under Step 3-6.

Current documentation: PDF reports signed by chief scientist. Trust us.

$299 per bundle vs $47.5M raise and a nine-figure clinical program.

## Run it

```bash
python demos/client_scenarios/02_pharma/run_scenario.py
# SCENARIO 2 PASS: PsiThera — ADMET solubility prediction verified (FDA 21 CFR Part 11)

python scripts/mg.py verify --pack demos/client_scenarios/02_pharma/bundle/
# VERIFY: PASS
```

Free pilot: yehor@metagenesis-core.dev | Price: $299
