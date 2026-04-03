# Wave-2 Outreach Email Drafts

**Prepared:** 2026-04-02
**Task:** TASK-026
**From:** yehor@metagenesis-core.dev (Zoho only)

---

## EMAIL 1: Francois Chollet

**To:** chollet@google.com
**Subject:** Cryptographic provenance layer for ARC Prize results -- open source, 60s verification

Dear Francois,

ARC Prize measures genuine reasoning ability -- the hardest benchmark in AI today. But when a team claims 85% on ARC-AGI, there is no cryptographic proof that this specific model produced this specific score on this specific dataset at this specific time.

MetaGenesis Core adds that missing layer. It bundles every evaluation run into a tamper-evident artifact that any reviewer can verify offline in 60 seconds:

```
python mg.py verify --pack arc_eval_bundle.zip  ->  PASS / FAIL
```

What makes this different from checksums: we anchor verification to physical constants. The Boltzmann constant kB = 1.380649x10^-23 J/K (SI 2019, exact by definition, zero uncertainty) serves as an immutable reference point in every verification chain. Change any computation step -- the cryptographic hash chain breaks.

Current state: 20 verified claims across 8 domains, 1313 adversarial tests, 5 independent verification layers. MIT licensed. USPTO PPA #63/996,819.

I would love to run a free pilot with ARC Prize evaluation data -- no integration needed, just your existing result files.

Free pilot signup: metagenesis-core.dev/#pilot
Code: github.com/Lama999901/metagenesis-core-public

Best regards,
Yehor Bazhynov
yehor@metagenesis-core.dev

---

## EMAIL 2: Anastasios Angelopoulos / Wei-Lin Chiang (LMArena)

**To:** support@lmarena.ai
**Subject:** Cryptographic proof layer for Arena evaluations -- after the Leaderboard Illusion

Dear Anastasios and Wei-Lin,

Your NeurIPS 2025 paper "The Leaderboard Illusion" showed that Meta tested 27 private variants on public benchmarks before submitting their best. The problem is fundamental: there is no cryptographic record of which model was evaluated, when, and whether the submission was the first attempt or the twenty-seventh.

MetaGenesis Core solves exactly this. Every model evaluation gets bundled into a tamper-evident artifact with a cryptographic hash chain anchored to physical constants. The Avogadro constant NA = 6.02214076x10^23 mol^-1 (SI 2019, exact by definition) serves as an immutable anchor -- change any step in the evaluation chain, and the hash breaks.

For Arena specifically: each anonymous battle could produce a verification bundle. Reviewers verify offline in 60 seconds without model access:

```
python mg.py verify --pack arena_battle_42.zip  ->  PASS / FAIL
```

5 independent verification layers. 1313 adversarial tests proving each layer catches attacks the others miss. MIT licensed.

I would welcome a free pilot with LMArena evaluation data.

Free pilot: metagenesis-core.dev/#pilot
Code: github.com/Lama999901/metagenesis-core-public

Best regards,
Yehor Bazhynov
yehor@metagenesis-core.dev

---

## EMAIL 3: Percy Liang

**To:** pliang@cs.stanford.edu
**Subject:** Offline-verifiable evidence layer for HELM -- 60-second verification

Dear Professor Liang,

HELM has the most rigorous holistic LLM evaluation methodology available today. The missing piece is cryptographic provenance: when HELM reports that Model X scores 0.87 on scenario Y, there is no independently verifiable artifact that a third party can audit offline without Stanford infrastructure access.

MetaGenesis Core adds that layer. Every evaluation run produces a tamper-evident bundle verifiable in 60 seconds on any machine:

```
python mg.py verify --pack helm_eval_bundle.zip  ->  PASS / FAIL
```

The verification chain is anchored to SI 2019 exact constants (kB = 1.380649x10^-23 J/K, NA = 6.02214076x10^23 mol^-1) -- physical constants with zero measurement uncertainty. This is the strongest possible verification anchor: defined by international agreement, immutable, universally reproducible.

5 independent verification layers, each proven to catch attacks the other four miss. 20 verified claims across 8 domains. 1313 adversarial tests. MIT licensed. USPTO PPA #63/996,819.

I would be glad to run a free pilot with HELM evaluation outputs -- no integration work needed on your side.

Free pilot: metagenesis-core.dev/#pilot
Code: github.com/Lama999901/metagenesis-core-public

Best regards,
Yehor Bazhynov
yehor@metagenesis-core.dev
