"""Headless UI tests for the Profile and History pages (streamlit.testing)."""
import pytest
from streamlit.testing.v1 import AppTest

from career import db
from career.config import ROOT


def _app(rel):
    return AppTest.from_file(str(ROOT / rel), default_timeout=30)


@pytest.fixture(autouse=True)
def temp_db(db_path, monkeypatch):
    monkeypatch.setenv("CAREER_DB_PATH", str(db_path))
    return db_path


def _profile():
    at = _app("views/1_Profile.py").run()
    assert not at.exception
    return at


def _fill(at, srn="ui22cs001", name="Ravi Kumar", college="Demo College", cgpa=None):
    at.text_input(key="f_srn").input(srn)
    at.text_input(key="f_name").input(name)
    at.text_input(key="f_college").input(college)
    at.selectbox(key="f_year").select(2)
    if cgpa is not None:
        at.number_input(key="f_cgpa").set_value(cgpa)
    return at


def _save(at):
    at.button(key="save_btn").click().run()
    assert not at.exception
    return at


def test_home_and_all_pages_render():
    for f in ["app.py", "views/1_Profile.py", "views/2_Results.py", "views/3_History.py",
              "views/4_About.py"]:
        assert not _app(f).run().exception, f


def test_save_new_profile(temp_db):
    at = _save(_fill(_profile(), cgpa=7.5))
    saved = db.get_student("UI22CS001", db_path=temp_db)  # SRN normalised to uppercase
    assert saved and saved.name == "Ravi Kumar" and saved.year_of_study == 2 and saved.cgpa == 7.5
    assert any("Saved profile" in s.value for s in at.success)
    assert at.text_input(key="f_srn").disabled  # now in edit mode


def test_inline_validation_errors(temp_db):
    at = _save(_fill(_profile(), srn="bad", name="", cgpa=12.0))
    msgs = " ".join(e.value for e in at.error)
    assert "SRN must be" in msgs and "Full name is required" in msgs and "CGPA must be" in msgs
    assert db.list_students(db_path=temp_db) == []


def test_duplicate_srn_blocked(temp_db, full_student):
    db.save_student(full_student, db_path=temp_db)
    at = _save(_fill(_profile(), srn=full_student.srn))
    assert any("already exists" in e.value for e in at.error)
    assert db.get_student(full_student.srn, db_path=temp_db).name == full_student.name


def test_load_edit_and_delete(temp_db, full_student):
    db.save_student(full_student, db_path=temp_db)
    at = _profile()
    at.text_input(key="load_input").input(full_student.srn.lower())
    at.button[0].click().run()  # "Load"
    assert at.text_input(key="f_name").value == full_student.name
    assert at.text_input(key="f_srn").value == full_student.srn
    at.text_input(key="f_branch").input("ECE")
    _save(at)
    edited = db.get_student(full_student.srn, db_path=temp_db)
    assert edited.branch == "ECE"
    assert len(edited.certificates) == 2 and len(edited.events) == 2  # lists kept on edit

    at.checkbox(key="del_ok").check().run()
    next(b for b in at.button if b.label == "Delete profile").click().run()
    assert db.get_student(full_student.srn, db_path=temp_db) is None
    assert at.text_input(key="f_name").value == ""


def test_history_lists_and_deletes(temp_db, full_student):
    db.save_student(full_student, db_path=temp_db)
    at = _app("views/3_History.py").run()
    assert full_student.srn in at.dataframe[0].value["SRN"].tolist()
    at.checkbox(key="hist_del_ok").check().run()
    at.button(key="hist_delete").click().run()
    assert not at.exception
    assert db.list_students(db_path=temp_db) == []


def test_profile_shows_area_scores_and_suggests_domain(temp_db, full_student):
    full_student.certificates[0].domain = ""          # AWS Cloud Practitioner, no domain
    db.save_student(full_student, db_path=temp_db)
    at = _profile()
    at.text_input(key="load_input").input(full_student.srn)
    at.button[0].click().run()
    assert any("Skill areas" in h.value for h in at.subheader)
    labels = [e.label for e in at.expander]
    assert any(l.startswith("Cloud & DevOps") for l in labels)
    md = " ".join(m.value for m in at.markdown)
    assert "CLOUD_DEVOPS +2 from certificate 'AWS Cloud Practitioner'" in md
    _save(at)
    assert db.get_student(full_student.srn, db_path=temp_db).certificates[0].domain == "CLOUD_DEVOPS"


def test_results_page_shows_match_first_and_logs_once(temp_db):
    from career.demo import load_demo
    demo = load_demo("web_2nd_year")
    db.save_student(demo.student, db_path=temp_db)
    at = _app("views/2_Results.py").run()
    assert not at.exception
    html = " ".join(m.value for m in at.markdown)
    assert demo.expected_role in html
    assert "skill match" in html and 'class="match-num"' in html
    assert "Model confidence: 100%" not in html
    assert len(at.tabs) == 3
    assert "chip-Strong" in html and "chip-Beginner" in html          # level labels shown
    assert at.get("download_button")[0].proto.label == "⬇️ Download PDF report"
    at.run()  # rerun must not log a duplicate prediction
    assert len(db.list_predictions(demo.student.srn, db_path=temp_db)) == 1


def test_results_page_without_profiles(temp_db):
    at = _app("views/2_Results.py").run()
    assert not at.exception and "No saved profiles" in at.info[0].value


def test_about_page_shows_metrics_and_synthetic_note():
    at = _app("views/4_About.py").run()
    assert not at.exception
    assert "synthetic data" in at.warning[0].value
    assert any(m.label == "Top-3 accuracy" for m in at.metric)
