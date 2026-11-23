"""PDF report and level labels."""
import pytest

from career.demo import list_demos, load_demo
from career.explain import recommend
from career.models import Student
from career.report import build_pdf, report_filename, save_pdf
from career.skills import area_level


@pytest.mark.parametrize("score, level", [(0, "Beginner"), (29.9, "Beginner"), (30, "Intermediate"),
                                          (45, "Intermediate"), (60, "Intermediate"), (60.1, "Strong"),
                                          (100, "Strong")])
def test_area_level_boundaries(score, level):
    assert area_level(score) == level


@pytest.mark.parametrize("demo", list_demos(), ids=lambda d: d.key)
def test_pdf_report_is_created(demo, tmp_path):
    pred, exps = recommend(demo.student)
    path = save_pdf(pred, exps, tmp_path)
    assert path.name == f"{demo.student.srn}_career_report.pdf"
    data = path.read_bytes()
    assert data.startswith(b"%PDF") and len(data) > 20_000


def test_pdf_for_empty_profile(tmp_path):
    """No evidence, no gaps covered — the report must still build."""
    s = Student(srn="EMPTY0001", name="Émilie Ñúñez — test", year_of_study=1)
    pred, exps = recommend(s)
    assert build_pdf(pred, exps).startswith(b"%PDF")


def test_report_filename():
    assert report_filename("PES1UG22CS101") == "PES1UG22CS101_career_report.pdf"


def test_charts_build():
    from career.charts import area_bar_figure, gap_figure, radar_figure
    from career.config import role_by_name
    demo = load_demo("web_2nd_year")
    pred, exps = recommend(demo.student)
    ideal = role_by_name(exps[0].role)["profile"]
    assert len(radar_figure(pred.extraction.scores, exps[0].role, ideal, ideal, 2).data) == 3
    assert len(gap_figure(exps[0].gaps, 2).data) == 2
    bar = area_bar_figure(pred.extraction.scores)
    assert any("Strong" in t for t in bar.data[0].text)
