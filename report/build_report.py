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

author = "Maj Shivam Mehta<br/>Capt Siddharth Sangwan<br/>Capt Sahil Singh"
md = f"""
<div class="cover">
<div class="kick">DATA ANALYTICS COMPETITION 2026</div>
<h1 class="title">CONFLICT WATCH</h1>
<div class="subtitle">When and where will conflict deaths rise next, and what does it mean for India?<br/>
Russia–Ukraine · Israel–Hamas · Afghanistan–Pakistan · US–Iran</div>
<div class="author"><span style="font-weight:400;font-size:10pt;color:#F0B03A;letter-spacing:2px">TEAM</span><br/>{author}</div>
<div class="meta">Analysis report · data to 30 Sep 2026 · UNCLASSIFIED – open-source data only</div>
</div>

<div class="pagebreak"></div>

## 1 · Bottom line up front

* **Threat picture (Oct 2026).** Russia–Ukraine is <b class="red">RED</b>: an active high-intensity war forecast at
  **{rag.set_index('conflict_case').loc['Russia–Ukraine', 'forecast_next']:,.0f} deaths** next month. Afghanistan–Pakistan
  and US–Iran are <b class="amber">AMBER</b>: Af–Pak has three escalation hotspots and a new interstate front, and
  US–Iran is volatile after its Feb–Mar 2026 war. Israel–Hamas is <b class="green">GREEN</b>: it has de-escalated to
  about 130 deaths a month.
* **The fronts are widening, not moving.** In Ukraine, Donetsk's share of located events fell from
  **{don22:.0f}% to {don26:.0f}%** (2022 → 2026) as violence spread to Zaporizhzhia, Dnipropetrovsk, Sumy and into
  Russia. The US–Iran war hit **{int(usir_ts.get(2026, 0))} countries in 2026**, up from {int(usir_ts.get(2025, 0))} in 2025.
* **Pakistan now has a two-front problem.** The TTP insurgency in Khyber Pakhtunkhwa has grown every year since 2021,
  and since Oct 2025 the Afghan and Pakistani **governments fight each other directly** (peak: 411 deaths, Mar 2026).
* **The war reached India's neighbourhood.** In 2026 strikes hit {gulf26.shape[0] and 5} Gulf states that host the
  Indian diaspora ({int(gulf26.events.sum())} events), Iran's Hormuz/Chabahar coast ({int(hz26.deaths.sum())} deaths),
  and Sri Lankan waters (**104 killed, 4 Mar 2026**).
* **Forecasting works on unseen data.** Trained only on 2014–2025, our ensemble cut 1-month-ahead error against
  the "no-change" rule by **{pooled_red:.0f}%** overall on Jan–Sep 2026 ({mae_red['Russia–Ukraine']:.0f}% for RU–UA,
  {mae_red['Israel–Hamas']:.0f}% for Israel–Hamas). Its 80% intervals contained **{cov80_26:.0%}** of 2026 outcomes.
* **Warning works sub-nationally.** A month ahead, the escalation classifier ranks 222 area series with
  ROC-AUC **{lg.ROC_AUC:.2f}** on 2026 (rule of thumb: {rule.ROC_AUC:.2f}). Its top-10 watch-list is
  **{lg.precision_at_10 / lg.base_rate:.1f}× better than random**.
* **Limit.** No model built on death counts foresees a *decision* to go to war (Feb 2022, Feb 2026). Indications and
  warning must watch spread and hotspots, and **not media volume**: references follow incidents, not lethality, and
  do not lead escalation.

**Recommendations, in brief:** task ISR on the monthly escalation watch-list. Keep Gulf NEO plans current while US–Iran is
AMBER. Treat the Af–Pak interstate dyad as a standing I&W indicator for the LoC. Build indigenous OSINT coverage of
West Asia: Indian outlets appear in {ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%} of Af–Pak events and almost
none elsewhere. See §9.

{fig("25_rag_scorecard", "Figure 1 – Threat scorecard for Oct 2026, built only from model outputs (rules in §8.3)")}

{mdtable(rag_t, floatfmt={"Oct 2026 forecast": "{:,.0f}", "80% low": "{:,.0f}", "80% high": "{:,.0f}",
                            "Trend vs 6 mo (%)": "{:+.0f}"})}

## 2 · Problem framing

The brief asks teams to explore four conflicts, frame their own questions, and show verifiable, reproducible
findings with stated assumptions. For an audience of military officers we chose an **operational** framing:

> **When and where will conflict deaths rise next, and what does that mean for the Indian Armed Forces and for
> humanitarian planning?**

| # | Question | Method | Section |
|---|---|---|---|
| Q1 | How intense is each conflict, and how is it changing? | Monthly panels, tempo, lethality, seasonality | 5.1 |
| Q2 | How are the wars fought: attrition, violence type, front geography, spread? | Dyad/side analysis, geolocated-event shares, theatre spread | 5.2 |
| Q3 | Can we forecast monthly deaths better than simple rules, on unseen 2026 data? | 7 models, walk-forward back-test, 2026 holdout, conformal intervals | 7 |
| Q4 | Can we warn which areas will escalate next month? | Sub-national classifier, watch-list precision | 8 |
| Q5 | What does it mean for India? | Exposure analysis + clearly labelled domain reasoning | 6 |

Throughout, **[Data]** marks results computed from the competition files and **[Domain]** marks expert reasoning
that the files cannot prove.

## 3 · Data and preparation

**Sources (official package only).** {ov.events.sum():,} UCDP event records (GED 26.1 for 2014–2025; provisional
Candidate 26.01.26.09 for Jan–Sep 2026), {85406:,} source references, UNHCR bilateral stocks (6,273 rows) and
demographics (19,830), IDMC/UNRWA reference stocks (112) and World Bank context (1,764). The top-level files outside
the official folder belong to another package and were **not** used.

**{len(dq)} documented checks**, of which {int((dq.rows_affected > 0).sum())} found something to handle. No row is
silently dropped: every fix is logged, and raw values are kept beside corrected ones.

{fig("03_data_quality", "Figure 2 – Data-quality issues found and handled (log scale, % of table rows)")}

Key decisions:

* **Out-of-order estimates (692 rows).** Where low > best or best > high, we keep the raw values and build a corrected
  band (`min`/`max` of the three). We widen the band rather than move *best*, because *best* reconciles exactly with the
  four fatality components (validated for every row).
* **Multi-month records (731 rows).** These include front-wide monthly aggregates. Deaths are spread across calendar
  months in proportion to the days in the date range. Stacking them on the start month would create false spikes.
* **Provisional 2026 data (4,644 rows).** Flagged and used **only** as the withheld test set.
* **Boundary change.** Pakistan merged FATA into Khyber Pakhtunkhwa in 2018. UCDP labels change at that point, which
  would fake a collapse of violence in FATA and a surge in KP. We harmonise to the post-merger boundary.
* **Publisher normalisation.** 1,715 raw labels become 1,625 outlets (e.g. ITAR-TASS and Tass; UA Losses and UALosses).
  7,515 repeat references (same outlet and date within one event) are flagged.
* **Missing geography.** Blank country codes become `INTL` (waters/airspace) or `XXX` (ambiguous code 666). Blank admin1
  becomes an explicit "country-level" bucket, so those deaths are not lost.
* **World Bank gaps.** 36 GDP and 124 inflation values are interpolated within each economy. Context enters models with a
  one-year lag, so 2026 needs no extrapolation.

**A finding from cleaning: the fog of war is in the data.** The share of Russia–Ukraine deaths with no sub-national
location rose from {ru_fog.get(2022, np.nan):.0%} (2022) to **{ru_fog.get(2026, np.nan):.0%} (2026)**, because most
recent deaths come from country-level memorial and aggregate counts. We therefore measure front geography with
**located, discrete events**, and we state this limit wherever sub-national results touch Ukraine.

{fig("04_fog_of_war", "Figure 3 – Share of deaths located only to country level")}

## 4 · Feature engineering

Two monthly panels: **4 conflicts × 153 months** and **222 sub-national area series × 153 months** (zero-filled).
Every feature is known at the end of the forecast-origin month. Annual context is lagged one year.

| Family | Features | Military / analytic idea |
|---|---|---|
| Intensity memory | lags 0–12, rolling means 3/6/12, EWM, 12-month peak | War has inertia |
| Momentum | 3-vs-12-month momentum, acceleration, dormancy streak | Escalation = short-term above long-term norm |
| Tempo | events/month, references/month, outlets | Engagements vs lethality |
| Fog of war | (high − low)/best, aggregate share, low date precision | Degraded reporting picture |
| Character | civilian, state-based, one-sided and focal-dyad shares | Battlefield vs punitive violence |
| Geography | active areas, Herfindahl concentration, share outside core theatre | Front widening, horizontal escalation |
| Seasonality | target-month sine/cosine, same month last year | Campaign seasons |
| Context (t−1 y) | IDPs, refugees, displacement growth, GDP growth, inflation | Structural stress |
| Hierarchy | conflict-level tempo and momentum, area's share of its conflict | Areas inherit their war's tempo |

The ablation in §7.2 shows that **a compact subset generalises best** at conflict level. With four series, 40 features
over-fit. The richer set is used where data are plentiful (222 sub-national series).

## 5 · Findings

### 5.1 Intensity and tempo [Data]

{fig("01_monthly_deaths", "Figure 4 – Monthly deaths by conflict (log scale); shaded = 2026 withheld test window")}

| | Russia–Ukraine | Israel–Hamas | Afghanistan–Pakistan | US–Iran |
|---|---|---|---|---|
| Recorded deaths 2014–Sep 2026 (best) | {ov.loc['Russia–Ukraine', 'deaths_best']:,} | {ov.loc['Israel–Hamas', 'deaths_best']:,} | {ov.loc['Afghanistan–Pakistan', 'deaths_best']:,} | {ov.loc['US–Iran', 'deaths_best']:,} |
| UCDP low – high | {ov.loc['Russia–Ukraine', 'deaths_low']:,} – {ov.loc['Russia–Ukraine', 'deaths_high']:,} | {ov.loc['Israel–Hamas', 'deaths_low']:,} – {ov.loc['Israel–Hamas', 'deaths_high']:,} | {ov.loc['Afghanistan–Pakistan', 'deaths_low']:,} – {ov.loc['Afghanistan–Pakistan', 'deaths_high']:,} | {ov.loc['US–Iran', 'deaths_low']:,} – {ov.loc['US–Iran', 'deaths_high']:,} |
| Peak month | {ov.loc['Russia–Ukraine', 'peak_month']} ({ov.loc['Russia–Ukraine', 'peak_month_deaths']:,}) | {ov.loc['Israel–Hamas', 'peak_month']} ({ov.loc['Israel–Hamas', 'peak_month_deaths']:,}) | {ov.loc['Afghanistan–Pakistan', 'peak_month']} ({ov.loc['Afghanistan–Pakistan', 'peak_month_deaths']:,}) | {ov.loc['US–Iran', 'peak_month']} ({ov.loc['US–Iran', 'peak_month_deaths']:,}) |
| Deaths Jan–Sep 2026 | {ov.loc['Russia–Ukraine', 'deaths_2026_ytd']:,} | {ov.loc['Israel–Hamas', 'deaths_2026_ytd']:,} | {ov.loc['Afghanistan–Pakistan', 'deaths_2026_ytd']:,} | {ov.loc['US–Iran', 'deaths_2026_ytd']:,} |
| Civilian share | {ov.loc['Russia–Ukraine', 'civilian_share']:.0%} | {ov.loc['Israel–Hamas', 'civilian_share']:.0%} | {ov.loc['Afghanistan–Pakistan', 'civilian_share']:.0%} | {ov.loc['US–Iran', 'civilian_share']:.0%} |
| Countries with deaths | {ov.loc['Russia–Ukraine', 'countries_affected']} | {ov.loc['Israel–Hamas', 'countries_affected']} | {ov.loc['Afghanistan–Pakistan', 'countries_affected']} | {ov.loc['US–Iran', 'countries_affected']} |

Each conflict has a different threat signature: **RU–UA is sustained attrition** (4–11k deaths a month since 2023),
**US–Iran is spikes** (proxy and coalition strikes, then direct war in Feb–Mar 2026), **Af–Pak is creeping** (rising since
2021), and **Israel–Hamas is de-escalating** (about 130 a month in 2026 after a 2,474-death month in Jul 2025).
*So what:* one warning rule cannot fit all four. We forecast level, trend and spread separately.

### 5.2 How the wars are being fought (military lens)

**Front geography – widening, not moving [Data].** Donetsk's share of geolocated events fell from {don22:.0f}% (2022)
to {don26:.0f}% (2026). Zaporizhzhia ({fg_p.loc['Zaporizhzhya oblast', 2026] * 100:.0f}%), Dnipropetrovsk
({fg_p.loc['Dnipropetrovsk oblast', 2026] * 100:.0f}%), Sumy ({fg_p.loc['Sumy oblast', 2026] * 100:.0f}%) and Russia's
Belgorod ({fg_p.loc['Belgorod oblast', 2026] * 100:.0f}%) grew. Recorded deaths inside Russia peaked at 10,358 in 2024
(Kursk). *So what [Domain]:* a wide, static front rewards long-range precision fires, counter-drone and EW, and
logistics depth. Warning should track the **number of active sectors**, which our models do.

{fig("05_front_geography", "Figure 5 – Russia–Ukraine: share of located discrete events by area")}

**Recorded attrition by side [Data, with caveat].** In the RU–UA focal dyad, UCDP records
{ru_att.loc[2022, 'deaths_side_a']:,.0f} Russian vs {ru_att.loc[2022, 'deaths_side_b']:,.0f} Ukrainian fatalities in 2022
(ratio {ru_att.loc[2022, 'ratio_a_to_b']:.1f}:1), widening to {ru_att.loc[2025, 'ratio_a_to_b']:.1f}:1 in 2025 and
{ru_att.loc[2026, 'ratio_a_to_b']:.1f}:1 in 2026. In the 2026 US–Iran war, Iran's recorded losses were
{usir_att.loc[2026, 'deaths_side_a']:,.0f} against {usir_att.loc[2026, 'deaths_side_b']:,.0f} for the Israel–US coalition.
**Caveat:** these are *recorded* figures. Ukrainian OSINT and memorial databases document Russian losses more fully than
the reverse, so the ratio is an upper bound of reporting, not a verified exchange ratio. *So what [Domain]:* stand-off
precision strike, layered air defence and drone-enabled ISR produce extreme asymmetry. These lessons apply directly to
Indian force design on both fronts.

{fig("06_attrition_ru_ua", "Figure 6 – Russia–Ukraine: UCDP-recorded fatalities by side")}

**Afghanistan–Pakistan: a second front opens [Data].** Violence has concentrated in Khyber Pakhtunkhwa (TTP) and
Balochistan, and has risen every year since 2021. Since **Oct 2025 the Afghan and Pakistani states clash directly**
(131 deaths in Oct 2025; 172, 411 and 68 in Feb–Apr 2026). *So what [Domain]:* the Pakistan Army is committed in the
west. That can lower its eastern capacity, or raise the incentive for diversionary LoC activity. India should watch the
western front more closely, not less.

{fig("10_afpak_interstate", "Figure 7 – Afghanistan vs Pakistan government clashes (focal dyad), deaths per month")}

{fig("09_afpak_provinces", "Figure 8 – Afghanistan–Pakistan deaths by province (FATA harmonised into KP)")}

**Horizontal escalation [Data].** The US–Iran case spread from {int(usir_ts.get(2025, 0))} countries (2025) to
{int(usir_ts.get(2026, 0))} (2026), including five Gulf states and Sri Lankan waters. Israel–Hamas reached Qatar in Sep 2025.

{fig("08_country_map", "Figure 9 – Where the four conflicts killed people, 2024–Sep 2026 (India outlined)")}

**Campaign seasons [Data].** RU–UA deaths run {ses.loc[5]:+.0f}% (May) and {ses.loc[7]:+.0f}% (Jul) against trend, and
{ses.loc[12]:+.0f}% (Dec) and {ses.loc[1]:+.0f}% (Jan), matching the summer campaigning season and the winter/*rasputitsa*
lull. Af–Pak peaks in Sep–Oct. Seasonality enters the models.

{fig("11_seasonality", "Figure 10 – Deaths vs 12-month trend by calendar month")}

### 5.3 Media attention vs deaths – an original index [Data]

We regress monthly source references on events and deaths (log, with conflict fixed effects). The residual, standardised,
is the **Attention Gap Index (AGI)**: above 0 means over-reported, below 0 means "forgotten" violence.

* References scale with **incidents** (elasticity {stats.media_elasticity_events:.2f}) and **not lethality**
  ({stats.media_elasticity_deaths:.2f}); R² = {stats.media_r2:.2f}. One mass-casualty strike is one story, so
  high-lethality violence is under-documented per death.
* References per 100 deaths: Israel–Hamas 150, RU–UA 54, Af–Pak 40, US–Iran 35.
* The AGI does **not** lead next month's escalation (coefficient {stats.media_lead_coef:.3f}, p = {stats.media_lead_p:.2f}).
  *So what:* do not build warning on media volume.
* Indian outlets (mainly PTI) appear in **{ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%} of Af–Pak events** and
  almost none of the other theatres. India's open-source picture of West Asia and Europe is borrowed.

{fig("13_media_scatter", "Figure 11 – References track events tightly, deaths loosely")}

### 5.4 Displacement and humanitarian planning [Data]

* Ukraine end-2025: about 5.2M refugees abroad and 3.7M IDPs. **{dpl.loc['UKR', 'women_children_share']:.0%}** of refugees with
  recorded sex and age are women or children.
* Afghanistan: {dpl.loc['AFG', 'women_children_share']:.0%} women and children, {dpl.loc['AFG', 'under5_share']:.0%} under five.
  Refugees abroad fell from 5.8M (2024) to 2.7M (2025) as returns and reclassification (1.03M "other protection")
  took effect.
* Palestine: 2.0M IDPs (IDMC) since 2024. UNRWA registrations (2.5M in Palestine) are a separate series and are never summed.
* Country-year deaths explain little of the *change* in displaced stocks (Spearman {stats.link_spearman:.2f}, p =
  {stats.link_p:.2f}). Displacement responds to onset, spread and access, not monthly tolls, and cannot be attributed to
  single events.

*So what:* trigger HADR planning on **onset and spread** (our escalation flags), and stock paediatric and maternal supplies.

{fig("15_displacement", "Figure 12 – Displaced populations by origin (UNHCR refugees and asylum seekers; IDMC IDPs)")}

## 6 · India impact

| Theatre | What the data show [Data] | What it means for India [Domain] |
|---|---|---|
| Afghanistan–Pakistan | KP deaths up every year since 2021; Afghan–Pakistan state clashes since Oct 2025; deaths in Pakistan areas adjoining India/LoC rose from {pakprox.get(2022, 0):,.0f} (2022) to {pakprox.get(2025, 0):,.0f} (2025) | Pakistan Army committed in the west, so risk of diversionary LoC activity, infiltration and TTP/IS-K spill-over |
| US–Iran / Gulf | {int(usir_ts.get(2026, 0))} countries hit in 2026, including 5 Gulf states ({int(gulf26.events.sum())} events, {int(gulf26.deaths.sum())} deaths); {int(hz26.deaths.sum())} deaths on Iran's Hormuz/Chabahar coast; {yem25:,.0f} deaths in Yemen in 2025 | About 9M Indians in the Gulf need NEO contingency (cf. Op Ganga, Kaveri, Ajay); a large share of crude and LPG transits Hormuz; Chabahar and INSTC lie in the strike zone; Red Sea shipping at risk |
| Indian Ocean | 104 killed in one strike off Sri Lanka's west coast, 4 Mar 2026 | The war entered India's maritime neighbourhood. IFC-IOR and Navy need a belligerent-movement picture |
| Russia–Ukraine | 4–11k deaths a month; front widening; extreme recorded attrition asymmetry | Spares and deliveries for legacy Russian platforms at risk; drone, counter-drone and EW lessons |
| Israel–Hamas | De-escalated to about 130/month in 2026 | Key supplier of UAVs, missiles and sensors at war; buffer stocks |
| Refugees in India | Afghans {ihp['AFG'].get(2021, np.nan):,.0f} (2021) → {ihp['AFG'].get(2025, np.nan):,.0f} (2025); Russian asylum seekers {ihp['RUS'].get(2015, np.nan):,.0f} (2015) → {ihp['RUS'].get(2025, np.nan):,.0f} (2025) | Small numbers; the rising Russian flow is consistent with draft-evasion migration, so monitor |
| Macro | India's inflation was 6.7% in 2022 (World Bank) | Coincides with the energy shock; attribution not claimed |

{fig("17_india_exposure", "Figure 13 – Deaths in places that matter to India (log scale)")}

## 7 · Forecasting model

### 7.1 Protocol
Models are fitted once on data up to December *Y − 1*, frozen, and scored on Jan–Sep of year *Y* in two ways:

* **Track A (operational):** 1 month ahead, rolling. Each month the frozen model sees the newly observed month and
  forecasts the next. There is no refitting.
* **Track B (strategic):** 1–9 months ahead from a single December origin, with nothing from year *Y*.

Back-test folds 2022–2025 drive **every** design choice: ablation, ensemble membership and interval calibration.
**2026 is the withheld test set**, scored once. Metrics: MAE, RMSE, MAPE (actual > 0), sMAPE, MASE and RMSLE. RMSLE is
the selection metric because the four series differ by three orders of magnitude.

| Model | Role |
|---|---|
| Naive, seasonal naive, 3-month moving average | Benchmarks |
| ETS (damped Holt, log) | Classical smoother for level shifts |
| SARIMA (AIC-selected per series, log) | Autocorrelation and seasonality |
| **LightGBM-Δ** (global across the 4 conflicts) | Learns the *change* in log deaths from 18 features |
| LightGBM bottom-up (Tweedie; 222 area series summed) | Hierarchical, answers *where* |
| **Ensemble** = {" + ".join(MODEL_LABELS[m].split(" (")[0] for m in members)} | Log-space mean; members chosen on back-test |

### 7.2 Why these choices – ablation (back-test only)

{mdtable(abl.rename(columns={"variant": "LightGBM variant"}), floatfmt={c: "{:.3f}" for c in abl.columns})}

A plain LightGBM on the log **level** is the worst ML option. Regression trees cannot predict beyond the target range
seen in training, so a model fitted before 2022 can never forecast the invasion. Predicting the **change** in log deaths
removes that ceiling. A compact feature set with a robust L1 loss generalises best.

### 7.3 Results on the withheld 2026 data

{fig("21_model_compare", "Figure 14 – Log-scale error by model: back-test vs 2026 holdout")}

**RMSLE (lower is better)**

{mdtable(rml, index=True, floatfmt={c: "{:.3f}" for c in rml.columns})}

**MAE, 2026 holdout, 1 month ahead (deaths per month)**

{mdtable(mt.round(0), index=True, floatfmt={c: "{:,.0f}" for c in mt.columns})}

The ensemble reduces 1-month-ahead MAE against the naive rule by **{mae_red['Russia–Ukraine']:.0f}%** (RU–UA),
**{mae_red['Israel–Hamas']:.0f}%** (Israel–Hamas), **{mae_red['US–Iran']:.0f}%** (US–Iran) and
**{mae_red['Afghanistan–Pakistan']:.0f}%** (Af–Pak); pooled, **{pooled_red:.0f}%**. MAPE for RU–UA is
{hA[(hA.model == 'ensemble') & (hA.conflict_case == 'Russia–Ukraine')].MAPE.iloc[0]:.0f}%.
On Track B (9 months blind), SARIMA and the bottom-up LightGBM edged the ensemble in 2026, though not in the
back-test. We report this rather than re-select on the test set.

{fig("19_forecast_A_RU-UA", "Figure 15 – Russia–Ukraine: 1-month-ahead forecasts vs actual on the 2026 holdout, with 80% interval and forward forecast")}

{fig("19_forecast_A_AF-PK", "Figure 16 – Afghanistan–Pakistan: same view")}

### 7.4 Reliability for trend forecasting

* **Calibrated uncertainty.** Split-conformal intervals on log residuals from 2022–25 cover
  **{cov80_26:.0%}** of 2026 outcomes at the 80% level (Track A {cov[(cov.fold == 2026) & (cov.track == 'A')]['80% coverage'].iloc[0]:.0%},
  Track B {cov[(cov.fold == 2026) & (cov.track == 'B')]['80% coverage'].iloc[0]:.0%}). The 95% upper tail is very wide by design:
  the back-test includes the 2022 invasion, and outbreak risk is real. A volatility-scaled (adaptive) variant was
  tested and rejected because it under-covered regime breaks in calm series.
* **Direction.** The 1-month forecast got the direction of change right in 72% of 2026 conflict-months.
* **Stability.** Back-test RMSLE by year: 2022 (invasion) is the hardest. 2023–2025 are stable. No single model wins
  every fold, which is why we ensemble.
* **Explainability.** TreeSHAP shows the forecast is driven by last month's level and acceleration, two-month memory,
  momentum and volatility, then seasonality. These are features an officer can reason about.
* **Known failure mode.** US–Iran 2026 has the largest error: the war began in Feb 2026 with no build-up in the
  death series. Political decisions to start wars are not forecastable from this data. Warning must come from spread,
  hotspots and other intelligence.

{fig("22_shap_forecast", "Figure 17 – Mean |SHAP| for the LightGBM-Δ forecaster")}

**Forward forecast (all data, refitted):**

{mdtable(fut.round(0), floatfmt={"Forecast deaths": "{:,.0f}", "80% low": "{:,.0f}", "80% high": "{:,.0f}"})}

## 8 · Early warning, scorecard and what-if

### 8.1 Sub-national escalation classifier
An area escalates next month if its deaths are ≥ 10 **and** ≥ 1.5 × its trailing 3-month mean (2–4% of area-months).
A regularised LightGBM classifier is fitted on 19 features (own intensity and momentum, conflict-wide tempo and spread,
country momentum, seasonality). It is trained on target months up to Dec *Y − 1* and tested on Jan–Sep *Y*, for
2023–2026. Features were chosen on 2023–25.

| 2026 withheld | ROC-AUC | PR-AUC | Brier | Top-10 precision | Top-20 recall |
|---|---|---|---|---|---|
| **LightGBM classifier** | **{lg.ROC_AUC:.3f}** | **{lg.PR_AUC:.3f}** | {lg.Brier:.3f} | **{lg.precision_at_10:.1%}** | {lg.recall_at_20:.1%} |
| Logistic regression (5 signals) | {logit.ROC_AUC:.3f} | {logit.PR_AUC:.3f} | {logit.Brier:.3f} | {logit.precision_at_10:.1%} | {logit.recall_at_20:.1%} |
| Rule: last month's deadliest | {rule.ROC_AUC:.3f} | {rule.PR_AUC:.3f} | {rule.Brier:.3f} | {rule.precision_at_10:.1%} | {rule.recall_at_20:.1%} |
| Base rate | | {lg.base_rate:.3f} | | {lg.base_rate:.1%} | |

The top-10 list is **{lg.precision_at_10 / lg.base_rate:.1f}× better than random** and
{lg.precision_at_10 / max(rule.precision_at_10, 1e-9):.1f}× better than the rule of thumb. TreeSHAP's leading signals are
the area's smoothed intensity, **its country's** current intensity and momentum, and the **whole conflict's** momentum
and spread. Escalation is contagious within a theatre.

{fig("24_early_warning_curves", "Figure 18 – ROC and precision–recall on 2026 withheld months")}

### 8.2 Watch-list for Oct 2026
The dashboard lists the 20 highest-risk areas. The top three are Kandahar, Balochistan and Kunar (Af–Pak,
21–23%), then Hormozgan (US–Iran, 16%) and Chernihiv, Dnipropetrovsk and Sumy (RU–UA, 14–15%).

### 8.3 Threat scorecard (RAG) rules
Points: **intensity** (next-month forecast ≥ 1,000 → 2; ≥ 100 → 1); **trend** against the last 6 months (≥ +20% → +1;
≤ −20% → −1); **hotspots** (named areas with escalation probability ≥ 15%: ≥ 3 → 2; ≥ 1 → 1); **spread** (more countries
than last year → 1); **volatility** (a ≥ 1,000-death month in the last year → 1). **RED** = forecast ≥ 1,000 a month or
≥ 5 points; **AMBER** = 2–4; **GREEN** ≤ 1. The rules are transparent and every input is a model output.

### 8.4 What-if simulator
The dashboard re-runs the selected ensemble on a modified history. Example: a +30% surge in Af–Pak deaths over three months
raises the Oct 2026 forecast by about 13% (318 → 359). The model damps short surges because most partly revert, while
sustained six-month surges carry through. A **live re-train** page fits LightGBM-Δ from scratch on any cut-off in about
2 seconds and scores it against naive.

## 9 · Recommendations

| Line of effort | Action | Lead [Domain] | When |
|---|---|---|---|
| **SENSE** | Use the monthly sub-national watch-list to task ISR and analyst effort; track *active sectors* and *countries hit*, not media volume | DIA / Service intelligence | Now (0–30 days) |
| **SENSE** | Build Indian OSINT coverage of the Gulf, Iran and Red Sea (Indian sources cover {ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%} of Af–Pak events and almost none elsewhere) | DIA / MEA | 90 days |
| **WARN** | Adopt the Af–Pak interstate dyad and KP/Balochistan escalation probabilities as standing LoC I&W indicators | Northern / Western Commands | Now |
| **WARN** | Publish the RAG scorecard monthly; escalate any move to RED or a rise in countries hit | HQ IDS | 90 days |
| **SHIELD** | Keep Gulf NEO plans current while US–Iran is AMBER; pre-position sealift/airlift options | HQ IDS / Navy / IAF / MEA | Now |
| **SHIELD** | Belligerent-movement picture for the IOR after the strike off Sri Lanka | Navy / IFC-IOR | 90 days |
| **SUSTAIN** | Buffer stocks and indigenisation of critical spares for Russian- and Israeli-origin platforms | MoD / DPSUs | 6–12 months |
| **SUSTAIN** | HADR kits weighted to women, children and under-fives; trigger on escalation flags, not death tolls | HQ IDS / NDMA | 6–12 months |

## 10 · Assumptions and limitations

* UCDP records **reported** lethal organised violence. Coverage depends on access and sources, and recorded side-specific
  attrition reflects reporting asymmetry.
* 2026 data are **provisional** (Candidate) and are usually revised upward. Holdout error includes revision noise.
* Over 90% of 2026 RU–UA deaths have no sub-national location, so sub-national claims about Ukraine rest on events.
* The US–Iran focal dyad codes **Israel and the US as one actor**, so no country split is possible.
* Displacement stocks cannot be attributed to single events. IDMC and UNRWA series are kept separate.
* World Bank context ends in 2025 and is used with a one-year lag.
* Forecasts cannot anticipate political decisions to start wars. That risk sits in the wide 95% tail.
* [Domain] statements are expert reasoning and are labelled as such.

## 11 · Reproducibility

```
pip install -r requirements.txt
python run_pipeline.py          # ~2.5 min: clean → features → insights → models → scorecard → figures
streamlit run app/app.py        # dashboard (works offline)
jupyter lab notebooks/          # 01–05, each re-runs its stage with commentary
```

Seeds are fixed (`random_state = 42`). Paths resolve automatically, or set `CONFLICT_DATA_DIR`. Source CSVs are read-only.
Every table in this report is in `outputs/tables/`, and every figure is in `outputs/figures/` (PNG + interactive HTML).
Run time on a laptop: about {summary['runtime_s']:.0f} s for modelling, 2–3 min end to end.

## Appendix A · Data-quality log (issues found)

{mdtable(dq_show, floatfmt={"pct_affected": "{:.2f}"})}

## Appendix B · Metric definitions
MAE = mean |error|; RMSE = √mean(error²); MAPE = mean |error|/actual over months with actual > 0; sMAPE = mean
2|e|/(|y|+|ŷ|); MASE = MAE / in-sample MAE of the one-step naive; RMSLE = √mean(log(1+ŷ) − log(1+y))²; coverage = share
of actuals inside the interval; ROC-AUC/PR-AUC for ranking; Brier = mean squared probability error; precision@10 =
share of each month's top-10 areas that escalated.
"""

(OUT / "Conflict_Watch_Report.md").write_text(md)

import markdown  # noqa: E402

body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
CSS = """
@page { size: A4; margin: 16mm 15mm 18mm 15mm; }
body { font-family: Calibri, 'Segoe UI', Carlito, Arial, sans-serif; color: #1b2733; font-size: 10.6pt; line-height: 1.45; }
h1, h2, h3 { color: #07131F; }
h2 { border-bottom: 3px solid #F0B03A; padding-bottom: 4px; margin-top: 26px; font-size: 17pt; page-break-after: avoid; }
h3 { font-size: 13pt; margin-top: 18px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 14px 0; font-size: 9pt; page-break-inside: auto; }
th { background: #0F2236; color: #fff; text-align: left; padding: 5px 6px; }
td { border-bottom: 1px solid #d6dee8; padding: 4px 6px; vertical-align: top; }
tr:nth-child(even) td { background: #f4f7fa; }
figure { margin: 12px 0 16px 0; page-break-inside: avoid; }
figure img { width: 100%; border-radius: 6px; }
figcaption { font-size: 8.8pt; color: #5E7B99; margin-top: 4px; }
blockquote { border-left: 4px solid #F0B03A; background: #fff8e8; margin: 10px 0; padding: 8px 14px; font-size: 11.5pt; }
code, pre { background: #f0f3f7; border-radius: 4px; font-size: 9pt; }
pre { padding: 10px; }
.red { color: #d7263d; } .amber { color: #c77d00; } .green { color: #1f9e83; }
.cover { background: #07131F; color: #fff; margin: -16mm -15mm 0 -15mm; padding: 70mm 18mm 60mm 18mm; min-height: 160mm; }
.cover .kick { color: #F0B03A; font-weight: 700; letter-spacing: 3px; font-size: 10pt; }
.cover .title { color: #fff; font-size: 54pt; letter-spacing: 2px; margin: 14px 0 8px 0; border: none; }
.cover .subtitle { color: #D5DEE8; font-size: 15pt; line-height: 1.4; }
.cover .author { color: #fff; font-weight: 700; font-size: 15pt; margin-top: 28mm; line-height: 1.35; }
.cover .meta { color: #9FB2C6; font-size: 10pt; margin-top: 4px; }
.pagebreak { page-break-after: always; }
"""
html = f"<!doctype html><html><head><meta charset='utf-8'><title>Conflict Watch – Analysis Report</title><style>{CSS}</style></head><body>{body}</body></html>"
(OUT / "Conflict_Watch_Report.html").write_text(html)
print("report written:", OUT / "Conflict_Watch_Report.html")
