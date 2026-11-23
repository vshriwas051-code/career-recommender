import pytest

from career.config import app_config, load_yaml, role_names, roles, skill_areas
from career.models import Certificate, Event, Project, Student
from career.skills import extract, match_skills, skill_area, suggest_domain


@pytest.mark.parametrize("text, area", [
    ("AWS Cloud Practitioner", "CLOUD_DEVOPS"),
    ("React", "WEB"),
    ("Built a to-do app with Node.js and Express", "WEB"),
    ("React Native expense tracker", "MOBILE"),
    ("Flutter weather app", "MOBILE"),
    ("SQL and Power BI dashboard", "DATA_ANALYSIS"),
    ("Machine Learning Specialization", "ML_AI"),
    ("Image classification with PyTorch", "ML_AI"),
    ("Docker and Kubernetes basics", "CLOUD_DEVOPS"),
    ("Google Cybersecurity Certificate", "SECURITY"),
    ("CTF competition", "SECURITY"),
    ("Figma prototype", "DESIGN_UX"),
    ("ESP32 sensor network", "EMBEDDED_IOT"),
    ("Agile product management", "BUSINESS_PRODUCT"),
    ("C++ data structures", "PROGRAMMING"),
])
def test_known_keywords_map_to_areas(text, area):
    assert area in {skill_area(s) for s in match_skills(text)}


def test_longest_keyword_wins_and_no_substring_matches():
    assert match_skills("React Native") == ["android"]        # MOBILE, not WEB "react"
    assert match_skills("HTML basics") == ["html/css"]          # "ml" inside html must not match
    assert match_skills("Smart India Hackathon") == []


def test_suggest_domain():
    assert suggest_domain("AWS Certified Cloud Practitioner") == "CLOUD_DEVOPS"
    assert suggest_domain("Google Data Analytics") == "DATA_ANALYSIS"
    assert suggest_domain("Certificate of Participation") is None


def test_extraction_weights_and_evidence():
    s = Student(
        srn="EVID00001", name="Test", year_of_study=2,
        skills={"react": 4},
        certificates=[Certificate("AWS Cloud Practitioner", "Amazon", "AWS")],
        projects=[
            Project("Portfolio", "Personal site", ["react"], "Solo", "Personal"),
            Project("Hack app", "React web app", [], "Team Member", "Hackathon"),
        ],
        events=[Event("CTF Night", "Competition", "SECURITY", None, "Winner"),
                Event("Web Workshop", "Workshop", "WEB", None, "Attended")],
    )
    ex = extract(s)
    texts = [e.text() for e in ex.evidence]
    assert "CLOUD_DEVOPS +2 from certificate 'AWS Cloud Practitioner'" in texts
    assert "WEB +3 from project 'Portfolio'" in texts
    assert "WEB +4 from project 'Hack app'" in texts                 # hackathon bonus
    assert "SECURITY +2 from event 'CTF Night'" in texts             # winner bonus
    assert "WEB +1 from event 'Web Workshop'" in texts
    assert "WEB +2 from self-rated skill 'react (4/5)'" in texts      # 4 x 0.5
    assert ex.raw["WEB"] == 3 + 4 + 1 + 2
    assert ex.raw["CLOUD_DEVOPS"] == 2 and ex.raw["SECURITY"] == 2
    # every point is accounted for by evidence
    for area, pts in ex.raw.items():
        assert pts == pytest.approx(sum(e.points for e in ex.evidence_for(area)))


def test_team_lead_bonus_and_one_award_per_area():
    p = Project("Analytics", "pandas, numpy and matplotlib analysis", ["python", "pandas"],
                "Team Lead", "Academic")
    ex = extract(Student(srn="EVID00002", name="T", projects=[p]))
    # pandas/numpy/matplotlib all DATA_ANALYSIS -> counted once; python -> PROGRAMMING
    assert ex.raw["DATA_ANALYSIS"] == 4 and ex.raw["PROGRAMMING"] == 4
    assert len(ex.evidence) == 2


def test_declared_domain_used_when_no_keyword_matches():
    ex = extract(Student(srn="EVID00003", name="T",
                         certificates=[Certificate("Certificate of Merit", domain="DESIGN_UX")]))
    assert ex.raw["DESIGN_UX"] == 2


def test_scores_normalised_0_100(full_student):
    ex = extract(full_student)
    assert set(ex.scores) == set(skill_areas())
    assert all(0 <= v <= 100 for v in ex.scores.values())
    big = Student(srn="EVID00004", name="T",
                  projects=[Project(f"React app {i}", tech_stack=["react"]) for i in range(10)])
    assert extract(big).scores["WEB"] == 100


def test_empty_profile_scores_zero():
    ex = extract(Student(srn="EVID00005", name="T"))
    assert all(v == 0 for v in ex.scores.values()) and ex.evidence == []


# ---------- config integrity ----------
def test_skills_yaml_consistent():
    cfg = load_yaml("skills.yaml")
    areas = set(cfg["areas"])
    assert len(areas) == 10
    assert set(cfg["skills"].values()) <= areas
    assert set(cfg["keywords"].values()) <= set(cfg["skills"])


def test_roles_yaml_consistent():
    app = app_config()
    assert len(roles()) == 11 and len(set(role_names())) == 11
    for r in roles():
        assert set(r["profile"]) == set(skill_areas()), r["name"]
        assert all(0 <= v <= 100 for v in r["profile"].values())
        assert set(r["interests"]) <= set(app["interests"])
        for item in r["certificates"] + r["projects"]:
            assert item["area"] in skill_areas() and item["level"] in ("beginner", "advanced")
        assert {"beginner", "advanced"} <= {c["level"] for c in r["certificates"]}
        assert {"beginner", "advanced"} <= {p["level"] for p in r["projects"]}
        assert {e["type"] for e in r["events"]} <= set(app["event_types"])
