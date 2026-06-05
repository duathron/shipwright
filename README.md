# Shipwright

![CI](https://github.com/duathron/shipwright/actions/workflows/ci.yml/badge.svg)
![CodeQL](https://github.com/duathron/shipwright/actions/workflows/codeql.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-%E2%89%A590%25-brightgreen.svg)
![Types](https://img.shields.io/badge/types-mypy-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

Shipwright is two things that share one repo:

- an installable, **import-light Python library** of shared dev-tooling runtime —
  `shipwright_kit.design` (severity tiers + accessible output), `shipwright_kit.eval`
  (detection-quality eval harness), `shipwright_kit.security` (a security pack);
- an **AI-agent-operated development framework** — reusable CI/CD, a Copier
  scaffolder, quality gates, and bundled agent skills + personas — that **dogfoods**
  the library and the gates it hands to the projects built with it.

The library is consumed today by two real tools: **barb** and **sift** both import
`shipwright_kit.eval` to run their detection-quality gates.

## Install

The library is **not on PyPI** — the bare name `shipwright` belongs to an unrelated
project, so the published distribution is **`shipwright-kit`** and the import name is
**`shipwright_kit`**. For now, install from git:

```bash
uv pip install "git+https://github.com/duathron/shipwright@main"
# then: import shipwright_kit
```

> [!NOTE]
> Pin a release tag instead of `@main` for reproducible builds once a tagged
> release of the `shipwright-kit` distribution is cut. Do **not** `pip install
> shipwright` from PyPI — that is a different, unrelated package.

The security pack needs no extra — it ships with the base install and registers
through the `shipwright_kit.packs` entry point.

## Library quickstart

**Run an eval gate** — score a classifier against a labeled corpus and fail if it
misses a floor (the exact pattern barb and sift use):

```python
from shipwright_kit.eval import Sample, evaluate, gate

corpus = [Sample("phish-login", "phishing"),
          Sample("example.com", "benign"),
          Sample("secure-phish", "phishing")]

result = evaluate(
    lambda text: "phishing" if "phish" in text else "benign",
    corpus,
    positive_pred=lambda pred: pred == "phishing",
    positive_expected=lambda label: label == "phishing",
)
print(result.precision, result.recall)        # 1.0 1.0
gate(result, min_precision=1.0, min_recall=0.9)  # raises EvalGateError if below
```

**Use the shared severity tiers** — one generic scale tools map their own verdicts
onto, with accessible (Unicode-or-ASCII) labels:

```python
from shipwright_kit.design import Severity, tier_label

Severity.OK, Severity.INFO, Severity.NOTICE, Severity.WARN, Severity.CRITICAL  # IntEnum 0..4
print(tier_label(Severity.CRITICAL))  # ✗ CRITICAL
print(tier_label(Severity.OK))        # ✓ OK
```

`import shipwright_kit` pulls in no `rich` or `pyfiglet` — the heavy deps load lazily only
when you actually render. Full API: **[docs/library.md](docs/library.md)**.

## The framework

The repo contains **no project code**. Projects stay their own Git repositories and
their own packages; locally you clone each into the **gitignored** `projects/`
directory, where a [uv](https://docs.astral.sh/uv/) workspace ties them together for
development:

```
shipwright/
├─ shipwright_kit/          # the importable library (design / eval / security)
├─ tooling/ruff-base.toml   # single source of truth for lint rules
├─ templates/               # Copier scaffolder (python-cli) + release config
├─ skills/ · personas/      # the agent operating layer (scaffold, onboard, review …)
├─ .github/workflows/       # reusable python-ci.yml + python-release.yml (SHA-pinned)
└─ projects/                # GITIGNORED, local-only — your projects plug in here
```

Work is promoted through gates; failing a rung blocks promotion:

```
commit → lint + unit (auto) → build → dogfood + eval (auto) →
QM gate (manual) → beta sign-off (manual) → release
```

The reusable CI/CD that wires these gates, the Copier scaffolder (`templates/`), and
the agent skills (`skills/`) and personas (`personas/`) all ship now. This repo runs
the exact gates it gives the projects built with it.

## Framework quickstart

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and
[just](https://github.com/casey/just).

```bash
uv sync --dev              # create the dev environment
uv run pre-commit install  # install the local gate
just lint                  # ruff check + format-check
just test                  # pytest
```

The local `pre-commit` gate runs the same lint/format/secret checks as CI; add
`just test` (and `uv build`) for the test and build rungs CI also enforces.

## Docs

- **[docs/library.md](docs/library.md)** — per-module API reference (design / eval / security)
- **[docs/release-policy.md](docs/release-policy.md)** — SemVer + release policy
- **[docs/ci-cd.md](docs/ci-cd.md)** — the reusable CI/CD workflows
- **[CHANGELOG.md](CHANGELOG.md)**

## Security

Report vulnerabilities privately via GitHub's
[private vulnerability reporting](https://github.com/duathron/shipwright/security/advisories/new)
(repo **Security** tab → **Report a vulnerability**). See [SECURITY.md](SECURITY.md).

## Author

**Christian Huhn** — building security tooling for SOC/DFIR workflows.

- GitHub: [@duathron](https://github.com/duathron)
- LinkedIn: [Christian Huhn](https://www.linkedin.com/in/christian-huhn-76a407114)

## License

[MIT](LICENSE) © 2026 Christian Huhn
