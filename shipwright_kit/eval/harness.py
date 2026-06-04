"""Run a predict function over a corpus and gate the result. Count-and-skip on a
predict-time exception (faithful to barb — a bad row must not abort the run)."""

from __future__ import annotations

from collections.abc import Callable

from .corpus import Sample
from .metrics import EvalResult


class EvalGateError(AssertionError):
    """Raised when an eval result is below the required thresholds."""


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
