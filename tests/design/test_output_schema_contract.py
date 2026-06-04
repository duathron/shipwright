"""Contract lock: render(fmt='json') is versioned; ndjson/csv shapes frozen (G10)."""

from __future__ import annotations

import json

from shipwright_kit.design import OUTPUT_SCHEMA_VERSION, Severity, render


class _Demo:
    def rows(self):
        return [{"name": "a", "score": 1}, {"name": "b", "score": 2}]

    def tier(self):
        return Severity.WARN


def test_output_schema_version_is_1():
    assert OUTPUT_SCHEMA_VERSION == 1


def test_render_json_envelope_contract():
    d = json.loads(render(_Demo(), fmt="json"))
    assert set(d) == {"schema_version", "tier", "rows"}, "json envelope changed — bump OUTPUT_SCHEMA_VERSION"
    assert d["schema_version"] == OUTPUT_SCHEMA_VERSION
    assert isinstance(d["schema_version"], int) and isinstance(d["tier"], str)
    assert d["rows"] == [{"name": "a", "score": 1}, {"name": "b", "score": 2}]


def test_render_ndjson_and_csv_shape_frozen():
    nd = render(_Demo(), fmt="ndjson").splitlines()
    assert [json.loads(x) for x in nd] == [{"name": "a", "score": 1}, {"name": "b", "score": 2}]
    assert render(_Demo(), fmt="csv").splitlines()[0] == "name,score"
