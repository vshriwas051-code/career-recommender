"""Profile page: enter, load, edit, save and delete a student profile."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from datetime import date  # noqa: E402

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from career import db  # noqa: E402
from career.charts import area_bar_figure  # noqa: E402
from career.config import app_config, area_label, skill_areas, skill_names  # noqa: E402
from career.models import Certificate, Event, Project, Student, _to_date  # noqa: E402
from career.skills import area_level, extract, suggest_domain  # noqa: E402
from career.ui import apply_style  # noqa: E402
from career.validate import normalize_srn, validate_student  # noqa: E402

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")
apply_style()

cfg = app_config()
ss = st.session_state
TODAY = date.today()

SKILL_COLS = ["skill", "rating"]
CERT_COLS = ["title", "issuer", "platform", "domain", "completion_date", "credential_url"]
PROJ_COLS = ["title", "description", "tech_stack", "role", "project_type", "github_url"]
EVENT_COLS = ["name", "event_type", "theme", "event_date", "participation"]
FORM_KEYS = ["f_srn", "f_name", "f_college", "f_branch", "f_class", "f_year", "f_cgpa", "f_interests"]


# ---------- state helpers ----------
def fill_form(student: Student | None) -> None:
    """Load a profile (or a blank one) into the form. Must run before widgets render."""
    s = student or Student(srn="", name="")
    ss.form_student = s
    ss.editing = student.srn if student else None
    ss.f_srn, ss.f_name, ss.f_college = s.srn, s.name, s.college
    ss.f_branch, ss.f_class = s.branch, s.class_section
    ss.f_year, ss.f_cgpa, ss.f_interests = s.year_of_study, s.cgpa, list(s.interests)
    ss.skills_df = pd.DataFrame([{"skill": k, "rating": v} for k, v in s.skills.items()],
                                columns=SKILL_COLS)
    certs = pd.DataFrame([{k: getattr(c, k) for k in CERT_COLS} for c in s.certificates],
                         columns=CERT_COLS)
    certs["completion_date"] = pd.to_datetime(certs["completion_date"])
    ss.certs_df = certs
    ss.projects_df = pd.DataFrame([{k: getattr(p, k) for k in PROJ_COLS} for p in s.projects],
                                  columns=PROJ_COLS)
    events = pd.DataFrame([{k: getattr(e, k) for k in EVENT_COLS} for e in s.events],
                          columns=EVENT_COLS)
    events["event_date"] = pd.to_datetime(events["event_date"])
    ss.events_df = events
    ss.editor_ver = ss.get("editor_ver", 0) + 1  # fresh keys reset the data editors
    ss.errors = {}


def flash(kind: str, msg: str) -> None:
    ss.flash = (kind, msg)


def on_load() -> None:
    srn = normalize_srn(ss.get("load_input", ""))
    student = db.get_student(srn) if srn else None
    if student:
        fill_form(student)
        flash("success", f"Loaded profile {srn}.")
    else:
        flash("warning", f"No saved profile with SRN '{srn}'.")


def on_new() -> None:
    fill_form(None)
    flash("info", "Started a new blank profile.")


def on_delete() -> None:
    srn = ss.editing
    if srn and db.delete_student(srn):
        fill_form(None)
        flash("success", f"Deleted profile {srn} and all its certificates, projects and events.")


# ---------- dataframe -> model ----------
def _txt(v) -> str:
    return "" if v is None or (not isinstance(v, (list, str)) and pd.isna(v)) else str(v).strip()


def _blank(row: dict) -> bool:
    return all((not v) if isinstance(v, list) else _txt(v) == "" for v in row.values())


def _rows(df: pd.DataFrame) -> list[dict]:
    return [r for r in df.to_dict("records") if not _blank(r)]


def build_student(skills_df, certs_df, projects_df, events_df) -> Student:
    skills = {}
    for r in _rows(skills_df):
        if _txt(r["skill"]):
            rating = r["rating"]
            skills[_txt(r["skill"])] = 3 if rating is None or pd.isna(rating) else int(rating)
    return Student(
        srn=normalize_srn(ss.f_srn), name=_txt(ss.f_name), college=_txt(ss.f_college),
        branch=_txt(ss.f_branch), class_section=_txt(ss.f_class), year_of_study=int(ss.f_year),
        cgpa=None if ss.f_cgpa is None else float(ss.f_cgpa),
        interests=list(ss.f_interests), skills=skills,
        certificates=[Certificate(
            title=_txt(r["title"]), issuer=_txt(r["issuer"]), platform=_txt(r["platform"]) or "Other",
            domain=_txt(r["domain"]) or suggest_domain(_txt(r["title"])) or "",
            completion_date=_to_date(r["completion_date"]),
            credential_url=_txt(r["credential_url"])) for r in _rows(certs_df)],
        projects=[Project(
            title=_txt(r["title"]), description=_txt(r["description"]),
            tech_stack=[t.strip() for t in (r["tech_stack"] if isinstance(r["tech_stack"], list) else [])
                        if t and t.strip()],
            role=_txt(r["role"]) or "Solo", project_type=_txt(r["project_type"]) or "Academic",
            github_url=_txt(r["github_url"])) for r in _rows(projects_df)],
        events=[Event(
            name=_txt(r["name"]), event_type=_txt(r["event_type"]) or "Workshop",
            theme=_txt(r["theme"]), event_date=_to_date(r["event_date"]),
            participation=_txt(r["participation"]) or "Attended") for r in _rows(events_df)],
    )


def err(field: str) -> None:
    if field in ss.get("errors", {}):
        st.error(ss.errors[field], icon="⚠️")


# ---------- initialise / handle pending actions (before any widget renders) ----------
if "pending_load" in ss:
    fill_form(db.get_student(ss.pop("pending_load")))
elif "form_student" not in ss:
    fill_form(None)
elif "f_name" not in ss:
    # Widget state is dropped when the user visits another page; restore the last loaded profile.
    fill_form(ss.form_student if ss.editing else None)

# ---------- header ----------
st.title("👤 Student Profile")
mode = f"Editing **{ss.editing}**" if ss.editing else "Creating a **new** profile"
st.caption(f"{mode} · fields marked * are required")

c1, c2, c3 = st.columns([3, 1, 1], vertical_alignment="bottom")
c1.text_input("Load a saved profile by SRN", key="load_input", placeholder="e.g. PES1UG22CS101")
c2.button("Load", on_click=on_load, width="stretch")
c3.button("New profile", on_click=on_new, width="stretch")

if "flash" in ss:
    kind, msg = ss.pop("flash")
    getattr(st, kind)(msg)

ver = ss.editor_ver

# ---------- form ----------
with st.form("profile_form", border=False):
    st.subheader("Basic details")
    a, b = st.columns(2)
    with a:
        st.text_input("Full name *", key="f_name")
        err("name")
        st.text_input("SRN *", key="f_srn", disabled=bool(ss.editing),
                      help="Uppercase letters and digits, 6–15 characters. Lowercase is converted.")
        err("srn")
        st.text_input("College name *", key="f_college")
        err("college")
    with b:
        st.text_input("Branch / department", key="f_branch", placeholder="e.g. CSE")
        st.text_input("Class / section", key="f_class", placeholder="e.g. 5A")
        y, g = st.columns(2)
        with y:
            st.selectbox("Year of study *", list(range(cfg["year_min"], cfg["year_max"] + 1)),
                         key="f_year")
            err("year_of_study")
        with g:
            st.number_input("CGPA (optional)", key="f_cgpa", step=0.1, format="%.2f",
                            placeholder="0 – 10")
            err("cgpa")

    st.subheader("Skills & interests")
    s1, s2 = st.columns([3, 2])
    with s1:
        st.caption("Self-rated skills — pick a skill and rate yourself 1 (beginner) to 5 (expert).")
        skills_df = st.data_editor(
            ss.skills_df, key=f"skills_{ver}", num_rows="dynamic", width="stretch",
            hide_index=True,
            column_config={
                "skill": st.column_config.SelectboxColumn("Skill", options=skill_names(), required=True),
                "rating": st.column_config.NumberColumn("Rating", min_value=1, max_value=5, step=1,
                                                        default=3),
            })
        err("skills")
    with s2:
        st.multiselect("Interests", cfg["interests"], key="f_interests")

    st.subheader("Certificates")
    st.caption("Leave **Domain** blank to auto-detect it from the title.")
    certs_df = st.data_editor(
        ss.certs_df, key=f"certs_{ver}", num_rows="dynamic", width="stretch", hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Title *"),
            "issuer": st.column_config.TextColumn("Issuing organisation"),
            "platform": st.column_config.SelectboxColumn("Platform", options=cfg["certificate_platforms"],
                                                         default="Other"),
            "domain": st.column_config.SelectboxColumn(
                "Domain", options=skill_areas(),
                help="Leave blank and it is auto-detected from the title when you save."),
            "completion_date": st.column_config.DateColumn("Completed on", max_value=TODAY,
                                                           format="YYYY-MM-DD"),
            "credential_url": st.column_config.LinkColumn("Credential URL"),
        })
    err("certificates")

    st.subheader("Projects")
    projects_df = st.data_editor(
        ss.projects_df, key=f"projects_{ver}", num_rows="dynamic", width="stretch",
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Title *"),
            "description": st.column_config.TextColumn("Short description", width="large"),
            "tech_stack": st.column_config.MultiselectColumn(
                "Tech stack", options=skill_names(), accept_new_options=True,
                help="Pick from the list or type your own."),
            "role": st.column_config.SelectboxColumn("Role", options=cfg["project_roles"], default="Solo"),
            "project_type": st.column_config.SelectboxColumn("Type", options=cfg["project_types"],
                                                             default="Academic"),
            "github_url": st.column_config.LinkColumn("GitHub link"),
        })
    err("projects")

    st.subheader("Events attended")
    events_df = st.data_editor(
        ss.events_df, key=f"events_{ver}", num_rows="dynamic", width="stretch",
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Event name *"),
            "event_type": st.column_config.SelectboxColumn("Type", options=cfg["event_types"],
                                                           default="Workshop"),
            "theme": st.column_config.SelectboxColumn("Theme / domain", options=skill_areas()),
            "event_date": st.column_config.DateColumn("Date", max_value=TODAY, format="YYYY-MM-DD"),
            "participation": st.column_config.SelectboxColumn(
                "Participation", options=cfg["participation_levels"], default="Attended"),
        })
    err("events")

    submitted = st.form_submit_button("💾 Save profile", type="primary", key="save_btn")

if submitted:
    student = build_student(skills_df, certs_df, projects_df, events_df)
    taken = ss.editing is None and bool(student.srn) and db.student_exists(student.srn)
    errors = validate_student(student, srn_taken=taken)
    if errors:
        ss.errors = errors
        flash("error", f"Please fix {len(errors)} problem(s) highlighted below.")
    else:
        db.save_student(student, overwrite=ss.editing is not None)
        ss.pending_load = student.srn
        flash("success", f"Saved profile {student.srn}.")
    st.rerun()



def skill_area_section(student: Student) -> None:
    """Area scores (0-100) with the evidence behind each one."""
    ex = extract(student)
    st.subheader("🧭 Skill areas")
    st.caption("Calculated from your saved profile. Every point is traced back to its source. "
               "Levels: Beginner below 30 · Intermediate 30–60 · Strong above 60.")
    c1, c2 = st.columns([3, 2])
    c1.plotly_chart(area_bar_figure(ex.scores), width="stretch", config={"displayModeBar": False})
    with c2:
        st.markdown("**Evidence**")
        if not ex.evidence:
            st.info("No evidence yet — add skills, certificates, projects or events.")
        for area in sorted(ex.scores, key=lambda a: -ex.scores[a]):
            items = ex.evidence_for(area)
            if items:
                with st.expander(f"{area_label(area)} — {ex.scores[area]:.0f}/100 · "
                                 f"{area_level(ex.scores[area])} ({ex.raw[area]:g} pts)"):
                    st.markdown("\n".join(f"- {e.text()}" for e in items))


if ss.editing:
    if st.button("📊 See my career results", type="primary", key="to_results"):
        ss.results_srn = ss.editing
        st.switch_page("views/2_Results.py")
    skill_area_section(ss.form_student)
    with st.expander("🗑️ Delete this profile"):
        sure = st.checkbox(f"Yes, permanently delete {ss.editing} and all its entries", key="del_ok")
        st.button("Delete profile", on_click=on_delete, disabled=not sure, type="secondary")
