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
| 17 | 2 | Keywords map to **skills**, skills map to **areas**; each skill name (and each `/` part of 3+ chars) is a keyword automatically | One small taxonomy drives the picker, matching and explanations |
| 18 | 2 | Keyword matching is case-insensitive on word boundaries, longest keyword first, and matched text is consumed | "React Native" → MOBILE not WEB; "ml" never matches inside "html" |
| 19 | 2 | An item adds its points **once per area** it touches, however many keywords match | Stops a keyword-heavy description from inflating a score |
| 20 | 2 | A certificate's chosen domain / an event's theme is added to the keyword-matched areas | Users can steer scoring where titles are vague ("Certificate of Merit") |
| 21 | 2 | Project +1 bonus applies to team leads and **hackathon-type** projects | Projects have no result field, so "hackathon winner" can't be captured directly; event wins get their own bonus |
| 22 | 2 | Absolute normalisation: score = min(100, raw / 15 × 100) (`area_cap` in skills.yaml) | Keeps gaps meaningful (a beginner really is below the ideal) instead of every student's best area being 100 |
| 23 | 2 | Weights live in `skills.yaml → scoring` | Tunable without code changes |
| 24 | 2 | Feature order: 10 areas, year, CGPA, 8 interest flags (20 features); missing CGPA → 7.0 | Fixed, documented order; neutral imputation keeps CGPA optional |
| 25 | 2 | All 11 roles from the prompt are included (it says "about 10") | Each listed role is distinct and useful |
| 26 | 2 | Certificate domain auto-suggest happens on save when the domain is left blank | `st.data_editor` cells can't react live to typing |
| 27 | 2 | Area scores + evidence are shown on the Profile page for a saved profile | Meets the Phase 2 "done when" before the Results page exists |
| 28 | 3 | Synthetic students are generated **at the same 0–100 scale `extract()` produces** (strength 15–45 % of the ideal in year 1, up to 45–100 % in year 4) | A model trained on idealised 80–90 scores would misjudge real profiles, which score ~25–60 |
| 29 | 3 | Noise: per-area personal factor (sd 0.2), additive noise (sd 7), 35 % chance of a side-interest bump, interests ticked 75 % (role) / 10 % (other), 10 % missing CGPA | Gives overlapping, realistic classes; top-1 accuracy ~0.88 rather than a suspicious 1.0 |
| 30 | 3 | Roles balanced (272–273 each of 3,000) | No real-world prior on role frequency; balance keeps macro F1 meaningful |
| 31 | 3 | Model selection by 5-fold CV accuracy on the training set; the test set is only for final numbers | Picking on the test set would leak |
| 32 | 3 | **LogisticRegression** selected (CV 0.879 vs RandomForest 0.860); both are reported | The prompt says keep the better one; LR is also smaller (3 KB) and easier to explain |
| 33 | 3 | Trained model + metadata + reports are committed | A fresh clone runs without training; `PYTHONPATH=src python -m career.train` regenerates them identically |
| 34 | 3 | Model tests evaluate the **committed** model on the regenerated test split | Proves the saved artifact meets top-3 ≥ 0.85, not just a fresh retrain |
| 35 | 3 | Known for Phase 4: LR gives near-100 % confidence to clear-cut profiles | The cosine match score shown alongside keeps the result interpretable; revisit display if it looks odd |
| 36 | 4 | **Result cards lead with the skill match %** (cosine similarity × 100); model confidence is a smaller secondary line with a bar | User request: match is easy to explain, and it's believable |
| 37 | 4 | **Displayed confidence is softened** with temperature scaling (T = 4, p ∝ exp(log p / T)), then **capped at 90 %**; labelled High ≥ 60 %, Medium ≥ 25 %, else Low. Raw probability is kept in the prediction record | User request. Raw LR output is 99.8–99.99 % for real profiles, which score above most of the synthetic training range. Softening keeps the ranking and gives 81–90 % for clear cases. Settings in app.yaml |
| 38 | 4 | Roles are **ranked by the model**; match is shown, not used to re-rank | Keeps "the AI part" in charge; for all demos model order and match order agree |
| 39 | 4 | Gaps use a **year-adjusted target**: role ideal × 40 / 55 / 70 / 85 % for years 1–4; only areas the role relies on (ideal ≥ 25) and gaps ≥ 5 | A year-1 student shouldn't be measured against a professional's profile |
| 40 | 4 | "Why" = areas ranked by student score × role ideal; an area must score ≥ 20 to count as a reason | Stops weak areas (e.g. 10/100) being presented as strengths |
| 41 | 4 | Next steps: level from year stage (1–2 beginner/explore, 3–4 advanced/internship-ready). Tiers: own right-level → other role's right-level item that closes the biggest gap → own other-level → anything; max one top-up per area; skip items already done | Always gives 2–3 certs / 1–2 projects even when a student has done most of a role's list, without drifting off-role |
| 42 | 4 | "Already done" = word-set match (subset either way, or ≥ 3 shared words covering half the suggestion); projects compared on title + description | Simple and explainable; leans towards skipping a borderline match rather than repeating what the student has done |
| 43 | 4 | Added `sql injection` and `xss` → web security keywords | "SQL injection" was wrongly scoring DATA_ANALYSIS via `sql` |
| 44 | 4 | AWS Cloud Practitioner marked beginner in the Full-Stack role | It is an entry-level certificate |
| 45 | 4 | Demo profiles created now (`demo/*.json`, loader in `src/career/demo.py`); the "Load demo profile" button stays in Phase 6 | Phase 4's "done when" needs them; a loader in `src/` is importable by pages and tests |
| 46 | 4 | A prediction is logged to history each time the Results page shows a **new version** of a profile (once per session per profile hash) | Append-only history without duplicate rows on every rerun |
| 47 | 4 | Basic Results page built now (cards, why, gaps table, next-steps checklist, history); charts, radar, animations and PDF in Phase 5 | Lets Phase 4 be checked in the app |
| 48 | 5 | **Level labels** next to every area score: Beginner < 30, Intermediate 30–60, Strong > 60 (`skill_levels` in app.yaml). Shown on Profile (bar colours + text), Results (overview chips, why, gap chart), PDF | User request: low numbers shouldn't read as failures. Chip colours are slate/blue/green, deliberately no red |
| 49 | 5 | Radar per role tab shows **You vs role ideal vs year-N target** | The target line explains where the gap numbers come from |
| 50 | 5 | Gap chart = You (bar) over the year target (outline), biggest gap at the top | Matches the gap rule; readable without a legend lookup |
| 51 | 5 | Confidence under 0.5 % shows as "<1%", never "0%" | "0%" looks like a bug |
| 52 | 5 | PDF uses fpdf2 + matplotlib charts + the **DejaVu Sans font bundled with matplotlib** | Core PDF fonts can't print "—", "·" or accents; no extra dependency or download |
| 53 | 5 | PDF: page 1 summary/top-3/areas+radar, page 2 top-role why/gaps/next-steps checklist, page 3 other two roles + method note | Same content as the Results page, laid out for print (white background) |
| 54 | 5 | PDF bytes cached per session per profile version | `st.download_button` needs the bytes up front; avoids rebuilding on every rerun |
| 55 | 5 | **`app.py` uses `st.navigation`**, and the page folder is renamed **`pages/` → `views/`** | Classic multipage labelled the home page "app". With `st.navigation` plus a folder named `pages/`, direct links (e.g. /Results) bypassed the new navigation. Renaming fixes both; `streamlit run app.py` is unchanged |
| 56 | 5 | About page: synthetic-data warning first, pipeline diagram (Graphviz DOT, rendered in the browser), weights, live metrics from metadata.json, confusion matrix, how to read the cards, limitations | Matches section 2.5 / 5 of the prompt |
| 57 | 5 | Animations kept light: page fade-in, staggered role-card fade-in, confidence bar grows, card hover lift | "Don't overdo it" |
| 58 | 6 | "Load demo profile" **saves the fictional demo to the database** (refreshing it if present) and opens it in edit mode; Home has a one-click "See demo results" | Lets the app be shown with zero typing; demos are fictional, and the database is git-ignored |
| 59 | 6 | Architecture diagram generated by `docs/make_architecture.py` (matplotlib): **outline-only boxes and open arrowheads, no fills, transparent background, text converted to outlines**; two inks (dark for light slides, white for dark slides), SVG + PNG | User request: reusable on slides. Regenerable; renders the same everywhere |
| 60 | 6 | README shows the diagram with `<picture>` (dark-mode source) | Legible in GitHub light and dark themes |
| 61 | 6 | Domain / Theme dropdowns show area names ("Cloud & DevOps") while storing codes | Readability; stored values unchanged |
| 62 | 6 | Docs tests: README sections/links/images, diagram transparency + no fills, requirements cover all imports | Keeps "a fresh clone runs with only the README steps" true as the code changes |
| 63 | 6 | Fresh-clone check run with the system `python3` (3.14), not the dev 3.12 venv | Tests the README as a new user would follow it |
| 64 | 7 | Phase 7 prompt saved as `docs/PHASE7_UI_REDESIGN.md`; no reference screenshot arrived with the request, so the design follows the prompt's written description only | Nothing copied from any other product; all artwork original or CC0 |
| 65 | 7 | **Manrope variable font** downloaded once from the official `google/fonts` repo, converted to `.woff2` (54 KB), served from `static/fonts/` with `OFL.txt`; `font = "Manrope, system-ui, sans-serif"` | Offline-safe, licence included. Manrope has no "✦" glyph, so ticker separators are an inline sparkle SVG instead |
| 66 | 7 | 12 **original doodle SVGs** hand-authored (ink outlines, stroke 2.5, round caps, lime/blue/white fills); logo = compass + "Career Recommender" in Manrope ExtraBold **converted to outlines** | Spec: original art; outlined text renders the same in an `<img>` logo |
| 67 | 7 | **Avatars**: 8 Open Peeps (CC0) downloaded once from DiceBear with friendly expressions only (no masks, no tearful "LOL" faces), embedded as data URIs and picked by a SHA-1 of the SRN | Default seeds produced sad and crying faces, which is wrong for a careers app; data URIs avoid duplicate SVG ids and need no network |
| 68 | 7 | Top navigation (`position="top"`) with Material line icons, `st.logo` (full wordmark; `icon_image` dropped because top nav would show only the icon), toolbar `viewer` mode | Matches the reference style; hides the developer "Deploy" button |
| 69 | 7 | White section cards = `st.container(key="card-…")`, styled through `[class*="st-key-card"]` | That class comes from our own key, so it's stable; widgets are styled through `data-testid` |
| 70 | 7 | Card **hover lift + -0.6° tilt** only on display cards (how-it-works, role, student, empty state); form and chart cards just deepen their shadow | A tilting form while you type or hover a chart is distracting |
| 71 | 7 | Every animation's **resting style is its final state**, and keyframes only animate "from"; reduced motion sets `animation/transition: none` and hides the plane and confetti | Reduced motion verified: 0 running animations and pixel-identical frames 2 s apart |
| 72 | 7 | Hero motion budget: 7 floating doodles + 2 blobs + plane + ticker = **11** continuous animations (≤ 12); every doodle gets its own duration and negative delay | Verified out of sync: each doodle's y-position follows a different curve over time |
| 73 | 7 | Match ring = `@property --p` + `conic-gradient`; skill bars and the confidence bar animate `transform: scaleX` (not width) | Smooth, no layout shift |
| 74 | 7 | Skill areas on Profile and Results are **HTML bars with level chips** (the Plotly area bar chart is removed) | Needed for the grow-from-0 animation; one shared component |
| 75 | 7 | Tabs styled through `[data-testid="stTab"][aria-selected]` (this Streamlit uses React Aria, not BaseWeb); checkbox boxes get an ink border; multiselect chips wrap instead of scrolling | Found by inspecting the live DOM: default checkboxes were nearly invisible, and the scrolling chips hid the first one |
| 76 | 7 | Radar labels wrap onto two lines and side margins shrink (90 → 56 px); the gap chart's axis labels are pinned to ink | Long names were clipped on phones; Streamlit's theme tinted the Plotly tick labels blue |
| 77 | 7 | Confusion-matrix image re-rendered on white with a cream→blue scale (plotting code only) | Retraining was deterministic: the model file is byte-identical and the metrics are unchanged |
| 78 | 7 | PDF keeps its white page and layout; accents are now ink (header band) + lime stripe/underlines + level chips matching the app | Spec |
| 79 | 7 | **This Mac has "Reduce motion" on** (`com.apple.universalaccess reduceMotion = 1`), so the app shows no animation here by design; the motion tests emulate "no-preference" | Respecting the OS setting is a requirement, not a bug |
| 80 | 7 | Tests: cream tokens, no navy colours left in code, reduced-motion block, WCAG AA for every text/background pair, assets + licences, doodle fill palette, no runtime DiceBear/Google Fonts URLs, stable avatar per SRN, animation budget | Guards the redesign rules |
| 81 | 7 | Home demo picker shows **"Name — role"** (e.g. "Arjun Desai — ML/AI Engineer"), dropping the "(demo)" suffix because the field label already says "fictional" | User request: the long descriptions were cut off; the shorter label fits at 390 px |
