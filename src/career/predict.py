"""Top-3 role prediction: model confidence (softened for display) + cosine match score."""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np

from . import db
from .config import app_config, role_by_name, roles, skill_areas
from .features import student_features
from .models import Student
from .skills import Extraction, extract
from .train import load_model


@dataclass
class RoleMatch:
    role: str
    match: float              # cosine similarity × 100 — the headline number
    confidence: float         # softened + capped model probability (0–1), for display
    confidence_label: str     # High / Medium / Low
    raw_probability: float    # untouched model output, kept for transparency
    summary: str = ""


@dataclass
class Prediction:
    student: Student
    extraction: Extraction
    top: list[RoleMatch]
    matches: dict[str, float] = field(default_factory=dict)   # every role -> match score
    model_version: str = ""


@lru_cache(maxsize=1)
def _artifacts():
    return load_model()


def soften(proba: np.ndarray, temperature: float, cap: float) -> np.ndarray:
    """Temperature-scale probabilities (keeps the ranking, flattens extremes), then cap.

    p_i ∝ exp(log p_i / T). T = 1 leaves them unchanged; larger T is softer.
    """
    logits = np.log(np.clip(proba, 1e-12, 1.0)) / temperature
    p = np.exp(logits - logits.max())
    return np.minimum(p / p.sum(), cap)


def format_confidence(conf: float) -> str:
    """Display string: never "0%" (reads as broken) and never above the cap."""
    return "<1%" if conf < 0.005 else f"{conf * 100:.0f}%"


def confidence_label(conf: float) -> str:
    bands = app_config()["confidence_bands"]
    return "High" if conf >= bands["high"] else "Medium" if conf >= bands["medium"] else "Low"


def match_scores(area_scores: dict[str, float]) -> dict[str, float]:
    """Cosine similarity between the student's area vector and each role's ideal profile (0–100)."""
    areas = skill_areas()
    s = np.array([area_scores.get(a, 0.0) for a in areas], dtype=float)
    out = {}
    for r in roles():
        ideal = np.array([r["profile"][a] for a in areas], dtype=float)
        denom = np.linalg.norm(s) * np.linalg.norm(ideal)
        out[r["name"]] = round(float(s @ ideal / denom) * 100, 1) if denom else 0.0
    return out


def predict(student: Student, k: int = 3) -> Prediction:
    model, meta = _artifacts()
    cfg = app_config()
    ex = extract(student)
    raw = model.predict_proba(student_features(student, ex).reshape(1, -1))[0]
    soft = soften(raw, cfg["confidence_temperature"], cfg["confidence_cap"])
    matches = match_scores(ex.scores)
    top = []
    for i in np.argsort(raw)[::-1][:k]:
        name = str(model.classes_[i])
        conf = round(float(soft[i]), 3)
        top.append(RoleMatch(role=name, match=matches[name], confidence=conf,
                             confidence_label=confidence_label(conf),
                             raw_probability=round(float(raw[i]), 6),
                             summary=role_by_name(name).get("summary", "")))
    return Prediction(student=student, extraction=ex, top=top, matches=matches,
                      model_version=meta.get("model_version", ""))


def save_prediction(pred: Prediction, db_path=None) -> int:
    """Append to the predictions history table (never overwrites)."""
    top = [{"role": r.role, "match": r.match, "confidence": r.confidence,
            "raw_probability": r.raw_probability} for r in pred.top]
    return db.add_prediction(pred.student.srn, top, pred.extraction.scores,
                             pred.model_version, db_path=db_path)
