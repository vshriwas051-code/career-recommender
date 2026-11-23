# Decisions log

| # | Phase | Decision | Why |
|---|---|---|---|
| 1 | 0 | Created `.venv` with Python 3.12 (Homebrew) inside the repo | No venv existed in the repo; 3.12 has stable wheels for every dependency |
| 2 | 0 | Copied `CAREER_MASTER_PROMPT.md` into the repo root | `CLAUDE.md` points at it, so it must live in the repo |
| 3 | 0 | Classic Streamlit multipage layout (`app.py` + `pages/`) | Matches the layout in the master prompt; zero extra routing code |
| 4 | 0 | `src/` layout; pages add `src/` to `sys.path`, pytest uses `pythonpath = ["src"]` | `streamlit run app.py` works on a fresh clone with no `pip install -e .` |
| 5 | 0 | Theme uses `base = "dark"` plus the navy colours and `font = "sans serif"` | Dark base keeps widgets/charts readable on navy |
| 6 | 1 | `config/skills.yaml` started in Phase 1 with the skill → area taxonomy only | The Profile page's skill picker needs it; keyword mappings come in Phase 2 |
| 7 | 1 | Certificate domain is a manual dropdown for now; auto-suggest from title arrives in Phase 2 | Auto-suggest needs the keyword → area mapping from skills.yaml |
| 8 | 1 | Saving a profile replaces its certificate/project/event rows (delete + re-insert) | Simplest correct way to sync an edited list; row IDs may change, nothing references them |
| 9 | 1 | Student row saved with `INSERT … ON CONFLICT DO UPDATE`, never `INSERT OR REPLACE` | REPLACE deletes the row, and the cascade would wipe prediction history |
| 10 | 1 | `predictions` table + helpers created now (used in Phase 4) | Schema lives in one place; cascade-delete is tested from day one |
| 11 | 1 | SRN is normalised (trim + uppercase) before validation; locked while editing | SRN is the primary key; changing it means a new profile |
| 12 | 1 | Name and college are required, besides SRN | A report without them makes no sense |
| 13 | 1 | Lists use `st.data_editor` (dynamic rows); tech stack uses `MultiselectColumn(accept_new_options=True)` | Gives "multi-select plus free text" with no custom widgets |
| 14 | 1 | Inline errors: on submit, errors are stored in session state and the page reruns to show them under each field | Streamlit forms render fields before the submit result is known |
| 15 | 1 | `CAREER_DB_PATH` env var overrides the DB path | Lets UI tests run against a temporary database |
| 16 | 1 | "Load demo profile" button deferred to Phase 6 (with `demo/`) | The phase table schedules the demo loader there |
