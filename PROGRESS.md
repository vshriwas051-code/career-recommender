# Progress

| Phase | Status | Notes |
|---|---|---|
| 0 Setup | ✅ Done | Skeleton, requirements, navy theme, CLAUDE.md, .gitignore, smoke tests |
| 1 Profile & storage | ✅ Done | models/db/validate; Profile page (basic details, skills, interests, certificate/project/event lists) with inline validation; History page (open/delete by SRN); 36 tests |
| 2 Skill extraction | ✅ Done | skills.yaml keywords + scoring weights, roles.yaml (11 roles), skills.py (evidence trail), features.py (20 features); certificate-domain auto-suggest; Profile page shows area scores + evidence; 64 tests |
| 3 Model | ✅ Done | synth.py (3,000 synthetic students, seed 42), train.py (RF vs LR, CV selection → LogisticRegression); test accuracy 0.885, **top-3 0.982**, macro F1 0.885; reports/model_evaluation.md + confusion_matrix.png; 75 tests |
| 4 Prediction & advice | ✅ Done | predict.py (top-3, cosine match, softened/capped confidence ≤ 90 %), explain.py (why / year-adjusted gaps / next steps), 3 fictional demo profiles all predict their expected role, prediction history logged, basic Results page (match-first cards); 101 tests |
| 5 Results UI & PDF | ✅ Done | Results page (match-first cards, level chips, radar, why, gap chart, next-steps checklist, history), PDF download `<SRN>_career_report.pdf`, About page, `st.navigation` (pages/ → views/); level labels Beginner/Intermediate/Strong everywhere; 116 tests |
| 6 Polish & submit | ✅ Done | Demo loader (Profile + one-click on Home), README with screenshots, docs/architecture.md, outline-only transparent diagrams (light/dark · SVG/PNG), CLAUDE.md + master-prompt layout → views/; **fresh clone from GitHub verified** (README steps, Python 3.14: install, 123 tests, app + demo flow); 123 tests |

**All phases complete.**

## Run
```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
pytest

# retrain the model (deterministic, ~30 s)
PYTHONPATH=src python -m career.train
```
