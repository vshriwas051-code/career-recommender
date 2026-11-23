# Decisions log

| # | Phase | Decision | Why |
|---|---|---|---|
| 1 | 0 | Created `.venv` with Python 3.12 (Homebrew) inside the repo | No venv existed in the repo; 3.12 has stable wheels for every dependency |
| 2 | 0 | Copied `CAREER_MASTER_PROMPT.md` into the repo root | `CLAUDE.md` points at it, so it must live in the repo |
| 3 | 0 | Classic Streamlit multipage layout (`app.py` + `pages/`) | Matches the layout in the master prompt; zero extra routing code |
| 4 | 0 | `src/` layout; pages add `src/` to `sys.path`, pytest uses `pythonpath = ["src"]` | `streamlit run app.py` works on a fresh clone with no `pip install -e .` |
| 5 | 0 | Theme uses `base = "dark"` plus the navy colours and `font = "sans serif"` | Dark base keeps widgets/charts readable on navy |
