#!/usr/bin/env sh
# Fail if any bundled persona drifts from the vault SSOT.
# No-op (exit 0) when the vault is not available (CI, fresh clones, other machines).
# The vault path comes from $SHIPWRIGHT_VAULT_PERSONAS — never hardcode it (public repo).
set -eu

VAULT="${SHIPWRIGHT_VAULT_PERSONAS:-}"
if [ -z "$VAULT" ] || [ ! -d "$VAULT" ]; then
    echo "bundle-drift: SHIPWRIGHT_VAULT_PERSONAS unset or dir missing — skip (vault-agnostic)."
    exit 0
fi

ROOT="$(CDPATH= cd "$(dirname "$0")/.." && pwd)"
drift=0
checked=0
for f in "$ROOT"/personas/*.md; do
    name="$(basename "$f")"
    [ "$name" = "README.md" ] && continue
    src="$VAULT/$name"
    if [ ! -f "$src" ]; then
        echo "bundle-drift: WARN repo-only persona (no vault SSOT): $name"
        continue
    fi
    checked=$((checked + 1))
    if ! diff -q "$src" "$f" >/dev/null 2>&1; then
        echo "bundle-drift: DRIFT $name"
        drift=1
    fi
done

# Vault dir present but no SSOT files readable (e.g. iCloud-evicted / unreadable)
# → refuse to certify parity rather than fail open.
if [ "$checked" -eq 0 ]; then
    echo "bundle-drift: vault present but no SSOT files readable — refusing to certify. Run: just sync-personas"
    exit 1
fi

if [ "$drift" -ne 0 ]; then
    echo "bundle-drift: bundled personas differ from the vault SSOT. Run: just sync-personas"
    exit 1
fi
echo "bundle-drift: OK (bundled personas match the vault)."
