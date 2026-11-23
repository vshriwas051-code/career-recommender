from dataclasses import replace
from datetime import date

import pytest

from career import db
from career.models import Certificate, Event
from career.validate import normalize_srn, validate_srn, validate_student


@pytest.mark.parametrize("srn", ["PES1UG22CS101", "ABC123", "A1B2C3D4E5F6G7H"])
def test_valid_srns(srn):
    assert validate_srn(srn) is None


@pytest.mark.parametrize("srn", ["", "AB12", "A" * 16, "pes1ug22cs101", "PES-1UG", "PES 12345"])
def test_invalid_srns(srn):
    assert validate_srn(srn) is not None


def test_normalize_srn_uppercases_and_strips():
    assert normalize_srn("  pes1ug22cs101 ") == "PES1UG22CS101"
    assert validate_srn(normalize_srn("pes1ug22cs101")) is None


def test_duplicate_srn(full_student, db_path):
    db.save_student(full_student, db_path=db_path)
    taken = db.student_exists(full_student.srn, db_path=db_path)
    assert taken
    assert "already exists" in validate_student(full_student, srn_taken=taken)["srn"]
    with pytest.raises(db.DuplicateSRNError):
        db.save_student(full_student, db_path=db_path)


def test_full_profile_is_valid(full_student):
    assert validate_student(full_student, today=date(2026, 1, 1)) == {}


@pytest.mark.parametrize("year", [0, 5])
def test_year_out_of_range(full_student, year):
    assert "year_of_study" in validate_student(replace(full_student, year_of_study=year))


@pytest.mark.parametrize("cgpa", [-0.1, 10.5])
def test_cgpa_out_of_range(full_student, cgpa):
    assert "cgpa" in validate_student(replace(full_student, cgpa=cgpa))


def test_cgpa_optional(full_student):
    assert "cgpa" not in validate_student(replace(full_student, cgpa=None))


def test_future_dates_rejected(full_student):
    today = date(2026, 1, 1)
    s = replace(full_student,
                certificates=[Certificate("X", completion_date=date(2026, 2, 1))],
                events=[Event("Y", event_date=date(2027, 1, 1))])
    errs = validate_student(s, today=today)
    assert "future" in errs["certificates"]
    assert "future" in errs["events"]


def test_required_fields(full_student):
    s = replace(full_student, name=" ", college="",
                certificates=[Certificate("")], events=[Event("")])
    errs = validate_student(s)
    assert {"name", "college", "certificates", "events"} <= errs.keys()
