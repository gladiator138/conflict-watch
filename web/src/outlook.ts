// 2027 outlook, visual: an animated map of India's theatre zones with the wars' impact lines, and for each war a short
// chain "war → what it does to them → what it means for India → what India should do". Levels come from
// web/public/data/outlook2027.json (analogue scenario range, scripts/outlook_2027.py); the chains are our analysis.
import { type Data, RAG_COLOR } from "./data";
import { regionMap } from "./maps";

const esc = (s: any) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
const k = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n));

const CSS = `
.o7 { display:grid; grid-template-columns: minmax(0,1.2fr) minmax(0,1fr); gap:18px; align-items:start; }
@media (max-width: 1100px) { .o7 { grid-template-columns: 1fr; } }
.o7-map { position:relative; height: clamp(420px, 78vh, 720px); background: var(--panel); border:1px solid var(--line); border-radius:14px; overflow:hidden; }
.o7-map .arc { fill:none; stroke-width:2.6; stroke-dasharray: 9 7; animation: o7dash 1.6s linear infinite; }
.o7-map .arc-bg { fill:none; stroke-width:9; }
.o7-map .lbl { font: 700 12px var(--mono); letter-spacing:.08em; paint-order: stroke; stroke:#05070A; stroke-width:4px; }
.o7-map .zl { font: 800 13px var(--mono); letter-spacing:.14em; paint-order: stroke; stroke:#05070A; stroke-width:4px; }
@keyframes o7dash { to { stroke-dashoffset: -32; } }
.o7-leg { position:absolute; left:14px; bottom:12px; display:flex; gap:12px; flex-wrap:wrap; font: 700 11px var(--mono); letter-spacing:.08em; color: var(--tx2); }
.o7-leg i { display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:5px; vertical-align:-2px; }
.o7-tag { position:absolute; left:14px; top:12px; font: 800 11px var(--mono); letter-spacing:.14em; color: var(--amber); }
.o7-chains { display:flex; flex-direction:column; gap:12px; }
.o7-ch { background: var(--panel); border:1px solid var(--line); border-left:4px solid var(--c); border-radius:12px; padding:12px 14px; opacity:0; transform: translateY(8px); animation: o7in .5s ease forwards; }
.o7-ch h4 { margin:0 0 10px; display:flex; align-items:center; gap:10px; font-size:17px; flex-wrap:wrap; }
.o7-ch h4 .lv { font: 800 11px var(--mono); letter-spacing:.1em; color: var(--tx3); display:flex; gap:6px; align-items:center; }
.o7-ch h4 .lv b { padding:2px 7px; border-radius:5px; color:#05070A; }
.o7-ch h4 .n { margin-left:auto; font: 700 12px var(--mono); color: var(--tx3); }
.o7-steps { display:grid; grid-template-columns: 1fr 22px 1fr 22px 1fr; align-items:stretch; }
.o7-st { border-radius:10px; padding:8px 10px; background: rgba(255,255,255,.035); opacity:0; animation: o7in .45s ease forwards; }
.o7-st .h { font: 800 10.5px var(--mono); letter-spacing:.14em; margin-bottom:5px; }
.o7-st ul { margin:0; padding:0; list-style:none; } .o7-st li { font-size:13.5px; line-height:1.35; margin:3px 0; }
.o7-st li::before { content:"▸ "; color: var(--tx3); }
.o7-st.them .h { color:#F2B33D; } .o7-st.ind .h { color:#4FD1E0; } .o7-st.do { background: rgba(53,194,166,.08); border:1px solid rgba(53,194,166,.35); } .o7-st.do .h { color:#35C2A6; }
.o7-ar { display:flex; align-items:center; justify-content:center; color: var(--tx3); font-size:18px; }
.o7-ar span { display:inline-block; animation: o7nudge 1.4s ease-in-out infinite; }
@keyframes o7nudge { 0%,100% { transform: translateX(-2px); opacity:.5 } 50% { transform: translateX(3px); opacity:1 } }
@keyframes o7in { to { opacity:1; transform:none; } }
@media (max-width: 700px) { .o7-steps { grid-template-columns: 1fr; } .o7-ar { height:18px; } .o7-ar span { animation:none; transform: rotate(90deg); } }
.o7-india { background: linear-gradient(135deg, rgba(79,209,224,.10), rgba(53,194,166,.06)); border:1px solid rgba(79,209,224,.45); border-radius:12px; padding:12px 16px; opacity:0; animation: o7in .5s ease forwards; }
.o7-india .h { font: 800 12px var(--mono); letter-spacing:.16em; color: var(--teal); margin-bottom:8px; }
.o7-india .row { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr)); gap:8px; }
.o7-india .row div { background: rgba(5,11,18,.5); border:1px solid var(--line); border-radius:10px; padding:8px 10px; font-size:13.5px; line-height:1.35; }
.o7-india .row div b { display:block; font-size:15px; margin-bottom:2px; }
.o7-gap { border:1px dashed #E28CC1; background: rgba(226,140,193,.06); border-radius:12px; padding:10px 14px; font-size:14px; }
.o7-per { display:flex; gap:6px; flex-wrap:wrap; }
.o7-per button { font: 800 12px var(--mono); letter-spacing:.12em; padding:8px 14px; border-radius:999px; border:1px solid var(--line2); background: var(--panel); color: var(--tx2); cursor:pointer; }
.o7-per button.on { background: var(--teal); color:#05070A; border-color: var(--teal); }
.o7-so { border-radius:14px; padding:14px 18px; background: linear-gradient(120deg, rgba(242,179,61,.16), rgba(255,107,107,.10)); border:1px solid rgba(242,179,61,.55); opacity:0; animation: o7in .5s ease .1s forwards; }
.o7-so .h { font: 800 12px var(--mono); letter-spacing:.2em; color: var(--amber); margin-bottom:4px; }
.o7-so { border-color: var(--sc); background: linear-gradient(120deg, color-mix(in srgb, var(--sc) 18%, transparent), rgba(5,11,18,.2)); }
.o7-so .t { font-size: clamp(20px, 1.6vw, 26px); font-weight:800; line-height:1.3; }
.o7-so .t .c, .o7-so .s .c { font-size:.72em; font-weight:600; color: var(--tx2); }
.o7-so .s { font-size: 16px; line-height:1.45; color: var(--tx); margin-top:6px; }
.o7-so .s b { font-weight:800; }
.o7-map svg.map { animation: o7zoom 1s cubic-bezier(.2,.8,.2,1) both; transform-origin: 60% 55%; }
@keyframes o7zoom { from { transform: scale(1.12); opacity:.25; filter: blur(3px); } to { transform: none; opacity:1; filter:none; } }
.o7-map .breath { animation: o7fade .8s ease both, o7breath 2.6s ease-in-out .8s infinite; }
@keyframes o7breath { 0%,100% { fill-opacity: var(--fo); } 50% { fill-opacity: calc(var(--fo) * 1.9); } }
.o7-ch h4 .n { margin-left:auto; text-align:right; font: 700 12px var(--mono); color: var(--tx3); }
.o7-ch h4 .n b { display:block; font: 800 30px var(--sans); line-height:1; color: var(--lvc); letter-spacing:-.01em; }
.o7-ch h4 .lv b { font-size:13px; padding:3px 9px; }
.o7-st.ind { background: rgba(79,209,224,.10); border:1px solid rgba(79,209,224,.45); }
.o7-st.ind li { font-size:15px; font-weight:600; }
.o7-st.them li { color: var(--tx2); }
.o7-map .stamp { font: 900 64px var(--sans); letter-spacing:-.02em; fill: #fff; fill-opacity:.07; }
.o7-map .draw { animation: o7draw 1.1s ease-out both, o7dash 1.6s linear 1.1s infinite; }
@keyframes o7draw { from { stroke-dasharray: 1400; stroke-dashoffset: 1400; } to { stroke-dasharray: 1400; stroke-dashoffset: 0; } }
.o7-map .pop { transform-box: fill-box; transform-origin: center; animation: o7pop .7s cubic-bezier(.2,1.6,.4,1) both; }
@keyframes o7pop { from { transform: scale(0); opacity:0 } to { transform: scale(1); opacity:1 } }
.o7-map .fade { opacity:0; animation: o7fade .6s ease forwards; }
@keyframes o7fade { to { opacity:1 } }
.o7-map .halo { transform-box: fill-box; transform-origin:center; animation: o7halo 2.2s ease-out infinite; }
@keyframes o7halo { 0% { transform: scale(.6); opacity:.7 } 100% { transform: scale(2.4); opacity:0 } }
.o7-map .zone { animation: o7fade .8s ease both; }
.o7-foot { grid-column: 1 / -1; font-size:12.5px; color: var(--tx3); }
`;

type Chain = { lab: [number, number, "start" | "end"]; war: string; short: string; c: string; at: [number, number]; to: [number, number]; via: string; themLabel: string; them: string[]; ind: string[]; act: string[] };
// Facts from our data (deaths, spread, prices, Donetsk share) and our judgement (worded as risk / watch).
const CHAINS: Record<string, Chain> = {
  "Afghanistan–Pakistan": { lab: [-14, -10, "end"], war: "Afghanistan–Pakistan", short: "Af–Pak", c: "#F2B33D", at: [66.5, 31.2], to: [74.6, 34.1], via: "LoC diversion",
    themLabel: "ON PAKISTAN", them: ["Army fighting on its western front", "411 killed in Mar 2026", "Kandahar · Balochistan · Kunar hot"],
    ind: ["LoC diversion risk", "Attack → state fighting in ~15 days (since 2016)", "Afghan evacuation"],
    act: ["Watch the LoC when Af–Pak is AMBER/RED", "ISR on the top-3 districts", "Readiness keyed to the 15-day clock"] },
  "US–Iran": { lab: [-14, 18, "end"], war: "US–Iran", short: "US–Iran", c: "#FF6B6B", at: [56.3, 27.0], to: [72.9, 19.0], via: "oil · diaspora · sea lanes",
    themLabel: "ON THE US & GULF", them: ["War reached 14 countries (4 in 2025)", "Brent +55% in 20 trading days", "US forces held in the Gulf"],
    ind: ["Oil bill ≈ +$52 B a year (est.)", "~9 M Indians in the Gulf", "Hormuz & Chabahar route at risk"],
    act: ["On a posture alert: top up reserves, hedge", "Keep Gulf evacuation plans live", "Watch Hormuz sea lanes"] },
  "Russia–Ukraine": { lab: [14, 4, "start"], war: "Russia–Ukraine", short: "RU–UA", c: "#A794FF", at: [35.5, 48.5], to: [77.2, 28.6], via: "energy · fertiliser · spares",
    themLabel: "ON RUSSIA & EUROPE", them: ["Front widening (Donetsk 55% → 30%)", "War reaches inside Russia", "Sanctions & energy shock"],
    ind: ["Energy & fertiliser prices", "Defence spares supply", "Russia–China closeness (LAC)"],
    act: ["Diversify energy & fertiliser", "Stock critical spares", "Watch Russia–China on the LAC"] },
  "Israel–Hamas": { lab: [8, 24, "start"], war: "Israel–Hamas", short: "IL–H", c: "#3DD68C", at: [34.4, 31.4], to: [76.3, 9.9], via: "Red Sea trade",
    themLabel: "ON ISRAEL & REGION", them: ["Cooled to ~100 deaths a month", "Gaza & West Bank still watched", "Red Sea / Houthi risk"],
    ind: ["Red Sea trade route", "Indians in Israel & the Gulf", "India–Middle East corridor on hold"],
    act: ["Naval presence: Red Sea & Arabian Sea", "Evacuation plan ready (Op Ajay model)"] },
};
const ROLE_WARS: Record<string, string[]> = { WTC: ["Afghanistan–Pakistan"], MTC: ["US–Iran", "Israel–Hamas"], NTC: ["Russia–Ukraine", "Afghanistan–Pakistan"], CDS: ["US–Iran", "Afghanistan–Pakistan", "Russia–Ukraine", "Israel–Hamas"] };
const ZONE: Record<string, { lv: string; why: string; at: [number, number] }> = { WTC: { lv: "AMBER", why: "Af–Pak rising", at: [71.6, 28.6] }, MTC: { lv: "AMBER", why: "restart risk · oil", at: [67, 9] }, NTC: { lv: "DATA GAP", why: "1 fatal clash since 1975", at: [87, 33.5] } };
const PRI: Record<string, { h: string; items: string[][] }> = {
  WTC: { h: "WESTERN THEATRE · 2027 PRIORITIES", items: [["LoC first", "Raise LoC watch whenever Af–Pak is AMBER/RED."], ["Eyes on 3 districts", "Kandahar, Balochistan, Kunar."], ["15-day clock", "Pre-set readiness after any qualifying attack."]] },
  MTC: { h: "MARITIME THEATRE · 2027 PRIORITIES", items: [["Sea lanes", "Hormuz, Arabian Sea, Red Sea under watch."], ["NEO ready", "~9 M Indians in the Gulf."], ["Same-day action", "Posture alert → Warning Order."]] },
  NTC: { h: "NORTHERN THEATRE · 2027 PRIORITIES", items: [["Close the data gap", "Face-offs, build-ups, infrastructure, patrol clashes."], ["Watch the partners", "Russia–China closeness; Pakistan on two fronts."], ["Drill the flow", "FLASH drill on synthetic data until real indicators exist."]] },
  CDS: { h: "INDIA LEVEL (CDS) · 2027 PRIORITIES", items: [["Main effort: West & sea", "Af–Pak the rising front; US–Iran the restart risk with the widest reach."], ["Energy shield", "Reserves, crude hedging, rupee readiness on a posture alert."], ["Evacuation ready", "Gulf & Afghanistan plans live; 6 of 7 past evacuations were on our list."], ["Close the LAC gap", "Add non-fatal LAC & LoC indicators in H1 2027."], ["One monthly picture", "Watch-list & RAG in the HQ IDS brief; tripwire daily."]] },
};
const BOX: [[number, number], [number, number]] = [[28, 2], [98, 51]];

// ── What-if scenario levers (Ops Console). They change only the scenario shown, never the data: each lever scales a
// war's 2027 range (or moves US–Iran between its low, middle and high case), then the same RAG rule as the data file
// is re-applied (monthly middle case ≥ 1000 RED, ≥ 100 AMBER; GREEN turns AMBER if the chance of a surge ≥ 30%).
type Sim = { afpak: number; ruua: number; ilh: number; iran: number | null; oil: number; attack: boolean };
const SIM0: Sim = { afpak: 0, ruua: 0, ilh: 0, iran: null, oil: 55, attack: false };
const SIM: Sim = { ...SIM0 };
const isBase = () => JSON.stringify(SIM) === JSON.stringify(SIM0);
const LEVERS: Record<string, (keyof Sim)[]> = { WTC: ["afpak", "attack"], MTC: ["iran", "ilh", "oil"], NTC: ["ruua", "afpak"], CDS: ["afpak", "iran", "ruua", "ilh", "oil", "attack"] };
const MULT: Record<string, keyof Sim> = { "Afghanistan–Pakistan": "afpak", "Russia–Ukraine": "ruua", "Israel–Hamas": "ilh" };
// Rating: the data file's rule (monthly middle case ≥ 1000 RED, ≥ 100 AMBER; ≥ 30% chance of a surge → AMBER) plus the
// deck's escalation test: RED once a surge (deaths ≥ 1.5× today's pace) is more likely than not (≥ 50%).
// The chance of a surge comes from a lognormal fitted to each range (p50, p90); the surge line is calibrated so that at
// baseline the fit returns the data file's own p_up exactly, so baseline ratings are unchanged.
const rag = (monthly: number, pu: number) => (monthly >= 1000 || pu >= 0.5 ? "RED" : monthly >= 100 || pu >= 0.3 ? "AMBER" : "GREEN");
const Phi = (x: number) => { const t = 1 / (1 + 0.2316419 * Math.abs(x)), d = 0.3989423 * Math.exp((-x * x) / 2), p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))); return x > 0 ? 1 - p : p; };
const PhiInv = (p: number) => { let lo = -8, hi = 8; for (let i = 0; i < 60; i++) { const m = (lo + hi) / 2; if (Phi(m) < p) lo = m; else hi = m; } return (lo + hi) / 2; };
const RANK: Record<string, number> = { GREEN: 0, AMBER: 1, RED: 2 };
const worst = (ls: string[]) => ls.reduce((a, b) => (RANK[b] > RANK[a] ? b : a), "GREEN");
const oilBill = () => Math.round((52 * SIM.oil) / 55);
const PRESETS: Record<string, Partial<Sim>> = {
  "BASELINE": {},
  "CALM 2027": { afpak: -60, ruua: -80, ilh: -50, iran: 3, oil: 10 },
  "WEST HEATS UP": { afpak: 120, attack: true },
  "GULF RESTART": { iran: 70, oil: 110, ilh: 100 },
  "WORST CASE": { afpak: 150, ruua: 60, ilh: 200, iran: 85, oil: 140, attack: true },
};

// Tiered text: what each war means at GREEN / AMBER / RED. The baseline tier keeps the analysis text in CHAINS; a lever
// that pushes a war into another tier swaps in that tier's chain. "{bill}" is filled with the live oil-bill estimate.
type Tier = { them: string[]; ind: string[]; act: string[]; so: string };
const TIER: Record<string, Partial<Record<string, Tier>>> = {
  "Afghanistan–Pakistan": {
    AMBER: { them: ["Army fighting on its western front", "Hundreds killed a month", "Kandahar · Balochistan · Kunar hot"],
      ind: ["LoC diversion risk", "Attack → state fighting in ~15 days (since 2016)", "Afghan evacuation"],
      act: ["Watch the LoC while Af–Pak is AMBER", "ISR on the top-3 districts", "Readiness keyed to the 15-day clock"],
      so: "Af–Pak at AMBER: watch the LoC and keep the 15-day clock set." },
    GREEN: { them: ["Western front quietens", "Pakistan Army freed from the west", "Fewer cross-border strikes"],
      ind: ["Two-front pressure on Pakistan eases", "LoC: troops can shift back east", "Afghan evacuation risk low"],
      act: ["Track Pakistani units moving east", "Routine LoC watch", "ISR back to normal tasking"],
      so: "Af–Pak calming: Pakistan's western pull weakens, so watch for forces returning to the LoC." },
    RED: { them: ["Major war on Pakistan's western front", "Refugee flow into KP & Balochistan", "Army stretched on two fronts"],
      ind: ["High LoC spill-over & diversion risk", "15-day clock: an attack escalates fast", "Indians in Afghanistan exposed"],
      act: ["Raise LoC readiness now", "Warning Order to WTC; ISR surge on hot districts", "Kabul evacuation plan to READY"],
      so: "Af–Pak at war: the LoC is the risk point. Readiness now, ISR surge, evacuation ready." },
  },
  "US–Iran": {
    AMBER: { them: ["Restart risk rising: posture moves in the Gulf", "Tanker insurance and freight up", "US & Iran trading threats"],
      ind: ["Oil bill ≈ +${bill} B a year (est.)", "~9 M Indians in the Gulf: plans to READY", "Hormuz & Chabahar route at risk"],
      act: ["Watch the posture-news tripwire daily", "Gulf NEO plan to READY", "Top up reserves; hedge crude"],
      so: "Gulf restart risk rising: move from watch to ready." },
    GREEN: { them: ["Ceasefire holding", "Gulf shipping normal", "US forces drawing down"],
      ind: ["Oil bill ≈ +${bill} B a year (est.)", "Diaspora safe; remittances steady", "Chabahar work can resume"],
      act: ["Rebuild crude reserves while prices allow", "Keep the posture-news tripwire on", "Routine Gulf NEO planning"],
      so: "Gulf quiet: rebuild reserves and keep the tripwire on; a restart comes by decision, not by build-up." },
    RED: { them: ["War restarted: strikes across the Gulf", "Hormuz traffic under threat", "Brent spikes on every strike"],
      ind: ["Oil bill ≈ +${bill} B a year (est.)", "~9 M Indians inside the strike envelope", "Hormuz & Red Sea shipping disrupted"],
      act: ["Gulf NEO: Warning Order → execute", "Navy escorts for tankers (Op Sankalp model)", "Release reserves; RBI ready on the rupee"],
      so: "Gulf war restarts: evacuation, tanker escort and the energy shield all at once." },
  },
  "Russia–Ukraine": {
    RED: { them: ["Front widening (Donetsk 55% → 30%)", "War reaches inside Russia", "Sanctions & energy shock"],
      ind: ["Energy & fertiliser prices", "Defence spares supply", "Russia–China closeness (LAC)"],
      act: ["Diversify energy & fertiliser", "Stock critical spares", "Watch Russia–China on the LAC"],
      so: "Russia–Ukraine stays at war: energy and spares stay dear." },
    "RED+": { them: ["Escalation: front widening fast", "Strikes deep inside Russia; NATO tension up", "Energy & grain shock"],
      ind: ["Energy & fertiliser prices spike", "Defence spares disrupted", "Russia leans harder on China (LAC)"],
      act: ["Switch to alternate energy & fertiliser suppliers", "Draw on spares reserve; alternate vendors", "Raise watch on Russia–China along the LAC"],
      so: "Russia–Ukraine escalating: an energy, fertiliser and spares shock for India." },
    GREEN: { them: ["Ceasefire / frozen front", "Sanctions talks open", "Energy prices ease"],
      ind: ["Cheaper energy & fertiliser", "Defence spares flow steadier", "Russia less tied to China"],
      act: ["Lock in long-term energy contracts", "Restock critical spares", "Re-open the INSTC trade route"],
      so: "Russia–Ukraine ceasefire: an energy and spares window for India." },
    AMBER: { them: ["Fighting winding down", "Front stabilising", "Sanctions stay in place"],
      ind: ["Energy still elevated", "Spares supply uncertain", "Russia–China ties hold (LAC)"],
      act: ["Keep energy & fertiliser diversified", "Hold spares stock", "Watch Russia–China on the LAC"],
      so: "Russia–Ukraine easing but not over: keep diversifying energy and spares." },
  },
  "Israel–Hamas": {
    GREEN: { them: ["Cooled to ~100 deaths a month", "Gaza & West Bank still watched", "Red Sea / Houthi risk"],
      ind: ["Red Sea trade route", "Indians in Israel & the Gulf", "India–Middle East corridor on hold"],
      act: ["Naval presence: Red Sea & Arabian Sea", "Evacuation plan ready (Op Ajay model)"],
      so: "Israel–Hamas quiet: routine Red Sea watch." },
    AMBER: { them: ["Fighting flares in Gaza", "West Bank & Lebanon spill-over risk", "Houthi attacks resume"],
      ind: ["Red Sea freight costs rise", "Indians in Israel & the Gulf at risk", "India–Middle East corridor delayed"],
      act: ["Naval presence in the Red Sea", "Evacuation plan to READY (Op Ajay model)", "Watch the Houthi front"],
      so: "Israel–Hamas flaring: Red Sea and diaspora move up the list." },
    RED: { them: ["Major regional war", "Neighbours drawn in", "Red Sea shunned by shippers"],
      ind: ["Suez route cut: freight & oil up", "Indians in Israel need evacuation", "Trade & remittances hit"],
      act: ["Evacuate: Op Ajay model", "Escort merchant ships in the Red Sea", "Re-route trade via the Cape"],
      so: "Israel–Hamas at regional war: evacuate, escort shipping, re-route trade." },
  },
};
// Theatre priorities by the zone's level (baseline tier keeps PRI).
const PRI_T: Record<string, Partial<Record<string, string[][]>>> = {
  WTC: {
    GREEN: [["Steady watch", "Af–Pak quiet: routine LoC watch."], ["Track redeployment", "Pakistani forces returning east."], ["Keep the clock", "15-day readiness drill stays."]],
    RED: [["LoC readiness now", "Af–Pak at war or an attack in J&K: Warning Order today."], ["ISR surge", "Hot districts and LoC launch pads, daily."], ["15-day clock", "State fighting has followed within ~15 days since 2016: pre-set the response."]],
  },
  MTC: {
    GREEN: [["Sea lanes open", "Routine Hormuz & Red Sea watch."], ["Rebuild reserves", "Buy while prices are low."], ["Tripwire on", "Restarts come by decision; posture news first."]],
    RED: [["Escort & protect", "Tanker escort in Hormuz & the Red Sea (Op Sankalp model)."], ["NEO execute", "~9 M Indians in the Gulf: evacuation to execute."], ["Energy shield", "Release reserves, hedge crude, rupee readiness."]],
  },
};

export function mountOutlook(host: HTMLElement, D: Data, role: string, per = "2027") {
  const O = (D as any).outlook, X = D.theatre;
  if (!O) { host.innerHTML = `<p class="muted">2027 outlook not built.</p>`; return; }
  if (!document.getElementById("o7-css")) document.head.insertAdjacentHTML("beforeend", `<style id="o7-css">${CSS}${SIMCSS}</style>`);
  const wars = ROLE_WARS[role] ?? ROLE_WARS.CDS, P = PRI[role] ?? PRI.CDS;
  const PER = ["2027", "Q1", "Q2", "Q3", "Q4"];
  host.innerHTML = `<div class="o7">
    <div class="o7-left"><div class="o7-map"></div><div class="o7-sim"></div></div>
    <div class="o7-chains"></div>
    <div class="o7-foot">${esc(O.meta.footnote ?? "Level = middle case of a scenario range from history, for the whole year or each quarter of 2027: what happened next to similar conflicts in 117 countries, 1989–2025 (the range held 89% out of time). Not a validated forecast. Chains are our analysis.")} What-if levers are a scenario tool: they rescale our ranges and re-apply the same RAG rule; they are not a model run.</div></div>`;
  const box = host.querySelector(".o7-map") as HTMLElement, side = host.querySelector(".o7-chains") as HTMLElement, simEl = host.querySelector(".o7-sim") as HTMLElement;
  let first = true, prevZone: Record<string, string> = {}, prevLvl: Record<string, string> = {};

  // Base value of a war for the period, and the same value under the current levers.
  const base = (w: string, pp = per) => { const c = O.cases[w]; if (!c) return null; return pp === "2027" ? { ...c.y2027, level: c.level2027, p_up: c.p_up } : c.quarters?.[pp]; };
  const pv = (w: string, pp = per) => {
    const v = base(w, pp); if (!v) return null;
    const n = pp === "2027" ? 12 : 3; let { p10, p50, p90 } = v, pu = v.p_up ?? 0;
    const mk = MULT[w], sg = v.p50 > 0 && v.p90 > v.p50 ? Math.log(v.p90 / v.p50) / 1.2816 : 1;
    const T = v.p50 > 0 && pu > 0 && pu < 1 ? v.p50 * Math.exp(sg * PhiInv(1 - pu)) : 0; // surge line for this period
    if (mk) { const f = Math.max(0.001, 1 + (SIM[mk] as number) / 100); p10 *= f; p50 *= f; p90 *= f; if (T) pu = 1 - Phi((Math.log(T) - Math.log(p50)) / sg); }
    if (w === "US–Iran" && SIM.iran !== null) {
      const r = SIM.iran / 100, r0 = Math.max(0.01, pu);
      if (r >= r0) { const t = (r - r0) / Math.max(0.01, 1 - r0); p10 = p10 + t * (p50 - p10); p50 = p50 + t * (p90 - p50); p90 = Math.max(p90 * (1 + 0.5 * t), p50); }
      else { const t = r / r0; p90 = p50 + t * (p90 - p50); p50 = p10 + t * (p50 - p10); }
      pu = r;
    }
    const level = isBase() ? v.level : rag(p50 / n, pu);
    return { p10: Math.round(p10), p50: Math.round(p50), p90: Math.round(p90), level, p_up: pu, bpu: v.p_up ?? 0, b50: v.p50, blevel: v.level, surge: T, n };
  };
  const lvl = (w: string) => pv(w)?.level ?? "-";
  const tierOf = (w: string, v: any): Tier | undefined => {
    if (isBase() || !v) return undefined;
    if (v.level !== v.blevel) return TIER[w]?.[v.level];
    if (v.b50 && v.p50 >= 1.5 * v.b50) return TIER[w]?.[`${v.level}+`];
    return undefined;
  };
  const pvRaw = (w: string) => { const v = pv(w); return v ? rag(v.p50 / v.n, v.p_up) : "GREEN"; };
  const zone = (code: string) => {
    const z = ZONE[code]; if (!z) return null; if (isBase() || code === "NTC") return z;
    if (code === "WTC") { const l = SIM.attack ? "RED" : lvl("Afghanistan–Pakistan"); return { ...z, lv: l, why: SIM.attack ? "attack · 15-day clock running" : SIM.afpak > 0 ? "Af–Pak escalating" : SIM.afpak < 0 ? "Af–Pak easing" : z.why }; }
    if (code === "MTC") {
      const ir = SIM.iran ?? Math.round((O.cases["US–Iran"]?.p_up ?? 0.12) * 100);
      let l = worst([lvl("US–Iran"), lvl("Israel–Hamas")]);
      if (l === "GREEN" && (ir >= 10 || SIM.oil >= 30)) l = "AMBER"; // restart risk or oil shock keeps the sea at AMBER
      if (SIM.oil >= 100 && l === "AMBER") l = "RED";
      return { ...z, lv: l, why: ir >= 50 ? "Gulf war restarting" : SIM.oil >= 100 ? `oil shock +${SIM.oil}%` : l === "GREEN" ? "sea lanes quiet" : z.why };
    }
    return z;
  };

  const render = () => {
    const pl = per === "2027" ? "2027" : `${per} 2027`;
    const SEASON: Record<string, string> = { Q1: "Seasonal norm for Af–Pak.", Q2: "Af–Pak's quietest quarter in our data (June −11%).", Q3: "Af–Pak fighting season: September runs +26% in our data.", Q4: "October stays high (+22%); December is the year's low (−24%).", "2027": "Af–Pak peaks every September–October." };
    const prev = (w: string) => { const c = O.cases[w]; if (!c) return null; if (per === "2027") return c.last12; if (per === "Q1") return Math.round(c.recent_month * 3); return c.quarters?.[`Q${+per[1] - 1}`]?.p50; };
    const chg = (w: string) => { const v = pv(w), p0 = prev(w); if (!v || !p0) return ""; const d = (v.p50 - p0) / p0; return Math.abs(d) < 0.05 ? "about level" : `${d > 0 ? "▲ up" : "▼ down"} ${Math.round(Math.abs(d) * 100)}% on ${per === "2027" ? "the last 12 months" : per === "Q1" ? "today's pace" : `Q${+per[1] - 1}`}`; };
    const ln = (w: string, nm: string) => { const v = pv(w); return v ? `<b style="color:${RAG_COLOR[v.level]}">${nm} ${v.level}</b> ~${k(v.p50)} deaths <span class="c">(${chg(w)})</span>` : ""; };
    const bill = oilBill(), oilTxt = `≈ $${bill} B a year on oil (est., Brent +${SIM.oil}%)`;
    const clock = SIM.attack ? "<b style=\"color:" + RAG_COLOR.RED + "\">Qualifying attack: 15-day clock running.</b> " : "";
    const so = ({
      WTC: { t: `${clock}${ln("Afghanistan–Pakistan", "Af–Pak")} in ${pl}.`, s: `${SEASON[per]} For India: pressure on the LoC while Pakistan fights on two fronts; state fighting has followed a major attack within ~15 days since 2016.` },
      MTC: { t: `${ln("US–Iran", "US–Iran")} in ${pl}, up to ${k(pv("US–Iran")?.p90 ?? 0)} if it restarts.`, s: `${lvl("US–Iran") === "RED" ? "" : `A quiet ${per === "2027" ? "year" : "quarter"} is not a closed war. `}India's stake: ~9 M people in the Gulf, the Hormuz sea lanes and ${oilTxt}. Israel–Hamas: ${ln("Israel–Hamas", "")}.` },
      NTC: { t: `No LAC forecast for ${pl}: one fatal clash in 36 years (Galwan 2020).`, s: `The risk reaches the north through Pakistan (${ln("Afghanistan–Pakistan", "Af–Pak")}) and Russia–China (${ln("Russia–Ukraine", "RU–UA")}).` },
      CDS: { t: `${clock}${ln("Afghanistan–Pakistan", "Af–Pak")} on land · ${ln("US–Iran", "US–Iran")} at sea.`, s: `${ln("Russia–Ukraine", "RU–UA")} ${({ RED: "keeps energy dear", AMBER: "still keeps energy elevated", GREEN: "eases energy prices" } as Record<string, string>)[lvl("Russia–Ukraine")] ?? ""}; ${oilTxt}. ${SEASON[per]} ${isBase() ? "Main effort: West and sea." : ""}` },
    } as Record<string, { t: string; s: string }>)[role] ?? { t: "", s: "" };
    { const notes = [...wars].sort((x, y) => RANK[lvl(y)] - RANK[lvl(x)]).map((w) => { const v = pv(w); return v ? tierOf(w, v)?.so ?? "" : ""; }).filter(Boolean).slice(0, 2);
      if (notes.length) so.s = `<b>${notes.join(" ")}</b> ${so.s}`; }
    const lvls = wars.map((w) => pv(w)?.level ?? "GREEN").concat(SIM.attack && (role === "WTC" || role === "CDS") ? ["RED"] : []);
    const soCol = RAG_COLOR[worst(lvls)];
    const sc = isBase() ? "" : `<div class="o7-scn">⚗ SCENARIO · what-if levers moved · not a forecast <button class="o7-reset">RESET</button></div>`;
    const chain = (w: string, i: number) => {
      const C = CHAINS[w], c = O.cases[w], v = pv(w)!, d0 = first ? (per === "2027" ? 250 + i * 450 : 60 + i * 140) : 0;
      const TT = tierOf(w, v), src = TT ?? C;
      const fill = (x: string) => x.replace("{bill}", String(bill));
      // Bullets built from this period's numbers in our data (deaths, change, season, surge chance, peak quarter) plus the tier's analysis.
      const MON = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const q = per === "2027" ? null : c.quarters?.[per], sp = Math.round(v.p_up * 100), mo = Math.round(v.p50 / v.n);
      const QS = ["Q1", "Q2", "Q3", "Q4"], qv = QS.map((x) => pv(w, x)!), pk = QS[qv.reduce((bi, x, i) => (x.p50 > qv[bi].p50 ? i : bi), 0)];
      const pct = (x: number) => `${x > 0 ? "+" : ""}${x}%`, oneOff = (x: number) => (Math.abs(x) >= 100 ? ", one-off events" : "");
      const seas = q && q.peak_moy ? (q.peak_pct >= 10 ? `Strongest month ${MON[q.peak_moy]} (${pct(q.peak_pct)}${oneOff(q.peak_pct)})` : q.low_pct <= -10 ? `Seasonal low: ${MON[q.low_moy]} (${pct(q.low_pct)}${oneOff(q.low_pct)})` : `Seasonal norm (${MON[q.peak_moy]} ${pct(q.peak_pct)})`)
        : `Momentum ${c.momentum_class}; ${Math.round((c.p_down ?? 0) * 100)}% chance 2027 runs lower`;
      const them = [chg(w) ? `${chg(w).replace(/^(.)/, (m) => m.toUpperCase())}` : `~${k(mo)} deaths a month`, seas, src.them[0]];
      const qOil = per === "2027" ? `Oil bill ≈ +$${bill} B a year (est., Brent +${SIM.oil}%)` : `≈ +$${Math.round(bill / 4)} B on oil in ${pl} (est., Brent +${SIM.oil}%)`;
      const dline: Record<string, string> = {
        "US–Iran": `Restart / surge chance in ${pl}: ${sp}%`,
        "Afghanistan–Pakistan": `LoC watch: surge chance ${sp}% in ${pl}`,
        "Russia–Ukraine": `~${k(mo)} deaths a month in ${pl}: ${v.level === "RED" ? "energy stays dear" : v.level === "AMBER" ? "energy still elevated" : "energy prices ease"}`,
        "Israel–Hamas": `Red Sea risk: surge chance ${sp}% in ${pl}`,
      };
      const rest = src.ind.map(fill).filter((x) => !x.startsWith("Oil bill") && !/^LoC diversion|^Red Sea trade route$|^Energy & fertiliser prices$/.test(x));
      let ind = w === "US–Iran" ? [qOil, dline[w], rest[0]] : [dline[w], ...rest.slice(0, 2)];
      if (w === "Afghanistan–Pakistan" && SIM.attack) ind = ["15-day clock running: state fighting likely", ...ind.slice(0, 2)];
      const ready = v.level === "GREEN" ? "keep plans current" : v.level === "AMBER" ? "plans to READY" : "forces & plans at READY";
      const timing = per === "2027" ? `Peak quarter: ${pk} (~${k(qv[QS.indexOf(pk)].p50)} deaths) · plan for it`
        : per === pk ? `${pl} is the peak quarter for ${C.short}: ${ready}`
        : QS.indexOf(per) + 1 === QS.indexOf(pk) ? `Prepare in ${pl}: ${pk} is the peak quarter (~${k(qv[QS.indexOf(pk)].p50)})`
        : QS.indexOf(per) > QS.indexOf(pk) ? `Past the ${pk} peak (~${k(v.p50)} in ${per} vs ~${k(qv[QS.indexOf(pk)].p50)}): ${v.level === "GREEN" ? "draw down to routine" : "hold, then review"}`
        : `${per} ~${k(v.p50)}, below the ${pk} peak (~${k(qv[QS.indexOf(pk)].p50)}): ${ready}`;
      const pre = q && q.peak_pct >= 15 && q.peak_pct < 100 && w === "Afghanistan–Pakistan" ? [`Pre-position ISR before ${MON[q.peak_moy]} (${pct(q.peak_pct)})`] : [];
      const act = [timing, ...pre, ...src.act].slice(0, 3), chgC = TT ? " chg" : "", actH = v.level === "RED" && TT ? "INDIA SHOULD · NOW" : "INDIA SHOULD";
      const st = (cls: string, h: string, items: string[], d: number) => `<div class="o7-st ${cls}" style="animation-delay:${d}ms"><div class="h">${h}</div><ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
      const dv = v.b50 ? (v.p50 - v.b50) / Math.max(1, v.b50) : 0, moved = !isBase() && (Math.abs(dv) >= 0.01 || v.level !== v.blevel);
      const flip = prevLvl[w] && prevLvl[w] !== v.level ? " flip" : "";
      return `<div class="o7-ch${flip}" style="--c:${C.c};animation-delay:${d0}ms">
        <h4><span style="color:${C.c}">●</span>${esc(C.war)}
          <span class="lv">NOW <b style="background:${RAG_COLOR[c.rating_now] ?? "#888"}">${c.rating_now}</b> → ${pl} <b style="background:${RAG_COLOR[v.level]}">${v.level}</b>${moved && v.level !== v.blevel ? `<s style="opacity:.6">${v.blevel}</s>` : ""}</span>
          <span class="n" style="--lvc:${RAG_COLOR[v.level]}"><b>~${k(v.p50)}</b>deaths in ${pl} · range ${k(v.p10)}–${k(v.p90)}<span class="pg" title="Chance deaths reach 1.5× today's pace (a surge). 30% → AMBER, 50% → RED."><span class="pgb"><i style="width:${Math.round(v.p_up * 100)}%;background:${RAG_COLOR[rag(0, v.p_up)]}"></i><u style="left:30%"></u><u style="left:50%"></u></span>surge chance <b2>${Math.round(v.p_up * 100)}%</b2>${moved && Math.round(v.p_up * 100) !== Math.round(v.bpu * 100) ? ` <em2>(was ${Math.round(v.bpu * 100)}%)</em2>` : ""}</span>${moved ? `<em class="dv" style="color:${dv > 0 ? RAG_COLOR.RED : RAG_COLOR.GREEN}">${dv > 0 ? "▲" : "▼"} ${Math.abs(Math.round(dv * 100))}% vs baseline</em>` : ""}</span></h4>
        <div class="o7-steps${chgC}">${st("them", C.themLabel, them, d0 + 150)}<div class="o7-ar"><span>➜</span></div>${st("ind", "ON INDIA", ind, d0 + 300)}<div class="o7-ar"><span>➜</span></div>${st("do", actH, act, d0 + 450)}</div>${TT ? `<div class="o7-tnote" style="--tc:${RAG_COLOR[v.level]}">▸ ${esc(TT.so)}</div>` : ""}</div>`;
    };
    const zl = (c: string) => zone(c)?.lv ?? "AMBER";
    let baseItems = P.items;
    if (!isBase() && (role === "WTC" || role === "MTC")) baseItems = PRI_T[role]?.[zl(role)] ?? P.items;
    if (!isBase() && role === "CDS") {
      const w = zl("WTC"), mz = zl("MTC"), reds = [w === "RED" ? "West" : "", mz === "RED" ? "sea" : ""].filter(Boolean);
      baseItems = [
        ["Main effort", reds.length ? `${reds.join(" and ")} at RED: resources there first.` : w === "GREEN" && mz === "GREEN" ? "Both fronts quiet: shift effort to closing the LAC data gap." : "West & sea at AMBER: watch, pre-position, no surge yet."],
        ["Energy shield", SIM.oil >= 100 ? `Brent +${SIM.oil}%: release reserves, hedge, rupee readiness.` : SIM.oil < 30 ? "Prices calm: refill reserves." : "Reserves, crude hedging, rupee readiness on a posture alert."],
        ["Evacuation", ["Afghanistan–Pakistan", "US–Iran", "Israel–Hamas"].some((x) => lvl(x) === "RED") ? `Execute where RED: ${["Afghanistan–Pakistan", "US–Iran", "Israel–Hamas"].filter((x) => lvl(x) === "RED").map((x) => CHAINS[x].short).join(", ")}.` : "Gulf & Afghanistan plans live; 6 of 7 past evacuations were on our list."],
        P.items[3], P.items[4],
      ];
    }
    const items = [...baseItems];
    const glance = wars.map((w) => { const v = pv(w)!; return `${CHAINS[w].short} ${v.level} ~${k(v.p50)} · surge ${Math.round(v.p_up * 100)}%`; }).join(" · ");
    if (!isBase() && role !== "CDS" && baseItems === P.items) {
      if (SIM.attack && (role === "WTC" || role === "CDS")) items.unshift(["Readiness now", "Qualifying attack: state fighting has followed within ~15 days since 2016. Warning Order today."]);
      if (SIM.oil >= 100 && (role === "MTC" || role === "CDS")) items.unshift(["Energy shock", `Brent +${SIM.oil}% ≈ $${bill} B a year: release reserves, hedge crude, ready the rupee.`]);
      if ((SIM.iran ?? 0) >= 50 && (role === "MTC" || role === "CDS")) items.unshift(["Gulf NEO", "Restart likely: move evacuation plans to ready; escort tankers."]);
    }
    side.classList.toggle("re", !first);
    side.innerHTML = `${sc}
      <div class="o7-so${first ? "" : " re"}" style="--sc:${soCol}"><div class="h">SO WHAT FOR INDIA · ${pl.toUpperCase()}${isBase() ? "" : " · SCENARIO"}</div><div class="t">${so.t}</div><div class="s">${so.s}</div></div>
      <div class="o7-per" role="tablist" aria-label="Period">${PER.map((p) => `<button role="tab" data-per="${p}" class="${p === per ? "on" : ""}">${p === "2027" ? "2027 · WHOLE YEAR" : p}</button>`).join("")}</div>
      ${role === "NTC" ? `<div class="o7-gap"><b>Northern theatre: no 2027 numbers.</b> The data hold one fatal LAC clash since 1975 (Galwan, Jun 2020), too few to project; the outlook works through the wars that touch it.</div>` : ""}
      ${wars.map(chain).join("")}
      <div class="o7-india" style="animation-delay:${first ? 300 + wars.length * 450 : 0}ms"><div class="h">${P.h}</div>
        <div class="row"><div class="gl"><b>${esc(pl)} at a glance</b>${esc(glance)}</div>${items.map(([a, b], i) => `<div class="${!isBase() && (i < items.length - baseItems.length || baseItems !== P.items) ? "new" : ""}"><b>${esc(a)}</b>${esc(b)}</div>`).join("")}</div></div>`;
    side.querySelectorAll<HTMLElement>(".o7-per button").forEach((b) => b.addEventListener("click", () => { per = b.dataset.per!; first = true; render(); syncSim(); }));
    side.querySelector(".o7-reset")?.addEventListener("click", () => { Object.assign(SIM, SIM0); syncSim(); render(); });
    wars.forEach((w) => (prevLvl[w] = lvl(w)));
    drawMap(pl);
    first = false;
  };

  const drawMap = (pl: string) => {
    box.innerHTML = `<div class="o7-tag">${esc((X?.theatres?.[role]?.name ?? "All theatres").toUpperCase())} · ${pl.toUpperCase()}${isBase() ? "" : " · SCENARIO"}</div>
      <div class="o7-leg"><span><i style="background:${RAG_COLOR.RED}"></i>RED</span><span><i style="background:${RAG_COLOR.AMBER}"></i>AMBER</span><span><i style="background:${RAG_COLOR.GREEN}"></i>GREEN</span><span><i style="border:1.5px dashed #E28CC1"></i>DATA GAP</span><span>┅ impact on India</span></div>`;
    const go = () => {
      if (!box.clientWidth) return requestAnimationFrame(go);
      const keep = [...box.children];
      const m = regionMap(box, D.world, BOX);
      keep.forEach((c) => box.appendChild(c));
      const svg = box.querySelector("svg.map"); if (svg && !first) svg.classList.add("still");
      { const st = document.createElementNS("http://www.w3.org/2000/svg", "text"); st.setAttribute("x", String(m.w - 24)); st.setAttribute("y", String(m.h - 40)); st.setAttribute("text-anchor", "end"); st.setAttribute("class", "stamp fade"); st.textContent = isBase() ? pl.toUpperCase() : "WHAT-IF"; m.layer.appendChild(st); }
      const ns = "http://www.w3.org/2000/svg";
      const mk = (tag: string, a: Record<string, any>, parent: Element) => { const e = document.createElementNS(ns, tag); for (const [kk, v] of Object.entries(a)) e.setAttribute(kk, String(v)); parent.appendChild(e); return e; };
      for (const f of X?.aor?.features ?? []) {
        const code = f.properties.code, z = zone(code); if (!z) continue;
        const on = role === "CDS" || code === role, col = z.lv === "DATA GAP" ? "#E28CC1" : RAG_COLOR[z.lv];
        const fo = (on ? (z.lv === "RED" ? 0.34 : 0.26) : 0.06) * (code === "MTC" ? 0.45 : 1);
        const changed = prevZone[code] && prevZone[code] !== z.lv;
        const p = mk("path", { d: m.path(f) || "", class: on ? `zone breath${z.lv === "RED" ? " fast" : ""}${changed ? " zflash" : ""}` : "zone", style: `--fo:${fo}`, fill: col, "fill-opacity": fo, stroke: col, "stroke-width": on ? (z.lv === "RED" ? 3.4 : 2.6) : 1 }, m.layer);
        if (z.lv === "DATA GAP" || !on) p.setAttribute("stroke-dasharray", "5 4");
        prevZone[code] = z.lv;
        const ct = m.proj(z.at);
        if (ct && isFinite(ct[0])) {
          const t = mk("text", { x: ct[0], y: ct[1], "text-anchor": "middle", class: `zl fade${changed ? " pop" : ""}`, style: "animation-delay:.3s", fill: col, "fill-opacity": on ? 1 : 0.45 }, m.top); t.textContent = `${code} · ${z.lv}`;
          const t2 = mk("text", { x: ct[0], y: ct[1] + 16, "text-anchor": "middle", class: "lbl fade", style: "animation-delay:.4s", fill: "#C9D6E3", "fill-opacity": on ? 1 : 0.45 }, m.top); t2.textContent = z.why;
        }
      }
      Object.keys(CHAINS).forEach((w, i) => {
        const C = CHAINS[w], on = wars.includes(w), col = RAG_COLOR[lvl(w)] ?? C.c;
        const a = m.proj(C.at), b = m.proj(C.to); if (!a || !b) return;
        const mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - Math.abs(b[0] - a[0]) * 0.22;
        const d = `M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}`;
        mk("path", { d, class: "arc-bg", stroke: C.c, "stroke-opacity": on ? 0.14 : 0.03 }, m.layer);
        const dl = first ? 0.15 + i * 0.22 : 0.05 * i, v0 = pv(w), sw = on && v0 ? Math.max(2.4, Math.min(8, 1.2 + 1.1 * Math.log10(1 + v0.p50))) : 2;
        if (on) mk("path", { d, fill: "none", stroke: col, "stroke-width": sw * 3.2, "stroke-opacity": v0?.level === "RED" ? 0.22 : 0.12, class: "fade", style: `animation-delay:${dl + 0.6}s;filter:blur(4px)` }, m.layer);
        mk("path", { d, class: on ? "arc draw" : "arc", stroke: C.c, "stroke-width": sw, "stroke-opacity": on ? 1 : 0.15, style: on ? `animation-delay:${dl}s, ${dl + 1.1}s;animation-duration:1.1s, ${v0?.level === "RED" ? 0.8 : v0?.level === "AMBER" ? 1.6 : 2.6}s` : "" }, m.layer);
        if (on) { // particles from the war into India: more and faster when the scenario is deadlier
          const n = v0 && v0.p50 > 10000 ? 6 : v0 && v0.p50 > 1000 ? 4 : v0 && v0.p50 > 100 ? 3 : v0 && v0.p50 > 10 ? 2 : 1, dur = v0?.level === "RED" ? 1.5 : v0?.level === "AMBER" ? 2.4 : 3.6;
          for (let j = 0; j < n; j++) {
            const c = mk("circle", { r: Math.max(3, sw * 0.9), fill: "#fff", "fill-opacity": 0.95, stroke: col, "stroke-width": 2 }, m.top);
            const am = document.createElementNS(ns, "animateMotion");
            am.setAttribute("dur", `${dur}s`); am.setAttribute("repeatCount", "indefinite"); am.setAttribute("path", d);
            am.setAttribute("begin", `${dl + 1.1 + (j * dur) / n}s`); am.setAttribute("keyPoints", "0;1"); am.setAttribute("keyTimes", "0;1"); am.setAttribute("calcMode", "linear");
            c.setAttribute("opacity", "0"); c.appendChild(am);
            const op = document.createElementNS(ns, "set"); op.setAttribute("attributeName", "opacity"); op.setAttribute("to", "1"); op.setAttribute("begin", `${dl + 1.1 + (j * dur) / n}s`); c.appendChild(op);
          }
        }
        const v = pv(w), rr = on && v ? Math.max(8, Math.min(34, 5 + 4.2 * Math.log10(1 + v.p50))) : 5;
        if (on) mk("circle", { cx: a[0], cy: a[1], r: rr, fill: col, "fill-opacity": 0.25, stroke: col, "stroke-width": 2, class: `halo${v?.level === "RED" ? " fast" : ""}`, style: `animation-delay:${dl}s` }, m.top);
        mk("circle", { cx: a[0], cy: a[1], r: on ? rr * 0.55 : 3, fill: col, "fill-opacity": on ? 0.9 : 0.4, class: "pop", style: `animation-delay:${dl}s` }, m.top);
        if (on) {
          mk("circle", { cx: b[0], cy: b[1], r: 7, fill: C.c, stroke: "#05070A", "stroke-width": 2, class: "pop", style: `animation-delay:${dl + 1.0}s` }, m.top);
          mk("circle", { cx: b[0], cy: b[1], r: 7, fill: "none", stroke: C.c, "stroke-width": 2, class: "halo", style: `animation-delay:${dl + 1.1}s` }, m.top);
          let [dx, dy, an] = C.lab;
          if (m.w < 760 && an === "end") { const tw = 10.5 * `${C.short} · ${pl} ${lvl(w)} · ~${k(v?.p50 ?? 0)}`.length; if (a[0] + dx - tw < 4) { an = "start"; dx = 12; } }
          const t = mk("text", { x: a[0] + dx, y: a[1] + dy, "text-anchor": an, class: "zl fade", style: `animation-delay:${dl + .2}s`, fill: col }, m.top); t.textContent = `${C.short} · ${pl} ${lvl(w)} · ~${k(v?.p50 ?? 0)}`;
          const t2 = mk("text", { x: a[0] + dx, y: a[1] + dy + 15, "text-anchor": an, class: "lbl fade", style: `animation-delay:${dl + .5}s`, fill: C.c }, m.top); t2.textContent = `→ India: ${C.via}`;
        }
      });
    };
    requestAnimationFrame(go);
  };

  // Lever panel (built once; re-rendering the map and cards leaves it in place so a drag is not interrupted).
  const ir0 = Math.round((O.cases["US–Iran"]?.p_up ?? 0.12) * 100);
  const DEF: Record<string, { lab: string; min: number; max: number; step: number; base: number; fmt: (v: number) => string; say: (v: number) => string; war?: string }> = {
    afpak: { lab: "Af–Pak fighting", min: -90, max: 200, step: 5, base: 0, war: "Afghanistan–Pakistan", fmt: (v) => (v === 0 ? "baseline" : `${v > 0 ? "+" : ""}${v}%`), say: (v) => (v <= -60 ? "ceasefire" : v < -10 ? "easing" : v <= 10 ? "as today" : v < 100 ? "escalating" : "major offensive") },
    iran: { lab: "US–Iran restart risk", min: 0, max: 100, step: 1, base: ir0, war: "US–Iran", fmt: (v) => `${v}%`, say: (v) => (v < 5 ? "deal holds" : v < 20 ? "low" : v < 50 ? "rising" : v < 80 ? "likely" : "war restarts") },
    ruua: { lab: "RU–UA fighting", min: -98, max: 100, step: 5, base: 0, war: "Russia–Ukraine", fmt: (v) => (v === 0 ? "baseline" : `${v > 0 ? "+" : ""}${v}%`), say: (v) => (v <= -95 ? "full ceasefire" : v <= -70 ? "ceasefire" : v < -10 ? "winding down" : v <= 10 ? "as today" : "escalation") },
    ilh: { lab: "Israel–Hamas fighting", min: -80, max: 300, step: 10, base: 0, war: "Israel–Hamas", fmt: (v) => (v === 0 ? "baseline" : `${v > 0 ? "+" : ""}${v}%`), say: (v) => (v <= -50 ? "truce holds" : v <= 20 ? "as today" : v < 150 ? "flare-up" : "truce collapses") },
    oil: { lab: "Brent oil shock", min: 0, max: 150, step: 5, base: 55, fmt: (v) => `+${v}%`, say: (v) => `≈ $${Math.round((52 * v) / 55)} B/yr on India's crude bill` },
  };
  const levers = LEVERS[role] ?? LEVERS.CDS;
  simEl.innerHTML = `<div class="o7-sim-h"><b>⚗ WHAT-IF · MOVE THE LEVERS</b><span>Scenario on our 2027 ranges · not a model run</span></div>
    <div class="o7-chips"></div>
    <div class="o7-pre">${Object.keys(PRESETS).map((p) => `<button data-pre="${p}">${p}</button>`).join("")}</div>
    <div class="o7-lv">${levers.map((id) => {
      if (id === "attack") return `<label class="o7-tg"><input type="checkbox" data-id="attack"><span class="sw"></span><span><b>Qualifying terror attack in J&amp;K</b><em>starts the 15-day clock → WTC RED</em></span></label>`;
      const L = DEF[id as string];
      return `<div class="o7-sl" data-id="${id}"><div class="top"><b>${L.lab}</b><span class="val"></span><span class="res"></span></div>
        <div class="trk"><input type="range" min="${L.min}" max="${L.max}" step="${L.step}" aria-label="${L.lab}"><i class="bm" style="left:${((L.base - L.min) / (L.max - L.min)) * 100}%" title="baseline"></i></div><div class="bot"><span class="say"></span><span class="thr"></span></div></div>`;
    }).join("")}</div>
    <details class="o7-rule"><summary>How the rating is set</summary>
      <p><b style="color:${RAG_COLOR.RED}">RED</b> if the middle case is ≥ 1,000 deaths a month <i>or</i> a surge is more likely than not (≥ 50%). <b style="color:${RAG_COLOR.AMBER}">AMBER</b> if ≥ 100 a month <i>or</i> surge chance ≥ 30%. Otherwise <b style="color:${RAG_COLOR.GREEN}">GREEN</b>.</p>
      <p><b>Surge</b> = deaths at least 1.5× today's pace (the deck's escalation test). Its chance comes from a lognormal fitted to each war's 2027 range; at baseline it returns the data file's own figures (e.g. Af–Pak 13%, US–Iran 12%), so baseline ratings do not move. For US–Iran the lever <i>is</i> the chance of a restart.</p>
      <p><b>Theatre zones:</b> WTC follows Af–Pak (RED on a qualifying attack). MTC is the worse of US–Iran and Israel–Hamas, held at AMBER while restart risk ≥ 10% or Brent ≥ +30%, RED at Brent ≥ +100%. Coloured ticks on each lever mark where it turns <span style="color:${RAG_COLOR.AMBER}">AMBER</span> and <span style="color:${RAG_COLOR.RED}">RED</span> for the selected period.</p>
    </details>`;
  // Where on each lever the war turns AMBER and RED (for the period shown): scan the lever's range.
  const marks = () => simEl.querySelectorAll<HTMLElement>(".o7-sl").forEach((row) => {
    const id = row.dataset.id as keyof Sim, L = DEF[id as string], trk = row.querySelector(".trk") as HTMLElement;
    trk.querySelectorAll(".tk").forEach((e) => e.remove());
    const keep = (SIM as any)[id], xs: number[] = [], ls: string[] = [];
    for (let x = L.min; x <= L.max + 1e-9; x += L.step) { (SIM as any)[id] = x; xs.push(x); ls.push(L.war ? pvRaw(L.war) : x >= 100 ? "RED" : x >= 30 ? "AMBER" : "GREEN"); }
    (SIM as any)[id] = keep;
    const up: string[] = [], dn: string[] = [];
    for (let i = 1; i < xs.length; i++) if (ls[i] !== ls[i - 1]) {
      const x = xs[i], col = RAG_COLOR[ls[i]];
      trk.insertAdjacentHTML("beforeend", `<i class="tk" style="left:${((x - L.min) / (L.max - L.min)) * 100}%;background:${RANK[ls[i]] > RANK[ls[i - 1]] ? col : RAG_COLOR[ls[i - 1]]}" title="${ls[i - 1]} → ${ls[i]} at ${L.fmt(x)}"></i>`);
      if (x > L.base) up.push(`<span style="color:${col}">${ls[i]} from ${L.fmt(x)}</span>`);
      else dn.unshift(`<span style="color:${RAG_COLOR[ls[i - 1]]}">${ls[i - 1]} below ${L.fmt(x)}</span>`);
    }
    const all = [...dn, ...up];
    (row.querySelector(".thr") as HTMLElement).innerHTML = all.join(" · ") || `<span style="color:${RAG_COLOR[ls[0]]}">${ls[0]} across the range</span>`;
  });
  const chips = () => {
    const el = simEl.querySelector(".o7-chips") as HTMLElement;
    const z = ["WTC", "MTC"].map((c) => [c, zone(c)?.lv ?? "-"]), all = worst(z.map((x) => x[1])); // CDS = worse of the two fronts that touch India
    el.innerHTML = [...z, ["CDS", all]].map(([c, l]) => `<span class="chip" style="--cc:${RAG_COLOR[l] ?? "#888"}"><b>${c}</b>${l}</span>`).join("") +
      Object.keys(CHAINS).map((w) => { const v = pv(w)!; return `<span class="chip sm" style="--cc:${RAG_COLOR[v.level]}"><b>${CHAINS[w].short}</b>${v.level} · surge ${Math.round(v.p_up * 100)}%</span>`; }).join("");
  };
  const syncSim = () => {
    simEl.querySelectorAll<HTMLElement>(".o7-sl").forEach((row) => {
      const id = row.dataset.id as keyof Sim, L = DEF[id as string], inp = row.querySelector("input") as HTMLInputElement;
      const v = id === "iran" ? (SIM.iran ?? L.base) : (SIM[id] as number);
      inp.value = String(v);
      const pct = ((v - L.min) / (L.max - L.min)) * 100, lv = L.war ? lvl(L.war) : SIM.oil >= 100 ? "RED" : SIM.oil >= 30 ? "AMBER" : "GREEN";
      inp.style.setProperty("--p", `${pct}%`); inp.style.setProperty("--lc", RAG_COLOR[lv] ?? "#4FD1E0");
      (row.querySelector(".val") as HTMLElement).textContent = L.fmt(v);
      (row.querySelector(".say") as HTMLElement).textContent = L.say(v);
      const r = row.querySelector(".res") as HTMLElement; r.textContent = lv; r.style.background = RAG_COLOR[lv] ?? "#888";
      row.classList.toggle("moved", v !== L.base);
    });
    marks(); chips();
    const tg = simEl.querySelector<HTMLInputElement>('input[data-id="attack"]'); if (tg) tg.checked = SIM.attack;
  };
  let tmr = 0;
  const schedule = () => { syncSim(); clearTimeout(tmr); tmr = window.setTimeout(render, 140); };
  simEl.querySelectorAll<HTMLElement>(".o7-sl").forEach((row) => {
    const id = row.dataset.id as keyof Sim, inp = row.querySelector("input") as HTMLInputElement;
    inp.addEventListener("input", () => { (SIM as any)[id] = +inp.value; schedule(); });
    inp.addEventListener("dblclick", () => { (SIM as any)[id] = (SIM0 as any)[id]; schedule(); });
  });
  simEl.querySelector<HTMLInputElement>('input[data-id="attack"]')?.addEventListener("change", (e) => { SIM.attack = (e.target as HTMLInputElement).checked; schedule(); });
  simEl.querySelectorAll<HTMLElement>(".o7-pre button").forEach((b) => b.addEventListener("click", () => { Object.assign(SIM, SIM0, PRESETS[b.dataset.pre!]); syncSim(); render(); }));
  render();
  syncSim();
}

const SIMCSS = `
.o7-left { display:flex; flex-direction:column; gap:12px; min-width:0; }
.o7-left .o7-map { height: clamp(380px, 62vh, 640px); }
.o7-map svg.map.still { animation:none; }
.o7-map .breath.fast { animation: o7fade .5s ease both, o7breath 1.1s ease-in-out .5s infinite; }
.o7-map .halo.fast { animation-duration: 1.1s; }
.o7-map .zflash { animation: o7zf .9s ease 2, o7breath 1.6s ease-in-out 1.8s infinite; }
@keyframes o7zf { 0%,100% { fill-opacity: var(--fo); } 40% { fill-opacity: .75; } }
.o7-sim { background: var(--panel); border:1px solid var(--line); border-radius:14px; padding:12px 14px; }
.o7-sim-h { display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap; margin-bottom:8px; }
.o7-sim-h b { font: 800 12px var(--mono); letter-spacing:.16em; color: var(--teal); }
.o7-sim-h span { font-size:12px; color: var(--tx3); }
.o7-pre { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
.o7-pre button { font: 800 11px var(--mono); letter-spacing:.1em; padding:6px 11px; border-radius:999px; border:1px solid var(--line2); background: transparent; color: var(--tx2); cursor:pointer; }
.o7-pre button:hover { border-color: var(--teal); color: var(--tx); }
.o7-lv { display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:12px 20px; }
.o7-pre button:focus:not(:focus-visible) { border-color: var(--line2); }
.o7-sl .top { display:flex; align-items:center; gap:8px; font-size:14px; }
.o7-sl .top b { font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; min-width:0; }
.o7-sl .bot { display:flex; justify-content:space-between; gap:8px; margin-top:5px; flex-wrap:wrap; }
.o7-sl .say { color: var(--tx2); font-size:12.5px; }
.o7-sl .thr { font: 700 11px var(--mono); letter-spacing:.04em; }
.o7-sl .tk { position:absolute; top:-2px; width:3px; height:18px; border-radius:2px; transform: translateX(-1px); pointer-events:none; box-shadow: 0 0 0 1px #05070A; }
.o7-chips { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
.o7-chips .chip { display:inline-flex; gap:6px; align-items:center; font: 800 11px var(--mono); letter-spacing:.08em; padding:4px 9px; border-radius:7px; border:1px solid var(--cc); color: var(--cc); background: color-mix(in srgb, var(--cc) 12%, transparent); transition: all .3s; }
.o7-chips .chip b { color: var(--tx); font-weight:800; }
.o7-chips .chip.sm { font-size:10.5px; padding:3px 7px; opacity:.9; }
.o7-rule { margin-top:12px; font-size:13px; color: var(--tx2); border-top:1px solid var(--line); padding-top:8px; }
.o7-rule summary { cursor:pointer; font: 800 11px var(--mono); letter-spacing:.12em; color: var(--tx2); }
.o7-rule p { margin:6px 0; line-height:1.45; }
.o7-ch .pg { display:flex; align-items:center; justify-content:flex-end; gap:6px; margin-top:4px; font: 700 11px var(--mono); color: var(--tx3); }
.o7-ch .pg b2 { font-weight:800; color: var(--tx); } .o7-ch .pg em2 { font-style:normal; color: var(--tx3); }
.o7-ch .pgb { position:relative; width:90px; height:7px; border-radius:99px; background: rgba(255,255,255,.12); overflow:hidden; }
.o7-ch .pgb i { position:absolute; left:0; top:0; bottom:0; border-radius:99px; transition: width .4s; }
.o7-ch .pgb u { position:absolute; top:0; bottom:0; width:1px; background: rgba(255,255,255,.55); }
.o7-sl .val { margin-left:auto; font: 800 13px var(--mono); white-space:nowrap; }
.o7-sl .res { font: 800 10.5px var(--mono); letter-spacing:.08em; color:#05070A; padding:2px 7px; border-radius:5px; transition: background .3s; }
.o7-sl.moved .val { color: var(--amber); }
.o7-sl .trk { position:relative; margin-top:6px; }
.o7-sl .bm { position:absolute; top:-3px; width:2px; height:20px; background: var(--tx2); transform: translateX(-1px); pointer-events:none; opacity:.7; }
.o7-sl input[type=range] { -webkit-appearance:none; appearance:none; width:100%; height:8px; border-radius:99px; outline:none; cursor:pointer;
  background: linear-gradient(90deg, var(--lc) 0 var(--p), rgba(255,255,255,.12) var(--p) 100%); }
.o7-sl input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:22px; height:22px; border-radius:50%; background:#fff; border:4px solid var(--lc); box-shadow:0 0 0 4px rgba(0,0,0,.35); }
.o7-sl input[type=range]::-moz-range-thumb { width:16px; height:16px; border-radius:50%; background:#fff; border:4px solid var(--lc); }
.o7-tg { display:flex; align-items:center; gap:10px; cursor:pointer; font-size:14px; }
.o7-tg input { position:absolute; opacity:0; width:0; height:0; }
.o7-tg .sw { width:44px; height:24px; border-radius:99px; background: rgba(255,255,255,.15); position:relative; flex:none; transition: background .2s; }
.o7-tg .sw::after { content:""; position:absolute; left:3px; top:3px; width:18px; height:18px; border-radius:50%; background:#fff; transition: transform .2s; }
.o7-tg input:checked + .sw { background: #FF6B6B; } .o7-tg input:checked + .sw::after { transform: translateX(20px); }
.o7-tg input:focus-visible + .sw { outline: 2px solid var(--teal); outline-offset:2px; }
.o7-tg em { display:block; font-style:normal; font-size:12.5px; color: var(--tx2); }
.o7-scn { display:flex; align-items:center; gap:10px; font: 800 12px var(--mono); letter-spacing:.12em; color: var(--amber); border:1px dashed var(--amber); border-radius:10px; padding:7px 12px; }
.o7-scn button { margin-left:auto; font: 800 11px var(--mono); letter-spacing:.12em; padding:5px 12px; border-radius:999px; border:1px solid var(--amber); background: transparent; color: var(--amber); cursor:pointer; }
.o7-steps.chg .o7-st { animation: o7chg .9s ease both !important; opacity:1; }
@keyframes o7chg { 0% { box-shadow: 0 0 0 0 rgba(242,179,61,.0); background: rgba(242,179,61,.28); } 100% { box-shadow:none; } }
.o7-india .row div.gl { border-color: rgba(79,209,224,.55); background: rgba(79,209,224,.08); font-family: var(--mono); font-size:12.5px; }
.o7-tnote { margin-top:8px; font-size:14px; font-weight:700; color: var(--tc); }
.o7-ch .dv { display:block; font: 800 12px var(--mono); font-style:normal; margin-top:3px; }
.o7-ch .lv s { font: 700 11px var(--mono); }
.o7-ch.flip { animation: o7flip .7s ease both; }
@keyframes o7flip { 0% { box-shadow: 0 0 0 0 var(--c); transform: scale(.985); } 40% { box-shadow: 0 0 0 4px color-mix(in srgb, var(--c) 45%, transparent); } 100% { box-shadow:none; transform:none; opacity:1; } }
.o7-chains.re .o7-ch, .o7-chains.re .o7-st, .o7-chains.re .o7-india { animation:none; opacity:1; transform:none; }
.o7-chains.re .o7-ch.flip { animation: o7flip .7s ease both; }
.o7-so.re { animation: none; opacity:1; transition: border-color .4s, background .4s; }
.o7-india .row div.new { border-color: var(--amber); background: rgba(242,179,61,.10); }
`;

export function openOutlookModal(D: Data, role: string) {
  document.getElementById("ol-modal")?.remove();
  const m = document.createElement("div");
  m.id = "ol-modal"; m.setAttribute("role", "dialog"); m.setAttribute("aria-modal", "true"); m.setAttribute("aria-label", "2027 outlook");
  m.style.cssText = "position:fixed;inset:0;z-index:80;background:rgba(5,11,18,.97);backdrop-filter:blur(6px);overflow:auto;padding:24px 2.5vw";
  const T = D.theatre?.theatres?.[role];
  m.innerHTML = `<div style="max-width:1500px;margin:0 auto"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div class="eyebrow" style="margin:0">${esc((T ? T.name : "All theatres").toUpperCase())} · 2027 OUTLOOK · HOW THE WARS REACH INDIA</div>
      <button class="btn" id="ol-x" aria-label="Close">✕ CLOSE</button></div><div id="ol-host"></div></div>`;
  document.body.appendChild(m);
  mountOutlook(m.querySelector("#ol-host") as HTMLElement, D, role);
  const close = () => { m.remove(); document.removeEventListener("keydown", onKey); };
  const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") close(); };
  document.addEventListener("keydown", onKey);
  (m.querySelector("#ol-x") as HTMLElement).addEventListener("click", close);
  m.addEventListener("click", (e) => { if (e.target === m) close(); });
}
