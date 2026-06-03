from hypothesis import given
from hypothesis import strategies as st

from shipwright.design.tiers import Severity, TierMappable


def test_five_ordered_tiers():
    assert [s.name for s in Severity] == ["OK", "INFO", "NOTICE", "WARN", "CRITICAL"]
    assert Severity.OK < Severity.INFO < Severity.NOTICE < Severity.WARN < Severity.CRITICAL


@given(st.sampled_from(list(Severity)), st.sampled_from(list(Severity)))
def test_total_transitive_order(a, b):
    assert (a < b) or (b < a) or (a == b)  # total
    assert (a < b) == (int(a) < int(b))  # consistent with level


def test_tier_mappable_overlay_and_off_axis():
    import enum

    class Verdict(enum.Enum):
        CLEAN = "clean"
        UNKNOWN = "unknown"  # off-axis
        MALICIOUS = "malicious"

        def base_tier(self) -> Severity:
            return {
                Verdict.CLEAN: Severity.OK,
                Verdict.UNKNOWN: Severity.NOTICE,  # explicit off-axis map
                Verdict.MALICIOUS: Severity.CRITICAL,
            }[self]

    assert isinstance(Verdict.CLEAN, TierMappable)  # structural
    assert Verdict.MALICIOUS.base_tier() is Severity.CRITICAL
    # a tool may map FEWER than 5 tiers — that's allowed
    mapped = {v.base_tier() for v in Verdict}
    assert mapped <= set(Severity) and len(mapped) == 3


def test_label_and_role():
    assert Severity.WARN.label == "WARN"
    assert Severity.WARN.role == "warn"
