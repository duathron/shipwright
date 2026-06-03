"""Themeable palette: maps a tier to a style token (a plain string the rich
renderer later consumes). Stdlib-only — no Rich import here."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .tiers import Severity


@runtime_checkable
class Theme(Protocol):
    name: str

    def style(self, tier: Severity) -> str: ...


class DefaultTheme:
    name = "default"
    _STYLES = {
        Severity.OK: "green",
        Severity.INFO: "cyan",
        Severity.NOTICE: "blue",
        Severity.WARN: "yellow",
        Severity.CRITICAL: "bold red",
    }

    def style(self, tier: Severity) -> str:
        return self._STYLES[tier]


class ColorblindTheme:
    """Blue/orange-leaning, avoids red/green reliance (deuteranopia-safe).
    Colour is never the sole signal — see glyphs.tier_label."""

    name = "colorblind"
    _STYLES = {
        Severity.OK: "blue",
        Severity.INFO: "cyan",
        Severity.NOTICE: "white",
        Severity.WARN: "yellow",
        Severity.CRITICAL: "bold magenta",
    }

    def style(self, tier: Severity) -> str:
        return self._STYLES[tier]
