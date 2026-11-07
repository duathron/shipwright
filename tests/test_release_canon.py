"""Drift guard: the template's release workflow must equal the root CANON.

`.github/workflows/release.yml` is the canonical release workflow; the copier
template ships a copy wrapped in a Jinja raw block with exactly one extra header
comment line (line index 1, right after `name: Release`). Dependabot never edits
`*.jinja`, so without this test the two drift apart silently. The comparison is
byte-exact (no newline normalisation, no CR). Scope: root vs template only;
consumer repos keep their own copies and are re-synced (diffed) by hand on each
shipwright update.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / ".github" / "workflows" / "release.yml"
TEMPLATE = ROOT / "templates" / "python-cli" / "project" / ".github" / "workflows" / "release.yml.jinja"
_RAW = re.compile(r"\{%-\s*raw\s*%\}(.*?)\{%\s*endraw\s*-%\}\s*", re.S)
_HEADER_PREFIX = "# Copy of shipwright"
_HEADER_INDEX = 1  # 0-based line index inside the raw body
# Exact header text (update together with the version on every re-sync).
_HEADER = (
    "# Copy of shipwright `.github/workflows/release.yml` at v0.12.2"
    " - re-sync from shipwright on template update (drift note);"
    " keep this filename - your PyPI Trusted Publisher names it."
)


def _read(path: Path) -> str:
    data = path.read_bytes()
    assert b"\r" not in data, f"{path.name}: CR found (CRLF or lone CR)"
    return data.decode("utf-8")


def template_body(text: str) -> str:
    """Raw-block content of the template minus its single copy-header line."""
    m = _RAW.fullmatch(text)
    assert m is not None, "template is not a single {%- raw %}...{% endraw -%} block"
    lines = m.group(1).split("\n")
    headers = [i for i, ln in enumerate(lines) if ln.startswith(_HEADER_PREFIX)]
    assert headers == [_HEADER_INDEX], f"copy-header must appear exactly once at line {_HEADER_INDEX}, got {headers}"
    assert lines[_HEADER_INDEX] == _HEADER, "copy-header text differs from the expected literal"
    del lines[_HEADER_INDEX]
    return "\n".join(lines)


def test_template_release_matches_canon() -> None:
    body = template_body(_read(TEMPLATE))
    canon = _read(CANON)
    assert canon.endswith("\n") and not canon.endswith("\n\n")
    assert body == canon


def test_template_body_and_canon_parse_to_equal_yaml() -> None:
    body = template_body(_read(TEMPLATE))
    assert yaml.safe_load(body) == yaml.safe_load(_read(CANON))


def test_guard_detects_sha_drift() -> None:
    """The comparison is not vacuous: a changed SHA in the template body differs."""
    text = _read(TEMPLATE)
    sha = re.search(r"@([0-9a-f]{40})", text)
    assert sha is not None
    mutated = text.replace(sha.group(1), "0" * 40, 1)
    assert template_body(mutated) != _read(CANON)
