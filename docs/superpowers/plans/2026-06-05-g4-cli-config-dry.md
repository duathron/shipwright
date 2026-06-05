# G4 — CLI/config DRY Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the duplicated CLI/config boilerplate (secure app-dir, the config-resolution skeleton, the Typer app factory) into import-light `shipwright_kit.config` + `shipwright_kit.cli`, wire them into the Copier template, and retrofit vex/barb/sift onto the shared config mechanism — behavior-preserving.

**Architecture:** The library stays `deps=[]` / import-light. `shipwright_kit.config` is **stdlib-only**: it owns the *mechanism* (secure `app_dir`, ordered-candidate file resolution, a `load_config` skeleton) and the consumer **injects** its yaml-`loader` + pydantic-`validator` callables — so pyyaml/pydantic never enter the lib. `shipwright_kit.cli` is a thin **typer-coupled** submodule (`build_typer` factory + version helper); it is NOT imported by `shipwright_kit/__init__` (same lazy pattern as `design.console`/rich), so `import shipwright_kit` stays typer-free. Each tool keeps its own config *schema*, its env-override step (vex's lazy `@property` accessors / barb+sift's eager block), `save_config`, and `.env`/dotenv handling — only the resolve→load→validate skeleton + the secure app-dir move to the lib.

**Tech Stack:** Python 3.11+, stdlib `pathlib`/`typing`/`collections.abc`/`stat`, Typer (consumer-side), pydantic (consumer-side), pyyaml (consumer-side), uv, pytest, ruff (lint AND `format --check` — run BOTH), mypy. Lib released via release-please; consumers pin `shipwright-kit @ git+…@v0.5.0`.

**Scope — 4 repos + a release:**
1. `shipwright` — new `shipwright_kit/config.py` + `shipwright_kit/cli.py` + tests + import-light guard, then **cut v0.5.0**, then wire the **template** (new `config.py.jinja`, thinner `main.py.jinja`).
2. `barb`, `sift` — characterization-test the current `load_config` (neither has config tests today), THEN retrofit onto `shipwright_kit.config` (@v0.5.0).
3. `vex` — retrofit onto `shipwright_kit.config` (already has `tests/test_config.py`); preserve dotenv + packaged-default fallback + the lazy `@property` env accessors + `save_config`.

**Ground-truth (verified 2026-06-05):**
- barb `load_config`: `paths = [p for p in [config_path, ~/.barb/config.yaml, Path("config.yaml")] if p and p.exists()]`; `data = yaml.safe_load(first) or {}` else `{}`; `AppConfig(**data)`; then eager env: `BARB_LLM_KEY -> config.explain.api_key`. `_APP_DIR = ~/.barb`, `_DIR_MODE = 0o700`, `_ensure_app_dir()` = `mkdir(mode=0o700, parents=True, exist_ok=True)` (no chmod-after). No dotenv.
- sift `load_config`: same first-existing path list; `AppConfig(**data)`; loads `~/.sift/.env` (dotenv) THEN eager env `SIFT_LLM_KEY`. `_APP_DIR = ~/.sift`, `_ensure_app_dir()`. `save_config(config, path=None)`, plus `.env` read/write helpers (mode 600).
- vex `load_config`: `load_dotenv()`; priority `explicit > ~/.vex/config.yaml (_USER_CONFIG_PATH) > <pkg>/config.yaml (_DEFAULT_CONFIG_PATH)`; if none → `Config()`; else `Config.model_validate(yaml.safe_load(f) or {})`. Env is LAZY via `@property` (`api_key` reads `VT_API_KEY`, etc.) — NOT applied in load_config. `_ensure_dir(path)` = `mkdir(exist_ok) + chmod(0o700)` (chmod-after, enforces on pre-existing). `save_config` writes `~/.vex/config.yaml` 0o600.
- Each tool: config internals referenced in exactly **3 files**. Current shipwright-kit pins: **barb `@v0.3.0`**, sift `@v0.4.0`, vex `@v0.4.0` → all bump to `@v0.5.0`. (sift already has `tests/test_zero_config.py` — a CLI smoke test, NOT a `load_config` test; the new `tests/test_config.py` won't collide.)
- Template `main.py.jinja` builds `typer.Typer(name=…, help=…, add_completion=False, no_args_is_help=True)` + `classify`/`version` commands; the template currently has **no** config module.

**Decision — app_dir chmod unification (flag for Skeptic):** the lib `app_dir(name, *, create=True)` does `mkdir(mode=0o700) + chmod(0o700)` — the stricter vex behavior (enforces 0o700 even on a pre-existing dir). For barb/sift this is a minor **hardening**, not a functional regression (owner-only perms; files stay owner-readable). Confirm with the Skeptic this is acceptable; if not, add `enforce_mode: bool` and default it per-tool to match exact prior behavior.

---

### Task 0: Library — sync `main` to origin (release-correctness gate)

> **Why:** lib `main` advanced (v0.4.0 + v0.5.0-pending release commits). The G4 `feat:` commits must sit on top of the latest released manifest so release-please proposes the NEXT version, not a colliding one.

- [ ] **Step 1:** `cd shipwright && git fetch origin --tags && git status --short`
- [ ] **Step 2:** stash any dirty `uv.lock` (`git stash push uv.lock` if present).
- [ ] **Step 3:** `git pull --ff-only origin main`
- [ ] **Step 4:** `cat .release-please-manifest.json && git describe --tags` — note the current released version (expected `v0.4.0`, possibly a pending release PR for `0.5.0` from the G11 feat). If a `chore(main): release 0.5.0` PR is already open/merged, the G4 feats target the version AFTER it. Record the baseline before committing.

---

### Task 1: Library — `shipwright_kit.config` (stdlib mechanism)

**Files:**
- Create: `shipwright/shipwright_kit/config.py`
- Test: `shipwright/tests/test_config.py`

- [ ] **Step 1: Write the failing test** `shipwright/tests/test_config.py`:

```python
"""Tests for the import-light config mechanism."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

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
    out = load_config([None, tmp_path / "missing.yml"], loader=lambda p: {"never": True},
                      validator=lambda d: d)
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
```

- [ ] **Step 2: Run → FAIL** (`ModuleNotFoundError: shipwright_kit.config`):
  `cd shipwright && uv run pytest tests/test_config.py -q`

- [ ] **Step 3: Implement** `shipwright/shipwright_kit/config.py`:

```python
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
```

- [ ] **Step 4: Run → PASS:** `cd shipwright && uv run pytest tests/test_config.py -q`
- [ ] **Step 5: Lint + format + types:**
  `uv run ruff check shipwright_kit/config.py tests/test_config.py && uv run ruff format --check shipwright_kit/config.py tests/test_config.py && uv run mypy shipwright_kit/config.py`
- [ ] **Step 6: Commit:**
```bash
cd shipwright
git add shipwright_kit/config.py tests/test_config.py
git commit -m "feat(config): import-light shared config mechanism

app_dir (secure owner-only) + resolve_config_file + a resolve/load/validate
skeleton with consumer-injected loader+validator, so the lib stays stdlib-only
(no pyyaml/pydantic). Consumers keep their own schema + env + save_config.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Library — `shipwright_kit.cli` (Typer factory)

**Files:**
- Create: `shipwright/shipwright_kit/cli.py`
- Test: `shipwright/tests/test_cli.py`

- [ ] **Step 1: Write the failing test** `shipwright/tests/test_cli.py`:

```python
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
    return any(
        (c.name or c.callback.__name__).replace("_", "-") == "version"
        for c in app.registered_commands
    )


def test_build_typer_returns_configured_app():
    app = build_typer("widget", "Widget CLI")
    assert isinstance(app, typer.Typer)
    assert app.info.name == "widget"
    assert app.info.help == "Widget CLI"
    assert app.info.no_args_is_help is True
    assert app.info.add_completion is False


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
    # Importing the package root must NOT pull typer (import-light invariant).
    code = (
        "import importlib, sys; importlib.import_module('shipwright_kit'); "
        "assert 'typer' not in sys.modules, 'typer eagerly imported'; print('ok')"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "ok" in out.stdout
```

- [ ] **Step 2: Run → FAIL:** `cd shipwright && uv run pytest tests/test_cli.py -q`

- [ ] **Step 3: Implement** `shipwright/shipwright_kit/cli.py`:

```python
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
```

> **Implementer note (Skeptic-verified):** the `version_.__name__ = "version"` rename trick is SOUND — Typer derives the command name from `__name__`, giving a `version` subcommand. The earlier worry about `CliRunner().invoke(app, ["version"])` failing is a typer-0.26.7 artifact of *single-command collapse* (an app with only one command parses the subcommand name as an argument → exit 2), NOT a problem with the factory. That collapse never happens in the real scaffolded `main.py` (it has ≥2 commands: `classify` + `version`). The lib test (above) handles it by adding a 2nd command before invoking. Do NOT "fix" build_typer for the single-command case — keep it as written.

- [ ] **Step 4: Run → PASS:** `cd shipwright && uv run pytest tests/test_cli.py -q`
- [ ] **Step 5:** confirm `shipwright_kit/__init__.py` does NOT import `cli` (it shouldn't already; do not add it). Lint+format+mypy the 2 files (mypy may need typer stubs — Typer ships types; if mypy complains about the dynamic command, add a targeted `# type: ignore[misc]` on the decorator line, not a blanket ignore).
- [ ] **Step 6: Full lib suite + commit:**
```bash
cd shipwright && uv run pytest -q && uv run ruff check . && uv run ruff format --check . && uv run mypy shipwright_kit
git add shipwright_kit/cli.py tests/test_cli.py
git commit -m "feat(cli): Typer app factory (build_typer)

Standard Shipwright CLI defaults + optional version command. Typer-coupled
submodule, not imported by the package root, so import shipwright_kit stays
import-light.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: Library — release v0.5.0 (barrier)

> **Release reality (Skeptic-verified):** release-please PR **#10 `chore(main): release 0.5.0`** is ALREADY OPEN (the G11 `feat` opened it; manifest still `0.4.0`, latest tag `v0.4.0`). Pushing the G4 `feat` commits to `main` makes release-please **amend them into PR #10** — so G4 ships in **v0.5.0**, NOT a new 0.6.0. Do NOT cut a separate release. **The tag is `v0.5.0`; all consumer pins below are `@v0.5.0`.**

> **HARD GATE:** Tasks 4–7 pin `@v0.5.0`. Do NOT start them until this completes (PR #10 merged + `v0.5.0` tag pushed + tag contains both new modules).

- [ ] **Step 1:** `cd shipwright && git push origin main`
- [ ] **Step 2:** wait for release-please to refresh PR #10, then `gh pr view 10 --repo duathron/shipwright` — confirm its changelog now lists the G11 template self-test AND the G4 `feat(config)` + `feat(cli)` + `feat(template)` commits, version **0.5.0**.
- [ ] **Step 3:** confirm `main` CI is green, then `gh pr merge 10 --repo duathron/shipwright --squash`.
- [ ] **Step 4:** `git fetch origin --tags`; confirm `v0.5.0`; verify it contains the modules:
  `git show v0.5.0:shipwright_kit/config.py | head -3 && git show v0.5.0:shipwright_kit/cli.py | head -3`

---

### Task 4: Template — consume `cli` + add a `config.py.jinja`

**Files:**
- Create: `shipwright/templates/python-cli/project/{{ package_name }}/config.py.jinja`
- Modify: `shipwright/templates/python-cli/project/{{ package_name }}/main.py.jinja`
- Modify: `shipwright/templates/python-cli/project/pyproject.toml.jinja` (bump the `shipwright-kit @ …@main` is fine — template tracks main; leave as-is)

- [ ] **Step 1:** Create `config.py.jinja` — a minimal, real config module using the lib mechanism:

```jinja
"""{{ project_name }} configuration: ~/.{{ cli_command }}/config.yaml + env > defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

from shipwright_kit.config import app_dir, load_config

_APP_DIR = app_dir("{{ cli_command }}")


class OutputConfig(BaseModel):
    default_format: str = "rich"


class AppConfig(BaseModel):
    output: OutputConfig = OutputConfig()


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load(config_path: Optional[Path] = None) -> AppConfig:
    """Resolve {{ env_prefix }}-style config: explicit > ~/.{{ cli_command }}/config.yaml > ./config.yaml > defaults."""
    return load_config(
        [config_path, _APP_DIR / "config.yaml", Path("config.yaml")],
        loader=_load_yaml,
        validator=AppConfig.model_validate,
    )
```

- [ ] **Step 2:** Rewire `main.py.jinja` to use `build_typer` + the config:

```jinja
"""{{ project_name }} — CLI entry point."""

from __future__ import annotations

from rich.console import Console

from shipwright_kit.cli import build_typer

from {{ package_name }} import __version__
from {{ package_name }}.detect import classify as classify_input

app = build_typer("{{ cli_command }}", "{{ description }}", version=__version__)
console = Console()


@app.command()
def classify(value: str) -> None:
    """Classify an input string (example parse boundary)."""
    console.print(classify_input(value))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

> Note: `build_typer(..., version=__version__)` provides the `version` command, so the hand-written `version` command is removed. `classify`'s `typer.Argument` is dropped to avoid importing typer in main; a bare `str` positional works. If the existing `test_detect`/CLI tests assert a typer.Argument help string, keep `import typer` and `typer.Argument(...)` — verify against `tests/`.

- [ ] **Step 3:** Run the template self-test for BOTH presets:
  `cd shipwright && bash scripts/template-selftest.sh none && bash scripts/template-selftest.sh security`
  Expected: both reach `TEMPLATE SELF-TEST PASSED`. This is the proof the wired template still scaffolds a green project. Fix any rendered-project lint/format/test failure (the self-test is the gate).

- [ ] **Step 4:** Commit:
```bash
cd shipwright
git add "templates/python-cli/project/{{ package_name }}/config.py.jinja" "templates/python-cli/project/{{ package_name }}/main.py.jinja"
git commit -m "feat(template): scaffold config.py + use build_typer (G4)

Generated projects now ship a real config module (shipwright_kit.config
mechanism) and build their Typer app via shipwright_kit.cli.build_typer.
Proven green by the template self-test, both presets.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: barb — characterization-test then retrofit `load_config`

**Files:**
- Modify: `projects/barb/pyproject.toml` (pin → vNEXT)
- Create: `projects/barb/tests/test_config.py` (characterization — barb has none)
- Modify: `projects/barb/barb/config.py`

- [ ] **Step 1: Pin + sync:** set `shipwright-kit @ …@vNEXT` in `projects/barb/pyproject.toml`; `cd projects/barb && uv sync --reinstall-package shipwright-kit`.
- [ ] **Step 2: Characterization tests** (capture CURRENT behavior BEFORE touching config.py) — `projects/barb/tests/test_config.py`:

```python
"""Characterization tests for barb config loading (pin behavior before G4 retrofit)."""

from __future__ import annotations

import textwrap
from pathlib import Path

from barb.config import AppConfig, load_config


def test_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no ./config.yaml
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    cfg = load_config()
    assert isinstance(cfg, AppConfig)


def test_explicit_path_wins(tmp_path):
    f = tmp_path / "c.yaml"
    f.write_text(textwrap.dedent("output:\n  default_format: json\n"))
    cfg = load_config(f)
    assert cfg.output.default_format == "json"


def test_env_override_llm_key(tmp_path, monkeypatch):
    monkeypatch.setenv("BARB_LLM_KEY", "sekret")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    cfg = load_config()
    assert cfg.explain.api_key == "sekret"
```

> **Implementer:** adjust field paths (`output.default_format`, `explain.api_key`) to barb's ACTUAL schema by reading `barb/config.py`. Run these GREEN against the current (pre-retrofit) code first: `uv run pytest tests/test_config.py -q`. If any fails, your test is wrong about current behavior — fix the test, not the code. These lock behavior across the refactor.

- [ ] **Step 3: Retrofit** `barb/config.py` to use the lib — replace `_ensure_app_dir` + the path-list/load block in `load_config`, KEEP the `BARB_LLM_KEY` env block and `AppConfig`:

```python
from pathlib import Path
from typing import Optional

import os
import yaml
from pydantic import BaseModel

from shipwright_kit.config import app_dir, load_config as _load_config

# ... AppConfig and nested models unchanged ...

_APP_DIR = app_dir("barb")  # ~/.barb (created lazily by callers that need it)


def _ensure_app_dir() -> Path:
    return app_dir("barb", create=True)


def _load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    config = _load_config(
        [config_path, _APP_DIR / "config.yaml", Path("config.yaml")],
        loader=_load_yaml,
        validator=lambda data: AppConfig(**data),
    )
    llm_key = os.getenv("BARB_LLM_KEY")
    if llm_key:
        config.explain.api_key = llm_key
    return config
```

> **Implementer:** preserve barb's exact env block + any other lines verbatim. Keep the `AppConfig(**data)` form (barb used it, not `model_validate`) for byte-identical validation behavior. Watch the name clash: import the lib function `as _load_config`.

- [ ] **Step 4:** Run the characterization tests (must still PASS) + full barb suite + lint+format:
  `cd projects/barb && uv run pytest -q && uv run ruff check barb tests && uv run ruff format --check barb tests`
- [ ] **Step 5: Commit:**
```bash
cd projects/barb
git add pyproject.toml barb/config.py tests/test_config.py
git commit -m "refactor(config): consume shipwright_kit.config mechanism (G4)

Delegate app-dir + config-file resolution/load to shipwright_kit.config
(@vNEXT); keep barb's schema + BARB_LLM_KEY env override. Adds characterization
tests (barb had none) that lock load_config behavior across the refactor.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: sift — characterization-test then retrofit `load_config`

**Files:**
- Modify: `projects/sift/pyproject.toml` (pin → vNEXT — currently @v0.4.0)
- Create: `projects/sift/tests/test_config.py`
- Modify: `projects/sift/sift/config.py`

- [ ] **Step 1: Pin + sync** to vNEXT; `uv sync --reinstall-package shipwright-kit`.
- [ ] **Step 2: Characterization tests** mirroring Task 5 Step 2 but for sift's schema + the `SIFT_LLM_KEY` env + the `~/.sift/.env` dotenv path. Read `sift/config.py` for exact field names. Include a test that a `~/.sift/.env` with `SIFT_LLM_KEY=…` is picked up (sift loads dotenv from the app dir). Run GREEN against current code first.
- [ ] **Step 3: Retrofit** `sift/config.py` `load_config` to call `shipwright_kit.config.load_config([config_path, app_dir("sift")/"config.yaml", Path("config.yaml")], loader=_load_yaml, validator=lambda d: AppConfig(**d))`, then KEEP sift's dotenv(`~/.sift/.env`) load + `SIFT_LLM_KEY` block verbatim. Replace `_ensure_app_dir` with `app_dir("sift", create=True)`. Leave `save_config` + the `.env` helpers untouched (they use `_ensure_app_dir()` → keep that wrapper returning `app_dir("sift", create=True)`).
- [ ] **Step 4:** characterization tests still PASS + full sift suite (incl the injection/IOC eval gates unaffected) + lint+format:
  `cd projects/sift && uv run pytest -q && uv run ruff check sift tests && uv run ruff format --check sift tests`
- [ ] **Step 5: Commit** (message analogous to Task 5).

---

### Task 7: vex — retrofit `load_config` (has tests)

**Files:**
- Modify: `projects/vex/pyproject.toml` (add/upgrade pin → vNEXT; vex pins shipwright-kit @v0.4.0 from G12)
- Modify: `projects/vex/vex/config.py`

- [ ] **Step 1: Pin + sync** to vNEXT.
- [ ] **Step 2: Retrofit** `vex/config.py`:
  - `_ensure_dir(path)` → keep signature; implement via the lib where it maps cleanly, OR keep as-is (it takes an arbitrary path, not an app-name — `app_dir` is app-name-based, so `_ensure_dir` for `cache_db_path`'s parent may stay tool-local). Use `app_dir("vex", create=True)` only where the code creates `~/.vex`.
  - `load_config`: keep `load_dotenv()` first; then use `shipwright_kit.config.load_config([config_path, _USER_CONFIG_PATH, _DEFAULT_CONFIG_PATH], loader=_load_yaml, validator=Config.model_validate)`. **Critical:** vex returns `Config()` (defaults) when no file exists — the lib's `validator({})` = `Config.model_validate({})` gives the same all-defaults instance, so the behavior matches. Verify the packaged-default `_DEFAULT_CONFIG_PATH` is still a candidate (3rd in the list).
  - Keep ALL `@property` env accessors (`api_key`, `ai_api_key`, …) and `save_config` untouched.
- [ ] **Step 3:** `cd projects/vex && uv run pytest tests/test_config.py -q` (the EXISTING config tests must pass unchanged) + full vex suite + lint+format (`ruff check` AND `ruff format --check`).
- [ ] **Step 4: Commit** (message analogous; note vex keeps dotenv + packaged-default + lazy property env).

---

### Task 8: Drift note + vault freshness

- [ ] **Step 1:** (optional) a one-line guard test in each tool asserting `from shipwright_kit.config import load_config` is importable + the tool's `load_config` is its own wrapper — low value; SKIP unless trivial. The real guard is each tool's characterization/existing config tests now passing against the shared mechanism.
- [ ] **Step 2:** Sweep `_shipwright/STATUS.md` + `SESSION_LOG.md` + `HORIZON-areas-backlog.md` (G4 → done; lib at vNEXT; `shipwright_kit.config`/`cli` added; template scaffolds config; all 3 tools retrofitted) per the `freshness` skill — ALL current-state files. Update the `shipwright-framework` memory + `MEMORY.md` index (lib version, new modules, tools consume `shipwright_kit.config`).

---

## Self-Review

**Spec coverage:** lib config (T1) + cli (T2) ✓; release (T3) ✓; template wiring (T4) ✓; barb/sift/vex retrofit (T5/T6/T7) ✓ — the user's "also retrofit vex/barb/sift" honored; freshness (T8) ✓. Import-light preserved (config stdlib-only + guard test; cli not imported by root + guard test).

**Placeholder scan:** Task 5/6 instruct the implementer to adjust field names to each tool's real schema by reading the file — that's grounding, not a TBD; exact verbatim-preservation of env blocks is specified. No "TODO/handle edge cases".

**Type consistency:** lib API `app_dir(name, *, create=False, mode=0o700)`, `resolve_config_file(candidates)`, `load_config(candidates, *, loader, validator)` used consistently in T1 + all consumers. Consumers keep their own `AppConfig`/`Config` types + `load_config` wrapper names (call sites unchanged → the 3 files/tool that import `load_config`/`_APP_DIR` keep working).

**Risk flags for the reviewer:**
- **app_dir chmod unification** (stricter 0o700-enforce for barb/sift) — flagged for Skeptic as intentional hardening; add `enforce_mode` param if deemed a behavior change.
- barb/sift have **no prior config tests** — characterization tests are added FIRST and must pass against pre-retrofit code, else the test is wrong.
- vex's **no-file → Config() defaults** path must equal `Config.model_validate({})` — verify (T7 Step 2).
- The cli `version`-command name derivation depends on the Typer version — T2 has a verify note.
- Run BOTH `ruff check` AND `ruff format --check` everywhere (this session's repeated CI-miss; the reusable CI gates format separately).
- The shared core is intentionally thin; the value is the secure app-dir consistency + the template gaining a real config/cli + a single place to evolve the pattern. Do not over-extract tool-specific env/dotenv/save logic into the lib.
