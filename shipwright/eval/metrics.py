"""Binary-classification metrics, faithful to barb's EvalMetrics. Stdlib-only."""

from __future__ import annotations

from dataclasses import dataclass


def _safe_div(num: float, den: float) -> float:
    return num / den if den else 0.0


@dataclass(frozen=True)
class EvalResult:
    tp: int = 0
    fp: int = 0
    tn: int = 0
    fn: int = 0
    errors: int = 0  # predict-time failures (count-and-skip)

    @property
    def precision(self) -> float:
        return _safe_div(self.tp, self.tp + self.fp)

    @property
    def recall(self) -> float:
        return _safe_div(self.tp, self.tp + self.fn)

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return _safe_div(2 * p * r, p + r)

    @property
    def accuracy(self) -> float:
        return _safe_div(self.tp + self.tn, self.tp + self.fp + self.tn + self.fn)

    @property
    def false_positive_rate(self) -> float:
        return _safe_div(self.fp, self.fp + self.tn)

    @property
    def confusion(self) -> dict[str, int]:
        return {"tp": self.tp, "fp": self.fp, "tn": self.tn, "fn": self.fn}
