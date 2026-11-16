"""Third fetcher: World Bank annual, IMF reserves (monthly), GPR index."""
import csv, json, os, time, urllib.request, datetime as dt
OUT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "*/*"}
def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
log = []
def rec(*a):
    log.append(list(a)); print(a, flush=True)
WB = {"BX.TRF.PWKR.CD.DT": "remit_in", "NY.GDP.MKTP.KD.ZG": "gdp_growth",
      "FP.CPI.TOTL.ZG": "cpi", "FI.RES.TOTL.MO": "res_months_imports",
      "FI.RES.TOTL.CD": "reserves_usd", "MS.MIL.XPND.GD.ZS": "milex_gdp",
      "NY.GDP.MKTP.CD": "gdp_usd", "PA.NUS.FCRF": "fx_official",
      "NE.IMP.GNFS.CD": "imports_usd"}
for ind, name in WB.items():
    u = (f"https://api.worldbank.org/v2/country/IND;RUS;UKR;ISR;PSE;PAK;AFG;IRN;SAU;ARE;WLD/indicator/{ind}"
         "?format=json&date=2013:2025&per_page=2000")
    try:
        rows = json.loads(get(u))[1] or []
        with open(os.path.join(OUT, f"wb_{name}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["iso3", "year", "value"])
            for r in rows: w.writerow([r["countryiso3code"], r["date"], r["value"]])
        rec("worldbank", name, len(rows), "ok")
    except Exception as e:
        rec("worldbank", name, 0, repr(e)[:150])
# IMF IFS reserves excl gold, USD, monthly (legacy SDMX JSON service)
for c in ["IN", "RU", "IL", "PK", "UA", "IR", "AF"]:
    ok = False
    for u in [f"https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/M.{c}.RAXGFX_USD?startPeriod=2013",
              f"http://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS/M.{c}.RAXGFX_USD?startPeriod=2013"]:
        try:
            js = json.loads(get(u, 90))
            s = js["CompactData"]["DataSet"].get("Series", {})
            obs = s.get("Obs", []) if isinstance(s, dict) else []
            if isinstance(obs, dict): obs = [obs]
            with open(os.path.join(OUT, f"imf_res_{c}.csv"), "w", newline="") as f:
                w = csv.writer(f); w.writerow(["period", "value_musd"])
                for o in obs: w.writerow([o.get("@TIME_PERIOD"), o.get("@OBS_VALUE")])
            rec("imf", c, len(obs), "ok"); ok = True; break
        except Exception as e:
            rec("imf", c, 0, repr(e)[:150])
    if not ok and c == "IN": break  # service down, don't hammer
for nm, u in {"gpr_daily": "https://www.matteoiacoviello.com/gpr_files/data_gpr_daily_recent.xls",
              "gpr_monthly": "https://www.matteoiacoviello.com/gpr_files/data_gpr_export.xls"}.items():
    try:
        b = get(u, 90); open(os.path.join(OUT, nm + ".xls"), "wb").write(b); rec("gpr", nm, len(b), "ok")
    except Exception as e:
        rec("gpr", nm, 0, repr(e)[:150])
with open(os.path.join(OUT, "fetch_log3.csv"), "w", newline="") as f:
    csv.writer(f).writerows([["source", "key", "n", "status"]] + log)
print("DONE3")
