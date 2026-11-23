# MASTER PROMPT — AI Career Recommendation System (college mini-project)

You are building a simple, polished college mini-project. A student enters their
academic profile: college, SRN, class, year of study, certificates, projects and
events attended. The system predicts the job roles that suit them best. It explains
**why**, shows their **skill gaps**, and suggests **next steps**.

Keep it simple, working and well documented. A clean demo beats extra features.

---

## 0. How to work

- Work **phase by phase** (Section 9). After each phase, run `pytest`, fix any failures,
  update `PROGRESS.md`, commit, push, and stop to report.
- In Phase 0, create a `CLAUDE.md` that says: "Always follow CAREER_MASTER_PROMPT.md.
  Status is in PROGRESS.md. Decisions are in docs/decisions.md."
- Don't stop to ask about small details. Decide, log it in `docs/decisions.md`, and
  continue.
- **Never commit real student data.** The `data/` database is git-ignored. Demo profiles
  must be fictional.

## 1. Tech stack

- Python 3.11+, **Streamlit** (UI), **SQLite** (`sqlite3`, profile storage),
  **scikit-learn** (model), **pandas**, **numpy**, **plotly** (charts), **fpdf2** (PDF
  report), **pyyaml**, **pytest**.
- There are no paid APIs and no LLM calls. Everything runs offline on a laptop.
- `pyproject.toml` or `requirements.txt`. The app starts with `streamlit run app.py`.

## 2. Features

### 2.1 Student profile (input)
| Section | Fields |
|---|---|
| Basic details | Full name; **SRN** (unique, required, uppercase letters and digits, 6–15 chars, pattern in config); **college name**; **branch/department**; **class / section**; **year of study** (1–4); CGPA (0–10, optional) |
| Skills & interests | Self-rated skills: pick from the taxonomy and rate each 1–5. Interests: multi-select of work styles and domains, e.g. building apps, working with data, design, security, hardware, business |
| **Certificates** (repeatable list) | Title, issuing organisation, platform (Coursera, NPTEL, AWS, Google, Udemy, other), domain (auto-suggested from title), completion date, credential URL (optional) |
| **Projects** (repeatable list) | Title, short description, tech stack (multi-select plus free text), role (solo or team lead or member), type (academic, personal, hackathon, internship), GitHub link (optional) |
| **Events attended** (repeatable list) | Event name, type (hackathon, workshop, seminar, conference, competition, bootcamp), theme/domain, date, participation (attended, participant, finalist, winner) |

- Users can add, edit and delete entries in each list (`st.data_editor` or add/remove
  rows).
- Profiles are saved in SQLite and loaded back by SRN.
- Validation runs before saving: SRN format, year 1–4, CGPA 0–10, and dates not in the
  future.

### 2.2 Skill extraction (rule-based, explainable)
- `config/skills.yaml` maps keywords to skills, and skills to about 10 **skill areas**.
  For example, "AWS Cloud Practitioner" maps to skill aws, area CLOUD; "React" maps to
  WEB.
- Skill areas: PROGRAMMING, WEB, MOBILE, DATA_ANALYSIS, ML_AI, CLOUD_DEVOPS, SECURITY,
  DESIGN_UX, EMBEDDED_IOT, BUSINESS_PRODUCT.
- Each piece of evidence adds weighted points to its area:
  - project: 3 (+1 if team lead or hackathon winner)
  - certificate: 2
  - self-rated skill: rating × 0.5
  - event: 1 (+1 if finalist or winner)
- Area scores are normalised to 0–100.
- **Every point keeps its source**, e.g. "CLOUD +2 from certificate 'AWS Cloud
  Practitioner'". This powers the "why" explanation.

### 2.3 Career prediction (the AI part)
- About 10 target roles in `config/roles.yaml`: Software Developer, Full-Stack Web
  Developer, Mobile App Developer, Data Analyst, Data Scientist, ML/AI Engineer,
  Cloud/DevOps Engineer, Cybersecurity Analyst, UI/UX Designer, Embedded/IoT Engineer,
  Business/Product Analyst.
- Each role has an ideal skill-area profile, recommended certificates, project ideas and
  event types.
- **Model:** a `RandomForestClassifier` (compare it against `LogisticRegression` and keep
  the better one). Features are the 10 area scores, year of study, CGPA and interest
  flags.
- **Training data:** a synthetic dataset of about 3,000 students generated from the role
  profiles with realistic noise, using a fixed seed (e.g. 42) so it's reproducible.
  State clearly in the README that the training data is synthetic and why: no real
  student data was available or appropriate.
- **Output:**
  - The **top 3 roles** with confidence %.
  - A **match score** per role: cosine similarity between the student's area vector and
    the role's ideal profile. Show this alongside the model confidence so the result is
    easy to explain.
- **Year-of-study rule:**
  - Years 1–2 get "explore" guidance (fundamentals and beginner certificates).
  - Years 3–4 get "internship-ready" guidance (portfolio projects, interview prep).

### 2.4 Explanation, gaps and next steps
- **Why this role:** the top contributing skill areas, each with the exact
  certificates, projects and events behind it (from 2.2).
- **Skill gaps:** areas where the student is below the role's ideal profile, ranked by
  size of gap.
- **Next steps** (from roles.yaml), filtered by the gaps and year of study:
  - 2–3 certificates to do
  - 1–2 project ideas
  - 1–2 event types to attend

### 2.5 Results dashboard
- **Navy theme.** Use `.streamlit/config.toml` with:
  - `primaryColor="#4C8DFF"`
  - `backgroundColor="#0B1B3B"`
  - `secondaryBackgroundColor="#12264F"`
  - `textColor="#E8EEF9"`
  - a clean sans-serif font
- Add light CSS for smooth fade-in and hover transitions on cards. Don't overdo it.
- Pages: **Profile** (form) → **Results** → **History** (saved profiles, open or delete
  by SRN) → **About** (how the model works, its accuracy, and the synthetic-data note).
- Results page:
  - student summary card: name, SRN, college, class, year
  - top-3 role cards with confidence bars
  - **radar chart** of skill areas, student vs. the top role
  - "why" bullets
  - gap bar chart
  - next steps checklist
- **Download PDF report** with the same content (fpdf2), named `<SRN>_career_report.pdf`.

## 3. Repository layout

```
career-recommender/
├── app.py                     Streamlit entry (multipage)
├── pages/                     1_Profile.py, 2_Results.py, 3_History.py, 4_About.py
├── src/career/
│   ├── models.py              dataclasses: Student, Certificate, Project, Event
│   ├── db.py                  SQLite schema + CRUD (students, certificates, projects, events)
│   ├── validate.py            SRN/year/CGPA/date validation
│   ├── skills.py              keyword → skill → area extraction with evidence trail
│   ├── features.py            profile → feature vector
│   ├── synth.py               synthetic training data generator (fixed seed)
│   ├── train.py               train + evaluate + save model
│   ├── predict.py             top-3 roles, confidence, match score
│   ├── explain.py             why / gaps / next steps / year rules
│   └── report.py              PDF report
├── config/                    skills.yaml, roles.yaml, app.yaml (SRN pattern etc.)
├── models/                    trained model (.joblib) + metadata.json
├── reports/                   model_evaluation.md, confusion_matrix.png
├── demo/                      3 fictional demo profiles (JSON) + loader
├── data/                      SQLite db (git-ignored)
├── docs/                      decisions.md, architecture.md (diagram), screenshots/
├── tests/
├── .streamlit/config.toml
├── README.md, PROGRESS.md, CLAUDE.md
```

## 4. Database (SQLite)

- `students`: srn (PK), name, college, branch, class_section, year_of_study, cgpa,
  interests (JSON), skills (JSON), created_at, updated_at
- `certificates`: cert_id (PK), srn (FK), title, issuer, platform, domain,
  completion_date, credential_url
- `projects`: project_id (PK), srn (FK), title, description, tech_stack (JSON), role,
  project_type, github_url
- `events`: event_id (PK), srn (FK), name, event_type, theme, event_date, participation
- `predictions`: prediction_id (PK), srn (FK), created_at, model_version, top_roles
  (JSON), area_scores (JSON). Keep history; never overwrite.

Turn on foreign keys. Deleting a student cascades to their rows.

## 5. Model evaluation (shown in the About page and README)

- Train/test split 80/20, stratified.
- Report accuracy, **top-3 accuracy**, macro F1, and a confusion matrix image.
- Save `models/metadata.json` with model type, seed, training rows, feature list,
  metrics and date.

## 6. Demo profiles

Create 3 fictional students with very different profiles:
- a 2nd-year student strong in web
- a 3rd-year student strong in data/ML with AWS certificates
- a 4th-year student into security with CTF events

Add a "Load demo profile" button so the app can be shown without typing.

## 7. Tests (pytest)

- SRN validation (valid, invalid, duplicate)
- Save then load round-trip for a full profile, including the lists
- Skill extraction maps known keywords to the right areas and keeps evidence
- Feature vector shape and order
- Synthetic data is reproducible with the same seed
- Model top-3 accuracy ≥ 0.85 on the synthetic test set
- Each demo profile's top-1 role is the expected one
- The PDF report file is created

## 8. README

1. Overview and screenshots
2. Features
3. How it works: a diagram of profile → skill extraction → features → model → explanation
4. Setup and run commands
5. Model and evaluation, with the synthetic-data note
6. Project structure
7. Limitations and future work, e.g. real anonymised data, resume upload, LLM-written
   advice

## 9. Phases

| Phase | Scope | Done when |
|---|---|---|
| 0 Setup | Project skeleton, requirements, navy theme config, CLAUDE.md, PROGRESS.md, .gitignore (`.venv/`, `data/`, `__pycache__/`) | `streamlit run app.py` opens a navy home page; `pytest` passes |
| 1 Profile & storage | models.py, db.py, validate.py, Profile page with the basic details plus repeatable certificate/project/event lists; History page | A full profile saves, reloads by SRN, edits and deletes; validation errors show inline |
| 2 Skill extraction | skills.yaml, roles.yaml, skills.py, features.py | The extraction tests pass; a profile shows area scores with an evidence list |
| 3 Model | synth.py, train.py, evaluation report, saved model | Top-3 accuracy ≥ 0.85; reports/model_evaluation.md and confusion matrix exist |
| 4 Prediction & advice | predict.py, explain.py, year rules, predictions history table | Demo profiles give the expected top-1 role with a sensible why, gaps and next steps |
| 5 Results UI & PDF | Results page cards, radar and gap charts, animations, PDF download, About page | The full demo flow works end to end and looks polished |
| 6 Polish & submit | Demo loader, README with screenshots, architecture diagram, final tests | A fresh clone runs with only the README steps |
