"""Shared Streamlit UI helpers: light CSS for the navy theme."""
from __future__ import annotations

import streamlit as st

_CSS = """
<style>
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.block-container { animation: fadeIn .45s ease-out; }
.card {
  background: #12264F; border: 1px solid rgba(76,141,255,.25); border-radius: 14px;
  padding: 1.1rem 1.3rem; margin-bottom: .9rem;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}
.card:hover { transform: translateY(-2px); border-color: #4C8DFF; box-shadow: 0 6px 18px rgba(0,0,0,.35); }
.card h3 { margin: 0 0 .35rem 0; }
.muted { color: #9FB2D6; font-size: .92rem; }
.role-card { min-height: 24rem; }
.role-card h3 { min-height: 2.6em; }
.match-num { font-size: 2.6rem; font-weight: 700; color: #4C8DFF; line-height: 1.1; }
.conf-bar { height: 6px; background: rgba(232,238,249,.12); border-radius: 3px; margin: .6rem 0 .3rem; }
.conf-bar > div { height: 100%; background: #4C8DFF; border-radius: 3px; opacity: .75; }
.role-card { animation: fadeIn .5s ease-out both; }
.role-card.r2 { animation-delay: .12s; } .role-card.r3 { animation-delay: .24s; }
@keyframes grow { from { width: 0; } }
.conf-bar > div { animation: grow .9s ease-out; }
.chip { display: inline-block; padding: .05rem .55rem; border-radius: 999px; font-size: .78rem;
  font-weight: 600; margin-left: .35rem; vertical-align: middle; border: 1px solid transparent; }
.chip-Beginner { color: #C9D6EE; background: rgba(159,178,214,.14); border-color: rgba(159,178,214,.35); }
.chip-Intermediate { color: #CFE0FF; background: rgba(76,141,255,.22); border-color: rgba(76,141,255,.55); }
.chip-Strong { color: #C8F5DF; background: rgba(61,214,140,.18); border-color: rgba(61,214,140,.5); }
.area-row { display: flex; justify-content: space-between; align-items: center;
  padding: .32rem 0; border-bottom: 1px solid rgba(232,238,249,.07); }
.area-row:last-child { border-bottom: none; }
.hero { padding: 1.6rem 1.8rem; border-radius: 18px;
  background: linear-gradient(135deg, #12264F 0%, #0B1B3B 100%);
  border: 1px solid rgba(76,141,255,.3); margin-bottom: 1.2rem; }
.hero h1 { margin-bottom: .25rem; }
</style>
"""


def apply_style() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def card(title: str, body: str) -> None:
    st.markdown(f'<div class="card"><h3>{title}</h3><div class="muted">{body}</div></div>',
                unsafe_allow_html=True)


LEVEL_COLORS = {"Beginner": "#9FB2D6", "Intermediate": "#4C8DFF", "Strong": "#3DD68C"}


def level_chip(level: str) -> str:
    return f'<span class="chip chip-{level}">{level}</span>'
