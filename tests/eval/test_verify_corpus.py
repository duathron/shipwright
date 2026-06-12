"""Tests for verify_corpus — corpus-honesty tooling (W4)."""

from __future__ import annotations

import pytest

from shipwright_kit.eval import (
    CorpusDisagreement,
    CorpusVerifyReport,
    Sample,
    verify_corpus,
)


def _exact_predictor(x: str) -> str:
    """Predictor that simply echoes the input as if it were the label (perfect agreement)."""
    return x


# ---------------------------------------------------------------------------
# Clean corpus — zero disagreements
# ---------------------------------------------------------------------------


def test_clean_corpus_no_disagreements():
    corpus = [
        Sample("benign.com", "benign"),
        Sample("phish.example", "phishing"),
    ]
    # predictor agrees with every label
    report = verify_corpus(
        corpus, lambda s: s.split(".", 1)[0] if "phish" in s else "benign", eq=lambda label, pred: label == pred
    )
    # let's use a simpler perfectly-agreeing predictor instead
    preds = {"benign.com": "benign", "phish.example": "phishing"}
    report = verify_corpus(corpus, lambda s: preds[s])
    assert report.clean
    assert report.disagreement_count == 0
    assert report.total == 2
    assert report.disagreements == []
    assert "OK" in report.summary()
    assert "0 disagreements" in report.summary()


def test_clean_corpus_is_true():
    corpus = [Sample("a", "benign"), Sample("b", "phishing")]
    preds = {"a": "benign", "b": "phishing"}
    report = verify_corpus(corpus, lambda s: preds[s])
    assert report.clean is True


# ---------------------------------------------------------------------------
# Single mislabeled row
# ---------------------------------------------------------------------------


def test_single_mislabeled_row_flagged():
    corpus = [
        Sample("good.com", "benign"),
        Sample("evil.com", "benign"),  # mislabeled — should be phishing
        Sample("ok.com", "benign"),
    ]
    preds = {"good.com": "benign", "evil.com": "phishing", "ok.com": "benign"}
    report = verify_corpus(corpus, lambda s: preds[s])
    assert not report.clean
    assert report.disagreement_count == 1
    assert report.total == 3
    assert len(report.disagreements) == 1
    d = report.disagreements[0]
    assert d.value == "evil.com"
    assert d.label == "benign"
    assert d.predicted == "phishing"
    assert "FAIL" in report.summary()
    assert "1/3" in report.summary()


# ---------------------------------------------------------------------------
# All rows disagree
# ---------------------------------------------------------------------------


def test_all_disagree_corpus_all_flagged():
    corpus = [
        Sample("a", "benign"),
        Sample("b", "benign"),
        Sample("c", "phishing"),
    ]
    # predictor always returns the opposite
    opposite = {"benign": "phishing", "phishing": "benign"}
    labels = {"a": "benign", "b": "benign", "c": "phishing"}
    report = verify_corpus(corpus, lambda s: opposite[labels[s]])
    assert report.disagreement_count == 3
    assert report.total == 3
    assert len(report.disagreements) == 3
    assert not report.clean


# ---------------------------------------------------------------------------
# Empty corpus
# ---------------------------------------------------------------------------


def test_empty_corpus_no_crash():
    report = verify_corpus([], lambda s: "benign")
    assert report.clean
    assert report.disagreement_count == 0
    assert report.total == 0
    assert report.disagreements == []
    assert "OK" in report.summary()


# ---------------------------------------------------------------------------
# Predictor exception → counted as disagreement with predicted="<error>"
# ---------------------------------------------------------------------------


def test_predictor_exception_counted_as_disagreement():
    corpus = [
        Sample("good", "benign"),
        Sample("boom", "benign"),
    ]

    def predict(s: str) -> str:
        if s == "boom":
            raise RuntimeError("predictor crash")
        return "benign"

    report = verify_corpus(corpus, predict)
    assert report.disagreement_count == 1
    assert report.total == 2
    d = report.disagreements[0]
    assert d.value == "boom"
    assert d.predicted == "<error>"


# ---------------------------------------------------------------------------
# Custom equality function
# ---------------------------------------------------------------------------


def test_custom_eq_case_insensitive():
    corpus = [Sample("x", "Benign"), Sample("y", "Phishing")]
    preds = {"x": "benign", "y": "phishing"}  # lower-case predictions
    # without custom eq → disagrees (case mismatch)
    report_default = verify_corpus(corpus, lambda s: preds[s])
    assert report_default.disagreement_count == 2

    # with case-insensitive eq → agrees
    report_ci = verify_corpus(corpus, lambda s: preds[s], eq=lambda label, pred: label.lower() == pred.lower())
    assert report_ci.clean
    assert report_ci.disagreement_count == 0


# ---------------------------------------------------------------------------
# CorpusDisagreement dataclass is frozen / hashable
# ---------------------------------------------------------------------------


def test_corpus_disagreement_is_frozen():
    d = CorpusDisagreement(value="v", label="l", predicted="p")
    with pytest.raises(Exception):  # frozen dataclass → AttributeError or FrozenInstanceError
        d.value = "other"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Report is importable from the top-level eval package
# ---------------------------------------------------------------------------


def test_top_level_import():
    from shipwright_kit.eval import CorpusDisagreement as CD
    from shipwright_kit.eval import CorpusVerifyReport as CVR
    from shipwright_kit.eval import verify_corpus as vc

    assert CD is CorpusDisagreement
    assert CVR is CorpusVerifyReport
    assert vc is verify_corpus
