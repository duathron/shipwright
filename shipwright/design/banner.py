"""Plain ASCII banner generator (dep-free). Optional figlet via the `banner`
extra is imported lazily, with a plain fallback if it is absent."""

from __future__ import annotations


def _figlet(name: str) -> str:
    try:
        from pyfiglet import figlet_format
    except (ModuleNotFoundError, ImportError, TypeError):
        return name.upper()
    return figlet_format(name).rstrip("\n")


def make_banner(name: str, version: str, tagline: str = "", *, figlet: bool = False, ascii_only: bool = False) -> str:
    """Return a banner string. Caller decides where to print it (typically stderr)."""
    title = _figlet(name) if figlet else name.upper()
    info = f"v{version}" + (f" | {tagline}" if tagline else "")
    width = max([len(line) for line in title.splitlines()] + [len(info), 12])
    rule = ("-" if ascii_only else "─") * width
    return "\n".join([title, rule, info])
