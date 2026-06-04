# tests/test_packs_entrypoint.py
from importlib.metadata import entry_points

from shipwright_kit.security.theme import SecurityTheme


def test_security_pack_is_discoverable():
    eps = entry_points(group="shipwright_kit.packs")
    names = {e.name for e in eps}
    assert "security" in names
    loaded = next(e for e in eps if e.name == "security").load()
    assert loaded is SecurityTheme
