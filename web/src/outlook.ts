// 2027 outlook for each theatre: a scenario range from history (analogue method, scripts/outlook_2027.py),
// plus what our analysis says to watch and do in that theatre. Data: web/public/data/outlook2027.json + facts.json.
import { type Data, RAG_COLOR, fmt } from "./data";

const esc = (s: any) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
const pc = (x: number) => `${Math.round(x * 100)}%`;
const CSS = `
.ol { display:flex; flex-direction:column; gap:14px; }
.ol-top { display:flex; flex-wrap:wrap; gap:10px; align-items:center; }
.ol-tag { font: 800 11px var(--mono); letter-spacing:.14em; padding:4px 9px; border-radius:6px; border:1px solid var(--amber); color: var(--amber); }
.ol-tag.r { border-color: var(--red); color: var(--red); }
.ol-cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap:14px; }
.ol-card { background: var(--panel); border:1px solid var(--line); border-radius:14px; padding:16px 18px; }
.ol-card h4 { margin:0 0 6px; font-size:19px; display:flex; justify-content:space-between; gap:8px; align-items:center; }
.ol-lv { display:flex; gap:8px; align-items:center; font: 800 12px var(--mono); letter-spacing:.1em; }
.ol-lv b { padding:3px 8px; border-radius:6px; color:#05070A; }
.ol-big { font-size:30px; font-weight:800; line-height:1.15; margin:8px 0 2px; }
.ol-sub { color: var(--tx2); font-size:14.5px; }
.ol-bars { margin:12px 0 8px; }
.ol-row { display:grid; grid-template-columns: 92px 1fr 92px; gap:8px; align-items:center; font-size:13.5px; margin:5px 0; }
.ol-row .lab { font: 700 11.5px var(--mono); letter-spacing:.08em; color: var(--tx3); }
.ol-row .v { text-align:right; font-family: var(--mono); font-size:13px; }
.ol-track { position:relative; height:14px; background: rgba(255,255,255,.04); border-radius:7px; }
.ol-bar { position:absolute; left:0; top:2px; bottom:2px; border-radius:6px; }
.ol-rng { position:absolute; top:5px; height:4px; border-radius:2px; opacity:.55; }
.ol-dot { position:absolute; top:0; width:3px; height:14px; border-radius:2px; background:#fff; }
.ol-odds { display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin:10px 0; }
.ol-odds div { background: rgba(255,255,255,.03); border:1px solid var(--line); border-radius:10px; padding:8px 10px; }
.ol-odds b { display:block; font-size:22px; }
.ol-odds span { font-size:12.5px; color: var(--tx2); }
.ol-h { font: 800 12px var(--mono); letter-spacing:.16em; color: var(--tx3); margin:12px 0 4px; }
.ol ul { margin:4px 0 0; padding-left:18px; } .ol li { margin:4px 0; font-size:14.5px; line-height:1.5; }
.ol-do { background: rgba(79,209,224,.05); border:1px solid rgba(79,209,224,.3); border-radius:12px; padding:12px 16px; }
.ol-do .ol-h { color: var(--teal); margin-top:0; }
.ol-foot { font-size:13px; color: var(--tx3); line-height:1.55; }
.ol-none { background: rgba(226,140,193,.06); border:1px dashed #E28CC1; border-radius:12px; padding:14px 16px; }
`;

/** What our analysis says about each war for 2027 (drivers) and what to watch. Facts come from facts.json. */
function caseNotes(name: string, F: any, s: any): { drivers: string[]; watch: string[] } {
  const ind = F.india, mil = F.military, top = (s?.top || []).map((t: any) => `${t.name} ${Math.round(t.p * 100)}%`).join(", ");
  switch (name) {
    case "Afghanistan–Pakistan": return {
      drivers: [`Interstate Afghan–Pakistani fighting since Oct 2025; 2026 to September already above all of 2025.`,
        `Hotspots for next month: ${top}. Our October forecast is ${s ? `+${s.trend_pct}%` : "rising"} against the last six months.`,
        `A Pakistan Army committed in the west raises the risk of diversion along the LoC.`],
      watch: [`The autumn peak: in our data Af–Pak deaths run about 20–25% above normal in September–October and are lowest in December.`, `Any terror attack in India with ≥ 15 deaths: since 2016 state fighting followed in 11–15 days (3 of 4 cases).`, `Pakistan moving forces between its western front and the LoC.`] };
    case "US–Iran": return {
      drivers: [`The war peaked in March 2026 and has fallen to tens of deaths a month, but it reached ${ind.usir_countries[1]} countries this year (${ind.usir_countries[0]} last year), ${ind.gulf_states} of them Gulf states.`,
        `${ind.srilanka.deaths} killed in one strike off Sri Lanka (${new Date(ind.srilanka.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}); ${fmt(ind.hormuz_deaths)} deaths around Hormuz.`,
        `A quiet month is not a closed war: deliberate wars restart by decision, which casualty data cannot see.`],
      watch: [`Military-posture news between the US and Iran: in 2026 it warned 9 days before the strikes.`, `Hormozgan and the Strait of Hormuz (top area ${s?.top?.[0] ? Math.round(s.top[0].p * 100) + "%" : ""}); shipping attacks.`, `Brent: the 2026 onset moved it +55% in 20 trading days, after our warning.`] };
    case "Russia–Ukraine": return {
      drivers: [`Steady at about ${fmt(Math.round((F.scorecard.find((x: any) => x.name === name)?.last6) || 0))} deaths a month; the October forecast is ${s ? `+${s.trend_pct}%` : "flat"}.`,
        `The front is widening, not moving: Donetsk's share of fighting fell from ${mil.donetsk[0]}% to ${mil.donetsk[1]}%; ${fmt(mil.russia_inside_peak.deaths)} killed inside Russia in ${mil.russia_inside_peak.year}.`,
        `History says wars this large often shrink within a year, but this one has held its level for three years.`],
      watch: [`New oblasts entering the fighting (${top}).`, `Ceasefire talks: the main reason the range runs down to near zero.`, `Energy and fertiliser prices that reach India.`] };
    case "Israel–Hamas": return {
      drivers: [`Down to about a hundred deaths a month after 2023–24; rated GREEN, trend ${s ? `${s.trend_pct}%` : "flat"}.`, `Areas to watch: ${top}.`],
      watch: [`A collapse of the truce in Gaza or a new front in the West Bank.`, `Spill-over into the Gulf or the Red Sea.`] };
  }
  return { drivers: [], watch: [] };
}

const THEATRE_DO: Record<string, { title: string; items: string[] }> = {
  WTC: { title: "What it means for the Western theatre in 2027", items: [
    "Keep the Af–Pak front as a standing indicator for the LoC; review posture when Af–Pak is AMBER or RED.",
    "Hold ISR on Kandahar, Balochistan and Kunar; refresh the district watch-list monthly.",
    "Key readiness and notice-to-move timings to the 15-day clock after any qualifying attack."] },
  MTC: { title: "What it means for the Maritime theatre in 2027", items: [
    "Plan for a restart, not an end: keep Gulf evacuation plans current for ~9 M Indians [domain].",
    "Watch Hormuz and the sea lanes; act on a posture alert the same day (Warning Order).",
    "On a posture alert, flag MoPNG and RBI: reserves, crude hedging, shipping cover."] },
  NTC: { title: "What it means for the Northern theatre in 2027", items: [
    "No numeric outlook: the issued data hold no fatal LAC events (the India–China dyad has no recorded death since 1975).",
    "Galwan showed fatality data cannot warn of a first clash: add non-fatal indicators (face-offs, build-ups, infrastructure, patrol clashes).",
    "Context only: Af–Pak (two-front Pakistan) and Russia–Ukraine (China–Russia alignment, energy)."] },
  CDS: { title: "What it means for all theatres in 2027", items: [
    "Main effort stays West and sea: Af–Pak is the rising front for India, US–Iran the restart risk with the widest reach.",
    "Russia–Ukraine remains the largest war (RED) and an energy and fertiliser risk, not a direct threat.",
    "Adopt the monthly watch-list and RAG in the HQ IDS brief; add non-fatal LAC and LoC indicators in the first half of 2027."] },
};

export function outlookHTML(D: Data, role: string): string {
  const O = (D as any).outlook, X = D.theatre, F = D.facts;
  if (!O) return `<p class="muted">2027 outlook not built. Run <code>python scripts/outlook_2027.py</code>.</p>`;
  if (!document.getElementById("ol-css")) document.head.insertAdjacentHTML("beforeend", `<style id="ol-css">${CSS}</style>`);
  const T = X?.theatres?.[role];
  const names: string[] = role === "NTC" ? [] : T ? [...T.cases, ...T.context] : Object.keys(O.cases);
  const ctxNames: string[] = role === "NTC" ? T.context : [];
  const sc = (n: string) => F.scorecard.find((x: any) => x.name === n);
  const card = (n: string, ctx: boolean) => {
    const c = O.cases[n]; if (!c) return "";
    const s = sc(n), y = c.y2027, now = c.rating_now, lv = c.level2027;
    const max = Math.max(c.cal2025, c.last12, y.p90, 1);
    const bar = (lab: string, v: number, col: string, rng?: [number, number]) => `<div class="ol-row"><span class="lab">${lab}</span>
      <div class="ol-track">${rng ? `<div class="ol-rng" style="left:${(rng[0] / max) * 100}%;width:${Math.max(((rng[1] - rng[0]) / max) * 100, 0.6)}%;background:${col}"></div><div class="ol-dot" style="left:calc(${(v / max) * 100}% - 1px)"></div>`
        : `<div class="ol-bar" style="width:${Math.max((v / max) * 100, 0.6)}%;background:${col}"></div>`}</div><span class="v">${fmt(v)}</span></div>`;
    const N = caseNotes(n, F, s);
    return `<div class="ol-card">
      <h4><span>${esc(n)}${ctx ? ` <span class="muted small">· context</span>` : ""}</span>
        <span class="ol-lv" title="2027 level from the middle case">NOW <b style="background:${RAG_COLOR[now] ?? "#888"}">${now ?? "-"}</b> → 2027 <b style="background:${RAG_COLOR[lv]}">${lv}</b></span></h4>
      <div class="ol-big">≈ ${fmt(y.p50)} <span style="font-size:15px;font-weight:600;color:var(--tx2)">deaths in 2027 (middle case)</span></div>
      <div class="ol-sub">80% range ${fmt(y.p10)} – ${fmt(y.p90)} · about ${fmt(c.month2027_p50)} a month</div>
      <div class="ol-bars">
        ${bar("2025", c.cal2025, "rgba(159,178,198,.55)")}
        ${bar("LAST 12 MO", c.last12, "rgba(159,178,198,.85)")}
        ${bar("2027", y.p50, RAG_COLOR[lv], [y.p10, y.p90])}
      </div>
      <div class="ol-odds">
        <div><b style="color:var(--red)">${pc(c.p_up)}</b><span>rises by half or more</span></div>
        <div><b style="color:var(--green)">${pc(c.p_down)}</b><span>halves or less</span></div>
        <div><b style="color:var(--teal)">${pc(c.p_quiet)}</b><span>goes near-quiet</span></div>
      </div>
      <div class="ol-sub" style="font-size:13px">Basis: ${c.n_cases} similar conflicts (${esc(c.basis)}); recent level ${fmt(c.recent_month)} a month, momentum from our October forecast (${c.momentum_class}).</div>
      ${N.drivers.length ? `<div class="ol-h">FROM OUR ANALYSIS</div><ul>${N.drivers.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>` : ""}
      ${N.watch.length ? `<div class="ol-h">WATCH IN 2027</div><ul>${N.watch.map((d) => `<li>${esc(d)}</li>`).join("")}</ul>` : ""}
    </div>`;
  };
  const Dd = THEATRE_DO[role] ?? THEATRE_DO.CDS;
  return `<div class="ol">
    <div class="ol-top"><span class="ol-tag">2027 OUTLOOK</span><span class="ol-tag r">SCENARIO RANGE · NOT A VALIDATED FORECAST</span>
      <span class="muted small mono">${esc(T ? T.name : "All theatres")} · window ${esc(O.meta.window)}</span></div>
    ${role === "NTC" ? `<div class="ol-none"><b>No 2027 numbers for the Northern theatre.</b> The issued data contain no fatal LAC events, so there is nothing to project from; the theatre's drill on this site is synthetic. Context wars are shown below.</div>` : ""}
    <div class="ol-cards">${names.map((n) => card(n, !!T && T.context.includes(n))).join("")}${ctxNames.map((n) => card(n, true)).join("")}</div>
    <div class="ol-do"><div class="ol-h">${esc(Dd.title.toUpperCase())}</div><ul>${Dd.items.map((d) => `<li>${esc(d)}</li>`).join("")}</ul></div>
    <div class="ol-foot"><b>How these numbers were made.</b> For each war we took its recent level (average of the last six months to Sep 2026) and its momentum (our October forecast against that level), then looked up what happened next to every conflict in the world file (117 countries, 1989–2025) that stood at the same level with the same momentum: their deaths over months +4 to +15, i.e. the calendar-2027 window seen from September. The middle case is the median of those outcomes; the range covers 80% of them. Checked out of time (built on 1989–2009, scored on 2010–2024), the 80% range held ${pc(O.meta.oot_coverage)} of outcomes. Our monthly models were tested only 1–3 months ahead, so this is a planning range, not a forecast; a decision to strike, a ceasefire or a new war can move it, which is what the monthly watch-list and the daily news tripwire are for. Level 2027 uses the middle case: RED ≥ 1,000 a month, AMBER ≥ 100 (or ≥ 30% chance of rising by half), else GREEN.</div>
  </div>`;
}

export function openOutlookModal(D: Data, role: string) {
  document.getElementById("ol-modal")?.remove();
  const m = document.createElement("div");
  m.id = "ol-modal"; m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true"); m.setAttribute("aria-label", "2027 outlook");
  m.style.cssText = "position:fixed;inset:0;z-index:80;background:rgba(5,11,18,.97);backdrop-filter:blur(6px);overflow:auto;padding:28px 3vw";
  const T = D.theatre?.theatres?.[role];
  m.innerHTML = `<div style="max-width:1320px;margin:0 auto"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="eyebrow" style="margin:0">${esc((T ? T.name : "All theatres").toUpperCase())} · 2027 OUTLOOK</div>
      <button class="btn" id="ol-x" aria-label="Close">✕ CLOSE</button></div>${outlookHTML(D, role)}</div>`;
  document.body.appendChild(m);
  const close = () => { m.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey);
  (m.querySelector("#ol-x") as HTMLElement).addEventListener("click", close);
  m.addEventListener("click", (e) => { if (e.target === m) close(); });
}
