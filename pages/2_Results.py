"""Results page: top-3 roles (match score first), why, gaps and next steps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import hashlib  # noqa: E402
import json  # noqa: E402
from html import escape  # noqa: E402

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from career import db  # noqa: E402
from career.config import app_config  # noqa: E402
from career.explain import recommend  # noqa: E402
from career.predict import save_prediction  # noqa: E402
from career.ui import apply_style  # noqa: E402

st.set_page_config(page_title="Results", page_icon="📊", layout="wide")
apply_style()
ss = st.session_state
cfg = app_config()

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

# Log each distinct profile version once per session (history is append-only).
profile_hash = hashlib.sha1(json.dumps(student.to_dict(), sort_keys=True).encode()).hexdigest()
logged = ss.setdefault("logged_predictions", set())
if (srn, profile_hash) not in logged:
    save_prediction(pred)
    logged.add((srn, profile_hash))

# ---------- student summary ----------
stage = cfg["stage_guidance"][cfg["year_stage"][student.year_of_study]]["title"]
cgpa = f" · CGPA {student.cgpa:g}" if student.cgpa is not None else ""
st.markdown(
    f'<div class="card"><h3>{escape(student.name)}</h3><div class="muted">'
    f'SRN {escape(student.srn)} · {escape(student.college)}'
    f'{" · " + escape(student.branch) if student.branch else ""}'
    f'{" · Class " + escape(student.class_section) if student.class_section else ""}'
    f' · Year {student.year_of_study}{cgpa}<br>Stage: <b>{escape(stage)}</b></div></div>',
    unsafe_allow_html=True)

# ---------- top-3 role cards ----------
st.subheader("Your top 3 roles")
cols = st.columns(3)
for i, (col, r) in enumerate(zip(cols, pred.top), 1):
    with col:
        st.markdown(
            f'<div class="card role-card">'
            f'<div class="muted">#{i}</div>'
            f'<h3>{escape(r.role)}</h3>'
            f'<div class="match-num">{r.match:.0f}%</div>'
            f'<div class="muted">skill match</div>'
            f'<div class="conf-bar"><div style="width:{r.confidence * 100:.0f}%"></div></div>'
            f'<div class="muted">Model confidence: {r.confidence * 100:.0f}% · {r.confidence_label}</div>'
            f'<p class="muted" style="margin-top:.6rem">{escape(r.summary)}</p></div>',
            unsafe_allow_html=True)
st.caption(
    "**Skill match** = how closely your skill-area profile resembles the role's ideal profile "
    "(cosine similarity). **Model confidence** = the trained model's estimate, softened and capped at "
    f"{cfg['confidence_cap'] * 100:.0f}% because no prediction is ever certain. Roles are ranked by the model.")

# ---------- per-role explanation ----------
tabs = st.tabs([f"#{i} {e.role}" for i, e in enumerate(explanations, 1)])
for t_idx, (tab, e) in enumerate(zip(tabs, explanations)):
    with tab:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### ✅ Why this role")
            if not e.why:
                st.info("Not enough evidence yet — add projects, certificates or events in this area.")
            for w in e.why:
                st.markdown(f"**{escape(w.headline())}**")
                st.markdown("\n".join(f"- {escape(x)}" for x in w.evidence[:5]))
        with c2:
            st.markdown("#### 📉 Skill gaps")
            if not e.gaps:
                st.success(f"No significant gaps — you meet the year-{student.year_of_study} target "
                           "in every area this role relies on.")
            else:
                st.caption(f"Compared with what's reasonable for year {student.year_of_study} "
                           f"({cfg['year_expectation'][student.year_of_study] * 100:.0f}% of the role's ideal).")
                st.dataframe(pd.DataFrame([{"Area": g.label, "You": g.score, "Target": g.target,
                                            "Gap": g.gap} for g in e.gaps]),
                             hide_index=True, width="stretch")

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
