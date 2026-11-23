"""Rule-based, explainable skill extraction.

Text from certificates, projects and events is matched against keywords in
config/skills.yaml (keyword -> skill -> area). Each piece of evidence adds
weighted points to its area(s), and every point keeps its source so the app can
explain *why* an area scored the way it did.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from functools import lru_cache

from .config import load_yaml, scoring, skill_areas
from .models import Student

SOURCE_LABELS = {"certificate": "certificate", "project": "project", "event": "event",
                 "skill": "self-rated skill"}


@dataclass(frozen=True)
class Evidence:
    area: str
    points: float
    source_type: str         # certificate | project | event | skill
    source: str              # title / name of the item
    matched: tuple[str, ...] = ()  # skills that matched, for the detail line

    def text(self) -> str:
        """e.g. "CLOUD_DEVOPS +2 from certificate 'AWS Cloud Practitioner'"."""
        return f"{self.area} {self.short()}"

    def short(self) -> str:
        """e.g. "+2 from certificate 'AWS Cloud Practitioner'"."""
        return f"+{self.points:g} from {SOURCE_LABELS[self.source_type]} '{self.source}'"


@dataclass
class Extraction:
    raw: dict[str, float]               # area -> raw points
    scores: dict[str, float]            # area -> 0-100
    evidence: list[Evidence] = field(default_factory=list)

    def evidence_for(self, area: str) -> list[Evidence]:
        return sorted((e for e in self.evidence if e.area == area), key=lambda e: -e.points)

    def top_areas(self, n: int = 3) -> list[str]:
        return [a for a, s in sorted(self.scores.items(), key=lambda kv: -kv[1]) if s > 0][:n]


# ---------- keyword matching ----------
@lru_cache(maxsize=1)
def _taxonomy() -> tuple[dict[str, str], list[tuple[re.Pattern, str]]]:
    """Return (skill -> area, [(compiled keyword pattern, skill)] longest keyword first)."""
    cfg = load_yaml("skills.yaml")
    skill_area: dict[str, str] = {k.lower(): v for k, v in cfg["skills"].items()}
    kw_skill: dict[str, str] = {}
    for skill in skill_area:
        kw_skill[skill] = skill
        for part in skill.split("/"):
            if len(part.strip()) >= 3:
                kw_skill.setdefault(part.strip(), skill)
    for kw, skill in (cfg.get("keywords") or {}).items():
        kw_skill[str(kw).lower()] = skill.lower()
    patterns = [(re.compile(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9+#])"), skill)
                for kw, skill in sorted(kw_skill.items(), key=lambda kv: -len(kv[0]))]
    return skill_area, patterns


def skill_area(skill: str) -> str | None:
    return _taxonomy()[0].get(skill.lower())


def match_skills(text: str) -> list[str]:
    """Skills found in free text, in order of first match. Longer keywords win
    (so "react native" is MOBILE, not WEB), and each matched span is consumed."""
    text = (text or "").lower()
    found: list[str] = []
    for pattern, skill in _taxonomy()[1]:
        if pattern.search(text):
            text = pattern.sub(" ", text)
            if skill not in found:
                found.append(skill)
    return found


def suggest_domain(title: str) -> str | None:
    """Most frequent area among skills matched in a certificate title (None if nothing matches)."""
    areas = [skill_area(s) for s in match_skills(title)]
    areas = [a for a in areas if a]
    return Counter(areas).most_common(1)[0][0] if areas else None


# ---------- extraction ----------
def _item_areas(text: str, declared: str | None) -> tuple[list[str], tuple[str, ...]]:
    skills = match_skills(text)
    areas = []
    for s in skills:
        a = skill_area(s)
        if a and a not in areas:
            areas.append(a)
    valid = set(skill_areas())
    if declared and declared in valid and declared not in areas:
        areas.append(declared)
    return areas, tuple(skills)


def extract(student: Student) -> Extraction:
    """Score every skill area from the profile, keeping an evidence trail.

    Each item adds its points once to each area it touches (a project using
    Python and pandas adds to PROGRAMMING and DATA_ANALYSIS, not twice to one).
    """
    w = scoring()
    evidence: list[Evidence] = []

    def add(areas, points, kind, source, skills):
        for a in areas:
            matched = tuple(s for s in skills if skill_area(s) == a)
            evidence.append(Evidence(a, float(points), kind, source, matched))

    for c in student.certificates:
        areas, skills = _item_areas(f"{c.title} {c.issuer}", c.domain)
        add(areas, w["certificate"], "certificate", c.title, skills)

    for p in student.projects:
        areas, skills = _item_areas(f"{p.title} {p.description} {' , '.join(p.tech_stack)}", None)
        bonus = w["project_bonus"] if (p.role == "Team Lead" or p.project_type == "Hackathon") else 0
        add(areas, w["project"] + bonus, "project", p.title, skills)

    for e in student.events:
        areas, skills = _item_areas(e.name, e.theme)
        bonus = w["event_bonus"] if e.participation in ("Finalist", "Winner") else 0
        add(areas, w["event"] + bonus, "event", e.name, skills)

    for skill, rating in student.skills.items():
        a = skill_area(skill)
        if a:
            evidence.append(Evidence(a, float(rating) * w["skill_rating_factor"], "skill",
                                     f"{skill} ({rating}/5)", (skill.lower(),)))

    raw: dict[str, float] = defaultdict(float)
    for ev in evidence:
        raw[ev.area] += ev.points
    raw = {a: raw.get(a, 0.0) for a in skill_areas()}
    return Extraction(raw=raw, scores=normalise(raw, w["area_cap"]), evidence=evidence)


def normalise(raw: dict[str, float], cap: float) -> dict[str, float]:
    """Map raw points to 0-100 on an absolute scale: `cap` points or more = 100."""
    return {a: round(min(100.0, 100.0 * v / cap), 1) for a, v in raw.items()}
