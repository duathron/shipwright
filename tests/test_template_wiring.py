# tests/test_template_wiring.py
import json
import re
import subprocess
import tomllib
from pathlib import Path

import yaml
from packaging.requirements import Requirement

# copier is a dev dependency (added in Task 3) → its console script is on the
# venv PATH under `uv run pytest`. No skip-guard: the test MUST run in CI.


def _render(tmp: Path, preset: str, pypi_name: str = "acme") -> Path:
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
            f"pypi_name={pypi_name}",
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
    # PyPI range pin (>=0.12.1,<0.13) — url is None, specifier encodes the range
    assert req.url is None
    assert ">=0.12.1" in str(req.specifier)
    assert "<0.13" in str(req.specifier)
    assert 'preset = "security"' in text
    banner = proj / "acme" / "banner.py"
    assert banner.exists()
    assert "from shipwright_kit.design.banner import make_banner" in banner.read_text()


def test_none_preset_core_only(tmp_path):
    proj = _render(tmp_path, "none")
    text = (proj / "pyproject.toml").read_text()
    req = _shipwright_req(text)
    assert req.extras == set()  # no security extra
    # PyPI range pin (>=0.12.1,<0.13) — url is None, specifier encodes the range
    assert req.url is None
    assert ">=0.12.1" in str(req.specifier)
    assert "<0.13" in str(req.specifier)
    assert 'preset = "none"' in text


_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def _workflows(proj: Path) -> list[Path]:
    wfs = sorted((proj / ".github" / "workflows").glob("*.yml"))
    assert wfs
    return wfs


def test_rendered_workflows_are_sha_pinned(tmp_path):
    for preset in ("none", "security"):
        proj = _render(tmp_path / preset, preset)
        for wf in _workflows(proj):
            text = wf.read_text()
            assert "@main" not in text and "@master" not in text, wf.name
            for ref in re.findall(r"uses:\s*\S+@(\S+)", text):
                assert _SHA40.match(ref), (wf.name, ref)


def test_rendered_release_publish_job_is_inline_and_least_privilege(tmp_path):
    for preset in ("none", "security"):
        proj = _render(tmp_path / preset, preset)
        text = (proj / ".github" / "workflows" / "release.yml").read_text()
        assert "python-release.yml" not in text
        # GitHub expressions must survive Jinja rendering literally
        assert "${{ needs.release-please.outputs.release_created == 'true' }}" in text
        assert "shipwright-kit" not in text
        wf = yaml.safe_load(text)
        jobs = wf["jobs"]
        assert jobs["publish"]["environment"] == "pypi"
        assert jobs["publish"]["permissions"] == {"id-token": "write"}
        for name, job in jobs.items():
            if name != "publish":
                assert "id-token" not in (job.get("permissions") or {}), name
        assert "id-token" not in (wf.get("permissions") or {})


def _uvlock_jsonpath(proj: Path) -> str:
    cfg = json.loads((proj / "release-please-config.json").read_text())
    files = cfg["packages"]["."]["extra-files"]
    return next(f["jsonpath"] for f in files if f["path"] == "uv.lock")


def test_release_please_uvlock_extra_file_names_normalised_dist(tmp_path):
    proj = _render(tmp_path / "a", "none")
    assert "'acme'" in _uvlock_jsonpath(proj)
    proj2 = _render(tmp_path / "b", "none", pypi_name="Acme_Scanner")
    assert "'acme-scanner'" in _uvlock_jsonpath(proj2)


def test_pypi_name_validator_rejects_consecutive_separators(tmp_path):
    dst = tmp_path / "proj"
    res = subprocess.run(
        [
            "copier",
            "copy",
            "--defaults",
            "--vcs-ref",
            "HEAD",
            "--data",
            "project_name=Acme",
            "--data",
            "pypi_name=a__b",
            "--data",
            "package_name=acme",
            "--data",
            "cli_command=acme",
            "--data",
            "description=d",
            "--data",
            "env_prefix=ACME",
            ".",
            str(dst),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    assert "pypi_name must be alphanumerics with single separators" in res.stderr


def test_rendered_dependabot_has_cooldown_on_every_entry(tmp_path):
    proj = _render(tmp_path, "none")
    cfg = yaml.safe_load((proj / ".github" / "dependabot.yml").read_text())
    assert cfg["updates"]
    for entry in cfg["updates"]:
        assert "cooldown" in entry, entry["package-ecosystem"]


def test_version_annotation_and_generic_extra_file(tmp_path):
    proj = _render(tmp_path, "none", pypi_name="Acme_Scanner")
    init = (proj / "acme" / "__init__.py").read_text()
    line = next(ln for ln in init.splitlines() if ln.startswith("__version__"))
    assert "# x-release-please-version" in line
    cfg = json.loads((proj / "release-please-config.json").read_text())
    extra = cfg["packages"]["."]["extra-files"]
    assert {"type": "generic", "path": "acme/__init__.py"} in extra
