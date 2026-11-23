"""Tests run against the committed model in models/ (retrain: PYTHONPATH=src python -m career.train)."""
import numpy as np
import pytest

from career.config import ROOT, role_names
from career.features import feature_names
from career.synth import generate
from career.train import evaluate, load_model, split


@pytest.fixture(scope="module")
def artifacts():
    return load_model()


def test_metadata_complete(artifacts):
    _, meta = artifacts
    for key in ["model_type", "seed", "training_rows", "feature_names", "metrics", "trained_on"]:
        assert key in meta
    assert meta["model_type"] in ("RandomForestClassifier", "LogisticRegression")
    assert meta["feature_names"] == feature_names()
    assert set(meta["classes"]) == set(role_names())
    assert meta["training_rows"] == 2400 and meta["test_rows"] == 600
    assert set(meta["comparison"]) == {"RandomForestClassifier", "LogisticRegression"}


def test_top3_accuracy_at_least_085(artifacts):
    model, meta = artifacts
    _, X_test, _, y_test = split(generate(meta["total_rows"], meta["seed"]), meta["seed"])
    metrics = evaluate(model, X_test, y_test)
    assert metrics["top3_accuracy"] >= 0.85
    assert metrics == {k: meta["metrics"][k] for k in metrics}  # saved metrics are reproducible


def test_selected_model_is_the_better_one(artifacts):
    _, meta = artifacts
    best = max(meta["comparison"], key=lambda k: meta["comparison"][k]["cv_accuracy"])
    assert meta["model_type"] == best


def test_predict_proba_shape(artifacts):
    model, _ = artifacts
    p = model.predict_proba(np.zeros((1, len(feature_names()))))
    assert p.shape == (1, len(role_names())) and np.isclose(p.sum(), 1)


def test_reports_exist():
    md = (ROOT / "reports/model_evaluation.md").read_text()
    assert "synthetic" in md.lower() and "Top-3 accuracy" in md
    assert (ROOT / "reports/confusion_matrix.png").stat().st_size > 10_000


def test_train_function_small_run():
    """train() works end to end without overwriting the committed artifacts."""
    from career import train as t
    result = t.train(n=550, seed=7, save=False)
    assert result["metadata"]["metrics"]["top3_accuracy"] >= 0.85
    assert result["confusion_matrix"].shape == (11, 11)
