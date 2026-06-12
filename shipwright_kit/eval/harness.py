"""Run a predict function over a corpus and gate the result. Count-and-skip on a
predict-time exception (faithful to barb — a bad row must not abort the run)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .corpus import Sample
from .metrics import EvalResult


class EvalGateError(AssertionError):
    """Raised when an eval result is below the required thresholds."""


@dataclass(frozen=True)
class CorpusDisagreement:
    """A single row where the predictor's output disagrees with the human label."""

    value: str  # the sample input
    label: str  # the human-assigned label
    predicted: str  # what the predictor returned


@dataclass(frozen=True)
class CorpusVerifyReport:
    """Result of :func:`verify_corpus`. Stdlib-only, no rich/pyfiglet import."""

    disagreements: list[CorpusDisagreement]
    total: int
    disagreement_count: int

    @property
    def clean(self) -> bool:
        """True when every row agrees — safe to proceed to floor-setting."""
        return self.disagreement_count == 0

    def summary(self) -> str:
        """Single-line human-readable summary, suitable for stderr."""
        if self.clean:
            return f"corpus-verify: OK — {self.total} rows, 0 disagreements"
        return f"corpus-verify: FAIL — {self.disagreement_count}/{self.total} rows disagree (label vs prediction)"


def verify_corpus(
    corpus: list[Sample],
    predictor: Callable[[str], str],
    *,
    eq: Callable[[str, str], bool] | None = None,
) -> CorpusVerifyReport:
    """Run *predictor* over every labeled row and report label-vs-prediction disagreements.

    Use this **before** setting a precision/recall floor to catch mislabeled or
    dishonest corpus rows — a predictor that is believed correct is compared
    directly to the human label; rows that differ are flagged.

    Parameters
    ----------
    corpus:
        List of :class:`~shipwright_kit.eval.Sample` objects (input + label pairs).
    predictor:
        Callable that maps an input string to a prediction string.  Must be the
        same callable you intend to gate — usually the production classifier.
    eq:
        Optional equality function ``(label, predicted) -> bool``.  Defaults to
        plain string equality (``label == predicted``).  Supply a custom function
        when the label space differs from the prediction space (e.g. case-folding,
        synonyms, or a mapping dict).

    Returns
    -------
    CorpusVerifyReport
        Structured report with the full list of disagreements plus a summary count.
        Predictor exceptions on a row are treated as a disagreement (predicted value
        is set to ``"<error>"``).
    """
    _eq: Callable[[str, str], bool] = eq if eq is not None else (lambda a, b: a == b)
    disagreements: list[CorpusDisagreement] = []
    for sample in corpus:
        try:
            pred = predictor(sample.input)
        except Exception:
            disagreements.append(CorpusDisagreement(sample.input, sample.label, "<error>"))
            continue
        if not _eq(sample.label, pred):
            disagreements.append(CorpusDisagreement(sample.input, sample.label, pred))
    return CorpusVerifyReport(
        disagreements=disagreements,
        total=len(corpus),
        disagreement_count=len(disagreements),
    )


def evaluate(
    predict_fn: Callable[[str], str],
    corpus: list[Sample],
    *,
    positive_pred: Callable[[str], bool],
    positive_expected: Callable[[str], bool] | None = None,
) -> EvalResult:
    binarize_expected = positive_expected or positive_pred  # default = same-space (Phase B)
    tp = fp = tn = fn = errors = 0
    for sample in corpus:
        try:
            pred = predict_fn(sample.input)
        except Exception:  # count-and-skip, surfaced via errors
            errors += 1
            continue
        exp = binarize_expected(sample.label)
        got = positive_pred(pred)
        if exp and got:
            tp += 1
        elif got and not exp:
            fp += 1
        elif exp and not got:
            fn += 1
        else:
            tn += 1
    return EvalResult(tp, fp, tn, fn, errors)


def gate(result: EvalResult, *, min_precision: float, min_recall: float) -> None:
    if result.precision < min_precision:
        raise EvalGateError(f"precision {result.precision:.3f} < {min_precision}")
    if result.recall < min_recall:
        raise EvalGateError(f"recall {result.recall:.3f} < {min_recall}")
    if (result.tp + result.fn) > 0 and result.recall == 0.0:
        raise EvalGateError("zero recall with positives present")
