"""Streamlit entry point: AI Career Recommendation System.

Run with:  streamlit run app.py
Defines the navigation (so the sidebar shows proper page names) and the home page.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st  # noqa: E402

from career.demo import install_demo, list_demos  # noqa: E402
from career.ui import apply_style, card  # noqa: E402

st.set_page_config(page_title="Career Recommender", page_icon="🎯", layout="wide")


def home() -> None:
    apply_style()
    st.markdown(
        '<div class="hero"><h1>🎯 AI Career Recommender</h1>'
        '<div class="muted">Enter your academic profile — certificates, projects and events — '
        'and get the job roles that fit you best, with the reasons, your skill gaps and next steps.'
        '</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        card("1 · Profile", "Add your basic details, skills, certificates, projects and events.")
    with c2:
        card("2 · Results", "See your top-3 roles, why they fit, your gaps and what to do next.")
    with c3:
        card("3 · History", "Open or delete saved profiles by SRN.")
    g1, g2 = st.columns(2, vertical_alignment="bottom")
    with g1:
        st.markdown("**New here?** Enter your own profile.")
        if st.button("Get started →", type="primary"):
            st.switch_page("views/1_Profile.py")
    with g2:
        demos = {d.key: d for d in list_demos()}
        pick = st.selectbox("…or see it work on a fictional demo student", list(demos), key="home_demo",
                            format_func=lambda k: f"{demos[k].student.name} — {demos[k].description}")
        if st.button("🎓 See demo results →", key="home_demo_btn"):
            student = install_demo(pick)
            st.session_state.results_srn = student.srn
            st.session_state.pending_load = student.srn   # Profile page opens it too
            st.switch_page("views/2_Results.py")
    st.caption("Everything runs offline — no paid APIs, no LLM calls.")


st.navigation([
    st.Page(home, title="Home", icon="🏠", default=True),
    st.Page("views/1_Profile.py", title="Profile", icon="👤"),
    st.Page("views/2_Results.py", title="Results", icon="📊"),
    st.Page("views/3_History.py", title="History", icon="🗂️"),
    st.Page("views/4_About.py", title="About", icon="ℹ️"),
]).run()
