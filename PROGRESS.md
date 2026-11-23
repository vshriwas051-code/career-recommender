# Progress

| Phase | Status | Notes |
|---|---|---|
| 0 Setup | ✅ Done | Skeleton, requirements, navy theme, CLAUDE.md, .gitignore, smoke tests |
| 1 Profile & storage | ✅ Done | models/db/validate; Profile page (basic details, skills, interests, certificate/project/event lists) with inline validation; History page (open/delete by SRN); 36 tests |
| 2 Skill extraction | ✅ Done | skills.yaml keywords + scoring weights, roles.yaml (11 roles), skills.py (evidence trail), features.py (20 features); certificate-domain auto-suggest; Profile page shows area scores + evidence; 64 tests |
| 3 Model | ⏳ Next | synth.py, train.py, evaluation report, saved model |
| 4 Prediction & advice | — | |
| 5 Results UI & PDF | — | |
| 6 Polish & submit | — | |

## Run
```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
pytest
```
