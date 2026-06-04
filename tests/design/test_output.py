import json

import pytest
from hypothesis import given
from hypothesis import strategies as st

from shipwright_kit.design.output import VALID_FORMATS, Renderable, render
from shipwright_kit.design.tiers import Severity


class Sample:
    def rows(self):
        return [{"ioc": "8.8.8.8", "verdict": "CLEAN"}, {"ioc": "evil.com", "verdict": "BAD"}]

    def tier(self):
        return Severity.WARN


def test_is_renderable():
    assert isinstance(Sample(), Renderable)


def test_json_golden():
    out = json.loads(render(Sample(), "json"))
    assert out == {
        "schema_version": 1,
        "tier": "WARN",
        "rows": [{"ioc": "8.8.8.8", "verdict": "CLEAN"}, {"ioc": "evil.com", "verdict": "BAD"}],
    }


def test_ndjson_golden():
    lines = render(Sample(), "ndjson").splitlines()
    assert [json.loads(x) for x in lines] == Sample().rows()


def test_csv_golden():  # csv is NET-NEW (vex had no csv)
    assert render(Sample(), "csv") == "ioc,verdict\r\n8.8.8.8,CLEAN\r\nevil.com,BAD\r\n"


def test_console_is_plain_reduced_density_with_symbol_label():
    out = render(Sample(), "console", ascii_only=True)
    assert "WARN" in out and "!" in out  # symbol + label header
    assert "8.8.8.8" in out and "\x1b[" not in out  # no ANSI in plain console


def test_unknown_format_raises():
    with pytest.raises(ValueError):
        render(Sample(), "xml")


@given(st.sampled_from([f for f in VALID_FORMATS if f != "rich"]))
def test_render_never_raises_on_valid_nonrich_format(fmt):
    assert isinstance(render(Sample(), fmt), str)
