import pandas as pd

from career.config import role_names
from career.features import feature_names
from career.synth import generate


def test_reproducible_with_same_seed():
    pd.testing.assert_frame_equal(generate(500, seed=42), generate(500, seed=42))


def test_different_seed_differs():
    assert not generate(200, seed=1).equals(generate(200, seed=2))


def test_shape_columns_and_balance():
    df = generate()
    assert len(df) == 3000
    assert list(df.columns) == [*feature_names(), "role"]
    counts = df["role"].value_counts()
    assert set(counts.index) == set(role_names())
    assert counts.max() - counts.min() <= 1


def test_value_ranges():
    df = generate(1000)
    areas = [c for c in df.columns if c.startswith("area_")]
    assert df[areas].min().min() >= 0 and df[areas].max().max() <= 100
    assert df["year_of_study"].between(1, 4).all()
    assert df["cgpa"].between(0, 10).all()
    interests = [c for c in df.columns if c.startswith("interest_")]
    assert set(pd.unique(df[interests].to_numpy().ravel())) <= {0.0, 1.0}


def test_role_profile_shape_is_preserved():
    """Each role's strongest synthetic area matches its ideal profile's strongest area."""
    from career.config import roles
    df = generate()
    areas = [c for c in df.columns if c.startswith("area_")]
    means = df.groupby("role")[areas].mean()
    for r in roles():
        top_ideal = max(r["profile"], key=r["profile"].get)
        assert means.loc[r["name"]].idxmax() == f"area_{top_ideal}", r["name"]
