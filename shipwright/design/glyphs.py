"""Per-tier glyphs with an ASCII fallback. Rule: a tier indicator always
renders symbol + label, never color alone (the #1 colorblind fix)."""

from __future__ import annotations

from .tiers import Severity

_UNICODE: dict[Severity, str] = {
    Severity.OK: "✓",
    Severity.INFO: "ℹ",
    Severity.NOTICE: "•",
    Severity.WARN: "⚠",
    Severity.CRITICAL: "✗",
}
_ASCII: dict[Severity, str] = {
    Severity.OK: "OK",
    Severity.INFO: "i",
    Severity.NOTICE: "*",
    Severity.WARN: "!",
    Severity.CRITICAL: "XX",
}


def glyph(tier: Severity, *, ascii_only: bool = False) -> str:
    return (_ASCII if ascii_only else _UNICODE)[tier]


def tier_label(tier: Severity, *, ascii_only: bool = False) -> str:
    """Symbol + label — never color/symbol alone."""
    return f"{glyph(tier, ascii_only=ascii_only)} {tier.label}"
