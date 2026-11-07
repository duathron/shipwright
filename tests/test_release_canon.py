"""Drift guard: the template's release workflow must equal the root CANON.

`.github/workflows/release.yml` is the canonical release workflow; the copier
template ships a copy wrapped in a Jinja raw block with one extra header
comment line. Dependabot never edits `*.jinja`, so without this test the two
drift apart silently. Scope: root vs template only; consumer repos keep their
own copies and are re-synced (diffed) by hand on each shipwright update.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANON = ROOT / ".github" / "workflows" / "release.yml"
TEMPLATE = ROOT / "templates" / "python-cli" / "project" / ".github" / "workflows" / "release.yml.jinja"
_RAW = re.compile(r"\{%-\s*raw\s*%\}(.*?)\{%\s*endraw\s*-%\}\s*", re.S)
_HEADER_PREFIX = "# Copy of shipwright"


def template_body(text: str) -> str:
    """Raw-block content of the template minus the copy-header comment lines."""
    m = _RAW.fullmatch(text)
    assert m is not None, "template is not a single {%- raw %}...{% endraw -%} block"
    lines = [ln for ln in m.group(1).split("\n") if not ln.startswith(_HEADER_PREFIX)]
    return "\n".join(lines).rstrip("\n")


def test_template_release_matches_canon() -> None:
    expected = CANON.read_text(encoding="utf-8").rstrip("\n")
    assert template_body(TEMPLATE.read_text(encoding="utf-8")) == expected


def test_guard_detects_sha_drift() -> None:
    """The comparison is not vacuous: a changed SHA in the template body differs."""
    text = TEMPLATE.read_text(encoding="utf-8")
    sha = re.search(r"@([0-9a-f]{40})", text)
    assert sha is not None
    mutated = text.replace(sha.group(1), "0" * 40, 1)
    expected = CANON.read_text(encoding="utf-8").rstrip("\n")
    assert template_body(mutated) != expected
