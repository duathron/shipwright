"""Integration test: corpus -> predict -> metrics -> gate as one operation (G9).
Uses a pure-shipwright predict_fn (no external tool) so it is deterministic."""

from __future__ import annotations

from pathlib import Path

from shipwright.eval.corpus import load_corpus
from shipwright.eval.harness import EvalGateError, evaluate, gate

_FIXTURE = Path(__file__).parent / "fixtures" / "sample.csv"


def _predict(value: str) -> str:
    # trivial but connected classifier: the marker "phish" → phishing
    return "phishing" if "phish" in value else "benign"


def test_full_pipeline_perfect_classifier_passes_gate():
    corpus = load_corpus(_FIXTURE)
    assert len(corpus) == 6  # 6 data rows, 2 comment lines skipped
    result = evaluate(
        _predict,
        corpus,
        positive_pred=lambda p: p == "phishing",
        positive_expected=lambda label: label == "phishing",
    )
    assert (result.tp, result.fp, result.tn, result.fn) == (3, 0, 3, 0)
    assert result.precision == 1.0 and result.recall == 1.0
    gate(result, min_precision=1.0, min_recall=0.70)  # no raise


def test_full_pipeline_blind_classifier_fails_gate():
    corpus = load_corpus(_FIXTURE)
    result = evaluate(
        lambda x: "benign",
        corpus,  # never flags anything
        positive_pred=lambda p: p == "phishing",
        positive_expected=lambda label: label == "phishing",
    )
    assert (result.tp, result.recall) == (0, 0.0)
    try:
        gate(result, min_precision=1.0, min_recall=0.70)
        raise AssertionError("gate should have failed on zero recall")
    except EvalGateError:
        pass
