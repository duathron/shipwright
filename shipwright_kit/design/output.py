"""Output-format contract. Core formats are stdlib-only; `rich` is lazy.
`console` is a distinct reduced-density plain formatter (not Rich-no-color)."""

from __future__ import annotations

import csv as _csv
import io
import json
from typing import Protocol, runtime_checkable

from .glyphs import tier_label
from .tiers import Severity

VALID_FORMATS = ("rich", "console", "json", "ndjson", "csv")

# render(fmt="json") envelope contract version (G10). Bump = structural break;
# update the golden test + a migration note (docs/release-policy.md).
OUTPUT_SCHEMA_VERSION = 1


@runtime_checkable
class Renderable(Protocol):
    def rows(self) -> list[dict]: ...

    def tier(self) -> Severity: ...


def render(obj: Renderable, fmt: str = "console", *, ascii_only: bool = False) -> str:
    if fmt not in VALID_FORMATS:
        raise ValueError(f"unknown format {fmt!r}; valid: {', '.join(VALID_FORMATS)}")
    rows = list(obj.rows())
    if fmt == "json":
        return json.dumps({"schema_version": OUTPUT_SCHEMA_VERSION, "tier": obj.tier().label, "rows": rows}, indent=2)
    if fmt == "ndjson":
        return "\n".join(json.dumps(r) for r in rows)
    if fmt == "csv":
        if not rows:
            return ""
        buf = io.StringIO()
        writer = _csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()
    if fmt == "console":
        head = tier_label(obj.tier(), ascii_only=ascii_only)
        body = ["  " + " ".join(f"{k}={v}" for k, v in r.items()) for r in rows]
        return "\n".join([head, *body])
    # fmt == "rich" — lazy import
    from rich.console import Console
    from rich.table import Table

    table = Table()
    if rows:
        for key in rows[0]:
            table.add_column(str(key))
        for r in rows:
            table.add_row(*[str(v) for v in r.values()])
    buf = io.StringIO()
    Console(file=buf, force_terminal=False, no_color=True).print(table)
    return buf.getvalue()
