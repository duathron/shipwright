# tests/security/test_theme.py
import enum
import sys

from shipwright.design.palette import Theme
from shipwright.design.tiers import Severity
from shipwright.security.theme import SECURITY_LABELS, SecurityTheme, label


def test_security_theme_is_complete_theme():
    t = SecurityTheme()
    assert isinstance(t, Theme)
    for s in Severity:
        assert isinstance(t.style(s), str) and t.style(s)


def test_security_labels_map_all_tiers():
    assert SECURITY_LABELS == {
        Severity.OK: "CLEAN",
        Severity.INFO: "LOW",
        Severity.NOTICE: "SUSPICIOUS",
        Severity.WARN: "HIGH",
        Severity.CRITICAL: "MALICIOUS",
    }
    assert label(Severity.CRITICAL) == "MALICIOUS"


def test_barb_verdicts_map_via_overlay():
    # barb RiskVerdict labels → base tiers (worked example, not shipped)
    class RiskVerdict(enum.Enum):
        SAFE = "safe"
        LOW_RISK = "low"
        SUSPICIOUS = "suspicious"
        HIGH_RISK = "high"
        PHISHING = "phishing"

        def base_tier(self) -> Severity:
            return {
                "SAFE": Severity.OK,
                "LOW_RISK": Severity.INFO,
                "SUSPICIOUS": Severity.NOTICE,
                "HIGH_RISK": Severity.WARN,
                "PHISHING": Severity.CRITICAL,
            }[self.name]

    assert RiskVerdict.PHISHING.base_tier() is Severity.CRITICAL
    assert {v.base_tier() for v in RiskVerdict} == set(Severity)  # full 5


def test_vex_verdicts_map_with_off_axis_unknown():
    class Verdict(enum.Enum):
        CLEAN = "clean"
        UNKNOWN = "unknown"
        SUSPICIOUS = "suspicious"
        MALICIOUS = "malicious"

        def base_tier(self) -> Severity:
            return {
                "CLEAN": Severity.OK,
                "UNKNOWN": Severity.NOTICE,  # off-axis
                "SUSPICIOUS": Severity.WARN,
                "MALICIOUS": Severity.CRITICAL,
            }[self.name]

    assert Verdict.UNKNOWN.base_tier() is Severity.NOTICE
    assert len({v.base_tier() for v in Verdict}) == 4  # maps FEWER than 5, allowed


def test_security_import_is_light():
    for m in list(sys.modules):
        if m == "rich" or m.startswith("rich."):
            del sys.modules[m]
    import shipwright.security.theme  # noqa: F401

    assert "rich" not in sys.modules
