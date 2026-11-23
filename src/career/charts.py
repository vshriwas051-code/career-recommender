"""Plotly figures for the Streamlit pages (cream "doodle campus" theme)."""
from __future__ import annotations

import plotly.graph_objects as go

from .config import area_label, skill_areas
from .explain import Gap
from .skills import area_level
from .ui import TOKENS

INK = TOKENS["ink"]
BLUE = TOKENS["blue"]
LIME_DARK = TOKENS["lime-dark"]
LINE = TOKENS["line"]
CREAM_2 = TOKENS["cream-2"]
MUTED = TOKENS["muted"]
FONT = "Manrope, system-ui, sans-serif"


def _layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=10, r=30, t=30, b=10),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=INK, family=FONT), legend=dict(orientation="h", y=-0.12),
                      hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=INK, font=dict(color=INK, family=FONT)))
    return fig


def _wrap(label: str, width: int = 12) -> str:
    """Break a long area name onto two lines (at the space nearest the middle) for the radar."""
    if len(label) <= width or " " not in label:
        return label
    spaces = [i for i, ch in enumerate(label) if ch == " "]
    cut = min(spaces, key=lambda i: abs(i - len(label) / 2))
    return label[:cut] + "<br>" + label[cut + 1:]


def radar_figure(scores: dict[str, float], role: str, ideal: dict[str, float],
                 target: dict[str, float] | None = None, year: int | None = None) -> go.Figure:
    """You (blue, 25% fill) vs the role's ideal (ink, dashed) vs the year target (lime-dark)."""
    areas = skill_areas()
    labels = [_wrap(area_label(a)) for a in areas] + [_wrap(area_label(areas[0]))]

    def closed(d):
        return [d.get(a, 0) for a in areas] + [d.get(areas[0], 0)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=closed(ideal), theta=labels, name=f"{role} (ideal)",
                                  line=dict(color=INK, width=2, dash="dash")))
    if target:
        fig.add_trace(go.Scatterpolar(r=closed(target), theta=labels, name=f"Year-{year} target",
                                      line=dict(color=LIME_DARK, width=2)))
    fig.add_trace(go.Scatterpolar(
        r=closed(scores), theta=labels, name="You", line=dict(color=BLUE, width=2.5), fill="toself",
        fillcolor="rgba(47,75,201,.25)",
        customdata=[area_level(v) for v in closed(scores)],
        hovertemplate="%{theta}: %{r:.0f}/100 · %{customdata}<extra>You</extra>"))
    fig.update_layout(polar=dict(bgcolor="rgba(0,0,0,0)",
                                 radialaxis=dict(range=[0, 100], gridcolor=LINE, linecolor=LINE,
                                                 tickfont=dict(size=9, color=MUTED)),
                                 angularaxis=dict(gridcolor=LINE, linecolor=LINE, tickfont=dict(size=10.5, color=INK))))
    _layout(fig, 450)
    fig.update_layout(margin=dict(l=56, r=56, t=40, b=20))  # labels wrap, so modest side margins
    return fig


def gap_figure(gaps: list[Gap], year: int) -> go.Figure:
    """You (blue) over the year-adjusted target (cream-2 with a line border), biggest gap at the top."""
    order = list(reversed(gaps))
    y = [g.label for g in order]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=y, x=[g.target for g in order], orientation="h", name=f"Year-{year} target",
                         marker=dict(color=CREAM_2, line=dict(color=LINE, width=1.5)),
                         hovertemplate="%{y} target: %{x:.0f}<extra></extra>"))
    fig.add_trace(go.Bar(y=y, x=[g.score for g in order], orientation="h", name="You",
                         marker_color=BLUE,
                         text=[f"{g.score:.0f} · {area_level(g.score)} (gap {g.gap:.0f})" for g in order],
                         textposition="outside", textfont=dict(color=INK),
                         hovertemplate="%{y} you: %{x:.0f}<extra></extra>"))
    fig.update_layout(barmode="overlay", bargap=0.35)
    _layout(fig, 110 + 55 * len(gaps))
    fig.update_layout(legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0), margin=dict(t=40))
    fig.update_xaxes(range=[0, 115], gridcolor=LINE, zerolinecolor=LINE, tickfont=dict(color=MUTED))
    fig.update_yaxes(tickfont=dict(color=INK, size=12))   # Streamlit's theme would tint these blue
    return fig
