# CLAUDE.md

Always follow CAREER_MASTER_PROMPT.md. Status is in PROGRESS.md. Decisions are in docs/decisions.md.

- Page scripts live in `views/` and are registered with `st.navigation` in `app.py`.
  Do **not** create a `pages/` folder — Streamlit would auto-discover it and direct links
  (e.g. `/Results`) would bypass the navigation (decision #55).
- Run: `streamlit run app.py` · Test: `pytest` · Retrain: `PYTHONPATH=src python -m career.train`
