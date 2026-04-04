---
phase: quick
plan: 260319-uah
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/agent_chronicle.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "agent_chronicle.py extracts all 15 claim IDs from scientific_claim_index.md"
    - "Each claim has its correct domain (e.g. MTR-1 -> Materials Science)"
    - "Chronicle output shows clean table rows like | 1 | MTR-1 | Materials Science |"
  artifacts:
    - path: "scripts/agent_chronicle.py"
      provides: "Fixed read_claim_domains() using regex on ## headers"
      contains: "re.findall"
  key_links:
    - from: "scripts/agent_chronicle.py"
      to: "reports/scientific_claim_index.md"
      via: "regex parsing of ## CLAIM-ID headers and **domain** rows"
      pattern: "re\\.(findall|search)"
---

<objective>
Fix the `read_claim_domains()` function in `scripts/agent_chronicle.py` so it correctly parses claim IDs and domains from `reports/scientific_claim_index.md`.

Purpose: The current table-row parser picks up `Field | Value` header rows and `**claim_id** | MTR-1` data rows instead of extracting clean claim IDs. The file uses `## CLAIM-ID` section headers with sub-tables containing `| **domain** | Domain Name |` rows.

Output: Fixed `agent_chronicle.py` that produces clean chronicle claim tables.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/agent_chronicle.py (lines 39-52 — the broken read_claim_domains function)
@reports/scientific_claim_index.md (source file — uses ## CLAIM-ID headers, not flat tables)

The file structure in scientific_claim_index.md is:
```
## MTR-1

| Field | Value |
|-------|--------|
| **claim_id** | MTR-1 |
| **domain** | Materials Science |
...

---

## MTR-2
...
```

Each claim is a `## CLAIM-ID` header followed by a key-value table. The domain is in the `**domain**` row.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix read_claim_domains() to use regex header parsing</name>
  <files>scripts/agent_chronicle.py</files>
  <action>
Replace the `read_claim_domains()` function (lines 39-52) with regex-based parsing:

1. Use `re.findall()` to find all `## CLAIM-ID` headers. Pattern: `r'^## (MTR-\d+|SYSID-\d+|DATA-PIPE-\d+|DRIFT-\d+|ML_BENCH-\d+|DT-[\w-]+|PHARMA-\d+|FINRISK-\d+|AGENT-[\w-]+)'` with `re.MULTILINE`.

2. For each matched claim ID, find its domain by searching for the `**domain**` row in the section between this header and the next `---` or `## ` header. Pattern for domain extraction: find line containing `**domain**` and extract the value after the `|`. Use something like: split content by `## ` sections, then for each section find the `**domain**` row.

Recommended implementation approach:
```python
def read_claim_domains():
    index_path = REPO_ROOT / "reports" / "scientific_claim_index.md"
    if not index_path.exists():
        return []
    content = index_path.read_text(encoding="utf-8", errors="ignore")

    # Split into sections by ## headers
    header_pattern = re.compile(
        r'^## (MTR-\d+|SYSID-\d+|DATA-PIPE-\d+|DRIFT-\d+|ML_BENCH-\d+|DT-[\w-]+|PHARMA-\d+|FINRISK-\d+|AGENT-[\w-]+)',
        re.MULTILINE
    )
    domain_pattern = re.compile(r'\*\*domain\*\*\s*\|\s*(.+?)\s*\|?\s*$', re.MULTILINE)

    domains = []
    for match in header_pattern.finditer(content):
        claim_id = match.group(1)
        # Search for domain in the text after this header until next section
        section_start = match.end()
        next_header = header_pattern.search(content, section_start)
        section_end = next_header.start() if next_header else len(content)
        section = content[section_start:section_end]

        domain_match = domain_pattern.search(section)
        domain = domain_match.group(1).strip() if domain_match else ""
        domains.append((claim_id, domain))

    return domains
```

Do NOT change any other function in the file. Keep the encoding fix at the top and all other functions intact.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python -c "from scripts.agent_chronicle import read_claim_domains; pairs = read_claim_domains(); print(f'{len(pairs)} claims found'); [print(f'  {cid}: {dom}') for cid, dom in pairs]; assert len(pairs) == 15, f'Expected 15, got {len(pairs)}'; assert pairs[0] == ('MTR-1', 'Materials Science'), f'First pair wrong: {pairs[0]}'"</automated>
  </verify>
  <done>read_claim_domains() returns exactly 15 (claim_id, domain) tuples with clean IDs like "MTR-1" and domains like "Materials Science"</done>
</task>

<task type="auto">
  <name>Task 2: Run chronicle and verify clean output, then commit and push</name>
  <files>scripts/agent_chronicle.py</files>
  <action>
1. Run `python scripts/agent_chronicle.py --summary` and verify it prints a clean summary line.
2. Run `python scripts/agent_chronicle.py` and check the generated chronicle file in reports/ has a clean claims table with rows like `| 1 | MTR-1 | Materials Science |` (not `| 1 | Field | Value |` or `| 1 | **claim_id** | MTR-1 |`).
3. Create branch `fix/chronicle-parse`, commit the fix, and push.

Git workflow:
```bash
git checkout -b fix/chronicle-parse
git add scripts/agent_chronicle.py
git commit -m "fix: use regex header parsing in agent_chronicle.py read_claim_domains()"
git push origin fix/chronicle-parse
```

Do NOT commit the generated chronicle report file (it is a test artifact). Only commit agent_chronicle.py.
  </action>
  <verify>
    <automated>cd C:/Users/999ye/Downloads/metagenesis-core-public && python scripts/agent_chronicle.py --summary</automated>
  </verify>
  <done>Chronicle summary prints clean line. Branch fix/chronicle-parse pushed to origin with the fix commit.</done>
</task>

</tasks>

<verification>
- `python -c "from scripts.agent_chronicle import read_claim_domains; pairs = read_claim_domains(); assert len(pairs) == 15"` passes
- `python scripts/agent_chronicle.py --summary` shows clean output
- Generated chronicle has proper `| # | Claim ID | Domain |` table with 15 rows
- Branch fix/chronicle-parse exists on remote
</verification>

<success_criteria>
- read_claim_domains() returns 15 clean (claim_id, domain) tuples
- No "Field", "Value", or "**claim_id**" strings appear in chronicle output
- Fix committed to fix/chronicle-parse branch and pushed
</success_criteria>

<output>
After completion, create `.planning/quick/260319-uah-fix-agent-chronicle-py-claims-table-pars/260319-uah-SUMMARY.md`
</output>
