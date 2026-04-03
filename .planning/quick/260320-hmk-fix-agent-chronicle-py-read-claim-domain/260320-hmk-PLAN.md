---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [scripts/agent_chronicle.py]
autonomous: true
requirements: [FIX-CHRONICLE-CLAIMS]
must_haves:
  truths:
    - "read_claim_domains() returns exactly 15 (claim_id, domain) tuples"
    - "Claim IDs match ## headings in scientific_claim_index.md (MTR-1, MTR-2, MTR-3, DATA-PIPE-01, SYSID-01, DRIFT-01, ML_BENCH-01, DT-FEM-01, ML_BENCH-02, ML_BENCH-03, PHARMA-01, FINRISK-01, DT-SENSOR-01, DT-CALIB-LOOP-01, AGENT-DRIFT-01)"
    - "Domains are extracted from **domain** table rows, not from table headers or other rows"
  artifacts:
    - path: "scripts/agent_chronicle.py"
      provides: "Fixed read_claim_domains() using regex-based heading parser"
  key_links:
    - from: "scripts/agent_chronicle.py"
      to: "reports/scientific_claim_index.md"
      via: "regex parsing of ## headings + **domain** rows"
      pattern: "r'^## ([A-Z][A-Z0-9_-]+(?:-\\d+)?)'"
---

<objective>
Fix read_claim_domains() in agent_chronicle.py to correctly parse scientific_claim_index.md.

Purpose: The current implementation parses every table row in the file, returning 146 tuples including garbage like ('Field', 'Value'). The file uses `## CLAIM-ID` section headings with sub-tables containing `| **domain** | Materials Science |` rows. The fix replaces table-row scanning with regex-based heading detection + domain extraction from following lines.

Output: Fixed agent_chronicle.py that returns exactly 15 (claim_id, domain) tuples. Committed to fix/chronicle-claims branch from main and pushed.
</objective>

<execution_context>
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/workflows/execute-plan.md
@C:/Users/999ye/Downloads/metagenesis-core-public/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@scripts/agent_chronicle.py
@reports/scientific_claim_index.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix read_claim_domains() and commit on fix branch</name>
  <files>scripts/agent_chronicle.py</files>
  <action>
1. Create branch fix/chronicle-claims from main:
   git checkout main && git pull && git checkout -b fix/chronicle-claims

2. Replace the read_claim_domains() function (lines 39-52) with this implementation:

```python
def read_claim_domains():
    """Read scientific_claim_index.md and extract claim-domain pairs.

    The file uses ## CLAIM-ID section headings (e.g., ## MTR-1, ## DRIFT-01)
    with sub-tables containing | **domain** | Value | rows.
    """
    index_path = REPO_ROOT / "reports" / "scientific_claim_index.md"
    if not index_path.exists():
        return []
    content = index_path.read_text(encoding="utf-8", errors="ignore")

    # Match ## headings that look like claim IDs (uppercase letters, digits, hyphens)
    heading_re = re.compile(r'^## ([A-Z][A-Z0-9_-]+(?:-\d+)?)\s*$', re.MULTILINE)
    domain_re = re.compile(r'\|\s*\*\*domain\*\*\s*\|\s*(.+?)\s*\|', re.IGNORECASE)

    domains = []
    for heading_match in heading_re.finditer(content):
        claim_id = heading_match.group(1)
        # Search for **domain** row in the text following this heading
        # until the next ## heading or end of file
        start = heading_match.end()
        next_heading = heading_re.search(content, start)
        section = content[start:next_heading.start() if next_heading else len(content)]
        domain_match = domain_re.search(section)
        domain = domain_match.group(1).strip() if domain_match else ""
        domains.append((claim_id, domain))

    return domains
```

3. Verify the fix works:
   python -c "import sys; sys.path.insert(0,'.'); from scripts.agent_chronicle import read_claim_domains; pairs = read_claim_domains(); print(f'Count: {len(pairs)}'); [print(f'  {cid}: {dom}') for cid, dom in pairs]; assert len(pairs) == 15, f'Expected 15, got {len(pairs)}'"

4. Run verification gates:
   python scripts/steward_audit.py
   python -m pytest tests/ -q
   python scripts/deep_verify.py

5. Commit and push:
   git add scripts/agent_chronicle.py
   git commit -m "fix: read_claim_domains() use regex heading parser instead of table rows"
   git push origin fix/chronicle-claims
  </action>
  <verify>
    <automated>python -c "from scripts.agent_chronicle import read_claim_domains; pairs = read_claim_domains(); assert len(pairs) == 15, f'Expected 15, got {len(pairs)}'; assert pairs[0][0] == 'MTR-1'; assert pairs[0][1] == 'Materials Science'; assert pairs[-1][0] == 'AGENT-DRIFT-01'; print('PASS: 15 claim-domain pairs extracted correctly')"</automated>
  </verify>
  <done>read_claim_domains() returns exactly 15 (claim_id, domain) tuples matching all 15 active claims. Fix committed to fix/chronicle-claims and pushed.</done>
</task>

</tasks>

<verification>
- read_claim_domains() returns exactly 15 tuples
- Each tuple contains a valid claim ID from ## headings
- Each tuple contains the correct domain from **domain** table row
- All verification gates pass (steward_audit, pytest, deep_verify)
- Branch fix/chronicle-claims pushed to origin
</verification>

<success_criteria>
- python -c assertion: len(pairs) == 15, all claim IDs correct, all domains non-empty
- python scripts/steward_audit.py -> PASS
- python -m pytest tests/ -q -> all pass
- git log shows commit on fix/chronicle-claims
</success_criteria>

<output>
After completion, create `.planning/quick/260320-hmk-fix-agent-chronicle-py-read-claim-domain/260320-hmk-SUMMARY.md`
</output>
