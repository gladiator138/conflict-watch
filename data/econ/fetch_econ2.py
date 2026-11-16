"""Second fetcher: exchange-native APIs for indices Yahoo lacks.
MOEX ISS (IMOEX, RTSI), PSX data portal (KSE-100), TSETMC (Iran TEDPIX)."""
import csv, json, os, time, urllib.request, datetime as dt
OUT = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()
log = []
# MOEX ISS history, paginated 100 rows
for sec in ["IMOEX", "RTSI"]:
    rows, start = [], 0
    try:
        while True:
            u = (f"https://iss.moex.com/iss/history/engines/stock/markets/index/securities/{sec}.json"
                 f"?from=2013-01-01&till=2026-11-17&start={start}&history.columns=TRADEDATE,CLOSE,HIGH,LOW")
            js = json.loads(get(u))["history"]["data"]
            if not js: break
            rows += js; start += len(js)
        with open(os.path.join(OUT, f"moex_{sec}.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["date", "close", "high", "low"]); w.writerows(rows)
        log.append(["moex", sec, len(rows), rows[0][0] if rows else "", rows[-1][0] if rows else "", "ok"])
    except Exception as e:
        log.append(["moex", sec, len(rows), "", "", repr(e)[:150]])
    print(log[-1], flush=True)
# PSX KSE-100
try:
    js = json.loads(get("https://dps.psx.com.pk/timeseries/eod/KSE100"))
    data = js.get("data", [])
    with open(os.path.join(OUT, "psx_KSE100.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["date", "close", "volume", "open"])
        for r in data:
            w.writerow([dt.datetime.utcfromtimestamp(r[0]).date().isoformat(), r[1], r[2], r[3] if len(r) > 3 else ""])
    log.append(["psx", "KSE100", len(data), "", "", "ok"])
except Exception as e:
    log.append(["psx", "KSE100", 0, "", "", repr(e)[:150]])
print(log[-1], flush=True)
# TSETMC overall index (TEDPIX) id 32097828799138957
for u in ["https://cdn.tsetmc.com/api/Index/GetIndexB2History/32097828799138957",
          "http://cdn.tsetmc.com/api/Index/GetIndexB2History/32097828799138957"]:
    try:
        js = json.loads(get(u))
        data = js.get("indexB2", [])
        with open(os.path.join(OUT, "tse_TEDPIX.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["dEven", "close", "high", "low"])
            for r in data:
                w.writerow([r.get("dEven"), r.get("xNivInuClMresIbs"), r.get("xNivInuPhMresIbs"), r.get("xNivInuPbMresIbs")])
        log.append(["tsetmc", "TEDPIX", len(data), "", "", "ok"]); print(log[-1]); break
    except Exception as e:
        log.append(["tsetmc", "TEDPIX", 0, "", "", repr(e)[:150]]); print(log[-1])
with open(os.path.join(OUT, "fetch_log2.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["source", "key", "n", "first", "last", "status"]); w.writerows(log)
print("DONE2")
