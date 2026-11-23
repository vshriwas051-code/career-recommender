from dataclasses import replace

import pytest

from career.config import app_config, role_by_name
from career.demo import list_demos, load_demo
from career.explain import (MIN_WHY_SCORE, already_done, explain_role, gaps, next_steps,
                            recommend, why)
from career.models import Certificate, Project, Student
from career.skills import extract

DEMOS = list_demos()


@pytest.mark.parametrize("demo", DEMOS, ids=[d.key for d in DEMOS])
def test_demo_explanations_are_sensible(demo):
    pred, exps = recommend(demo.student)
    assert [e.role for e in exps] == [r.role for r in pred.top]
    top = exps[0]
    ideal = role_by_name(top.role)["profile"]
    strongest = max(ideal, key=ideal.get)
    assert top.why and top.why[0].area == strongest          # the role's core area leads the "why"
    assert all(w.score >= MIN_WHY_SCORE and w.evidence for w in top.why)
    ns = top.next_steps
    assert 2 <= len(ns.certificates) <= 3
    assert 1 <= len(ns.projects) <= 2
    assert 1 <= len(ns.events) <= 2
    assert ns.tips


def test_why_evidence_names_real_items():
    demo = load_demo("security_4th_year")
    w = why("Cybersecurity Analyst", extract(demo.student))
    assert any("CTF Night" in e or "CompTIA Security+" in e for e in w[0].evidence)


def test_gaps_ranked_and_year_adjusted():
    s = Student(srn="GAPS00001", name="T", year_of_study=1)
    ex = extract(s)
    g1 = gaps("Data Scientist", ex, 1)
    g4 = gaps("Data Scientist", ex, 4)
    assert [x.gap for x in g1] == sorted([x.gap for x in g1], reverse=True)
    assert g1[0].area == "ML_AI"                              # largest ideal -> largest gap from zero
    exp = app_config()["year_expectation"]
    assert g1[0].target == pytest.approx(85 * exp[1], abs=0.1)
    assert g4[0].target == pytest.approx(85 * exp[4], abs=0.1)
    assert all(x.ideal >= 25 for x in g1)                     # only areas the role relies on


def test_year_rule_levels():
    base = Student(srn="YEAR00001", name="T")
    for year, stage, level in [(1, "explore", "beginner"), (2, "explore", "beginner"),
                               (3, "internship-ready", "advanced"), (4, "internship-ready", "advanced")]:
        s = replace(base, year_of_study=year)
        e = explain_role("Cloud/DevOps Engineer", s, extract(s))
        assert e.next_steps.stage == stage
        assert e.next_steps.certificates[0].level == level
        assert e.next_steps.projects[0].level == level


def test_next_steps_skip_what_is_already_done():
    s = Student(srn="DONE00001", name="T", year_of_study=1,
                certificates=[Certificate("AWS Cloud Practitioner")],
                projects=[Project("Static site", "Host a static website on AWS S3 bucket")])
    ns = next_steps("Cloud/DevOps Engineer", s, gaps("Cloud/DevOps Engineer", extract(s), 1))
    titles = [c.title for c in ns.certificates + ns.projects]
    assert "AWS Certified Cloud Practitioner" not in titles
    assert "Host a static website on AWS S3" not in titles


def test_gap_areas_are_prioritised():
    s = Student(srn="PRIO00001", name="T", year_of_study=2, skills={"react": 5, "html/css": 5})
    ex = extract(s)
    g = gaps("Full-Stack Web Developer", ex, 2)
    ns = next_steps("Full-Stack Web Developer", s, g)
    assert ns.certificates[0].area == g[0].area or ns.certificates[0].reason.startswith("Closes")


@pytest.mark.parametrize("suggestion, done, expected", [
    ("AWS Certified Cloud Practitioner", ["AWS Cloud Practitioner"], True),
    ("Cisco CCNA", ["Cisco CCNA: Introduction to Networks"], True),
    ("CompTIA Security+", ["Google Cybersecurity Certificate"], False),
    ("Personal portfolio website", ["Portfolio"], False),               # single word: too weak
    ("Web vulnerability audit of a deliberately vulnerable app (DVWA/Juice Shop)",
     ["Web vulnerability audit of OWASP Juice Shop"], True),
])
def test_already_done(suggestion, done, expected):
    assert already_done(suggestion, done) is expected
