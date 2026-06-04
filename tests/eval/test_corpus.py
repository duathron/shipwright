import json

import pytest

from shipwright_kit.eval.corpus import Sample, load_corpus


def test_csv_with_comments_and_blanks(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("input,label\n# a section\n\n8.8.8.8,benign\nevil.com,phishing\n")
    rows = load_corpus(p)
    assert rows == [Sample("8.8.8.8", "benign"), Sample("evil.com", "phishing")]


def test_json_loads(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"input": "a", "label": "benign"}]))
    assert load_corpus(p) == [Sample("a", "benign")]


def test_input_col_override(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("url,label\nevil.com,phishing\n")
    assert load_corpus(p, input_col="url") == [Sample("evil.com", "phishing")]


def test_missing_column_raises(tmp_path):
    p = tmp_path / "c.csv"
    p.write_text("input,verdict\nx,benign\n")  # no 'label' column
    with pytest.raises(ValueError):
        load_corpus(p)
