"""Synthetic training data, generated from the role profiles in config/roles.yaml.

No real student data was available (or appropriate to use), so each synthetic
student is drawn around one role's ideal skill-area profile, with noise that
mimics real profiles:

* **Strength** — students are only part-way to the ideal, more so in early years
  (year 1: 15-45 % of the ideal, year 4: 45-100 %). This matches the absolute
  0-100 scale produced by `skills.extract`, where a typical student's strongest
  area scores roughly 25-60.
* **Personal variation** — each area is scaled by its own factor around 1.0.
* **Measurement noise** — Gaussian noise on every area; small values clip to 0,
  giving the sparse vectors real profiles have.
* **Side interests** — some students dabble in one unrelated area.
* **Interests** — the role's typical interests are usually ticked, others sometimes.
* **CGPA** — independent of role; some students leave it blank (imputed as in features.py).

Everything uses a single seeded `numpy.random.Generator`, so the same seed
always gives the same dataset.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import app_config, roles, skill_areas
from .features import build_vector, feature_names

SEED = 42
N_SAMPLES = 3000

# (low, high) fraction of the ideal profile reached, by year of study
STRENGTH_BY_YEAR = {1: (0.15, 0.45), 2: (0.25, 0.60), 3: (0.35, 0.80), 4: (0.45, 1.00)}
PERSONAL_SD = 0.20        # per-area multiplicative variation
NOISE_SD = 7.0            # additive noise on the 0-100 scale
SIDE_INTEREST_P = 0.35    # chance of a bump in one random area
SIDE_INTEREST_RANGE = (8, 30)
ROLE_INTEREST_P = 0.75    # chance each of the role's interests is ticked
OTHER_INTEREST_P = 0.10   # chance any other interest is ticked
CGPA_MISSING_P = 0.10


def generate(n: int = N_SAMPLES, seed: int = SEED) -> pd.DataFrame:
    """Return a DataFrame with the model's feature columns plus a `role` label.

    Roles are balanced (n is split as evenly as possible across roles).
    """
    rng = np.random.default_rng(seed)
    areas = skill_areas()
    all_interests = app_config()["interests"]
    role_list = roles()
    labels = np.resize(np.arange(len(role_list)), n)
    rng.shuffle(labels)

    rows = []
    for label in labels:
        role = role_list[label]
        ideal = np.array([role["profile"][a] for a in areas], dtype=float)
        year = int(rng.integers(1, 5))
        lo, hi = STRENGTH_BY_YEAR[year]
        strength = rng.uniform(lo, hi)
        personal = rng.normal(1.0, PERSONAL_SD, size=len(areas)).clip(0.3, 1.7)
        scores = ideal * strength * personal + rng.normal(0, NOISE_SD, size=len(areas))
        if rng.random() < SIDE_INTEREST_P:
            scores[rng.integers(len(areas))] += rng.uniform(*SIDE_INTEREST_RANGE)
        scores = scores.clip(0, 100).round(1)

        interests = [i for i in all_interests
                     if rng.random() < (ROLE_INTEREST_P if i in role["interests"] else OTHER_INTEREST_P)]
        cgpa = None if rng.random() < CGPA_MISSING_P else round(float(np.clip(rng.normal(7.6, 0.9), 5.0, 10.0)), 2)

        vec = build_vector(dict(zip(areas, scores)), year, cgpa, interests)
        rows.append([*vec, role["name"]])

    df = pd.DataFrame(rows, columns=[*feature_names(), "role"])
    return df
