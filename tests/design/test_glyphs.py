from shipwright_kit.design.glyphs import glyph, tier_label
from shipwright_kit.design.tiers import Severity


def test_every_tier_has_unicode_and_ascii():
    for s in Severity:
        u = glyph(s, ascii_only=False)
        a = glyph(s, ascii_only=True)
        assert u and a
        assert a.isascii()


def test_tier_label_is_symbol_plus_label_never_color_only():
    # the indicator must carry text, not just a glyph/color
    out = tier_label(Severity.CRITICAL, ascii_only=True)
    assert "CRITICAL" in out and out != "CRITICAL"  # has a symbol AND the label
    assert out.isascii()
