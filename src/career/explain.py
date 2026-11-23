"""Why this role, skill gaps, and next steps (filtered by gaps and year of study)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .config import app_config, area_label, role_by_name, roles, skill_areas
from .models import Student
from .predict import Prediction, predict
from .skills import Extraction

RELEVANT_IDEAL = 25     # an area matters to a role if its ideal score is at least this
MIN_WHY_SCORE = 20      # a student's area must be at least this to count as a reason
MIN_GAP = 5             # ignore gaps smaller than this (noise)
N_WHY = 3
N_CERTS, N_PROJECTS, N_EVENTS = 3, 2, 2


@dataclass
class WhyItem:
    area: str
    label: str
    score: float
    ideal: float
    evidence: list[str]

    def headline(self) -> str:
        return f"{self.label} — you score {self.score:g}/100 (role ideal {self.ideal:g})"


@dataclass
class Gap:
    area: str
    label: str
    score: float
    target: float      # ideal × year expectation
    ideal: float
    gap: float


@dataclass
class Step:
    title: str
    area: str
    level: str
    reason: str


@dataclass
class NextSteps:
    stage: str
    stage_title: str
    tips: list[str]
    certificates: list[Step] = field(default_factory=list)
    projects: list[Step] = field(default_factory=list)
    events: list[Step] = field(default_factory=list)


@dataclass
class RoleExplanation:
    role: str
    why: list[WhyItem]
    gaps: list[Gap]
    next_steps: NextSteps


# ---------- why ----------
def why(role: str, ex: Extraction, n: int = N_WHY) -> list[WhyItem]:
    """Areas that contribute most to the fit: high student score × high role ideal."""
    ideal = role_by_name(role)["profile"]
    ranked = sorted((a for a in skill_areas() if ex.scores[a] >= MIN_WHY_SCORE and ideal[a] >= RELEVANT_IDEAL),
                    key=lambda a: -(ex.scores[a] * ideal[a]))
    return [WhyItem(a, area_label(a), ex.scores[a], ideal[a],
                    [e.short() for e in ex.evidence_for(a)]) for a in ranked[:n]]


# ---------- gaps ----------
def gaps(role: str, ex: Extraction, year: int) -> list[Gap]:
    """Areas below the year-adjusted target for the role, biggest gap first."""
    expect = app_config()["year_expectation"][year]
    ideal = role_by_name(role)["profile"]
    out = []
    for a in skill_areas():
        if ideal[a] < RELEVANT_IDEAL:
            continue
        target = round(ideal[a] * expect, 1)
        g = round(target - ex.scores[a], 1)
        if g >= MIN_GAP:
            out.append(Gap(a, area_label(a), ex.scores[a], target, ideal[a], g))
    return sorted(out, key=lambda g: -g.gap)


# ---------- next steps ----------
_STOP = {"certificate", "certified", "certification", "professional", "specialization", "course",
         "the", "of", "and", "for", "to", "in", "a", "an", "with", "on", "coursera", "udemy",
         "nptel", "introduction", "intro", "basics", "fundamentals", "your", "own", "using", "my"}


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+#]+", text.lower()) if t not in _STOP}


def already_done(suggestion: str, done_texts: list[str]) -> bool:
    """True if a suggested certificate/project looks like one the student already has.

    Matches when one word set contains the other, or they share at least 3 words
    covering half of the suggestion's words.
    """
    s = _tokens(suggestion)
    if not s:
        return False
    for text in done_texts:
        t = _tokens(text)
        if len(t) < 2:
            continue
        shared = len(s & t)
        if t <= s or s <= t or (shared >= 3 and shared / len(s) >= 0.5):
            return True
    return False


LEVEL_NOTE = {("beginner", "beginner"): "beginner-friendly",
              ("advanced", "advanced"): "portfolio / interview level",
              ("beginner", "advanced"): "stretch goal",
              ("advanced", "beginner"): "quick foundation to fill in"}


def _pool(role: str, kind: str, key: str) -> list[dict]:
    """The role's own suggestions, then other roles' suggestions in areas this role relies on.

    The top-up keeps 2-3 suggestions available for students who have already done
    most of a role's own list.
    """
    ideal = role_by_name(role)["profile"]
    own = [{**i, "own": True} for i in role_by_name(role)[kind]]
    seen = {i[key] for i in own}
    extra = []
    for r in roles():
        for i in r[kind]:
            if r["name"] != role and i[key] not in seen and ideal[i["area"]] >= RELEVANT_IDEAL:
                seen.add(i[key])
                extra.append({**i, "own": False})
    return own + extra


def _pick(items: list[dict], key: str, level: str, gap_rank: dict[str, int],
          done: list[str], n: int, ideal: dict[str, float]) -> list[Step]:
    """Choose up to n suggestions the student hasn't done yet.

    Tiers: (0) role's own item at the right level; (1) another role's item at the
    right level that closes the biggest gap; (2) role's own item at the other level;
    (3) anything else. Within a tier: biggest gap first, then the area the role
    needs most. At most one top-up item (from another role) per area.
    """
    top_gap = min(gap_rank, key=gap_rank.get) if gap_rank else None

    def tier(i):
        right, own = i["level"] == level, i.get("own", True)
        if own and right:
            return 0
        if right and i["area"] == top_gap:
            return 1
        return 2 if own else 3

    fresh = [i for i in items if not already_done(i[key], done)]
    ranked = sorted(fresh, key=lambda i: (tier(i), gap_rank.get(i["area"], 99),
                                          -ideal.get(i["area"], 0)))
    chosen, topup_areas = [], set()
    for i in ranked:
        if not i.get("own", True):
            if i["area"] in topup_areas:
                continue
            topup_areas.add(i["area"])
        chosen.append(i)
        if len(chosen) == n:
            break

    steps = []
    for i in chosen:
        if i["area"] in gap_rank:
            reason = f"Closes your {area_label(i['area'])} gap"
        else:
            reason = f"Strengthens {area_label(i['area'])}"
        reason += f" · {LEVEL_NOTE[(level, i['level'])]}"
        steps.append(Step(i[key], i["area"], i["level"], reason))
    return steps


def next_steps(role: str, student: Student, role_gaps: list[Gap]) -> NextSteps:
    cfg = app_config()
    r = role_by_name(role)
    stage = cfg["year_stage"][student.year_of_study]
    guide = cfg["stage_guidance"][stage]
    level = "beginner" if stage == "explore" else "advanced"
    gap_rank = {g.area: i for i, g in enumerate(role_gaps)}

    certs = _pick(_pool(role, "certificates", "name"), "name", level, gap_rank,
                  [c.title for c in student.certificates], N_CERTS, r["profile"])
    projects = _pick(_pool(role, "projects", "title"), "title", level, gap_rank,
                     [f"{p.title} {p.description}" for p in student.projects], N_PROJECTS, r["profile"])

    attended = {e.event_type for e in student.events}
    events = sorted(r["events"], key=lambda e: e["type"] in attended)[:N_EVENTS]
    event_steps = [Step(e["type"], "", "",
                        e["why"] + (" (you've been to one — go for a higher placing)"
                                    if e["type"] in attended else ""))
                   for e in events]
    return NextSteps(stage, guide["title"], list(guide["tips"]), certs, projects, event_steps)


# ---------- bundle ----------
def explain_role(role: str, student: Student, ex: Extraction) -> RoleExplanation:
    g = gaps(role, ex, student.year_of_study)
    return RoleExplanation(role, why(role, ex), g, next_steps(role, student, g))


def recommend(student: Student) -> tuple[Prediction, list[RoleExplanation]]:
    """Predict the top-3 roles and explain each one."""
    pred = predict(student)
    return pred, [explain_role(r.role, student, pred.extraction) for r in pred.top]
