"""History page: list saved profiles; open or delete them by SRN."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from career import db  # noqa: E402
from career.ui import apply_style, doodle, html, page_header, section_title  # noqa: E402

st.set_page_config(page_title="History · Career Recommender", layout="wide")
apply_style()
ss = st.session_state

page_header("Saved profiles", "Everyone who has saved a profile on this computer. Open one to edit it, "
            "or delete it for good.", "books")

if "hist_flash" in ss:
    st.success(ss.pop("hist_flash"))

rows = db.list_students()
if not rows:
    with st.container(key="card-empty"):
        html(f'<div class="empty"><div class="dd float" style="--dur:5.4s">{doodle("paper-plane")}</div>'
             '<h3>No profiles yet</h3><p class="muted">Add your certificates, projects and events to see '
             'your top 3 roles.</p></div>')
        _, mid, _ = st.columns([1, 1.2, 1])
        if mid.button("Build your first profile", type="primary", width="stretch", key="hist_build"):
            st.switch_page("views/1_Profile.py")
    st.stop()

with st.container(key="card-table"):
    section_title(f"{len(rows)} saved profile{'s' if len(rows) != 1 else ''}", "grad-cap")
    df = pd.DataFrame(rows).rename(columns={
        "srn": "SRN", "name": "Name", "college": "College", "branch": "Branch",
        "class_section": "Class", "year_of_study": "Year", "certificates": "Certs",
        "projects": "Projects", "events": "Events", "updated_at": "Last updated"})
    st.dataframe(df, hide_index=True, width="stretch")

with st.container(key="card-actions"):
    section_title("Open or delete", "magnifier")
    srn = st.selectbox("Select SRN", [r["srn"] for r in rows],
                       format_func=lambda s: f"{s} — {next(r['name'] for r in rows if r['srn'] == s)}",
                       key="hist_srn")
    c1, c2 = st.columns(2, vertical_alignment="bottom")
    with c1:
        if st.button("Open in Profile", type="primary", width="stretch", key="hist_open"):
            ss.pending_load = srn
            st.switch_page("views/1_Profile.py")
    with c2:
        sure = st.checkbox(f"Confirm delete of {srn}", key="hist_del_ok")
        if st.button("Delete", icon=":material/delete:", disabled=not sure, width="stretch", key="hist_delete"):
            db.delete_student(srn)
            if ss.get("editing") == srn:  # the Profile page had this one loaded
                ss.pop("form_student", None)
                ss.editing = None
            ss.hist_flash = f"Deleted {srn} and all its entries."
            st.rerun()
