"""README, architecture diagram and requirements stay consistent with the code."""
import ast
import re

import pytest

from career.config import ROOT

README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_has_required_sections():
    for heading in ["## 1. Overview", "## 2. Features", "## 3. How it works", "## 4. Setup and run",
                    "## 5. Model and evaluation", "## 6. Project structure", "## 7. Limitations"]:
        assert heading in README
    assert "synthetic" in README.lower() and "streamlit run app.py" in README


def test_readme_links_and_images_exist():
    targets = re.findall(r"\]\(([^)#\s]+)\)", README) + re.findall(r'(?:src|srcset)="([^"]+)"', README)
    local = [t for t in targets if not t.startswith(("http://", "https://"))]
    assert len(local) >= 10
    missing = [t for t in local if not (ROOT / t).exists()]
    assert not missing, missing


@pytest.mark.parametrize("stem", ["architecture", "architecture-dark"])
def test_architecture_diagram_outline_only_and_transparent(stem):
    from PIL import Image
    svg = (ROOT / "docs" / f"{stem}.svg").read_text()
    png = Image.open(ROOT / "docs" / f"{stem}.png").convert("RGBA")
    assert png.getpixel((1, 1))[3] == 0                          # transparent background
    fills = set(re.findall(r"fill:\s*([^;\"]+)", svg))
    # only "none" (boxes, lines, background) and the single ink colour used for text glyphs
    assert "none" in fills and len(fills - {"none"}) == 1, fills
    assert "<rect" not in svg or 'style="fill: none' in svg


def _third_party_imports() -> set[str]:
    mods = set()
    for path in [ROOT / "app.py", *ROOT.glob("views/*.py"), *ROOT.glob("src/career/*.py"),
                 ROOT / "docs" / "make_architecture.py"]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                mods |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods.add(node.module.split(".")[0])
    import sys
    return {m for m in mods if m not in sys.stdlib_module_names and m != "career"}


def test_requirements_cover_imports():
    reqs = {re.split(r"[<>=\[ ]", line)[0].lower()
            for line in (ROOT / "requirements.txt").read_text().splitlines() if line.strip()}
    pip_name = {"sklearn": "scikit-learn", "yaml": "pyyaml", "fpdf": "fpdf2"}
    missing = {pip_name.get(m, m) for m in _third_party_imports()} - reqs
    assert not missing, missing
