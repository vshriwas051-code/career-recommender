"""Results page: top-3 roles (match score first), skill levels, radar, why, gaps, next steps, PDF."""
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
from career.ui import apply_style, level_chip  # noqa: E402

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
apply_style()
ss = st.session_state
cfg = app_config()
PLOT_CFG = {"displayModeBar": False}

st.title("📊 Career Results")

rows = db.list_students()
if not rows:
    st.info("No saved profiles yet. Create one on the **Profile** page first.")
    st.stop()

srns = [r["srn"] for r in rows]
default = ss.get("results_srn") or ss.get("editing")
names = {r["srn"]: r["name"] for r in rows}
srn = st.selectbox("Student", srns, index=srns.index(default) if default in srns else 0,
                   format_func=lambda s: f"{s} — {names[s]}", key="results_pick")
ss.results_srn = srn

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

# ---------- student summary + PDF ----------
stage = cfg["stage_guidance"][cfg["year_stage"][year]]["title"]
cgpa = f" · CGPA {student.cgpa:g}" if student.cgpa is not None else ""
c_sum, c_pdf = st.columns([4, 1], vertical_alignment="center")
with c_sum:
    st.markdown(
        f'<div class="card"><h3>{escape(student.name)}</h3><div class="muted">'
        f'SRN {escape(student.srn)} · {escape(student.college)}'
        f'{" · " + escape(student.branch) if student.branch else ""}'
        f'{" · Class " + escape(student.class_section) if student.class_section else ""}'
        f' · Year {year}{cgpa}<br>Stage: <b>{escape(stage)}</b></div></div>',
        unsafe_allow_html=True)
with c_pdf:
    pdf_cache = ss.setdefault("pdf_cache", {})
    if (srn, profile_hash) not in pdf_cache:
        pdf_cache[(srn, profile_hash)] = build_pdf(pred, explanations)
    st.download_button("⬇️ Download PDF report", pdf_cache[(srn, profile_hash)],
                       file_name=report_filename(srn), mime="application/pdf",
                       type="primary", width="stretch", key="pdf_dl")

# ---------- top-3 role cards ----------
st.subheader("Your top 3 roles")
cols = st.columns(3)
for i, (col, r) in enumerate(zip(cols, pred.top), 1):
    with col:
        st.markdown(
            f'<div class="card role-card r{i}">'
            f'<div class="muted">#{i}</div>'
            f'<h3>{escape(r.role)}</h3>'
            f'<div class="match-num">{r.match:.0f}%</div>'
            f'<div class="muted">skill match</div>'
            f'<div class="conf-bar"><div style="width:{r.confidence * 100:.0f}%"></div></div>'
            f'<div class="muted">Model confidence: {format_confidence(r.confidence)} · {r.confidence_label}</div>'
            f'<p class="muted" style="margin-top:.6rem">{escape(r.summary)}</p></div>',
            unsafe_allow_html=True)
st.caption(
    "**Skill match** = how closely your skill-area profile resembles the role's ideal profile "
    "(cosine similarity). **Model confidence** = the trained model's estimate, softened and capped at "
    f"{cfg['confidence_cap'] * 100:.0f}% because no prediction is ever certain. Roles are ranked by the model.")

# ---------- skill-area overview with level labels ----------
st.subheader("Your skill areas")
lv = cfg["skill_levels"]
st.caption(f"Levels: **Beginner** below {lv['beginner_below']} · **Intermediate** "
           f"{lv['beginner_below']}–{lv['strong_above']} · **Strong** above {lv['strong_above']}. "
           "Everyone starts as a beginner somewhere — these show where to grow, not pass/fail.")
ordered = sorted(skill_areas(), key=lambda a: -ex.scores[a])
half = (len(ordered) + 1) // 2
for col, chunk in zip(st.columns(2), (ordered[:half], ordered[half:])):
    with col:
        st.markdown('<div class="card">' + "".join(
            f'<div class="area-row"><span>{escape(area_label(a))}</span>'
            f'<span><b>{ex.scores[a]:.0f}</b>{level_chip(area_level(ex.scores[a]))}</span></div>'
            for a in chunk) + "</div>", unsafe_allow_html=True)

# ---------- per-role detail ----------
st.subheader("Role details")
tabs = st.tabs([f"#{i} {e.role}" for i, e in enumerate(explanations, 1)])
for t_idx, (tab, e) in enumerate(zip(tabs, explanations)):
    with tab:
        ideal = role_by_name(e.role)["profile"]
        target = {a: round(ideal[a] * expect, 1) for a in skill_areas()}
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"#### 🧭 You vs {escape(e.role)}")
            st.plotly_chart(radar_figure(ex.scores, e.role, ideal, target, year),
                            width="stretch", config=PLOT_CFG, key=f"radar_{t_idx}")
        with c2:
            st.markdown("#### ✅ Why this role")
            if not e.why:
                st.info("Not enough evidence yet — add projects, certificates or events in this area.")
            for w in e.why:
                st.markdown(f"**{escape(w.label)}** — {w.score:.0f}/100 {level_chip(area_level(w.score))} "
                            f'<span class="muted">(role ideal {w.ideal:g})</span>', unsafe_allow_html=True)
                st.markdown("\n".join(f"- {escape(x)}" for x in w.evidence[:5]))

        st.markdown("#### 📉 Skill gaps")
        if not e.gaps:
            st.success(f"No significant gaps — you meet the year-{year} target in every area this role relies on.")
        else:
            st.caption(f"You vs what's reasonable for year {year} ({expect * 100:.0f}% of the role's ideal), "
                       "biggest gap first.")
            st.plotly_chart(gap_figure(e.gaps, year), width="stretch", config=PLOT_CFG, key=f"gap_{t_idx}")

        ns = e.next_steps
        st.markdown(f"#### 🚀 Next steps — {ns.stage_title}")
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
with st.expander("🕑 Prediction history for this student"):
    hist = db.list_predictions(srn)
    st.dataframe(pd.DataFrame([{
        "When": h["created_at"], "Model": h["model_version"],
        "Top roles": " · ".join(f"{r['role']} ({r['match']:.0f}% match)" for r in h["top_roles"]),
    } for h in hist]), hide_index=True, width="stretch")
