"""Security-pack eval helpers: threat binarization + barb's baseline thresholds
+ a per-tier breakdown. Stdlib-only (no rich import)."""

from __future__ import annotations

from collections import Counter

from shipwright_kit.design.tiers import Severity

SECURITY_MIN_PRECISION = 1.0
SECURITY_MIN_RECALL = 0.70


def is_alert(tier: Severity, *, alert_at: Severity = Severity.NOTICE) -> bool:
    """A verdict at/above the alert threshold counts as a positive prediction.
    Default NOTICE reproduces barb's positive set {SUSPICIOUS, HIGH_RISK, PHISHING}."""
    return tier >= alert_at


def tier_breakdown(items: list[tuple[Severity, str]]) -> str:
    """Plain-text benign-vs-malicious counts per tier (no rich → import-light)."""
    counts: Counter = Counter(items)
    lines = ["tier | label | count"]
    for (tier, label), n in sorted(counts.items(), key=lambda kv: (int(kv[0][0]), kv[0][1])):
        lines.append(f"{tier.label} | {label} | {n}")
    return "\n".join(lines)
