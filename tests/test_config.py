"""Tests for the import-light config mechanism."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from shipwright_kit.config import app_dir, load_config, resolve_config_file


def test_app_dir_path(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    d = app_dir("widget", create=False)
    assert d == tmp_path / ".widget"
    assert not d.exists()


def test_app_dir_create_is_owner_only(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    d = app_dir("widget", create=True)
    assert d.is_dir()
    assert (d.stat().st_mode & 0o777) == 0o700


def test_app_dir_enforces_mode_on_existing(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".widget").mkdir(mode=0o755)
    d = app_dir("widget", create=True)
    assert (d.stat().st_mode & 0o777) == 0o700  # chmod-after hardens a loose pre-existing dir


def test_resolve_first_existing(tmp_path):
    a, b = tmp_path / "a.yml", tmp_path / "b.yml"
    b.write_text("x")
    assert resolve_config_file([None, a, b]) == b
    assert resolve_config_file([None, a]) is None


def test_load_config_uses_first_existing_then_validates(tmp_path):
    f = tmp_path / "c.yml"
    f.write_text("ignored")
    seen = {}

    def loader(p):
        seen["path"] = p
        return {"k": 1}

    out = load_config([None, f], loader=loader, validator=lambda d: ("ok", d))
    assert seen["path"] == f
    assert out == ("ok", {"k": 1})


def test_load_config_no_file_validates_empty(tmp_path):
    out = load_config([None, tmp_path / "missing.yml"], loader=lambda p: {"never": True}, validator=lambda d: d)
    assert out == {}  # loader not called; validator({})


def test_import_light_no_pydantic_or_yaml():
    code = (
        "import importlib, sys; importlib.import_module('shipwright_kit.config'); "
        "bad=[m for m in sys.modules if m.split('.')[0] in {'pydantic','yaml','typer','rich'}]; "
        "assert not bad, bad; print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
