# tests/test_dependabot_policy.py
"""Majors must never land inside grouped Dependabot PRs (W3-c)."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / ".github" / "dependabot.yml",
    ROOT / "templates" / "python-cli" / "project" / ".github" / "dependabot.yml",
]


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_group_excludes_major_updates(path):
    cfg = yaml.safe_load(path.read_text())
    groups = [(e["package-ecosystem"], name, g) for e in cfg["updates"] for name, g in e.get("groups", {}).items()]
    assert groups
    for eco, name, group in groups:
        admitted = {f"version-update:semver-{t}" for t in group.get("update-types", ["major", "minor", "patch"])}
        assert "version-update:semver-major" not in admitted, f"{eco}/{name} admits majors"
        assert admitted, f"{eco}/{name} admits nothing"
