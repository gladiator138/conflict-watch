"""Fetch public market/macro series for the economic-front event study.
Stdlib only (urllib). Writes raw files next to this script and a fetch_log.csv.
Sources: Yahoo Finance chart API (daily closes), FRED (fredgraph.csv),
World Bank API (annual), Caldara-Iacoviello GPR index.
"""
import csv, json, os, sys, time, urllib.request, datetime as dt

OUT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
P1 = int(dt.datetime(2013, 1, 1).timestamp())
P2 = int(dt.datetime(2026, 11, 17).timestamp())
log = []

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:
            err = e
            time.sleep(2 * (i + 1))
    raise err

YAHOO = {
    "NSEI": "^NSEI", "BSESN": "^BSESN", "INR": "INR=X",
    "IMOEX": "IMOEX.ME", "RTSI": "RTSI.ME", "RUB": "RUB=X",
    "TA35": "TA35.TA", "TA125": "^TA125.TA", "ILS": "ILS=X",
    "KSE100": "^KSE", "PKR": "PKR=X", "IRR": "IRR=X", "AFN": "AFN=X",
    "UAH": "UAH=X", "BRENT": "BZ=F", "WTI": "CL=F", "GOLD": "GC=F",
    "VIX": "^VIX", "SPX": "^GSPC", "BDRY": "BDRY", "ZIM": "ZIM",
    "FRO": "FRO", "DXY": "DX-Y.NYB", "TTF": "TTF=F", "WHEAT": "ZW=F",
    "MSCIEM": "EEM", "ITA": "ITA",
}
for key, sym in YAHOO.items():
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/" +
           urllib.request.quote(sym) + f"?period1={P1}&period2={P2}&interval=1d&events=history")
    try:
        js = json.loads(get(url))
        res = js["chart"]["result"][0]
        ts = res.get("timestamp") or []
        q = res["indicators"]["quote"][0]
        adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose")
        with open(os.path.join(OUT, f"yahoo_{key}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "close", "adjclose", "high", "low"])
            for i, t in enumerate(ts):
                d = dt.datetime.utcfromtimestamp(t + res["meta"].get("gmtoffset", 0)).date().isoformat()
                w.writerow([d, q["close"][i], adj[i] if adj else "", q["high"][i], q["low"][i]])
        log.append(["yahoo", key, sym, len(ts), ts and dt.datetime.utcfromtimestamp(ts[0]).date(), ts and dt.datetime.utcfromtimestamp(ts[-1]).date(), "ok"])
    except Exception as e:
        log.append(["yahoo", key, sym, 0, "", "", repr(e)[:150]])
    print(log[-1], flush=True)

FRED = ["DCOILBRENTEU", "DEXINUS", "EXINUS", "TRESEGINM052N", "TRESEGRUM052N",
        "TRESEGILM052N", "TRESEGPKM052N", "TRESEGUAM052N", "TRESEGIRM052N",
        "TRESEGAFM052N", "INDCPIALLMINMEI", "GEPUCURRENT", "VIXCLS",
        "PCU483111483111", "DHHNGSP", "WPU0561", "PNGASEUUSDM", "POILBREUSDM"]
for s in FRED:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}&cosd=2013-01-01"
    try:
        b = get(url)
        open(os.path.join(OUT, f"fred_{s}.csv"), "wb").write(b)
        n = b.count(b"\n") - 1
        log.append(["fred", s, s, n, "", "", "ok"])
    except Exception as e:
        log.append(["fred", s, s, 0, "", "", repr(e)[:150]])
    print(log[-1], flush=True)

WB = {"BX.TRF.PWKR.CD.DT": "remit_in", "NY.GDP.MKTP.KD.ZG": "gdp_growth",
      "FP.CPI.TOTL.ZG": "cpi", "FI.RES.TOTL.MO": "res_months_imports",
      "FI.RES.TOTL.CD": "reserves_usd", "MS.MIL.XPND.GD.ZS": "milex_gdp",
      "NY.GDP.MKTP.CD": "gdp_usd", "PA.NUS.FCRF": "fx_official"}
for ind, name in WB.items():
    url = (f"https://api.worldbank.org/v2/country/IND;RUS;UKR;ISR;PSE;PAK;AFG;IRN;SAU;ARE/indicator/{ind}"
           "?format=json&date=2013:2025&per_page=2000")
    try:
        js = json.loads(get(url))
        rows = js[1] or []
        with open(os.path.join(OUT, f"wb_{name}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["iso3", "year", "value"])
            for r in rows:
                w.writerow([r["countryiso3code"], r["date"], r["value"]])
        log.append(["worldbank", name, ind, len(rows), "", "", "ok"])
    except Exception as e:
        log.append(["worldbank", name, ind, 0, "", "", repr(e)[:150]])
    print(log[-1], flush=True)

for nm, url in {"gpr_daily": "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls",
                "gpr_monthly": "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"}.items():
    try:
        b = get(url); open(os.path.join(OUT, nm + ".xls"), "wb").write(b)
        log.append(["gpr", nm, url, len(b), "", "", "ok"])
    except Exception as e:
        log.append(["gpr", nm, url, 0, "", "", repr(e)[:150]])
    print(log[-1], flush=True)

with open(os.path.join(OUT, "fetch_log.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["source", "key", "id", "n", "first", "last", "status"]); w.writerows(log)
print("DONE", dt.datetime.now().isoformat())
