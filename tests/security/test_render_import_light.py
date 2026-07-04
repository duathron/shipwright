import subprocess
import sys


def test_render_import_loads_neither_pydantic_nor_rich():
    code = (
        "import importlib, sys; "
        "importlib.import_module('shipwright_kit.security.render'); "
        "bad = sorted(m for m in sys.modules if 'pydantic' in m or m == 'rich' or m.startswith('rich.')); "
        "assert not bad, bad; "
        "print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
