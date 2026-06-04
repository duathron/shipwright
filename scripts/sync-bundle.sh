#!/usr/bin/env sh
# Refresh the bundled personas from the vault SSOT (vault -> repo).
# Requires $SHIPWRIGHT_VAULT_PERSONAS (absolute path to AI/AGENT PERSONAS/Agents).
set -eu

VAULT="${SHIPWRIGHT_VAULT_PERSONAS:-}"
if [ -z "$VAULT" ] || [ ! -d "$VAULT" ]; then
    echo "sync-bundle: set SHIPWRIGHT_VAULT_PERSONAS to the vault personas dir first." >&2
    exit 2
fi

ROOT="$(CDPATH= cd "$(dirname "$0")/.." && pwd)"
n=0
for f in "$ROOT"/personas/*.md; do
    name="$(basename "$f")"
    [ "$name" = "README.md" ] && continue
    src="$VAULT/$name"
    if [ ! -f "$src" ]; then
        echo "sync-bundle: WARN no vault SSOT for $name — left untouched." >&2
        continue
    fi
    cp "$src" "$f"
    n=$((n + 1))
done
if [ "$n" -eq 0 ]; then
    echo "sync-bundle: vault present but no SSOT files readable (iCloud-evicted?) — nothing copied." >&2
    exit 2
fi
echo "sync-bundle: refreshed $n bundled personas from the vault."
