"""Train, compare, evaluate and save the career-role model.

Run from the repo root:
    PYTHONPATH=src python -m career.train

Steps
1. Generate the synthetic dataset (synth.py, fixed seed).
2. Stratified 80/20 train/test split.
3. Compare RandomForest vs LogisticRegression with 5-fold CV (top-1 accuracy) on the
   training set only, so the test set is never used for model selection.
4. Refit the winner on the full training set; evaluate on the test set
   (accuracy, top-3 accuracy, macro F1, confusion matrix).
5. Save models/career_model.joblib, models/metadata.json,
   reports/model_evaluation.md and reports/confusion_matrix.png.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, f1_score,
                             top_k_accuracy_score)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import ROOT
from .features import feature_names
from .synth import N_SAMPLES, SEED, generate

MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
MODEL_PATH = MODEL_DIR / "career_model.joblib"
METADATA_PATH = MODEL_DIR / "metadata.json"
TEST_SIZE = 0.2


def candidates(seed: int = SEED) -> dict[str, Any]:
    return {
        "RandomForestClassifier": RandomForestClassifier(
            n_estimators=200, min_samples_leaf=2, random_state=seed, n_jobs=-1),
        "LogisticRegression": make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000, C=1.0, random_state=seed)),
    }


def split(df, seed: int = SEED):
    X = df[feature_names()].to_numpy()
    y = df["role"].to_numpy()
    return train_test_split(X, y, test_size=TEST_SIZE, stratify=y, random_state=seed)


def evaluate(model, X_test, y_test) -> dict[str, float]:
    proba = model.predict_proba(X_test)
    pred = model.classes_[proba.argmax(axis=1)]
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "top3_accuracy": round(float(top_k_accuracy_score(y_test, proba, k=3,
                                                          labels=model.classes_)), 4),
        "macro_f1": round(float(f1_score(y_test, pred, average="macro")), 4),
    }


def train(n: int = N_SAMPLES, seed: int = SEED, save: bool = True) -> dict[str, Any]:
    df = generate(n, seed)
    X_train, X_test, y_train, y_test = split(df, seed)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)

    comparison: dict[str, dict[str, float]] = {}
    fitted: dict[str, Any] = {}
    for name, est in candidates(seed).items():
        cv_acc = cross_val_score(clone(est), X_train, y_train, cv=cv, scoring="accuracy")
        model = clone(est).fit(X_train, y_train)
        fitted[name] = model
        comparison[name] = {"cv_accuracy": round(float(cv_acc.mean()), 4),
                            "cv_accuracy_std": round(float(cv_acc.std()), 4),
                            **evaluate(model, X_test, y_test)}

    best = max(comparison, key=lambda k: comparison[k]["cv_accuracy"])
    model = fitted[best]
    pred = model.predict(X_test)
    labels = list(model.classes_)
    cm = confusion_matrix(y_test, pred, labels=labels)

    metadata = {
        "model_type": best,
        "model_version": f"{best}-seed{seed}-{date.today().isoformat()}",
        "seed": seed,
        "training_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "total_rows": int(len(df)),
        "test_size": TEST_SIZE,
        "feature_names": feature_names(),
        "classes": labels,
        "metrics": comparison[best],
        "comparison": comparison,
        "selection": "highest 5-fold CV accuracy on the training set",
        "trained_on": date.today().isoformat(),
        "sklearn_version": sklearn.__version__,
        "data": "synthetic (career.synth) — no real student data",
    }
    if save:
        MODEL_DIR.mkdir(exist_ok=True)
        REPORT_DIR.mkdir(exist_ok=True)
        joblib.dump(model, MODEL_PATH, compress=3)
        METADATA_PATH.write_text(json.dumps(metadata, indent=2))
        _plot_confusion(cm, labels, REPORT_DIR / "confusion_matrix.png")
        report = classification_report(y_test, pred, labels=labels, digits=3)
        (REPORT_DIR / "model_evaluation.md").write_text(_markdown(metadata, report, cm, labels))
    return {"model": model, "metadata": metadata, "confusion_matrix": cm}


def load_model(path: Path = MODEL_PATH):
    """Return (model, metadata). Raises FileNotFoundError if the model hasn't been trained."""
    if not path.exists():
        raise FileNotFoundError(f"No trained model at {path}. Run: PYTHONPATH=src python -m career.train")
    return joblib.load(path), json.loads(METADATA_PATH.read_text())


# ---------- report helpers ----------
def _plot_confusion(cm: np.ndarray, labels: list[str], path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from matplotlib.colors import LinearSegmentedColormap

    ink, blue = "#1E1C1A", "#2F4BC9"     # app tokens (src/career/ui.py)
    fig, ax = plt.subplots(figsize=(10, 8.5), facecolor="#FFFFFF")
    ax.set_facecolor("#FFFFFF")
    norm = cm / cm.sum(axis=1, keepdims=True)
    im = ax.imshow(norm, cmap=LinearSegmentedColormap.from_list("cream_blue", ["#FFFFFF", "#EFEADD", blue]),
                   vmin=0, vmax=1)
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", color=ink, fontsize=9)
    ax.set_yticks(range(len(labels)), labels, color=ink, fontsize=9)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, cm[i, j], ha="center", va="center", fontsize=8,
                        color="#FFFFFF" if norm[i, j] > 0.5 else ink)
    ax.set_xlabel("Predicted role", color=ink)
    ax.set_ylabel("True role", color=ink)
    ax.set_title("Confusion matrix — synthetic test set (row-normalised colour, counts shown)",
                 color=ink, fontsize=11)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.yaxis.set_tick_params(color=ink, labelcolor=ink)
    fig.tight_layout()
    fig.savefig(path, dpi=130, facecolor=fig.get_facecolor())
    plt.close(fig)


def _markdown(meta: dict, report: str, cm: np.ndarray, labels: list[str]) -> str:
    m = meta["metrics"]
    rows = "\n".join(
        f"| {name}{' ✅' if name == meta['model_type'] else ''} | {c['cv_accuracy']:.3f} ± {c['cv_accuracy_std']:.3f} "
        f"| {c['accuracy']:.3f} | {c['top3_accuracy']:.3f} | {c['macro_f1']:.3f} |"
        for name, c in meta["comparison"].items())
    worst = sorted(((cm[i, j], labels[i], labels[j]) for i in range(len(labels))
                    for j in range(len(labels)) if i != j), reverse=True)[:5]
    confusions = "\n".join(f"- **{t}** predicted as **{p}**: {n} times" for n, t, p in worst if n)
    return f"""# Model evaluation

> **The training data is synthetic.** No real student data was available, and using real
> students' records would raise privacy concerns. Instead, `src/career/synth.py` generates
> {meta['total_rows']:,} fictional students around each role's ideal skill profile in
> `config/roles.yaml`, with noise (fixed seed {meta['seed']}). These numbers show the model
> learns the role profiles well. They are **not** a measure of real-world accuracy.

## Selected model: {meta['model_type']}

| Metric (test set, {meta['test_rows']} rows) | Value |
|---|---|
| Accuracy (top-1) | **{m['accuracy']:.3f}** |
| Top-3 accuracy | **{m['top3_accuracy']:.3f}** |
| Macro F1 | **{m['macro_f1']:.3f}** |

## Model comparison

Selected by 5-fold cross-validation on the training set ({meta['training_rows']} rows); the test
set is held out and only used for the final numbers.

| Model | CV accuracy | Test accuracy | Test top-3 | Test macro F1 |
|---|---|---|---|---|
{rows}

## Setup

- Features ({len(meta['feature_names'])}): 10 skill-area scores (0–100), year of study, CGPA
  (missing → 7.0), and {len(meta['feature_names']) - 12} interest flags.
- Split: {int((1 - meta['test_size']) * 100)}/{int(meta['test_size'] * 100)} stratified, seed {meta['seed']}.
- Trained {meta['trained_on']} with scikit-learn {meta['sklearn_version']}.

## Confusion matrix

![Confusion matrix](confusion_matrix.png)

Most common mix-ups — these are roles with genuinely overlapping skill profiles, which is
why the app shows the **top 3** roles instead of a single answer:

{confusions}

## Per-role report

```
{report}
```

Regenerate with: `PYTHONPATH=src python -m career.train`
"""


if __name__ == "__main__":
    result = train()
    meta = result["metadata"]
    print(f"Selected {meta['model_type']}: {meta['metrics']}")
    for name, c in meta["comparison"].items():
        print(f"  {name}: {c}")
