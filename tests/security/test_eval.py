from shipwright.design.tiers import Severity
from shipwright.security.eval import (
    SECURITY_MIN_PRECISION,
    SECURITY_MIN_RECALL,
    is_alert,
    tier_breakdown,
)


def test_alert_default_notice_reproduces_barb_positive_set():
    # barb positive = {SUSPICIOUS, HIGH_RISK, PHISHING} == Severity >= NOTICE
    assert is_alert(Severity.OK) is False
    assert is_alert(Severity.INFO) is False
    assert is_alert(Severity.NOTICE) is True
    assert is_alert(Severity.WARN) is True
    assert is_alert(Severity.CRITICAL) is True


def test_alert_threshold_override():
    assert is_alert(Severity.NOTICE, alert_at=Severity.WARN) is False


def test_security_defaults():
    assert SECURITY_MIN_PRECISION == 1.0
    assert SECURITY_MIN_RECALL == 0.70


def test_tier_breakdown_golden():
    items = [(Severity.OK, "benign"), (Severity.CRITICAL, "phishing"), (Severity.OK, "benign")]
    out = tier_breakdown(items)
    assert "OK | benign | 2" in out
    assert "CRITICAL | phishing | 1" in out
