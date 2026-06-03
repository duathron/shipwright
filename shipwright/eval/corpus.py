"""Labeled-sample corpus loader (CSV/JSON). Trusted local fixture data → STRICT:
a malformed row raises ValueError (unlike liberal external-API parsing)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Sample:
    input: str
    label: str


def _make(row: dict, input_col: str, label_col: str, idx: int) -> Sample:
    try:
        inp, lab = row[input_col], row[label_col]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"corpus row {idx}: missing column {exc}") from exc
    if not inp or not lab:
        raise ValueError(f"corpus row {idx}: empty {input_col!r}/{label_col!r}")
    return Sample(str(inp), str(lab))


def load_corpus(path, *, input_col: str = "input", label_col: str = "label") -> list[Sample]:
    p = Path(path)
    if p.suffix == ".json":
        data = json.loads(p.read_text())
        return [_make(d, input_col, label_col, i) for i, d in enumerate(data)]
    lines = [ln for ln in p.read_text().splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    return [_make(row, input_col, label_col, i) for i, row in enumerate(csv.DictReader(lines))]
