// Commander view: the landing screen. One screen, no scrolling at 1920×1080.
// Level 1 (glance) is this screen. Level 2 (understand) is the evidence sheet. Level 3 (analyse) is the Ops console.
// Every number is read from facts.json / monthly_conflict.json / areas.json; nothing is typed in here.
import { gsap } from "gsap";
import { type Data, type Score, CASE_COLOR, CASE_NAME, CASE_SHORT, RAG_COLOR, fmt, pct } from "./data";
import { rate, verify, DOCTRINE } from "./rules";
import { mount, axis, csv, C } from "./charts";
import { regionMap, el, tip } from "./maps";
import { strip, navBar, footer } from "./chrome";

const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
const fast = () => document.documentElement.classList.contains("pres");
const RAG_ICON: Record<string, string> = { RED: "▲", AMBER: "◆", GREEN: "●" };
const LINE_COLOR: Record<string, string> = { SENSE: "#4FD1E0", WARN: "#F2B33D", SHIELD: "#FF4D5E", SUSTAIN: "#A78BFA" };
/** Short glance wording for each order; the full text, lead and timeline are in the evidence sheet. */
const GLANCE: Record<string, string> = { SENSE: "Task ISR on the watch-list", WARN: "Treat the Af–Pak front as an LoC indicator", SHIELD: "Keep Gulf evacuation plans current", SUSTAIN: "Buffer critical spares" };
const CASE_LINE: Record<string, string | null> = { ruua: "SUSTAIN", afpak: "WARN", usir: "SHIELD", ilh: null };
const $ = <T extends HTMLElement = HTMLElement>(s: string, r: ParentNode = document) => r.querySelector(s) as T;
const $$ = <T extends HTMLElement = HTMLElement>(s: string, r: ParentNode = document) => Array.from(r.querySelectorAll(s)) as T[];

function spark(vals: number[], color: string, w = 220, h = 44) {
  const max = Math.max(...vals, 1), n = vals.length;
  const pts = vals.map((v, i) => `${((i / (n - 1)) * w).toFixed(1)},${(h - 3 - (v / max) * (h - 6)).toFixed(1)}`).join(" ");
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
    <polyline points="0,${h} ${pts} ${w},${h}" fill="${color}" opacity=".10" stroke="none"/>
    <polyline class="sl" points="${pts}" fill="none" stroke="${color}" stroke-width="2" pathLength="1" vector-effect="non-scaling-stroke"/></svg>`;
}

export function renderCommander(D: Data) {
  const F = D.facts, R = DOCTRINE(F);
  const S: Score[] = F.scorecard;
  const byId: Record<string, Score> = Object.fromEntries(S.map((s) => [s.id, s]));
  const recs: any[] = F.recommendations;
  const rec = (line: string | null) => recs.find((r) => r.line === line);
  const ind = F.india, mil = F.military, fc = F.forecasting, ew = F.warning;
  const bad = verify(S, R);
  if (bad.length) console.error("Scorecard parity FAILED", bad);
  const con = (page: string) => (D.inline ? `#console/${page}` : `console/index.html#${page}`);
  const count = (r: string) => S.filter((s) => s.rating === r).length;
  const words = ["No", "One", "Two", "Three", "Four"];
  const head = (["RED", "AMBER", "GREEN"] as const).filter((r) => count(r)).map((r, i) => `<span style="color:${RAG_COLOR[r]}">${i ? words[count(r)].toLowerCase() : words[count(r)]} at ${r}</span>`).join(", ");
  const watch = D.areas.areas.filter((a) => !a.unloc).slice(0, 10);
  const maxP = Math.max(...watch.map((a) => a.p));

  const reason = (s: Score) => {
    const p: string[] = [];
    if (s.forecast >= R.red_fc) p.push(`Forecast above ${fmt(R.red_fc)} deaths a month`);
    if (s.hotspots > 0) p.push(`${s.hotspots} area${s.hotspots > 1 ? "s" : ""} likely to escalate`);
    if (s.pts.spread > 0) p.push(`spread to ${s.countries_now} countries (${s.countries_prev} last year)`);
    if (s.pts.trend > 0) p.push("rising against the last six months");
    if (!p.length) p.push(s.pts.trend < 0 ? "No hotspots; falling" : "No hotspots; trend flat");
    const t = p.slice(0, 2).join("; ");
    return t.charAt(0).toUpperCase() + t.slice(1) + ".";
  };
  const trend = (s: Score) => (s.trend_pct >= R.trend_up ? "▲" : s.trend_pct <= R.trend_dn ? "▼" : "▶") + ` ${s.trend_pct > 0 ? "+" : ""}${s.trend_pct}% vs 6-month average`;

  document.body.classList.add("cmd-mode");
  document.body.insertAdjacentHTML("beforeend", `
  ${strip(F)} ${navBar(F, "command")}
  <main class="cmd" id="main">
    <header class="cmd-h">
      <div>
        <div class="eyebrow">COMMANDER'S VIEW · ${S[0].month.toUpperCase()}</div>
        <h1 class="cmd-t">${head}.</h1>
      </div>
      <button class="btn" id="cmd-detail" aria-pressed="false" title="Show or hide trends, reasons, leads and the full watch-list (D)">MORE DETAIL · OFF</button>
    </header>

    <section class="cmd-tiles" aria-label="Threat status by conflict">
      ${S.map((s) => { const col = RAG_COLOR[s.rating]; const m = D.monthly[s.id];
        return `<button class="tile" data-ev="c:${s.id}" style="--rag:${col}" aria-label="${s.name}: ${s.rating}. Forecast ${fmt(s.forecast)} deaths in ${s.month}. Open evidence.">
          <div class="tile-n">${s.name}</div>
          <div class="pill"><i>${RAG_ICON[s.rating]}</i>${s.rating}</div>
          <div class="tile-mid"><span class="tile-v" data-count="${s.forecast}">${fmt(s.forecast)}</span><span class="tile-u">deaths forecast, ${s.month}</span></div>
          <div class="tile-more">${spark(m.deaths.slice(-36), col)}<div class="tile-tr">${trend(s)}</div><div class="tile-r">${reason(s)}</div></div>
        </button>`; }).join("")}
    </section>

    <section class="cmd-main">
      <div class="cmd-map panel">
        <div class="ph"><span class="t">Where it touches India</span><span class="tag data">DATA</span></div>
        <div class="mapbox" id="cmd-map" aria-label="Map of India's exposure: Line of Control, Gulf states, Hormuz and Chabahar coast, Sri Lankan waters, Red Sea"></div>
      </div>
      <aside class="cmd-side" aria-label="Orders and watch-list">
        <div class="side-h">ORDERS THIS MONTH</div>
        ${recs.map((r) => `<button class="order" data-ev="o:${r.line}" style="--lc:${LINE_COLOR[r.line] ?? "#4FD1E0"}">
          <span class="o-l">${r.line}</span><span class="o-w">${r.when.split(" / ")[0]}</span>
          <span class="o-a">${GLANCE[r.line] ?? r.action.split(". ")[0]}</span>
          <span class="o-m">${r.lead}</span></button>`).join("")}
        <div class="side-h" style="margin-top:6px">WATCH NEXT MONTH <button class="lnk" data-ev="w:all">ALL 10 ▸</button></div>
        <div class="wl">${watch.map((a, i) => `<a class="wl-r" href="${con("area?id=" + encodeURIComponent(a.id))}" title="${a.name}, ${a.iso}: open area drill-down">
          <span class="wl-i">${i + 1}</span><span class="wl-n">${a.name}<em>${CASE_SHORT[a.c]}</em></span>
          <span class="wl-b"><i style="width:${(a.p / maxP * 100).toFixed(0)}%;background:${CASE_COLOR[a.c]}"></i></span><span class="wl-p">${pct(a.p)}</span></a>`).join("")}</div>
      </aside>
    </section>

    <nav class="cmd-go" aria-label="Go deeper">
      <a class="btn primary" href="#bluf">FULL BRIEFING ▸</a>
      <a class="btn" href="${con("brief")}">OPS CONSOLE ▸</a>
      <span class="grow"></span>
      <button class="trustline" data-ev="trust">Tested on unseen 2026 data: forecast error <b>−${fc.mae_pooled}%</b> against "no change" · watch-list <b>${ew.lift}×</b> better than chance <span>HOW FAR TO TRUST THIS ▸</span></button>
    </nav>
  </main>
  <aside class="sheet" id="sheet" role="dialog" aria-modal="false" aria-label="Evidence"><div class="sheet-in" id="sheet-in"></div></aside>
  <div class="sheet-bg" id="sheet-bg"></div>
  ${footer(F)}`);

  // ---- India exposure map
  const m = regionMap($("#cmd-map"), D.world, [[33, 3], [92, 38]]);
  const dots = D.points.filter((p) => (p[0] === "usir" && p[3] === 2026) || (p[0] === "afpak" && p[3] >= 2025));
  const maxD = Math.max(...dots.map((p) => p[4]), 1);
  for (const p of dots) { const xy = m.proj([p[1], p[2]]); if (!xy) continue;
    el("circle", { cx: xy[0], cy: xy[1], r: (2 + 12 * Math.sqrt(p[4] / maxD)).toFixed(1), fill: CASE_COLOR[p[0]], opacity: 0.45, class: "cdot" }, m.layer); }
  const adj = ind.pak_india_adjoining;
  type Mk = { id: string; lon: number; lat: number; label: string; v: string; anchor?: "start" | "end" };
  const marks: Mk[] = [
    { id: "loc", lon: 74.2, lat: 33.6, label: "LoC", v: `${adj[2022]} → ${adj[2025]} deaths`, anchor: "end" },
    { id: "gulf", lon: 53.2, lat: 24.6, label: "GULF STATES", v: `${ind.gulf_states} struck`, anchor: "end" },
    { id: "hormuz", lon: 57.6, lat: 26.6, label: "HORMUZ · CHABAHAR", v: `${ind.hormuz_deaths} deaths` },
    { id: "lanka", lon: 79.0, lat: 6.6, label: "OFF SRI LANKA", v: `${ind.srilanka.deaths} killed`, anchor: "end" },
    { id: "redsea", lon: 43.6, lat: 14.6, label: "RED SEA · YEMEN", v: `${fmt(ind.yemen_2025)} deaths` },
  ];
  marks.forEach((k, i) => {
    const xy = m.proj([k.lon, k.lat]); if (!xy) return;
    const g = el("g", { class: "mk", tabindex: 0, role: "button", "aria-label": `${k.label}: ${k.v}. Open evidence.`, "data-ev": "m:" + k.id, style: `--d:${0.5 + i * 0.12}s` }, m.top);
    el("circle", { cx: xy[0], cy: xy[1], r: 22, class: "mk-hit" }, g);
    el("circle", { cx: xy[0], cy: xy[1], r: 11, class: "mk-ring" }, g);
    el("circle", { cx: xy[0], cy: xy[1], r: 11, class: "mk-ping" }, g);
    el("circle", { cx: xy[0], cy: xy[1], r: 4.5, class: "mk-dot" }, g);
    const end = k.anchor === "end", x = end ? xy[0] - 18 : xy[0] + 18;
    const t1 = el("text", { x, y: xy[1] - 2, "text-anchor": end ? "end" : "start", class: "mk-l" }, g); t1.textContent = k.label;
    const t2 = el("text", { x, y: xy[1] + 15, "text-anchor": end ? "end" : "start", class: "mk-v" }, g); t2.textContent = k.v;
  });

  // ---- Evidence sheet (Level 2), with links to Level 3
  const sheet = $("#sheet"), sin = $("#sheet-in"), sbg = $("#sheet-bg");
  let lastFocus: HTMLElement | null = null;
  const close = () => { sheet.classList.remove("open"); sbg.classList.remove("open"); $$(".tile,.order,.mk").forEach((e) => e.classList.remove("sel")); lastFocus?.focus?.(); };
  const nums = (a: [string, string][]) => `<div class="ev-n">${a.map(([v, l]) => `<div><b>${v}</b><span>${l}</span></div>`).join("")}</div>`;
  const action = (r: any, note = "") => r ? `<div class="ev-act" style="--lc:${LINE_COLOR[r.line]}"><span class="o-l">${r.line}</span><div><b>${r.action}</b><span>Lead: ${r.lead} · When: ${r.when}</span>${note ? `<span>${note}</span>` : ""}</div></div>`
    : `<div class="ev-act" style="--lc:var(--green)"><span class="o-l">HOLD</span><div><b>No new action this month.</b><span>Review at the next monthly run.</span></div></div>`;
  const links = (a: [string, string][], dl = false) => `<div class="ev-go">${a.map(([l, h], i) => `<a class="btn${i ? "" : " primary"}" href="${h}">${l}</a>`).join("")}${dl ? `<button class="btn" id="ev-csv">⬇ CSV</button>` : ""}</div>`;
  const shell = (kick: string, title: string, body: string) => `<button class="btn ev-x" id="ev-x" aria-label="Close evidence">✕ CLOSE</button>
    <div class="eyebrow">${kick}</div><h2 class="ev-t">${title}</h2>${body}`;
  const usirSeries = () => { const M = D.monthly.usir, i0 = M.months.indexOf("2025-01"); return { x: M.months.slice(i0), y: M.deaths.slice(i0) }; };
  const bar = (x: (string | number)[], y: number[], color: string, name: string) => ({
    grid: { left: 52, right: 14, top: 18, bottom: 34 }, legend: { show: false }, toolbox: { show: false },
    xAxis: { type: "category", data: x, ...axis() }, yAxis: { type: "value", ...axis() },
    series: [{ type: "bar", name, data: y, itemStyle: { color, borderRadius: [3, 3, 0, 0] }, barMaxWidth: 26 }] });

  const open = (key: string, from: HTMLElement) => {
    lastFocus = from;
    $$(".tile,.order,.mk").forEach((e) => e.classList.toggle("sel", e === from));
    const [kind, id] = key.split(":");
    let chart: any = null, rows: Record<string, any>[] = [], file = "evidence.csv";
    if (kind === "c") {
      const s = byId[id], r = rate(s, R), M = D.monthly[id], col = RAG_COLOR[s.rating], n = 36;
      const x = [...M.months.slice(-n), ...s.forward.map((f) => f.month)], act = M.deaths.slice(-n);
      const pad = (v: (number | null)[]) => [...Array(n - 1).fill(null), act[n - 1], ...v];
      chart = { grid: { left: 58, right: 16, top: 30, bottom: 34 }, toolbox: { show: false },
        legend: { top: 0, right: 0, left: "auto", data: ["Recorded", "Forecast", "80% band"], textStyle: { color: C.tx2(), fontSize: 12 } },
        xAxis: { type: "category", data: x, ...axis({ axisLabel: { color: C.tx2(), fontSize: 12, interval: 5 } }) }, yAxis: { type: "value", ...axis() },
        series: [
          { type: "line", name: "Recorded", data: [...act, ...s.forward.map(() => null)], showSymbol: false, lineStyle: { color: CASE_COLOR[id], width: 2.5 }, itemStyle: { color: CASE_COLOR[id] }, areaStyle: { color: CASE_COLOR[id], opacity: 0.08 } },
          { type: "line", name: "lo", stack: "b", data: pad(s.forward.map((f) => f.lo)), showSymbol: false, lineStyle: { opacity: 0 }, tooltip: { show: false }, silent: true },
          { type: "line", name: "80% band", stack: "b", data: pad(s.forward.map((f) => f.hi - f.lo)).map((v, i) => (i === n - 1 ? 0 : v)), showSymbol: false, lineStyle: { opacity: 0 }, areaStyle: { color: col, opacity: 0.2 }, itemStyle: { color: col } },
          { type: "line", name: "Forecast", data: pad(s.forward.map((f) => f.pred)), symbolSize: 8, lineStyle: { color: col, width: 2.5, type: "dashed" }, itemStyle: { color: col } },
        ] };
      rows = s.forward.map((f) => ({ conflict: s.name, month: f.month, forecast: f.pred, low80: f.lo, high80: f.hi })); file = `forecast_${id}.csv`;
      const pr = (l: string, v: number) => `<div class="ptsrow"><span>${l}</span><b style="color:${v > 0 ? col : "var(--tx2)"}">${v > 0 ? "+" : ""}${v}</b></div>`;
      sin.innerHTML = shell(`${s.name.toUpperCase()} · ${s.month.toUpperCase()}`, `<span style="color:${col}">${RAG_ICON[s.rating]} ${s.rating}</span> · ${reason(s)}`,
        nums([[fmt(s.forecast), `deaths forecast, ${s.month}`], [`${fmt(s.lo)}–${fmt(s.hi)}`, "likely range (80% band)"], [`${s.trend_pct > 0 ? "+" : ""}${s.trend_pct}%`, "against the 6-month average"]]) +
        `<div class="ev-ch" id="ev-ch"></div>` + action(rec(CASE_LINE[id])) +
        `<details class="ev-d"><summary>How the rating was scored (${r.points} points)</summary>${pr("Intensity of the forecast", r.pts.intensity)}${pr("Trend", r.pts.trend)}${pr(`Hotspots (areas at ${Math.round(R.hot_p * 100)}% or more)`, r.pts.hotspots)}${pr("Spread to new countries", r.pts.spread)}${pr("A 1,000-death month in the last year", r.pts.volatility)}
          <p class="small muted">RED: forecast of ${fmt(R.red_fc)} or more, or ${R.red_pts}+ points. AMBER: ${R.amber_pts}–${R.red_pts - 1} points. GREEN: below ${R.amber_pts}.${s.top.length ? ` Areas to watch: ${s.top.map((t) => `${t.name} ${Math.round(t.p * 100)}%`).join(", ")}.` : ""}</p></details>` +
        links([["FULL FORECAST ▸", con("forecast")], ["TEST A WHAT-IF ▸", con(`whatif?c=${id}`)], ["CHANGE THE RULES ▸", con("scorecard")]], true));
    } else if (kind === "m") {
      const shield = rec("SHIELD"), U = usirSeries();
      const usir = () => { chart = bar(U.x, U.y, CASE_COLOR.usir, "US–Iran deaths"); chart.xAxis.axisLabel = { color: C.tx2(), fontSize: 12, interval: 3 }; rows = U.x.map((mth, i) => ({ month: mth, usiran_deaths: U.y[i] })); file = "usiran_monthly.csv"; };
      if (id === "loc") {
        const ys = Object.keys(adj).filter((y) => +y >= 2018); chart = bar(ys, ys.map((y) => adj[y]), CASE_COLOR.afpak, "Deaths"); rows = ys.map((y) => ({ year: y, deaths_pakistan_areas_adjoining_india: adj[y] })); file = "loc_adjoining.csv";
        sin.innerHTML = shell("LINE OF CONTROL · AF–PAK", "Pakistan now fights on two fronts in the west.",
          nums([[fmt(mil.afpak_dyad["2026-03"]), "deaths in Afghan–Pakistani state clashes, Mar 2026 (peak)"], [`${adj[2022]} → ${adj[2025]}`, "deaths in Pakistan areas adjoining India / LoC, 2022 → 2025"], [String(byId.afpak.hotspots), `Af–Pak areas likely to escalate in ${byId.afpak.month}`]]) +
          `<div class="ev-ch" id="ev-ch"></div><p class="ev-p"><span class="tag domain">DOMAIN</span> With the Pakistan Army committed in the west, watch for diversionary activity on the LoC and for spill-over.</p>` +
          action(rec("WARN")) + links([["THE FINDING ▸", "#afpak"], ["AREA MAP ▸", con("map")]], true));
      } else if (id === "gulf") { usir();
        sin.innerHTML = shell("GULF STATES · US–IRAN WAR", `The war reached ${ind.gulf_states} Gulf states.`,
          nums([[String(ind.gulf_states), "Gulf states struck in 2026"], [String(ind.gulf_events), "recorded events in those states"], [`${ind.usir_countries[0]} → ${ind.usir_countries[1]}`, "countries with US–Iran war deaths, 2025 → 2026"]]) +
          `<div class="ev-ch" id="ev-ch"></div><p class="ev-p"><span class="tag domain">DOMAIN</span> These states host a large Indian diaspora. Evacuation plans must be current before the next spike, not after it.</p>` +
          action(shield) + links([["THE FINDING ▸", "#india"], ["US–IRAN FORECAST ▸", con("forecast")]], true));
      } else if (id === "hormuz") { usir();
        sin.innerHTML = shell("HORMUZ · CHABAHAR COAST", "Deaths cluster on Iran's Hormuz and Chabahar coast.",
          nums([[fmt(ind.hormuz_deaths), "deaths on that coast in 2026"], [pct(byId.usir.top[0]?.p ?? 0), `chance ${byId.usir.top[0]?.name ?? "the area"} escalates in ${byId.usir.month}`], [fmt(mil.usir_2026.iran), "Iranian deaths recorded in 2026"]]) +
          `<div class="ev-ch" id="ev-ch"></div><p class="ev-p"><span class="tag domain">DOMAIN</span> Gulf energy shipments, Chabahar and the INSTC all sit inside this strike zone.</p>` +
          action(shield) + links([["THE FINDING ▸", "#india"], ["AREA MAP ▸", con("map")]], true));
      } else if (id === "lanka") { usir();
        const d = new Date(ind.srilanka.date + "T00:00:00");
        sin.innerHTML = shell("INDIAN OCEAN · SRI LANKAN WATERS", `One strike killed ${ind.srilanka.deaths} off Sri Lanka.`,
          nums([[String(ind.srilanka.deaths), "killed in one strike"], [d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }), "date of the strike"], [String(ind.usir_countries[1]), "countries the war reached in 2026"]]) +
          `<div class="ev-ch" id="ev-ch"></div><p class="ev-p"><span class="tag domain">DOMAIN</span> The war reached India's maritime neighbourhood. Belligerent movement in the IOR needs a standing picture.</p>` +
          action(shield) + links([["THE FINDING ▸", "#india"], ["OPS CONSOLE ▸", con("brief")]], true));
      } else {
        sin.innerHTML = shell("RED SEA · YEMEN", `Yemen recorded ${fmt(ind.yemen_2025)} deaths in 2025.`,
          nums([[fmt(ind.yemen_2025), "deaths in Yemen, 2025"], [String(ind.usir_countries[1]), "countries the US–Iran war reached in 2026"]]) +
          `<p class="ev-p"><span class="tag domain">DOMAIN</span> The Red Sea shipping lane runs past this coast.</p>` + action(shield) + links([["THE FINDING ▸", "#india"]]));
      }
    } else if (kind === "w") {
      rows = watch.map((a, i) => ({ rank: i + 1, area: a.name, country: a.iso, conflict: CASE_NAME[a.c], chance_of_escalation: a.p })); file = "watchlist.csv";
      sin.innerHTML = shell(`WATCH-LIST · ${S[0].month.toUpperCase()}`, "Ten areas most likely to escalate next month.",
        `<p class="ev-p">Use the list as a ranking, not as exact odds. Select an area for its history.</p>
         <div class="ev-wl">${watch.map((a, i) => `<a class="wl-r" href="${con("area?id=" + encodeURIComponent(a.id))}"><span class="wl-i">${i + 1}</span><span class="wl-n">${a.name}<em>${a.iso} · ${CASE_SHORT[a.c]}</em></span><span class="wl-b"><i style="width:${(a.p / maxP * 100).toFixed(0)}%;background:${CASE_COLOR[a.c]}"></i></span><span class="wl-p">${pct(a.p)}</span></a>`).join("")}</div>` +
        action(rec("SENSE")) + links([["REPLAY 2026 ▸", con("warning")], ["AREA MAP ▸", con("map")]], true));
    } else if (kind === "o") {
      const r = rec(id);
      sin.innerHTML = shell(`ORDER · ${r.line}`, r.action,
        `<div class="ev-n"><div><b>${r.lead}</b><span>lead</span></div><div><b>${r.when}</b><span>timeline</span></div></div>
         <p class="ev-p"><span class="tag data">TRIGGER</span> ${r.why}.</p>` + links([["SEE THE FINDING ▸", "#" + r.trigger], ["ALL RECOMMENDATIONS ▸", "#recs"]]));
    } else {
      const lb = fc.leaderboard.find((x: any) => x.model === "ensemble"), nv = fc.leaderboard.find((x: any) => x.model === "naive");
      const cs = S.map((s) => s.id);
      chart = bar(cs.map((c) => CASE_SHORT[c]), cs.map((c) => fc.mae_vs_naive[c]), "#4FD1E0", "Error cut vs no change (%)");
      rows = cs.map((c) => ({ conflict: CASE_NAME[c], error_cut_vs_no_change_pct: fc.mae_vs_naive[c] })); file = "error_cut.csv";
      sin.innerHTML = shell("HOW FAR TO TRUST THIS", "Tested once on 2026 data the models never saw.",
        nums([[`−${fc.mae_pooled}%`, "forecast error against \"no change\""], [`${fc.coverage.all}%`, "of 2026 outcomes fell inside the stated range"], [`${ew.lift}×`, "watch-list better than chance"]]) +
        `<div class="ev-ch" id="ev-ch"></div><p class="ev-p">Error cut by conflict, in per cent. ${(ew.p10 * 10).toFixed(1)} of each month's top 10 areas escalated, against ${(ew.base * 10).toFixed(1)} by chance.</p>
         <p class="ev-p"><span class="tag caveat">LIMIT</span> ${F.limits[F.limits.length - 1]}</p>
         <p class="ev-p small muted">${bad.length ? "⚠ Scorecard parity failed: " + bad.join("; ") : "✓ Ratings recomputed in the browser match the pipeline."} Run ${F.run_id}.</p>
         <details class="ev-d"><summary>For the analyst</summary><p class="small muted">Ensemble RMSLE ${lb.A_hold} against ${nv.A_hold} for "no change" (1 month ahead, 2026). Early-warning ROC-AUC ${ew.auc}; top-10 precision ${pct(ew.p10, 1)} against a base rate of ${pct(ew.base, 1)}. Every design choice was made on the 2022–25 back-test.</p></details>` +
        links([["FORECAST TEST ▸", con("forecast")], ["WARNING REPLAY ▸", con("warning")], ["LIMITS AND METHOD ▸", "#method"]], true));
    }
    sheet.classList.add("open"); sbg.classList.add("open"); sheet.scrollTop = 0;
    const ce = document.getElementById("ev-ch");
    if (ce && chart) setTimeout(() => mount(ce, { animationDuration: fast() ? 300 : 700, ...chart }, false), 60);
    $("#ev-x").addEventListener("click", close);
    document.getElementById("ev-csv")?.addEventListener("click", () => csv(file, rows));
    if (!REDUCE) gsap.fromTo(sin.children, { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: fast() ? 0.15 : 0.3, stagger: 0.04, ease: "power2.out" });
    setTimeout(() => $("#ev-x").focus(), 80);
  };
  document.addEventListener("click", (e) => { const t = (e.target as Element).closest("[data-ev]") as HTMLElement | null; if (t) open(t.dataset.ev!, t); });
  document.addEventListener("keydown", (e) => {
    const t = e.target as HTMLElement;
    if ((e.key === "Enter" || e.key === " ") && t.matches?.(".mk")) { e.preventDefault(); open(t.dataset.ev!, t); }
    if (e.key === "Escape") close();
  });
  sbg.addEventListener("click", close);
  $$(".mk").forEach((g) => { g.addEventListener("mousemove", (e) => tip("Open evidence", e as MouseEvent)); g.addEventListener("mouseleave", () => tip(null)); });
  // ---- Glance by default; "More detail" adds trends, reasons, leads and the full watch-list
  const root = document.documentElement, db = $("#cmd-detail");
  const setDetail = (on: boolean) => { root.classList.toggle("cmd-detail", on); db.textContent = `MORE DETAIL · ${on ? "ON" : "OFF"}`; db.classList.toggle("on", on); db.setAttribute("aria-pressed", String(on)); try { sessionStorage.setItem("cw-detail", on ? "1" : "0"); } catch {} };
  let d0 = false; try { d0 = sessionStorage.getItem("cw-detail") === "1"; } catch {}
  setDetail(d0);
  db.addEventListener("click", () => setDetail(!root.classList.contains("cmd-detail")));
  addEventListener("keydown", (e) => { const tg = (e.target as HTMLElement).tagName; if (tg === "INPUT" || tg === "SELECT" || tg === "TEXTAREA" || e.metaKey || e.ctrlKey) return; if (e.key === "d" || e.key === "D") setDetail(!root.classList.contains("cmd-detail")); });

  // ---- Entrance: tiles, then map, then orders. Numbers count up; trend lines draw in.
  if (REDUCE) { document.documentElement.classList.add("noanim"); return; }
  const k = fast() ? 0.45 : 1;
  gsap.from(".cmd-h > *", { opacity: 0, y: 12, duration: 0.4 * k, stagger: 0.08 * k, ease: "power2.out" });
  gsap.from(".tile", { opacity: 0, y: 18, duration: 0.45 * k, stagger: 0.09 * k, delay: 0.1 * k, ease: "power3.out", clearProps: "transform,opacity" });
  gsap.from(".cmd-map, .cmd-go", { opacity: 0, y: 16, duration: 0.45 * k, stagger: 0.08 * k, delay: 0.4 * k, ease: "power3.out", clearProps: "transform,opacity" });
  gsap.from(".side-h, .order, .wl-r", { opacity: 0, x: 14, duration: 0.35 * k, stagger: 0.06 * k, delay: 0.65 * k, ease: "power2.out", clearProps: "transform,opacity" });
  gsap.from(".wl-b i", { scaleX: 0, transformOrigin: "left center", duration: 0.6 * k, stagger: 0.03 * k, delay: 0.75 * k, ease: "power2.out" });
  gsap.fromTo(".spark .sl", { strokeDasharray: 1, strokeDashoffset: 1 }, { strokeDashoffset: 0, duration: 1.0 * k, delay: 0.3 * k, ease: "power2.inOut", stagger: 0.09 * k });
  $$(".tile-v").forEach((e, i) => { const end = +e.dataset.count!, o = { v: 0 };
    gsap.to(o, { v: end, duration: 1.0 * k, delay: (0.2 + i * 0.09) * k, ease: "power3.out", onUpdate: () => (e.textContent = fmt(Math.round(o.v))), onComplete: () => (e.textContent = fmt(end)) }); });
}
