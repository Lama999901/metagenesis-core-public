# Agent Research Report -- TASK-004: Predict JOSS reviewer questions

**Date:** 2026-03-18 22:06
**Task Description:** Read paper.md, identify 5 likely JOSS reviewer questions with prepared answers.
**Priority:** P2

---

## JOSS Reviewer Question Predictions

Date: 2026-03-18 22:06

### Paper Analysis

- **Word count:** ~2356
- **Sections:** Summary, → PASS  or  FAIL: <specific reason and layer>, Statement of Need, The verification gap, Why existing tools do not solve this, The bypass attack, Technical Design, Evidence bundle, Step Chain verification, Physical Anchor Principle
- **Bibliography entries:** 9
- **Claims table present:** Yes
- **AI disclosure present:** Yes

---

### Predicted Questions

**Q1: How does MetaGenesis Core compare to existing reproducibility tools like ReproZip or Binder?**

- **JOSS Criterion:** State of the Field
- **Why likely:** JOSS reviewers check that related work is adequately cited and
  the paper clearly differentiates from existing tools. The paper mentions MLflow,
  DVC, and lm-eval but does not discuss container-based reproducibility (ReproZip,
  Binder, Code Ocean) which are commonly associated with computational reproducibility.
- **Prepared Answer:** MetaGenesis Core is complementary to container-based tools.
  ReproZip/Binder guarantee the same *environment* runs; MetaGenesis guarantees a
  specific *result* was produced by a specific *computation*. A Docker container
  proves the binary is identical -- it does not prove the binary's output meets a
  scientific threshold. See paper.md 'Why existing tools do not solve this' section.
  Adding a brief mention of ReproZip/Binder would strengthen the paper.
- **Confidence:** HIGH -- this is a standard JOSS review point.

**Q2: Can a user install and run the verifier without cloning the full repository?**

- **JOSS Criterion:** Installation instructions
- **Why likely:** JOSS requires clear installation instructions. Currently the tool
  is used via `python scripts/mg.py` from within the repo. There is no `pip install`
  package, no PyPI distribution, and no `setup.py`/`pyproject.toml` for installation.
- **Prepared Answer:** MetaGenesis Core intentionally ships as a single-repo tool
  with zero external dependencies (stdlib only). Installation is `git clone` + run.
  A PyPI package is planned for v0.6.0. The zero-dependency design is a feature:
  the verifier must be auditable without trusting any third-party package. See README.md
  'Quick Start' section for current installation steps.
- **Confidence:** HIGH -- JOSS mandates clear install docs.

**Q3: Are there integration tests that verify the full pack-verify round-trip, or only unit tests?**

- **JOSS Criterion:** Tests
- **Why likely:** The paper claims 526 tests and adversarial proofs, but a reviewer
  may ask whether these are unit tests on individual functions or end-to-end tests
  that exercise the complete workflow (claim execution -> pack -> verify -> PASS/FAIL).
- **Prepared Answer:** Both. The test suite includes: (a) unit tests per claim in
  `tests/<domain>/`, (b) integration tests in `tests/steward/test_cert*.py` that run
  full pack-verify round-trips, (c) adversarial tests (CERT-02 through CERT-12) that
  tamper with bundles and verify the correct layer catches each attack, (d) a 13-test
  deep verification script (`scripts/deep_verify.py`). CI runs all 526 tests on every PR.
- **Confidence:** MEDIUM-HIGH -- test depth is a common JOSS concern.

**Q4: Where are the contribution guidelines and code of conduct?**

- **JOSS Criterion:** Community guidelines
- **Why likely:** JOSS requires a CONTRIBUTING.md or equivalent and a code of conduct.
  Many first-time JOSS submissions lack these. The repo should have CONTRIBUTING.md
  explaining how to add new claims, run the test suite, and submit PRs.
- **Prepared Answer:** CONTRIBUTING.md should be created before JOSS submission.
  Key content: (1) how to add a new claim (6-step procedure in CLAUDE.md),
  (2) how to run the verification gates (steward audit + pytest + deep_verify),
  (3) PR workflow (branch -> CI pass -> merge). A CODE_OF_CONDUCT.md (Contributor
  Covenant) should also be added. These are low-effort, high-impact additions.
- **Confidence:** HIGH -- JOSS checklist explicitly requires this.

**Q5: How does verification performance scale with bundle size or number of claims?**

- **JOSS Criterion:** Functionality / Performance
- **Why likely:** The paper states verification completes 'in under 60 seconds' but
  does not provide benchmarks. A reviewer may ask: what happens with 100 claims?
  1000 evidence files? Does SHA-256 hashing dominate? Is there a scalability ceiling?
- **Prepared Answer:** Current verification of a 14-claim bundle takes ~2 seconds.
  SHA-256 hashing is O(n) in file count and size. Step chain verification is O(k)
  where k = steps per claim (always 4). The bottleneck for large bundles would be
  I/O, not computation. A benchmark script (`scripts/mg.py bench`) exists but
  scalability benchmarks with synthetic large bundles should be added before submission.
  See `tests/steward/test_cert08_reproducibility.py` for existing timing assertions.
- **Confidence:** MEDIUM -- depends on reviewer's focus.

---

### Pre-Submission Checklist (derived from questions above)

1. [ ] Add brief mention of ReproZip/Binder in State of the Field
2. [ ] Create CONTRIBUTING.md with 6-step claim procedure
3. [ ] Add CODE_OF_CONDUCT.md (Contributor Covenant)
4. [ ] Consider adding scalability benchmark to paper or supplementary
5. [ ] Verify README.md Quick Start is clear enough for first-time users
