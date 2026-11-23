import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st  # noqa: E402

from career.ui import apply_style  # noqa: E402

st.set_page_config(page_title="🗂️ History", layout="wide")
apply_style()
st.title("🗂️ History")
st.info("Coming in a later phase.")
