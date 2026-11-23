"""Phase 0 smoke tests: skeleton, config and theme are in place."""
import tomllib
from pathlib import Path

from career.config import ROOT, app_config


def test_package_imports():
    import career

    assert career.__version__


def test_app_config_has_srn_pattern():
    cfg = app_config()
    assert cfg["srn_pattern"]
    assert cfg["year_min"] == 1 and cfg["year_max"] == 4


def test_navy_theme():
    theme = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())["theme"]
    assert theme["backgroundColor"] == "#0B1B3B"
    assert theme["primaryColor"] == "#4C8DFF"


def test_pages_exist():
    for name in ["1_Profile", "2_Results", "3_History", "4_About"]:
        assert (ROOT / "pages" / f"{name}.py").exists()


def test_gitignore_excludes_data():
    gi = (ROOT / ".gitignore").read_text()
    for entry in [".venv/", "data/", "__pycache__/"]:
        assert entry in gi
