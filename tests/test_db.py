import sqlite3
from dataclasses import replace

from career import db
from career.models import Event, Student


def _strip_ids(s: Student) -> dict:
    d = s.to_dict()
    for key, id_field in [("certificates", "cert_id"), ("projects", "project_id"), ("events", "event_id")]:
        for row in d[key]:
            row[id_field] = None
    return d


def test_round_trip_full_profile(full_student, db_path):
    db.save_student(full_student, db_path=db_path)
    loaded = db.get_student(full_student.srn, db_path=db_path)
    assert loaded is not None
    assert _strip_ids(loaded) == _strip_ids(full_student)
    assert len(loaded.certificates) == 2 and len(loaded.projects) == 1 and len(loaded.events) == 2
    assert loaded.projects[0].tech_stack == ["python", "pandas", "power bi"]
    assert all(c.cert_id for c in loaded.certificates)


def test_edit_replaces_lists(full_student, db_path):
    db.save_student(full_student, db_path=db_path)
    edited = replace(full_student, name="Asha R.", certificates=[],
                     events=[Event("CTF Night", "Competition", "SECURITY", None, "Winner")])
    db.save_student(edited, overwrite=True, db_path=db_path)
    loaded = db.get_student(full_student.srn, db_path=db_path)
    assert loaded.name == "Asha R."
    assert loaded.certificates == []
    assert [e.name for e in loaded.events] == ["CTF Night"]


def test_edit_keeps_prediction_history(full_student, db_path):
    db.save_student(full_student, db_path=db_path)
    db.add_prediction(full_student.srn, [{"role": "Data Analyst", "confidence": 0.7}],
                      {"DATA_ANALYSIS": 80.0}, "v1", db_path=db_path)
    db.save_student(replace(full_student, cgpa=9.0), overwrite=True, db_path=db_path)
    db.add_prediction(full_student.srn, [{"role": "Data Scientist", "confidence": 0.6}],
                      {"ML_AI": 70.0}, "v1", db_path=db_path)
    assert len(db.list_predictions(full_student.srn, db_path=db_path)) == 2


def test_delete_cascades(full_student, db_path):
    db.save_student(full_student, db_path=db_path)
    db.add_prediction(full_student.srn, [], {}, db_path=db_path)
    assert db.delete_student(full_student.srn, db_path=db_path)
    assert db.get_student(full_student.srn, db_path=db_path) is None
    conn = sqlite3.connect(db_path)
    for table in ("certificates", "projects", "events", "predictions"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    conn.close()
    assert not db.delete_student(full_student.srn, db_path=db_path)


def test_list_students(full_student, db_path):
    db.save_student(full_student, db_path=db_path)
    rows = db.list_students(db_path=db_path)
    assert rows[0]["srn"] == full_student.srn
    assert (rows[0]["certificates"], rows[0]["projects"], rows[0]["events"]) == (2, 1, 2)


def test_dict_round_trip(full_student):
    assert Student.from_dict(full_student.to_dict()) == full_student
