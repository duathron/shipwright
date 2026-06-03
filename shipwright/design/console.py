"""Accessibility-aware console helpers. Rich is imported lazily inside
`get_console` so `import shipwright` stays light."""

from __future__ import annotations

import os
import sys


def supports_color(stream=None) -> bool:
    stream = stream if stream is not None else sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    isatty = getattr(stream, "isatty", None)
    return bool(isatty and isatty())


def supports_unicode(stream=None) -> bool:
    stream = stream if stream is not None else sys.stdout
    enc = (getattr(stream, "encoding", "") or "").lower()
    if "utf" in enc:
        return True
    return bool(os.environ.get("WT_SESSION") or os.environ.get("ANSICON"))


def get_console(*, no_color: bool = False, force_terminal: bool | None = None):
    """Return a configured Rich Console (lazy import). Requires the `rich` extra."""
    try:
        from rich.console import Console
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("rich output requires `pip install shipwright[rich]`") from exc
    use_color = supports_color() and not no_color
    return Console(no_color=not use_color, force_terminal=force_terminal, safe_box=not supports_unicode())
