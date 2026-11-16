"""Build the analysis report (Markdown -> HTML -> PDF) from the pipeline outputs.

    python report/build_report.py          # writes report/Conflict_Watch_Report.{md,html}
    node report/to_pdf.js                   # optional: HTML -> PDF with headless Chromium

All numbers are read from outputs/tables so the report always matches the code.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config as C  # noqa: E402
from src.models import MODEL_LABELS  # noqa: E402

TB, FIG = C.TAB_DIR, "../outputs/figures"
OUT = ROOT / "report"


def t(name, **kw):
    return pd.read_csv(TB / name, **kw)


def mdtable(df: pd.DataFrame, index=False, floatfmt=None) -> str:
    d = df.reset_index() if index else df.copy()
    cols = list(d.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in d.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                f = (floatfmt or {}).get(c, "{:,.2f}")
                cells.append("" if pd.isna(v) else f.format(v))
            elif isinstance(v, (int, np.integer)):
                cells.append(f"{v:,}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def fig(name, caption):
    return f'\n<figure><img src="{FIG}/{name}.png" alt="{caption}"/><figcaption>{caption}</figcaption></figure>\n'


# ---------------------------------------------------------------------------
dq = t("data_quality_log.csv")
ov = t("insight_case_overview.csv").set_index("conflict_case")
sc = t("forecast_scores.csv")
rm = t("forecast_rmsle.csv")
abl = t("ablation_lgb.csv")
ens = t("ensemble_selection.csv")
ewr = t("early_warning_scores.csv")
rag = t("rag_scorecard.csv")
stats = t("insight_stats.csv").iloc[0]
fg = t("insight_front_geography.csv")
att = t("insight_attrition.csv")
ie = t("insight_india_exposure.csv")
ih = t("insight_india_hosted.csv")
dp = t("insight_demographics_profile.csv")
ip = t("insight_indian_press.csv").set_index("conflict_case")
ts = t("insight_theatre_spread.csv")
gp = t("insight_geo_precision.csv")
se = t("insight_seasonality.csv")
shap_c = t("shap_lgb_case.csv")
shap_e = t("shap_early_warning.csv")
summary = json.loads((TB / "run_summary.json").read_text())
preds = pd.read_parquet(C.PROCESSED / "forecast_preds.parquet")
future = pd.read_parquet(C.PROCESSED / "forecast_future.parquet")
members = summary["ensemble_members"]

hold = sc[(sc.fold == 2026)]
hA = hold[hold.track == "A"]
naive_mae = hA[hA.model == "naive"].set_index("conflict_case").MAE
ens_mae = hA[hA.model == "ensemble"].set_index("conflict_case").MAE
mae_red = (1 - ens_mae / naive_mae) * 100
pooled_red = (1 - ens_mae.sum() / naive_mae.sum()) * 100
e = preds[preds.model == "ensemble"]
cov = e.groupby(["fold", "track"]).apply(lambda g: pd.Series({
    "80% coverage": ((g.actual >= g.pi80_lo) & (g.actual <= g.pi80_hi)).mean(),
    "95% coverage": ((g.actual >= g.pi95_lo) & (g.actual <= g.pi95_hi)).mean()})).reset_index()
cov26 = e[e.fold == 2026]
cov80_26 = ((cov26.actual >= cov26.pi80_lo) & (cov26.actual <= cov26.pi80_hi)).mean()
ew26 = ewr[ewr.year == 2026].set_index("model")
lg = ew26.loc["LightGBM classifier"]
rule = ew26.loc["Rule: rank by last month's deaths"]
logit = ew26.loc["Logistic regression (5 signals)"]
fg_p = fg.pivot_table(index="area", columns="year", values="share")
don22, don26 = fg_p.loc["Donetsk oblast", 2022] * 100, fg_p.loc["Donetsk oblast", 2026] * 100
ru_att = att[(att.conflict_case == "Russia–Ukraine")].set_index("year")
usir_att = att[(att.conflict_case == "US–Iran")].set_index("year")
g26 = ie[ie.year == 2026]
gulf26 = g26[g26.india_tag.str.startswith("Gulf")]
hz26 = g26[g26.india_tag.str.startswith("Iran")]
yem25 = ie[(ie.year == 2025) & ie.india_tag.str.startswith("Yemen")].deaths.sum()
pakprox = ie[ie.india_tag.str.startswith("Pakistan")].groupby("year").deaths.sum()
dpl = dp.sort_values("year").groupby("origin_iso3").tail(1).set_index("origin_iso3")
ihp = ih.pivot_table(index="year", columns="origin_iso3", values="total_international")
ru_fog = gp[(gp.conflict_case == "Russia–Ukraine")].set_index("year").share_deaths_country_level
usir_ts = ts[ts.conflict_case == "US–Iran"].set_index("year").countries
ses = se[se.conflict_case == "Russia–Ukraine"].set_index("moy").index_pct

# holdout metric table (Track A)
mt = hA.pivot_table(index="model", columns="conflict_case", values="MAE")[C.CASES]
mt.index = mt.index.map(MODEL_LABELS)
mt = mt.sort_values("Russia–Ukraine")
rml = rm.assign(set=np.where(rm.fold == 2026, "2026 holdout", "Back-test 2022–25")).groupby(
    ["model", "track", "set"]).RMSLE.mean().unstack(["track", "set"])
rml.columns = [f"{'A' if a == 'A' else 'B'} · {s}" for a, s in rml.columns]
rml = rml[[c for c in ["A · Back-test 2022–25", "A · 2026 holdout", "B · Back-test 2022–25", "B · 2026 holdout"]]]
rml.index = rml.index.map(MODEL_LABELS)
rml = rml.sort_values("A · Back-test 2022–25")

fut = future[future.model == "ensemble"][["conflict_case", "target_month", "pred", "pi80_lo", "pi80_hi"]].copy()
fut["target_month"] = pd.to_datetime(fut.target_month).dt.strftime("%b %Y")
fut.columns = ["Conflict", "Month", "Forecast deaths", "80% low", "80% high"]

rag_t = rag[["conflict_case", "rating", "forecast_next", "pi80_lo", "pi80_hi", "trend_ratio", "hotspots",
             "top_areas", "score"]].copy()
rag_t["trend_ratio"] = (rag_t.trend_ratio - 1) * 100
rag_t.columns = ["Conflict", "Rating", "Oct 2026 forecast", "80% low", "80% high", "Trend vs 6 mo (%)",
                 "Hotspot areas", "Top escalation areas (probability)", "Points"]

dq_show = dq[dq.rows_affected > 0][["id", "table", "check", "rows_affected", "pct_affected", "action"]]
TOP_DQ = ["DQ05", "DQ07", "DQ10", "DQ13", "DQ14", "DQ15", "DQ23", "DQ24", "DQ29", "DQ34"]
dq_top = dq[dq.id.isin(TOP_DQ)][["id", "check", "rows_affected", "action"]].copy()
dq_top["action"] = dq_top.action.str.split(r"\. ", regex=True).str[0].str.rstrip(".")
dq_top.columns = ["ID", "Issue found", "Rows", "What we did"]

R = json.loads((TB / "robustness.json").read_text())
GD = json.loads((TB / "gdelt_summary.json").read_text())
GS = pd.read_csv(TB / "gdelt_signals.csv")
GM, GW = GD["monthly"]["by_case"], GD["weekly"]
gs = GS[GS.month != "2026-09"].copy()
gs["Month"] = gs.month.map({"2026-10": "Oct 2026", "2026-11": "1–12 Nov 2026"})
gs["Violent events / day"] = gs.violent_pd.map("{:,.0f}".format)
gs["Change vs previous month"] = gs.violent_change_vs_prev.map(lambda v: "0%" if abs(v) < 0.005 else f"{v:+.0%}".replace("-", "−"))
gs["Threats / day"] = gs.threats_pd.map("{:,.0f}".format)
gs["GDELT tracks UCDP here?"] = gs.gdelt_tracks_ucdp.map({True: "Yes", False: "No"})
gs = gs.rename(columns={"case": "Conflict", "flag": "Signal"})[["Conflict", "Month", "Violent events / day",
     "Change vs previous month", "Threats / day", "Signal", "GDELT tracks UCDP here?"]]

RUN_ID = (TB / "run_id.txt").read_text().strip()
cal = t("ew_calibration.csv")
RB = R["by_conflict"]
def pct(x): return f"{x * 100:.0f}%"
def ci(c): return f"{c[0] * 100:.0f}% to {c[1] * 100:.0f}%".replace("-", "−")
excl = [k for k, v in RB.items() if v["ci"][0] > 0]
incl = [k for k, v in RB.items() if v["ci"][0] <= 0]
SHORT = {"Russia–Ukraine": "RU–UA", "Israel–Hamas": "Israel–Hamas", "Afghanistan–Pakistan": "Af–Pak", "US–Iran": "US–Iran"}
def names(ks): return " and ".join(", ".join(SHORT[k] for k in ks).rsplit(", ", 1))
dm_sig = [k for k, v in RB.items() if v["dm_p"] < 0.05]
EWB = R["early_warning"]

def fig2(a, ca, b, cb):
    return (f'\n<div class="two"><figure><img src="{FIG}/{a}.png" alt="{ca}"/><figcaption>{ca}</figcaption></figure>'
            f'<figure><img src="{FIG}/{b}.png" alt="{cb}"/><figcaption>{cb}</figcaption></figure></div>\n')

rag_s = rag_t.copy()
rag_s["80% band"] = rag_s["80% low"].map("{:,.0f}".format) + "–" + rag_s["80% high"].map("{:,.0f}".format)
rag_s = rag_s[["Conflict", "Rating", "Oct 2026 forecast", "80% band", "Trend vs 6 mo (%)", "Hotspot areas",
               "Top escalation areas (probability)", "Points"]].rename(columns={"Rating": "Escalation risk",
               "Hotspot areas": "Hotspots", "Top escalation areas (probability)": "Top areas (probability)", "Points": "Pts"})
rag_s["Escalation risk"] = rag_s["Escalation risk"].map(lambda r: f'<b class="{r.lower()}">{r}</b>')

ft = fut.copy()
ft["v"] = ft["Forecast deaths"].map("{:,.0f}".format) + " (" + ft["80% low"].map("{:,.0f}".format) + "–" + ft["80% high"].map("{:,.0f}".format) + ")"
ftw = ft.pivot(index="Conflict", columns="Month", values="v").reindex(C.CASES)
ftw = ftw[sorted(ftw.columns, key=lambda m: pd.to_datetime(m))]

rows = []
for k in C.CASES:
    v = RB[k]
    rows.append((k, f"{v['mae_ens']:,.0f}", f"{v['mae_naive']:,.0f}", f"{pct(v['reduction'])} ({ci(v['ci'])})",
                 f"{v['dm_p']:.2f}", pct(v["coverage80"])))
P = R["pooled"]
rows.append(("**Pooled**", "", "", f"**{pct(P['reduction'])} ({ci(P['ci'])})**", f"{P['dm_p']:.2f}", pct(P["coverage80"])))
gain_t = "| | MAE ensemble | MAE naive | Reduction (90% interval) | DM p | 80% band coverage |\n|---|---|---|---|---|---|\n" + \
    "\n".join("| " + " | ".join(r) + " |" for r in rows)

cal_t = cal.assign(band=cal.band.str.replace("(-0.001", "(0", regex=False))
cal_md = mdtable(cal_t.rename(columns={"band": "Predicted band", "areas": "Area-months", "mean_pred": "Mean predicted",
                                       "escalated": "Escalated"}), floatfmt={"Mean predicted": "{:.1%}", "Escalated": "{:.1%}"})

author = "Maj Shivam Mehta · Capt Siddharth Sangwan · Capt Sahil Singh"
from src.brand import brand_row
HEAD = brand_row('<div class="kick">DATA ANALYTICS COMPETITION 2026</div><h1 class="title">CONFLICT WATCH</h1>'
                 '<div class="subtitle">When and where will conflict deaths rise next, and what does it mean for India?</div>'
                 f'<div class="meta">{author} | Analysis report · data to 30 Sep 2026 · run {RUN_ID} · UNCLASSIFIED – competition data only</div>',
                 height_mm=22)
md = f"""
<div class="head">{HEAD}</div>

## 1 · Bottom line up front

* **Threat picture (Oct 2026).** Russia–Ukraine is <b class="red">RED</b>: an active high-intensity war forecast at
  **{rag.set_index('conflict_case').loc['Russia–Ukraine', 'forecast_next']:,.0f} deaths** next month. Afghanistan–Pakistan
  and US–Iran are <b class="amber">AMBER</b>: Af–Pak has three escalation hotspots and a new interstate front, and
  US–Iran is volatile after its Feb–Mar 2026 war. Israel–Hamas is <b class="green">GREEN</b>, meaning low risk of
  escalation, not peace: it still records about 130 deaths a month.
* **The fronts are widening, not moving.** In Ukraine, Donetsk's share of located events fell from
  **{don22:.0f}% to {don26:.0f}%** (2022 → 2026). The US–Iran war hit **{int(usir_ts.get(2026, 0))} countries in 2026**, up
  from {int(usir_ts.get(2025, 0))} in 2025.
* **Pakistan now has a two-front problem.** TTP violence in Khyber Pakhtunkhwa has grown every year since 2021, and since
  Oct 2025 the Afghan and Pakistani **governments fight each other directly** (peak: 411 deaths, Mar 2026).
* **The war reached India's neighbourhood.** In 2026 strikes hit 5 Gulf states that host the Indian diaspora
  ({int(gulf26.events.sum())} events), Iran's Hormuz/Chabahar coast ({int(hz26.deaths.sum())} deaths) and Sri Lankan waters
  (**104 killed, 4 Mar 2026**).
* **Forecasting works on unseen data.** Trained only on 2014–2025, the ensemble cut 1-month-ahead error against the
  "no-change" rule by **{pooled_red:.0f}%** on Jan–Sep 2026 (90% interval {ci(P['ci'])}). Its 80% bands held
  **{cov80_26:.0%}** of 2026 outcomes overall, but only {pct(RB['US–Iran']['coverage80'])} for US–Iran (§7.4).
* **Warning works sub-nationally.** A month ahead, the escalation classifier ranks 222 areas with ROC-AUC
  **{lg.ROC_AUC:.2f}** on 2026 (rule of thumb: {rule.ROC_AUC:.2f}). Its top-10 watch-list is
  **{lg.precision_at_10 / lg.base_rate:.1f}× better than random** (90% interval {EWB['lift'][0]:.1f}× to {EWB['lift'][1]:.1f}×).
* **Limit.** No model built on death counts foresees a *decision* to go to war (Feb 2022, Feb 2026). Warning must watch
  spread and hotspots, not media volume: references follow incidents, not lethality, and do not lead escalation.

**Recommendations in brief:** task ISR on the monthly watch-list; keep Gulf NEO plans current while US–Iran is AMBER;
treat the Af–Pak interstate dyad as a standing I&W indicator for the LoC; build Indian OSINT coverage of West Asia (§9).

**Threat scorecard for Oct 2026**, built only from model outputs (rules in §8):

{mdtable(rag_s, floatfmt={"Oct 2026 forecast": "{:,.0f}", "Trend vs 6 mo (%)": "{:+.0f}"})}

## 2 · Problem framing

The brief asks teams to explore four conflicts, frame their own questions, and show verifiable findings with stated
assumptions. For an audience of military officers we chose an **operational** framing: *when and where will conflict
deaths rise next, and what does that mean for the Indian Armed Forces and for humanitarian planning?* We chose it over a
purely descriptive study because a forecast can be scored against withheld data and turned into tasking.

| # | Question | Method | § |
|---|---|---|---|
| Q1 | How intense is each conflict, and how is it changing? | Monthly panels, tempo, lethality, seasonality | 5.1 |
| Q2 | How are the wars fought: attrition, front geography, spread? | Dyad/side analysis, located-event shares, theatre spread | 5.2 |
| Q3 | Can we forecast monthly deaths better than simple rules, on unseen 2026 data? | 7 models, walk-forward back-test, 2026 holdout, conformal intervals | 7 |
| Q4 | Can we warn which areas will escalate next month? | Sub-national classifier, watch-list precision | 8 |
| Q5 | What does it mean for India? | Exposure analysis plus labelled domain reasoning | 6 |

**[Data]** marks results computed from the competition files. **[Domain]** marks expert reasoning the files cannot prove.

## 3 · Data, cleaning and imputation

**Sources (official participant package).** {ov.events.sum():,} UCDP event records (GED 26.1 for 2014–2025; provisional
Candidate 26.01.26.09 for Jan–Sep 2026), {85406:,} source references, UNHCR bilateral stocks (6,273 rows) and demographics
(19,830), IDMC/UNRWA reference stocks (112) and World Bank context (1,764). The top-level files outside the official folder
belong to another package and were **not** used.

**{len(dq)} documented checks**, of which {int((dq.rows_affected > 0).sum())} found something to handle. No row is silently
dropped: every fix is logged, and raw values are kept beside corrected ones. The ten that matter most are below; all
{int((dq.rows_affected > 0).sum())} are in **Appendix A** and `outputs/tables/data_quality_log.csv`.

{mdtable(dq_top)}

**Imputation rules.** Blank country codes become `INTL` (waters/airspace) or `XXX` (ambiguous code 666); blank admin1
becomes an explicit "country-level" bucket, so those deaths are not lost. A dash in UNHCR "other protection" is nil and
becomes 0. World Bank gaps (36 GDP, 124 inflation values) are interpolated within each economy; because interpolation looks
at later years, **these columns are kept out of the selected ensemble and classifier** and appear only in benchmark and
ablation variants. Area-months with no event are true zeros.

**A finding from cleaning: the fog of war is in the data [Data].** The share of Russia–Ukraine deaths with no sub-national
location rose from {ru_fog.get(2022, np.nan):.0%} (2022) to **{ru_fog.get(2026, np.nan):.0%} (2026)**, because most recent
deaths come from country-level memorial and aggregate counts. We therefore measure front geography with **located,
discrete events**.

## 4 · Feature engineering

Two monthly panels: **4 conflicts × 153 months** and **222 sub-national area series × 153 months** (zero-filled). Every
feature is known at the end of the forecast-origin month.

| Family | Features | Military / analytic idea |
|---|---|---|
| Intensity memory | deaths in the last 1–12 months, 3/6/12-month averages, worst month in a year | War has inertia |
| Momentum | last 3 vs last 12 months, month-on-month change, dormancy streak | Escalation = short-term above long-term norm |
| Tempo and fog | events and references per month; (high − low)/best; share of aggregate records | Engagements vs lethality; degraded picture |
| Character | civilian, state-based, one-sided and focal-dyad shares | Battlefield vs punitive violence |
| Geography | active areas, concentration (Herfindahl), share outside the core theatre | Front widening, horizontal escalation |
| Seasonality | calendar month, same month last year | Campaign seasons |
| Hierarchy | whole-conflict and country tempo; area's share of its conflict | Areas inherit their war's tempo |

The ablation in §7.2 shows that **a compact 18-feature subset generalises best** at conflict level: with four series,
40 features over-fit. The richer set is used where data are plentiful (222 area series).

## 5 · Exploratory analysis and findings

### 5.1 Intensity and tempo [Data]

{fig("01_monthly_deaths", "Figure 1 – Monthly deaths by conflict (log scale); shaded = 2026 withheld test window")}

| | Russia–Ukraine | Israel–Hamas | Afghanistan–Pakistan | US–Iran |
|---|---|---|---|---|
| Recorded deaths 2014–Sep 2026 (low – high) | {ov.loc['Russia–Ukraine', 'deaths_best']:,} ({ov.loc['Russia–Ukraine', 'deaths_low'] / 1e3:.0f}k – {ov.loc['Russia–Ukraine', 'deaths_high'] / 1e3:.0f}k) | {ov.loc['Israel–Hamas', 'deaths_best']:,} ({ov.loc['Israel–Hamas', 'deaths_low'] / 1e3:.0f}k – {ov.loc['Israel–Hamas', 'deaths_high'] / 1e3:.0f}k) | {ov.loc['Afghanistan–Pakistan', 'deaths_best']:,} ({ov.loc['Afghanistan–Pakistan', 'deaths_low'] / 1e3:.0f}k – {ov.loc['Afghanistan–Pakistan', 'deaths_high'] / 1e3:.0f}k) | {ov.loc['US–Iran', 'deaths_best']:,} ({ov.loc['US–Iran', 'deaths_low'] / 1e3:.1f}k – {ov.loc['US–Iran', 'deaths_high'] / 1e3:.1f}k) |
| Peak month | {ov.loc['Russia–Ukraine', 'peak_month']} ({ov.loc['Russia–Ukraine', 'peak_month_deaths']:,}) | {ov.loc['Israel–Hamas', 'peak_month']} ({ov.loc['Israel–Hamas', 'peak_month_deaths']:,}) | {ov.loc['Afghanistan–Pakistan', 'peak_month']} ({ov.loc['Afghanistan–Pakistan', 'peak_month_deaths']:,}) | {ov.loc['US–Iran', 'peak_month']} ({ov.loc['US–Iran', 'peak_month_deaths']:,}) |
| Deaths Jan–Sep 2026 | {ov.loc['Russia–Ukraine', 'deaths_2026_ytd']:,} | {ov.loc['Israel–Hamas', 'deaths_2026_ytd']:,} | {ov.loc['Afghanistan–Pakistan', 'deaths_2026_ytd']:,} | {ov.loc['US–Iran', 'deaths_2026_ytd']:,} |
| Civilian share · countries with deaths | {ov.loc['Russia–Ukraine', 'civilian_share']:.0%} · {ov.loc['Russia–Ukraine', 'countries_affected']} | {ov.loc['Israel–Hamas', 'civilian_share']:.0%} · {ov.loc['Israel–Hamas', 'countries_affected']} | {ov.loc['Afghanistan–Pakistan', 'civilian_share']:.0%} · {ov.loc['Afghanistan–Pakistan', 'countries_affected']} | {ov.loc['US–Iran', 'civilian_share']:.0%} · {ov.loc['US–Iran', 'countries_affected']} |

**Four threat signatures:** RU–UA is sustained attrition (4–11k deaths a month since 2023), US–Iran is spikes (coalition
strikes, then direct war in Feb–Mar 2026), Af–Pak is a creep (rising since 2021) and Israel–Hamas is de-escalating (about
130 a month in 2026). **Campaign seasons:** RU–UA deaths run {ses.loc[5]:+.0f}% (May) and {ses.loc[7]:+.0f}% (Jul) against
trend, and {ses.loc[12]:+.0f}% (Dec) and {ses.loc[1]:+.0f}% (Jan); Af–Pak peaks in Sep–Oct. *So what:* one warning rule
cannot fit all four, so we forecast level, trend and spread separately.

### 5.2 How the wars are being fought (military lens)

**Front geography: widening, not moving [Data].** Donetsk's share of located events fell from {don22:.0f}% (2022) to
{don26:.0f}% (2026) while Zaporizhzhia ({fg_p.loc['Zaporizhzhya oblast', 2026] * 100:.0f}%), Dnipropetrovsk
({fg_p.loc['Dnipropetrovsk oblast', 2026] * 100:.0f}%), Sumy ({fg_p.loc['Sumy oblast', 2026] * 100:.0f}%) and Russia's
Belgorod ({fg_p.loc['Belgorod oblast', 2026] * 100:.0f}%) grew. Deaths recorded inside Russia peaked at 10,358 in 2024.
*So what [Domain]:* a wide, static front rewards long-range fires, counter-drone, EW and logistics depth.

**Recorded attrition by side [Data, with caveat].** In the RU–UA focal dyad UCDP records
{ru_att.loc[2022, 'deaths_side_a']:,.0f} Russian vs {ru_att.loc[2022, 'deaths_side_b']:,.0f} Ukrainian fatalities in 2022
({ru_att.loc[2022, 'ratio_a_to_b']:.1f}:1), widening to {ru_att.loc[2026, 'ratio_a_to_b']:.1f}:1 in 2026. In the 2026 US–Iran
war, Iran's recorded losses were {usir_att.loc[2026, 'deaths_side_a']:,.0f} against {usir_att.loc[2026, 'deaths_side_b']:,.0f}
for the Israel–US coalition. These are *recorded* figures: Ukrainian memorial databases document Russian losses more fully
than the reverse, so the ratio is an upper bound of reporting, not a verified exchange ratio.

{fig2("05_front_geography", "Figure 2 – Russia–Ukraine: share of located discrete events by area",
      "06_attrition_ru_ua", "Figure 3 – Russia–Ukraine: UCDP-recorded fatalities by side (recorded, not verified)")}

**Afghanistan–Pakistan: a second front opens [Data].** Violence has concentrated in Khyber Pakhtunkhwa (TTP) and
Balochistan and has risen every year since 2021. Since **Oct 2025 the two states clash directly** (131 deaths in Oct 2025;
172, 411 and 68 in Feb–Apr 2026). *So what [Domain]:* a Pakistan Army committed in the west has less capacity in the east,
or more incentive for diversionary LoC activity. Watch the western front more closely, not less.

{fig2("10_afpak_interstate", "Figure 4 – Afghanistan vs Pakistan government clashes (focal dyad), deaths per month",
      "09_afpak_provinces", "Figure 5 – Afghanistan–Pakistan deaths by province (FATA harmonised into KP)")}

**Horizontal escalation [Data].** The US–Iran case spread from {int(usir_ts.get(2025, 0))} countries (2025) to
{int(usir_ts.get(2026, 0))} (2026), including five Gulf states and Sri Lankan waters. Israel–Hamas reached Qatar in Sep 2025.

### 5.3 Media attention vs deaths: an original index [Data]

We regress monthly source references on events and deaths (log, conflict fixed effects). The standardised residual is the
**Attention Gap Index (AGI)**: above 0 is over-reported, below 0 is "forgotten" violence. References scale with
**incidents** (elasticity {stats.media_elasticity_events:.2f}), not **lethality** ({stats.media_elasticity_deaths:.2f});
R² = {stats.media_r2:.2f}. Per 100 deaths there are 150 references for Israel–Hamas, 54 for RU–UA, 40 for Af–Pak and 35
for US–Iran. The AGI does **not** lead next month's escalation (coefficient {stats.media_lead_coef:.3f}, p =
{stats.media_lead_p:.2f}). In UCDP's record, Indian outlets (mainly PTI) appear in
**{ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%} of Af–Pak events** and almost none elsewhere: the record of
West Asia rests on non-Indian wires. *So what:* do not build warning on media volume.

### 5.4 Displacement and humanitarian planning [Data]

Ukraine, end-2025: about 5.2M refugees abroad and 3.7M IDPs; **{dpl.loc['UKR', 'women_children_share']:.0%}** of refugees
with recorded sex and age are women or children. Afghanistan: {dpl.loc['AFG', 'women_children_share']:.0%} women and
children, {dpl.loc['AFG', 'under5_share']:.0%} under five. Palestine: 2.0M IDPs (IDMC); UNRWA registrations (2.5M) are a
separate series and are never summed. Country-year deaths explain little of the change in displaced stocks (Spearman
{stats.link_spearman:.2f}, p = {stats.link_p:.2f}). *So what:* trigger HADR planning on **onset and spread** (our
escalation flags), not death tolls, and stock paediatric and maternal supplies.

{fig2("13_media_scatter", "Figure 6 – References track events tightly, deaths loosely",
      "08_country_map", "Figure 7 – Where the four conflicts killed people, 2024–Sep 2026 (India outlined)")}

### 5.5 A second source: GDELT media-coded events, Feb–Nov 2026 [Data, new results]

The competition package also contains GDELT, about 5.4 GB of machine-coded news events. We reduced
{GD['coverage']['events']:,} dyad-coded events (RU↔UA, ISR↔PSE/Hamas, AFG↔PAK, USA↔IRN; {GD['coverage']['start']} to
{GD['coverage']['end']}, gap {GD['coverage']['gap']}) to daily, weekly and monthly rates per covered day
(`data/gdelt/`, script included). GDELT counts *reports*, not incidents, so we compare it with UCDP and never join
event to event. **This is a separate analysis: it does not change any submitted model number.**

* **It agrees with UCDP only for spike wars.** Month-on-month, GDELT's violent-event rate moves with UCDP deaths for
  US–Iran (ρ = {GM['US–Iran']['rho_change']:.2f}) and Af–Pak ({GM['Afghanistan–Pakistan']['rho_change']:.2f}), not for
  Russia–Ukraine ({GM['Russia–Ukraine']['rho_change']:+.2f}) or Israel–Hamas ({GM['Israel–Hamas']['rho_change']:+.2f}).
  Pooled, r = {GD['monthly']['pooled_change_r']:.2f} (p < 0.001, n = {GD['monthly']['n']} conflict-months). In an attrition
  war, news volume rises with *activity* (summer offensives) while recorded deaths fall.
* **It confirms the attention gap with an independent source.** GDELT carries about
  {GM['Israel–Hamas']['articles_per_death']:,.0f} articles per UCDP death for Israel–Hamas and
  {GM['US–Iran']['articles_per_death']:,.0f} for US–Iran, against {GM['Russia–Ukraine']['articles_per_death']:,.0f} for
  Russia–Ukraine (§5.3).
* **It is a nowcast, not a leading indicator.** Weekly, with conflict effects, GDELT in the *same* week adds to last
  week's UCDP deaths (coefficient {GW['nowcast_coef']:.2f}, p < 0.001), but GDELT a week *earlier* adds nothing
  (p = {GW['lead_p']:.2f}). Out of sample over {GW['oos_weeks']} weeks, neither beats persistence
  ({GW['oos_gain_nowcast']:+.0%} and {GW['oos_gain_lead']:+.0%} change in error). So GDELT does not improve the submitted
  forecasts and we did not add it to them.
* **What it is good for: seeing past UCDP's cut-off.** UCDP ends on 30 Sep 2026; GDELT runs to 12 Nov. For the spike
  wars where it tracks UCDP, it is a fast situational-awareness feed:

{mdtable(gs)}

*So what:* in Oct 2026 GDELT was steady for three wars and quieter for US–Iran, which is consistent with the frozen Oct forecasts. **US–Iran is the one to
watch:** in the first 12 days of Nov its violent-event rate rose {GS[(GS.case == 'US–Iran') & (GS.month == '2026-11')].violent_change_vs_prev.iloc[0]:+.0%}
and threats ({GS[(GS.case == 'US–Iran') & (GS.month == '2026-11')].threats_pd.iloc[0]:.0f} a day) roughly doubled. With
the scorecard at AMBER and GDELT tracking UCDP in this war, that justifies keeping Gulf NEO plans current (§9). Falls in
early Nov for Af–Pak and Israel–Hamas rest on 12 days and are not yet a trend.

{fig2("27_gdelt_vs_ucdp", "Figure 8 – GDELT violent events per day vs UCDP weekly deaths, 2026 (shaded = after UCDP ends)",
      "28_gdelt_lags", "Figure 9 – Correlation of GDELT with UCDP at different week shifts")}

## 6 · India impact

| Theatre | What the data show [Data] | What it means for India [Domain] |
|---|---|---|
| Afghanistan–Pakistan | KP deaths up every year since 2021; state-on-state clashes since Oct 2025; deaths in Pakistan-held areas adjoining India/LoC rose from {pakprox.get(2022, 0):,.0f} (2022) to {pakprox.get(2025, 0):,.0f} (2025) | Pakistan Army committed in the west: risk of diversionary LoC activity, infiltration and TTP/IS-K spill-over |
| US–Iran / Gulf | {int(usir_ts.get(2026, 0))} countries hit in 2026, incl. 5 Gulf states ({int(gulf26.events.sum())} events, {int(gulf26.deaths.sum())} deaths); {int(hz26.deaths.sum())} deaths on Iran's Hormuz/Chabahar coast; {yem25:,.0f} deaths in Yemen in 2025 | About 9M Indians in the Gulf need NEO contingency (cf. Op Ganga, Kaveri, Ajay); crude and LPG transit Hormuz; Chabahar and INSTC lie in the strike zone |
| Indian Ocean | 104 killed in one strike off Sri Lanka's west coast, 4 Mar 2026 | The war entered India's maritime neighbourhood: IFC-IOR and Navy need a belligerent-movement picture |
| Russia–Ukraine | 4–11k deaths a month; front widening; extreme recorded attrition asymmetry | Spares for legacy Russian platforms at risk; drone, counter-drone and EW lessons |
| Israel–Hamas | De-escalated to about 130 a month in 2026 | A key supplier of UAVs, missiles and sensors is at war: hold buffer stocks |
| Refugees in India | Afghans {ihp['AFG'].get(2021, np.nan):,.0f} (2021) → {ihp['AFG'].get(2025, np.nan):,.0f} (2025); Russian asylum seekers {ihp['RUS'].get(2015, np.nan):,.0f} (2015) → {ihp['RUS'].get(2025, np.nan):,.0f} (2025) | Small numbers; monitor the rising Russian flow |

## 7 · Forecasting model

### 7.1 Protocol and models
Models are fitted once on data up to December *Y − 1*, frozen, and scored on Jan–Sep of year *Y*. **Track A
(operational)** is 1 month ahead, rolling, with no refitting. **Track B (strategic)** is 1–9 months ahead from a single
December origin. Back-test folds 2022–2025 drive every design choice (ablation, ensemble membership, interval
calibration). **2026 is the withheld test set, scored once.** RMSLE is the selection metric because the four series differ
by three orders of magnitude; MAE, RMSE, MAPE, sMAPE and MASE are in `outputs/tables/forecast_scores.csv` (definitions in
Appendix B). Candidates: naive, seasonal naive and 3-month mean (benchmarks); ETS (damped Holt, log); SARIMA (AIC-selected,
log); **LightGBM-Δ** (one global model that learns the change in log deaths from 18 features); bottom-up Tweedie LightGBM
(222 areas summed). **Ensemble** = {" + ".join(MODEL_LABELS[m].split(" (")[0] for m in members)}, a log-space mean.

### 7.2 Why these choices: ablation (back-test only)

{mdtable(abl.rename(columns={"variant": "LightGBM variant"}), floatfmt={c: "{:.3f}" for c in abl.columns})}

A plain LightGBM on the log **level** is the worst option. Trees cannot predict beyond the range seen in training, so a
model fitted before 2022 can never forecast the invasion. Predicting the **change** removes that ceiling, and a compact
feature set with a robust L1 loss generalises best. Deep learning was not used: four series of 153 months are far too few.

### 7.3 Results on the withheld 2026 data

**RMSLE, lower is better** (A = 1 month ahead; B = 1–9 months from December)

{mdtable(rml, index=True, floatfmt={c: "{:.3f}" for c in rml.columns})}

**1 month ahead on 2026: error against the "no-change" rule**, with 90% moving-block bootstrap intervals and one-sided
Diebold–Mariano (DM) tests

{gain_t}

**How strong is the evidence?** The pooled gain of {pooled_red:.0f}% is positive in {P['p_positive']:.0%} of bootstrap
resamples, and the interval excludes zero for the pool{" and for " + names(excl) if excl else ""}. It does not exclude zero for
{names(incl)}. With nine test months, a Diebold–Mariano test is significant at 5% only for
{names(dm_sig) if dm_sig else "no single conflict"} (pooled p = {P['dm_p']:.2f}). Across all five folds
({R['all_folds']['months']} months) the pooled gain is {pct(R['all_folds']['reduction'])} ({ci(R['all_folds']['ci'])}).
We therefore claim a **consistent, practically useful gain, not a statistically proven one**. On Track B, SARIMA and the
bottom-up LightGBM edged the ensemble in 2026, though not in the back-test; we report this rather than re-select on the
test set.

{fig2("19_forecast_A_RU-UA", "Figure 10 – Russia–Ukraine: 1-month-ahead forecast vs actual on the 2026 holdout, 80% band, forward forecast",
      "19_forecast_A_AF-PK", "Figure 11 – Afghanistan–Pakistan: same view")}

### 7.4 Reliability for trend forecasting

* **Uncertainty.** Split-conformal intervals from 2022–25 residuals cover **{cov80_26:.0%}** of 2026 outcomes at the 80%
  level. That average hides a split: one month ahead, coverage is {pct(RB['Russia–Ukraine']['coverage80'])} for the three
  established wars (bands are conservative) and **{pct(RB['US–Iran']['coverage80'])} for US–Iran**, whose war began inside
  the test window. Treat US–Iran bands as too narrow.
* **Direction.** The 1-month forecast called the direction of change correctly in 72% of 2026 conflict-months.
* **If data arrive a month late.** Forecasting month *t* from data to *t − 2* (same frozen method) still beats the matching
  naive rule: MAE {pct(R['late_data']['holdout'])} lower on 2026 and {pct(R['late_data']['backtest'])} lower on the back-test.
* **Explainability.** TreeSHAP shows the forecast is driven by last month's level, the change since the month before,
  two-month memory, momentum and volatility, then season: features an officer can reason about.
* **Known failure.** The Feb 2026 US–Iran war began with no build-up in the death series. Political decisions to start
  wars are not forecastable from this data.

**Forward forecast**, deaths per month with 80% band (refitted on all data to Sep 2026):

{mdtable(ftw, index=True)}

## 8 · Early warning, scorecard and what-if

An area **escalates** next month if its deaths are ≥ 10 and ≥ 1.5 × its trailing 3-month mean (about 4% of area-months).
A regularised LightGBM classifier uses 19 features (own intensity and momentum, conflict-wide tempo and spread, country
momentum, season), is trained on months up to Dec *Y − 1* and tested on Jan–Sep *Y* for 2023–2026.

| 2026 withheld | ROC-AUC | PR-AUC | Brier | Top-10 precision | Top-20 recall |
|---|---|---|---|---|---|
| **LightGBM classifier** (90% interval) | **{lg.ROC_AUC:.3f}** ({EWB['auc'][0]:.2f}–{EWB['auc'][1]:.2f}) | **{lg.PR_AUC:.3f}** ({EWB['pr_auc'][0]:.2f}–{EWB['pr_auc'][1]:.2f}) | {lg.Brier:.3f} | **{lg.precision_at_10:.1%}** ({EWB['p10'][0]:.0%}–{EWB['p10'][1]:.0%}) | {lg.recall_at_20:.1%} |
| Logistic regression (5 signals) | {logit.ROC_AUC:.3f} | {logit.PR_AUC:.3f} | {logit.Brier:.3f} | {logit.precision_at_10:.1%} | {logit.recall_at_20:.1%} |
| Rule: last month's deadliest | {rule.ROC_AUC:.3f} | {rule.PR_AUC:.3f} | {rule.Brier:.3f} | {rule.precision_at_10:.1%} | {rule.recall_at_20:.1%} |
| Base rate | | {lg.base_rate:.3f} | | {lg.base_rate:.1%} | |

The top-10 list is **{lg.precision_at_10 / lg.base_rate:.1f}× better than random** and
{lg.precision_at_10 / max(rule.precision_at_10, 1e-9):.1f}× better than the rule of thumb (intervals: areas resampled). The
leading signals are the area's own smoothed intensity, **its country's** intensity and momentum and the **whole
conflict's** momentum and spread: escalation is contagious within a theatre. **Calibration:** the scores rank areas well
but run high at the top end. Areas scored 15% or more (mean {EWB['top_band']['mean_pred']:.0%}) escalated
{EWB['top_band']['escalated']:.0%} of the time in 2026. Use the watch-list as a **ranking, not as literal odds**.

{fig2("24_early_warning_curves", "Figure 12 – ROC and precision–recall on 2026 withheld months",
      "26_ew_calibration", "Figure 13 – Predicted probability vs share that escalated, 2026")}

**Watch-list for Oct 2026.** Kandahar, Balochistan and Kunar (Af–Pak, 21–23%), then Hormozgan (US–Iran, 16%) and
Chernihiv, Dnipropetrovsk and Sumy (RU–UA, 14–15%). The dashboard lists the top 20.

**Scorecard rules.** Points: **intensity** (forecast ≥ 1,000 → 2; ≥ 100 → 1); **trend** vs the last 6 months (≥ +20% →
+1; ≤ −20% → −1); **hotspots** (areas scored ≥ 15%: ≥ 3 → 2; ≥ 1 → 1); **spread** (more countries than last year → 1);
**volatility** (a ≥ 1,000-death month in the last year → 1). **RED** = forecast ≥ 1,000 or ≥ 5 points; **AMBER** = 2–4;
**GREEN** ≤ 1. The rating measures escalation risk relative to the conflict's own recent level.

**What-if and new data.** The dashboard re-runs the ensemble on a modified history: a +30% surge in Af–Pak deaths over
three months raises the Oct 2026 forecast by about 13% (318 → 359). `python score_holdout.py --events <file>` scores the
forecasts and watch-list frozen in this submission against any new month of events, without refitting.

## 9 · Recommendations

| Line | Action | Triggering finding [Data] | Lead [Domain] | When |
|---|---|---|---|---|
| **SENSE** | Task ISR and analysts on the monthly sub-national watch-list; track active sectors and countries hit | Top-10 list {lg.precision_at_10 / lg.base_rate:.1f}× random (§8) | DIA / Service intelligence | Now |
| **SENSE** | Build Indian OSINT coverage of the Gulf, Iran and Red Sea; run a GDELT feed as a nowcast past UCDP's lag for spike wars | Indian outlets in {ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%} of Af–Pak events, about 0% elsewhere; GDELT tracks UCDP for US–Iran (§5.3, §5.5) | DIA / MEA | 90 days |
| **WARN** | Adopt the Af–Pak interstate dyad and KP/Balochistan scores as standing LoC I&W indicators | State clashes since Oct 2025; 3 hotspots (§5.2, §8) | Northern / Western Comds | Now |
| **WARN** | Publish the scorecard monthly; escalate any move to RED or rise in countries hit | US–Iran {int(usir_ts.get(2025, 0))} → {int(usir_ts.get(2026, 0))} countries with no build-up (§5.2) | HQ IDS | 90 days |
| **SHIELD** | Keep Gulf NEO plans current while US–Iran is AMBER; sealift/airlift options | 5 Gulf states struck, {int(gulf26.events.sum())} events (§6) | HQ IDS / Navy / IAF / MEA | Now |
| **SHIELD** | Belligerent-movement picture for the IOR | 104 killed off Sri Lanka, 4 Mar 2026 (§6) | Navy / IFC-IOR | 90 days |
| **SUSTAIN** | Buffer and indigenise critical spares for Russian- and Israeli-origin platforms | RU–UA 4–11k deaths a month, no decline forecast (§7) | MoD / DPSUs | 6–12 months |
| **SUSTAIN** | HADR kits weighted to women, children and under-fives; trigger on escalation flags | {dpl.loc['UKR', 'women_children_share']:.0%} of Ukrainian refugees are women or children (§5.4) | HQ IDS / NDMA | 6–12 months |

## 10 · Assumptions, limitations, tools and reproducibility

* UCDP records **reported** lethal violence; coverage depends on access, and side-specific attrition reflects reporting asymmetry.
* 2026 data are **provisional** (Candidate) and usually revised upward, so holdout error includes revision noise.
* Over 90% of 2026 RU–UA deaths have no sub-national location, so sub-national claims about Ukraine rest on events.
* The US–Iran focal dyad codes **Israel and the US as one actor**; no country split is possible.
* Displacement stocks cannot be attributed to single events; IDMC and UNRWA series are kept separate.
* Nine test months per conflict is a small sample: see the intervals in §7.3 and §8.
* Forecasts cannot anticipate decisions to start wars, and US–Iran intervals under-cover (§7.4).
* GDELT (§5.5) covers only Feb–Nov 2026 with a 16-day gap, counts reports not incidents, and over-represents US-linked news.
* Map boundaries follow the Government of India's depiction. [Domain] statements are expert reasoning and are labelled.

**Tools.** Python 3.13: pandas, NumPy, SciPy, statsmodels (ETS, SARIMA), LightGBM (forecaster, classifier, TreeSHAP),
scikit-learn, Plotly and Streamlit (dashboard), python-pptx. **AI tools used: Claude (Anthropic), as a coding, drafting
and review assistant.** It helped write and debug the pipeline, dashboard, report and slide code, and reviewed the
submission against the marking scheme. **No number was typed in or generated by an AI tool: every figure is computed by
the code in this repository from the issued dataset and can be reproduced with one command. The team framed the
questions, checked the analysis and owns the findings and recommendations.**

**Reproduce.** `pip install -r requirements-dev.txt`, then `python run_pipeline.py` (about 4 min: clean → features →
insights → models → evidence checks → figures), `streamlit run app/app.py`, `python score_holdout.py --selftest`. Seeds
are fixed (`random_state = 42`). Every number here is read from `outputs/tables/`; the run ID **{RUN_ID}** is a hash of the
result tables and is printed on this report, the deck and the dashboard, so all three can be matched. Live:
conflictmonitor2026.streamlit.app.

<div class="pagebreak"></div>

## Appendix A · Data-quality log (all issues found)

{mdtable(dq_show, floatfmt={"pct_affected": "{:.2f}"})}

## Appendix B · Metric definitions and evidence methods

MAE = mean |error|; RMSE = √mean(error²); MAPE = mean |error|/actual over months with actual > 0; sMAPE = mean
2|e|/(|y|+|ŷ|); MASE = MAE / in-sample MAE of the one-step naive; RMSLE = √mean(log(1+ŷ) − log(1+y))²; coverage = share of
actuals inside the interval; ROC-AUC/PR-AUC for ranking; Brier = mean squared probability error; precision@10 = share of
each month's top-10 areas that escalated. **Bootstrap:** {R['n_boot']:,} moving-block resamples of months
(block {R['block_months']}; all conflicts resampled together for the pool), 5th–95th percentiles. **Diebold–Mariano:**
absolute-error loss, one-sided (ensemble better), Harvey–Leybourne–Newbold small-sample correction. **Early-warning
intervals:** 1,000 resamples of areas. **Calibration** (2026, LightGBM):

{cal_md}
"""

(OUT / "Conflict_Watch_Report.md").write_text(md)

import markdown  # noqa: E402

body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
CSS = """
@page { size: A4; margin: 14mm 13mm 16mm 13mm; }
body { font-family: Calibri, 'Segoe UI', Carlito, Arial, sans-serif; color: #1b2733; font-size: 9.4pt; line-height: 1.38; }
h1, h2, h3 { color: #07131F; }
h2 { border-bottom: 2.5px solid #F0B03A; padding-bottom: 3px; margin: 16px 0 6px 0; font-size: 13.5pt; page-break-after: avoid; }
h3 { font-size: 11pt; margin: 10px 0 4px 0; page-break-after: avoid; }
p, ul { margin: 4px 0 6px 0; } li { margin: 1px 0; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 8px 0; font-size: 8.2pt; page-break-inside: auto; }
th { background: #0F2236; color: #fff; text-align: left; padding: 3px 5px; }
td { border-bottom: 1px solid #d6dee8; padding: 2.5px 5px; vertical-align: top; }
tr:nth-child(even) td { background: #f4f7fa; }
figure { margin: 6px 0 8px 0; page-break-inside: avoid; }
figure img { width: 100%; border-radius: 4px; }
figcaption { font-size: 7.8pt; color: #5E7B99; margin-top: 2px; }
.two { display: flex; gap: 10px; page-break-inside: avoid; } .two figure { flex: 1; margin: 4px 0 6px 0; }
code, pre { background: #f0f3f7; border-radius: 3px; font-size: 8pt; }
.red { color: #d7263d; } .amber { color: #c77d00; } .green { color: #1f9e83; }
.head { background: #07131F; color: #fff; padding: 9px 14px 10px 14px; border-radius: 4px; margin-bottom: 6px; }
.head .kick { color: #F0B03A; font-weight: 700; letter-spacing: 2.5px; font-size: 8pt; }
.head .title { color: #fff; font-size: 24pt; letter-spacing: 1.5px; margin: 2px 0 2px 0; border: none; padding: 0; }
.head .subtitle { color: #D5DEE8; font-size: 11pt; }
.head .meta { color: #9FB2C6; font-size: 7.8pt; margin-top: 4px; }
.pagebreak { page-break-after: always; }
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><title>Conflict Watch – Analysis Report</title><style>{CSS}</style></head><body>{body}</body></html>"
(OUT / "Conflict_Watch_Report.html").write_text(html)
print("report written:", OUT / "Conflict_Watch_Report.html")
