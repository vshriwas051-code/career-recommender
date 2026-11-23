# Phase 7 — UI redesign: cream "doodle campus" look + fun floating animations

You are continuing the **career-recommender** project (Phases 0–6 are done and pushed).
This phase changes **only how the app looks and moves**. Do not change the model, scoring,
features, explanations, database or any behaviour. All existing tests must keep passing
(update only the theme/colour assertions that this redesign intentionally changes).

The user attached a reference screenshot (a student-portal landing page). Use it as **style
inspiration only**: cream background, big bold dark headings, blue body text, black pill
buttons, white rounded cards, playful hand-drawn doodles with lime-green accents, and a clean
top navigation bar. **Do not copy** its logo, brand name, wording or illustrations; everything
you add must be original or properly licensed.

Work in small steps, take screenshots, look at them, fix what's wrong, then commit and push as
`Phase 7: cream doodle redesign + floating animations`. Log every design decision in
`docs/decisions.md`, update `PROGRESS.md`, and stop when done.

---

## 1. Design tokens

### Colours (replace the navy theme everywhere)

| Token | Hex | Use |
|---|---|---|
| `cream` | `#F7F4EC` | page background |
| `cream-2` | `#EFEADD` | secondary background, table stripes, input fill |
| `card` | `#FFFFFF` | cards, tabs panel, form sections |
| `ink` | `#1E1C1A` | headings, primary buttons, doodle outlines |
| `body` | `#3A3733` | normal paragraph text |
| `blue` | `#2F4BC9` | intro/subtitle text, links, "Intermediate", chart "You" series |
| `lime` | `#B6F04A` | highlight fills, doodle accents, blobs, "Top pick" sticker |
| `lime-dark` | `#7DB51A` | lime borders, "Strong" level |
| `muted` | `#6B6760` | captions, secondary text |
| `line` | `#E6E0D2` | borders, chart grid lines |

Rules: lime is **never** used as text colour on cream (fails contrast) — text on lime is `ink`.
All text must meet WCAG AA contrast.

### Typography
- Font: **Manrope** (SIL Open Font License). **Bundle it locally** so the app still runs offline:
  download the variable `.woff2` (e.g. from the google/fonts GitHub repo, `ofl/manrope`) into
  `static/fonts/`, add its `OFL.txt` next to it, set `[server] enableStaticServing = true`, and
  register it with `[[theme.fontFaces]]` (url `app/static/fonts/...`). Fallback: `system-ui, sans-serif`.
- Headings: weight 800, letter-spacing `-0.02em`, line-height 1.1. Hero H1 ≈ 3.2rem desktop, 2.2rem mobile.
- Body 1rem / 1.6, weight 400–500. Intro lines under headings in `blue`.

### Shapes
- Cards: radius 20px, 1px `line` border, shadow `0 8px 24px rgba(30,28,26,.06)`.
- Buttons: **pill** (`buttonRadius = "full"` in the theme). Primary = `ink` fill + white text,
  weight 600. Secondary = transparent with 1.5px `ink` border.
- Inputs: `cream-2` fill, 12px radius, visible 2px `ink` focus ring.

### `.streamlit/config.toml`
Switch to `base = "light"` with the tokens above (`primaryColor = "#1E1C1A"`,
`backgroundColor = "#F7F4EC"`, `secondaryBackgroundColor = "#EFEADD"`, `textColor = "#1E1C1A"`),
Manrope as `font` and `headingFont`, `buttonRadius = "full"`. Verify each key against the
installed Streamlit version. Bump `requirements.txt` to `streamlit>=1.50` (needed for top
navigation, custom fonts and button radius).

---

## 2. Layout changes

### Navigation
- Use `st.navigation(..., position="top")` so pages appear as a **top nav bar** like the reference.
- `st.logo(...)` with a small **original** doodle logo (e.g. a hand-drawn compass) + the text
  "Career Recommender".
- Remove the emoji page icons or replace them with simple line icons; keep page names
  Home · Profile · Results · History · About.

### Home (`app.py`)
Two-column hero (stacks on mobile):
- **Left:** H1 "Find the career that fits you" (wraps to 3 lines), blue intro line
  ("Add your certificates, projects and events, and see your top 3 roles with reasons,
  gaps and next steps."), two pill buttons: **Build my profile** (primary) and
  **See a demo** (secondary). The demo picker sits under the buttons.
- **Right:** a floating doodle scene (section 3) on a soft lime/blue blob.
- **Below the hero:** "How it works" — 3 white cards (Add your profile → We score 10 skill
  areas → Get your top 3 roles), each with a small doodle icon and a fade-up stagger.
- **Bottom:** a slow scrolling **role ticker** ("Data Scientist ✦ Cloud/DevOps Engineer ✦ UI/UX
  Designer ✦ …" — all 11 roles from `config/roles.yaml`), pausing on hover.

### Profile
- Page header: H1 + blue intro + a small floating doodle on the right.
- Each form section (Basic details, Skills & interests, Certificates, Projects, Events) inside its
  own white card with a small doodle icon in its heading.
- Skill-areas section: horizontal bars that grow from 0 on load, with level chips.

### Results
- Student card: white card with a **doodle avatar** (section 3), name, SRN, year, college.
- Three role cards, equal height, staggered fade-up:
  - the match % shown as an **animated ring** (conic-gradient, fills from 0 to the value)
  - model confidence as the thin bar under it (keep the existing cap/softening logic)
  - the #1 card gets a lime **"Top pick"** sticker, rotated about -6°, with a gentle wobble
- Tabs restyled as pills. The radar chart, gap chart and checklist sit inside white cards.
- A **one-time confetti sprinkle** (lime/blue/ink pieces) when the results first appear in a
  session — CSS only, about 2.5 s, then it stops for good.

### History & About
- History: the table inside a white card; an **empty state** with a doodle and a
  "Build your first profile" button.
- About: content in white cards. The page is light now, so show `docs/architecture.svg`
  (the light version), not the dark one.

---

## 3. Illustrations (original or CC0 only)

Create `assets/doodles/` with **hand-drawn-style SVGs that you write yourself**: black
`ink` outlines, stroke width about 2.5, round caps and joins, slightly uneven lines, fills only in
`lime`, `blue` or white. Draw at least these:

- rocket, lightbulb, compass, graduation cap, laptop with code brackets, stack of books,
  paper plane, star, 4-point sparkle, squiggle underline, small trophy, magnifying glass

**People / avatars:** use **Open Peeps** by Pablo Stanley (CC0 public-domain licence,
https://www.openpeeps.com). The easiest route is DiceBear's `open-peeps` style
(https://www.dicebear.com/styles/open-peeps): **download about 8 avatar SVGs once**, save them to
`assets/avatars/`, and pick one per student from a hash of their SRN. Do not call the API at
runtime, because the app must work offline. Add a credit line in the README ("Avatars: Open Peeps
by Pablo Stanley, CC0"). If downloading fails, draw a simple original doodle avatar instead.

**Hero scene:** compose the doodles: a laptop or compass in the middle, with a rocket,
lightbulb, books, stars and sparkles around it, on a soft morphing lime blob with a smaller
blue blob behind it.

**Inline the SVG markup** with `st.html()` (or `st.markdown(..., unsafe_allow_html=True)`)
rather than `<img>`, so individual parts can be animated with CSS classes.

---

## 4. Animations (CSS only — no JS animation libraries)

Put all shared CSS in `src/career/ui.py` (replace the navy CSS). Animate only `transform` and
`opacity` (plus the ring's custom property), so the animations stay smooth on a laptop.

| # | Effect | Where | Spec |
|---|---|---|---|
| 1 | **Float** | hero doodles, page-header doodles | `translateY(0 → -12px → 0)`, ease-in-out, infinite; give each doodle its own duration (4.5–7 s) and delay so they never move in sync |
| 2 | **Drift-rotate** | stars, sparkles | rotate -8° ↔ 8°, 8 s, infinite |
| 3 | **Twinkle** | sparkles | scale .8 → 1.15 and opacity .5 → 1, 2.4 s, staggered |
| 4 | **Paper plane** | Home hero | glides across the hero on a gentle curve (CSS `offset-path`, with a translate fallback), about 9 s, repeating every ~14 s |
| 5 | **Blob morph** | behind the hero scene and page headers | animate `border-radius` between organic shapes plus a slow rotation, 14 s, lime and blue at about 35% opacity |
| 6 | **Squiggle draw** | under H1s | SVG path drawn with `stroke-dashoffset`, 1.2 s, once |
| 7 | **Fade-up stagger** | cards, role cards, how-it-works | `opacity 0→1`, `translateY(16px→0)`, 0.5 s, 80 ms per card |
| 8 | **Card hover** | all cards | lift 6px, rotate -0.6°, deeper shadow, 200 ms |
| 9 | **Button hover/press** | pill buttons | hover lifts 2px and a "→" nudges right; active presses to `scale(.97)` |
| 10 | **Match ring** | role cards | `@property --p` animated from 0 to the match value, 1.2 s |
| 11 | **Bar grow** | skill areas, confidence bar | width from 0, 0.9 s, staggered |
| 12 | **Role ticker** | Home bottom | marquee, 35 s linear infinite, pauses on hover |
| 13 | **Confetti** | Results, once per session | ~24 pieces fall and spin for 2.5 s, `animation-iteration-count: 1`, then removed or hidden |
| 14 | **Wave** | 👋 next to "Hi, <name>" on Results | rotates twice on load |
| 15 | **Sticker wobble** | "Top pick" | rotates -6° ↔ -3° every few seconds |

Rules:
- Keep it playful but calm: **no more than about 12 elements animating continuously per page**,
  and nothing that flashes or moves fast.
- **Respect reduced motion:** wrap everything so that under
  `@media (prefers-reduced-motion: reduce)` every animation and transition is turned off and
  elements show in their final state.
- Animations must never shift the layout (use `transform`, not margins) and never cover
  text or controls.
- Style Streamlit widgets with stable `[data-testid="..."]` selectors, not generated class names.

---

## 5. Charts, levels and PDF

- **Plotly** (`charts.py`): transparent backgrounds, Manrope font, `ink` text, `line` grid.
  Radar: You = `blue` (fill 25%), Role ideal = `ink` dashed, Year target = `lime-dark`.
  Gap chart: target in `cream-2` with a `line` border, you in `blue`.
- **Level chips** (`LEVEL_COLORS`): Beginner = warm grey (`#D9D3C5` background, `ink` text),
  Intermediate = `blue` (white text), Strong = `lime` (`ink` text, `lime-dark` border).
  Keep the "room to grow, not pass/fail" wording.
- **PDF** (`report.py`): keep the white background, and switch its accent colours to
  ink, blue and lime so it matches the app. Keep the layout.

---

## 6. Responsive

Check that everything works at **390 px wide (phone)**:
- the hero stacks (text first, then the doodle scene, shown smaller)
- cards go to one column
- the top nav collapses correctly
- nothing overflows horizontally

---

## 7. Verify before committing

1. `pytest` — all tests pass. Replace `test_navy_theme` with a test for the new tokens, and add tests that:
   - `ui.py` CSS contains the `prefers-reduced-motion` block
   - the font file, its licence and the doodle/avatar assets exist
   - no runtime URL to dicebear or Google Fonts is used
2. Run the app and take **screenshots at 1440×900 and 390×844** of Home, Profile (with a demo
   loaded), Results (demo), History and About. **Look at every screenshot** and fix:
   - overlaps and clipped doodles
   - low contrast
   - leftover navy colours
   - unstyled widgets
3. Record a few frames or a short GIF of the Home hero to confirm the floating motion looks
   smooth and unsynchronised.
4. Test with reduced motion turned on: nothing should move.
5. Replace the README screenshots with new ones (fictional demo data only), and add the
   font and avatar credits.
6. Commit, push, update `PROGRESS.md` and `docs/decisions.md`, then report back:
   - what changed
   - anything you couldn't do
   - the exact command to run the app

**Done when:** every page uses the cream/ink/blue/lime look with Manrope, the home hero has
the floating doodle scene, the 15 animations work and respect reduced motion, the app still
runs offline, and all tests pass.
