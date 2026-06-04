# tests/test_template_wiring.py
import subprocess
import tomllib
from pathlib import Path

from packaging.requirements import Requirement

# copier is a dev dependency (added in Task 3) → its console script is on the
# venv PATH under `uv run pytest`. No skip-guard: the test MUST run in CI.


def _render(tmp: Path, preset: str) -> Path:
    dst = tmp / "proj"
    subprocess.run(
        [
            "copier",
            "copy",
            "--defaults",
            "--vcs-ref",
            "HEAD",
            "--data",
            "project_name=Acme",
            "--data",
            "pypi_name=acme",
            "--data",
            "package_name=acme",
            "--data",
            "cli_command=acme",
            "--data",
            "description=d",
            "--data",
            "env_prefix=ACME",
            "--data",
            f"preset={preset}",
            ".",
            str(dst),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return dst


def _shipwright_req(pyproject_text: str) -> Requirement:
    data = tomllib.loads(pyproject_text)
    for dep in data["project"]["dependencies"]:
        req = Requirement(dep)
        if req.name == "shipwright-kit":
            return req
    raise AssertionError("no shipwright dependency in rendered pyproject")


def test_security_preset_installs_security_extra(tmp_path):
    proj = _render(tmp_path, "security")
    text = (proj / "pyproject.toml").read_text()
    req = _shipwright_req(text)
    assert req.extras == set()  # security pack ships with base (entry-point); no [security] extra exists
    assert "git+https://github.com/duathron/shipwright" in str(req.url)
    assert 'preset = "security"' in text
    banner = proj / "acme" / "banner.py"
    assert banner.exists()
    assert "from shipwright_kit.design.banner import make_banner" in banner.read_text()


def test_none_preset_core_only(tmp_path):
    proj = _render(tmp_path, "none")
    text = (proj / "pyproject.toml").read_text()
    req = _shipwright_req(text)
    assert req.extras == set()  # no security extra
    assert "git+https://github.com/duathron/shipwright" in str(req.url)
    assert 'preset = "none"' in text
