"""SQLite storage for student profiles and prediction history."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .config import ROOT, app_config
from .models import Certificate, Event, Project, Student, _to_date

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    srn            TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    college        TEXT,
    branch         TEXT,
    class_section  TEXT,
    year_of_study  INTEGER NOT NULL CHECK (year_of_study BETWEEN 1 AND 4),
    cgpa           REAL CHECK (cgpa IS NULL OR cgpa BETWEEN 0 AND 10),
    interests      TEXT NOT NULL DEFAULT '[]',
    skills         TEXT NOT NULL DEFAULT '{}',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS certificates (
    cert_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    srn             TEXT NOT NULL REFERENCES students(srn) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    issuer          TEXT,
    platform        TEXT,
    domain          TEXT,
    completion_date TEXT,
    credential_url  TEXT
);
CREATE TABLE IF NOT EXISTS projects (
    project_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    srn          TEXT NOT NULL REFERENCES students(srn) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    description  TEXT,
    tech_stack   TEXT NOT NULL DEFAULT '[]',
    role         TEXT,
    project_type TEXT,
    github_url   TEXT
);
CREATE TABLE IF NOT EXISTS events (
    event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    srn           TEXT NOT NULL REFERENCES students(srn) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    event_type    TEXT,
    theme         TEXT,
    event_date    TEXT,
    participation TEXT
);
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    srn           TEXT NOT NULL REFERENCES students(srn) ON DELETE CASCADE,
    created_at    TEXT NOT NULL,
    model_version TEXT,
    top_roles     TEXT NOT NULL,
    area_scores   TEXT NOT NULL
);
"""


class DuplicateSRNError(ValueError):
    pass


def default_db_path() -> Path:
    """`CAREER_DB_PATH` env var overrides config (used by tests)."""
    return Path(os.environ.get("CAREER_DB_PATH") or ROOT / app_config()["db_path"])


@contextmanager
def connect(db_path: str | Path | None = None) -> Iterator[sqlite3.Connection]:
    path = Path(db_path) if db_path else default_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _iso(d) -> str | None:
    return d.isoformat() if d else None


def student_exists(srn: str, db_path=None) -> bool:
    with connect(db_path) as conn:
        return conn.execute("SELECT 1 FROM students WHERE srn = ?", (srn,)).fetchone() is not None


def save_student(student: Student, *, overwrite: bool = False, db_path=None) -> None:
    """Insert or update a profile and replace its certificate/project/event lists.

    Uses an UPSERT (not INSERT OR REPLACE) so the student row is never deleted —
    that keeps prediction history intact.
    """
    now = _now()
    with connect(db_path) as conn:
        exists = conn.execute("SELECT 1 FROM students WHERE srn = ?", (student.srn,)).fetchone()
        if exists and not overwrite:
            raise DuplicateSRNError(f"SRN {student.srn} already exists")
        conn.execute(
            """INSERT INTO students (srn, name, college, branch, class_section, year_of_study,
                                     cgpa, interests, skills, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(srn) DO UPDATE SET
                 name=excluded.name, college=excluded.college, branch=excluded.branch,
                 class_section=excluded.class_section, year_of_study=excluded.year_of_study,
                 cgpa=excluded.cgpa, interests=excluded.interests, skills=excluded.skills,
                 updated_at=excluded.updated_at""",
            (student.srn, student.name, student.college, student.branch, student.class_section,
             student.year_of_study, student.cgpa, json.dumps(student.interests),
             json.dumps(student.skills), now, now),
        )
        for table in ("certificates", "projects", "events"):
            conn.execute(f"DELETE FROM {table} WHERE srn = ?", (student.srn,))
        conn.executemany(
            """INSERT INTO certificates (srn, title, issuer, platform, domain, completion_date,
                                         credential_url) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(student.srn, c.title, c.issuer, c.platform, c.domain, _iso(c.completion_date),
              c.credential_url) for c in student.certificates],
        )
        conn.executemany(
            """INSERT INTO projects (srn, title, description, tech_stack, role, project_type,
                                     github_url) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(student.srn, p.title, p.description, json.dumps(p.tech_stack), p.role,
              p.project_type, p.github_url) for p in student.projects],
        )
        conn.executemany(
            """INSERT INTO events (srn, name, event_type, theme, event_date, participation)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(student.srn, e.name, e.event_type, e.theme, _iso(e.event_date), e.participation)
             for e in student.events],
        )


def get_student(srn: str, db_path=None) -> Student | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM students WHERE srn = ?", (srn,)).fetchone()
        if row is None:
            return None
        certs = [Certificate(title=r["title"], issuer=r["issuer"] or "", platform=r["platform"] or "",
                             domain=r["domain"] or "", completion_date=_to_date(r["completion_date"]),
                             credential_url=r["credential_url"] or "", cert_id=r["cert_id"])
                 for r in conn.execute("SELECT * FROM certificates WHERE srn = ? ORDER BY cert_id",
                                       (srn,))]
        projects = [Project(title=r["title"], description=r["description"] or "",
                            tech_stack=json.loads(r["tech_stack"]), role=r["role"] or "",
                            project_type=r["project_type"] or "", github_url=r["github_url"] or "",
                            project_id=r["project_id"])
                    for r in conn.execute("SELECT * FROM projects WHERE srn = ? ORDER BY project_id",
                                          (srn,))]
        events = [Event(name=r["name"], event_type=r["event_type"] or "", theme=r["theme"] or "",
                        event_date=_to_date(r["event_date"]), participation=r["participation"] or "",
                        event_id=r["event_id"])
                  for r in conn.execute("SELECT * FROM events WHERE srn = ? ORDER BY event_id", (srn,))]
    return Student(
        srn=row["srn"], name=row["name"], college=row["college"] or "", branch=row["branch"] or "",
        class_section=row["class_section"] or "", year_of_study=row["year_of_study"],
        cgpa=row["cgpa"], interests=json.loads(row["interests"]), skills=json.loads(row["skills"]),
        certificates=certs, projects=projects, events=events,
    )


def list_students(db_path=None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT s.srn, s.name, s.college, s.branch, s.class_section, s.year_of_study,
                      (SELECT COUNT(*) FROM certificates c WHERE c.srn = s.srn) AS certificates,
                      (SELECT COUNT(*) FROM projects p WHERE p.srn = s.srn) AS projects,
                      (SELECT COUNT(*) FROM events e WHERE e.srn = s.srn) AS events,
                      s.updated_at
               FROM students s ORDER BY s.updated_at DESC, s.srn"""
        ).fetchall()
    return [dict(r) for r in rows]


def delete_student(srn: str, db_path=None) -> bool:
    with connect(db_path) as conn:
        return conn.execute("DELETE FROM students WHERE srn = ?", (srn,)).rowcount > 0


def add_prediction(srn: str, top_roles: list[dict], area_scores: dict[str, float],
                   model_version: str = "", db_path=None) -> int:
    with connect(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO predictions (srn, created_at, model_version, top_roles, area_scores)
               VALUES (?, ?, ?, ?, ?)""",
            (srn, _now(), model_version, json.dumps(top_roles), json.dumps(area_scores)),
        )
        return cur.lastrowid


def list_predictions(srn: str, db_path=None) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM predictions WHERE srn = ? ORDER BY prediction_id DESC", (srn,)
        ).fetchall()
    return [{**dict(r), "top_roles": json.loads(r["top_roles"]),
             "area_scores": json.loads(r["area_scores"])} for r in rows]
