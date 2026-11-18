// 2027 outlook, visual: an animated map of India's theatre zones with the wars' impact lines, and for each war a short
// chain "war → what it does to them → what it means for India → what India should do". Levels come from
// web/public/data/outlook2027.json (analogue scenario range, scripts/outlook_2027.py); the chains are our analysis.
import { type Data, RAG_COLOR } from "./data";
import { regionMap, pulse } from "./maps";

const esc = (s: any) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
const k = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k` : String(n));

const CSS = `
.o7 { display:grid; grid-template-columns: minmax(0,1.05fr) minmax(0,1fr); gap:18px; align-items:start; }
@media (max-width: 1100px) { .o7 { grid-template-columns: 1fr; } }
.o7-map { position:relative; height:620px; background: var(--panel); border:1px solid var(--line); border-radius:14px; overflow:hidden; }
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
const ZONE: Record<string, { lv: string; why: string; at: [number, number] }> = { WTC: { lv: "AMBER", why: "Af–Pak rising", at: [71.6, 28.6] }, MTC: { lv: "AMBER", why: "restart risk · oil", at: [67, 9] }, NTC: { lv: "DATA GAP", why: "no LAC data", at: [87, 33.5] } };
const PRI: Record<string, { h: string; items: string[][] }> = {
  WTC: { h: "WESTERN THEATRE · 2027 PRIORITIES", items: [["LoC first", "Raise LoC watch whenever Af–Pak is AMBER/RED."], ["Eyes on 3 districts", "Kandahar, Balochistan, Kunar."], ["15-day clock", "Pre-set readiness after any qualifying attack."]] },
  MTC: { h: "MARITIME THEATRE · 2027 PRIORITIES", items: [["Sea lanes", "Hormuz, Arabian Sea, Red Sea under watch."], ["NEO ready", "~9 M Indians in the Gulf."], ["Same-day action", "Posture alert → Warning Order."]] },
  NTC: { h: "NORTHERN THEATRE · 2027 PRIORITIES", items: [["Close the data gap", "Face-offs, build-ups, infrastructure, patrol clashes."], ["Watch the partners", "Russia–China closeness; Pakistan on two fronts."], ["Drill the flow", "FLASH drill on synthetic data until real indicators exist."]] },
  CDS: { h: "INDIA LEVEL (CDS) · 2027 PRIORITIES", items: [["Main effort: West & sea", "Af–Pak the rising front; US–Iran the restart risk with the widest reach."], ["Energy shield", "Reserves, crude hedging, rupee readiness on a posture alert."], ["Evacuation ready", "Gulf & Afghanistan plans live; 6 of 7 past evacuations were on our list."], ["Close the LAC gap", "Add non-fatal LAC & LoC indicators in H1 2027."], ["One monthly picture", "Watch-list & RAG in the HQ IDS brief; tripwire daily."]] },
};
const BOX: [[number, number], [number, number]] = [[28, 2], [98, 51]];

export function mountOutlook(host: HTMLElement, D: Data, role: string) {
  const O = (D as any).outlook, X = D.theatre;
  if (!O) { host.innerHTML = `<p class="muted">2027 outlook not built.</p>`; return; }
  if (!document.getElementById("o7-css")) document.head.insertAdjacentHTML("beforeend", `<style id="o7-css">${CSS}</style>`);
  const wars = ROLE_WARS[role] ?? ROLE_WARS.CDS, P = PRI[role] ?? PRI.CDS;
  const lvl = (w: string) => O.cases[w]?.level2027 ?? "-";
  const chain = (w: string, i: number) => {
    const C = CHAINS[w], c = O.cases[w], d0 = 250 + i * 450;
    const st = (cls: string, h: string, items: string[], d: number) => `<div class="o7-st ${cls}" style="animation-delay:${d}ms"><div class="h">${h}</div><ul>${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
    return `<div class="o7-ch" style="--c:${C.c};animation-delay:${d0}ms">
      <h4><span style="color:${C.c}">●</span>${esc(C.war)}
        <span class="lv">NOW <b style="background:${RAG_COLOR[c.rating_now] ?? "#888"}">${c.rating_now}</b> → 2027 <b style="background:${RAG_COLOR[c.level2027]}">${c.level2027}</b></span>
        <span class="n">~${k(c.y2027.p50)} deaths in 2027</span></h4>
      <div class="o7-steps">${st("them", C.themLabel, C.them, d0 + 150)}<div class="o7-ar"><span>➜</span></div>${st("ind", "ON INDIA", C.ind, d0 + 300)}<div class="o7-ar"><span>➜</span></div>${st("do", "INDIA SHOULD", C.act, d0 + 450)}</div></div>`;
  };
  host.innerHTML = `<div class="o7">
    <div class="o7-map"><div class="o7-tag">${esc((X?.theatres?.[role]?.name ?? "All theatres").toUpperCase())} · 2027</div>
      <div class="o7-leg"><span><i style="background:${RAG_COLOR.RED}"></i>RED</span><span><i style="background:${RAG_COLOR.AMBER}"></i>AMBER</span><span><i style="background:${RAG_COLOR.GREEN}"></i>GREEN</span><span><i style="border:1.5px dashed #E28CC1"></i>DATA GAP</span><span>┅ impact on India</span></div></div>
    <div class="o7-chains">
      ${role === "NTC" ? `<div class="o7-gap"><b>Northern theatre: no 2027 numbers.</b> The data hold no fatal LAC events, so the outlook works through the wars that touch it.</div>` : ""}
      ${wars.map(chain).join("")}
      <div class="o7-india" style="animation-delay:${300 + wars.length * 450}ms"><div class="h">${P.h}</div>
        <div class="row">${P.items.map(([a, b]) => `<div><b>${esc(a)}</b>${esc(b)}</div>`).join("")}</div></div>
    </div>
    <div class="o7-foot">2027 level = middle case of a scenario range from history (what happened next to similar conflicts in 117 countries, 1989–2025; the range held 89% out of time). Not a validated forecast. Chains are our analysis.</div>
  </div>`;
  const box = host.querySelector(".o7-map") as HTMLElement;
  const draw = () => {
    if (!box.clientWidth) return requestAnimationFrame(draw);
    const keep = [...box.children];
    const m = regionMap(box, D.world, BOX);
    keep.forEach((c) => box.appendChild(c));
    const ns = "http://www.w3.org/2000/svg";
    const mk = (tag: string, a: Record<string, any>, parent: Element) => { const e = document.createElementNS(ns, tag); for (const [kk, v] of Object.entries(a)) e.setAttribute(kk, String(v)); parent.appendChild(e); return e; };
    for (const f of X?.aor?.features ?? []) {
      const code = f.properties.code, z = ZONE[code]; if (!z) continue;
      const on = role === "CDS" || code === role, col = z.lv === "DATA GAP" ? "#E28CC1" : RAG_COLOR[z.lv];
      const p = mk("path", { d: m.path(f) || "", fill: col, "fill-opacity": (on ? 0.24 : 0.06) * (code === "MTC" ? 0.45 : 1), stroke: col, "stroke-width": on ? 2.4 : 1 }, m.layer);
      if (z.lv === "DATA GAP" || !on) p.setAttribute("stroke-dasharray", "5 4");
      const ct = m.proj(z.at);
      if (ct && isFinite(ct[0])) {
        const t = mk("text", { x: ct[0], y: ct[1], "text-anchor": "middle", class: "zl", fill: col, "fill-opacity": on ? 1 : 0.45 }, m.top); t.textContent = `${code} · ${z.lv}`;
        const t2 = mk("text", { x: ct[0], y: ct[1] + 16, "text-anchor": "middle", class: "lbl", fill: "#C9D6E3", "fill-opacity": on ? 1 : 0.45 }, m.top); t2.textContent = z.why;
      }
    }
    Object.keys(CHAINS).forEach((w, i) => {
      const C = CHAINS[w], on = wars.includes(w), col = RAG_COLOR[lvl(w)] ?? C.c;
      const a = m.proj(C.at), b = m.proj(C.to); if (!a || !b) return;
      const mx = (a[0] + b[0]) / 2, my = Math.min(a[1], b[1]) - Math.abs(b[0] - a[0]) * 0.22;
      const d = `M${a[0]},${a[1]} Q${mx},${my} ${b[0]},${b[1]}`;
      mk("path", { d, class: "arc-bg", stroke: C.c, "stroke-opacity": on ? 0.14 : 0.03 }, m.layer);
      mk("path", { d, class: "arc", stroke: C.c, "stroke-opacity": on ? 1 : 0.15, style: `animation-duration:${1.2 + i * 0.25}s` }, m.layer);
      pulse(m, C.at[0], C.at[1], col, undefined, i * 300, on ? 9 : 5);
      if (on) {
        mk("circle", { cx: b[0], cy: b[1], r: 5, fill: C.c, stroke: "#05070A", "stroke-width": 2 }, m.top);
        const [dx, dy, an] = C.lab;
        const t = mk("text", { x: a[0] + dx, y: a[1] + dy, "text-anchor": an, class: "zl", fill: col }, m.top); t.textContent = `${C.short} · 2027 ${lvl(w)}`;
        const t2 = mk("text", { x: a[0] + dx, y: a[1] + dy + 15, "text-anchor": an, class: "lbl", fill: C.c }, m.top); t2.textContent = `→ India: ${C.via}`;
      }
    });
  };
  requestAnimationFrame(draw);
}

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
