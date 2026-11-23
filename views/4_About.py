"""About page: how the system works, model accuracy, and the synthetic-data note."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from career.config import ROOT, app_config, role_names, scoring  # noqa: E402
from career.ui import apply_style, level_chip  # noqa: E402

st.set_page_config(page_title="About", page_icon="ℹ️", layout="wide")
apply_style()
cfg = app_config()
w = scoring()

st.title("ℹ️ How it works")

st.warning(
    "**The model is trained on synthetic data.** No real student data was available, and using real "
    "students' records would raise privacy concerns. Instead, 3,000 fictional students were generated "
    "around each role's ideal skill profile, with realistic noise and a fixed seed so the results are "
    "reproducible. The accuracy below shows the model learns those profiles well. It is **not** a "
    "measure of real-world accuracy, so treat recommendations as guidance, not a verdict.", icon="🧪")

st.graphviz_chart("""
digraph {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fillcolor="#12264F", color="#4C8DFF",
        fontcolor="#E8EEF9", fontname="Helvetica", fontsize=11, margin="0.18,0.1"];
  edge [color="#9FB2D6"];
  p [label="Student profile\\ncertificates · projects\\nevents · skills"];
  s [label="Skill extraction\\nkeywords → skills → 10 areas\\n(every point keeps its source)"];
  f [label="Feature vector\\n10 area scores + year\\n+ CGPA + interests"];
  m [label="ML model\\n(Logistic Regression)\\ntop-3 roles"];
  x [label="Explanation\\nwhy · gaps · next steps\\n(year-of-study rules)"];
  p -> s -> f -> m -> x;
  s -> x [style=dashed, label=" evidence", fontcolor="#9FB2D6", fontsize=9];
}
""", width="stretch")

# ---------- 1. extraction ----------
st.header("1 · Skill extraction (rule-based)")
st.markdown(
    "Titles, descriptions and tech stacks are matched against about 200 keywords in "
    "`config/skills.yaml` (e.g. *“AWS Cloud Practitioner”* → **aws** → **Cloud & DevOps**). "
    "Each piece of evidence adds points to its area, once per area per item:")
st.dataframe(pd.DataFrame([
    {"Evidence": "Project", "Points": f"{w['project']:g} (+{w['project_bonus']:g} if team lead or hackathon)"},
    {"Evidence": "Certificate", "Points": f"{w['certificate']:g}"},
    {"Evidence": "Self-rated skill", "Points": f"rating × {w['skill_rating_factor']:g}"},
    {"Evidence": "Event", "Points": f"{w['event']:g} (+{w['event_bonus']:g} if finalist or winner)"},
]), hide_index=True, width="content")
lv = cfg["skill_levels"]
st.markdown(
    f"Raw points become a 0–100 score per area ({w['area_cap']:g} points or more = 100). Each score gets a "
    f"friendly level: {level_chip('Beginner')} below {lv['beginner_below']}, "
    f"{level_chip('Intermediate')} {lv['beginner_below']}–{lv['strong_above']}, "
    f"{level_chip('Strong')} above {lv['strong_above']}.", unsafe_allow_html=True)

# ---------- 2. model ----------
st.header("2 · Career prediction (machine learning)")
meta_path = ROOT / "models" / "metadata.json"
if not meta_path.exists():
    st.error("No trained model found. Run `PYTHONPATH=src python -m career.train`.")
else:
    import json
    meta = json.loads(meta_path.read_text())
    m = meta["metrics"]
    st.markdown(
        f"Two models were trained on {meta['training_rows']:,} synthetic students and compared with "
        f"5-fold cross-validation. **{meta['model_type']}** was kept. It predicts one of "
        f"{len(role_names())} roles from {len(meta['feature_names'])} features. Results on "
        f"{meta['test_rows']} held-out students:")
    c1, c2, c3 = st.columns(3)
    c1.metric("Top-3 accuracy", f"{m['top3_accuracy'] * 100:.1f}%",
              help="The true role is among the 3 shown")
    c2.metric("Top-1 accuracy", f"{m['accuracy'] * 100:.1f}%")
    c3.metric("Macro F1", f"{m['macro_f1']:.3f}")
    st.dataframe(pd.DataFrame([{"Model": k + (" ✅" if k == meta["model_type"] else ""),
                                "CV accuracy": c["cv_accuracy"], "Test accuracy": c["accuracy"],
                                "Test top-3": c["top3_accuracy"], "Macro F1": c["macro_f1"]}
                               for k, c in meta["comparison"].items()]),
                 hide_index=True, width="stretch")
    cm = ROOT / "reports" / "confusion_matrix.png"
    if cm.exists():
        with st.expander("Confusion matrix"):
            st.image(str(cm), caption="Mix-ups happen between roles with overlapping skills "
                                      "(e.g. Data Scientist ↔ ML/AI Engineer), which is why the top 3 are shown.")
    st.caption(f"Trained {meta['trained_on']} · seed {meta['seed']} · scikit-learn {meta['sklearn_version']}")

# ---------- 3. scores ----------
st.header("3 · Reading the result cards")
st.markdown(f"""
- **Skill match (big number):** cosine similarity between your 10 area scores and the role's ideal profile.
  It measures the *shape* of your skills, so a first-year student with the right mix can still match well.
- **Model confidence (small line):** the model's probability, **softened** (temperature
  {cfg['confidence_temperature']:g}) and **capped at {cfg['confidence_cap'] * 100:.0f}%**. The raw model is
  over-sure on clear-cut profiles, and no career prediction is ever certain. Softening never changes the ranking.
  Labels: High ≥ {cfg['confidence_bands']['high'] * 100:.0f}%, Medium ≥ {cfg['confidence_bands']['medium'] * 100:.0f}%.
""")

# ---------- 4. advice ----------
st.header("4 · Why, gaps and next steps")
ye = cfg["year_expectation"]
st.markdown(f"""
- **Why:** your strongest areas that the role relies on, each with the exact certificates, projects and events behind it.
- **Gaps:** measured against a **year-adjusted target**, not the professional ideal:
  {', '.join(f'year {y}: {v * 100:.0f}%' for y, v in ye.items())} of the role's ideal.
- **Next steps:** years 1–2 get **explore** guidance (fundamentals, beginner certificates);
  years 3–4 get **internship-ready** guidance (portfolio projects, interview prep).
  Suggestions that close your biggest gap come first, and anything you've already done is skipped.
""")

# ---------- 5. limits ----------
st.header("5 · Limitations")
st.markdown("""
- Synthetic training data: real outcomes (who actually got which job) would make a much better model.
- Keyword matching can miss unusual wording, or credit a keyword in an unexpected context.
- Self-ratings are subjective.
- Everything runs offline: no paid APIs and no LLM calls. Data stays in a local SQLite file.
""")
