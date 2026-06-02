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
