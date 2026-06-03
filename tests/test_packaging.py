import sys


def test_import_is_light_no_rich():
    # `import shipwright` must not pull Rich (import latency / zero mandatory non-stdlib deps).
    for m in list(sys.modules):
        if m == "rich" or m.startswith("rich."):
            del sys.modules[m]
    import shipwright  # noqa: F401

    assert "rich" not in sys.modules, "importing shipwright must not import rich"


def test_version_is_literal():
    import shipwright

    assert shipwright.__version__ == "0.1.0"
