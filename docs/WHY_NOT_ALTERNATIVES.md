# Why Not Alternatives

**Audience:** Technical evaluators asking "why do I need this on top of the tools I already use?"
**Stance:** Composability, not replacement. MetaGenesis Core adds a verification envelope around the tools already in your stack.
**Last updated:** 2026-04-16 · MetaGenesis Core v1.0.0-rc1 · 2407 tests PASS · 20 claims · 5 layers

---

## The one question this document answers

> *"I already use Docker / MLflow / git / signed PDFs / a workflow engine / a formal prover. Why would I add MetaGenesis Core?"*

Every tool listed above solves a real problem correctly — and none of them was designed to answer the specific question MetaGenesis Core answers: **given only the output artefact, can a third party (auditor, regulator, client, reviewer) verify offline that this exact computational claim came from this exact code on this exact data at this exact time, signed by this exact producer?** The primitives overlap with that question but do not cover it. That is the gap, and it is a narrow one.

The right framing is additive. Docker + MetaGenesis still gets you a pinned environment; you also get a verifiable output bundle. MLflow + MetaGenesis still gets you team experiment hygiene; you also get an offline audit artefact the tracking server cannot forge. Git + MetaGenesis still gets you source versioning; you also get a cryptographic link from source to the specific numerical result it produced. Coq/Lean + MetaGenesis still gets you algorithmic correctness; you also get execution attestation for a particular run. Every alternative in the table below is kept, used, and trusted in its own niche. MetaGenesis Core is the verification envelope on top.

### One-line role matrix

| Alternative | Role it plays (and plays well) | MetaGenesis delta (what it adds) |
|---|---|---|
| SHA-256 of output file | Single-file byte integrity | Binds inputs, code, time, signer, execution trace |
| Docker image hash | Environment reproducibility at build time | Attests what the environment actually produced at runtime |
| MLflow / DVC | Team experiment logging and data versioning | Offline-verifiable bundle; third-party audit without server access |
| Manual audit | Human judgement on semantic correctness | Cryptographic identity for the artefact the human reviewed |
| Signed PDF (Adobe / DocuSign) | Document-byte integrity and signer attribution | Proof that the numbers inside the document came from a declared computation |
| Git history | Versioned source code and authorship | Proof that the committed code was executed on declared inputs and produced this result |
| Jupyter notebook (saved output) | Human-readable narrative of an analysis | Bundle whose numbers cannot be edited in place without detection |
| CWL / Snakemake / Nextflow | Pipeline orchestration and step dependency tracking | External signed, timestamped anchor over the trace the engine produces |
| Chainpoint / RFC 3161 timestamp | Existence-of-hash at a point in time | Semantic payload behind the hash, so the timestamp is interpretable later |
| Coq / Lean4 formal verification | Mathematical proof of algorithmic correctness | Execution attestation: this correct algorithm actually ran on these inputs |

The rest of this document expands each row into a steel-man, a concrete failure, and the minimum delta MetaGenesis adds, then walks through the flagship CERT-02 proof that the Layer 1 integrity hash alone is insufficient, and finally makes the rerun-as-verification argument fail by cost-and-determinism math in three real domains.

---

## Section 1 — The ten alternatives, one by one

### 1. SHA-256 of the output file alone

**What it is.** A single cryptographic hash (SHA-256 by convention; BLAKE3 or SHA-512 equivalently) computed over the bytes of a result file. The publisher records the digest alongside or inside the file; a consumer recomputes it on receipt and compares. FIPS 180-4 standardises the algorithm. This is the most widely deployed integrity primitive in computing.

**What it solves well.** Single-file byte-level integrity. If you publish `accuracy.json` with `sha256: abc...def`, any one-bit modification to the file is detected at verification time. The operation is fast (GB/s on commodity hardware), the standard is stable, and the implementation is everywhere. For the narrow question "has this exact byte sequence been altered since I recorded the hash?", SHA-256 is the right primitive. MetaGenesis Core uses SHA-256 inside Layer 1 for exactly this reason.

**Where it fails for computational verification.** A digest is bound to one file and nothing else. It is not bound to the inputs that produced the file, the code that produced it, the moment it was produced, the producer's identity, or any other artefact that logically travels with it. A prospect who hands you `accuracy.json` plus its SHA-256 teaches you exactly one thing: the bytes of that file, unchanged since hashing. You learn nothing about the claim inside.

**Concrete failure scenario.** An ML team reports test-set accuracy 0.94 on image-classification benchmark X. They publish `accuracy.json` and its SHA-256. Later the same team runs the same model on a different (easier) test set and gets 0.97. They swap the result file and publish the new SHA-256. Both files are individually valid. Neither hash proves which test set was used, which model checkpoint was used, or when the measurement happened. A verifier who only checks SHA-256 equality against a published digest is checking that a file is unchanged — not that the claim is true.

**What MetaGenesis adds.** Layer 3 Step Chain binds the hash to the inputs, the code path, and the four-step execution trace. The `trace_root_hash` commits the full sequence `init_params -> compute -> metrics -> threshold_check`, so swapping the test set changes `inputs`, which changes every subsequent chain hash. Layer 5 Temporal Commitment binds the bundle to a NIST Randomness Beacon value that did not exist before a specific wall-clock moment — "which came first" becomes cryptographically answerable. **SHA-256 + MetaGenesis = SHA-256 is still the integrity primitive, and the other four layers cover what SHA-256 was never designed to cover.**

---

### 2. Docker image hash and reproducible builds

**What it is.** A container image is a layered filesystem snapshot of an operating system, libraries, and application code. Image digests — content-addressed SHA-256 values over layer content in OCI image specs — let a consumer verify they pulled the exact image the publisher produced. Tools such as cosign and Notary sign these digests.

**What it solves well.** Environment reproducibility. Docker and OCI image specs resolved a real pain: "it works on my machine" caused by undeclared library versions, missing system packages, and path assumptions. For pinning an execution environment, image digests are robust, standardised, and production-tested. MetaGenesis Core does not replace them and does not attempt to.

**Where it fails for computational verification.** The image hash covers what is baked in at build time. A typical ML or scientific workload produces its output at runtime: the container is launched with a mounted dataset, reads an env var or mounted config, writes a result to a mounted volume. None of those runtime artefacts are covered by the image digest. Additionally, even with bit-identical inputs and a pinned image, non-determinism from GPU ops, thread scheduling, or floating-point reduction ordering can change numerical output — so "same image, same inputs" does not imply "same output bytes".

**Concrete failure scenario.** A quant team publishes image `risk-model:2026.04` with digest `sha256:a1b2...`. It contains the VaR model and its dependencies. In production, the container launches with a mounted portfolio CSV and writes `var_result.json` to a shared volume. On Monday the result is 8.2 million USD loss at 99 percent confidence. On Tuesday someone replaces `var_result.json` with a file showing 6.1 million USD loss. The image digest is unchanged. Nothing in the Docker trust model catches this — image signing (cosign, Notary) signs the image, not the output produced when the image was run.

**What MetaGenesis adds.** The Step Chain records the computation's inputs, result, and the hash of each step of the actual execution, not the image that ran it. The bundle is signed with Ed25519 at Layer 4, so the verifier knows who produced the output, not only who published the image. Layer 5 binds output-production time to an external beacon. **Docker + MetaGenesis compose cleanly: Docker pins the environment, MetaGenesis certifies what that environment produced.**

---

### 3. MLflow and DVC

**What they are.** MLflow is an open-source platform for logging ML experiment parameters, metrics, and artefacts into a tracking server. DVC (Data Version Control) is a git-adjacent tool that versions large data and model files via content-addressed storage and pointer files committed to git.

**What they solve well.** Inside a single team with a single tracking server or a shared remote, both tools solve day-to-day experiment hygiene. MLflow gives a UI over all runs, lets users compare hyperparameters against metrics, and standardises artefact logging. DVC addresses "git is bad at large binaries" by keeping content-addressed blobs in object storage and putting pointers in the repo. For an internal data-science team, they are excellent and should stay.

**Where they fail for computational verification.** Both are server-of-record architectures. MLflow's authority is whatever the tracking server currently says; DVC's authority is whatever the content-addressed store resolves to. A third-party auditor or a regulator cannot verify a claim offline without access to the server or store, and even with access, neither system is tamper-evident in the cryptographic sense: an administrator with write access to the MLflow database or the DVC remote can modify records. MLflow added model signatures in recent versions, but those describe schema (input/output types) — not cryptographic origin signatures over the run. Nothing in either system provides a cross-artefact hash chain, a bundle signing layer, or a temporal commitment.

**Concrete failure scenario.** A pharma ML team runs an ADMET prediction model and logs to MLflow: metric "MAE 0.08", checkpoint saved as artefact, dataset version pinned via DVC. Six months later an FDA auditor asks for evidence. The team exports the MLflow run to CSV and hands over the DVC-pinned data. The auditor has no way to verify that (a) the CSV matches what the MLflow server held at the time of the run, (b) the MLflow server itself was never edited, (c) the DVC pointer still resolves to the same bytes it did at run time, or (d) the run happened before the auditor's request rather than being fabricated last week. None of these are hypothetical; all are standard audit questions.

**What MetaGenesis adds.** Offline verifiability. The bundle is a single zip that contains every artefact, the Step Chain binding them, the signature, and the temporal commitment. A regulator running `python scripts/mg.py verify --pack bundle.zip` returns PASS or FAIL without calling any server. **MLflow + MetaGenesis: generate a bundle from the MLflow run, ship both. The auditor gets the offline artefact; the team keeps the MLflow experience.**

---

### 4. Manual audit (human domain expert)

**What it is.** A domain expert — internal risk officer, external auditor, peer reviewer — inspects code, data, logs, and outputs and forms a judgement that the result is trustworthy.

**What it solves well.** Context. A human catches semantic errors that no automated system can: wrong metric chosen, inappropriate test population, unjustified assumption, data leakage in feature engineering. Manual review is irreplaceable for questions like "is this the right thing to measure?" and "is the conclusion sound?". A serious verification stack always includes human review; automating it is not the goal.

**Where it fails for computational verification.** Human review does not scale. It is expensive. It is not repeatable — two auditors on the same artefacts reach different conclusions. It relies on the auditor trusting that the logs they are reading are the logs that were actually produced. And it is bypassed trivially by changing the artefact after the audit: the auditor's sign-off is frozen at review time, but the files are not.

**Concrete failure scenario.** A bank's Model Risk Management team convenes a 12-person review for a new credit-loss model. After six weeks they sign off on version 2.3.1 with documented assumptions. Three months later an engineer patches a bug and redeploys without a fresh review, documenting the change only in a Confluence page. An external auditor six months after that discovers the production model is not the one that was reviewed. No cryptographic linkage exists between the reviewed artefact and the deployed artefact, so reconstructing the gap takes weeks.

**What MetaGenesis adds.** An auditor does not stop being useful — but the artefact the auditor signs off on now has a cryptographic identity (`trace_root_hash`) that travels with it. When the model is re-deployed, the new bundle has a new trace root; a simple comparison detects drift from the approved version. **Human judgement + MetaGenesis = scalable, re-checkable audit. The human does what only a human can do; the protocol does what only cryptography can do.**

---

### 5. Signed PDF (Adobe / DocuSign)

**What it is.** A PDF document with an embedded X.509 digital signature over the byte content, verified by a certificate chain up to a trust anchor. The signature proves authorship and detects post-signing modification.

**What it solves well.** Document-level integrity and signer attribution. If somebody modifies the PDF bytes, the signature breaks. This is the right primitive for contracts, engineering drawings, approvals — any workflow where the artefact of interest is the document itself. For regulatory submissions where the document is the record, signed PDFs are mandatory infrastructure.

**Where it fails for computational verification.** The signature covers the bytes of the PDF. The numbers inside the PDF are unverified. Whoever produced the report can write any number on the page and sign the page. The signature proves signer identity and non-modification-after-signing; it proves nothing about the computation that produced the numbers.

**Concrete failure scenario.** A medical-device manufacturer submits a 510(k) filing to the FDA. The submission includes a 400-page PDF with ML benchmark results: "sensitivity 97.2 percent, specificity 94.1 percent on validation set of 5,000 images". The PDF is signed by the VP of Regulatory. The signature is valid — the VP actually signed it, the PDF has not been altered. The 97.2 percent number was produced by a script later discovered to have used the training set as the validation set. No property of the signed PDF detects this. The number was wrong before the pen touched the page.

**What MetaGenesis adds.** The bundle inside (or referenced by) the report carries its own computational provenance. The Step Chain records `inputs` (dataset hash, code hash, thresholds), `result` (the actual computed metrics), and the hash chain linking them. A regulator can verify not only "who signed the report" but "what computation produced the numbers in the report". **Signed PDF + MetaGenesis composes naturally: the PDF signature still covers the narrative, the bundle proves the numbers.**

---

### 6. Git history (commits + tags)

**What it is.** A Merkle DAG of commits, each identified by the SHA-1 (or SHA-256 in newer git) of its content plus parent pointers. Tags identify specific commits by name. Signed commits (GPG, SSH, Sigstore) add signer identity.

**What it solves well.** Versioned source code and attribution. Git is a tamper-evident history of source-file changes: modifying an old commit invalidates every downstream commit. For source-of-truth code, git is excellent and irreplaceable — MetaGenesis is itself versioned in git.

**Where it fails for computational verification.** Git tracks source files. Computational outputs — training metrics, simulation results, analysis tables — are produced when the code runs, not when it is committed. The link between "commit `4f3a2b1` existed at 14:32" and "this result file was produced by running commit `4f3a2b1` on dataset X" is not made anywhere in git. Tags are movable by anyone with push access unless signed and managed carefully. And large result files are poorly tracked by git in the first place (which is precisely why DVC exists).

**Concrete failure scenario.** A research lab publishes a paper. The Methods section says "trained using commit `4f3a2b1` of repo `research/models`". A reviewer clones the repo, checks out that commit, runs the training, and gets different numbers than the paper claims. No artefact in git bridges "commit `4f3a2b1`" and the specific numbers printed in the paper. The commit proves the code existed; it proves nothing about what that code produced in the authors' environment.

**What MetaGenesis adds.** The bundle binds the code hash, the dataset hash, the actual numerical result, the execution trace, and the producer's signature into one verifiable object. **Git + MetaGenesis: git owns the code history, the bundle owns the "this code produced this number on this data at this time" claim.**

---

### 7. Jupyter notebook with saved output

**What it is.** A notebook is a JSON document interleaving code cells, markdown cells, and execution outputs (stdout, plots, cell values). `.ipynb` files are widely used to share analyses with embedded results. Rendered by Jupyter, VS Code, Colab, and many other tools.

**What it solves well.** Communication. A reader sees code and output side by side, can rerun cells, and can follow the author's reasoning. For teaching, exploration, and internal sharing, notebooks are excellent. Nothing in this document is arguing notebooks should be replaced.

**Where it fails for computational verification.** `.ipynb` is a plaintext JSON file. Output cells are string fields inside that JSON. There is no binding between a code cell and its reported output — open the file in a text editor, change `"text": "0.94"` to `"text": "0.95"`, save. The notebook renders normally. There is no cryptographic link, no hash of each cell's output, no commitment to execution time. Additionally, hidden-state problems — cells executed out of order, deleted cells, imports from a stale kernel — mean even an honestly edited notebook may not reproduce its own shown output.

**Concrete failure scenario.** A pharma benchmark report is circulated as `results.ipynb`. Cell 14 shows `print(classification_report(y_true, y_pred))` with an output block reporting AUC 0.93. A skeptical reviewer opens the file in VS Code, sees that the AUC value is a plain string inside the JSON, and realises nothing prevents anyone from typing in 0.93. Rerunning the cell gives 0.81. No tampering evidence remains.

**What MetaGenesis adds.** Notebook-as-documentation continues to work. The numerical claims it references are bundled outside the notebook with a `trace_root_hash` that commits inputs, computation, and result. The notebook cites the bundle ID; the reviewer verifies the bundle. **Notebook + MetaGenesis: the notebook is for humans, the bundle is for verifiers. Both keep doing what they do best.**

---

### 8. CWL / Snakemake / Nextflow (workflow orchestration)

**What they are.** Declarative workflow languages and runtimes that orchestrate multi-step computational pipelines. CWL (Common Workflow Language) is a portable standard; Snakemake is Python-based with Make-style dependency rules; Nextflow is DSL-based and popular in bioinformatics.

**What they solve well.** Reproducible orchestration. Given a pipeline definition and input parameters, these engines execute steps in dependency order, cache intermediate results, track what ran, and produce a trace file. They make complex pipelines executable and rerunnable. They are correct infrastructure for data-intensive science and should stay.

**Where they fail for computational verification.** The engine trusts its own traces. Nextflow's `trace.txt`, Snakemake's log files, and CWL's execution reports are plaintext files in the working directory. They have no external cryptographic anchor, no signature, no binding to a beacon value. Anyone with filesystem access after the run can edit them. The workflow engine is honest about what it executed in real time, but it does not produce an artefact that a third party can verify months later without trusting the original filesystem.

**Concrete failure scenario.** A genomics lab runs a Nextflow pipeline: variant calling on 200 samples. The `trace.txt` shows 47 processes, wall time 18 hours, specific software versions from a container cache. Six months later the results feed a published paper. A replication attempt fails. Was the pipeline rerun with different reference data? Was `trace.txt` edited? The trace itself cannot answer. There is no external anchor, no signature, no chain back to a point-in-time commitment.

**What MetaGenesis adds.** Ship the workflow run artefacts plus the pipeline definition inside a bundle. The Step Chain commits each stage's inputs and outputs; Layer 4 binds producer identity; Layer 5 binds the run to a beacon. **Nextflow + MetaGenesis: the workflow engine keeps doing orchestration, the bundle provides the external verification layer the engine does not produce.**

---

### 9. Chainpoint / RFC 3161 timestamping

**What it is.** Timestamp anchoring services aggregate many hashes into a Merkle tree and periodically commit the root to a public cryptographic hash chain (Bitcoin, Ethereum) or to a trusted timestamp authority per RFC 3161. The resulting proof shows a specific hash existed by a specific time.

**What it solves well.** "This hash existed by time T." This is genuinely useful: priority disputes, inventor notebooks, intellectual-property filings. The math is clean and the proofs are compact. For the narrow question "when did this digest first exist?", these services answer it correctly.

**Where they fail for computational verification.** Timestamp services answer existence-at-a-time. They do not answer what the hash represents, what computation produced the bytes behind it, or what inputs went into them. A verifier receives a proof of the form "hash H was committed on 2026-04-16" and can say nothing else about H. If the bytes behind H are lost, the timestamp is worthless.

**Concrete failure scenario.** A climate-modelling group timestamps the SHA-256 of their model output to a public hash-chain ledger every month. Two years later, a carbon-credit auditor wants to verify a specific emissions-reduction figure came from the August 2026 run. The hash is timestamped — pass — but the underlying files have been overwritten in the group's storage, and even if recovered, nothing in the timestamp proves which dataset, which model version, or which scenario parameters produced the number. The timestamp is necessary but insufficient.

**What MetaGenesis adds.** The bundle itself contains the semantic content (inputs, execution trace, result, code hashes), so the hash anchored by Layer 5 points to a self-describing artefact — not an opaque digest. The NIST Beacon commitment inside Layer 5 provides the same "when" guarantee a Chainpoint proof provides, but bound to a bundle that remains independently interpretable. **Chainpoint + MetaGenesis: Layer 5 is a focused, offline-friendly timestamp pattern; it composes with public hash-chain ledger timestamping if deeper public anchoring is desired.**

---

### 10. Coq / Lean4 / proof-carrying code (formal verification)

**What it is.** Mathematical frameworks for proving that a program satisfies a formal specification. Coq and Lean4 are the most widely used interactive proof assistants; projects such as CompCert (a verified C compiler) and seL4 (a verified microkernel) are landmark results in the field.

**What it solves well.** Correctness of an algorithm against a specification, at mathematical certainty. For security-critical primitives — cryptographic libraries, compiler correctness, operating-system kernels — formal verification is the gold standard and nothing weaker is acceptable. If the question is "does this algorithm satisfy this specification for all valid inputs?", formal methods answer it exactly.

**Where they fail for computational verification.** Formal verification proves a program meets a specification; it does not prove the program was actually executed, was executed on the declared inputs, or produced the claimed output on a given day. Additionally, the computational claims most users make are not about algorithm correctness (the FEM solver is correct) but about runtime inputs and results (this specific simulation of this specific part under these specific loads produced these specific stresses). Expressing "this training dataset, this random seed, this weight initialisation" as a formal spec is either impossible or impractical for production numerical workloads.

**Concrete failure scenario.** A safety-critical FEM solver is formally verified in Coq: given any valid mesh and boundary conditions, the displacement output is correct to specified tolerance. An engineering team runs the solver on a specific aluminium bracket design and reports peak stress of 187 MPa. A reviewer asks: "Was that result produced by the verified solver on the declared mesh, or by an unverified post-processing script that later overwrote the result file?" Formal verification of the solver says nothing about this question.

**What MetaGenesis adds.** The bundle proves a specific run happened — which inputs, which code (hashed), which output, which producer, which time. **Coq/Lean + MetaGenesis: formal verification proves the code is correct; MetaGenesis proves the correct code actually ran on declared inputs and produced this specific number. They are complementary and the combination is strictly stronger than either alone.**

---

## Section 2 — The CERT-02 strip-and-recompute walk-through

> **Source of truth:** `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py`, specifically `test_semantic_negative_missing_job_snapshot_fails_verify` (lines 108-148). The walk-through below matches what the test code actually does; if this section and the test code ever diverge, the test code is authoritative.

This is the flagship proof that Layer 1 integrity alone is insufficient for computational claims. The attack is not theoretical — it is executed by a fifty-line test block that runs in CI on every commit.

### 2.1 The attacker's position

Start with a valid MetaGenesis bundle for claim MTR-1 (aluminium elastic-modulus calibration against the NIST reference E = 70 GPa). The bundle contains, among other files:

- `pack_manifest.json` — the integrity manifest (every file's SHA-256 plus a Merkle-style `root_hash` over all entries).
- `evidence_index.json` — the semantic index of claims.
- `evidence/MTR-1/normal/run_artifact.json` — the detailed run record, which includes a `job_snapshot` block (this is the authoritative run record for the normal, non-canary execution mode).

### 2.2 What the attacker controls

The attacker has **write access to every byte of the bundle after packaging**. They can:

- modify any file's contents,
- recompute the SHA-256 of the modified file,
- update the manifest entry with the new SHA-256 and new file size,
- resort the manifest file list and recompute the `root_hash` over the new sorted list.

The attacker can make the Layer 1 integrity layer pass trivially. The test does exactly this — and that is the point of the proof.

### 2.3 The specific tamper (test lines 122-144)

The test performs these steps in order:

1. **Load** `evidence/MTR-1/normal/run_artifact.json`.
2. **Assert** the artefact contains a `job_snapshot` key (it does — this is the authoritative semantic payload).
3. **Strip** the semantic evidence: `del data["job_snapshot"]`.
4. **Write** the shorter JSON back to disk (indent=2, UTF-8).
5. **Recompute** the SHA-256 of the modified file: `hashlib.sha256(run_artifact_path.read_bytes()).hexdigest()`.
6. **Patch** the manifest entry for `evidence/MTR-1/normal/run_artifact.json`: update `sha256` to the new digest and `bytes` to the new file size.
7. **Resort** the manifest file list and **recompute** the `root_hash` over the updated sorted list.
8. **Write** the patched manifest back.

At this point, Layer 1 (SHA-256 integrity plus root-hash verification) is **perfectly consistent**. Every file in the manifest has the correct hash. The root hash is correct over the sorted list. A pure integrity check — including file-by-file SHA-256 verification, Merkle-root verification, or any variation of hashes-over-hashes — returns **PASS**.

### 2.4 Which layer catches the attack, and why

Layer 2 (Semantic Verification) in `scripts/mg.py` → `_verify_semantic()`. The check iterates `evidence_index.json`, locates each declared run artefact, loads it, and asserts presence and type of required domain keys. Specifically, the loop in `_verify_semantic()` enforces:

```python
for key in ("trace_id", "job_snapshot", "canary_mode"):
    if key not in art:
        msg = f"Run artifact {run_rel} missing required key: {key}"
        return False, msg, [msg]
```

When the semantic verifier encounters the tampered `run_artifact.json`, the check for `"job_snapshot" in art` is false. The verifier returns a non-zero exit code and an error message that names the missing key. The test asserts exactly this (lines 146-148):

```python
vrc, vout = _verify_pack(pack_out)
assert vrc != 0, f"mg verify must FAIL on semantic violation: {vout}"
assert "job_snapshot" in vout or "missing required key" in vout
```

The bundle is **rejected**.

### 2.5 Why SHA-256 alone cannot catch this, and why hashes-of-hashes cannot either

SHA-256 is a function of bytes. It verifies that the bytes of each file match their recorded hash. The attacker recomputed every hash, so every byte-to-hash relation is consistent. The missing semantic content is **not a byte-level property** — it is a property of the *meaning* of the file. An integrity-only verifier reads bytes and asks "have these bytes changed since recording?"; the answer is "no, they match their newly recorded hash". The check passes. Meanwhile the claim is hollow: the evidence that substantiates it has been removed.

Hashes-of-hashes, Merkle roots, signed manifests, and every other byte-level construction share this weakness. They verify byte relations. They do not verify that the bytes contain the structures a claim requires. If an adversary with write access recomputes the byte-level commitments consistently, every byte-level check passes. **The only way to catch this class of attack is to verify structural-semantic content against a declared schema — and that is Layer 2.**

This is why MetaGenesis Core maintains Layer 1 (integrity) and Layer 2 (semantic) as **separate, independent layers**. They read the same bundle and ask different questions: is-unchanged versus contains-required-content. CERT-02 is the executable proof that no single hash-based layer can collapse both questions into one. CERT-11 generalises the result to all five layers: each layer catches attacks the other four miss, and no subset of four is sufficient.

### 2.6 Defence-in-depth — adjacent semantic checks in the same test file

The same test file exercises further semantic edge cases that complete the picture:

- **Null-field partial strip.** Replacing a required field with `null` instead of deleting it is also rejected (`test_a_null_mtr_phase_rejected`). An attacker cannot weaken the strip by nullifying.
- **Forward compatibility.** Unknown extra fields are permitted and logged as warnings, so adding new fields never breaks existing verification.
- **Threshold weakening.** Zero or negative thresholds are rejected (`test_b_zero_threshold_rejected`, `test_c_negative_threshold_rejected`). An attacker cannot weaken a claim by replacing a tight threshold with one that accepts anything.

Together these tests define the semantic layer's operating envelope. The attack surface is closed, not by adding more hashes, but by adding a distinct semantic check that reads the same bytes differently.

---

## Section 3 — Why rerunning is not verification

A natural reply to any of the alternatives above is "why not just rerun the computation and check?". The reply fails in three domains for two reasons: compute cost and non-determinism. Below are three concrete domains with primary-source figures showing that verification-by-rerun is infeasible, insufficient, or both. In all three, verification must operate on the artefact itself.

### 3.1 Large ML training — the GPT-3 case

The GPT-3 training compute budget was independently estimated by Lambda Labs at 3.114 × 10²³ FLOPs, corresponding to a theoretical cost of approximately **4.6 million USD** on a single Tesla V100 GPU at 1.50 USD per hour, with a hypothetical single-GPU wall-time of **355 V100-years** ([Lambda Labs via TechTalks — "The GPT-3 economy"](https://bdtechtalks.com/2020/09/21/gpt-3-economy-business-model/); [Wikipedia — GPT-3](https://en.wikipedia.org/wiki/GPT-3)).

Lambda's Chief Science Officer noted in the original analysis that **in practice — because training is distributed across thousands of GPUs with communication overhead — the real end-to-end cost is higher than the simplified single-GPU estimate** ([TechTalks](https://bdtechtalks.com/2020/09/21/gpt-3-economy-business-model/)). The 4.6 million USD figure is an optimistic lower bound; real distributed training cost exceeds it. Independent later estimates place GPT-4 and successor-model training costs well above 10 million USD and climbing ([Stanford AI Index via Statista — "Estimated cost of training selected AI models"](https://www.statista.com/chart/33114/estimated-cost-of-training-selected-ai-models/)).

**Implication for verification.** A third party who receives a claim "GPT-3-scale model achieves X on benchmark Y" cannot re-verify by retraining. The compute budget makes retraining a regulator's decision, not a spot-check. Even re-*inference* over a large benchmark suite can take days on significant hardware. If verification by re-execution is not possible, verification is not possible at all — unless the artefact carries its own proof: inputs, code hash, output, execution trace, signature, temporal commitment. That is exactly what a MetaGenesis bundle contains.

Additionally, training runs on modern accelerators are **non-deterministic at the bit level** — GPU op-order variation, fused multiply-add variants, distributed all-reduce non-associativity, scheduler interaction with memory pressure. Even with unlimited budget and bit-identical inputs, rerunning does not produce bit-identical output files, so hash-equality on output is not a usable verification signal. Step Chain hashes commit to declared inputs and computation steps, not to bitwise output reproducibility; the bundle's `trace_root_hash` is stable across re-execution where output files are not.

### 3.2 Large CFD / aerospace simulation

Industrial CFD simulations of complex vehicles routinely use meshes exceeding **one billion cells**. Ansys Fluent demonstrates scaling to **nearly 200,000 CPU cores** for such problems ([Siemens Simcenter — "HPC for CFD: Superlinear Scaling on Supercomputers"](https://blogs.sw.siemens.com/simcenter/hpc-for-cfd/); [AIAA SciTech 2025 — "Ansys Fluent HPC for Large-Scale CFD Simulations"](https://arc.aiaa.org/doi/10.2514/6.2025-1950)). On engineering workstations, single CFD jobs routinely take days; cluster HPC brings them down to hours but at pay-per-core-hour pricing where a single large run is a significant capital expense. One vendor case study reports cloud HPC reducing runtime by over 95 percent while billing per core-hour ([Rescale — "CFD Aerospace: Scaling and Parallelizing CFD Runs"](https://rescale.com/blog/cfd-aerospace-scaling-and-parallelizing-cfd-runs/); [engineeringdownloads — "HPC Cloud: Accelerating Engineering Simulations"](https://engineeringdownloads.com/hpc-cloud-accelerating-engineering-simulations-fea-cfd-and-ai-at-low-cost/)).

**Implication for verification.** A regulator or partner receiving "CFD says this aerofoil produces lift L at Mach M" cannot plausibly rerun a multi-day billion-cell simulation as part of an audit. The verifier must answer the question on the artefact. MetaGenesis claim DT-FEM-01 is the exact analogue for this case: the bundle includes mesh inputs (hashed), the reference comparison, the computed `rel_err`, and the threshold decision bound in the Step Chain. The cross-claim chain MTR-1 → DT-FEM-01 → DRIFT-01 carries the physical anchor provenance forward **without re-executing the CFD run**.

Beyond cost: floating-point reduction across MPI ranks is **not associative**. The order in which partial sums combine depends on message-passing order, which depends on network scheduling, which varies between runs. Even with identical inputs and identical software on the same hardware, bit-identical CFD output is not guaranteed. Bit-equality on output files is not a valid verification signal for this class of computation by construction.

### 3.3 Monte Carlo VaR under Basel III

Under Basel II.5 / III, banks compute Value-at-Risk at 99 percent confidence over a one-day horizon (scaled to 10-day for regulatory capital), typically by Monte Carlo simulation. For practical portfolio risk, 10,000 paths is often adequate; for high-precision regulatory reporting or complex derivatives, **50,000 to 100,000-plus paths are used**, and for deep-tail Expected Shortfall or stressed VaR the path count rises further ([MDPI Risks (2025) — "Monte Carlo-Based VaR Estimation and Backtesting Under Basel III"](https://www.mdpi.com/2227-9091/13/8/146); [Ryan O'Connell CFA — "VaR Monte Carlo Method"](https://ryanoconnellfinance.com/var-monte-carlo-method/)). The computational pattern is an **overnight batch**: the bank's market-risk engine runs every business day after close, producing the regulatory VaR number reported the next morning ([Wikipedia — Value at Risk](https://en.wikipedia.org/wiki/Value_at_risk)).

**Implication for verification.** An independent validator or regulator — under the Basel SR 11-7 "independent model validation" requirement in the US Federal Reserve context — cannot "just rerun" a bank's overnight VaR. A rerun requires:

1. the bank's proprietary portfolio snapshot at market close (commercially sensitive),
2. the bank's calibrated factor model (commercially sensitive),
3. comparable compute (hours, seeded but non-trivial).

Even when a validator has all three, **the Monte Carlo paths are seeded**; a true rerun under a different seed gives a different number within sampling error. Hash-equality on the output is not a valid test. Even the **original commitment time** is not recovered by a rerun — the run happened yesterday; running today produces a new number at a new timestamp.

What the validator needs is: the inputs used (hash of portfolio snapshot), the calibration used (hash of factor model), the path count and seed, the produced VaR number, the threshold it was checked against, and cryptographic proof that the bundle was signed by the bank's risk team **before the regulatory deadline** (Layer 5 Temporal Commitment). This maps directly onto MetaGenesis claim FINRISK-01.

### 3.4 The common shape

| Domain | Why rerun fails | Why bit-equality fails | What must travel with the artefact |
|---|---|---|---|
| Large ML training | Millions of USD per run, days to weeks wall time, proprietary compute | GPU non-determinism, distributed reduction ordering | Declared inputs, code hash, train/test split hash, metric, execution trace, signature, temporal commitment |
| Large CFD / FEM | Billion-cell runs at HPC pay-per-core-hour pricing | Floating-point reduction non-associativity across MPI ranks | Mesh hash, boundary-condition hash, solver version, reference anchor, `rel_err`, threshold decision, signature |
| Monte Carlo VaR | Requires proprietary portfolio + overnight compute window | Paths are seeded; output varies by sampling | Portfolio snapshot hash, factor-model hash, seed, path count, VaR number, threshold, signature, temporal commitment |

All three converge on the same requirement: **verification operates on the artefact, offline, cryptographically — not by re-execution.** The MetaGenesis 60-second `verify --pack` command is designed precisely for this envelope. The artefact contains enough structured, signed, timestamped evidence that an independent party can render a PASS/FAIL judgement without access to the original compute, the original data, or the original team.

---

## Where this sits in the larger documentation

This document is the composability anchor for the rest of the v3.1.0 documentation set:

- **[docs/USE_CASES.md](USE_CASES.md)** — for each of the 14 domains it covers, the "What happens when verification fails" subsection names a real incident whose root cause was exactly the gap described above. The same gap, domain by domain.
- **[docs/CLIENT_JOURNEY.md](CLIENT_JOURNEY.md)** — each of the six persona journeys opens with "what they tried first". Persona 1 tried SHA-256 checksums. Persona 2 tried Docker image digests. Persona 3 tried internal MLflow. Persona 4 tried signed PDFs. Persona 5 tried git commit pinning. Persona 6 tried a Jupyter notebook with saved outputs. Every one of them discovered the exact failure mode Section 1 of this document describes, under audit pressure.
- **[SECURITY.md](../SECURITY.md)** — the full attack-class taxonomy. Every attack class in that file has an executable CI proof. CERT-02 is the proof for Layer 2, and its walk-through in Section 2 above is drawn verbatim from the test file cited there.
- **[docs/PROTOCOL.md](PROTOCOL.md)** — the protocol specification for the five layers, the bundle structure, and the claim lifecycle. If this document persuades you the gap is real, PROTOCOL.md tells you how to close it.

---

## One-paragraph summary

MetaGenesis Core is not a replacement for any existing tool. SHA-256 is still the right primitive for single-file integrity. Docker is still the right tool for environment reproducibility. MLflow is still the right tool for team experiment logging. Git is still the right tool for source history. Signed PDFs are still the right artefact for document-level attestation. Workflow engines are still the right layer for pipeline orchestration. Formal verifiers are still the right tool for algorithmic correctness. Chainpoint is still the right service for timestamp anchoring. What MetaGenesis Core adds is the narrow verification envelope around the output of any of those tools: who produced it, on what inputs, via which execution trace, when it was committed, and whether the bytes and the semantic structures inside them are both intact. The CERT-02 attack shows byte-level checks cannot collapse this into a single layer; the three compute-cost cases show rerunning is not a substitute. Add MetaGenesis on top. Keep everything else.

---

*Document version: 1.0 — created Phase 30 of v3.1.0 Documentation Deep Pass — 2026-04-16*
*Primary source: `.planning/research/ALTERNATIVES.md` (10 alternatives, CERT-02 walk-through, 3-domain rerun-cost math)*
*CERT-02 ground truth: `tests/steward/test_cert02_pack_includes_evidence_and_semantic_verify.py` lines 108-148*
*Requirements satisfied: ALT-01 (3 sections), ALT-02 (10 alternatives), ALT-03 (CERT-02 walk-through matching test), ALT-04 (3 domains with primary sources), ALT-05 (composability framing throughout)*
