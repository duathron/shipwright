import sys


def test_eval_and_security_eval_are_import_light():
    for m in list(sys.modules):
        if m.startswith(("rich", "pyfiglet")):
            del sys.modules[m]
    import shipwright.eval  # noqa: F401
    import shipwright.security.eval  # noqa: F401

    assert "rich" not in sys.modules and "pyfiglet" not in sys.modules
