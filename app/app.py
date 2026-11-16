"""CONFLICT WATCH - interactive dashboard for the Data Analytics Competition 2026.

Run from the submission folder:
    streamlit run app/app.py

It reads the artefacts written by ``python run_pipeline.py`` (already included),
so it starts in seconds and works offline. The What-if and Live re-train pages
run the real models on the fly.
"""
from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config as C, viz  # noqa: E402
from src import models as M  # noqa: E402

T = C.THEME
st.set_page_config(page_title="Conflict Watch | Data Analytics Competition 2026", page_icon="🛰️", layout="wide",
                   initial_sidebar_state="expanded")

# ---------------------------------------------------------------------------
# Styling: the jury-deck theme, sized for a video call
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
html, body, [class*="css"] {{ font-size: 18px; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }}
h1, h2, h3 {{ color: {T['text']} !important; letter-spacing: 0.2px; }}
h1 {{ font-size: 2.3rem !important; }} h2 {{ font-size: 1.7rem !important; }} h3 {{ font-size: 1.35rem !important; }}
section[data-testid="stSidebar"] {{ background: {T['panel']}; border-right: 1px solid {T['border']}; }}
section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {{ font-size: 1.05rem !important; }}
.kicker {{ color: {T['amber']}; font-weight: 700; font-size: 0.95rem; letter-spacing: 2px; text-transform: uppercase;
          margin-bottom: -0.4rem; }}
.card {{ background: {T['panel']}; border: 1px solid {T['border']}; border-radius: 12px; padding: 18px 20px;
        height: 100%; }}
.card .lab {{ color: {T['text3']}; font-size: 0.85rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }}
.card .big {{ font-size: 2.6rem; font-weight: 800; line-height: 1.1; margin: 6px 0 4px 0; }}
.card .sub {{ color: {T['text2']}; font-size: 1.0rem; }}
.card .note {{ color: {T['text3']}; font-size: 0.85rem; margin-top: 6px; }}
.sowhat {{ background: {T['amber_bg']}; border: 1px solid {T['amber']}; border-radius: 10px; padding: 12px 18px;
          color: {T['text']}; font-size: 1.05rem; margin: 10px 0 18px 0; }}
.sowhat b {{ color: {T['amber']}; letter-spacing: 1.5px; margin-right: 10px; }}
.rag {{ border-radius: 14px; padding: 16px 18px; background: {T['panel']}; text-align: center; }}
.rag .case {{ color: {T['text']}; font-size: 1.25rem; font-weight: 700; }}
.rag .rating {{ font-size: 2.6rem; font-weight: 900; letter-spacing: 2px; margin: 4px 0; }}
.rag .line {{ color: {T['text2']}; font-size: 1.0rem; }}
.rag .small {{ color: {T['text3']}; font-size: 0.88rem; margin-top: 6px; }}
.tag-data {{ background: {T['teal']}; color: {T['bg']}; border-radius: 6px; padding: 1px 8px; font-weight: 700;
            font-size: 0.8rem; }}
.tag-dom {{ background: {T['violet']}; color: {T['bg']}; border-radius: 6px; padding: 1px 8px; font-weight: 700;
           font-size: 0.8rem; }}
div[data-testid="stMetricValue"] {{ font-size: 2.2rem; }}
.stTabs [data-baseweb="tab"] {{ font-size: 1.05rem; }}
.footer {{ color: {T['muted']}; font-size: 0.8rem; letter-spacing: 1.5px; margin-top: 30px; }}
</style>
""", unsafe_allow_html=True)


def kicker(t):
    st.markdown(f'<div class="kicker">{t}</div>', unsafe_allow_html=True)


def sowhat(t, label="SO WHAT"):
    st.markdown(f'<div class="sowhat"><b>{label}</b>{t}</div>', unsafe_allow_html=True)


def card(label, big, sub, color=None, note=""):
    st.markdown(f'<div class="card"><div class="lab">{label}</div><div class="big" style="color:{color or T["amber"]}">'
                f'{big}</div><div class="sub">{sub}</div><div class="note">{note}</div></div>',
                unsafe_allow_html=True)


def show(fig, key=None, height=None):
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, theme=None, key=key, config={"displaylogo": False})


def download(df, name, label="Download CSV"):
    st.download_button(f"⬇ {label}", df.to_csv(index=False).encode("utf-8"), file_name=f"{name}.csv",
                       mime="text/csv", key=f"dl_{name}")


DATA_TAG = '<span class="tag-data">DATA</span>'
DOM_TAG = '<span class="tag-dom">DOMAIN</span>'


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
P, TB = C.PROCESSED, C.TAB_DIR


@st.cache_data(show_spinner=False)
def load_all():
    d = dict(
        events=pd.read_parquet(P / "events.parquet"),
        cm=pd.read_parquet(P / "case_month.parquet"),
        am=pd.read_parquet(P / "admin1_month.parquet"),
        preds=pd.read_parquet(P / "forecast_preds.parquet"),
        future=pd.read_parquet(P / "forecast_future.parquet"),
        admin_future=pd.read_parquet(P / "admin1_future.parquet"),
        ew_preds=pd.read_parquet(P / "early_warning_preds.parquet"),
        ew_live=pd.read_parquet(P / "early_warning_live.parquet"),
        dq=pd.read_csv(TB / "data_quality_log.csv"),
        scores=pd.read_csv(TB / "forecast_scores.csv"),
        rmsle=pd.read_csv(TB / "forecast_rmsle.csv"),
        ens=pd.read_csv(TB / "ensemble_selection.csv"),
        abl=pd.read_csv(TB / "ablation_lgb.csv"),
        ew_rep=pd.read_csv(TB / "early_warning_scores.csv"),
        rag=pd.read_csv(TB / "rag_scorecard.csv", parse_dates=["forecast_month"]),
        shap_case=pd.read_csv(TB / "shap_lgb_case.csv"),
        shap_ew=pd.read_csv(TB / "shap_early_warning.csv"),
        stats=pd.read_csv(TB / "insight_stats.csv").iloc[0].to_dict(),
    )
    for k in ["case_overview", "attrition", "front_geography", "geo_precision", "theatre_spread", "country_deaths",
              "seasonality", "violence_mix", "dyads", "afpak_provinces", "media", "outlet_mix", "displacement",
              "unrwa", "demographics_profile", "hosts", "india_hosted", "india_context", "india_exposure",
              "indian_press"]:
        d[k] = pd.read_csv(TB / f"insight_{k}.csv")
    d["media"]["month"] = pd.to_datetime(d["media"]["month"])
    return d


@st.cache_resource(show_spinner=False)
def load_models():
    return joblib.load(ROOT / "models" / "models.joblib")


try:
    D = load_all()
except FileNotFoundError:
    st.error("Artefacts not found. Run `python run_pipeline.py` from the submission folder first.")
    st.stop()

cm, E = D["cm"], D["events"]
LAST = cm.month.max()

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
PAGES = ["🎯 Commander's brief", "📊 Conflict explorer", "📍 Area drill-down", "⚔️ Military lens", "🇮🇳 India impact",
         "🏠 Displacement", "📡 Media attention", "📈 Forecast (2026 test)", "🚨 Early warning",
         "🧪 What-if simulator", "🎛️ Scorecard lab", "🧹 Data quality & method"]
with st.sidebar:
    st.markdown(f"<div style='color:{T['amber']};font-weight:800;letter-spacing:3px;font-size:1.0rem'>DATA ANALYTICS COMPETITION 2026</div>"
                f"<div style='color:{T['text']};font-weight:900;font-size:1.9rem;line-height:1.1'>CONFLICT WATCH</div>"
                f"<div style='color:{T['text3']};font-size:0.95rem;margin-bottom:12px'>When and where will deaths rise next, "
                f"and what does it mean for India?</div>", unsafe_allow_html=True)
    MODES = ["🛰️ Ops site", "📊 Analyst dashboard"]
    mode = st.radio("Mode", MODES, horizontal=True, label_visibility="collapsed", key="mode")
    st.markdown("---")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed") if mode == MODES[1] else None
    if mode == MODES[0]:
        st.markdown("The **Ops site** is the story and the ops console in one: scroll the story, or press "
                    "**OPS CONSOLE** for the staff-officer view. Switch to *Analyst dashboard* for the 12-page tool.")
        st.link_button("⤢ Open full screen", "https://conflictmonitor2026.streamlit.app/~/+/app/static/site/index.html", use_container_width=True)
    st.markdown("---")
    st.caption(f"Data: UCDP GED 26.1 (2014–25) + Candidate 26.01.26.09 (Jan–Sep 2026, provisional), UNHCR, IDMC, "
               f"UNRWA, World Bank. Latest month: {LAST:%b %Y}.")
    st.caption("Team: Maj Shivam Mehta · Capt Siddharth Sangwan · Capt Sahil Singh")
    st.caption("UNCLASSIFIED · OPEN-SOURCE DATA ONLY")


SITE = ROOT / "app" / "static" / "conflictwatch.html"
if page is None:
    import streamlit.components.v1 as components
    st.markdown("<style>.block-container,[data-testid=stMainBlockContainer]{padding:0.6rem 1rem 0 1rem!important;max-width:100%!important}"
                "header[data-testid='stHeader']{background:transparent}</style>", unsafe_allow_html=True)
    if SITE.exists():
        components.html(SITE.read_text(encoding="utf-8"), height=940, scrolling=True)
    else:
        st.warning("Ops site not built. Run `cd web && npm run build` then `python scripts/build_site.py`.")
    st.stop()


def footer():
    st.markdown('<div class="footer">CONFLICT WATCH  |  DATA ANALYTICS COMPETITION 2026  |  UNCLASSIFIED - OPEN-SOURCE DATA ONLY</div>',
                unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 1. Commander's brief
# ---------------------------------------------------------------------------
def page_brief():
    kicker("Bottom line up front")
    st.markdown("# Four wars, three warning signals, one exposed neighbour")
    rag = D["rag"]
    cols = st.columns(4)
    for c, (_, r) in zip(cols, rag.iterrows()):
        col = C.RAG_COLORS[r.rating]
        with c:
            st.markdown(
                f'<div class="rag" style="border:3px solid {col}"><div class="case">{r.conflict_case}</div>'
                f'<div class="rating" style="color:{col}">{r.rating}</div>'
                f'<div class="line"><b>{r.forecast_next:,.0f}</b> deaths forecast {r.forecast_month:%b %Y}</div>'
                f'<div class="small">80% range {r.pi80_lo:,.0f}–{r.pi80_hi:,.0f} · trend {r.trend_ratio - 1:+.0%} vs 6 mo'
                f'<br>{int(r.hotspots)} hotspot area(s) · {int(r.score)} pts</div></div>', unsafe_allow_html=True)
            with st.expander("Why this rating?"):
                st.markdown(f"Intensity **{int(r.pts_intensity):+d}** · trend **{int(r.pts_trend):+d}** · hotspots "
                            f"**{int(r.pts_hotspots):+d}** · spread **{int(r.pts_spread):+d}** · volatility "
                            f"**{int(r.pts_volatility):+d}**  \nTop areas: {r.top_areas}  \nChange the rules live in "
                            "**🎛️ Scorecard lab**.")
    st.markdown("")
    h = D["scores"]
    hold = h[(h.fold == 2026) & (h.track == "A")]
    base = hold[hold.model == "naive"].set_index("conflict_case").MAE
    ens = hold[hold.model == "ensemble"].set_index("conflict_case").MAE
    red = (1 - ens.sum() / base.sum())
    ew26 = D["ew_rep"][(D["ew_rep"].year == 2026) & (D["ew_rep"].model == "LightGBM classifier")].iloc[0]
    p = D["preds"]
    e26 = p[(p.model == "ensemble") & (p.fold == 2026)]
    cov = ((e26.actual >= e26.pi80_lo) & (e26.actual <= e26.pi80_hi)).mean()
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Forecast", f"−{red:.0%}", "error vs 'no-change' rule, 1 month ahead, on unseen 2026 data",
             T["cyan"], "Ensemble of ETS, moving average and LightGBM-Δ")
    with c2:
        card("Warning", f"{ew26.ROC_AUC:.2f} AUC", f"sub-national escalation, 2026 · top-10 list "
             f"{ew26.precision_at_10 / ew26.base_rate:.1f}× better than random", T["amber"])
    with c3:
        card("Reliability", f"{cov:.0%}", "of 2026 outcomes inside the 80% interval", T["teal"],
             "Conformal intervals calibrated on 2022–25")
    with c4:
        card("India", "104", "killed off Sri Lanka, 4 Mar 2026: the US–Iran war reached the Indian Ocean", T["red"],
             "Plus strikes in 5 Gulf states hosting the Indian diaspora")
    st.markdown("")
    l, r = st.columns([1.15, 1])
    with l:
        kicker("Key findings")
        st.markdown(f"""
1. **Russia–Ukraine is a sustained attrition war**: 4–11k recorded deaths a month since 2023 (median 7.8k). The front is
   **widening, not moving**: Donetsk's share of located events fell from 55% to 30% as Zaporizhzhia, Dnipropetrovsk,
   Sumy and Russia's border oblasts rose. {DATA_TAG}
2. **Af–Pak has become a two-front problem for Pakistan**: the TTP insurgency in Khyber Pakhtunkhwa has grown every
   year since 2021, and since Oct 2025 the two **governments fight each other directly** (411 deaths in Mar 2026). {DATA_TAG}
3. **US–Iran escalated from proxy strikes to direct war in Feb–Mar 2026**: 14 countries were hit, with 299 deaths
   on Iran's Hormuz/Chabahar coast. {DATA_TAG}
4. **Israel–Hamas has de-escalated** to about 130 deaths a month in 2026, but it had a 2,474-death month as recently as Jul 2025. {DATA_TAG}
5. **Forecastable vs not**: tempo and spread give sub-national warning a month ahead. A decision to go to war
   (Feb 2022, Feb 2026) does not show up in death counts beforehand, so watch spread and hotspots, not media volume. {DATA_TAG}
""", unsafe_allow_html=True)
    with r:
        kicker("India: what it means")
        st.markdown(f"""
| Theatre | Impact on India | Basis |
|---|---|---|
| Af–Pak | Pakistan stretched on its western front; risk of diversion along the LoC; TTP spill-over | {DATA_TAG} + {DOM_TAG} |
| US–Iran / Gulf | Diaspora of about 9M in the Gulf; Hormuz energy flows; Chabahar–INSTC in the strike zone | {DATA_TAG} + {DOM_TAG} |
| Indian Ocean | War reached Sri Lanka's waters, so maritime domain awareness and NEO readiness matter | {DATA_TAG} |
| Russia–Ukraine | Legacy-platform spares and S-400 deliveries at risk; lessons on drones and attrition | {DOM_TAG} |
| Israel–Hamas | Supplier of UAVs, missiles and sensors at war; Red Sea shipping | {DOM_TAG} |
""", unsafe_allow_html=True)
    sowhat("Task ISR on the escalation watch-list, not on headlines. Pre-position for a Gulf NEO while US–Iran is "
           "AMBER. Treat the Af–Pak interstate front as a standing indicator for the LoC.", "SO WHAT")
    footer()


# ---------------------------------------------------------------------------
# 2. Explorer
# ---------------------------------------------------------------------------
def page_explorer():
    kicker("Explore the data")
    st.markdown("# Conflict explorer")
    c1, c2, c3 = st.columns([2, 2, 1])
    cases = c1.multiselect("Conflicts", C.CASES, default=C.CASES)
    yr = c2.slider("Years", 2014, 2026, (2014, 2026))
    logy = c3.toggle("Log scale", value=True)
    d = cm[(cm.month.dt.year >= yr[0]) & (cm.month.dt.year <= yr[1])]
    show(viz.fig_monthly_deaths(d, log=logy, cases=cases or C.CASES, title="Deaths per month"), "ex1")
    ov = D["case_overview"].set_index("conflict_case")
    cols = st.columns(len(cases or C.CASES))
    for c, case in zip(cols, cases or C.CASES):
        o = ov.loc[case]
        with c:
            card(case, f"{o.deaths_best:,.0f}", f"recorded deaths 2014–Sep 2026 (range {o.deaths_low:,.0f}–{o.deaths_high:,.0f})",
                 C.CASE_COLORS[case], f"Peak {o.peak_month}: {o.peak_month_deaths:,} · civilians {o.civilian_share:.0%} · "
                 f"{o.areas_affected} areas")
    st.markdown("")
    t1, t5, t6, t2, t3, t4 = st.tabs(["Map", "▶ Animated: where the dying happens", "Event browser", "Violence type",
                                      "Seasonality", "Top areas & dyads"])
    with t5:
        anim_case = st.selectbox("Conflict", C.CASES, key="anim_case")
        x = E[(E.conflict_case == anim_case) & ~E.admin1.str.startswith("(")]
        g = x.groupby([x.month.dt.year.rename("year"), "admin1"]).deaths_best.sum().reset_index()
        top = g.groupby("admin1").deaths_best.sum().nlargest(12).index
        g = g[g.admin1.isin(top)]
        full = pd.MultiIndex.from_product([sorted(g.year.unique()), top], names=["year", "admin1"])
        g = g.set_index(["year", "admin1"]).reindex(full, fill_value=0).reset_index()
        g["area"] = g.admin1.str.replace(" province", "").str.replace(" oblast", "")
        import plotly.express as px
        fig = px.bar(g, x="deaths_best", y="area", animation_frame="year", orientation="h",
                     range_x=[0, g.deaths_best.max() * 1.1], color_discrete_sequence=[C.CASE_COLORS[anim_case]],
                     labels={"deaths_best": "located deaths in the year", "area": ""})
        fig.update_layout(height=620,
                          title=f"{anim_case}: located deaths by area, year by year (press ▶)",
                          paper_bgcolor=T["bg"], plot_bgcolor=T["bg"], font=dict(color=T["text2"], size=16),
                          yaxis=dict(categoryorder="total ascending"))
        show(fig, "ex_anim")
        st.caption("Located events only (country-level aggregates excluded). Press ▶ or drag the year slider.")
    with t6:
        f1, f2, f3, f4 = st.columns([1.4, 1.4, 1.2, 1])
        bc = f1.multiselect("Conflicts", C.CASES, default=["Afghanistan–Pakistan"], key="eb_c")
        vt = f2.multiselect("Violence type", sorted(E.violence_type.dropna().unique()), key="eb_v")
        md = f3.number_input("Minimum deaths per event", 0, 5000, 10, step=5, key="eb_m")
        q = f4.text_input("Search place / actor", key="eb_q")
        dr = st.slider("Date range", min_value=E.month.min().date(), max_value=E.month.max().date(),
                       value=(pd.Timestamp("2025-01-01").date(), E.month.max().date()), key="eb_d")
        x = E[E.conflict_case.isin(bc or C.CASES) & (E.deaths_best >= md)
              & (E.month >= pd.Timestamp(dr[0])) & (E.month <= pd.Timestamp(dr[1]))]
        if vt:
            x = x[x.violence_type.isin(vt)]
        if q:
            mask = (x.ucdp_location_name.str.contains(q, case=False, na=False) | x.admin1.str.contains(q, case=False, na=False)
                    | x.side_a_name.str.contains(q, case=False, na=False) | x.side_b_name.str.contains(q, case=False, na=False))
            x = x[mask]
        x = x.sort_values("date_start", ascending=False)
        k1, k2, k3 = st.columns(3)
        k1.metric("Events", f"{len(x):,}")
        k2.metric("Deaths (best)", f"{x.deaths_best.sum():,.0f}")
        k3.metric("Civilian share", f"{x.deaths_civilians.sum() / max(x.deaths_best.sum(), 1):.0%}")
        cols = ["date_start", "conflict_case", "country_iso3", "admin1", "ucdp_location_name", "violence_type",
                "side_a_name", "side_b_name", "deaths_best", "deaths_civilians", "is_provisional"]
        st.dataframe(x[cols].head(500), hide_index=True, use_container_width=True, height=460)
        download(x[cols], "event_browser_selection", "Download this selection")
    with t1:
        yf = st.select_slider("Map period from", options=list(range(2014, 2027)), value=2024)
        cs = st.selectbox("Conflict", ["All"] + C.CASES)
        show(viz.fig_country_map(D["country_deaths"], case=None if cs == "All" else cs, year_from=yf, height=720), "ex_map")
    with t2:
        show(viz.fig_violence_mix(D["violence_mix"]), "ex2")
    with t3:
        show(viz.fig_seasonality(D["seasonality"]), "ex3")
        sowhat("Russia–Ukraine runs about 15–35% above trend in May–August and well below in Dec–Jan. Af–Pak peaks in "
               "Sep–Oct. Seasonal priors go into the forecast.")
    with t4:
        case = st.selectbox("Conflict ", C.CASES, key="topa")
        x = E[(E.conflict_case == case) & (E.month.dt.year >= yr[0]) & (E.month.dt.year <= yr[1])]
        a = (x.groupby(["country_iso3", "admin1"]).agg(deaths=("deaths_best", "sum"), events=("event_id", "count"),
                                                        civilians=("deaths_civilians", "sum"))
             .sort_values("deaths", ascending=False).head(15).reset_index())
        st.dataframe(a, hide_index=True, column_config={"deaths": st.column_config.ProgressColumn(
            "deaths", format="%d", min_value=0, max_value=float(a.deaths.max() or 1))})
        dy = D["dyads"]
        st.dataframe(dy[dy.conflict_case == case], hide_index=True)
    footer()


# ---------------------------------------------------------------------------
# 3. Military lens
# ---------------------------------------------------------------------------
def page_military():
    kicker("How the wars are being fought")
    st.markdown("# Military lens")
    t1, t2, t3, t4, t5 = st.tabs(["Front geography", "Attrition by side", "Af–Pak: second front", "Horizontal escalation",
                                  "Fog of war"])
    with t1:
        show(viz.fig_front_geography(D["front_geography"]), "m1")
        sowhat("A wide, static front favours long-range strike, counter-drone and logistics depth over manoeuvre. "
               "Warning should track the number of active sectors, which our models use as a feature.")
    with t2:
        show(viz.fig_attrition(D["attrition"]), "m2")
        st.info("These are UCDP-recorded figures. Ukrainian memorial and OSINT databases document Russian losses more "
                "completely than the reverse, so treat the ratio as a reporting upper bound, not a verified exchange ratio.")
        sowhat("With ISR-cued precision fires and drones, the defender imposes disproportionate recorded attrition. "
               "This is relevant to India's force structure on both fronts. (Domain inference)")
    with t3:
        show(viz.fig_afpak_interstate(E), "m3")
        show(viz.fig_afpak(D["afpak_provinces"]), "m4")
        sowhat("Pakistan now fights the TTP in KP and the Afghan state on the Durand Line. Watch for diversionary "
               "activity on the LoC and for TTP spill-over. Treat the Af–Pak interstate dyad as a standing I&W indicator.")
    with t4:
        show(viz.fig_theatre_spread(D["theatre_spread"]), "m5")
        ts = D["theatre_spread"]
        st.dataframe(ts[ts.year >= 2022].round(3), hide_index=True)
        sowhat("US–Iran went from 4 countries in 2025 to 14 in 2026, including the Gulf states and Sri Lankan waters. "
               "Horizontal spread is the earliest sign that India's interests (diaspora, shipping) are in the envelope.")
    with t5:
        show(viz.fig_fog_of_war(D["geo_precision"]), "m6")
        sowhat("By 2026, over 90% of RU–UA deaths have no sub-national location. Any sub-national claim about "
               "Ukraine must say so. Located events are a better guide to where the fighting is.")
    footer()


# ---------------------------------------------------------------------------
# 4. India
# ---------------------------------------------------------------------------
def page_india():
    kicker("So what for India")
    st.markdown("# India impact")
    c1, c2, c3, c4 = st.columns(4)
    ie = D["india_exposure"]
    g26 = ie[(ie.year == 2026)]
    with c1:
        card("Gulf states hit (2026)", "5", f"{int(g26[g26.india_tag.str.startswith('Gulf')].events.sum())} events, "
             f"{int(g26[g26.india_tag.str.startswith('Gulf')].deaths.sum())} deaths", T["amber"], "UAE, Kuwait, Saudi Arabia, "
             "Bahrain, Oman (Qatar hit in 2025)")
    with c2:
        card("Indian Ocean", "104", "killed in one strike off Sri Lanka, 4 Mar 2026", T["red"])
    with c3:
        h = g26[g26.india_tag.str.startswith("Iran")]
        card("Hormuz / Chabahar coast", f"{int(h.deaths.sum())}", f"deaths in {int(h.events.sum())} events, 2026",
             T["cyan"], "Hormozgan, Bushehr, Sistan-Baluchestan")
    with c4:
        ip = D["indian_press"].set_index("conflict_case")
        card("Indian OSINT coverage", f"{ip.loc['Afghanistan–Pakistan', 'events_covered_share']:.0%}",
             "of Af–Pak events cite an Indian outlet; about 0% for the other three theatres", T["violet"])
    st.markdown("")
    show(viz.fig_country_map(D["country_deaths"], year_from=2025, height=720), "i_map")
    l, r = st.columns(2)
    with l:
        show(viz.fig_india_exposure(D["india_exposure"]), "i1")
    with r:
        show(viz.fig_india_hosted(D["india_hosted"]), "i2")
    kicker("Impact matrix")
    st.markdown(f"""
| Theatre | What the data show {DATA_TAG} | What it means for India {DOM_TAG} | Recommended action |
|---|---|---|---|
| **Af–Pak** | KP deaths up every year since 2021; Afghan–Pakistan state clashes since Oct 2025 (peak 411 in Mar 2026); deaths in Pakistan areas adjoining India rose from 2 to 52 (2022–25) | Pakistan Army committed to its west, so risk of diversionary LoC activity and infiltration; TTP and IS-K spill-over | Treat the AF–PK interstate dyad and KP escalation probability as LoC I&W indicators |
| **US–Iran / Gulf** | War hit 14 countries in 2026, including 5 Gulf states; 299 deaths on Iran's Hormuz/Chabahar coast | About 9M Indians in the Gulf; large share of crude and LPG via Hormuz; Chabahar/INSTC exposed | Keep NEO plans for the Gulf current; escort and route-diversification plans |
| **Indian Ocean** | 104 killed off Sri Lanka on 4 Mar 2026 | The war reached India's maritime neighbourhood | Strengthen IFC-IOR maritime picture; monitor belligerent naval movement |
| **Russia–Ukraine** | Sustained 4–11k deaths/month (median 7.8k); front widening | Legacy Russian platforms: spares and deliveries at risk; drone and EW lessons | Indigenise spares; accelerate counter-drone |
| **Israel–Hamas** | De-escalated to about 130/month in 2026 | Key supplier of UAVs, missiles and sensors; Red Sea route | Buffer stocks of critical imports |
| **Refugees in India** | Afghans 16.2k (2021) to 8.4k (2025); Russian asylum seekers 5 to 329 | Small numbers, but rising Russian flows signal draft-evasion migration | Monitor; no surge capacity needed now |
""", unsafe_allow_html=True)
    with st.expander("India macro context (World Bank) vs conflict years"):
        ic = D["india_context"]
        x = ic.pivot(index="year", columns="economy_name", values="consumer_inflation_annual_pct")
        fig = go.Figure()
        for c in x.columns:
            fig.add_trace(go.Scatter(x=x.index, y=x[c], name=c, mode="lines+markers",
                                     line=dict(width=4 if c == "India" else 2)))
        fig.update_layout(title="Consumer inflation, % (India bold)", height=420)
        show(fig, "i3")
        st.caption("Correlation is not attribution: 2022 Indian inflation (6.7%) coincides with the invasion and the "
                   "energy shock, but many factors drive inflation.")
    footer()


# ---------------------------------------------------------------------------
# 5. Displacement
# ---------------------------------------------------------------------------
def page_displacement():
    kicker("Humanitarian planning")
    st.markdown("# Displacement")
    show(viz.fig_displacement(D["displacement"]), "d1")
    l, r = st.columns(2)
    with l:
        show(viz.fig_demographics(D["demographics_profile"]), "d2")
    with r:
        iso = st.selectbox("Origin", ["UKR", "AFG", "PSE", "IRN", "RUS", "PAK"],
                           format_func=lambda s: viz.NAMES.get(s, s))
        h = D["hosts"][D["hosts"].origin_iso3 == iso]
        st.dataframe(h[["asylum_name", "refugees_unhcr", "asylum_seekers", "total_international"]], hide_index=True)
        u = D["unrwa"]
        st.caption("UNRWA registered Palestine refugees, kept separate from IDMC/UNHCR series (different definitions):")
        st.dataframe(u.pivot_table(index="reporting_name", columns="year", values="people"), height=230)
    sowhat("72% of Ukrainian and 63% of Afghan refugees with recorded sex and age are women or children (10% of Afghans are "
           "under five). Stock paediatric and maternal supplies. Displacement tracks war onset and spread more than monthly "
           "deaths (Spearman about 0.1), so trigger HADR planning on our escalation flags.")
    footer()


# ---------------------------------------------------------------------------
# 6. Media
# ---------------------------------------------------------------------------
def page_media():
    kicker("Original index")
    st.markdown("# Media attention vs deaths")
    s = D["stats"]
    c1, c2, c3 = st.columns(3)
    with c1:
        card("Elasticity to events", f"{s['media_elasticity_events']:.2f}", "References rise about 1:1 with incidents", T["cyan"])
    with c2:
        card("Elasticity to deaths", f"{s['media_elasticity_deaths']:.2f}", "…and hardly at all with lethality", T["red"])
    with c3:
        card("Leads escalation?", "No", f"Attention gap → next-month change: p = {s['media_lead_p']:.2f}", T["amber"])
    st.markdown("")
    show(viz.fig_media_scatter(D["media"]), "md1")
    show(viz.fig_media_gap(D["media"]), "md2")
    case = st.selectbox("Outlets cited for", C.CASES)
    om = D["outlet_mix"][D["outlet_mix"].conflict_case == case]
    st.dataframe(om[["publisher_norm", "refs", "share"]], hide_index=True,
                 column_config={"share": st.column_config.ProgressColumn("share", format="%.2f", min_value=0, max_value=1)})
    sowhat("The Attention Gap Index is a regression residual: references explained by events and deaths. One "
           "mass-casualty strike is one story, so high-lethality violence is under-documented per death. Do not use media "
           "volume as a warning signal.")
    footer()


# ---------------------------------------------------------------------------
# 7. Forecast
# ---------------------------------------------------------------------------
def page_forecast():
    kicker("Model performance on withheld data")
    st.markdown("# Forecast: Jan–Sep 2026 withheld test")
    c1, c2, c3 = st.columns([2, 2, 2])
    case = c1.selectbox("Conflict", C.CASES)
    track = c2.radio("Question", ["A: next month (rolling)", "B: 1–9 months from Dec 2025"], horizontal=False)
    tr = "A" if track.startswith("A") else "B"
    model = c3.selectbox("Model", list(M.MODEL_LABELS), index=list(M.MODEL_LABELS).index("ensemble"),
                         format_func=lambda m: M.MODEL_LABELS[m])
    show(viz.fig_forecast_case(cm, D["preds"], case, track=tr, model=model,
                               future=D["future"] if (tr == "A" and model == "ensemble") else None), "f1")
    sc = D["scores"]
    h = sc[(sc.fold == 2026) & (sc.track == tr) & (sc.conflict_case == case)].set_index("model")
    h.index = h.index.map(M.MODEL_LABELS)
    st.dataframe(h[["MAE", "RMSE", "MAPE", "sMAPE", "MASE", "RMSLE", "Bias"]].sort_values("RMSLE").round(2))
    t1, t2, t3, t4 = st.tabs(["All models", "Why these models (ablation)", "Interval reliability", "Explainability"])
    with t1:
        show(viz.fig_model_compare(D["rmsle"]), "f2")
        hold = sc[(sc.fold == 2026) & (sc.track == "A")]
        base = hold[hold.model == "naive"].set_index("conflict_case").MAE
        ens = hold[hold.model == "ensemble"].set_index("conflict_case").MAE
        st.dataframe(((1 - ens / base) * 100).round(1).rename("% MAE reduction vs naive (2026, 1 month ahead)").to_frame())
    with t2:
        st.dataframe(D["abl"].set_index("variant"))
        st.markdown("Trees cannot extrapolate. A level model trained before 2022 can never predict the invasion's "
                    "death toll. Predicting the **change** in log deaths, with a compact feature set and an L1 loss, "
                    "generalises best. Ensemble members were chosen on the 2022–25 back-test only:")
        st.dataframe(D["ens"].head(8), hide_index=True)
    with t3:
        p = D["preds"]
        e = p[p.model == "ensemble"]
        cov = e.groupby(["fold", "track"]).apply(lambda g: pd.Series({
            "80% interval coverage": ((g.actual >= g.pi80_lo) & (g.actual <= g.pi80_hi)).mean(),
            "95% interval coverage": ((g.actual >= g.pi95_lo) & (g.actual <= g.pi95_hi)).mean()})).round(2)
        st.dataframe(cov)
        st.caption("Split-conformal intervals on log residuals from 2022–25. The 95% upper tail is wide by design "
                   "because the back-test contains the 2022 invasion: outbreak risk is real.")
    with t4:
        show(viz.fig_shap(D["shap_case"]), "f3")
    kicker("Forward forecast")
    f = D["future"]
    ff = f[f.model == "ensemble"][["conflict_case", "target_month", "pred", "pi80_lo", "pi80_hi"]].copy()
    ff["target_month"] = ff.target_month.dt.strftime("%b %Y")
    st.dataframe(ff.round(0), hide_index=True)
    download(ff.round(0), "forward_forecast_oct_dec_2026")
    footer()


# ---------------------------------------------------------------------------
# 8. Early warning
# ---------------------------------------------------------------------------
def page_ew():
    kicker("Indications & warning")
    st.markdown("# Sub-national escalation warning")
    rep = D["ew_rep"]
    r26 = rep[rep.year == 2026].set_index("model")
    c1, c2, c3, c4 = st.columns(4)
    lg = r26.loc["LightGBM classifier"]
    with c1:
        card("ROC-AUC 2026", f"{lg.ROC_AUC:.2f}", f"vs {r26.loc['Rule: rank by last month' + chr(39) + 's deaths', 'ROC_AUC']:.2f} for "
             "'watch last month's deadliest'", T["amber"])
    with c2:
        card("Top-10 precision", f"{lg.precision_at_10:.0%}", f"base rate {lg.base_rate:.1%}: "
             f"{lg.precision_at_10 / lg.base_rate:.1f}× lift", T["cyan"])
    with c3:
        card("Escalations caught", f"{lg.recall_at_20:.0%}", "of each month's escalations are in the top-20 list", T["teal"])
    with c4:
        am_ = D["am"]
        card("Series monitored", f"{am_.groupby(['conflict_case', 'admin1_key']).ngroups}",
             f"sub-national area series in {am_.country_iso3.nunique()} countries, scored every month", T["violet"])
    st.markdown("")
    t1, t2, t4, t3 = st.tabs([f"Watch-list for {(LAST + pd.DateOffset(months=1)):%b %Y}", "Replay a 2026 month",
                              "Alert threshold", "Model quality"])
    with t4:
        ep = D["ew_preds"]
        x = ep[ep.fold == 2026]
        thr = st.slider("Raise an alert when P(escalation) is at least", 0.02, 0.60, 0.15, step=0.01, key="ew_thr")
        flag = x.p_lgb >= thr
        tp = int((flag & (x.escalation == 1)).sum()); fp = int((flag & (x.escalation == 0)).sum())
        fn = int((~flag & (x.escalation == 1)).sum()); tn = int((~flag & (x.escalation == 0)).sum())
        a1, a2, a3, a4 = st.columns(4)
        with a1:
            card("Alerts per month", f"{flag.sum() / x.target_month.nunique():.1f}", "areas flagged, 2026 average", T["amber"])
        with a2:
            card("Precision", f"{tp / max(tp + fp, 1):.0%}", f"of alerts escalated (base rate {x.escalation.mean():.1%})",
                 T["cyan"])
        with a3:
            card("Recall", f"{tp / max(tp + fn, 1):.0%}", f"of {tp + fn} escalations were alerted", T["teal"])
        with a4:
            card("False alarms", f"{fp}", f"over {x.target_month.nunique()} months", T["red"])
        th = np.linspace(0.02, 0.6, 59)
        prec = [((x.p_lgb >= t) & (x.escalation == 1)).sum() / max((x.p_lgb >= t).sum(), 1) for t in th]
        rec = [((x.p_lgb >= t) & (x.escalation == 1)).sum() / max(x.escalation.sum(), 1) for t in th]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=th, y=prec, name="Precision", line=dict(color=T["cyan"], width=4)))
        fig.add_trace(go.Scatter(x=th, y=rec, name="Recall", line=dict(color=T["teal"], width=4)))
        fig.add_vline(x=thr, line=dict(color=T["amber"], width=3, dash="dash"))
        fig.update_layout(title="Trade-off on the 2026 withheld months: move the slider", height=420,
                          paper_bgcolor=T["bg"], plot_bgcolor=T["bg"], font=dict(color=T["text2"], size=16),
                          xaxis_title="alert threshold", yaxis=dict(tickformat=".0%"))
        show(fig, "ew_thr_fig")
        st.markdown(f"**Confusion matrix (2026):** alerted & escalated **{tp}** · alerted, no escalation **{fp}** · "
                    f"missed **{fn}** · correctly quiet **{tn:,}**")
        sowhat("A lower threshold catches more escalations at the cost of more false alarms. Pick it by the ISR "
               "capacity available: about 10 alerts a month matches the top-10 list in the report.", "TRADE-OFF")
    with t1:
        cs = st.multiselect("Filter conflicts", C.CASES, default=C.CASES, key="ewc")
        lv = D["ew_live"]
        lv = lv[lv.conflict_case.isin(cs) & ~lv.admin1.str.startswith("(")].head(20).round({"deaths": 0, "base3": 0})
        st.dataframe(lv[["conflict_case", "country_iso3", "admin1", "deaths", "base3", "p_escalation"]].rename(
            columns={"conflict_case": "Conflict", "country_iso3": "Country", "admin1": "Area", "deaths": f"Deaths {LAST:%b}", "base3": "3-mo mean"}), hide_index=True, height=600, use_container_width=True,
            column_config={"p_escalation": st.column_config.ProgressColumn("P(escalation next month)", format="%.2f",
                                                                          min_value=0, max_value=0.4)})
        download(lv[["conflict_case", "country_iso3", "admin1", "deaths", "base3", "p_escalation"]], "watch_list")
    with t2:
        ep = D["ew_preds"]
        months = sorted(ep[ep.fold == 2026].target_month.unique())
        m = st.select_slider("Month being predicted", options=months, value=months[2],
                             format_func=lambda x: pd.Timestamp(x).strftime("%b %Y"))
        x = ep[(ep.fold == 2026) & (ep.target_month == m)].sort_values("p_lgb", ascending=False)
        top = x.head(10)
        hits = int(top.escalation.sum())
        st.markdown(f"### Top-10 list issued at end of {pd.Timestamp(m) - pd.DateOffset(months=1):%b %Y}: "
                    f"**{hits}** of 10 escalated (out of {int(x.escalation.sum())} escalations that month)")
        top = top.assign(outcome=np.where(top.escalation == 1, "✅ escalated", "—"))
        st.dataframe(top[["conflict_case", "admin1", "deaths", "target_deaths", "p_lgb", "outcome"]].round(
            {"deaths": 0, "target_deaths": 0, "p_lgb": 2}).rename(
            columns={"deaths": "deaths (month t)", "target_deaths": "deaths (t+1)", "p_lgb": "P(escalation)"}),
            hide_index=True)
        missed = x[(x.escalation == 1)].iloc[10:] if len(x) > 10 else x.iloc[0:0]
        missed = x[(x.escalation == 1) & ~x.index.isin(top.index)]
        if len(missed):
            st.caption("Missed escalations: " + ", ".join(f"{a} ({c})" for a, c in zip(missed.admin1, missed.conflict_case)))
    with t3:
        show(viz.fig_ew_curves(D["ew_preds"]), "e1")
        st.dataframe(rep.round(3), hide_index=True)
        show(viz.fig_shap(D["shap_ew"], title="What drives the warning (mean |SHAP|)"), "e2")
    sowhat("Use the list to task ISR and analysts. Escalation is contagious within a theatre: the whole conflict's tempo "
           "and spread are among the strongest signals. It cannot foresee a political decision to start a war.")
    footer()


# ---------------------------------------------------------------------------
# 9. What-if + live retrain
# ---------------------------------------------------------------------------
def page_whatif():
    kicker("Interactive")
    st.markdown("# What-if simulator")
    art = load_models()
    l, r = st.columns([1, 2.4])
    with l:
        case = st.selectbox("Conflict", C.CASES, index=2)
        shock = st.slider("Change in violence over the last months (%)", -80, 200, 30, step=10)
        k = st.slider("…applied to the last N months", 1, 6, 3)
        st.caption("The frozen full-data LightGBM-Δ, a refitted ETS and the moving average are re-run on the modified "
                   "history. This is the same ensemble that was scored on 2026.")
    base = M.scenario_forecast(cm, case, 0, k, art["m_case_full"], art["members"], art["conformal"])
    scen = M.scenario_forecast(cm, case, shock, k, art["m_case_full"], art["members"], art["conformal"])
    with r:
        fig = viz.fig_forecast_case(cm, D["preds"], case, track="A", future=D["future"], scenario=scen,
                                    history_from="2025-01-01")
        fig.update_layout(title=f"{case}: baseline forward forecast (amber) vs scenario {shock:+d}% (red)")
        show(fig, "w1")
    c = st.columns(3)
    for i in range(3):
        with c[i]:
            b, s = base.iloc[i], scen.iloc[i]
            card(f"{s.target_month:%b %Y}", f"{s.pred:,.0f}", f"baseline {b.pred:,.0f} ({s.pred / max(b.pred, 1) - 1:+.0%}); "
                 f"80% range {s.pi80_lo:,.0f}–{s.pi80_hi:,.0f}", T["red"] if s.pred > b.pred else T["teal"])
    tidy = pd.DataFrame({"Month": pd.to_datetime(scen.target_month).dt.strftime("%b %Y"),
                         "Baseline forecast": base.pred.round(0).values, "Scenario forecast": scen.pred.round(0).values,
                         "80% low": scen.pi80_lo.round(0).values, "80% high": scen.pi80_hi.round(0).values,
                         "95% high": scen.pi95_hi.round(0).values})
    st.dataframe(tidy, hide_index=True, use_container_width=True)
    sowhat("The model damps shocks: a 30% three-month surge raises the next-month forecast by less than 30%. "
           "That is because both the ensemble and history say that most surges partly revert. Sustained surges "
           "(6 months) carry through.")
    st.markdown("---")
    kicker("Live re-train")
    st.markdown("### Re-train LightGBM-Δ from scratch on any cut-off and test on the following year")
    yr = st.select_slider("Train on data up to December of", options=[2021, 2022, 2023, 2024, 2025], value=2025)
    if st.button("Train now", type="primary"):
        from src.features import make_supervised
        with st.spinner("Training on the 4-conflict panel…"):
            sup = M._prep_case(make_supervised(cm, ["conflict_case"], horizons=range(1, 10)))
            cut = pd.Timestamp(f"{yr}-12-01")
            trn = sup[(sup.target_month <= cut) & sup.target_y.notna() & (sup.month >= "2014-12-01")]
            feats = M.CASE_FEATURES + ["case_cat"]
            mdl = M.fit_lgb(trn, feats, "delta", **M.LGB_CASE_PARAMS)
            te = sup[(sup.h == 1) & (sup.month >= cut) & (sup.target_month <= min(cut + pd.DateOffset(months=9), LAST))]
            te = te.assign(pred=np.expm1(mdl.predict(te[feats])))
        out = []
        for cs in C.CASES:
            g = te[te.conflict_case == cs]
            mm = M.metrics(g.target_deaths, g.pred)
            nv = M.metrics(g.target_deaths, g.deaths)
            out.append(dict(conflict=cs, MAE_model=mm["MAE"], MAE_naive=nv["MAE"], RMSLE_model=mm["RMSLE"],
                            RMSLE_naive=nv["RMSLE"]))
        st.success(f"Trained on {len(trn):,} rows (data to Dec {yr}); scored 1-month-ahead on the next 9 months.")
        st.dataframe(pd.DataFrame(out).round(2), hide_index=True)
        fig = go.Figure()
        for cs in C.CASES:
            g = te[te.conflict_case == cs]
            fig.add_trace(go.Scatter(x=g.target_month, y=g.target_deaths, name=f"{cs} actual",
                                     line=dict(color=C.CASE_COLORS[cs], width=3)))
            fig.add_trace(go.Scatter(x=g.target_month, y=g.pred, name=f"{cs} model", line=dict(color=C.CASE_COLORS[cs],
                                     width=3, dash="dash")))
        fig.update_yaxes(type="log")
        fig.update_layout(title="Actual (solid) vs freshly trained model (dashed)", height=460)
        show(fig, "w2")
    footer()


# ---------------------------------------------------------------------------
# 10. DQ & method
# ---------------------------------------------------------------------------
def page_dq():
    kicker("Reproducible, auditable")
    st.markdown("# Data quality & method")
    dq = D["dq"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        card("Checks", f"{len(dq)}", "documented checks across 6 tables", T["cyan"])
    with c2:
        card("Issues handled", f"{int((dq.rows_affected > 0).sum())}", "fixed, imputed or flagged, never silently dropped",
             T["amber"])
    with c3:
        card("Estimate repairs", "692", "out-of-order low/best/high rows", T["red"])
    with c4:
        card("Provisional rows", "4,644", "2026 Candidate records, used for testing only", T["violet"])
    st.markdown("")
    show(viz.fig_dq_summary(dq), "q1")
    st.dataframe(dq, hide_index=True, height=420)
    download(dq, "data_quality_log")
    kicker("Pipeline")
    st.markdown("""
`python run_pipeline.py` reproduces everything in about 2.5 minutes:

**1 Clean** (36 checks, data-quality log) → **2 Features** (conflict-month and 222 sub-national series; 40+ features,
no look-ahead) → **3 Insights** (military, India, displacement, media) → **4 Models** (7 forecasters, 4-fold walk-forward
back-test, 2026 holdout, conformal intervals, escalation classifier, TreeSHAP) → **5 Scorecard** → **6 Figures**.
Notebooks `01`–`05` re-run each stage with commentary.
""")
    kicker("Assumptions and limitations")
    st.markdown("""
* UCDP records **reported** lethal organised violence. Access, coding and source mix vary by place and time.
* 2026 events are **provisional** (Candidate) and are usually revised upward. Holdout error includes revision noise.
* Over 90% of 2026 RU–UA deaths have no sub-national location, so sub-national results for Ukraine use events.
* The US–Iran focal dyad codes Israel + US as **one actor**, so there is no country split.
* Displacement stocks **cannot be attributed** to single events. IDMC and UNRWA series are kept separate.
* World Bank context ends in 2025 and is used with a one-year lag.
* Forecasts cannot anticipate political decisions to start wars. Outbreak risk sits in the wide 95% tail.
* Points marked DOMAIN are expert reasoning, not outputs of this dataset.
""")
    footer()


# ---------------------------------------------------------------------------
# Area drill-down
# ---------------------------------------------------------------------------
def page_area():
    kicker("Zoom in")
    st.markdown("# Area drill-down")
    am_ = D["am"]
    c1, c2, c3 = st.columns([1.2, 1.6, 1])
    case = c1.selectbox("Conflict", C.CASES, index=2, key="ar_case")
    a = am_[am_.conflict_case == case]
    tot = a.groupby(["admin1_key", "admin1"]).deaths.sum().sort_values(ascending=False).reset_index()
    tot = tot[~tot.admin1.str.startswith("(")]
    key = c2.selectbox("Area (sorted by total deaths)", tot.admin1_key, format_func=lambda k: k.split(" | ", 1)[1]
                       + f"  ({k.split(' | ')[0]})", key="ar_key")
    start = c3.select_slider("From", options=list(range(2014, 2027)), value=2020, key="ar_from")
    s_ = a[(a.admin1_key == key) & (a.month >= f"{start}-01-01")].sort_values("month")
    name = key.split(" | ", 1)[1]
    lv = D["ew_live"].set_index("admin1_key")
    af = D["admin_future"]
    af = af[af.admin1_key == key].sort_values("h")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        card("Deaths since " + str(start), f"{s_.deaths.sum():,.0f}", f"{int(s_.n_events.sum()):,} events", C.CASE_COLORS[case])
    with k2:
        last = s_.iloc[-1] if len(s_) else None
        card(f"Deaths {LAST:%b %Y}", f"{(last.deaths if last is not None else 0):,.0f}",
             f"3-month mean {s_.deaths.tail(3).mean():,.0f}", T["cyan"])
    with k3:
        pe = lv.loc[key, "p_escalation"] if key in lv.index else np.nan
        rank = int((D["ew_live"].p_escalation > pe).sum() + 1) if pe == pe else None
        card(f"P(escalation) {(LAST + pd.DateOffset(months=1)):%b}", f"{pe:.0%}" if pe == pe else "n/a",
             f"rank {rank} of {len(lv)} areas" if rank else "", T["amber"] if pe == pe and pe >= 0.15 else T["teal"])
    with k4:
        nxt = af.pred.iloc[0] if len(af) else np.nan
        card("Bottom-up forecast", f"{nxt:,.0f}" if nxt == nxt else "n/a", "deaths next month (LightGBM Tweedie)", T["violet"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=s_.month, y=s_.n_events, name="events", marker_color=T["border"], yaxis="y2", opacity=0.8))
    fig.add_trace(go.Scatter(x=s_.month, y=s_.deaths, name="deaths", line=dict(color=C.CASE_COLORS[case], width=4)))
    if len(af):
        fig.add_trace(go.Scatter(x=af.target_month, y=af.pred, name="forecast", mode="lines+markers",
                                 line=dict(color=T["amber"], width=3, dash="dash")))
    fig.update_layout(title=f"{name}: deaths and events per month", height=460, paper_bgcolor=T["bg"],
                      plot_bgcolor=T["bg"], font=dict(color=T["text2"], size=16), hovermode="x unified",
                      yaxis=dict(title="deaths", gridcolor=T["panel2"]),
                      yaxis2=dict(title="events", overlaying="y", side="right", showgrid=False),
                      legend=dict(orientation="h", y=-0.15), margin=dict(t=70, b=70))
    show(fig, "ar1")
    ep = D["ew_preds"]
    h = ep[ep.admin1_key == key].sort_values("target_month")
    if len(h):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=h.target_month, y=h.p_lgb, name="P(escalation), issued a month earlier",
                                 line=dict(color=T["amber"], width=3), fill="tozeroy", fillcolor="rgba(240,176,58,0.15)"))
        esc = h[h.escalation == 1]
        fig.add_trace(go.Scatter(x=esc.target_month, y=esc.p_lgb, mode="markers", name="escalation happened",
                                 marker=dict(color=T["red"], size=14, symbol="x")))
        fig.update_layout(title="Out-of-sample warning history (each year predicted by a model trained only on earlier years)",
                          height=360, paper_bgcolor=T["bg"], plot_bgcolor=T["bg"], font=dict(color=T["text2"], size=15),
                          yaxis=dict(tickformat=".0%", gridcolor=T["panel2"]), legend=dict(orientation="h", y=-0.18),
                          margin=dict(t=70, b=70))
        show(fig, "ar2")
    ev = E[(E.admin1_key == key)].sort_values("date_start", ascending=False)
    kicker("Latest events in this area")
    cols = ["date_start", "ucdp_location_name", "violence_type", "side_a_name", "side_b_name", "deaths_best",
            "deaths_civilians"]
    st.dataframe(ev[cols].head(100).assign(date_start=lambda d: pd.to_datetime(d.date_start).dt.strftime("%d %b %Y"))
                 .rename(columns={"date_start": "Date", "ucdp_location_name": "Country", "violence_type": "Type",
                                  "side_a_name": "Side A", "side_b_name": "Side B", "deaths_best": "Deaths",
                                  "deaths_civilians": "Civilians"}),
                 hide_index=True, use_container_width=True, height=360)
    download(ev[cols], f"events_{name.replace(' ', '_')}", "Download all events in this area")
    footer()


# ---------------------------------------------------------------------------
# Scorecard lab
# ---------------------------------------------------------------------------
def page_lab():
    kicker("Interactive")
    st.markdown("# Scorecard lab: change the rules, watch the ratings move")
    rag = D["rag"].set_index("conflict_case")
    live = D["ew_live"]
    l, r = st.columns([1, 2.3])
    with l:
        hi = st.number_input("Intensity: 2 points at ≥ deaths/month", 100, 20000, 1000, step=100)
        mid = st.number_input("Intensity: 1 point at ≥ deaths/month", 1, 5000, 100, step=10)
        tr = st.slider("Trend: ± point when forecast vs last 6 months moves by (%)", 5, 100, 20, step=5)
        p_hot = st.slider("Hotspot: area escalation probability ≥", 0.05, 0.40, 0.15, step=0.01)
        use_vol = st.toggle("Volatility rule", value=True)
        use_spread = st.toggle("Spread rule", value=True)
        red_pts = st.slider("RED at ≥ points", 3, 8, 5)
        amb_pts = st.slider("AMBER at ≥ points", 1, 4, 2)
        st.caption("Volatility: a ≥1,000-death month in the last year. Spread: more countries hit than last year. "
                   "Auto-RED: forecast at or above the 2-point intensity level.")
        red_auto = st.toggle("Auto-RED at top intensity", value=True)
    rows = []
    for case in C.CASES:
        g = rag.loc[case]
        f = g.forecast_next
        lv = live[(live.conflict_case == case) & ~live.admin1.str.startswith("(")]
        hot = int((lv.p_escalation >= p_hot).sum())
        pts = dict(Intensity=2 if f >= hi else 1 if f >= mid else 0,
                   Trend=1 if g.trend_ratio >= 1 + tr / 100 else -1 if g.trend_ratio <= 1 - tr / 100 else 0,
                   Hotspots=2 if hot >= 3 else 1 if hot >= 1 else 0,
                   Spread=int(g.pts_spread) if use_spread else 0,
                   Volatility=int(g.pts_volatility) if use_vol else 0)
        sc = sum(pts.values())
        rating = "RED" if ((red_auto and f >= hi) or sc >= red_pts) else "AMBER" if sc >= amb_pts else "GREEN"
        rows.append(dict(conflict=case, rating=rating, points=sc, hotspots=hot, forecast=f, base=g.rating, **pts))
    res = pd.DataFrame(rows)
    with r:
        cols = st.columns(4)
        for c, (_, x) in zip(cols, res.iterrows()):
            col = C.RAG_COLORS[x.rating]
            changed = "" if x.rating == x.base else f"<div class='small'>was {x.base}</div>"
            with c:
                st.markdown(f'<div class="rag" style="border:3px solid {col}"><div class="case" style="font-size:1.05rem">{x.conflict}</div>'
                            f'<div class="rating" style="color:{col};font-size:1.9rem;letter-spacing:1px">{x.rating}</div>'
                            f'<div class="line">{int(x.points)} pts · {x.hotspots} hotspot(s)</div>{changed}</div>',
                            unsafe_allow_html=True)
        long = res.melt(id_vars="conflict", value_vars=["Intensity", "Trend", "Hotspots", "Spread", "Volatility"],
                        var_name="rule", value_name="pts")
        import plotly.express as px
        fig = px.bar(long, x="pts", y="conflict", color="rule", orientation="h",
                     color_discrete_sequence=[T["red"], T["cyan"], T["amber"], T["violet"], T["teal"]])
        fig.add_vline(x=red_pts, line=dict(color=T["red"], dash="dash", width=2))
        fig.add_vline(x=amb_pts, line=dict(color=T["amber"], dash="dash", width=2))
        fig.update_layout(title="Points by rule (dashed lines: AMBER and RED thresholds)", height=420, barmode="relative",
                          paper_bgcolor=T["bg"], plot_bgcolor=T["bg"], font=dict(color=T["text2"], size=16),
                          yaxis_title="", xaxis_title="", legend=dict(orientation="h", y=-0.25, title_text=""),
                          margin=dict(l=210, t=70, b=90))
        show(fig, "lab1")
    sowhat("Every input is a model output, so the rating is transparent and auditable. Show how robust the picture is: "
           "Russia–Ukraine stays RED under any sensible rule set; the AMBER/GREEN line is where judgement matters.",
           "WHY IT MATTERS")
    download(res, "scorecard_lab_result")
    footer()


{
    PAGES[0]: page_brief, PAGES[1]: page_explorer, PAGES[2]: page_area, PAGES[3]: page_military, PAGES[4]: page_india,
    PAGES[5]: page_displacement, PAGES[6]: page_media, PAGES[7]: page_forecast, PAGES[8]: page_ew,
    PAGES[9]: page_whatif, PAGES[10]: page_lab, PAGES[11]: page_dq,
}[page]()
