"""Generic classification eval harness: corpus, metrics, evaluate + gate."""

from .corpus import Sample, load_corpus
from .harness import CorpusDisagreement, CorpusVerifyReport, EvalGateError, evaluate, gate, verify_corpus
from .metrics import EVAL_SCHEMA_VERSION, EvalResult

__all__ = [
    "Sample",
    "load_corpus",
    "EvalResult",
    "EVAL_SCHEMA_VERSION",
    "EvalGateError",
    "evaluate",
    "gate",
    "CorpusDisagreement",
    "CorpusVerifyReport",
    "verify_corpus",
]
