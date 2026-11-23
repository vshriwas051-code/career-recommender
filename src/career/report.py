"""PDF career report (fpdf2), with the same content as the Results page.

Charts are rendered with matplotlib into memory; text uses the DejaVu Sans font
that ships with matplotlib, so dashes, accents and "·" print correctly offline.
"""
from __future__ import annotations

import io
import os
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from fpdf import FPDF  # noqa: E402

from .config import app_config, area_label, role_by_name, skill_areas  # noqa: E402
from .explain import RoleExplanation  # noqa: E402
from .predict import Prediction, format_confidence  # noqa: E402
from .skills import area_level  # noqa: E402

# Accent colours match the app's cream "doodle campus" tokens (src/career/ui.py); page stays white.
INK = (30, 28, 26)
BLUE = (47, 75, 201)
GREY = (107, 103, 96)          # muted
CREAM_2 = (239, 234, 221)
LIME = (182, 240, 74)
LIME_DARK = (125, 181, 26)
# level chip: fill, text
LEVEL_CHIP = {"Beginner": ((217, 211, 197), INK), "Intermediate": (BLUE, (255, 255, 255)),
              "Strong": (LIME, INK)}
FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"


def report_filename(srn: str) -> str:
    return f"{srn}_career_report.pdf"


# ---------- matplotlib charts ----------
def _png(fig) -> io.BytesIO:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def radar_png(scores: dict[str, float], role: str, target: dict[str, float], year: int) -> io.BytesIO:
    areas = skill_areas()
    ideal = role_by_name(role)["profile"]
    ang = np.linspace(0, 2 * np.pi, len(areas), endpoint=False).tolist()
    ang += ang[:1]

    def closed(d):
        v = [d.get(a, 0) for a in areas]
        return v + v[:1]

    fig, ax = plt.subplots(figsize=(5.2, 5.2), subplot_kw=dict(polar=True))
    ax.plot(ang, closed(ideal), color="#1E1C1A", lw=1.6, ls="--", label=f"{role} (ideal)")
    ax.plot(ang, closed(target), color="#7DB51A", lw=1.6, label=f"Year-{year} target")
    ax.plot(ang, closed(scores), color="#2F4BC9", lw=2.2, label="You")
    ax.fill(ang, closed(scores), color="#2F4BC9", alpha=0.25)
    ax.set_xticks(ang[:-1], [area_label(a).replace(" & ", " &\n") for a in areas], fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([30, 60, 100], ["30", "60", "100"], fontsize=7, color="#6B6760")
    ax.grid(color="#E6E0D2")
    ax.spines["polar"].set_color("#E6E0D2")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, fontsize=7.5, frameon=False)
    return _png(fig)


def gap_png(exp: RoleExplanation, year: int) -> io.BytesIO:
    gaps = list(reversed(exp.gaps))
    fig, ax = plt.subplots(figsize=(6.4, 0.55 * len(gaps) + 0.8))
    y = np.arange(len(gaps))
    ax.barh(y, [g.target for g in gaps], color="#EFEADD", edgecolor="#CFC6B2", label=f"Year-{year} target")
    ax.barh(y, [g.score for g in gaps], height=0.5, color="#2F4BC9", label="You")
    for i, g in enumerate(gaps):
        ax.text(max(g.target, g.score) + 1.5, i, f"gap {g.gap:.0f}", va="center", fontsize=8, color="#444")
    ax.set_yticks(y, [g.label for g in gaps], fontsize=8.5)
    ax.set_xlim(0, 110)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7.5, frameon=False, loc="lower right")
    return _png(fig)


# ---------- PDF ----------
class _Report(FPDF):
    footer_text = ""

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(*GREY)
        self.cell(0, 5, f"{self.footer_text}   ·   page {self.page_no()}/{{nb}}", align="C")


def _setup() -> _Report:
    pdf = _Report(format="A4")
    pdf.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"))
    pdf.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"))
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.set_margins(15, 15, 15)
    return pdf


def _h(pdf: FPDF, text: str, size: float = 13) -> None:
    if pdf.get_y() > pdf.h - 45:
        pdf.add_page()
    pdf.ln(3)
    pdf.set_font("DejaVu", "B", size)
    pdf.set_text_color(*INK)
    pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*LIME_DARK)
    pdf.set_line_width(1.1)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 30, pdf.get_y())
    pdf.ln(2)


def _p(pdf: FPDF, text: str, size: float = 9.5, bold: bool = False, color=(30, 35, 50),
       indent: float = 0) -> None:
    pdf.set_font("DejaVu", "B" if bold else "", size)
    pdf.set_text_color(*color)
    pdf.set_x(pdf.l_margin + indent)
    pdf.multi_cell(0, size * 0.52, text, new_x="LMARGIN", new_y="NEXT")


def _bullet(pdf: FPDF, text: str, indent: float = 3, size: float = 9) -> None:
    pdf.set_font("DejaVu", "", size)
    pdf.set_text_color(40, 45, 60)
    pdf.set_x(pdf.l_margin + indent)
    pdf.cell(4, size * 0.52, "•")
    pdf.multi_cell(0, size * 0.52, text, new_x="LMARGIN", new_y="NEXT")


def _checkbox(pdf: FPDF, text: str, note: str) -> None:
    if pdf.get_y() > pdf.h - 25:
        pdf.add_page()
    y = pdf.get_y()
    pdf.set_draw_color(*GREY)
    pdf.set_line_width(0.3)
    pdf.rect(pdf.l_margin + 2, y + 0.9, 3.2, 3.2)
    pdf.set_x(pdf.l_margin + 8)
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(30, 35, 50)
    pdf.multi_cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin + 8)
    pdf.set_font("DejaVu", "", 8)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 4.2, note, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def build_pdf(pred: Prediction, explanations: list[RoleExplanation]) -> bytes:
    cfg = app_config()
    s, ex = pred.student, pred.extraction
    year = s.year_of_study
    expect = cfg["year_expectation"][year]
    stage = cfg["stage_guidance"][cfg["year_stage"][year]]["title"]

    pdf = _setup()
    pdf.footer_text = f"AI Career Recommender · {s.srn} · {date.today().isoformat()} · guidance, not a guarantee"
    pdf.alias_nb_pages()
    pdf.add_page()

    # header band
    pdf.set_fill_color(*INK)
    pdf.rect(0, 0, pdf.w, 30, "F")
    pdf.set_fill_color(*LIME)
    pdf.rect(0, 30, pdf.w, 1.6, "F")
    pdf.set_xy(15, 8)
    pdf.set_font("DejaVu", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 9, "Career Recommendation Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(15)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(*CREAM_2)
    pdf.cell(0, 6, f"Generated {date.today().strftime('%d %B %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(36)

    # student summary
    _h(pdf, "Student")
    rows = [("Name", s.name), ("SRN", s.srn), ("College", s.college), ("Branch", s.branch or "—"),
            ("Class / section", s.class_section or "—"), ("Year of study", str(year)),
            ("CGPA", f"{s.cgpa:g}" if s.cgpa is not None else "—"), ("Stage", stage)]
    for k, v in rows:
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(*GREY)
        pdf.cell(35, 5.5, k)
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(30, 35, 50)
        pdf.multi_cell(0, 5.5, v, new_x="LMARGIN", new_y="NEXT")

    # top 3
    _h(pdf, "Top 3 roles")
    widths = (10, 80, 35, 55)
    pdf.set_fill_color(*CREAM_2)
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(*INK)
    for w, t in zip(widths, ("#", "Role", "Skill match", "Model confidence")):
        pdf.cell(w, 7, t, fill=True)
    pdf.ln(7)
    for i, r in enumerate(pred.top, 1):
        pdf.set_font("DejaVu", "B" if i == 1 else "", 9.5)
        pdf.set_text_color(30, 35, 50)
        pdf.cell(widths[0], 7, str(i))
        pdf.cell(widths[1], 7, r.role)
        pdf.set_text_color(*BLUE)
        pdf.cell(widths[2], 7, f"{r.match:.0f}%")
        pdf.set_text_color(30, 35, 50)
        pdf.cell(widths[3], 7, f"{format_confidence(r.confidence)} · {r.confidence_label}",
                 new_x="LMARGIN", new_y="NEXT")
    _p(pdf, "Skill match = how closely your skill-area profile resembles the role's ideal profile "
            f"(cosine similarity). Model confidence is softened and capped at {cfg['confidence_cap'] * 100:.0f}%.",
       size=7.5, color=GREY)

    # skill areas + radar
    top = explanations[0]
    _h(pdf, f"Your skill areas vs {top.role}")
    y0 = pdf.get_y()
    for a in sorted(skill_areas(), key=lambda a: -ex.scores[a]):
        sc = ex.scores[a]
        lv = area_level(sc)
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(30, 35, 50)
        pdf.cell(44, 6.2, area_label(a))
        pdf.cell(12, 6.2, f"{sc:.0f}", align="R")
        fill, fg = LEVEL_CHIP[lv]
        pdf.set_font("DejaVu", "B", 7.5)
        x, y = pdf.get_x() + 2, pdf.get_y() + 1
        pdf.set_fill_color(*fill)
        pdf.set_draw_color(*(LIME_DARK if lv == "Strong" else fill))
        pdf.set_line_width(0.3)
        pdf.rect(x, y, 22, 4.4, "DF", round_corners=True, corner_radius=2.2)
        pdf.set_text_color(*fg)
        pdf.set_xy(x, y)
        pdf.cell(22, 4.4, lv, align="C")
        pdf.set_xy(pdf.l_margin, y - 1 + 6.2)
    _p(pdf, "Beginner < 30 · Intermediate 30–60 · Strong > 60", size=7.5, color=GREY)
    y1 = pdf.get_y()
    ideal = role_by_name(top.role)["profile"]
    target = {a: ideal[a] * expect for a in skill_areas()}
    pdf.image(radar_png(ex.scores, top.role, target, year), x=100, y=y0 - 2, w=95)
    pdf.set_y(max(y1, y0 + 95))

    # explanations: full detail for the top role, summary for the others
    for idx, e in enumerate(explanations):
        r = pred.top[idx]
        if idx == 0:
            pdf.add_page()
            _h(pdf, f"#1 {e.role} — why it fits", 14)
        else:
            if idx == 1:
                pdf.add_page()
                _h(pdf, "Other strong options", 14)
            _p(pdf, f"#{idx + 1} {e.role} — {r.match:.0f}% match", size=11, bold=True, color=INK)
        if not e.why:
            _bullet(pdf, "Not enough evidence yet — add projects, certificates or events in this area.")
        for w in e.why if idx == 0 else e.why[:2]:
            _p(pdf, f"{w.label} — {w.score:.0f}/100 · {area_level(w.score)} (role ideal {w.ideal:g})",
               size=9.5, bold=True)
            for item in w.evidence[:5 if idx == 0 else 2]:
                _bullet(pdf, item, indent=4, size=8.5)
            pdf.ln(1)

        if idx == 0:
            _h(pdf, "Skill gaps")
            if e.gaps:
                _p(pdf, f"Compared with what's reasonable for year {year} ({expect * 100:.0f}% of the role's "
                        "ideal), biggest gap first.", size=8.5, color=GREY)
                pdf.image(gap_png(e, year), w=150)
            else:
                _p(pdf, f"No significant gaps — you meet the year-{year} target in every area this role "
                        "relies on.", size=9.5)

            ns = e.next_steps
            _h(pdf, f"Next steps — {ns.stage_title}")
            for title, items in [("Certificates", ns.certificates), ("Projects", ns.projects),
                                 ("Events to attend", ns.events)]:
                _p(pdf, title, size=10, bold=True, color=INK)
                pdf.ln(1)
                for step in items:
                    _checkbox(pdf, step.title, step.reason)
                if not items:
                    _p(pdf, "You've already covered our suggestions here.", size=8.5, color=GREY)
                pdf.ln(1)
            _p(pdf, "Tips for your stage", size=10, bold=True, color=INK)
            for tip in ns.tips:
                _bullet(pdf, tip)
        else:
            if e.gaps:
                _p(pdf, "Biggest gaps: " + ", ".join(f"{g.label} ({g.gap:.0f})" for g in e.gaps[:3]),
                   size=8.5, color=GREY, indent=3)
            first = (e.next_steps.certificates + e.next_steps.projects)[:2]
            if first:
                _p(pdf, "Start with: " + "; ".join(st.title for st in first), size=8.5, color=GREY, indent=3)
            pdf.ln(3)

    _h(pdf, "About this report", 11)
    _p(pdf, "Area scores come from rule-based matching of your certificates, projects, events and self-rated "
            "skills; every point is traced to its source. Roles are predicted by a machine-learning model "
            "trained on synthetic (fictional) student profiles, because no real student data was available "
            "or appropriate to use. Treat the results as guidance for exploring careers, not a verdict. "
            f"Model: {pred.model_version}.",
       size=8.5, color=GREY)
    return bytes(pdf.output())


def save_pdf(pred: Prediction, explanations: list[RoleExplanation], out_dir: str | os.PathLike) -> Path:
    path = Path(out_dir) / report_filename(pred.student.srn)
    path.write_bytes(build_pdf(pred, explanations))
    return path
