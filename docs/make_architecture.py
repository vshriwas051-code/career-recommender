"""Generate the architecture diagram: outline-only, transparent background, no fills.

    python docs/make_architecture.py

Writes, in docs/:
  architecture.svg / .png        dark lines — for light slides and the README (light mode)
  architecture-dark.svg / .png   white lines — for dark slides and the README (dark mode)
Text is converted to outlines in the SVGs, so they look the same on any machine.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent
plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path"})

W, H = 2.05, 1.05                      # box size
TOP_Y, BOT_Y, DB_Y = 3.75, 0.55, 2.15  # row baselines
XS = [0.25, 2.65, 5.05, 7.45, 9.85, 12.25]

RUNTIME = [
    ("Student profile", "Profile page form\nbasic details · skills\ncerts · projects · events"),
    ("Skill extraction", "skills.py + skills.yaml\nkeywords → skills → 10 areas"),
    ("Feature vector", "features.py\n10 areas · year · CGPA\n8 interest flags"),
    ("ML model", "Logistic Regression\npredict.py · top-3 roles\n+ cosine match score"),
    ("Explanation", "explain.py\nwhy · gaps · next steps\nyear-of-study rules"),
    ("Results + PDF", "Results page · radar\ngap chart · checklist\nreport.py → PDF"),
]
TRAINING = [
    ("Role profiles", "roles.yaml\n11 ideal skill profiles"),
    ("Synthetic data", "synth.py · seed 42\n3,000 fictional students"),
    ("Training", "train.py · 80/20 split\nLR vs RF · 5-fold CV"),
    ("Saved model", "career_model.joblib\nmetadata.json · reports/"),
]


def draw(ink: str, path_stem: str) -> None:
    fig, ax = plt.subplots(figsize=(14.6, 5.95))
    fig.patch.set_alpha(0)
    ax.set_xlim(0, 14.55)
    ax.set_ylim(0.4, 6.35)
    ax.axis("off")

    def box(x, y, title, sub, dashed=False):
        ax.add_patch(FancyBboxPatch((x, y), W, H, boxstyle="round,pad=0.02,rounding_size=0.12",
                                    fill=False, edgecolor=ink, lw=1.5, ls=(0, (4, 3)) if dashed else "-"))
        ax.text(x + W / 2, y + H - 0.2, title, ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=ink)
        ax.text(x + W / 2, y + H / 2 - 0.13, sub, ha="center", va="center", fontsize=7.6,
                color=ink, linespacing=1.35)

    def arrow(p, q, dashed=False, rad=0.0, label=None, lx=0.0, ly=0.0):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="->", mutation_scale=13, lw=1.3, color=ink,
                                     ls=(0, (4, 3)) if dashed else "-",
                                     connectionstyle=f"arc3,rad={rad}", shrinkA=2, shrinkB=2))
        if label:
            ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, ha="center", va="center",
                    fontsize=7.6, style="italic", color=ink)

    # section labels
    ax.text(0.25, TOP_Y + H + 1.25, "AT RUNTIME — every time a student asks for a recommendation",
            fontsize=9, fontweight="bold", color=ink)
    ax.text(0.25, BOT_Y + H + 0.3, "OFFLINE, ONCE — training (no real student data)",
            fontsize=9, fontweight="bold", color=ink)

    # runtime row
    for x, (t, s) in zip(XS, RUNTIME):
        box(x, TOP_Y, t, s)
    for a, b in zip(XS, XS[1:]):
        arrow((a + W, TOP_Y + H / 2), (b, TOP_Y + H / 2))

    # evidence trail: extraction -> explanation (curved over the top)
    arrow((XS[1] + W / 2, TOP_Y + H), (XS[4] + W / 2, TOP_Y + H), dashed=True, rad=-0.18,
          label="evidence trail — every point keeps its source", ly=0.86)

    # SQLite store under the profile
    box(XS[0], DB_Y, "SQLite", "db.py · data/career.db\nprofiles + prediction history")
    arrow((XS[0] + W / 2 - 0.25, TOP_Y), (XS[0] + W / 2 - 0.25, DB_Y + H), label="save", lx=-0.32)
    arrow((XS[0] + W / 2 + 0.25, DB_Y + H), (XS[0] + W / 2 + 0.25, TOP_Y), label="load", lx=0.32)
    # predictions logged back to SQLite
    arrow((XS[3] + W / 2, TOP_Y), (XS[0] + W, DB_Y + H / 2), dashed=True, rad=-0.12,
          label="log prediction", lx=0.2, ly=0.0)

    # training row
    for x, (t, s) in zip(XS[1:5], TRAINING):
        box(x, BOT_Y, t, s, dashed=True)
    for a, b in zip(XS[1:4], XS[2:5]):
        arrow((a + W, BOT_Y + H / 2), (b, BOT_Y + H / 2))
    arrow((XS[4] + W / 2, BOT_Y + H), (XS[3] + W / 2 + 0.35, TOP_Y), dashed=True,
          label="loaded by", lx=0.5, ly=0.05)

    for ext in ("svg", "png"):
        fig.savefig(OUT / f"{path_stem}.{ext}", transparent=True, bbox_inches="tight", pad_inches=0.15,
                    dpi=220)
    plt.close(fig)


if __name__ == "__main__":
    draw("#1B2433", "architecture")       # for light backgrounds
    draw("#F2F5FB", "architecture-dark")  # for dark backgrounds
    print("wrote", *sorted(p.name for p in OUT.glob("architecture*.*") if p.suffix in (".svg", ".png")))
