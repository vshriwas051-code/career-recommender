"""Shared look & feel: cream "doodle campus" theme, inline doodles and CSS-only animations.

Design rules (docs/PHASE7_UI_REDESIGN.md):
* Tokens below are the only colours used. Lime is never text on cream; text on lime is ink.
* Every animation's resting style is its *final* state and keyframes only animate "from",
  so `prefers-reduced-motion: reduce` can switch all motion off and leave things in place.
* Animate transform / opacity only — plus the match ring's registered `--p`, the blob's
  border-radius morph and the paper plane's motion path, which the spec calls for.
* Streamlit widgets are styled through `[data-testid=...]`; white section cards are
  `st.container(key="card-...")`, whose `st-key-card-...` class comes from our own key.
"""
from __future__ import annotations

import base64
import hashlib
import re
from functools import lru_cache
from html import escape

import streamlit as st

from .config import ROOT

TOKENS = {
    "cream": "#F7F4EC", "cream-2": "#EFEADD", "card": "#FFFFFF", "ink": "#1E1C1A",
    "body": "#3A3733", "blue": "#2F4BC9", "lime": "#B6F04A", "lime-dark": "#7DB51A",
    "muted": "#6B6760", "line": "#E6E0D2",
}
# chip background, chip text, bar fill
LEVEL_STYLE = {
    "Beginner": ("#D9D3C5", TOKENS["ink"], "#B9B2A3"),
    "Intermediate": (TOKENS["blue"], "#FFFFFF", TOKENS["blue"]),
    "Strong": (TOKENS["lime"], TOKENS["ink"], TOKENS["lime"]),
}
LEVEL_COLORS = {k: v[2] for k, v in LEVEL_STYLE.items()}   # used by charts

DOODLE_DIR = ROOT / "assets" / "doodles"
AVATAR_DIR = ROOT / "assets" / "avatars"

_ROOT_VARS = "".join(f"--{k}:{v};" for k, v in TOKENS.items())

_CSS = """
<style>
@property --p { syntax: '<number>'; inherits: false; initial-value: 0; }
:root { %(vars)s --shadow: 0 8px 24px rgba(30,28,26,.06); --shadow-lg: 0 18px 38px rgba(30,28,26,.13); }

/* ---------- type ---------- */
h1, h2, h3, h4 { color: var(--ink) !important; font-weight: 800 !important;
  letter-spacing: -0.02em; line-height: 1.1 !important; }
.intro { color: var(--blue); font-size: 1.12rem; font-weight: 500; line-height: 1.6; margin: .8rem 0 1.2rem; }
.muted { color: var(--muted); font-size: .92rem; line-height: 1.55; }
.body { color: var(--body); line-height: 1.6; }
[data-testid="stCaptionContainer"] { color: var(--muted) !important; }
[data-testid="stHeader"] { background: var(--cream); }

/* ---------- cards ---------- */
.card, [class*="st-key-card"] { background: var(--card); border: 1px solid var(--line);
  border-radius: 20px; box-shadow: var(--shadow); }
.card { padding: 1.3rem 1.4rem; position: relative; }
[class*="st-key-card"] { padding: 1.3rem 1.4rem 1.1rem; transition: box-shadow .2s ease;
  animation: fadeUp .5s ease-out backwards; }
[class*="st-key-card"]:hover { box-shadow: var(--shadow-lg); }
.lift { transition: transform .2s ease, box-shadow .2s ease; }
.lift:hover { transform: translateY(-6px) rotate(-0.6deg); box-shadow: var(--shadow-lg); }
.card h3 { margin: 0 0 .35rem; font-size: 1.2rem; }
.sec-title { display: flex; align-items: center; gap: .6rem; margin: 0 0 .6rem; }
.sec-title h3 { margin: 0 !important; padding: 0 !important; font-size: 1.3rem; }
.sec-icon { width: 38px; height: 38px; flex: none; }
.sec-icon svg { width: 100%%; height: 100%%; display: block; }

/* ---------- buttons (pill) ---------- */
[data-testid^="stBaseButton-primary"] { background: var(--ink) !important; border: 1.5px solid var(--ink) !important;
  color: #fff !important; transition: transform .2s ease, box-shadow .2s ease; }
[data-testid^="stBaseButton-primary"] p { color: #fff !important; font-weight: 600; }
[data-testid^="stBaseButton-primary"] p::after { content: "→"; display: inline-block; margin-left: .45em;
  transition: transform .2s ease; }
[data-testid^="stBaseButton-primary"]:hover { transform: translateY(-2px); box-shadow: 0 8px 18px rgba(30,28,26,.2); }
[data-testid^="stBaseButton-primary"]:hover p::after { transform: translateX(4px); }
[data-testid^="stBaseButton-secondary"] { background: transparent !important; border: 1.5px solid var(--ink) !important;
  color: var(--ink) !important; transition: transform .2s ease, background .2s ease; }
[data-testid^="stBaseButton-secondary"] p { font-weight: 600; }
[data-testid^="stBaseButton-secondary"]:hover:not(:disabled) { transform: translateY(-2px); background: var(--card) !important; }
[data-testid^="stBaseButton"]:active:not(:disabled) { transform: scale(.97); }
[data-testid^="stBaseButton"]:focus-visible { outline: 2px solid var(--ink) !important; outline-offset: 2px; }

/* ---------- inputs ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
  background: var(--cream-2) !important; border-radius: 12px !important; }
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within, [data-baseweb="textarea"]:focus-within {
  box-shadow: 0 0 0 2px var(--ink) !important; }

/* ---------- tabs as pills (React Aria tabs: data-testid="stTab", aria-selected) ---------- */
[data-testid="stTabs"] [role="tablist"] { gap: .5rem; flex-wrap: wrap; border: none !important; box-shadow: none !important; }
[data-testid="stTab"] { border-radius: 999px; padding: .45rem 1.05rem !important; height: auto;
  background: var(--cream-2); border: 1.5px solid var(--line); transition: transform .2s ease; }
[data-testid="stTab"]:hover { transform: translateY(-2px); }
[data-testid="stTab"][aria-selected="true"] { background: var(--ink); border-color: var(--ink); }
[data-testid="stTab"][aria-selected="true"] p { color: #fff !important; }
[data-testid="stTab"]:focus-visible { outline: 2px solid var(--blue) !important; outline-offset: 2px; }
[data-testid="stTabs"] .react-aria-SelectionIndicator { display: none !important; }

/* ---------- checkboxes: visible ink box; multiselect chips wrap instead of scrolling ---------- */
[data-testid="stCheckbox"] label > span + div { border: 1.5px solid var(--ink) !important; border-radius: 6px !important; }
[data-testid="stMultiSelectTagsContainer"] { flex-wrap: wrap !important; overflow: visible !important;
  height: auto !important; max-height: none !important; row-gap: .3rem; }
[data-testid="stMultiSelect"] div:has(> [data-testid="stMultiSelectTagsContainer"]) {
  height: auto !important; max-height: none !important; min-height: 2.5rem; padding-top: .25rem; padding-bottom: .25rem; }
.student { margin-bottom: 1.4rem; }
[data-testid="stExpander"] details { background: var(--card); border-color: var(--line) !important; border-radius: 14px; }

/* ---------- headers, squiggle, blobs ---------- */
.page-head { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin: .2rem 0 1.2rem; }
.page-head h1 { font-size: clamp(2rem, 3.6vw, 2.7rem) !important; margin: 0 !important; padding: 0 !important; }
.ph-art { position: relative; width: 130px; height: 118px; flex: none; }
.ph-art .blob { inset: 6%% 4%% 4%% 8%%; }
.ph-art .dd { position: absolute; inset: 14%%; }
.hero-title { font-size: clamp(2.2rem, 4.4vw, 3.2rem) !important; margin: 0 !important; padding: .2rem 0 0 !important; }
.squiggle { display: block; width: min(240px, 62%%); height: auto; margin-top: .35rem; }
.squiggle-path { stroke-dasharray: 300; animation: draw 1.2s ease-out .25s backwards; }
@keyframes draw { from { stroke-dashoffset: 300; } }
.blob { position: absolute; opacity: .35; animation: morph 14s ease-in-out infinite;
  border-radius: 42%% 58%% 63%% 37%% / 41%% 44%% 56%% 59%%; }
.blob.lime { background: var(--lime); } .blob.blue { background: var(--blue); }
@keyframes morph {
  0%%, 100%% { border-radius: 42%% 58%% 63%% 37%% / 41%% 44%% 56%% 59%%; transform: rotate(0deg); }
  33%% { border-radius: 63%% 37%% 41%% 59%% / 58%% 36%% 64%% 42%%; transform: rotate(30deg); }
  66%% { border-radius: 38%% 62%% 47%% 53%% / 64%% 52%% 48%% 36%%; transform: rotate(-24deg); } }

/* ---------- doodles: float / drift / twinkle ---------- */
.dd svg { width: 100%%; height: auto; display: block; overflow: visible; }
.float { animation: float var(--dur, 5.5s) ease-in-out var(--delay, 0s) infinite; }
@keyframes float { 50%% { transform: translateY(-12px); } }
.drift { animation: drift 8s ease-in-out var(--delay, 0s) infinite; }
@keyframes drift { 0%%, 100%% { transform: rotate(-8deg); } 50%% { transform: rotate(8deg); } }
.twinkle { animation: twinkle 2.4s ease-in-out var(--tw, 0s) infinite; }
@keyframes twinkle { 0%%, 100%% { transform: scale(.8); opacity: .5; } 50%% { transform: scale(1.15); opacity: 1; } }

/* ---------- hero scene ---------- */
.scene { position: relative; width: 100%%; max-width: 540px; aspect-ratio: 1 / .9; margin: 0 auto; overflow: hidden; }
.scene .dd { position: absolute; }
.plane { position: absolute; left: 0; top: 0; width: 13%%; opacity: 0;
  offset-path: path('M -60 330 C 60 230, 170 340, 290 200 S 480 70, 620 20'); offset-rotate: auto 20deg;
  animation: glide 14s ease-in-out 1.5s infinite; }
@keyframes glide { 0%% { offset-distance: 0%%; opacity: 0; } 6%% { opacity: 1; } 56%% { opacity: 1; }
  64%% { offset-distance: 100%%; opacity: 0; } 100%% { offset-distance: 100%%; opacity: 0; } }
@supports not (offset-path: path('M0 0')) {
  .plane { animation-name: glideFallback; }
  @keyframes glideFallback { 0%% { transform: translate(-20%%, 520%%) rotate(-10deg); opacity: 0; } 6%% { opacity: 1; }
    56%% { opacity: 1; } 64%% { transform: translate(720%%, 0) rotate(-20deg); opacity: 0; } 100%% { opacity: 0; } } }

/* ---------- fade-up stagger ---------- */
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } }
.fade-up { animation: fadeUp .5s ease-out backwards; animation-delay: calc(var(--i, 0) * 80ms); }

/* ---------- how it works ---------- */
.steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.1rem; margin: .6rem 0 1.6rem; }
.step-icon { width: 76px; height: 76px; margin-bottom: .55rem; }
.step-num { display: inline-block; font-weight: 800; font-size: .8rem; color: var(--ink); background: var(--lime);
  border: 1.5px solid var(--ink); border-radius: 999px; padding: .05rem .6rem; margin-bottom: .45rem; }

/* ---------- role cards + match ring ---------- */
.roles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.1rem; align-items: stretch; margin: .4rem 0 .6rem; }
.role-card { display: flex; flex-direction: column; gap: .5rem; padding-top: 1.5rem; }
.role-card h3 { font-size: 1.25rem; min-height: 2.5em; margin: 0; }
.rank { font-weight: 800; color: var(--muted); font-size: .85rem; }
.ring-wrap { display: flex; align-items: center; gap: .9rem; }
.ring { --p: var(--target); width: 108px; aspect-ratio: 1; border-radius: 50%%; flex: none; display: grid; place-items: center;
  background: conic-gradient(var(--blue) calc(var(--p) * 1%%), var(--cream-2) 0); animation: ring 1.2s ease-out .25s backwards; }
@keyframes ring { from { --p: 0; } }
.ring::before { content: ""; grid-area: 1 / 1; width: 74%%; aspect-ratio: 1; border-radius: 50%%; background: var(--card); }
.ring .match-num { grid-area: 1 / 1; z-index: 1; font-weight: 800; font-size: 1.65rem; color: var(--ink); letter-spacing: -0.02em; }
.ring-label { font-weight: 700; color: var(--ink); line-height: 1.3; }
.conf-bar { height: 8px; background: var(--cream-2); border-radius: 999px; margin: .35rem 0 .2rem; overflow: hidden; }
.conf-bar > div { height: 100%%; background: var(--ink); border-radius: 999px; transform-origin: left;
  animation: grow .9s ease-out .35s backwards; }
.sticker { position: absolute; top: -13px; right: 16px; background: var(--lime); color: var(--ink); font-weight: 800;
  font-size: .85rem; padding: .22rem .75rem; border: 1.5px solid var(--ink); border-radius: 999px;
  box-shadow: 2px 2px 0 var(--ink); transform: rotate(-6deg); animation: wobble 4s ease-in-out 1.2s infinite; }
@keyframes wobble { 0%%, 72%%, 100%% { transform: rotate(-6deg); } 80%% { transform: rotate(-3deg); }
  88%% { transform: rotate(-6deg); } 94%% { transform: rotate(-3.5deg); } }

/* ---------- skill bars + level chips ---------- */
.bars { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: 2rem; }
.bars.one { grid-template-columns: 1fr; }
.bar-row { display: grid; grid-template-columns: minmax(0, 1fr) 2.2rem auto; align-items: center; gap: .55rem;
  padding: .42rem 0; border-bottom: 1px solid var(--line); }
.bar-name { color: var(--ink); font-weight: 600; font-size: .95rem; }
.bar-track { grid-column: 1 / -1; height: 9px; background: var(--cream-2); border-radius: 999px; overflow: hidden; margin-top: -.1rem; }
.bar-fill { height: 100%%; border-radius: 999px; transform-origin: left;
  animation: grow .9s ease-out backwards; animation-delay: calc(var(--i, 0) * 70ms + .15s); }
@keyframes grow { from { transform: scaleX(0); } }
.bar-score { font-weight: 800; color: var(--ink); text-align: right; }
.chip { display: inline-block; padding: .08rem .6rem; border-radius: 999px; font-size: .78rem; font-weight: 700;
  border: 1.5px solid transparent; white-space: nowrap; }
.chip-Beginner { background: #D9D3C5; color: var(--ink); }
.chip-Intermediate { background: var(--blue); color: #fff; }
.chip-Strong { background: var(--lime); color: var(--ink); border-color: var(--lime-dark); }

/* ---------- student card + wave ---------- */
.student { display: flex; align-items: center; gap: 1.1rem; }
.avatar { width: 84px; height: 84px; border-radius: 50%%; background: var(--lime); border: 1.5px solid var(--ink);
  flex: none; overflow: hidden; }
.avatar img { width: 100%%; height: 100%%; display: block; }
.facts { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .45rem; }
.fact { background: var(--cream-2); border-radius: 999px; padding: .12rem .65rem; font-size: .85rem; color: var(--body); }
.wave { display: inline-block; transform-origin: 70%% 75%%; animation: wave 1.1s ease-in-out .3s 2; }
@keyframes wave { 0%%, 100%% { transform: rotate(0); } 20%% { transform: rotate(16deg); } 40%% { transform: rotate(-8deg); }
  60%% { transform: rotate(14deg); } 80%% { transform: rotate(-4deg); } }

/* ---------- ticker ---------- */
.ticker { overflow: hidden; border-top: 1.5px solid var(--ink); border-bottom: 1.5px solid var(--ink); padding: .85rem 0; margin-top: .8rem;
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 7%%, #000 93%%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 7%%, #000 93%%, transparent); }
.ticker-track { display: flex; width: max-content; animation: marquee 35s linear infinite; }
.ticker:hover .ticker-track { animation-play-state: paused; }
@keyframes marquee { to { transform: translateX(-50%%); } }
.ticker-item { display: flex; align-items: center; gap: 1.1rem; padding-right: 1.1rem; white-space: nowrap;
  font-weight: 800; font-size: 1.25rem; color: var(--ink); letter-spacing: -0.01em; }
.ticker-item svg { width: 18px; height: 18px; }

/* ---------- confetti (once) ---------- */
.confetti { position: fixed; inset: 0; pointer-events: none; z-index: 999990; overflow: hidden; }
.confetti i { position: absolute; top: -3vh; left: var(--x); width: 9px; height: 14px; background: var(--c);
  border-radius: 2px; opacity: 0; animation: fall 2.5s cubic-bezier(.25,.6,.45,1) var(--d) 1 both; }
@keyframes fall { 0%% { opacity: 1; transform: translate(0, 0) rotate(0); } 85%% { opacity: 1; }
  100%% { opacity: 0; transform: translate(var(--dx), 104vh) rotate(var(--r)); } }

/* ---------- empty state ---------- */
.empty { text-align: center; padding: 2rem 1rem 1rem; }
.empty .dd { width: 130px; margin: 0 auto .6rem; }

/* ---------- responsive ---------- */
@media (max-width: 640px) {
  .steps, .roles, .bars { grid-template-columns: 1fr; }
  .scene { max-width: 340px; }
  .ph-art { width: 86px; height: 80px; }
  .page-head h1 { font-size: 1.9rem !important; }
  .ticker-item { font-size: 1.05rem; }
}

/* ---------- reduced motion: everything still, in its final state ---------- */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; }
  .plane, .confetti { display: none !important; }
}
</style>
"""


def apply_style() -> None:
    st.markdown(_CSS % {"vars": _ROOT_VARS}, unsafe_allow_html=True)


# ---------- assets ----------
@lru_cache(maxsize=None)
def _svg_source(name: str) -> str:
    raw = (DOODLE_DIR / f"{name}.svg").read_text(encoding="utf-8")
    return re.sub(r"\s*\n\s*", " ", raw).strip()   # one line: markdown must not see blank/indented lines


def doodle(name: str) -> str:
    """Inline SVG markup for a doodle (so CSS can animate its parts)."""
    return _svg_source(name)


@lru_cache(maxsize=None)
def _avatar_uris() -> tuple[str, ...]:
    files = sorted(AVATAR_DIR.glob("*.svg"))
    return tuple("data:image/svg+xml;base64," + base64.b64encode(p.read_bytes()).decode() for p in files)


def avatar_for(srn: str) -> str:
    """Pick one of the bundled Open Peeps avatars from a stable hash of the SRN."""
    uris = _avatar_uris()
    idx = int(hashlib.sha1(srn.encode()).hexdigest(), 16) % len(uris)
    return uris[idx]


# ---------- building blocks ----------
def html(markup: str) -> None:
    st.markdown(re.sub(r"\n\s*", " ", markup), unsafe_allow_html=True)


def page_header(title_html: str, intro: str, art: str = "compass") -> None:
    html(f"""<div class="page-head"><div><h1>{title_html}</h1>{doodle('squiggle').replace('<svg', '<svg class="squiggle"', 1)}
        <p class="intro">{escape(intro)}</p></div>
        <div class="ph-art" aria-hidden="true"><div class="blob lime"></div>
        <div class="dd float" style="--dur:5.2s">{doodle(art)}</div></div></div>""")


def section_title(text: str, icon: str) -> None:
    html(f'<div class="sec-title"><span class="sec-icon" aria-hidden="true">{doodle(icon)}</span>'
         f'<h3>{escape(text)}</h3></div>')


def card(title: str, body: str, icon: str | None = None, i: int = 0) -> str:
    icon_html = f'<div class="step-icon" aria-hidden="true">{doodle(icon)}</div>' if icon else ""
    return (f'<div class="card lift fade-up" style="--i:{i}">{icon_html}<h3>{escape(title)}</h3>'
            f'<div class="muted">{escape(body)}</div></div>')


def level_chip(level: str) -> str:
    return f'<span class="chip chip-{level}">{level}</span>'


def skill_bars(rows: list[tuple[str, float, str]], one_column: bool = False) -> str:
    """rows = (label, score 0-100, level). Bars grow from 0 with a stagger."""
    out = []
    for i, (label, score, level) in enumerate(rows):
        fill = LEVEL_STYLE[level][2]
        out.append(
            f'<div class="bar-row"><span class="bar-name">{escape(label)}</span>'
            f'<span class="bar-score">{score:.0f}</span>{level_chip(level)}'
            f'<div class="bar-track"><div class="bar-fill" style="--i:{i};width:{max(score, 0):.0f}%;'
            f'background:{fill}"></div></div></div>')
    return f'<div class="bars{" one" if one_column else ""}">{"".join(out)}</div>'


def ring(value: float) -> str:
    return (f'<div class="ring" style="--target:{value:.0f}" role="img" aria-label="{value:.0f}% skill match">'
            f'<span class="match-num">{value:.0f}%</span></div>')


def hero_scene() -> str:
    def dd(name, style, inner_cls=""):
        svg = doodle(name)
        if inner_cls:
            for c in reversed(inner_cls.split()):
                svg = f'<div class="{c}">{svg}</div>'
        return f'<div class="dd float" style="{style}">{svg}</div>'
    return ('<div class="scene" aria-hidden="true">'
            '<div class="blob blue" style="width:30%;height:30%;left:66%;top:3%;opacity:.3;animation-duration:17s;animation-delay:-6s"></div>'
            '<div class="blob lime" style="width:80%;height:78%;left:8%;top:14%"></div>'
            + dd("laptop", "left:27%;top:30%;width:48%;--dur:6.2s;--delay:-1s")
            + dd("rocket", "left:7%;top:8%;width:22%;--dur:5.1s;--delay:-2.4s")
            + dd("lightbulb", "left:73%;top:44%;width:21%;--dur:4.6s;--delay:-.6s")
            + dd("books", "left:8%;top:63%;width:25%;--dur:6.8s;--delay:-3.3s")
            + dd("star", "left:68%;top:9%;width:14%;--dur:5.6s;--delay:-1.7s", "drift")
            + dd("sparkle", "left:58%;top:77%;width:10%;--dur:4.9s;--delay:-2.9s;--tw:-.8s", "drift twinkle")
            + dd("sparkle", "left:5%;top:45%;width:8%;--dur:6.4s;--delay:-.3s;--tw:-1.6s", "twinkle")
            + f'<div class="plane">{doodle("paper-plane")}</div></div>')


def ticker(items: list[str]) -> str:
    sep = doodle("sparkle")
    row = "".join(f'<span class="ticker-item">{escape(t)}{sep}</span>' for t in items)
    return f'<div class="ticker" aria-label="Roles we recommend"><div class="ticker-track">{row}{row}</div></div>'


def confetti(n: int = 24) -> str:
    colours = [TOKENS["lime"], TOKENS["blue"], TOKENS["ink"], TOKENS["lime-dark"]]
    pieces = []
    for k in range(n):
        x = (k * 37 + 11) % 100
        dx = ((k * 53) % 21 - 10) * 3
        rot = 220 + (k * 71) % 400
        delay = (k * 17) % 40 / 100
        pieces.append(f'<i style="--x:{x}vw;--dx:{dx}px;--r:{rot}deg;--d:{delay:.2f}s;--c:{colours[k % 4]}"></i>')
    return f'<div class="confetti" aria-hidden="true">{"".join(pieces)}</div>'
