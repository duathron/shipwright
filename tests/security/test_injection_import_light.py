"""Guard: importing the injection module must not pull heavy deps (pydantic)."""

import subprocess
import sys


def test_injection_import_does_not_load_pydantic():
    code = (
        "import importlib, sys; "
        "importlib.import_module('shipwright_kit.security.injection'); "
        "assert 'pydantic' not in sys.modules, sorted(m for m in sys.modules if 'pydantic' in m); "
        "print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_exports_available_from_security_package():
    from shipwright_kit.security import (  # noqa: F401
        InjectionFinding,
        PromptInjectionDetector,
        SeverityLevel,
    )
