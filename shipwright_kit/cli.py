"""Typer application factory for Shipwright CLI tools.

Thin, opinionated defaults so every scaffolded CLI is consistent
(``add_completion=False``, ``no_args_is_help=True``) plus an optional
``version`` command. Imports Typer at module load, so this submodule is NOT
imported by ``shipwright_kit/__init__`` — ``import shipwright_kit`` stays
typer-free (import-light). Consumers that import ``shipwright_kit.cli`` already
depend on Typer.
"""

from __future__ import annotations

import typer

__all__ = ["build_typer"]


def build_typer(name: str, help: str, *, version: str | None = None) -> typer.Typer:
    """Return a Typer app with Shipwright's standard defaults. If ``version`` is
    given, register a ``version`` command that prints it."""
    app = typer.Typer(
        name=name,
        help=help,
        add_completion=False,
        no_args_is_help=True,
    )
    if version is not None:

        @app.command()
        def version_() -> None:  # registered as "version"
            """Print the version."""
            typer.echo(version)

        version_.__name__ = "version"

    return app
