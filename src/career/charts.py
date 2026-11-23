"""Plotly figures for the Streamlit pages (navy theme)."""
from __future__ import annotations

import plotly.graph_objects as go

from .config import area_label, skill_areas
from .explain import Gap
from .skills import area_level
from .ui import LEVEL_COLORS

TEXT = "#E8EEF9"
BLUE = "#4C8DFF"
AMBER = "#F5B942"
MUTED = "#9FB2D6"


def _layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=30, t=30, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=TEXT), legend=dict(orientation="h", y=-0.12))
    return fig


def area_bar_figure(scores: dict[str, float]) -> go.Figure:
    """Horizontal bars for all areas, coloured and labelled by level."""
    order = sorted(scores, key=lambda a: scores[a])
    levels = [area_level(scores[a]) for a in order]
    fig = go.Figure(go.Bar(
        x=[scores[a] for a in order], y=[area_label(a) for a in order], orientation="h",
        marker_color=[LEVEL_COLORS[lv] for lv in levels],
        text=[f"{scores[a]:.0f} · {lv}" for a, lv in zip(order, levels)], textposition="outside",
        hovertemplate="%{y}: %{x:.0f}/100<extra></extra>"))
    fig.update_xaxes(range=[0, 125], title="Score (0–100)", gridcolor="rgba(232,238,249,.08)")
    return _layout(fig, 380)


def radar_figure(scores: dict[str, float], role: str, ideal: dict[str, float],
                 target: dict[str, float] | None = None, year: int | None = None) -> go.Figure:
    areas = skill_areas()
    labels = [area_label(a) for a in areas] + [area_label(areas[0])]

    def closed(d):
        return [d.get(a, 0) for a in areas] + [d.get(areas[0], 0)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=closed(ideal), theta=labels, name=f"{role} (ideal)",
                                  line=dict(color=AMBER, width=2), fill="toself",
                                  fillcolor="rgba(245,185,66,.10)"))
    if target:
        fig.add_trace(go.Scatterpolar(r=closed(target), theta=labels, name=f"Year-{year} target",
                                      line=dict(color=MUTED, width=1.5, dash="dot")))
    fig.add_trace(go.Scatterpolar(
        r=closed(scores), theta=labels, name="You", line=dict(color=BLUE, width=2.5), fill="toself",
        fillcolor="rgba(76,141,255,.30)",
        customdata=[area_level(v) for v in closed(scores)],
        hovertemplate="%{theta}: %{r:.0f}/100 · %{customdata}<extra>You</extra>"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 100], gridcolor="rgba(232,238,249,.12)",
                                                 tickfont=dict(size=9, color=MUTED)),
                                 angularaxis=dict(gridcolor="rgba(232,238,249,.12)",
                                                  tickfont=dict(size=11))))
    _layout(fig, 450)
    fig.update_layout(margin=dict(l=90, r=90, t=40, b=20))  # room for long area names
    return fig


def gap_figure(gaps: list[Gap], year: int) -> go.Figure:
    """You vs the year-adjusted target, biggest gap at the top."""
    order = list(reversed(gaps))
    y = [g.label for g in order]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=y, x=[g.target for g in order], orientation="h", name=f"Year-{year} target",
                         marker=dict(color="rgba(159,178,214,.25)", line=dict(color=MUTED, width=1)),
                         hovertemplate="%{y} target: %{x:.0f}<extra></extra>"))
    fig.add_trace(go.Bar(y=y, x=[g.score for g in order], orientation="h", name="You",
                         marker_color=BLUE,
                         text=[f"{g.score:.0f} · {area_level(g.score)} (gap {g.gap:.0f})" for g in order],
                         textposition="outside",
                         hovertemplate="%{y} you: %{x:.0f}<extra></extra>"))
    fig.update_layout(barmode="overlay", bargap=0.35)
    _layout(fig, 110 + 55 * len(gaps))
    fig.update_layout(legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0), margin=dict(t=40))
    fig.update_xaxes(range=[0, 115], gridcolor="rgba(232,238,249,.08)")
    return fig
