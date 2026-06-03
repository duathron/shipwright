# tests/design/test_banner.py
import sys

from shipwright.design.banner import make_banner


def test_plain_banner_has_name_version_tagline():
    out = make_banner("acme", "1.2.0", "Acme Scanner")
    assert "ACME" in out
    assert "v1.2.0" in out
    assert "Acme Scanner" in out


def test_ascii_only_rule_is_ascii():
    out = make_banner("acme", "1.0", ascii_only=True)
    assert out.isascii()
    assert "-" in out and "─" not in out


def test_figlet_without_pyfiglet_falls_back(monkeypatch):
    # simulate pyfiglet absent → no crash, plain title still present
    monkeypatch.setitem(sys.modules, "pyfiglet", None)
    out = make_banner("acme", "1.0", figlet=True)
    assert "ACME" in out


def test_import_is_light():
    for m in list(sys.modules):
        if m in ("pyfiglet", "rich") or m.startswith(("pyfiglet.", "rich.")):
            del sys.modules[m]
    import shipwright.design.banner  # noqa: F401

    assert "pyfiglet" not in sys.modules and "rich" not in sys.modules
