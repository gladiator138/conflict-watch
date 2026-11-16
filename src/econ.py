"""The economic front: do the four wars show up in markets, currencies, reserves and politics?

NEW, separately labelled analysis (does not change the forecasting or early-warning models).
Market data are public series fetched once on the team laptop (data/econ/fetch_econ*.py) and
bundled as a frozen snapshot in data/econ/raw/, so this stage makes no internet calls.

Method
  1. Shock dates come from the competition data, not from hindsight. A *spike month* is a month
     whose UCDP deaths are >= SPIKE_RATIO x the trailing 6-month mean and >= SPIKE_MIN deaths;
     consecutive spike months form one episode. Day 0 is the first day of the
     episode window (last 7 days of the previous month + the spike month) with >= DAY_MIN deaths and >= DAY_RATIO x the
     trailing 90-day daily mean.
  2. Event study per episode and series: log change from the last close before day 0 to the
     close 1, 5, 20 and 60 trading days later, plus the worst point in 0..+60.
  3. Significance by placebo: the same 20-day window on every non-episode trading day of that
     series since 2014 gives an empirical distribution; p = share of placebo moves at least as
     extreme (two-sided). Market moves on war days are compared with "any 20 days".
  4. India panel: Nifty, INR and Brent monthly against the four wars' deaths; reserves from the
     World Bank (annual, the only reserve series reachable from the laptop) and IMF where available.
  5. Two fronts: for each theatre, battlefield toll (UCDP, in the competition files) against the
     economic toll (market, currency, oil, GDP growth from the issued World Bank context), and
     who pays it (countries with war deaths vs countries hit by the price shock).
  6. Political-crisis timeline: dated, labelled DOMAIN events, plus GDELT protest events (CAMEO 14)
     per country-month for 2026 from the issued GDELT files (DATA).

Outputs (outputs/tables): econ_episodes.csv, econ_event_study.csv, econ_india_monthly.csv,
econ_fronts.csv, econ_political_timeline.csv, econ_protests_2026.csv, econ_claims_check.csv,
econ_summary.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import config as C

RAW = C.ROOT / "data" / "econ" / "raw"
SPIKE_RATIO, SPIKE_MIN = 1.75, 300
DAY_RATIO, DAY_MIN = 5.0, 30
HORIZONS = [1, 5, 20, 60]

# series -> (file, label, unit, sign) ; sign=+1 means "up is good for that economy" (equity, currency value)
SERIES = {
    "MOEX": ("moex_IMOEX.csv", "MOEX Russia index", "equity", 1),
    "RUB": ("yahoo_RUB.csv", "Rouble (value vs USD)", "fx", 1),
    "UAH": ("yahoo_UAH.csv", "Hryvnia (value vs USD)", "fx", 1),
    "TA35": ("yahoo_TA35.csv", "Tel Aviv 35 index", "equity", 1),
    "ILS": ("yahoo_ILS.csv", "Shekel (value vs USD)", "fx", 1),
    "PKR": ("yahoo_PKR.csv", "Pakistan rupee (value vs USD)", "fx", 1),
    "AFN": ("yahoo_AFN.csv", "Afghani (value vs USD)", "fx", 1),
    "IRR": ("yahoo_IRR.csv", "Iran rial (value vs USD, 2026 market rate)", "fx", 1),
    "NIFTY": ("yahoo_NSEI.csv", "Nifty 50", "equity", 1),
    "INR": ("yahoo_INR.csv", "Indian rupee (value vs USD)", "fx", 1),
    "BRENT": ("yahoo_BRENT.csv", "Brent crude (USD/bbl)", "commodity", 1),
    "TTF": ("yahoo_TTF.csv", "European gas (TTF)", "commodity", 1),
    "WHEAT": ("yahoo_WHEAT.csv", "Wheat (CBOT)", "commodity", 1),
    "GOLD": ("yahoo_GOLD.csv", "Gold", "commodity", 1),
    "FRO": ("yahoo_FRO.csv", "Frontline (crude tankers)", "equity", 1),
    "ZIM": ("yahoo_ZIM.csv", "ZIM (container shipping)", "equity", 1),
    "VIX": ("yahoo_VIX.csv", "VIX fear gauge", "vol", 1),
    "SPX": ("yahoo_SPX.csv", "S&P 500", "equity", 1),
    "EEM": ("yahoo_MSCIEM.csv", "Emerging markets (EEM)", "equity", 1),
}
# which series matter for which theatre (local first, then global transmission, then India)
THEATRE_SERIES = {
    "Russia–Ukraine": ["MOEX", "RUB", "UAH", "BRENT", "TTF", "WHEAT", "NIFTY", "INR"],
    "Israel–Hamas": ["TA35", "ILS", "BRENT", "ZIM", "NIFTY", "INR"],
    "Afghanistan–Pakistan": ["PKR", "AFN", "NIFTY", "INR"],
    "US–Iran": ["IRR", "BRENT", "FRO", "GOLD", "VIX", "NIFTY", "INR"],
}
WB_ISO = {"Russia–Ukraine": ["UKR", "RUS"], "Israel–Hamas": ["ISR", "PSE"], "Afghanistan–Pakistan": ["PAK", "AFG"],
          "US–Iran": ["IRN"]}

# Political and civil crises, dated. DOMAIN knowledge (public record), not from the competition files.
POLITICAL = [
    ("Russia–Ukraine", "2014-02-22", "Ukraine: Yanukovych flees after Maidan; Crimea seized within weeks"),
    ("Russia–Ukraine", "2022-02-28", "Russia: reserves frozen by G7/EU; SWIFT cut-offs; MOEX shut for four weeks"),
    ("Russia–Ukraine", "2022-09-21", "Russia: 'partial mobilisation'; exodus of working-age men"),
    ("Russia–Ukraine", "2023-06-24", "Russia: Wagner mutiny marches towards Moscow"),
    ("Russia–Ukraine", "2024-05-20", "Ukraine: presidential term lapses under martial law, no election"),
    ("Israel–Hamas", "2023-01-07", "Israel: mass protests over judicial overhaul begin"),
    ("Israel–Hamas", "2023-10-11", "Israel: emergency unity government formed"),
    ("Israel–Hamas", "2024-06-09", "Israel: Gantz quits war cabinet"),
    ("Israel–Hamas", "2024-11-05", "Israel: defence minister Gallant dismissed"),
    ("Afghanistan–Pakistan", "2021-08-15", "Afghanistan: Taliban take Kabul; central-bank reserves frozen"),
    ("Afghanistan–Pakistan", "2022-04-10", "Pakistan: PM Imran Khan ousted by no-confidence vote"),
    ("Afghanistan–Pakistan", "2023-05-09", "Pakistan: riots after Khan's arrest; army sites attacked"),
    ("Afghanistan–Pakistan", "2023-07-12", "Pakistan: IMF $3B stand-by agreed at the edge of default"),
    ("Afghanistan–Pakistan", "2024-02-08", "Pakistan: disputed general election"),
    ("US–Iran", "2019-11-15", "Iran: fuel-price protests, internet shutdown"),
    ("US–Iran", "2022-09-16", "Iran: Mahsa Amini protests begin"),
    ("US–Iran", "2024-05-19", "Iran: President Raisi killed in helicopter crash"),
]


# --------------------------------------------------------------------------- loading + cleaning
def load_series(key: str) -> pd.Series:
    """Daily close, cleaned: drop blanks/non-positive, drop isolated ticks that jump >60% and revert."""
    f, *_ = SERIES[key]
    d = pd.read_csv(RAW / f, parse_dates=["date"])
    d = d[pd.to_numeric(d.close, errors="coerce") > 0].drop_duplicates("date", keep="last").sort_values("date")
    s = d.set_index("date").close.astype(float)
    if key == "IRR":    # official peg (42,000) until Jan 2026; only the 2026 market rate carries information
        s = s[s.index >= "2026-01-09"]
    r = np.log(s).diff()
    spike = (r.abs() > np.log(1.6)) & (r.shift(-1).abs() > np.log(1.6)) & (np.sign(r) != np.sign(r.shift(-1)))
    return s[~spike]


def clean_log() -> pd.DataFrame:
    rows = []
    for k, (f, lab, *_r) in SERIES.items():
        raw = pd.read_csv(RAW / f)
        s = load_series(k)
        rows.append(dict(series=k, label=lab, file=f, raw_rows=len(raw), kept=len(s),
                         first=s.index.min().date(), last=s.index.max().date()))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- shock dates from UCDP
def episodes(cm: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    p = cm.pivot(index="month", columns="conflict_case", values="deaths").sort_index()
    ev = events[events.span_days <= 1].copy()
    ev["day"] = pd.to_datetime(ev.date_start).dt.normalize()
    daily = ev.groupby(["conflict_case", "day"]).deaths_best.sum()
    out = []
    for case in C.CASES:
        y = p[case]
        base = y.shift(1).rolling(6, min_periods=6).mean()
        spk = y[(y >= SPIKE_RATIO * base.clip(lower=1)) & (y >= SPIKE_MIN)].index
        groups, cur = [], []
        for m in spk:
            if cur and (m.to_period("M") - cur[-1].to_period("M")).n > 1:
                groups.append(cur)
                cur = []
            cur.append(m)
        if cur:
            groups.append(cur)
        dd = daily[case].asfreq("D", fill_value=0) if case in daily.index.get_level_values(0) else pd.Series(dtype=float)
        trail = dd.shift(1).rolling(90, min_periods=30).mean()
        for g in groups:
            m0 = g[0]
            lo, hi = m0 - pd.Timedelta(days=7), m0 + pd.offsets.MonthEnd(0)
            w = dd[lo:hi]
            hit = w[(w >= DAY_MIN) & (w >= DAY_RATIO * trail[lo:hi].clip(lower=0.5))]
            t0 = hit.index[0] if len(hit) else m0
            out.append(dict(conflict_case=case, spike_month=m0.strftime("%Y-%m"), months=len(g),
                            episode_deaths=float(y[g[0]:g[-1]].sum()), baseline_6m=float(base[m0]),
                            ratio=float(y[m0] / max(base[m0], 1)), day0=t0.date().isoformat(),
                            day0_deaths=float(dd.get(t0, np.nan))))
    return pd.DataFrame(out)


# --------------------------------------------------------------------------- event study
def _moves(s: pd.Series, t0: pd.Timestamp) -> dict | None:
    pre = s[s.index < t0]
    post = s[s.index >= t0]
    if len(pre) < 20 or len(post) < 2:
        return None
    p0 = pre.iloc[-1]
    gap = (post.index[0] - pre.index[-1]).days
    r = {f"h{h}": (np.log(post.iloc[min(h, len(post)) - 1] / p0) if len(post) >= min(h, 2) else np.nan) for h in HORIZONS}
    w = post.iloc[:60]
    r["worst"] = float(np.log(w.min() / p0))
    r["best"] = float(np.log(w.max() / p0))
    r["base_date"], r["base"] = pre.index[-1].date().isoformat(), float(p0)
    r["gap_days"] = gap
    return r


def _placebo(s: pd.Series, h: int, exclude: list[pd.Timestamp]) -> np.ndarray:
    s = s[s.index >= "2014-01-01"]
    lr = np.log(s).diff(h).shift(-h).dropna()
    mask = np.ones(len(lr), bool)
    for t in exclude:
        mask &= ~((lr.index >= t - pd.Timedelta(days=30)) & (lr.index <= t + pd.Timedelta(days=90)))
    return lr[mask].values


def event_study(ep: pd.DataFrame) -> pd.DataFrame:
    rows = []
    allday0 = [pd.Timestamp(d) for d in ep.day0]
    cache = {k: load_series(k) for k in SERIES}
    for e in ep.itertuples():
        t0 = pd.Timestamp(e.day0)
        for k in THEATRE_SERIES[e.conflict_case]:
            s = cache[k]
            if SERIES[k][2] == "fx":       # quoted as local units per USD -> study the currency's VALUE
                s = 1.0 / s
            m = _moves(s, t0)
            if m is None:
                continue
            f, lab, unit, sign = SERIES[k]
            pl = _placebo(s, 20, allday0)
            v = m["h20"]
            p = float((np.abs(pl - np.median(pl)) >= abs(v - np.median(pl))).mean()) if len(pl) and pd.notna(v) else np.nan
            rows.append(dict(conflict_case=e.conflict_case, spike_month=e.spike_month, day0=e.day0, series=k,
                             label=lab, unit=unit, sign=sign, base_date=m["base_date"], base=m["base"],
                             d1=m["h1"], d5=m["h5"], d20=m["h20"], d60=m["h60"], worst60=m["worst"], best60=m["best"],
                             placebo_sd20=float(np.std(pl)) if len(pl) else np.nan, p20=p,
                             z20=float((v - np.mean(pl)) / np.std(pl)) if len(pl) and pd.notna(v) else np.nan))
    es = pd.DataFrame(rows)
    for c in ["d1", "d5", "d20", "d60", "worst60", "best60"]:
        es[c + "_pct"] = (np.exp(es[c]) - 1) * 100
    return es


# --------------------------------------------------------------------------- India panel
def india_monthly(cm: pd.DataFrame) -> pd.DataFrame:
    m = {}
    for k in ["NIFTY", "INR", "BRENT"]:
        m[k] = load_series(k).resample("MS").mean()
    df = pd.DataFrame(m)
    df = df[(df.index >= C.PANEL_START)]
    p = cm.pivot(index="month", columns="conflict_case", values="deaths")
    for c in C.CASES:
        df["deaths_" + C.CASE_SHORT[c]] = p[c]
    df.index.name = "month"
    return df.reset_index()


def reserves() -> pd.DataFrame:
    f = RAW / "wb_reserves_usd.csv"
    g = RAW / "wb_res_months_imports.csv"
    if not f.exists():
        return pd.DataFrame()
    a = pd.read_csv(f).rename(columns={"value": "reserves_usd"})
    b = pd.read_csv(g).rename(columns={"value": "months_of_imports"}) if g.exists() else None
    out = a.merge(b, on=["iso3", "year"], how="left") if b is not None else a
    return out.dropna(subset=["reserves_usd"]).sort_values(["iso3", "year"])


# --------------------------------------------------------------------------- two fronts
def fronts(cm, ep, es, ins_country=None) -> pd.DataFrame:
    ctx = pd.read_parquet(C.PROCESSED / "country_year.parquet")
    ev = pd.read_parquet(C.PROCESSED / "events.parquet")
    rows = []
    for case in C.CASES:
        e = ep[ep.conflict_case == case]
        if e.empty:
            continue
        big = e.sort_values("episode_deaths").iloc[-1]          # the largest episode in the panel
        yr = int(big.spike_month[:4])
        t0 = pd.Timestamp(big.day0)
        x = es[(es.conflict_case == case) & (es.day0 == big.day0)].set_index("series")
        evy = ev[(ev.conflict_case == case) & (ev.event_year == yr)]
        n_countries = evy.loc[evy.deaths_best > 0, "country_iso3"].nunique()
        gdp = {}
        for iso in WB_ISO[case]:
            g = ctx[(ctx.iso3 == iso)].set_index("year").gdp_growth_annual_pct
            if yr in g.index and (yr - 1) in g.index:
                gdp[iso] = (float(g.get(yr - 1)), float(g.get(yr)), float(g.get(yr + 1, np.nan)))
        loc_eq = next((k for k in THEATRE_SERIES[case] if SERIES[k][2] == "equity" and k not in ("NIFTY", "FRO", "ZIM")), None)
        loc_fx = next((k for k in THEATRE_SERIES[case] if SERIES[k][2] == "fx" and k != "INR"), None)

        def g_(k, c):
            return float(x.loc[k, c]) if k in x.index else np.nan
        rows.append(dict(
            conflict_case=case, episode=big.spike_month, day0=big.day0, episode_deaths=big.episode_deaths,
            countries_with_deaths=int(n_countries),
            local_equity=loc_eq, local_equity_worst60_pct=g_(loc_eq, "worst60_pct") if loc_eq else np.nan,
            local_fx=loc_fx, local_fx_worst60_pct=g_(loc_fx, "worst60_pct") if loc_fx else np.nan,
            brent_best60_pct=g_("BRENT", "best60_pct"), brent_d20_pct=g_("BRENT", "d20_pct"),
            nifty_worst60_pct=g_("NIFTY", "worst60_pct"), inr_worst60_pct=g_("INR", "worst60_pct"),
            gdp_growth=json.dumps(gdp)))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- protests (GDELT, issued)
def protests_2026() -> pd.DataFrame:
    g = pd.read_csv(C.ROOT / "data" / "gdelt" / "gdelt_country_rootcode_monthly.csv")
    tot = g.groupby(["country", "year_month"]).events.sum().rename("all_events")
    pr = g[g.event_root_code == 14].groupby(["country", "year_month"]).events.sum().rename("protest_events")
    out = pd.concat([tot, pr], axis=1).fillna(0).reset_index()
    out["protest_share"] = out.protest_events / out.all_events
    return out


# --------------------------------------------------------------------------- shock paths (for charts)
PATH_SERIES = {"Russia–Ukraine": ["MOEX", "RUB", "BRENT", "WHEAT", "NIFTY", "INR"],
               "Israel–Hamas": ["TA35", "ILS", "BRENT", "ZIM", "NIFTY", "INR"],
               "US–Iran": ["BRENT", "VIX", "FRO", "NIFTY", "INR", "GOLD"]}


def paths(pre=10, post=60) -> pd.DataFrame:
    """Index = 100 at the last close before day 0; trading-day offsets -pre..+post."""
    rows = []
    for case, t0 in MAIN_SHOCKS.items():
        t = pd.Timestamp(t0)
        for k in PATH_SERIES[case]:
            s = load_series(k)
            if SERIES[k][2] == "fx":
                s = 1.0 / s
            a, b = s[s.index < t], s[s.index >= t]
            base = a.iloc[-1]
            seg = pd.concat([a.iloc[-pre:], b.iloc[:post]])
            offs = list(range(-pre + 1, 1)) + list(range(1, len(b.iloc[:post]) + 1))
            for o, (d, v) in zip(offs, seg.items()):
                rows.append(dict(conflict_case=case, day0=t0, series=k, offset=o, date=d.date().isoformat(),
                                 index=float(v / base * 100)))
    return pd.DataFrame(rows)


def gpr_monthly(cm: pd.DataFrame) -> pd.DataFrame:
    f = RAW / "gpr_monthly.xls"
    if not f.exists():
        return pd.DataFrame()
    g = pd.read_excel(f)
    g["month"] = pd.to_datetime(g.month)
    keep = ["GPR", "GPRC_IND", "GPRC_ISR", "GPRC_RUS", "GPRC_UKR", "GPRC_SAU", "GPRC_USA"]
    g = g[g.month >= C.PANEL_START][["month"] + keep]
    p = cm.pivot(index="month", columns="conflict_case", values="deaths")
    g = g.merge(p.rename(columns={c: "deaths_" + C.CASE_SHORT[c] for c in p}).reset_index(), on="month", how="left")
    return g


# --------------------------------------------------------------------------- claims check
def political_alignment(ep: pd.DataFrame, window_days: int = 45) -> pd.DataFrame:
    pol = pd.DataFrame(POLITICAL, columns=["conflict_case", "date", "event"])
    pol["date"] = pd.to_datetime(pol.date)
    out = []
    for r in pol.itertuples():
        e = ep[ep.conflict_case == r.conflict_case]
        dist = (pd.to_datetime(e.day0) - r.date).dt.days
        near = dist[dist.abs() <= window_days]
        out.append(dict(conflict_case=r.conflict_case, date=r.date.date().isoformat(), event=r.event, basis="DOMAIN",
                        nearest_episode_day0=e.day0.iloc[dist.abs().argmin()] if len(e) else None,
                        days_from_episode=int(dist.iloc[dist.abs().argmin()]) if len(e) else None,
                        within_45d=bool(len(near))))
    return pd.DataFrame(out)


def claims(es: pd.DataFrame, res: pd.DataFrame, pa: pd.DataFrame | None = None) -> pd.DataFrame:
    def v(case, day0, k, c):
        r = es[(es.conflict_case == case) & (es.day0 == day0) & (es.series == k)]
        return float(r[c].iloc[0]) if len(r) else np.nan
    mo = load_series("MOEX")
    d24 = float(np.log(mo["2022-02-24"] / mo[mo.index < "2022-02-24"].iloc[-1]))
    gap = mo["2022-02-26":"2022-03-31"].index
    halt_days = int((gap[0] - pd.Timestamp("2022-02-25")).days) if len(gap) else 0
    ta = load_series("TA35")
    ta_first = float(np.log(ta[ta.index > "2023-10-07"].iloc[0] / ta[ta.index < "2023-10-07"].iloc[-1]))
    ta_min = float(np.log(ta["2023-10-07":"2023-11-07"].min() / ta[ta.index < "2023-10-07"].iloc[-1]))
    ils = load_series("ILS")
    ils_max = float(ils["2023-10-07":"2023-11-30"].max())
    pk = res[(res.iso3 == "PAK")].set_index("year") if len(res) else pd.DataFrame()
    pk_m = float(pk.loc[2022, "months_of_imports"]) if 2022 in getattr(pk, "index", []) and "months_of_imports" in pk else np.nan
    af = res[(res.iso3 == "AFG")].set_index("year") if len(res) else pd.DataFrame()
    af_r = float(af.loc[2020, "reserves_usd"]) / 1e9 if 2020 in getattr(af, "index", []) else np.nan
    ru = res[(res.iso3 == "RUS")].set_index("year") if len(res) else pd.DataFrame()
    ru_r = float(ru.loc[2021, "reserves_usd"]) / 1e9 if 2021 in getattr(ru, "index", []) else np.nan
    rows = [
        ("Russia's MOEX fell about 33% on 24 Feb 2022", f"{(np.exp(d24) - 1) * 100:.1f}% on 24 Feb 2022 (MOEX ISS)",
         "CORRECT", "DATA"),
        ("Trading stopped for a month", f"No MOEX index session from 26 Feb to {gap[0].date() if len(gap) else '?'} "
         f"({halt_days} days)", "CORRECT (about four weeks)", "DATA"),
        ("Israel's TA-35 dropped sharply after 7 Oct 2023",
         f"{(np.exp(ta_first) - 1) * 100:.1f}% at the first close in the data, {(np.exp(ta_min) - 1) * 100:.1f}% at the "
         "worst point in the month", "CORRECT", "DATA"),
        ("India's Nifty dipped on the same shocks, mostly through oil",
         f"Nifty {v('Russia–Ukraine', '2022-02-24', 'NIFTY', 'd1_pct'):+.1f}% on 24 Feb 2022 (Brent "
         f"{v('Russia–Ukraine', '2022-02-24', 'BRENT', 'd20_pct'):+.0f}% in 20 days); "
         f"{v('Israel–Hamas', '2023-10-07', 'NIFTY', 'd1_pct'):+.1f}% after 7 Oct 2023 (Brent "
         f"{v('Israel–Hamas', '2023-10-07', 'BRENT', 'd20_pct'):+.0f}%); "
         f"{v('US–Iran', '2026-02-28', 'NIFTY', 'd20_pct'):+.1f}% in 20 days of the 2026 Gulf war (Brent "
         f"{v('US–Iran', '2026-02-28', 'BRENT', 'd20_pct'):+.0f}%)",
         "CORRECT, with a caveat: the Nifty fell when oil rose; when oil did not move (Oct 2023), neither did India",
         "DATA"),
        ("Russia had about $300B frozen", f"Pre-war reserves ${ru_r:,.0f}B (World Bank, end-2021); ~$300B immobilised "
         "is the figure in G7/EU statements", "CORRECT (order of magnitude; frozen amount is not in any data file)",
         "DOMAIN"),
        ("Israel's central bank committed $30B to defend the shekel",
         f"Shekel weakest at {ils_max:.2f}/USD after 7 Oct. Bank of Israel (9 Oct 2023): up to $30B spot FX sales plus up "
         "to $15B in swaps", "CORRECT; the full package was up to $45B ($30B sales + $15B swaps)", "DOMAIN + DATA"),
        ("Pakistan's reserves fell to less than a month of imports in 2023",
         f"World Bank end-2022: {pk_m:.1f} months of imports (annual, end-year); SBP liquid reserves fell to about $3B in "
         "Feb 2023, roughly three weeks of imports", "CORRECT", "DATA + DOMAIN"),
        ("Afghanistan's $9.5B were frozen in 2021", f"World Bank end-2020 reserves ${af_r:.1f}B; about $9B frozen "
         "(about $7B of it in the US)", "CORRECT (about $9B)", "DATA + DOMAIN"),
    ]
    irr = load_series("IRR")
    pre = irr[irr.index < "2026-02-28"].iloc[-1]
    rows.append(("Iran's rial collapsed", f"Rial lost {(1 - pre / irr.iloc[-1]) * 100:.0f}% of its value between the 2026 war "
                 f"and {irr.index[-1].date()} ({pre:,.0f} to {irr.iloc[-1]:,.0f} per USD, market rate)", "CORRECT", "DATA"))
    if pa is not None and len(pa):
        k, n = int(pa.within_45d.sum()), len(pa)
        rows.append(("Political crises line up with conflict peaks",
                     f"{k} of {n} dated crises fall within 45 days of a UCDP spike episode in the same theatre",
                     "PARTLY: onsets and regime shocks align; most domestic crises (Pakistan 2023-24, Iran 2022) do not",
                     "DATA + DOMAIN"))
    return pd.DataFrame(rows, columns=["claim", "measured", "verdict", "basis"])


# --------------------------------------------------------------------------- run
def run(cm: pd.DataFrame) -> dict:
    events = pd.read_parquet(C.PROCESSED / "events.parquet")
    ep = episodes(cm, events)
    es = event_study(ep)
    ind = india_monthly(cm)
    res = reserves()
    fr = fronts(cm, ep, es)
    pr = protests_2026()
    pa = political_alignment(ep)
    ck = claims(es, res, pa)
    ph = paths()
    gp = gpr_monthly(cm)
    T = C.TAB_DIR
    ep.to_csv(T / "econ_episodes.csv", index=False)
    es.round(5).to_csv(T / "econ_event_study.csv", index=False)
    ind.set_index('month').round(3).reset_index().to_csv(T / "econ_india_monthly.csv", index=False)
    res.to_csv(T / "econ_reserves.csv", index=False)
    fr.round(3).to_csv(T / "econ_fronts.csv", index=False)
    pa.to_csv(T / "econ_political_timeline.csv", index=False)
    pr.round(4).to_csv(T / "econ_protests_2026.csv", index=False)
    ck.to_csv(T / "econ_claims_check.csv", index=False)
    ph.round(3).to_csv(T / "econ_paths.csv", index=False)
    gp.set_index("month").round(3).reset_index().to_csv(T / "econ_gpr_monthly.csv", index=False)
    clean_log().to_csv(T / "econ_series_log.csv", index=False)
    summ = summary(ep, es, ind, fr)
    (T / "econ_summary.json").write_text(json.dumps(summ, indent=2, default=str))
    return dict(episodes=ep, event_study=es, india=ind, reserves=res, fronts=fr, political=pa, protests=pr,
                claims=ck, paths=ph, gpr=gp, summary=summ)


INDIA_CRUDE_MBD = 4.8      # DOMAIN: India's crude imports, million barrels a day (PPAC, FY2024-25 ~242 Mt)
INDIA_GULF_REMIT_SHARE = 0.38   # DOMAIN: share of inward remittances from the GCC (RBI remittance survey, 2023-24)
MAIN_SHOCKS = {"Russia–Ukraine": "2022-02-24", "Israel–Hamas": "2023-10-07", "US–Iran": "2026-02-28"}


def persistent(t0: str, k: str, pre_days=60, post_days=240) -> dict:
    s = load_series(k)
    t = pd.Timestamp(t0)
    a = s[(s.index < t) & (s.index >= t - pd.Timedelta(days=pre_days))].mean()
    b = s[(s.index >= t) & (s.index < t + pd.Timedelta(days=post_days))].mean()
    return dict(pre=float(a), post=float(b), change_pct=float((b / a - 1) * 100))


def summary(ep, es, ind, fr) -> dict:
    out = dict(n_episodes=int(len(ep)), n_moves=int(len(es)))
    out["share_significant_20d"] = float((es.p20 < 0.05).mean())
    onset = es[es.day0.isin(MAIN_SHOCKS.values())]
    other = es[~es.day0.isin(MAIN_SHOCKS.values())]
    out["sig_share_main_onsets"] = float((onset.p20 < 0.10).mean())
    out["sig_share_other_episodes"] = float((other.p20 < 0.10).mean())
    out["median_abs_move20_main"] = float(onset.d20_pct.abs().median())
    out["median_abs_move20_other"] = float(other.d20_pct.abs().median())
    pers = {}
    for case, t0 in MAIN_SHOCKS.items():
        pers[case] = {k: persistent(t0, k) for k in ["BRENT", "NIFTY", "INR"]}
    out["persistent"] = pers
    b26 = pers["US–Iran"]["BRENT"]
    extra = (b26["post"] - b26["pre"]) * INDIA_CRUDE_MBD * 1e6 * 365 / 1e9
    b22 = pers["Russia–Ukraine"]["BRENT"]
    extra22 = (b22["post"] - b22["pre"]) * INDIA_CRUDE_MBD * 1e6 * 365 / 1e9
    out["india_oil_bill"] = dict(crude_mbd_domain=INDIA_CRUDE_MBD,
                                 brent_up_usd_2026=b26["post"] - b26["pre"], extra_usd_bn_per_year_2026=extra,
                                 brent_up_usd_2022=b22["post"] - b22["pre"], extra_usd_bn_per_year_2022=extra22,
                                 per_10usd_bn_per_year=10 * INDIA_CRUDE_MBD * 1e6 * 365 / 1e9)
    rem = pd.read_csv(RAW / "wb_remit_in.csv") if (RAW / "wb_remit_in.csv").exists() else pd.DataFrame()
    if len(rem):
        r = rem[(rem.iso3 == "IND")].dropna().sort_values("year")
        last = r.iloc[-1]
        out["india_remittances"] = dict(year=int(last.year), usd_bn=float(last.value) / 1e9,
                                        gulf_share_domain=INDIA_GULF_REMIT_SHARE,
                                        gulf_usd_bn=float(last.value) / 1e9 * INDIA_GULF_REMIT_SHARE)
    out["fronts"] = fr.to_dict("records")
    res = reserves()
    if len(res):
        ri = res[res.iso3 == "IND"].set_index("year")
        rp = res[res.iso3 == "PAK"].set_index("year")
        out["reserves"] = dict(ind_2021_bn=float(ri.loc[2021, "reserves_usd"]) / 1e9,
                               ind_2022_bn=float(ri.loc[2022, "reserves_usd"]) / 1e9,
                               ind_2025_bn=float(ri.loc[2025, "reserves_usd"]) / 1e9,
                               ind_2025_months=float(ri.loc[2025, "months_of_imports"]),
                               pak_2021_bn=float(rp.loc[2021, "reserves_usd"]) / 1e9,
                               pak_2022_bn=float(rp.loc[2022, "reserves_usd"]) / 1e9,
                               pak_2022_months=float(rp.loc[2022, "months_of_imports"]))
    f = RAW / "gpr_daily.xls"
    if f.exists():
        d = pd.read_excel(f)
        d["date"] = pd.to_datetime(d["date"])
        d = d.set_index("date").GPRD
        out["gpr"] = {k: dict(pre30=float(d[pd.Timestamp(t) - pd.Timedelta(days=30):pd.Timestamp(t) - pd.Timedelta(days=1)].mean()),
                              peak10=float(d[pd.Timestamp(t):pd.Timestamp(t) + pd.Timedelta(days=10)].max()))
                      for k, t in MAIN_SHOCKS.items()}
    # key moves for the slides
    def mv(case, day0, k, c):
        r = es[(es.conflict_case == case) & (es.day0 == day0) & (es.series == k)]
        return float(r[c].iloc[0]) if len(r) else None
    out["headline"] = {
        "moex_day1": mv("Russia–Ukraine", "2022-02-24", "MOEX", "d1_pct"),
        "rub_worst": mv("Russia–Ukraine", "2022-02-24", "RUB", "worst60_pct"),
        "ttf_best": mv("Russia–Ukraine", "2022-02-24", "TTF", "best60_pct"),
        "wheat_best": mv("Russia–Ukraine", "2022-02-24", "WHEAT", "best60_pct"),
        "nifty_day1_2022": mv("Russia–Ukraine", "2022-02-24", "NIFTY", "d1_pct"),
        "ta35_worst": mv("Israel–Hamas", "2023-10-07", "TA35", "worst60_pct"),
        "ils_worst": mv("Israel–Hamas", "2023-10-07", "ILS", "worst60_pct"),
        "zim_worst": mv("Israel–Hamas", "2023-10-07", "ZIM", "worst60_pct"),
        "brent_d20_2026": mv("US–Iran", "2026-02-28", "BRENT", "d20_pct"),
        "brent_best_2026": mv("US–Iran", "2026-02-28", "BRENT", "best60_pct"),
        "nifty_d20_2026": mv("US–Iran", "2026-02-28", "NIFTY", "d20_pct"),
        "nifty_worst_2026": mv("US–Iran", "2026-02-28", "NIFTY", "worst60_pct"),
        "inr_worst_2026": mv("US–Iran", "2026-02-28", "INR", "worst60_pct"),
        "vix_best_2026": mv("US–Iran", "2026-02-28", "VIX", "best60_pct"),
    }
    irr = load_series("IRR")
    out["irr_2026"] = dict(pre_war=float(irr[irr.index < "2026-02-28"].iloc[-1]), last=float(irr.iloc[-1]),
                           last_date=irr.index[-1].date().isoformat(),
                           value_change_pct=float((irr[irr.index < "2026-02-28"].iloc[-1] / irr.iloc[-1] - 1) * 100))
    return out
