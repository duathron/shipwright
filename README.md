# coding-framework

> Provisional name — a distributable, **AI-agent-operated development framework**.

A single, reusable home for the standards, tooling, and CI/CD that develop
software projects start-to-finish. The framework owns the complexity; the
operator decides and approves while AI agents execute. It ships its own
standards and **dogfoods them** — this repo passes the exact gates it gives to
the projects built with it.

## The `projects/` model

The framework repo contains **no project code**. Projects stay their own
independent Git repositories and their own packages. Locally, you clone each
project into the **gitignored** `projects/` directory, where a
[uv](https://docs.astral.sh/uv/) workspace ties them together for development
and testing:

```
coding-framework/
├─ tooling/ruff-base.toml   # single source of truth for lint rules
├─ justfile                 # shared task verbs (lint / fmt / test)
├─ .pre-commit-config.yaml  # local gate (ruff + gitleaks) mirroring CI
├─ .github/workflows/ci.yml # dogfood CI
└─ projects/                # GITIGNORED, local-only
       <your-project>/      # its own repo + own package
```

Because `projects/` is gitignored, the framework never contains your code and
stays generic — anyone can clone it and plug in their own projects.

## Quality-gate ladder

Work is promoted through gates; failing a rung blocks promotion:

```
commit → lint + unit (auto) → build → smoke (auto) →
QM gate (manual) → beta sign-off (manual) → release
```

> The reusable CI/CD that wires these gates, the project scaffolder, and the
> agent skills are built in later milestones. This repo currently provides the
> foundation: the shared config, local task runner, gates, and dogfood CI.

## Quickstart

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and
[just](https://github.com/casey/just).

```bash
uv sync --dev              # create the dev environment
uv run pre-commit install  # install the local gate
just lint                  # ruff check + format-check
just test                  # pytest
```

The local gate (`pre-commit`) runs the same checks as CI, so "passes locally"
means "passes in CI."

## License

[MIT](LICENSE) © 2026 Christian Huhn
