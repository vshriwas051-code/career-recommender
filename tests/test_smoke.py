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


def test_cream_theme_tokens():
    cfg = tomllib.loads((ROOT / ".streamlit/config.toml").read_text())
    theme = cfg["theme"]
    assert theme["base"] == "light"
    assert theme["backgroundColor"] == "#F7F4EC"
    assert theme["secondaryBackgroundColor"] == "#EFEADD"
    assert theme["primaryColor"] == theme["textColor"] == "#1E1C1A"
    assert theme["buttonRadius"] == "full"
    assert theme["font"].startswith("Manrope") and theme["headingFont"].startswith("Manrope")
    face = theme["fontFaces"][0]
    assert face["family"] == "Manrope" and face["url"].startswith("app/static/fonts/")
    assert cfg["server"]["enableStaticServing"] is True


def test_no_navy_colours_left():
    import re
    navy = re.compile(r"#(0B1B3B|12264F|4C8DFF|E8EEF9|9FB2D6|F5B942)", re.I)
    files = [ROOT / "app.py", ROOT / ".streamlit/config.toml", *ROOT.glob("views/*.py"), *ROOT.glob("src/career/*.py")]
    hits = [str(f.relative_to(ROOT)) for f in files if navy.search(f.read_text(encoding="utf-8"))]
    assert not hits, hits


def test_pages_exist():
    for name in ["1_Profile", "2_Results", "3_History", "4_About"]:
        assert (ROOT / "views" / f"{name}.py").exists()


def test_gitignore_excludes_data():
    gi = (ROOT / ".gitignore").read_text()
    for entry in [".venv/", "data/", "__pycache__/"]:
        assert entry in gi
