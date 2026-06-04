"""Generic severity tiers + a domain-overlay protocol."""

from __future__ import annotations

from enum import IntEnum
from typing import Protocol, runtime_checkable


class Severity(IntEnum):
    """Generic 5-tier severity ladder. Tools map their own enums onto it."""

    OK = 0
    INFO = 1
    NOTICE = 2
    WARN = 3
    CRITICAL = 4

    @property
    def label(self) -> str:
        return self.name

    @property
    def role(self) -> str:
        """Color-role key resolved by a Theme (see palette.py)."""
        return self.name.lower()


@runtime_checkable
class TierMappable(Protocol):
    """A domain enum maps to the base ladder via `base_tier()`. May map fewer
    than 5 tiers; off-axis states map explicitly."""

    def base_tier(self) -> Severity: ...
