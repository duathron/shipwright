# tests/test_tooling.py
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_ruff_base_config_is_valid_and_canonical():
    cfg_path = ROOT / "tooling" / "ruff-base.toml"
    assert cfg_path.exists(), "tooling/ruff-base.toml is missing"
    data = tomllib.loads(cfg_path.read_text())
    assert data["line-length"] == 120
    assert data["target-version"] == "py311"
    # Import-sorting (I) and core lint families must be on
    assert set(data["lint"]["select"]) >= {"E", "F", "I", "W"}
