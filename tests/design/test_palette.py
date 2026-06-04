import sys

from shipwright_kit.design.palette import ColorblindTheme, DefaultTheme, Theme
from shipwright_kit.design.tiers import Severity


def test_themes_are_complete_and_stringy():
    for theme in (DefaultTheme(), ColorblindTheme()):
        assert isinstance(theme, Theme)
        for s in Severity:  # completeness: every tier resolves
            style = theme.style(s)
            assert isinstance(style, str) and style


def test_palette_does_not_import_rich():
    for m in list(sys.modules):
        if m == "rich" or m.startswith("rich."):
            del sys.modules[m]
    import shipwright_kit.design.palette  # noqa: F401

    assert "rich" not in sys.modules
