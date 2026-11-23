"""Fictional demo profiles stored as JSON in demo/."""
from __future__ import annotations

import json
from dataclasses import dataclass

from .config import ROOT
from .models import Student

DEMO_DIR = ROOT / "demo"


@dataclass
class Demo:
    key: str
    description: str
    expected_role: str
    student: Student


def list_demos() -> list[Demo]:
    demos = []
    for path in sorted(DEMO_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        demos.append(Demo(path.stem, data["description"], data["expected_role"],
                          Student.from_dict(data["profile"])))
    return demos


def load_demo(key: str) -> Demo:
    for d in list_demos():
        if d.key == key:
            return d
    raise KeyError(key)


def install_demo(key: str, db_path=None) -> Student:
    """Save (or refresh) a fictional demo student in the database and return it."""
    from . import db
    demo = load_demo(key)
    db.save_student(demo.student, overwrite=True, db_path=db_path)
    return demo.student
