import pytest

from shipwright_kit.security.render import SAFE_RENDER_VERSION, safe_render


class TestSafeRender:
    def test_plain_text_unchanged(self):
        assert safe_render("hello world") == "hello world"

    def test_rich_markup_is_escaped_to_literal(self):
        assert safe_render("[red]x[/red]") == r"\[red]x\[/red]"

    def test_escape_markup_false_keeps_brackets_strips_ansi(self):
        assert safe_render("[red]x\x1b[31m", escape_markup=False) == "[red]x"

    def test_backslash_bypass_is_neutralized(self):
        assert safe_render(r"\[red]x") == r"\\\[red]x"

    def test_ansi_csi_stripped(self):
        assert safe_render("\x1b[31mred\x1b[0m") == "red"

    def test_osc_sequence_stripped(self):
        assert safe_render("\x1b]0;pwned\x07visible") == "visible"

    def test_control_chars_stripped_tab_and_newline_kept(self):
        assert safe_render("a\x00b\x07c\td\ne") == "abc\td\ne"

    def test_version_constant(self):
        assert SAFE_RENDER_VERSION == 2


_BIDI_AND_INVISIBLE = [
    "\u200b",
    "\u200e",
    "\u200f",
    "\u202a",
    "\u202b",
    "\u202c",
    "\u202d",
    "\u202e",
    "\u2060",
    "\u2066",
    "\u2067",
    "\u2068",
    "\u2069",
    "\u061c",
    "\ufeff",
]


class TestBidiAndInvisibleStripped:
    """Audit F14: bidi overrides / zero-width characters reorder or hide text."""

    @pytest.mark.parametrize("cp", _BIDI_AND_INVISIBLE, ids=lambda c: f"U+{ord(c):04X}")
    def test_stripped(self, cp):
        payload = "abc" + cp + "dcba"
        assert cp in payload
        out = safe_render(payload)
        assert cp not in out
        assert out == "abcdcba"

    @pytest.mark.parametrize("cp", _BIDI_AND_INVISIBLE, ids=lambda c: f"U+{ord(c):04X}")
    def test_stripped_without_markup_escape(self, cp):
        payload = "abc" + cp + "dcba"
        assert cp in payload
        assert safe_render(payload, escape_markup=False) == "abcdcba"

    def test_tab_and_newline_preserved(self):
        assert safe_render("a\tb\nc") == "a\tb\nc"

    def test_non_ascii_text_preserved(self):
        assert safe_render("M\u00fcller \u6771\u4eac") == "M\u00fcller \u6771\u4eac"

    @pytest.mark.parametrize("cp", ["\u200d", "\u200c"], ids=lambda c: f"U+{ord(c):04X}")
    def test_zwj_and_zwnj_preserved(self, cp):
        payload = "a" + cp + "b"
        assert cp in payload
        assert safe_render(payload) == payload


_MORE_STRIPPED = [
    "\U000e0041",
    "\U000e007f",
    "\u00ad",
    "\u206a",
    "\u206f",
    "\ufff9",
    "\ufffb",
    "\u180e",
    "\u2028",
    "\u2029",
    "\u034f",
]


class TestAllFormatCharsStripped:
    """A1 item 6: every Cf character except ZWJ/ZWNJ, plus U+2028/2029 and U+034F."""

    @pytest.mark.parametrize("cp", _MORE_STRIPPED, ids=lambda c: f"U+{ord(c):04X}")
    def test_stripped(self, cp):
        payload = "abc" + cp + "dcba"
        assert cp in payload
        assert safe_render(payload) == "abcdcba"

    def test_zwj_emoji_sequence_preserved(self):
        seq = "\U0001f468\u200d\U0001f469\u200d\U0001f467"
        assert "\u200d" in seq
        assert safe_render(seq) == seq

    def test_tab_lf_kept(self):
        assert safe_render("a\tb\nc") == "a\tb\nc"
