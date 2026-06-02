# Security Policy

## Reporting a Vulnerability
Email security reports to duathron@gmail.com. Do not open public issues for
undisclosed vulnerabilities. Expect an acknowledgement within 7 days.

## Secret Hygiene
This repo and every project it scaffolds run a `gitleaks` pre-commit and CI
gate. Never commit API keys, tokens, or private paths. Use `.env` (gitignored)
and the per-project config hierarchy for secrets.
