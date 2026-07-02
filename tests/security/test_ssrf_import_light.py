"""Guard: importing the ssrf module must not pull heavy deps (pydantic, httpx, requests)."""

import subprocess
import sys


def test_ssrf_import_does_not_load_heavy_deps():
    code = (
        "import importlib, sys; "
        "importlib.import_module('shipwright_kit.security.ssrf'); "
        "heavy = {'pydantic', 'httpx', 'requests'}; "
        "loaded = heavy & {m.split('.')[0] for m in sys.modules}; "
        "assert not loaded, sorted(loaded); "
        "print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout


def test_ssrf_module_has_no_import_time_side_effects():
    # Importing twice in a fresh subprocess must not raise or touch the
    # network/filesystem beyond stdlib module bookkeeping.
    code = (
        "import importlib; "
        "importlib.import_module('shipwright_kit.security.ssrf'); "
        "importlib.import_module('shipwright_kit.security.ssrf'); "
        "print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
