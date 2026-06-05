"""Tests for the Typer app factory.

NOTE (typer 0.26.7 quirk): invoking a Typer app that has 0 commands raises
RuntimeError, and an app with exactly 1 command collapses to single-command mode
(a subcommand name is parsed as an argument). So we assert structurally, and we
add a 2nd command before invoking the `version` subcommand — which is exactly the
real-world case (the scaffolded main.py is a multi-command app).
"""

from __future__ import annotations

import subprocess
import sys

import typer
from typer.testing import CliRunner

from shipwright_kit.cli import build_typer


def _has_version_command(app: typer.Typer) -> bool:
    return any((c.name or c.callback.__name__).replace("_", "-") == "version" for c in app.registered_commands)


def test_build_typer_returns_configured_app():
    app = build_typer("widget", "Widget CLI")
    assert isinstance(app, typer.Typer)
    assert app.info.name == "widget"
    assert app.info.help == "Widget CLI"
    assert app.info.no_args_is_help is True
    # add_completion lives on the private app._add_completion in typer 0.26.7,
    # not on app.info; assert against the real storage rather than mutating internals.
    assert app._add_completion is False


def test_version_command_registered_and_prints():
    app = build_typer("widget", "Widget CLI", version="1.2.3")
    assert _has_version_command(app)

    # Add a 2nd command so the app is multi-command (real-world shape); then the
    # `version` subcommand resolves and prints.
    @app.command()
    def other() -> None:  # noqa: D401
        typer.echo("other")

    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0, result.stdout
    assert "1.2.3" in result.stdout


def test_no_version_command_without_version():
    app = build_typer("widget", "Widget CLI")
    assert not _has_version_command(app)
    assert app.registered_commands == []


def test_cli_not_imported_by_package_root():
    code = (
        "import importlib, sys; importlib.import_module('shipwright_kit'); "
        "assert 'typer' not in sys.modules, 'typer eagerly imported'; print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
