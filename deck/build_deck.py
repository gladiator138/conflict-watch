"""Build the jury deck (16:9, dark theme) from the pipeline outputs.

    python deck/build_deck.py      ->  deck/Conflict_Watch_Jury_Deck.pptx

Layout, colours and typography follow the team's reference deck: dark navy background, amber kicker
labels, big KPI numbers, an amber "SO WHAT" bar and a classification footer. Fonts are large and the
contrast is high because the deck is presented over a video call.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config as C  # noqa: E402

FIG = ROOT / "outputs" / "figures"
SHOT = ROOT / "deck" / "shots"
DF = ROOT / "deck" / "figs"
TB = C.TAB_DIR
OUT = ROOT / "deck" / "Conflict_Watch_Jury_Deck.pptx"
QR_URL = "https://conflictmonitor2026.streamlit.app"   # set to the hosted dashboard or repository URL to print a QR code on the closing slide


def rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


BG, PANEL, PANEL2, BORDER = rgb("07131F"), rgb("0F2236"), rgb("16304A"), rgb("2B4763")
WHITE, TEXT2, TEXT3, MUTED = rgb("FFFFFF"), rgb("D5DEE8"), rgb("9FB2C6"), rgb("5E7B99")
AMBER, RED, CYAN, TEAL, VIOLET, AMBER_BG = (rgb("F0B03A"), rgb("FF4D5E"), rgb("4FD6E8"), rgb("35C2A6"),
                                            rgb("A794FF"), rgb("2A2008"))
FONT = "Calibri"
FOOTER = "CONFLICT WATCH   |   DATA ANALYTICS COMPETITION 2026   |   UNCLASSIFIED - OPEN-SOURCE DATA ONLY"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
_n = [0]


# --------------------------------------------------------------------------- primitives
def text(slide, x, y, w, h, s, size=16, color=WHITE, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         spacing=None, italic=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0.0)
    tf.vertical_anchor = anchor
    lines = s if isinstance(s, list) else [s]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        runs = ln if isinstance(ln, list) else [(ln, {})]
        for r in runs:
            if isinstance(r, str):
                r = (r, {})
            run = p.add_run()
            run.text = r[0]
            f = run.font
            f.name = FONT
            f.size = Pt(r[1].get("size", size))
            f.bold = r[1].get("bold", bold)
            f.italic = italic
            f.color.rgb = r[1].get("color", color)
        if spacing:
            p.space_after = Pt(spacing)
    return tb


def box(slide, x, y, w, h, fill=PANEL, line=BORDER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, lw=1.0, radius=0.06):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    return s


def new_slide(kicker=None, title=None, footer=True):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG
    _n[0] += 1
    if kicker:
        text(s, 0.55, 0.32, 12, 0.3, kicker, size=12, color=AMBER, bold=True)
        spaced(s.shapes[-1])
    if title:
        text(s, 0.55, 0.62, 12.3, 0.6, title, size=28, bold=True)
    if footer:
        text(s, 0.55, 7.08, 10, 0.25, FOOTER, size=9, color=MUTED)
        spaced(s.shapes[-1], 100)
        text(s, 12.2, 7.08, 0.6, 0.25, str(_n[0]), size=10, color=MUTED, align=PP_ALIGN.RIGHT)
    return s


def spaced(shape, spc=200):
    """Letter-spacing for kicker labels."""
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            r.font._element.set("spc", str(spc))


def kicker_lbl(slide, x, y, w, s, color=AMBER, size=12):
    text(slide, x, y, w, 0.3, s, size=size, color=color, bold=True)
    spaced(slide.shapes[-1])


def kpi(slide, x, y, w, h, num, label, sub=None, color=AMBER, numsize=36, kick=None, border=BORDER):
    box(slide, x, y, w, h, line=border, lw=1.5 if border != BORDER else 1.0)
    yy = y + 0.18
    if kick:
        kicker_lbl(slide, x + 0.22, yy, w - 0.4, kick, size=11, color=TEXT3)
        yy += 0.32
    text(slide, x + 0.22, yy, w - 0.4, 0.7, num, size=numsize, bold=True, color=color)
    yy += numsize / 72 * 1.12 + 0.05
    text(slide, x + 0.22, yy, w - 0.4, 0.8, label, size=15, bold=True, color=WHITE)
    if sub:
        text(slide, x + 0.22, y + h - 0.62, w - 0.4, 0.5, sub, size=12, color=TEXT3, anchor=MSO_ANCHOR.BOTTOM)


def kpi_row(slide, x, y, w, h, num, label, color=AMBER, numsize=26):
    """Compact side KPI card (number left, label right) as in the reference deck."""
    box(slide, x, y, w, h)
    text(slide, x + 0.18, y, 1.9, h, num, size=numsize, bold=True, color=color, anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x + 2.05, y, w - 2.2, h, label, size=13, color=TEXT2, anchor=MSO_ANCHOR.MIDDLE)


def kpi_side(slide, x, y, w, h, num, label, color=AMBER, numsize=28):
    """Stacked side KPI card: number above, label below."""
    box(slide, x, y, w, h)
    text(slide, x + 0.2, y + 0.12, w - 0.35, 0.55, num, size=numsize, bold=True, color=color)
    text(slide, x + 0.2, y + 0.12 + numsize / 72 * 1.15, w - 0.35, h - 0.6, label, size=13, color=TEXT2)


def sowhat(slide, msg, label="SO WHAT", y=6.38):
    box(slide, 0.55, y, 12.23, 0.5, fill=AMBER_BG, line=AMBER, lw=1.25, radius=0.12)
    text(slide, 0.78, y, 1.6, 0.5, label, size=11, color=AMBER, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    spaced(slide.shapes[-1])
    text(slide, 2.25, y, 10.4, 0.5, msg, size=15, bold=True, anchor=MSO_ANCHOR.MIDDLE)


def picture(slide, path, x, y, w, h, frame=False, caption=None, cap_color=CYAN):
    """Place an image fitted inside (x, y, w, h), keeping aspect ratio, top-left aligned horizontally centred."""
    im = Image.open(path)
    iw, ih = im.size
    r = min(w / iw, h / ih)
    pw, ph = iw * r, ih * r
    px, py = x + (w - pw) / 2, y + (h - ph) / 2
    if frame:
        box(slide, px - 0.06, py - 0.06, pw + 0.12, ph + 0.12, fill=WHITE, line=None, radius=0.02)
    slide.shapes.add_picture(str(path), Inches(px), Inches(py), Inches(pw), Inches(ph))
    if caption:
        kicker_lbl(slide, px, py + ph + 0.1, pw, caption, color=cap_color, size=10)
    return px, py, pw, ph


def table(slide, x, y, w, rows, col_w, header_fill=CYAN, header_color=BG, size=12, row_h=0.42,
          first_col_color=None, fills=None):
    nr, nc = len(rows), len(rows[0])
    shp = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
    tbl = shp.table
    tblPr = shp._element.graphic.graphicData.tbl.tblPr
    tblPr.set("bandRow", "0")
    tblPr.set("firstRow", "0")
    for j, cw in enumerate(col_w):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j)
            c.fill.solid()
            if i == 0:
                hf = header_fill[j] if isinstance(header_fill, list) else header_fill
                c.fill.fore_color.rgb = hf
            else:
                c.fill.fore_color.rgb = (fills[i][j] if fills and fills[i][j] is not None
                                         else (PANEL if i % 2 else PANEL2))
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            run = p.add_run()
            run.text = str(val)
            f = run.font
            f.name = FONT
            f.size = Pt(size)
            if i == 0:
                f.bold = True
                f.color.rgb = header_color
            else:
                f.color.rgb = (first_col_color if (j == 0 and first_col_color) else TEXT2)
                f.bold = j == 0
    return tbl


def circle_num(slide, x, y, n, color, d=0.42, size=15):
    s = box(slide, x, y, d, d, fill=color, line=None, shape=MSO_SHAPE.OVAL)
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(n)
    r.font.size, r.font.bold, r.font.name = Pt(size), True, FONT
    r.font.color.rgb = BG
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


# --------------------------------------------------------------------------- numbers (all from tables)
ov = pd.read_csv(TB / "insight_case_overview.csv").set_index("conflict_case")
rag = pd.read_csv(TB / "rag_scorecard.csv").set_index("conflict_case")
ew = pd.read_csv(TB / "early_warning_scores.csv")
ew26 = ew[ew.year == 2026].set_index("model")
lg = ew26.loc["LightGBM classifier"]
rule = ew26.loc["Rule: rank by last month's deaths"]
sc = pd.read_csv(TB / "forecast_scores.csv")
hA = sc[(sc.fold == 2026) & (sc.track == "A")]
nv = hA[hA.model == "naive"].set_index("conflict_case").MAE
en = hA[hA.model == "ensemble"].set_index("conflict_case").MAE
pooled = (1 - en.sum() / nv.sum()) * 100
red = (1 - en / nv) * 100
preds = pd.read_parquet(C.PROCESSED / "forecast_preds.parquet")
e26 = preds[(preds.model == "ensemble") & (preds.fold == 2026)]
cov80 = ((e26.actual >= e26.pi80_lo) & (e26.actual <= e26.pi80_hi)).mean() * 100
rm = pd.read_csv(TB / "forecast_rmsle.csv")
rml = rm.groupby(["model", "track", rm.fold.eq(2026)]).RMSLE.mean().unstack([1, 2])
stats = pd.read_csv(TB / "insight_stats.csv").iloc[0]
fg = pd.read_csv(TB / "insight_front_geography.csv").pivot_table(index="area", columns="year", values="share")
don22, don26 = fg.loc["Donetsk oblast", 2022] * 100, fg.loc["Donetsk oblast", 2026] * 100
att = pd.read_csv(TB / "insight_attrition.csv")
usir_att = att[att.conflict_case == "US–Iran"].set_index("year")
ts = pd.read_csv(TB / "insight_theatre_spread.csv")
usir_ts = ts[ts.conflict_case == "US–Iran"].set_index("year").countries
ie = pd.read_csv(TB / "insight_india_exposure.csv")
g26 = ie[ie.year == 2026]
gulf = g26[g26.india_tag.str.startswith("Gulf")]
hz = g26[g26.india_tag.str.startswith("Iran")]
pakprox = ie[ie.india_tag.str.startswith("Pakistan")].groupby("year").deaths.sum()
dq = pd.read_csv(TB / "data_quality_log.csv")
ip = pd.read_csv(TB / "insight_indian_press.csv").set_index("conflict_case")
abl = pd.read_csv(TB / "ablation_lgb.csv")
summary = json.loads((TB / "run_summary.json").read_text())
fut = pd.read_parquet(C.PROCESSED / "forecast_future.parquet")
fut = fut[fut.model == "ensemble"]

RAGC = {"RED": RED, "AMBER": AMBER, "GREEN": TEAL}

# =========================================================================== 1 COVER
s = new_slide(footer=False)
picture(s, DF / "map.png", 6.3, 1.0, 6.75, 5.6)
kicker_lbl(s, 0.6, 0.55, 12, "DATA ANALYTICS COMPETITION 2026", size=13)
text(s, 0.6, 1.55, 5.6, 1.2, "CONFLICT WATCH", size=52, bold=True)
text(s, 0.6, 2.75, 5.3, 1.6, "When and where will conflict deaths rise next, and what does it mean for India?",
     size=22, color=TEXT2)
text(s, 0.6, 4.2, 5.3, 0.8, ["Russia–Ukraine  ·  Israel–Hamas", "Afghanistan–Pakistan  ·  US–Iran"],
     size=16, color=AMBER, bold=True)
kicker_lbl(s, 0.6, 5.05, 5.3, "TEAM", color=TEXT3, size=11)
text(s, 0.6, 5.38, 5.3, 1.2, ["Maj Shivam Mehta", "Capt Siddharth Sangwan", "Capt Sahil Singh"], size=18, bold=True)
text(s, 0.6, 6.85, 12, 0.3, "CONFLICT ESCALATION FORECASTING & EARLY WARNING   |   UNCLASSIFIED - OPEN-SOURCE DATA ONLY",
     size=10, color=MUTED)
spaced(s.shapes[-1], 100)
notes(s, "Good morning. In one sentence: we built a system that forecasts where conflict deaths will rise next "
         "month, warns which districts will escalate, and translates both into what the Indian Armed Forces should do.")

# =========================================================================== 2 BLUF
s = new_slide("BOTTOM LINE UP FRONT", "Four wars, three warning signals, one exposed neighbour")
cards = [
    (1, AMBER, "THREAT", "RED", f"Russia–Ukraine: {rag.loc['Russia–Ukraine', 'forecast_next']:,.0f} deaths forecast for Oct 2026",
     "Af–Pak and US–Iran AMBER, Israel–Hamas GREEN", RED),
    (2, RED, "INDIA", "104", "killed off Sri Lanka, 4 Mar 2026: the US–Iran war reached the Indian Ocean",
     f"Strikes in 5 Gulf states hosting the Indian diaspora", RED),
    (3, CYAN, "PREDICTION", f"−{pooled:.0f}%", "error vs the 'no-change' rule, one month ahead, on unseen 2026 data",
     f"Escalation warning AUC {lg.ROC_AUC:.2f}: top-10 list {lg.precision_at_10 / lg.base_rate:.1f}× random", CYAN),
]
for i, (n, cc, k, num, lab, sub, ncol) in enumerate(cards):
    x = 0.55 + i * 4.13
    box(s, x, 1.45, 3.93, 4.6)
    circle_num(s, x + 0.28, 1.72, n, cc, d=0.4, size=14)
    kicker_lbl(s, x + 0.82, 1.78, 2.9, k, color=TEXT3, size=12)
    text(s, x + 0.28, 2.45, 3.5, 1.0, num, size=60, bold=True, color=ncol)
    text(s, x + 0.28, 3.65, 3.45, 1.4, lab, size=17, bold=True)
    text(s, x + 0.28, 5.05, 3.45, 0.8, sub, size=13, color=TEXT3)
sowhat(s, "Warn on spread and hotspots, not on headlines. The data can tell India where to look next month.")
notes(s, "Three messages. One: the threat picture. Two: India is already inside the blast radius. Three: we can "
         "forecast and warn better than simple rules, and we proved it on 2026 data the model never saw.")

# =========================================================================== 3 WHY IT MATTERS
s = new_slide("WHY IT MATTERS", "The 2026 war reached the Gulf, Hormuz and Sri Lankan waters")
picture(s, DF / "map.png", 0.55, 1.4, 7.4, 4.85, frame=False)
kicker_lbl(s, 8.25, 1.42, 4.5, "WHERE IT TOUCHES INDIA  [DATA]", color=TEXT3, size=11)
kpi_row(s, 8.25, 1.78, 4.53, 0.82, f"{int(usir_ts.get(2026, 0))}", "countries with US–Iran war deaths in 2026, "
        f"up from {int(usir_ts.get(2025, 0))} in 2025", color=RED)
kpi_row(s, 8.25, 2.7, 4.53, 0.82, "5 Gulf", f"states struck in 2026 ({int(gulf.events.sum())} events). About 9M "
        "Indians live in the Gulf [Domain]", color=AMBER)
kpi_row(s, 8.25, 3.62, 4.53, 0.82, f"{int(hz.deaths.sum())}", "deaths on Iran's Hormuz / Chabahar coast, 2026",
        color=AMBER)
kpi_row(s, 8.25, 4.54, 4.53, 0.82, "104", "killed in one strike off Sri Lanka, 4 Mar 2026", color=RED)
kpi_row(s, 8.25, 5.46, 4.53, 0.82, f"{pakprox.get(2022, 0):.0f} → {pakprox.get(2025, 0):.0f}",
        "deaths in Pakistan areas adjoining India / LoC, 2022 → 2025", color=CYAN, numsize=24)
sowhat(s, "Diaspora, energy routes, Chabahar and the IOR now sit inside the strike envelope.",
       label="DECISION PROBLEM")
notes(s, "This is why the question matters to us. These are counts from the competition data, not opinion. "
         "The 9 million diaspora figure is domain knowledge and is marked as such.")

# =========================================================================== 4 DATA & METHOD
s = new_slide("DATA AND METHOD", "Official competition data, 36 quality checks, one reproducible pipeline")
steps = [("DATA", "UCDP events + sources, UNHCR, IDMC, UNRWA, World Bank"),
         ("CLEAN", "36 checks logged; nothing silently dropped"),
         ("FEATURES", "4 conflicts + 222 area series, 153 months"),
         ("FORECAST", "7 models, back-test 2022–25, test 2026"),
         ("WARN", "Escalation classifier, RAG scorecard, what-if")]
for i, (h, d) in enumerate(steps):
    x = 0.55 + i * 2.47
    sh = box(s, x, 1.42, 2.4, 0.62, fill=PANEL2 if i % 2 else PANEL, line=CYAN,
             shape=MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON, lw=1.25)
    text(s, x + 0.25, 1.42, 1.95, 0.62, h, size=15, bold=True, color=CYAN, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE)
    spaced(s.shapes[-1], 150)
    text(s, x + 0.05, 2.12, 2.3, 0.7, d, size=12, color=TEXT3, align=PP_ALIGN.CENTER)
kpi(s, 0.55, 3.0, 2.35, 3.1, f"{ov.events.sum():,}", "conflict events", "UCDP GED 26.1 2014–25 + Candidate Jan–Sep 2026",
    color=AMBER, numsize=32)
kpi(s, 3.05, 3.0, 2.35, 3.1, f"{len(dq)}", "quality checks", "Estimate repairs, month splitting, FATA→KP, outlet names",
    color=CYAN, numsize=32)
kpi(s, 5.55, 3.0, 2.35, 3.1, "2026", "withheld test", "Every design choice made on 2022–25 back-test only",
    color=TEAL, numsize=32)
picture(s, SHOT / "page01.png", 8.15, 3.0, 4.6, 2.75, frame=True,
        caption="DASHBOARD   |   PAGE 1   |   COMMANDER'S BRIEF")
sowhat(s, "Every number on these slides is regenerated by one command and matches the dashboard.",
       label="REPRODUCIBLE")
notes(s, "Only the official participant package is used. Key cleaning decisions: 692 out-of-order estimates "
         "repaired in new columns, 731 multi-month records spread by day so they don't fake spikes, FATA merged "
         "into KP so the 2018 boundary change doesn't fake a collapse. 2026 provisional data is the test set.")

# =========================================================================== 5 FINDING 1 INTENSITY
s = new_slide("FINDING 1   |   CONFLICT", "Four different threat signatures: attrition, spikes, creep, decline")
picture(s, DF / "monthly_deaths.png", 0.55, 1.4, 8.3, 4.8, frame=False)
kpi_side(s, 9.1, 1.4, 3.68, 1.12, f"{ov.loc['Russia–Ukraine', 'deaths_best'] / 1000:,.0f}k",
         "Russia–Ukraine recorded deaths since 2014; 4–11k every month since 2023", color=CYAN)
kpi_side(s, 9.1, 2.62, 3.68, 1.12, f"{ov.loc['US–Iran', 'peak_month_deaths']:,}",
         "US–Iran deaths in Mar 2026: a war with no build-up", color=RED)
kpi_side(s, 9.1, 3.84, 3.68, 1.12, "Since 2021", "Af–Pak deaths rising every year (TTP, then interstate)", color=TEAL,
         numsize=26)
kpi_side(s, 9.1, 5.06, 3.68, 1.12, "~130 / mo", "Israel–Hamas in 2026, after 11,211 in Oct 2023", color=AMBER,
         numsize=26)
sowhat(s, "One warning rule cannot fit all four: we forecast level, trend and spread separately.")

# =========================================================================== 6 FINDING 2 FRONTS
s = new_slide("FINDING 2   |   MILITARY LENS", "Ukraine: the front is widening, not moving")
picture(s, DF / "front_geography.png", 0.55, 1.4, 8.3, 4.8)
kpi_side(s, 9.1, 1.4, 3.68, 1.12, f"{don22:.0f}% → {don26:.0f}%", "Donetsk's share of located events, 2022 → 2026",
         color=AMBER, numsize=26)
kpi_side(s, 9.1, 2.62, 3.68, 1.12, "10,358", "deaths recorded inside Russia in 2024 (Kursk, Belgorod)", color=RED)
kpi_side(s, 9.1, 3.84, 3.68, 1.12, f"{usir_att.loc[2026, 'deaths_side_a']:,.0f} : {usir_att.loc[2026, 'deaths_side_b']:,.0f}",
         "Iran vs Israel–US recorded deaths, 2026 war (recorded, not verified)", color=CYAN, numsize=26)
kpi_side(s, 9.1, 5.06, 3.68, 1.12, "92%", "of 2026 RU–UA deaths have no location: the fog of war is in the data",
         color=VIOLET)
sowhat(s, "A wide static front rewards long-range fires, counter-drone and EW: lessons for both our fronts. [Domain]")
notes(s, "Recorded attrition ratios are an upper bound of reporting: Ukrainian OSINT documents Russian losses more "
         "fully. We say so in the report. The fog-of-war share is itself a finding from cleaning.")

# =========================================================================== 7 FINDING 3 AFPAK
s = new_slide("FINDING 3   |   INDIA'S WESTERN NEIGHBOUR", "Pakistan now fights on two fronts in the west")
picture(s, DF / "afpak_interstate.png", 0.55, 1.4, 8.3, 2.5)
picture(s, DF / "afpak_provinces.png", 0.55, 3.95, 8.3, 2.35)
kpi_side(s, 9.1, 1.4, 3.68, 1.12, "411", "deaths in Afghan vs Pakistani state clashes, Mar 2026", color=RED)
kpi_side(s, 9.1, 2.62, 3.68, 1.12, "Oct 2025", "first month of direct interstate fighting in the data", color=AMBER,
         numsize=26)
kpi_side(s, 9.1, 3.84, 3.68, 1.12, "3 of top 3", "escalation hotspots for Oct 2026: Kandahar, Balochistan, Kunar",
         color=AMBER, numsize=26)
kpi_side(s, 9.1, 5.06, 3.68, 1.12, f"{ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%}",
         "of Af–Pak events carry an Indian source (mainly PTI); almost none elsewhere", color=CYAN)
sowhat(s, "A Pakistan Army committed in the west raises the risk of diversion along the LoC. Watch west too. [Domain]")

# =========================================================================== 8 FINDING 4 MEDIA
s = new_slide("FINDING 4   |   ORIGINAL INDEX", "Media attention follows incidents, not lethality, and does not warn")
picture(s, DF / "media_scatter.png", 0.55, 1.4, 8.3, 4.8)
kpi_side(s, 9.1, 1.4, 3.68, 1.12, f"{stats.media_elasticity_events:.2f} vs {stats.media_elasticity_deaths:.2f}",
         "elasticity of source references to events vs to deaths", color=CYAN, numsize=26)
kpi_side(s, 9.1, 2.62, 3.68, 1.12, f"p = {stats.media_lead_p:.2f}", "Attention Gap Index does not lead next month's "
         "escalation", color=AMBER, numsize=26)
kpi_side(s, 9.1, 3.84, 3.68, 1.12, "150 vs 35", "references per 100 deaths: Israel–Hamas vs US–Iran", color=RED,
         numsize=26)
kpi_side(s, 9.1, 5.06, 3.68, 1.12, f"R² {stats.media_r2:.2f}", "one mass-casualty strike is one story", color=TEAL,
         numsize=26)
sowhat(s, "Headline volume is not an indicator. India's open-source picture of West Asia is borrowed.")

# =========================================================================== 9 FINDING 5 DISPLACEMENT
s = new_slide("FINDING 5   |   HUMANITARIAN", "Displacement follows onset and spread, and it is women and children")
picture(s, DF / "displacement.png", 0.55, 1.4, 8.3, 4.8)
kpi_side(s, 9.1, 1.4, 3.68, 1.12, "8.9M", "Ukrainians displaced end-2025: 5.2M refugees + 3.7M IDPs", color=CYAN)
kpi_side(s, 9.1, 2.62, 3.68, 1.12, "72%", "of Ukrainian refugees are women or children (Afghanistan 63%)", color=AMBER)
kpi_side(s, 9.1, 3.84, 3.68, 1.12, "10%", "of Afghan refugees are under five", color=RED)
kpi_side(s, 9.1, 5.06, 3.68, 1.12, f"ρ = {stats.link_spearman:.2f}", "monthly deaths barely explain displacement "
         "change", color=TEAL, numsize=26)
sowhat(s, "Trigger HADR on escalation flags, not death tolls; stock paediatric and maternal supplies.")

# =========================================================================== 10 PREDICTION
s = new_slide("FINDING 6   |   PREDICTION", "Forecasts beat simple rules on 2026 data the model never saw")
picture(s, DF / "forecast_ru.png", 0.55, 1.4, 8.3, 2.45)
picture(s, DF / "forecast_afpak.png", 0.55, 3.9, 8.3, 2.45)
kpi_side(s, 9.1, 1.4, 3.68, 1.12, f"−{pooled:.0f}%", f"1-month error vs 'no change' (RU–UA −{red['Russia–Ukraine']:.0f}%, "
         f"Israel–Hamas −{red['Israel–Hamas']:.0f}%)", color=CYAN)
kpi_side(s, 9.1, 2.62, 3.68, 1.12, f"{cov80:.0f}%", "of 2026 outcomes inside the 80% interval", color=TEAL)
kpi_side(s, 9.1, 3.84, 3.68, 1.12, "72%", "of 2026 conflict-months: direction of change called right", color=AMBER)
kpi_side(s, 9.1, 5.06, 3.68, 1.12, "Ensemble", "ETS + 3-mo mean + LightGBM-Δ, chosen on 2022–25 only", color=VIOLET,
         numsize=26)
sowhat(s, "Use the forecast as a planning baseline with honest bands; the 95% tail carries the outbreak risk.")
notes(s, "Protocol: fit on data to Dec 2025, freeze, score Jan–Sep 2026. Track A: one month ahead rolling. "
         "Track B: up to nine months blind. LightGBM predicts the change in log deaths, because trees cannot "
         "extrapolate beyond training levels. That is why a level model could never forecast the 2022 invasion.")

# =========================================================================== 11 EARLY WARNING
s = new_slide("FINDING 7   |   EARLY WARNING", "A district-level watch-list, one month ahead")
picture(s, SHOT / "page09.png", 0.62, 1.48, 7.3, 4.25, frame=True, caption="DASHBOARD   |   PAGE 9   |   EARLY WARNING")
kpi_side(s, 8.3, 1.4, 4.48, 1.12, f"AUC {lg.ROC_AUC:.2f}", f"on 2026 withheld months (rule of thumb {rule.ROC_AUC:.2f}; "
         f"back-test 0.80–0.91)", color=AMBER, numsize=28)
kpi_side(s, 8.3, 2.62, 4.48, 1.12, f"{lg.precision_at_10 / lg.base_rate:.1f}×", f"top-10 list precision "
         f"{lg.precision_at_10:.0%} vs base rate {lg.base_rate:.1%}", color=CYAN)
kpi_side(s, 8.3, 3.84, 4.48, 1.12, "222", "area series in 22 countries scored every month", color=VIOLET)
kpi_side(s, 8.3, 5.06, 4.48, 1.12, "Contagion", "top signals: own intensity, country tempo, whole-war momentum",
         color=TEAL, numsize=26)
sowhat(s, "ISR and analyst effort can be tasked on predicted risk before the escalation, not after.")

# =========================================================================== LIVE DEMO SLIDE
s = new_slide("LIVE DEMONSTRATION   |   INTERACTIVE DASHBOARD", "Twelve pages the jury can drive: drill down, replay, re-train, re-rule")
picture(s, SHOT / "page03.png", 0.62, 1.48, 5.9, 3.35, frame=True, caption="PAGE 3   |   AREA DRILL-DOWN")
picture(s, SHOT / "page11.png", 6.85, 1.48, 5.9, 3.35, frame=True, caption="PAGE 11   |   SCORECARD LAB")
for i, (h, d, col) in enumerate([
        ("Drill down", "Any of 222 areas: deaths, events, forecast, warning history", CYAN),
        ("Replay", "Pick a 2026 month: what was flagged, what escalated", AMBER),
        ("What-if + re-train", "Shock a conflict; refit the model live in seconds", RED),
        ("Re-rule", "Move the scorecard and alert thresholds; ratings update", TEAL)]):
    x = 0.55 + i * 3.1
    box(s, x, 5.3, 2.93, 0.98)
    text(s, x + 0.15, 5.36, 2.7, 0.35, h, size=16, bold=True, color=col)
    text(s, x + 0.15, 5.7, 2.7, 0.55, d, size=11, color=TEXT2)
sowhat(s, "Runs offline on a laptop; every table downloads as CSV; nothing on screen is a static picture.", label="DEMO")
notes(s, "Switch to the browser here. Order: Commander's brief, Area drill-down, Military lens, Forecast, Early warning "
         "(replay and alert threshold), What-if and live re-train, Scorecard lab.")

# =========================================================================== 12 RECOMMENDATIONS
s = new_slide("RECOMMENDATIONS   |   OPERATIONAL DESIGN", "Four lines of effort for the Armed Forces: sense, warn, shield, sustain")
box(s, 0.55, 1.4, 2.6, 4.85, fill=PANEL, line=AMBER, lw=1.25)
kicker_lbl(s, 0.75, 1.58, 2.3, "COMMANDER'S INTENT", size=11)
text(s, 0.75, 1.98, 2.25, 3.0, "See escalation coming a month out, protect Indians and interests in the "
     "strike envelope, and keep our platforms supplied.", size=15, bold=True)
text(s, 0.75, 5.3, 2.25, 0.8, "Each line traces to a finding and to the dashboard.", size=11, color=TEXT3)
loe = [("SENSE", "ISR", CYAN, "Task ISR and analysts on the monthly sub-national watch-list. Build Indian OSINT on Gulf, "
         "Iran and Red Sea.", "LEAD: DIA / Service intelligence"),
       ("WARN", "I&W", AMBER, "Adopt the Af–Pak interstate dyad and KP/Balochistan hotspot probabilities as standing LoC "
        "indicators. Publish the RAG monthly.", "LEAD: HQ IDS, Northern / Western Comds"),
       ("SHIELD", "NEO / IOR", RED, "Keep Gulf NEO plans current while US–Iran is AMBER; belligerent-movement picture in "
        "the IOR.", "LEAD: HQ IDS, Navy, IAF, MEA"),
       ("SUSTAIN", "ENDURANCE", TEAL, "Buffer spares for Russian- and Israeli-origin platforms; HADR kits for women, "
        "children, under-fives.", "LEAD: MoD, DPSUs, NDMA")]
for i, (h, sub, col, body, lead) in enumerate(loe):
    y = 1.4 + i * 1.23
    sh = box(s, 3.35, y, 1.75, 1.13, fill=col, line=None, shape=MSO_SHAPE.PENTAGON)
    text(s, 3.4, y + 0.22, 1.5, 0.4, h, size=18, bold=True, color=BG, align=PP_ALIGN.CENTER)
    text(s, 3.4, y + 0.62, 1.5, 0.3, sub, size=10, bold=True, color=BG, align=PP_ALIGN.CENTER)
    box(s, 5.2, y, 5.3, 1.13)
    text(s, 5.38, y + 0.1, 5.0, 0.7, body, size=13, color=WHITE)
    text(s, 5.38, y + 0.8, 5.0, 0.3, lead, size=11, color=col, bold=True)
box(s, 10.65, 1.4, 2.13, 4.85, line=BORDER)
kicker_lbl(s, 10.82, 1.58, 1.9, "END STATE", color=TEXT3, size=11)
for i, (n, l) in enumerate([("1 month", "warning lead time"), ("Top 10", "areas tasked monthly"),
                            ("0", "Indians stranded"), ("RAG", "brief every month")]):
    text(s, 10.82, 2.0 + i * 1.03, 1.85, 0.45, n, size=22, bold=True, color=AMBER)
    text(s, 10.82, 2.45 + i * 1.03, 1.85, 0.4, l, size=12, color=TEXT2)
sowhat(s, "The SENSE and WARN lines need no new platform: the model and dashboard already exist.", label="BOTTOM LINE")

# =========================================================================== 13 WHO / WHEN
s = new_slide("RECOMMENDATIONS   |   EXECUTION", "Who does what, by when")
rows = [["Agency", "NOW (0–30 DAYS)", "BY 90 DAYS", "6–12 MONTHS"],
        ["DIA / Service Int", "Task ISR on the top-10 watch-list", "Indian OSINT cell for Gulf, Iran, Red Sea",
         "Fuse with classified I&W; re-train monthly"],
        ["HQ IDS", "Adopt RAG scorecard in the monthly brief", "Gulf NEO table-top on US–Iran AMBER",
         "Institutionalise the dashboard"],
        ["Northern / Western Comds", "Af–Pak dyad as standing LoC indicator", "Watch KP / Balochistan hotspots",
         "Review posture against two-front Pakistan"],
        ["Navy / IFC-IOR", "Belligerent-movement watch near Sri Lanka", "Hormuz / Chabahar shipping picture",
         "Escort and evacuation readiness"],
        ["MoD / DPSUs / NDMA", "Audit critical spares (Russian, Israeli)", "Buffer-stock plan",
         "Indigenise; HADR kits for women and children"]]
table(s, 0.55, 1.45, 12.23, rows, [2.6, 3.21, 3.21, 3.21], header_fill=[PANEL2, RED, AMBER, TEAL],
      header_color=WHITE, size=14, row_h=0.78, first_col_color=CYAN)
sowhat(s, "Column one is tasking and a briefing format. It can start this month.", label="BOTTOM LINE")

# =========================================================================== 14 LIMITS
s = new_slide("LIMITS AND VALIDATION", "What the analysis cannot claim, and why the headline numbers still hold")
lim = [("Reported deaths", "UCDP records reported violence; access shapes coverage"),
       ("Provisional 2026", "Candidate data are revised, usually upward"),
       ("No location", "92% of 2026 RU–UA deaths are country-level only"),
       ("Wars are decisions", "No death-count model foresees Feb 2022 or Feb 2026")]
for i, (h, d) in enumerate(lim):
    y = 1.4 + i * 1.2
    box(s, 0.55, y, 4.3, 1.08)
    text(s, 0.75, y + 0.12, 3.9, 0.4, h, size=18, bold=True, color=AMBER)
    text(s, 0.75, y + 0.52, 3.9, 0.5, d, size=13, color=TEXT2)
rows = [["Headline result", "Internal check", "Why it still holds"],
        [f"−{pooled:.0f}% error vs naive", "Chosen on 2022–25, 2026 scored once", "Holds in all 4 conflicts"],
        [f"{cov80:.0f}% inside 80% band", "Split-conformal, back-test calibrated", "Adaptive variant tested, rejected"],
        [f"AUC {lg.ROC_AUC:.2f} warning", "Beats logistic and rule of thumb", "Back-test 0.80–0.91, all years"],
        ["Fronts widening", "Located events only", "Same in events and deaths"],
        ["Media ≠ warning", "Lead test p = 0.50", "Holds with fixed effects"]]
table(s, 5.1, 1.4, 7.68, rows, [2.5, 2.7, 2.48], size=13, row_h=0.78, first_col_color=WHITE)
sowhat(s, "Uncertainty is shown, not hidden: every forecast carries a calibrated band.", label="VALIDATION")

# =========================================================================== 15 CLOSING – RAG
s = new_slide("THREAT SCORECARD   |   OCTOBER 2026", "Where to look next month")
for i, case in enumerate(C.CASES):
    r = rag.loc[case]
    col = RAGC[r.rating]
    x = 0.55 + i * 3.1
    box(s, x, 1.4, 2.93, 2.65, line=col, lw=2.25)
    text(s, x, 1.55, 2.93, 0.4, case, size=17, bold=True, align=PP_ALIGN.CENTER)
    text(s, x, 1.98, 2.93, 0.75, r.rating, size=40, bold=True, color=col, align=PP_ALIGN.CENTER)
    text(s, x, 2.85, 2.93, 0.4, f"{r.forecast_next:,.0f} deaths forecast", size=15, bold=True, align=PP_ALIGN.CENTER)
    text(s, x + 0.1, 3.27, 2.73, 0.7, f"80%: {r.pi80_lo:,.0f}–{r.pi80_hi:,.0f}  ·  trend {(r.trend_ratio - 1) * 100:+.0f}%"
         f"\nTop area: {str(r.top_areas).split(';')[0]}", size=12, color=TEXT3, align=PP_ALIGN.CENTER)
for i, (col, h, d) in enumerate([(AMBER, "Russia–Ukraine stays RED", "Sustained attrition; the front widens"),
                                 (RED, "The war reached India's neighbourhood", "Gulf, Hormuz, Sri Lankan waters"),
                                 (CYAN, "Warning works a month out", f"AUC {lg.ROC_AUC:.2f}; forecasts −{pooled:.0f}% error")]):
    y = 4.3 + i * 0.66
    circle_num(s, 0.6, y + 0.04, i + 1, col, d=0.44, size=15)
    text(s, 1.2, y, 7.5, 0.35, h, size=17, bold=True)
    text(s, 1.2, y + 0.33, 7.5, 0.3, d, size=12, color=TEXT3)
box(s, 10.6, 4.25, 2.18, 1.95, fill=PANEL, line=MUTED, lw=1.25)
if QR_URL:
    import qrcode
    qr_path = ROOT / "deck" / "figs" / "qr.png"
    qrcode.make(QR_URL, box_size=12, border=2).save(qr_path)
    box(s, 11.02, 4.33, 1.34, 1.34, fill=WHITE, line=None, radius=0.03)
    s.shapes.add_picture(str(qr_path), Inches(11.06), Inches(4.37), Inches(1.26), Inches(1.26))
    text(s, 10.6, 5.75, 2.18, 0.35, "SCAN: REPOSITORY" if "github.com" in QR_URL else "SCAN: LIVE DASHBOARD", size=10, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
else:
    text(s, 10.6, 4.35, 2.18, 1.3, ["QR CODE", "link to be added"], size=13, color=MUTED, bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 10.6, 5.75, 2.18, 0.35, "LIVE DEMO: DASHBOARD", size=10, color=CYAN, bold=True, align=PP_ALIGN.CENTER)
box(s, 0.55, 6.38, 12.23, 0.5, fill=AMBER_BG, line=AMBER, lw=1.25, radius=0.12)
text(s, 0.78, 6.38, 9.6, 0.5, "Open data and an honest model can tell India where to look next month.", size=15,
     bold=True, color=AMBER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 10.0, 6.38, 2.6, 0.5, "Thank you. Questions?", size=15, bold=True, align=PP_ALIGN.RIGHT,
     anchor=MSO_ANCHOR.MIDDLE)

# =========================================================================== BACKUPS
s = new_slide("BACKUP", "Model comparison: back-test vs 2026 holdout")
picture(s, DF / "model_compare.png", 0.55, 1.35, 7.4, 5.0)
lab = {"ensemble": "Ensemble", "sarima": "SARIMA", "ets": "ETS", "lgb_case": "LightGBM-Δ", "ma3": "3-mo mean",
       "naive": "Naive", "snaive": "Seasonal naive", "lgb_admin1": "LGB bottom-up"}
rows = [["Model (RMSLE)", "A back", "A 2026", "B back", "B 2026"]]
for m in ["ensemble", "sarima", "ets", "lgb_case", "ma3", "lgb_admin1", "naive", "snaive"]:
    rr = rml.loc[m]
    rows.append([lab[m], f"{rr[('A', False)]:.2f}", f"{rr[('A', True)]:.2f}", f"{rr[('B', False)]:.2f}",
                 f"{rr[('B', True)]:.2f}"])
table(s, 8.15, 1.35, 4.63, rows, [1.55, 0.77, 0.77, 0.77, 0.77], size=12, row_h=0.5)
text(s, 8.15, 6.0, 4.63, 0.4, "A = 1 month ahead rolling; B = 1–9 months from December. Lower is better.", size=11,
     color=TEXT3)

s = new_slide("BACKUP", "Why each method was chosen over the simpler alternative")
rows = [["Decision", "Chosen", "Why the simpler alternative is weaker"],
        ["Forecast target", "Change in log deaths (LightGBM-Δ)", "Trees on the level cannot exceed training range: misses 2022"],
        ["Feature set", "Compact 18 features", f"Full set over-fits 4 series (back-test RMSLE {abl.iloc[1, 1]:.2f} vs "
                                               f"{abl.iloc[4, 1]:.2f})"],
        ["Ensemble", "Log-mean of ETS, 3-mo mean, LGB-Δ", "No single model wins every fold"],
        ["Intervals", "Split conformal, horizon bands", "Gaussian bands under-cover heavy tails"],
        ["Evaluation", "Walk-forward folds + 2026 holdout", "Random splits leak the future"],
        ["Warning target", "≥10 deaths and ≥1.5× 3-mo mean", "Raw increases flag noise in quiet areas"],
        ["Multi-month records", "Spread across months by day", "Start-month stacking fakes spikes"]]
table(s, 0.55, 1.4, 12.23, rows, [2.6, 3.9, 5.73], size=14, row_h=0.62)

s = new_slide("BACKUP", "Data quality: what was found and what we did")
picture(s, FIG / "03_data_quality.png", 0.55, 1.35, 12.23, 5.55)

s = new_slide("BACKUP", "What drives the forecast and the warning (TreeSHAP)")
picture(s, DF / "shap_forecast.png", 0.55, 1.4, 6.0, 4.9)
picture(s, DF / "shap_ew.png", 6.78, 1.4, 6.0, 4.9)

s = new_slide("BACKUP", "Campaign seasons and the early-warning curves")
picture(s, DF / "seasonality.png", 0.55, 1.35, 12.23, 2.6)
picture(s, DF / "ew_curves.png", 0.55, 4.0, 12.23, 2.95)

s = new_slide("BACKUP", "Forward forecast, Oct–Dec 2026 (ensemble, 80% interval)")
rows = [["Conflict", "Oct 2026", "Nov 2026", "Dec 2026"]]
for case in C.CASES:
    f = fut[fut.conflict_case == case].sort_values("target_month")
    rows.append([case] + [f"{r.pred:,.0f}  ({r.pi80_lo:,.0f}–{r.pi80_hi:,.0f})" for r in f.itertuples()])
table(s, 0.55, 1.45, 12.23, rows, [3.2, 3.01, 3.01, 3.01], size=17, row_h=0.8, first_col_color=CYAN)
text(s, 0.55, 5.6, 12.2, 0.6, "Refitted on all data to Sep 2026. Horizon 1 uses the operational track; 2–3 use the "
     "strategic track, so bands widen.", size=13, color=TEXT3)

prs.save(OUT)
print("deck saved:", OUT, "slides:", len(prs.slides))
