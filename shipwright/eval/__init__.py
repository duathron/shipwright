"""Generic classification eval harness: corpus, metrics, evaluate + gate."""

from .corpus import Sample, load_corpus
from .harness import EvalGateError, evaluate, gate
from .metrics import EvalResult

__all__ = ["Sample", "load_corpus", "EvalResult", "EvalGateError", "evaluate", "gate"]
