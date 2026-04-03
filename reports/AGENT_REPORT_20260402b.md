# PHYS-01/02 Test Coverage Audit

**Date:** 2026-04-02
**Task:** TASK-025

---

## Test Function Count

| Claim | Test File | Functions | Coverage |
|-------|-----------|-----------|----------|
| PHYS-01 | tests/physics/test_phys01_boltzmann.py | 3 (pass, fail, determinism) | Standard 3-test pattern |
| PHYS-02 | tests/physics/test_phys02_avogadro.py | 3 (pass, fail, determinism) | Standard 3-test pattern |

**Total:** 6 test functions across 2 test files.

---

## SI 2019 Constant Verification in Documentation

### README.md

| Constant | Present | Location |
|----------|---------|----------|
| kB = 1.380649x10^-23 J/K | YES | Line 495 (claims table), Line 530 (anchor hierarchy) |
| NA = 6.02214076x10^23 mol^-1 | YES | Line 496 (claims table), Line 530 (anchor hierarchy) |
| SI 2019 exact designation | YES | Both constants labeled "(SI 2019, exact)" |

### paper.md

| Constant | Present | Location |
|----------|---------|----------|
| kB = 1.380649e-23 J/K | YES | Line 240 (claims table) |
| NA = 6.022e23 mol^-1 | YES | Line 241 (claims table, abbreviated) |

### CLAUDE.md

| Constant | Present | Location |
|----------|---------|----------|
| kB = 1.380649e-23 J/K | YES | Physical anchor section |
| NA = 6.02214076e23 mol^-1 | YES | Physical anchor section |

---

## Physical Anchor Hierarchy Verification

The hierarchy in CLAUDE.md, README.md, and CONTEXT_SNAPSHOT.md is consistent:
- **SI 2019 exact (zero uncertainty):** PHYS-01 (kB), PHYS-02 (NA)
- **NIST measured (~1% uncertainty):** MTR-1/2/3/4/5/6
- **Derived anchors:** DT-FEM-01, DRIFT-01, DT-CALIB-LOOP-01 (inherit from MTR-1)
- **Tamper-evident only:** all others

SCOPE_001 in known_faults.yaml correctly limits physical anchor claims.

---

## Verdict

PHYS-01 and PHYS-02 have standard 3-test coverage (pass/fail/determinism).
SI 2019 exact constants are correctly documented in all key files.
Physical anchor hierarchy is consistent across documentation.

No gaps found. No additional tests recommended at this time -- the standard
3-test pattern (pass, fail, determinism) covers the essential verification paths.
