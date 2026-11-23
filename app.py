"""Streamlit entry point: AI Career Recommendation System.

Run with:  streamlit run app.py
Defines the top navigation, the logo and the home page.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st  # noqa: E402

from career.config import role_names  # noqa: E402
from career.demo import install_demo, list_demos  # noqa: E402
from career.ui import apply_style, card, doodle, hero_scene, html, ticker  # noqa: E402

st.set_page_config(page_title="Career Recommender", page_icon=str(ROOT / "assets" / "logo-icon.svg"),
                   layout="wide")
st.logo(str(ROOT / "assets" / "logo.svg"), size="large")  # top nav: show the full wordmark


def home() -> None:
    apply_style()
    left, right = st.columns([1.1, 1], gap="large", vertical_alignment="center")
    with left:
        html(f"""<h1 class="hero-title">Find the<br>career that<br>fits you</h1>
            {doodle('squiggle').replace('<svg', '<svg class="squiggle"', 1)}
            <p class="intro">Add your certificates, projects and events, and see your top 3 roles
            with reasons, gaps and next steps.</p>""")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("Build my profile", type="primary", width="stretch", key="home_build"):
                st.switch_page("views/1_Profile.py")
        with b2:
            see_demo = st.button("See a demo", width="stretch", key="home_demo_btn")
        demos = {d.key: d for d in list_demos()}
        pick = st.selectbox("Demo student (fictional)", list(demos), key="home_demo",
                            format_func=lambda k: f"{demos[k].student.name} — {demos[k].description}")
        if see_demo:
            student = install_demo(pick)
            st.session_state.results_srn = student.srn
            st.session_state.pending_load = student.srn   # Profile page opens it too
            st.switch_page("views/2_Results.py")
    with right:
        html(hero_scene())

    st.markdown("## How it works")
    html('<div class="steps">'
         + card("Add your profile", "Basic details, skills, certificates, projects and the events you've "
                "attended. Takes about five minutes.", "laptop", 0)
         + card("We score 10 skill areas", "Every certificate, project and event adds points to an area, "
                "and each point keeps its source.", "magnifier", 1)
         + card("Get your top 3 roles", "See how well you match, why, where your gaps are and the next "
                "certificates, projects and events to go for.", "trophy", 2)
         + "</div>")
    html(ticker(role_names()))
    st.caption("Everything runs offline — no paid APIs, no LLM calls. Demo students are fictional.")


st.navigation([
    st.Page(home, title="Home", icon=":material/home:", default=True),
    st.Page("views/1_Profile.py", title="Profile", icon=":material/person:"),
    st.Page("views/2_Results.py", title="Results", icon=":material/insights:"),
    st.Page("views/3_History.py", title="History", icon=":material/history:"),
    st.Page("views/4_About.py", title="About", icon=":material/info:"),
], position="top").run()
