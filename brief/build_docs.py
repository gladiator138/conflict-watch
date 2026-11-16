"""Build the one-page commander's brief and the Q&A / speaker sheet (HTML; PDF via brief/to_pdf.js).

    python brief/build_docs.py
    NODE_PATH=$(npm root -g) node brief/to_pdf.js
"""
from __future__ import annotations

import sys
from pathlib import Path

import markdown
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config as C  # noqa: E402

TB = C.TAB_DIR
OUT = ROOT / "brief"

rag = pd.read_csv(TB / "rag_scorecard.csv").set_index("conflict_case")
ew = pd.read_csv(TB / "early_warning_scores.csv")
lg = ew[(ew.year == 2026) & (ew.model == "LightGBM classifier")].iloc[0]
rule = ew[(ew.year == 2026) & (ew.model.str.startswith("Rule"))].iloc[0]
sc = pd.read_csv(TB / "forecast_scores.csv")
hA = sc[(sc.fold == 2026) & (sc.track == "A")]
nv = hA[hA.model == "naive"].set_index("conflict_case").MAE
en = hA[hA.model == "ensemble"].set_index("conflict_case").MAE
pooled = (1 - en.sum() / nv.sum()) * 100
red = (1 - en / nv) * 100
preds = pd.read_parquet(C.PROCESSED / "forecast_preds.parquet")
e26 = preds[(preds.model == "ensemble") & (preds.fold == 2026)]
cov80 = ((e26.actual >= e26.pi80_lo) & (e26.actual <= e26.pi80_hi)).mean() * 100
stats = pd.read_csv(TB / "insight_stats.csv").iloc[0]
abl = pd.read_csv(TB / "ablation_lgb.csv")
RC = {"RED": "#FF4D5E", "AMBER": "#F0B03A", "GREEN": "#35C2A6"}

CSS = """
@page { size: A4; margin: 8mm 10mm; }
* { box-sizing: border-box; }
body { font-family: Calibri, Carlito, 'Segoe UI', Arial, sans-serif; color: #1b2733; font-size: 9.4pt; line-height: 1.3; margin: 0; }
.hdr { background: #07131F; color: #fff; padding: 9px 14px 10px 14px; border-radius: 6px; }
.hdr .k { color: #F0B03A; font-weight: 700; letter-spacing: 2px; font-size: 8pt; }
.hdr h1 { margin: 2px 0 2px 0; font-size: 18pt; }
.hdr .m { color: #9FB2C6; font-size: 8.4pt; }
h2 { font-size: 10.5pt; color: #07131F; border-bottom: 2px solid #F0B03A; margin: 9px 0 5px 0; padding-bottom: 2px; letter-spacing: .5px; }
h3 { font-size: 10.5pt; margin: 10px 0 4px 0; }
ul, ol { margin: 3px 0 3px 0; padding-left: 16px; } li { margin: 1.5px 0; }
table { border-collapse: collapse; width: 100%; font-size: 8.7pt; margin: 3px 0; }
th { background: #0F2236; color: #fff; text-align: left; padding: 3px 5px; }
td { border-bottom: 1px solid #d6dee8; padding: 3px 5px; vertical-align: top; }
.rag { display: flex; gap: 6px; margin: 6px 0 2px 0; }
.rag div { flex: 1; background: #0F2236; color: #fff; border-radius: 6px; padding: 5px 8px; border: 2px solid; }
.rag b.r { font-size: 14pt; display: block; }
.rag span { font-size: 8pt; color: #D5DEE8; }
.d { background: #35C2A6; color: #07131F; font-size: 7pt; font-weight: 700; padding: 0 4px; border-radius: 3px; }
.o { background: #A794FF; color: #07131F; font-size: 7pt; font-weight: 700; padding: 0 4px; border-radius: 3px; }
.foot { margin-top: 6px; font-size: 7.5pt; color: #5E7B99; text-align: center; letter-spacing: 1px; }
.bluf { background: #fff8e8; border-left: 4px solid #F0B03A; padding: 5px 9px; }
.q { font-weight: 700; color: #07131F; margin-top: 7px; }
.a { margin: 1px 0 0 0; }
.cols { display: flex; gap: 14px; } .cols > div { flex: 1; }
"""


def page(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>")


# ----------------------------------------------------------------------------------- commander's brief
cards = "".join(
    f"<div style='border-color:{RC[rag.loc[c, 'rating']]}'><b>{c}</b>"
    f"<b class='r' style='color:{RC[rag.loc[c, 'rating']]}'>{rag.loc[c, 'rating']}</b>"
    f"<span>{rag.loc[c, 'forecast_next']:,.0f} deaths forecast Oct 2026<br/>80%: {rag.loc[c, 'pi80_lo']:,.0f}–"
    f"{rag.loc[c, 'pi80_hi']:,.0f} · top area {str(rag.loc[c, 'top_areas']).split(' (')[0]}</span></div>"
    for c in C.CASES)

brief = f"""
<div class="hdr"><div class="k">COMMANDER'S BRIEF &nbsp;|&nbsp; DATA ANALYTICS COMPETITION 2026 &nbsp;|&nbsp; AS OF 30 SEP 2026</div>
<h1>Conflict Watch: where deaths rise next, and what it means for India</h1>
<div class="m">Maj Shivam Mehta · Capt Siddharth Sangwan · Capt Sahil Singh &nbsp;·&nbsp; Source: official competition package (UCDP, UNHCR, IDMC,
UNRWA, World Bank) &nbsp;·&nbsp; <span class="d">DATA</span> computed from the files &nbsp;
<span class="o">DOMAIN</span> expert reasoning</div></div>

<h2>BOTTOM LINE UP FRONT</h2>
<div class="bluf">Russia–Ukraine stays <b style="color:#d7263d">RED</b>; Afghanistan–Pakistan and US–Iran are
<b style="color:#c77d00">AMBER</b>; Israel–Hamas is <b style="color:#1f9e83">GREEN</b>. The 2026 US–Iran war reached
India's neighbourhood (Gulf, Hormuz, Sri Lankan waters). Our models, tested on unseen 2026 data, forecast
monthly deaths {pooled:.0f}% more accurately than "no change" and flag escalating districts a month ahead
(AUC {lg.ROC_AUC:.2f}). <b>Use them to task ISR, keep Gulf NEO plans current, and watch Pakistan's western front.</b></div>

<h2>THREAT ASSESSMENT – OCTOBER 2026</h2>
<div class="rag">{cards}</div>
<ul>
<li><b>Russia–Ukraine:</b> sustained attrition at 4–11k deaths a month since 2023. The front is widening, not moving:
Donetsk's share of located events fell from 55% to 30% (2022–26) while Zaporizhzhia, Dnipropetrovsk, Sumy and Russia's
border oblasts rose. <span class="d">DATA</span></li>
<li><b>Afghanistan–Pakistan:</b> deaths in KP have risen every year since 2021, and the two states have fought each other
directly since Oct 2025 (411 deaths in Mar 2026). Kandahar, Balochistan and Kunar head the escalation watch-list.
<span class="d">DATA</span></li>
<li><b>US–Iran:</b> calm now (26 forecast), but the Feb–Mar 2026 war came with no build-up and hit 14 countries.
Recorded losses: Iran 1,274 vs Israel–US 11. <span class="d">DATA</span></li>
<li><b>Israel–Hamas:</b> about 130 a month in 2026; the war reached Qatar in Sep 2025. <span class="d">DATA</span></li>
</ul>

<h2>INDIA IMPACT</h2>
<table><tr><th style="width:18%">Theatre</th><th style="width:44%">Evidence <span class="d">DATA</span></th><th>Implication <span class="o">DOMAIN</span></th></tr>
<tr><td><b>Western front</b></td><td>Af–Pak interstate clashes since Oct 2025; deaths in Pakistan areas adjoining India rose 2 → 52 (2022–25)</td><td>Pakistan Army stretched west: risk of diversionary LoC activity, TTP/IS-K spill-over</td></tr>
<tr><td><b>Gulf / Hormuz</b></td><td>5 Gulf states struck in 2026 (25 events); 299 deaths on Iran's Hormuz/Chabahar coast; 945 deaths in Yemen in 2025</td><td>~9M diaspora needs NEO readiness; crude/LPG via Hormuz; Chabahar and INSTC exposed</td></tr>
<tr><td><b>IOR</b></td><td>104 killed in one strike off Sri Lanka, 4 Mar 2026</td><td>Belligerents operating in India's maritime neighbourhood</td></tr>
<tr><td><b>Supply chains</b></td><td>RU–UA at 4–11k deaths/month; Israel at war since 2023</td><td>Spares and deliveries for Russian- and Israeli-origin platforms at risk</td></tr>
<tr><td><b>Information</b></td><td>Indian outlets cover 17% of Af–Pak events, about 0% elsewhere; media volume does not lead escalation (p = {stats.media_lead_p:.2f})</td><td>India's open-source picture of West Asia is borrowed; do not warn on headlines</td></tr>
</table>

<h2>RECOMMENDATIONS</h2>
<table><tr><th style="width:12%">Line</th><th>Action</th><th style="width:21%">Lead <span class="o">DOMAIN</span></th><th style="width:11%">When</th></tr>
<tr><td><b>SENSE</b></td><td>Task ISR and analysts on the monthly sub-national watch-list; build Indian OSINT for Gulf, Iran, Red Sea</td><td>DIA, Service intelligence</td><td>Now / 90 days</td></tr>
<tr><td><b>WARN</b></td><td>Adopt the Af–Pak dyad and KP/Balochistan hotspot probabilities as LoC I&amp;W; publish the RAG monthly</td><td>HQ IDS, N &amp; W Comds</td><td>Now</td></tr>
<tr><td><b>SHIELD</b></td><td>Keep Gulf NEO plans current while US–Iran is AMBER; belligerent-movement picture in the IOR</td><td>HQ IDS, Navy, IAF, MEA</td><td>Now / 90 days</td></tr>
<tr><td><b>SUSTAIN</b></td><td>Buffer and indigenise critical spares; HADR kits for women, children, under-fives</td><td>MoD, DPSUs, NDMA</td><td>6–12 months</td></tr>
</table>

<h2>CONFIDENCE AND LIMITS</h2>
<ul>
<li>Forecasts trained to Dec 2025, scored on Jan–Sep 2026: error −{pooled:.0f}% vs naive (RU–UA −{red['Russia–Ukraine']:.0f}%,
Israel–Hamas −{red['Israel–Hamas']:.0f}%); {cov80:.0f}% of outcomes inside the 80% interval. Escalation top-10 list
{lg.precision_at_10 / lg.base_rate:.1f}× better than random.</li>
<li>UCDP counts <i>reported</i> deaths; 2026 data are provisional; 92% of 2026 RU–UA deaths lack a location; decisions to
start a war (Feb 2022, Feb 2026) are not predictable from death counts.</li>
</ul>
<div class="foot">UNCLASSIFIED – OPEN-SOURCE DATA ONLY &nbsp;|&nbsp; Full method: Conflict Watch analysis report &nbsp;|&nbsp; Live: Conflict Watch dashboard</div>
"""
(OUT / "Commanders_Brief.html").write_text(page("Commander's Brief – Conflict Watch", brief))

# ----------------------------------------------------------------------------------- Q&A + speaker split
QA = [
    ("Problem framing", [
        ("Why forecast deaths and not events?", "Deaths are the measure of harm that planners act on, and the "
         "series is comparable across the four conflicts. Events drive media volume, not lethality, as our index shows."),
        ("Why only these four conflicts?", "They are the competition scope. The pipeline is generic: any UCDP "
         "conflict can be added by extending the case list in config.py."),
    ]),
    ("Data and cleaning", [
        ("Did you change the source data?", "No. Raw CSVs are read-only. Repairs go into new columns (e.g. deaths_low_c) "
         "and every change is in the 36-check data-quality log."),
        ("How did you handle multi-month events?", "731 records span more than one month, including front-wide "
         "aggregates. We spread their deaths across months by day count, otherwise the start month shows a false spike."),
        ("What about out-of-order low/best/high?", "692 rows. We keep best, because it reconciles exactly with the "
         "fatality components, and widen the band to min/max. Raw values are kept."),
        ("Why merge FATA into KP?", "Pakistan merged them in 2018. Without harmonising, FATA would show a fake collapse "
         "and KP a fake surge exactly at the boundary change."),
        ("2026 data are provisional; is the test fair?", "It is the hardest, most realistic test: operational users always "
         "work on provisional data. Revisions usually go upward, which makes our holdout error conservative."),
    ]),
    ("Models and validation", [
        ("Why not a deep-learning model (LSTM)?", "Four series of 153 months is far too little data. Our ablation shows "
         "even a 40-feature LightGBM over-fits. Simpler, regularised models generalise better and are explainable."),
        ("Why does LightGBM predict the change, not the level?", "Trees cannot predict above the highest value seen in "
         "training. A level model trained before 2022 can never forecast the invasion. The change target removes that ceiling: "
         f"back-test RMSLE {abl.iloc[0, 1]:.2f} (level) vs {abl.iloc[4, 1]:.2f} (change, compact)."),
        ("How do you know you didn't tune on 2026?", "All choices (features, ensemble members, interval bands, classifier "
         "features) were made on 2022–25 folds. 2026 was scored once. On Track B SARIMA beat the ensemble in 2026, and we "
         "report that rather than switch."),
        ("Why is RMSLE the selection metric?", "The series differ by three orders of magnitude. RMSE would be dominated "
         "by Russia–Ukraine. RMSLE scores relative error fairly. MAE, RMSE, MAPE, sMAPE and MASE are all reported too."),
        ("Your Af–Pak improvement is only 4%. Why?", "Af–Pak is a steady creep with little month-to-month signal, so "
         "'no change' is already a strong baseline. The ensemble still wins, and the gain is large where it matters (RU–UA, "
         "Israel–Hamas, US–Iran)."),
        ("Why are the 95% intervals so wide?", "The back-test includes the 2022 invasion. A calibrated interval must keep "
         "room for outbreaks. The 80% band, which covered 83% of 2026, is the planning band."),
        ("The model missed the US–Iran war. Isn't that a failure?", "Yes, and we say so. No death-count model can foresee "
         "a decision to go to war. That is why warning also tracks spread and hotspots, and why the scorecard has a "
         "volatility rule."),
        ("How good is the early warning, really?", f"AUC {lg.ROC_AUC:.2f} on 2026 (rule of thumb {rule.ROC_AUC:.2f}); "
         f"top-10 precision {lg.precision_at_10:.0%} vs base rate {lg.base_rate:.1%}. Escalations are rare (4%), so "
         "precision looks low in absolute terms, but it is 3.5× random: it focuses scarce ISR."),
    ]),
    ("Military and India", [
        ("Is the Russia:Ukraine 10:1 ratio real?", "No; it is recorded. Ukrainian OSINT and memorial databases record "
         "Russian deaths more fully. We show it as an upper bound of reporting and caveat it on the slide."),
        ("How do you link the Af–Pak war to the LoC?", "The data show Pakistan fighting on its western front. The LoC link "
         "is domain reasoning, labelled DOMAIN, and we recommend it as an indicator to watch, not a prediction."),
        ("Where does '9 million Indians in the Gulf' come from?", "It is public MEA-order-of-magnitude knowledge, not "
         "from the competition files, and is labelled DOMAIN."),
        ("What would you do with classified data?", "Fuse it as extra features (e.g. movement indicators). The pipeline "
         "already accepts new features; the walk-forward protocol would test their value."),
    ]),
    ("Dashboard and reproducibility", [
        ("Can it run offline at an HQ?", "Yes. Streamlit on a laptop, no internet calls, bundled map outline. One command "
         "rebuilds everything in about 2.5 minutes."),
        ("Can it be updated monthly?", "Drop in the new UCDP month and rerun. The 'live re-train' page refits LightGBM-Δ "
         "in about 2 seconds."),
        ("How was AI used?", "As a coding assistant, which the rules allow. Every number is produced by code in the "
         "repository and every result can be reproduced and checked."),
    ]),
]

qa_html = "".join(f"<h3>{sec}</h3>" + "".join(f"<div class='q'>Q. {q}</div><div class='a'>{a}</div>" for q, a in items)
                  for sec, items in QA)

speak = f"""
<div class="hdr"><div class="k">PRESENTER PACK &nbsp;|&nbsp; DATA ANALYTICS COMPETITION 2026</div>
<h1>Run of show, speaker split and Q&amp;A preparation</h1>
<div class="m">Designed for a Google Meet presentation: share the deck window, then switch to the dashboard tab for the demo.</div></div>

<h2>RUN OF SHOW (ABOUT 12 MINUTES + Q&amp;A)</h2>
<table><tr><th>Time</th><th>Slides / demo</th><th>Speaker</th><th>Key line</th></tr>
<tr><td>0:00–1:30</td><td>1 Cover, 2 BLUF</td><td>Maj Shivam Mehta</td><td>"Four wars, three warning signals, one exposed neighbour."</td></tr>
<tr><td>1:30–2:30</td><td>3 Why it matters</td><td>Maj Shivam Mehta</td><td>"The war reached the Gulf, Hormuz and Sri Lankan waters."</td></tr>
<tr><td>2:30–3:30</td><td>4 Data and method</td><td>Capt Siddharth Sangwan</td><td>"36 checks; 2026 withheld; one command reproduces everything."</td></tr>
<tr><td>3:30–6:00</td><td>5–9 Findings</td><td>Maj Shivam Mehta</td><td>"The front is widening, not moving. Pakistan fights on two fronts."</td></tr>
<tr><td>6:00–7:30</td><td>10–11 Prediction and warning</td><td>Capt Siddharth Sangwan</td><td>"−{pooled:.0f}% error on unseen data; watch-list 3.5× random."</td></tr>
<tr><td>7:30–10:00</td><td>12 <b>LIVE DEMO</b>: brief → drill-down → military → forecast → early warning → what-if → scorecard lab</td><td>Capt Siddharth Sangwan</td><td>"Here is the RED card, and here is where it comes from."</td></tr>
<tr><td>10:00–11:30</td><td>13–14 Recommendations</td><td>Capt Sahil Singh</td><td>"SENSE and WARN need no new platform."</td></tr>
<tr><td>11:30–12:00</td><td>15 Limits, 16 Scorecard</td><td>Capt Sahil Singh</td><td>"Open data and an honest model tell India where to look next month."</td></tr>
</table>
<p><b>Speaker split (proposed):</b> <b>Maj Shivam Mehta</b> opens: bottom line, why it matters for India, and the military findings. <b>Capt Siddharth Sangwan</b> covers data, models and runs the live demo. <b>Capt Sahil Singh</b> closes with recommendations, limits and the scorecard, and chairs Q&amp;A. In Q&amp;A the chair routes data and model questions to Capt Sangwan, and military and India questions to Maj Mehta.</p>

<h2>VIDEO-CALL CHECKLIST</h2>
<ul>
<li>Start the dashboard 10 minutes early (<code>streamlit run app/app.py</code>); open every page once so it is cached.</li>
<li>Share a single browser window at 1600×900 or similar; browser zoom 110–125% for legibility after compression.</li>
<li>Keep the backup video (deck/demo) and the deck PDF open in case the live demo or screen-share fails.</li>
<li>Mute notifications; use a wired connection; cameras on for Q&amp;A.</li>
</ul>

<h2>DEMO SCRIPT (ABOUT 3 MINUTES)</h2>
<ol>
<li><b>Commander's brief:</b> point at the four RAG cards; open "Why this rating?" on one card.</li>
<li><b>Area drill-down:</b> Af–Pak → Khyber Pakhtunkhwa: rising deaths, forecast, and the warning history with past escalations marked.</li>
<li><b>Military lens:</b> front-geography chart (Donetsk 55% → 30%), Af–Pak interstate bars.</li>
<li><b>Forecast (2026 test):</b> Russia–Ukraine, Track A: actual vs forecast inside the band.</li>
<li><b>Early warning:</b> Replay Mar 2026 (3 of the top 10 escalated), then move the Alert threshold slider.</li>
<li><b>What-if:</b> Af–Pak, +30% for 3 months: 318 → about 359. Click "Train now" for the live re-train.</li>
<li><b>Scorecard lab:</b> move the hotspot slider and show which ratings change and which do not.</li>
</ol>

<h2>LIKELY QUESTIONS AND ANSWERS</h2>
<div class="cols"><div>{qa_html}</div></div>
<div class="foot">UNCLASSIFIED – OPEN-SOURCE DATA ONLY</div>
"""
(OUT / "QA_Prep_and_Speaker_Split.html").write_text(page("Q&A Prep – Conflict Watch", speak))
print("brief and Q&A written")
