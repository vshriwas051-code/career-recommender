from datetime import date

import pytest

from career.models import Certificate, Event, Project, Student


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def full_student():
    """A fictional, fully filled profile."""
    return Student(
        srn="TEST22CS001", name="Asha Rao", college="Demo Institute of Technology",
        branch="CSE", class_section="5A", year_of_study=3, cgpa=8.4,
        interests=["Working with data", "Cloud & infrastructure"],
        skills={"python": 4, "sql": 3, "aws": 2},
        certificates=[
            Certificate("AWS Cloud Practitioner", "Amazon", "AWS", "CLOUD_DEVOPS",
                        date(2025, 6, 1), "https://example.com/cred/1"),
            Certificate("Machine Learning", "Stanford", "Coursera", "ML_AI", date(2025, 1, 10)),
        ],
        projects=[
            Project("Sales Dashboard", "Power BI sales analysis", ["python", "pandas", "power bi"],
                    "Team Lead", "Academic", "https://github.com/example/sales"),
        ],
        events=[
            Event("Smart India Hackathon", "Hackathon", "ML_AI", date(2024, 12, 5), "Finalist"),
            Event("Cloud Workshop", "Workshop", "CLOUD_DEVOPS", date(2025, 3, 2), "Attended"),
        ],
    )
