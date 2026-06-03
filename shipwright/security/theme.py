"""Security pack default theme — maps the generic Severity tiers to threat
verdict labels (CLEAN→MALICIOUS) and a green→red palette. Tools keep their own
verdict enums and map them to Severity via TierMappable (see tests for barb/vex
worked examples). Stdlib-only."""

from __future__ import annotations

from shipwright.design.tiers import Severity

SECURITY_LABELS: dict[Severity, str] = {
    Severity.OK: "CLEAN",
    Severity.INFO: "LOW",
    Severity.NOTICE: "SUSPICIOUS",
    Severity.WARN: "HIGH",
    Severity.CRITICAL: "MALICIOUS",
}


class SecurityTheme:
    name = "security"
    _STYLES = {
        Severity.OK: "green",
        Severity.INFO: "cyan",
        Severity.NOTICE: "yellow",
        Severity.WARN: "dark_orange",
        Severity.CRITICAL: "bold red",
    }

    def style(self, tier: Severity) -> str:
        return self._STYLES[tier]


def label(tier: Severity) -> str:
    return SECURITY_LABELS[tier]
