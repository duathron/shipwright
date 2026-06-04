# Security Policy

## Reporting a Vulnerability
Report security vulnerabilities **privately** via GitHub's
[private vulnerability reporting](https://github.com/duathron/shipwright/security/advisories/new)
(repo **Security** tab → **Report a vulnerability**). This keeps the report
confidential between you and the maintainers.

Do **not** open a public issue for an undisclosed vulnerability. Expect an
acknowledgement within 7 days.

## Secret Hygiene
This repo and every project it scaffolds run a `gitleaks` pre-commit and CI
gate. Never commit API keys, tokens, or private paths. Use `.env` (gitignored)
and the per-project config hierarchy for secrets.
