"""Profile -> fixed-order feature vector for the model.

Order: 10 area scores (0-100, skills.yaml order), year_of_study, cgpa, then one
0/1 flag per interest (app.yaml order). Missing CGPA is imputed with a neutral value.
"""
from __future__ import annotations

import re

import numpy as np

from .config import app_config, skill_areas
from .models import Student
from .skills import Extraction, extract

CGPA_DEFAULT = 7.0  # used when CGPA is not given


def interest_feature(interest: str) -> str:
    return "interest_" + re.sub(r"[^a-z0-9]+", "_", interest.lower()).strip("_")


def feature_names() -> list[str]:
    return ([f"area_{a}" for a in skill_areas()] + ["year_of_study", "cgpa"]
            + [interest_feature(i) for i in app_config()["interests"]])


def build_vector(area_scores: dict[str, float], year_of_study: int, cgpa: float | None,
                 interests: list[str]) -> np.ndarray:
    chosen = set(interests)
    return np.array(
        [float(area_scores.get(a, 0.0)) for a in skill_areas()]
        + [float(year_of_study), float(CGPA_DEFAULT if cgpa is None else cgpa)]
        + [1.0 if i in chosen else 0.0 for i in app_config()["interests"]],
        dtype=float,
    )


def student_features(student: Student, extraction: Extraction | None = None) -> np.ndarray:
    ex = extraction or extract(student)
    return build_vector(ex.scores, student.year_of_study, student.cgpa, student.interests)
