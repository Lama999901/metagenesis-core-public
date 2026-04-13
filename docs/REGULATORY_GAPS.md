# Regulatory Gap Analysis

**Date:** 2026-04-12
**Protocol version:** v1.0.0-rc1
**Purpose:** Assess MetaGenesis Core coverage against upcoming regulatory requirements

---

## Regulatory Timeline

| Regulation | Deadline | Status |
|-----------|----------|--------|
| FDA AI/ML Guidance (drug development) | Q2 2026 | Guidance expected |
| EU AI Act enforcement | August 2, 2026 | Enacted, enforcement upcoming |
| Basel III model risk management | Active now | Ongoing compliance |

---

## Coverage Assessment

### FDA AI/ML in Drug Development

**Current coverage:** PHARMA-01 (ADMET prediction certificate) verifies that
AI-predicted molecular properties match declared thresholds. The bundle
includes dataset fingerprint, computation trace, and timestamp.

**Gap:** PHARMA-01 covers ADMET predictions but not other common AI/ML
outputs in drug development:
- PK/PD simulation outputs (pharmacokinetics/pharmacodynamics)
- Clinical trial endpoint predictions
- Medical device ML outputs (e.g., diagnostic imaging)
- Biomarker discovery model outputs

**Assessment:** PHARMA-01 demonstrates the verification pattern. Additional
pharma claims (PHARMA-02+) would follow the same 6-step lifecycle.
The bundle format is domain-agnostic — any computation output can be
packaged. No protocol changes needed, only new claim templates.

### EU AI Act

**Current coverage:** ML_BENCH-01/02/03 verify that ML model outputs match
declared performance. The bundle provides an independently verifiable
artifact for "high-risk" AI system documentation requirements.

**Gap:** The EU AI Act requires documentation of:
- Training data provenance (MetaGenesis verifies computation outputs, not data lineage)
- Model bias metrics (not currently a claim template)
- Continuous monitoring (AGENT-DRIFT-01 covers protocol drift, not model drift)
- Credit scoring specifically (FINRISK-01 covers VaR, not credit scoring)

**Assessment:** MetaGenesis bundles can serve as *part* of EU AI Act
compliance documentation. They prove that a specific computation produced
a specific result. They do NOT prove that the computation was appropriate,
fair, or unbiased. This distinction is honest and documented (SCOPE_001).

### Basel III Model Risk Management

**Current coverage:** FINRISK-01 (VaR certificate) verifies that Value-at-Risk
model outputs match declared parameters. Regulators can verify the bundle
offline without accessing the model.

**Gap:** Basel III also requires:
- Stress testing output verification
- Credit risk model validation
- Counterparty credit risk calculations

**Assessment:** FINRISK-01 demonstrates the pattern. Additional finance
claims would follow the same lifecycle. The verification principle
(independent offline verification of computation output) aligns directly
with Basel III's requirement for independent model validation.

---

## SI 2019 Exact Constants — Expansion Opportunity

MetaGenesis currently anchors to two SI 2019 exact constants:
- **kB** = 1.380649 x 10^-23 J/K (Boltzmann constant, PHYS-01)
- **NA** = 6.02214076 x 10^23 mol^-1 (Avogadro constant, PHYS-02)

Five additional SI 2019 exact constants could anchor future claims:
- **h** = 6.62607015 x 10^-34 J·s (Planck constant)
- **e** = 1.602176634 x 10^-19 C (elementary charge)
- **c** = 299 792 458 m/s (speed of light)
- **Kcd** = 683 lm/W (luminous efficacy)
- **Delta-nu-Cs** = 9 192 631 770 Hz (cesium frequency)

**Assessment:** No existing claims can be anchored to these constants.
They would require new domain claims:
- Planck (h): quantum computing output verification
- Elementary charge (e): semiconductor device simulation
- Speed of light (c): electromagnetic simulation, GPS timing
- Cesium frequency: precision timing, atomic clock calibration

These are documented as opportunities for future milestones.
Adding new claims requires the full 6-step lifecycle (see HOW_TO_ADD_CLAIM.md).

---

## Recommendations

1. **Immediate (Level 2):** Document how existing bundles satisfy
   specific EU AI Act article requirements
2. **Near-term:** Add FINRISK-02 (credit scoring) before EU AI Act
   enforcement date
3. **Medium-term:** Add PHARMA-02 (PK/PD) to strengthen FDA positioning
4. **Long-term:** Explore Planck/elementary charge anchors for
   quantum computing and semiconductor verification domains

---

*This document assesses gaps, not plans. New claims require the full
lifecycle documented in HOW_TO_ADD_CLAIM.md and must go through GSD.*
