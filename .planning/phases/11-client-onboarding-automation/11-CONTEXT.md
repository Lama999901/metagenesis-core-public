# Phase 11: Client Onboarding Automation - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Build agent_pilot.py — an autonomous agent that processes pilot form submissions into verified bundles with email drafts. Turns a 2-hour manual process into 2 minutes. Input: CSV from Formspree. Output: verified bundle + email draft + queue tracking.

</domain>

<decisions>
## Implementation Decisions

### Domain Detection & Input
- Input format: CSV with columns name, email, company, domain_description, date
- Domain detection: keyword matching on description text (ml/ai/model→ML, drug/pharma→pharma, material/steel/aluminum→materials, etc.)
- Fallback: default to ML if domain can't be detected, flag for review in queue

### Email Draft & Queue
- Email drafts: plain text files in reports/pilot_drafts/{name}_{date}.txt
- Draft content: greeting + PASS result + bundle summary + "next step: $299 Stripe link" + signature
- Stripe link hardcoded: https://buy.stripe.com/14AcN57qH19R1qN3QQ6Na00
- Queue status: pending → processed → sent (manual --mark-sent flag)

### Claude's Discretion
- Internal code organization of agent_pilot.py
- Error handling for malformed CSV rows
- Bundle output directory structure

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- scripts/mg_client.py — existing client bundle generator (--domain flag, --demo mode)
- scripts/agent_*.py — established agent pattern (argparse, io.TextIOWrapper, REPO_ROOT)
- backend/progress/runner.py — dispatches claims by domain

### Established Patterns
- Agent scripts use argparse with --help
- Windows encoding: io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
- File paths use Path from pathlib
- JSON output uses json.dumps with sort_keys=True

### Integration Points
- mg_client.py --domain {domain} generates bundles
- reports/ directory for output files
- system_manifest.json for metadata

</code_context>

<specifics>
## Specific Ideas

- Formspree posts to metagenesis-core.dev/#pilot (form ID xlgpdwop)
- User exports CSV from Formspree dashboard
- agent_pilot.py --process submissions.csv reads and processes each row
- agent_pilot.py --help shows usage
- agent_pilot.py --status shows queue state
- reports/pilot_queue.json is the state file
- reports/pilot_drafts/ contains email draft files

</specifics>

<deferred>
## Deferred Ideas

- Zoho Mail API integration for automated sending (v2)
- Formspree webhook for automatic ingestion (v2)
- Web dashboard for queue management (v2)

</deferred>
