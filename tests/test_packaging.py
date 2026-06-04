import sys


def test_import_is_light_no_rich():
    # `import shipwright` must not pull Rich (import latency / zero mandatory non-stdlib deps).
    for m in list(sys.modules):
        if m == "rich" or m.startswith("rich."):
            del sys.modules[m]
    import shipwright  # noqa: F401

    assert "rich" not in sys.modules, "importing shipwright must not import rich"


def test_version_matches_package_metadata():
    import importlib.metadata

    import shipwright

    # __version__ is a literal string kept in sync with the package version.
    # release-please bumps pyproject [project] version + __init__ together, so
    # assert consistency with the installed dist metadata rather than a frozen literal.
    assert isinstance(shipwright.__version__, str)
    assert shipwright.__version__ == importlib.metadata.version("shipwright")
