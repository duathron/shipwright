"""Contract lock: the EvalResult serialized shape is versioned + frozen (G10).
A structural change MUST bump EVAL_SCHEMA_VERSION and update this golden + a
migration note — never silently (nightmare N6, library side)."""

from __future__ import annotations

from shipwright_kit.eval import EVAL_SCHEMA_VERSION, EvalResult

_EVAL_V1_KEYS = {
    "schema_version",
    "tp",
    "fp",
    "tn",
    "fn",
    "errors",
    "precision",
    "recall",
    "f1",
    "accuracy",
    "false_positive_rate",
}


def test_eval_schema_version_is_1():
    assert EVAL_SCHEMA_VERSION == 1  # bump deliberately + update the golden below


def test_eval_result_to_dict_contract():
    d = EvalResult(tp=3, fp=1, tn=4, fn=2, errors=0).to_dict()
    assert set(d) == _EVAL_V1_KEYS, "EvalResult.to_dict shape changed — bump EVAL_SCHEMA_VERSION"
    assert d["schema_version"] == EVAL_SCHEMA_VERSION
    assert d["tp"] == 3 and d["fp"] == 1 and d["tn"] == 4 and d["fn"] == 2 and d["errors"] == 0
    # lock TYPES, not just keys (Skeptic): counts int, metrics float
    for k in ("tp", "fp", "tn", "fn", "errors", "schema_version"):
        assert isinstance(d[k], int), k
    for k in ("precision", "recall", "f1", "accuracy", "false_positive_rate"):
        assert isinstance(d[k], float), k
    assert d["precision"] == 0.75 and d["recall"] == 0.6
