import io
import sys

from shipwright.design.console import get_console, supports_color, supports_unicode


class _Pipe(io.StringIO):
    def isatty(self):
        return False


class _Tty(io.StringIO):
    encoding = "utf-8"

    def isatty(self):
        return True


def test_no_color_env_disables_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert supports_color(_Tty()) is False


def test_pipe_disables_color(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert supports_color(_Pipe()) is False  # non-tty → no color
    assert supports_color(_Tty()) is True


def test_unicode_probe(monkeypatch):
    monkeypatch.delenv("WT_SESSION", raising=False)
    monkeypatch.delenv("ANSICON", raising=False)
    assert supports_unicode(_Tty()) is True  # utf-8 encoding
    ascii_stream = _Tty()
    ascii_stream.encoding = "cp1252"
    assert supports_unicode(ascii_stream) is False


def test_get_console_lazy_imports_rich():
    for m in list(sys.modules):
        if m == "rich" or m.startswith("rich."):
            del sys.modules[m]
    import shipwright.design.console  # noqa: F401

    assert "rich" not in sys.modules  # module import is light
    c = get_console(no_color=True)  # NOW rich loads
    assert "rich" in sys.modules
    assert c is not None
