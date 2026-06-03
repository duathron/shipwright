from hypothesis import given
from hypothesis import strategies as st

from shipwright.eval.metrics import EvalResult


def test_golden_metrics():
    r = EvalResult(tp=7, fp=0, tn=10, fn=3, errors=1)
    assert r.precision == 1.0
    assert round(r.recall, 2) == 0.70
    assert r.accuracy == 17 / 20
    assert r.false_positive_rate == 0.0
    assert r.confusion == {"tp": 7, "fp": 0, "tn": 10, "fn": 3}


def test_zero_denominators_return_zero_not_raise():
    r = EvalResult()  # all zero
    assert r.precision == 0.0 and r.recall == 0.0 and r.f1 == 0.0
    assert r.accuracy == 0.0 and r.false_positive_rate == 0.0


@given(st.integers(0, 1000), st.integers(0, 1000), st.integers(0, 1000), st.integers(0, 1000))
def test_metrics_always_in_unit_interval(tp, fp, tn, fn):
    r = EvalResult(tp, fp, tn, fn)
    for v in (r.precision, r.recall, r.f1, r.accuracy, r.false_positive_rate):
        assert 0.0 <= v <= 1.0
