import pytest
from hypothesis import given
from hypothesis import strategies as st

from shipwright.eval.corpus import Sample
from shipwright.eval.harness import EvalGateError, evaluate, gate


def _positive(label: str) -> bool:
    return label == "phishing"


def test_evaluate_golden_confusion():
    corpus = [
        Sample("a", "phishing"),
        Sample("b", "phishing"),  # 1 caught, 1 missed
        Sample("c", "benign"),
        Sample("d", "benign"),  # 1 clean, 1 false alarm
    ]
    preds = {"a": "phishing", "b": "benign", "c": "benign", "d": "phishing"}
    r = evaluate(lambda x: preds[x], corpus, positive=_positive)
    assert (r.tp, r.fp, r.tn, r.fn) == (1, 1, 1, 1)


def test_predict_exception_is_counted_not_raised():
    corpus = [Sample("ok", "benign"), Sample("boom", "phishing")]

    def predict(x):
        if x == "boom":
            raise RuntimeError("crash")
        return "benign"

    r = evaluate(predict, corpus, positive=_positive)
    assert r.errors == 1  # crashing row counted, run completed
    assert r.tn == 1


def test_gate_passes_and_fails():
    good = evaluate(lambda x: "phishing", [Sample("a", "phishing")], positive=_positive)
    gate(good, min_precision=1.0, min_recall=0.7)  # no raise
    bad = evaluate(lambda x: "benign", [Sample("a", "phishing")], positive=_positive)
    with pytest.raises(EvalGateError):
        gate(bad, min_precision=1.0, min_recall=0.7)  # recall 0


def test_zero_recall_floor():
    # positives exist, recall == 0 → fail even with min_recall=0
    r = evaluate(lambda x: "benign", [Sample("a", "phishing")], positive=_positive)
    with pytest.raises(EvalGateError):
        gate(r, min_precision=0.0, min_recall=0.0)


@given(st.lists(st.sampled_from(["benign", "phishing"]), max_size=20))
def test_evaluate_accounts_for_every_sample(labels):
    corpus = [Sample(str(i), lab) for i, lab in enumerate(labels)]
    r = evaluate(lambda x: "benign", corpus, positive=_positive)
    assert r.tp + r.fp + r.tn + r.fn + r.errors == len(corpus)
