import numpy as np

from career.config import app_config, skill_areas
from career.features import CGPA_DEFAULT, feature_names, student_features
from career.skills import extract


def test_feature_names_order():
    names = feature_names()
    n_int = len(app_config()["interests"])
    assert len(names) == 10 + 2 + n_int
    assert names[:10] == [f"area_{a}" for a in skill_areas()]
    assert names[10:12] == ["year_of_study", "cgpa"]
    assert names[12] == "interest_building_apps"
    assert len(set(names)) == len(names)


def test_vector_shape_and_values(full_student):
    v = student_features(full_student)
    names = feature_names()
    assert v.shape == (len(names),) and v.dtype == np.float64
    ex = extract(full_student)
    for i, a in enumerate(skill_areas()):
        assert v[i] == ex.scores[a]
    assert v[names.index("year_of_study")] == 3
    assert v[names.index("cgpa")] == 8.4
    assert v[names.index("interest_working_with_data")] == 1
    assert v[names.index("interest_cloud_infrastructure")] == 1
    assert v[names.index("interest_design")] == 0


def test_missing_cgpa_imputed(full_student):
    full_student.cgpa = None
    v = student_features(full_student)
    assert v[feature_names().index("cgpa")] == CGPA_DEFAULT
