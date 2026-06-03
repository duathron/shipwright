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
    positive: Callable[[str], bool],
) -> EvalResult:
    tp = fp = tn = fn = errors = 0
    for sample in corpus:
        try:
            pred = predict_fn(sample.input)
        except Exception:  # count-and-skip
            errors += 1
            continue
        exp = positive(sample.label)
        got = positive(pred)
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
