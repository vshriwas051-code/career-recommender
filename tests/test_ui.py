"""Phase 7 redesign: CSS rules, bundled assets, offline guarantees."""
import re

from career import ui
from career.config import ROOT

CSS = ui._CSS % {"vars": ui._ROOT_VARS}


def test_reduced_motion_block_turns_everything_off():
    block = CSS[CSS.index("@media (prefers-reduced-motion: reduce)"):]
    assert "animation: none !important" in block and "transition: none !important" in block


def test_tokens_and_contrast_rules():
    assert ui.TOKENS["cream"] == "#F7F4EC" and ui.TOKENS["lime"] == "#B6F04A"
    # lime is never used as a text colour (fails contrast on cream)
    assert not re.search(r"(?<![-\w])color:\s*var\(--lime\)", CSS)
    for level, (bg, fg, _) in ui.LEVEL_STYLE.items():
        assert fg in ("#1E1C1A", "#FFFFFF"), level


def _contrast(a: str, b: str) -> float:
    def lum(h):
        rgb = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_text_colour_pairs_meet_wcag_aa():
    t = ui.TOKENS
    pairs = [(t["ink"], t["cream"]), (t["body"], t["card"]), (t["blue"], t["cream"]), (t["blue"], t["card"]),
             (t["muted"], t["card"]), (t["muted"], t["cream"]), ("#FFFFFF", t["ink"]), ("#FFFFFF", t["blue"]),
             (t["ink"], t["lime"]), (t["ink"], "#D9D3C5"), (t["body"], t["cream-2"])]
    for fg, bg in pairs:
        assert _contrast(fg, bg) >= 4.5, (fg, bg, round(_contrast(fg, bg), 2))


def test_font_licence_and_assets_exist():
    assert (ROOT / "static/fonts/Manrope-Variable.woff2").stat().st_size > 20_000
    assert "SIL Open Font License" in (ROOT / "static/fonts/OFL.txt").read_text()
    names = {"rocket", "lightbulb", "compass", "grad-cap", "laptop", "books", "paper-plane", "star",
             "sparkle", "squiggle", "trophy", "magnifier"}
    assert names <= {p.stem for p in (ROOT / "assets/doodles").glob("*.svg")}
    avatars = list((ROOT / "assets/avatars").glob("*.svg"))
    assert len(avatars) >= 8 and all("CC0" in p.read_text() or "zero/1.0" in p.read_text() for p in avatars)
    assert (ROOT / "assets/logo.svg").exists()


def test_doodles_are_outline_style():
    for p in (ROOT / "assets/doodles").glob("*.svg"):
        svg = p.read_text()
        fills = set(re.findall(r'fill="(#[0-9A-Fa-f]{6})"', svg))
        assert fills <= {"#B6F04A", "#2F4BC9", "#FFFFFF"}, (p.name, fills)
        assert "stroke-linecap=\"round\"" in svg, p.name


def test_no_runtime_calls_to_external_fonts_or_avatars():
    pattern = re.compile(r"dicebear\.com|fonts\.googleapis|fonts\.gstatic|api\.dicebear", re.I)
    files = [ROOT / "app.py", ROOT / ".streamlit/config.toml", *ROOT.glob("views/*.py"), *ROOT.glob("src/career/*.py")]
    hits = [str(f.relative_to(ROOT)) for f in files if pattern.search(f.read_text(encoding="utf-8"))]
    assert not hits, hits


def test_avatar_is_stable_per_srn():
    assert ui.avatar_for("DEMO21SEC01") == ui.avatar_for("DEMO21SEC01")
    assert ui.avatar_for("DEMO21SEC01").startswith("data:image/svg+xml;base64,")
    assert len({ui.avatar_for(f"SRN{i:05d}") for i in range(40)}) > 3


def test_continuous_animations_per_page_within_budget():
    scene = ui.hero_scene()
    continuous = scene.count('class="dd float"') + scene.count('class="blob') + scene.count('class="plane"')
    assert continuous + 1 <= 12          # + the role ticker on Home
