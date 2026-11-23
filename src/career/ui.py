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
