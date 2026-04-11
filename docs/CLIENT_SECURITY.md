# Client Security & Privacy

MetaGenesis Core v0.9.0 | PPA: USPTO #63/996,819

---

## What data is collected

When you use `mg_onboard.py` or `mg_contribute.py`, the following data is stored **locally in the repository**:

| Data | Where | Purpose |
|------|-------|---------|
| Anonymous session hash | `reports/onboarding_log.json` | Track unique sessions without identifying users |
| Detected domain | `reports/onboarding_log.json` | Understand which domains are most requested |
| Detected language | `reports/onboarding_log.json` | Understand client language distribution |
| Verification result (PASS/FAIL) | `reports/onboarding_log.json` | Track verification success rate |
| Description length (chars) | `reports/onboarding_log.json` | Quality metric only |
| Contribution text | `reports/client_contributions/` | Your feedback, sanitized |
| Funnel stage counts | `reports/payment_funnel.json` | Anonymous conversion tracking |

## What is NOT collected

- **No personal data** -- no name, email, IP address, or location
- **No model details** -- your model architecture, weights, or training data are never stored
- **No API keys** -- your Anthropic API key is used in-memory only, never written to disk
- **No computation inputs** -- your actual data is processed in-memory and discarded
- **No persistent identifiers** -- session hashes are random, not linked across sessions

## How the session hash works

```
session_id = os.urandom(16)              # 16 random bytes
session_hash = SHA-256(session_id)[:16]  # first 16 hex chars
```

The session hash cannot be reversed to identify you. It exists only to count unique sessions, not to track individuals.

## How contributions are reviewed

1. You submit text via `mg_contribute.py` or the GitHub issue template
2. **Code patterns are stripped** before storage (imports, file paths, scripts, eval/exec calls)
3. Content is limited to 2000 characters
4. Each contribution is SHA-256 signed with its timestamp
5. Contributions are stored in `reports/client_contributions/` as individual JSON files
6. **A human reviews every contribution** before any action is taken
7. Contributions are **never auto-merged** to the main branch

## Content sanitization

The following patterns are automatically removed from contributions:

- Python imports (`import`, `from ... import`)
- Function/class definitions
- System calls (`subprocess`, `os.system`, `eval`, `exec`)
- File paths (Unix and Windows)
- Code blocks (fenced and inline)
- Script injection patterns

## How to verify the verification protocol

MetaGenesis Core is open source. You can verify every aspect:

```bash
# Clone the repository
git clone https://github.com/Lama999901/metagenesis-core-public.git
cd metagenesis-core-public

# Run the full test suite (2380 tests)
python -m pytest tests/ -q

# Run the deep verification (13 proofs)
python scripts/deep_verify.py

# Run the steward audit (governance check)
python scripts/steward_audit.py

# Verify a bundle yourself
python scripts/mg.py verify --pack bundle/
```

Every verification bundle is self-contained. The recipient needs only Python and the `mg.py` script to verify independently. No network access, no API keys, no trust required.

## Threat model

| Threat | Mitigation |
|--------|-----------|
| Code injection via contribution | All code patterns stripped; text-only storage |
| Personal data leakage | No personal data collected; anonymous session hashes only |
| API key exposure | Keys used in-memory only; never written to disk |
| Contribution tampering | SHA-256 signature on every contribution |
| Auto-merge of malicious content | Human review required; never auto-merged |
| Session tracking across visits | Random session IDs; no persistent identifiers |

## Contact

Questions about security or privacy: yehor@metagenesis-core.dev

---

*CLIENT_SECURITY.md v1.0 -- 2026-04-10 -- MetaGenesis Core v0.9.0*
