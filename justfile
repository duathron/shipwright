# Run `just` with no args to list available verbs.
default:
    @just --list

# Lint + format-check (single-source ruff config).
lint:
    uv run ruff check .
    uv run ruff format --check .

# Auto-fix formatting.
fmt:
    uv run ruff format .

# Run the test suite.
test:
    uv run pytest -q

# Refresh bundled personas from the vault SSOT (needs $SHIPWRIGHT_VAULT_PERSONAS).
sync-personas:
    sh scripts/sync-bundle.sh

# Fail if bundled personas drift from the vault (no-op without the vault).
check-bundle:
    sh scripts/check-bundle-drift.sh

# Render the template + run the generated project's QA gate (scaffold e2e, G11/G8).
selftest preset="none":
    bash scripts/template-selftest.sh {{ preset }}
