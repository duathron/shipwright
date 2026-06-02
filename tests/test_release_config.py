# tests/test_release_config.py
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REL = ROOT / "templates" / "release"


def test_release_please_config_is_valid():
    cfg = json.loads((REL / "release-please-config.json").read_text())
    pkg = cfg["packages"]["."]
    assert pkg["release-type"] == "python"
    assert pkg["changelog-path"] == "CHANGELOG.md"


def test_release_please_manifest_is_valid():
    manifest = json.loads((REL / ".release-please-manifest.json").read_text())
    assert manifest["."] == "0.0.0"
