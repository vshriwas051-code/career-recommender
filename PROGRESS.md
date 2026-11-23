# Progress

| Phase | Status | Notes |
|---|---|---|
| 0 Setup | ✅ Done | Skeleton, requirements, navy theme, CLAUDE.md, .gitignore, smoke tests |
| 1 Profile & storage | ✅ Done | models/db/validate; Profile page (basic details, skills, interests, certificate/project/event lists) with inline validation; History page (open/delete by SRN); 36 tests |
| 2 Skill extraction | ⏳ Next | Add keyword mappings to skills.yaml, roles.yaml, skills.py, features.py; certificate-domain auto-suggest |
| 3 Model | — | |
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
