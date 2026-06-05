"""Import-light config mechanism shared by Shipwright CLI tools.

Owns the *mechanism* only — a secure per-tool app directory, ordered-candidate
config-file resolution, and a resolve->load->validate skeleton. The consumer
injects its own yaml ``loader`` and (pydantic) ``validator`` callables, so this
module stays stdlib-only and ``import shipwright_kit.config`` pulls no
pyyaml/pydantic/typer. Each tool keeps its own config *schema*, env-override
step, ``save_config`` and ``.env`` handling.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TypeVar

__all__ = ["app_dir", "load_config", "resolve_config_file"]

T = TypeVar("T")

_OWNER_ONLY = 0o700


def app_dir(name: str, *, create: bool = False, mode: int = _OWNER_ONLY) -> Path:
    """Return ``~/.{name}``. With ``create=True`` make it owner-only (mkdir + chmod,
    so a pre-existing loose-permission dir is hardened too)."""
    d = Path.home() / f".{name}"
    if create:
        d.mkdir(mode=mode, parents=True, exist_ok=True)
        d.chmod(mode)
    return d


def resolve_config_file(candidates: Iterable[Path | None]) -> Path | None:
    """Return the first candidate that exists (``None`` entries skipped)."""
    for c in candidates:
        if c is not None and c.exists():
            return c
    return None


def load_config(
    candidates: Iterable[Path | None],
    *,
    loader: Callable[[Path], dict],
    validator: Callable[[dict], T],
) -> T:
    """Resolve the first existing candidate, ``loader`` it to a dict, and
    ``validator`` that dict into a config object. If no candidate exists, the
    loader is NOT called and ``validator({})`` is returned."""
    path = resolve_config_file(candidates)
    data = loader(path) if path is not None else {}
    return validator(data)
