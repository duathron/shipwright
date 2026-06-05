#!/usr/bin/env bash
# G11 — Template self-test: render the Copier template into a throwaway project
# and run THAT project's own QA gate (sync + lint + format-check + tests), asserting
# green. Proves the scaffolder emits a working, QA-passing project end-to-end (also
# closes G8). Run: `bash scripts/template-selftest.sh [preset]`  (preset: none|security)
set -euo pipefail

PRESET="${1:-none}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

PROJ="$WORKDIR/proj"
echo "== rendering template (preset=$PRESET) into $PROJ =="
uv run copier copy --defaults --vcs-ref HEAD \
  --data project_name="Self Test" \
  --data pypi_name="selftest-tool" \
  --data package_name="selftest_tool" \
  --data cli_command="selftest" \
  --data description="Template self-test fixture" \
  --data env_prefix="SELFTEST" \
  --data preset="$PRESET" \
  "$REPO_ROOT" "$PROJ"

cd "$PROJ"
echo "== generated project tree =="
find . -type f -not -path './.git/*' | sort

echo "== uv sync (builds the generated package + installs deps) =="
uv sync

echo "== generated project QA gate: lint =="
uv run ruff check .
echo "== generated project QA gate: format-check =="
uv run ruff format --check .
echo "== generated project QA gate: tests =="
uv run pytest -q

echo "== generated project QA gate: offline dogfood =="
if [ -f dogfood.sh ]; then
  uv run bash dogfood.sh || { echo "dogfood failed"; exit 1; }
fi

echo "== TEMPLATE SELF-TEST PASSED (preset=$PRESET) =="
