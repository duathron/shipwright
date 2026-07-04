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
        assert SAFE_RENDER_VERSION == 1
