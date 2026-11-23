"""Dataclasses for a student profile and its repeatable lists."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


def _to_date(value: Any) -> date | None:
    """Coerce None/''/NaN/NaT, date, datetime, pandas Timestamp or ISO string to a date."""
    if value is None or value == "" or value != value:  # NaN and NaT are != themselves
        return None
    if isinstance(value, datetime):  # includes pandas Timestamp
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


@dataclass
class Certificate:
    title: str
    issuer: str = ""
    platform: str = "Other"
    domain: str = ""
    completion_date: date | None = None
    credential_url: str = ""
    cert_id: int | None = None


@dataclass
class Project:
    title: str
    description: str = ""
    tech_stack: list[str] = field(default_factory=list)
    role: str = "Solo"
    project_type: str = "Academic"
    github_url: str = ""
    project_id: int | None = None


@dataclass
class Event:
    name: str
    event_type: str = "Workshop"
    theme: str = ""
    event_date: date | None = None
    participation: str = "Attended"
    event_id: int | None = None


@dataclass
class Student:
    srn: str
    name: str
    college: str = ""
    branch: str = ""
    class_section: str = ""
    year_of_study: int = 1
    cgpa: float | None = None
    interests: list[str] = field(default_factory=list)
    skills: dict[str, int] = field(default_factory=dict)  # skill -> self rating 1-5
    certificates: list[Certificate] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for c in d["certificates"]:
            c["completion_date"] = c["completion_date"].isoformat() if c["completion_date"] else None
        for e in d["events"]:
            e["event_date"] = e["event_date"].isoformat() if e["event_date"] else None
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Student":
        d = dict(d)
        certs = [Certificate(**{**c, "completion_date": _to_date(c.get("completion_date"))})
                 for c in d.pop("certificates", [])]
        projects = [Project(**p) for p in d.pop("projects", [])]
        events = [Event(**{**e, "event_date": _to_date(e.get("event_date"))})
                  for e in d.pop("events", [])]
        return cls(**d, certificates=certs, projects=projects, events=events)
