import numpy as np
import pytest

from career import db
from career.config import app_config, role_names, roles, skill_areas
from career.demo import list_demos
from career.models import Student
from career.predict import match_scores, predict, save_prediction, soften

DEMOS = list_demos()


def test_three_fictional_demo_profiles():
    assert len(DEMOS) == 3
    assert {d.student.year_of_study for d in DEMOS} == {2, 3, 4}
    assert all("(demo)" in d.student.name and d.student.srn.startswith("DEMO") for d in DEMOS)


@pytest.mark.parametrize("demo", DEMOS, ids=[d.key for d in DEMOS])
def test_demo_top1_is_expected(demo):
    assert predict(demo.student).top[0].role == demo.expected_role


@pytest.mark.parametrize("demo", DEMOS, ids=[d.key for d in DEMOS])
def test_confidence_softened_and_capped(demo):
    cap = app_config()["confidence_cap"]
    top = predict(demo.student).top
    assert len(top) == 3 and len({r.role for r in top}) == 3
    assert all(r.confidence <= cap for r in top)            # never shows 100 %
    assert top[0].raw_probability > 0.99                    # the raw model really is that sharp...
    assert top[0].confidence < top[0].raw_probability       # ...so softening is doing its job
    assert [r.raw_probability for r in top] == sorted([r.raw_probability for r in top], reverse=True)
    assert top[0].confidence_label == "High"
    assert all(0 <= r.match <= 100 for r in top)


def test_soften_keeps_order_and_caps():
    p = np.array([0.999, 0.0009, 0.0001])
    s = soften(p, temperature=4.0, cap=0.9)
    assert list(np.argsort(s)) == list(np.argsort(p))
    assert s.max() <= 0.9 and s[1] > p[1]
    assert np.allclose(soften(np.array([0.5, 0.3, 0.2]), 1.0, 1.0), [0.5, 0.3, 0.2])


def test_match_score_is_cosine():
    for r in roles():
        assert match_scores(r["profile"])[r["name"]] == pytest.approx(100.0)
    half = {a: v / 2 for a, v in roles()[0]["profile"].items()}   # scale-invariant
    assert match_scores(half)[roles()[0]["name"]] == pytest.approx(100.0)
    assert set(match_scores({a: 0 for a in skill_areas()}).values()) == {0.0}
    assert set(match_scores({})) == set(role_names())


def test_empty_profile_does_not_crash():
    pred = predict(Student(srn="EMPTY0001", name="Empty", year_of_study=1))
    assert len(pred.top) == 3 and all(r.match == 0 for r in pred.top)


def test_prediction_history_is_appended(db_path):
    student = DEMOS[0].student
    db.save_student(student, db_path=db_path)
    pred = predict(student)
    save_prediction(pred, db_path=db_path)
    save_prediction(pred, db_path=db_path)
    hist = db.list_predictions(student.srn, db_path=db_path)
    assert len(hist) == 2
    assert hist[0]["top_roles"][0]["role"] == pred.top[0].role
    assert set(hist[0]["top_roles"][0]) == {"role", "match", "confidence", "raw_probability"}
    assert hist[0]["model_version"] == pred.model_version != ""


def test_format_confidence_never_shows_zero():
    from career.predict import format_confidence
    assert format_confidence(0.0) == "<1%" and format_confidence(0.004) == "<1%"
    assert format_confidence(0.081) == "8%" and format_confidence(0.9) == "90%"
