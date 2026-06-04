"""Generic classification eval harness: corpus, metrics, evaluate + gate."""

from .corpus import Sample, load_corpus
from .harness import EvalGateError, evaluate, gate
from .metrics import EVAL_SCHEMA_VERSION, EvalResult

__all__ = ["Sample", "load_corpus", "EvalResult", "EVAL_SCHEMA_VERSION", "EvalGateError", "evaluate", "gate"]
