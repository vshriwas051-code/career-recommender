"""Results page: greeting, top-3 role cards (match ring first), skill levels, radar, why, gaps,
next steps, PDF download and history."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import hashlib  # noqa: E402
import json  # noqa: E402
from html import escape  # noqa: E402

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from career import db  # noqa: E402
from career.charts import gap_figure, radar_figure  # noqa: E402
from career.config import app_config, area_label, role_by_name, skill_areas  # noqa: E402
from career.explain import recommend  # noqa: E402
from career.predict import format_confidence, save_prediction  # noqa: E402
from career.report import build_pdf, report_filename  # noqa: E402
from career.skills import area_level  # noqa: E402
from career.ui import (apply_style, avatar_for, confetti, doodle, html, level_chip, page_header,  # noqa: E402
                       ring, section_title, skill_bars)

st.set_page_config(page_title="Results · Career Recommender", layout="wide")
apply_style()
ss = st.session_state
cfg = app_config()
PLOT_CFG = {"displayModeBar": False}

rows = db.list_students()
if not rows:
    page_header("Your results", "Save a profile first and your top 3 roles will show up here.", "trophy")
    st.info("No saved profiles yet. Create one on the **Profile** page first.")
    if st.button("Build my profile", type="primary", key="results_build"):
        st.switch_page("views/1_Profile.py")
    st.stop()

srns = [r["srn"] for r in rows]
default = ss.get("results_srn") or ss.get("editing")
names = {r["srn"]: r["name"] for r in rows}
header_slot = st.empty()          # filled after the picker, so the greeting matches the chosen student
srn = st.selectbox("Student", srns, index=srns.index(default) if default in srns else 0,
                   format_func=lambda s: f"{s} — {names[s]}", key="results_pick")
ss.results_srn = srn
with header_slot.container():
    page_header(f'Hi, {escape(names[srn].split(" ")[0])} <span class="wave" aria-hidden="true">👋</span>',
                "Here are the roles that fit your profile best — with the reasons, your gaps and what to do next.",
                "trophy")

student = db.get_student(srn)
try:
    pred, explanations = recommend(student)
except FileNotFoundError as exc:
    st.error(f"{exc}")
    st.stop()
ex = pred.extraction
year = student.year_of_study
expect = cfg["year_expectation"][year]

# Log each distinct profile version once per session (history is append-only).
profile_hash = hashlib.sha1(json.dumps(student.to_dict(), sort_keys=True).encode()).hexdigest()
logged = ss.setdefault("logged_predictions", set())
if (srn, profile_hash) not in logged:
    save_prediction(pred)
    logged.add((srn, profile_hash))

# One-time confetti sprinkle the first time results appear in this session.
if not ss.get("confetti_done"):
    html(confetti())
    ss.confetti_done = True

# ---------- student card + PDF ----------
stage = cfg["stage_guidance"][cfg["year_stage"][year]]["title"]
facts = [f"SRN {student.srn}", f"Year {year}", student.college]
if student.branch:
    facts.append(student.branch)
if student.class_section:
    facts.append(f"Class {student.class_section}")
if student.cgpa is not None:
    facts.append(f"CGPA {student.cgpa:g}")
c_sum, c_pdf = st.columns([4, 1.25], vertical_alignment="center")
with c_sum:
    html(f'<div class="card lift fade-up student"><div class="avatar"><img src="{avatar_for(student.srn)}" '
         f'alt="Illustrated avatar"></div><div><h3>{escape(student.name)}</h3>'
         f'<div class="facts">{"".join(f"<span class=fact>{escape(f)}</span>" for f in facts)}</div>'
         f'<div class="muted" style="margin-top:.45rem">Stage: <b>{escape(stage)}</b></div></div></div>')
with c_pdf:
    pdf_cache = ss.setdefault("pdf_cache", {})
    if (srn, profile_hash) not in pdf_cache:
        pdf_cache[(srn, profile_hash)] = build_pdf(pred, explanations)
    st.download_button("Download PDF report", pdf_cache[(srn, profile_hash)],
                       file_name=report_filename(srn), mime="application/pdf",
                       type="primary", width="stretch", key="pdf_dl")

# ---------- top-3 role cards ----------
st.markdown("## Your top 3 roles")
cards = []
for i, r in enumerate(pred.top, 1):
    sticker = '<span class="sticker">Top pick</span>' if i == 1 else ""
    cards.append(
        f'<div class="card lift fade-up role-card" style="--i:{i}">{sticker}'
        f'<div class="rank">#{i}</div><h3>{escape(r.role)}</h3>'
        f'<div class="ring-wrap">{ring(r.match)}<div class="ring-label">skill match'
        f'<div class="muted" style="font-weight:500">how closely your skills resemble this role</div></div></div>'
        f'<div class="conf-bar"><div style="width:{r.confidence * 100:.0f}%"></div></div>'
        f'<div class="muted">Model confidence: {format_confidence(r.confidence)} · {r.confidence_label}</div>'
        f'<p class="muted" style="margin:.3rem 0 0">{escape(r.summary)}</p></div>')
html(f'<div class="roles">{"".join(cards)}</div>')
st.caption(
    "**Skill match** = how closely your skill-area profile resembles the role's ideal profile "
    "(cosine similarity). **Model confidence** = the trained model's estimate, softened and capped at "
    f"{cfg['confidence_cap'] * 100:.0f}% because no prediction is ever certain. Roles are ranked by the model.")

# ---------- skill-area overview with level labels ----------
with st.container(key="card-areas"):
    section_title("Your skill areas", "magnifier")
    lv = cfg["skill_levels"]
    st.caption(f"Levels: **Beginner** below {lv['beginner_below']} · **Intermediate** "
               f"{lv['beginner_below']}–{lv['strong_above']} · **Strong** above {lv['strong_above']}. "
               "Everyone starts as a beginner somewhere — these show where to grow, not pass/fail.")
    ordered = sorted(skill_areas(), key=lambda a: -ex.scores[a])
    html(skill_bars([(area_label(a), ex.scores[a], area_level(ex.scores[a])) for a in ordered]))

# ---------- per-role detail ----------
st.markdown("## Role details")
tabs = st.tabs([f"#{i} {e.role}" for i, e in enumerate(explanations, 1)])
for t_idx, (tab, e) in enumerate(zip(tabs, explanations)):
    with tab:
        ideal = role_by_name(e.role)["profile"]
        target = {a: round(ideal[a] * expect, 1) for a in skill_areas()}
        c1, c2 = st.columns([1, 1], gap="medium")
        with c1, st.container(key=f"card-radar-{t_idx}"):
            section_title(f"You vs {e.role}", "compass")
            st.plotly_chart(radar_figure(ex.scores, e.role, ideal, target, year),
                            width="stretch", config=PLOT_CFG, key=f"radar_{t_idx}")
        with c2, st.container(key=f"card-why-{t_idx}"):
            section_title("Why this role", "lightbulb")
            if not e.why:
                st.info("Not enough evidence yet — add projects, certificates or events in this area.")
            for w in e.why:
                html(f"<p><b>{escape(w.label)}</b> — {w.score:.0f}/100 {level_chip(area_level(w.score))} "
                     f'<span class="muted">(role ideal {w.ideal:g})</span></p>')
                st.markdown("\n".join(f"- {escape(x)}" for x in w.evidence[:5]))

        with st.container(key=f"card-gaps-{t_idx}"):
            section_title("Skill gaps", "books")
            if not e.gaps:
                st.success(f"No significant gaps — you meet the year-{year} target in every area this role relies on.")
            else:
                st.caption(f"You vs what's reasonable for year {year} ({expect * 100:.0f}% of the role's ideal), "
                           "biggest gap first.")
                st.plotly_chart(gap_figure(e.gaps, year), width="stretch", config=PLOT_CFG, key=f"gap_{t_idx}")

        ns = e.next_steps
        with st.container(key=f"card-next-{t_idx}"):
            section_title(f"Next steps — {ns.stage_title}", "rocket")
            s1, s2, s3 = st.columns(3)
            for col, title, items in [(s1, "Certificates", ns.certificates), (s2, "Projects", ns.projects),
                                      (s3, "Events to attend", ns.events)]:
                with col:
                    st.markdown(f"**{title}**")
                    if not items:
                        st.caption("You've already covered our suggestions here.")
                    for j, step in enumerate(items):
                        st.checkbox(step.title, key=f"ns_{srn}_{t_idx}_{title}_{j}", help=step.reason)
                        st.caption(step.reason)
            with st.expander("Tips for your stage"):
                st.markdown("\n".join(f"- {tip}" for tip in ns.tips))

# ---------- history ----------
with st.expander("Prediction history for this student", icon=":material/history:"):
    hist = db.list_predictions(srn)
    st.dataframe(pd.DataFrame([{
        "When": h["created_at"], "Model": h["model_version"],
        "Top roles": " · ".join(f"{r['role']} ({r['match']:.0f}% match)" for r in h["top_roles"]),
    } for h in hist]), hide_index=True, width="stretch")

html(f'<div aria-hidden="true" style="width:46px;margin:1.2rem auto 0;opacity:.8">{doodle("sparkle")}</div>')
