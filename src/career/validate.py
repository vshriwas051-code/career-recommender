"""Validation for student profiles. Returns {field: message} so the UI can show errors inline."""
from __future__ import annotations

import re
from datetime import date

from .config import app_config
from .models import Student


def normalize_srn(srn: str) -> str:
    return (srn or "").strip().upper()


def validate_srn(srn: str) -> str | None:
    """Return an error message, or None if the SRN is valid. Expects a normalised SRN."""
    if not srn:
        return "SRN is required."
    if not re.fullmatch(app_config()["srn_pattern"], srn):
        return "SRN must be 6–15 uppercase letters and digits (e.g. PES1UG22CS101)."
    return None


def validate_student(student: Student, *, srn_taken: bool = False,
                     today: date | None = None) -> dict[str, str]:
    """Validate a full profile. `srn_taken` = another saved profile already uses this SRN."""
    cfg = app_config()
    today = today or date.today()
    errors: dict[str, str] = {}

    if err := validate_srn(student.srn):
        errors["srn"] = err
    elif srn_taken:
        errors["srn"] = f"SRN {student.srn} already exists. Load it from History to edit it."

    if not student.name.strip():
        errors["name"] = "Full name is required."
    if not student.college.strip():
        errors["college"] = "College name is required."

    if not isinstance(student.year_of_study, int) or not (
        cfg["year_min"] <= student.year_of_study <= cfg["year_max"]
    ):
        errors["year_of_study"] = f"Year of study must be {cfg['year_min']}–{cfg['year_max']}."

    if student.cgpa is not None and not (cfg["cgpa_min"] <= student.cgpa <= cfg["cgpa_max"]):
        errors["cgpa"] = f"CGPA must be between {cfg['cgpa_min']:g} and {cfg['cgpa_max']:g}."

    bad = [s for s, r in student.skills.items() if not (1 <= int(r) <= 5)]
    if bad:
        errors["skills"] = f"Skill ratings must be 1–5 (check: {', '.join(bad)})."

    msgs = []
    for i, c in enumerate(student.certificates, 1):
        if not c.title.strip():
            msgs.append(f"Row {i}: title is required.")
        if c.completion_date and c.completion_date > today:
            msgs.append(f"Row {i}: completion date {c.completion_date} is in the future.")
    if msgs:
        errors["certificates"] = " ".join(msgs)

    msgs = [f"Row {i}: title is required." for i, p in enumerate(student.projects, 1)
            if not p.title.strip()]
    if msgs:
        errors["projects"] = " ".join(msgs)

    msgs = []
    for i, e in enumerate(student.events, 1):
        if not e.name.strip():
            msgs.append(f"Row {i}: event name is required.")
        if e.event_date and e.event_date > today:
            msgs.append(f"Row {i}: event date {e.event_date} is in the future.")
    if msgs:
        errors["events"] = " ".join(msgs)

    return errors
