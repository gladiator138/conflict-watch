"""Build the slide-by-slide presenter script (DOCX; PDF via LibreOffice).

    python brief/build_script.py
"""
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Cm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "brief" / "Presenter_Script.docx"
URL = "conflictmonitor2026.streamlit.app"
M, S, H = "Maj Shivam Mehta", "Capt Siddharth Sangwan", "Capt Sahil Singh"
NAVY, AMBER, GREY, RED = RGBColor(0x07, 0x13, 0x1F), RGBColor(0xB0, 0x7A, 0x10), RGBColor(0x55, 0x60, 0x6E), RGBColor(0xC0, 0x30, 0x40)

# (slide, title, speaker, start, end, say, do, handover)
SLIDES = [
    (1, "Cover: Conflict Watch", M, "0:00", "0:30",
     ["Good morning, sir. We are Maj Shivam Mehta, Capt Siddharth Sangwan and Capt Sahil Singh.",
      "Our question was simple: when and where will conflict deaths rise next, and what does it mean for India?",
      "We looked at four wars: Russia–Ukraine, Israel–Hamas, Afghanistan–Pakistan and US–Iran, using all twelve issued data files."],
     "Slide on screen. Camera on.", None),
    (2, "BLUF: four wars, three warning signals, one exposed neighbour", M, "0:30", "1:30",
     ["Bottom line up front, in three points.",
      "One. Threat. Russia–Ukraine stays RED: our model forecasts about 6,780 deaths in October 2026. Af–Pak and US–Iran are AMBER; Israel–Hamas is GREEN.",
      "Two. India. On 4 March 2026, 104 people were killed in one strike off Sri Lanka. The US–Iran war reached the Indian Ocean, and struck five Gulf states that host the Indian diaspora.",
      "Three. Prediction. On 2026 data the model never saw, our forecast cut the error of the 'no change' rule by 29%, and our district watch-list is 3.5 times better than random.",
      "So what: warn on spread and hotspots, not on headlines."],
     "Point at each of the three numbers as you say it.", f"Capt Sangwan will now show how we built the evidence."),
    (3, "Our approach: how we went about the problem", S, "1:30", "2:05",
     ["Sir, we framed one operational question: when and where will conflict deaths rise next, and what does it mean for India?",
      "We broke it into five sub-questions: how intense, how fought, can we forecast, can we warn, and what it means for India. Each has a method and a slide, shown on the right."],
     "Builds play automatically; do not click until the APPROACH bar has appeared.", None),
    (4, "Data and pipeline, and the four rules", S, "2:05", "2:45",
     ["The pipeline runs left to right in one command: ingest all twelve issued files: 61,055 UCDP events, the UN, IDMC and World Bank files, GDELT and the Middle East events; clean with 36 logged checks, for example FATA merged into Khyber Pakhtunkhwa; build features for 4 conflicts and 222 districts; explore; model; warn; and deliver to the dashboard.",
      "Four rules: 2026 was withheld and scored once; every model had to beat the no-change rule; every claim is tagged DATA or DOMAIN; and one command rebuilds every number, stamped with this run ID."],
     "", None),
    (5, "Method: why each model was chosen", S, "2:45", "3:30",
     ["Seven forecasters competed, from 'no change' to SARIMA and LightGBM, and the back-test chose for us.",
      "LightGBM predicts the change in log deaths, because trees cannot go beyond their training range: a level model trained before 2022 could never forecast the invasion.",
      "Eighteen compact features beat the full set, the ensemble averages three models because no single one wins every fold, and walk-forward folds stop the future leaking in."],
     "", None),
    (6, "Validation: prediction on unseen 2026 data (Russia–Ukraine)", S, "3:30", "4:10",
     ["We compared seven forecasters, from 'no change' to SARIMA and LightGBM, on a walk-forward back-test.",
      "The chosen ensemble cut one-month error by 29% against 'no change' on 2026. Russia–Ukraine by 30%, Israel–Hamas by 55%.",
      "83% of 2026 outcomes fell inside our 80% band: all of them for the three established wars, but only 22% for US–Iran, whose war started inside the test year."],
     "", None),
    (7, "Validation: the same method on Af–Pak", S, "4:10", "4:35",
     ["The same method on India's western neighbour. We called the direction of change right 72% of the time.",
      "The ensemble is a 3-month mean, ETS and a LightGBM on the change in deaths, chosen on 2022–25 only. Use it as a planning baseline with honest bands."],
     "", None),
    (8, "Validation: a district-level watch-list, one month ahead", S, "4:35", "5:15",
     ["Every month we score 222 area series in 22 countries for escalation next month.",
      "On 2026, the model's AUC is 0.795. The top-10 list is right 14% of the time against a base rate of 4.1%: 3.5 times random.",
      "The strongest signals are contagion: the area's own intensity, the country's tempo and the whole war's momentum.",
      "So ISR and analyst effort can be tasked before the escalation, not after."],
     "Then switch screen share to the browser tab with the live app (already open and warmed up).", None),
    (9, "LIVE DEMO: Conflict Watch Ops site", S, "5:15", "7:30",
     ["(Hero globe) Twelve years of conflict deaths, by theatre. As I scroll, the globe turns to India and draws the exposure ring: Gulf, Hormuz, Chabahar, Sri Lanka, the LoC.",
      "(BLUF) Every rating is mechanical. Click Af–Pak: 3 points, intensity plus three hotspots, so AMBER.",
      "(Front) Toggle 'show all deaths': the grey flood is the 92% with no location. That is why we use located events.",
      "(Af–Pak) Raw labels make FATA look like it went quiet after the 2018 merger; harmonised into KP, that false drop disappears and the real rise since 2021 shows.",
      "(Prediction) Press play: the 80% band coverage ticks up to 83%. Track B: here SARIMA beat us, and we show it.",
      "(Early warning) Replay March 2026: three of our top ten escalated the next month, against 0.4 by chance. Move the threshold: fewer alarms, fewer catches.",
      "(What-if) Af–Pak, plus 30% for three months: the October forecast goes from 318 to 359. Short surges damp; sustained ones carry through.",
      "(Ops console) This is what a staff officer uses each month. Ctrl+K, Kandahar: deaths, forecast and warning history. It prints a one-page I&W bulletin."],
     f"Live URL: {URL}. If the network fails, open deck/conflictwatch.html (offline copy). Deep link for the what-if: #whatif?c=afpak&shock=30&m=3. Keep to 2 min 15 s; skip the GDELT chapter if short of time.", f"Capt Sahil Singh will now take you through what this means for India."),
    (10, "Finding 1a, borders and the LoC: Pakistan now fights Afghanistan directly", H, "7:30", "8:05",
     ["This is the finding closest to home.",
      "Pakistan's recorded conflict deaths rose from 310 in 2021 to 2,361 in 2025, with 2,020 more by September 2026.",
      "October 2025 was the first month of direct fighting between the Afghan and Pakistani states in the data: 685 deaths in Jan–Sep 2026, peaking at 411 in March."],
     "Return screen share to the deck.", None),
    (11, "Finding 1b, borders and the LoC: two fronts in the west", H, "8:05", "8:45",
     ["All three top escalation hotspots for October are on this front: Kandahar, Balochistan and Kunar.",
      "Interestingly, 17% of Af–Pak events carry an Indian source, mainly PTI. Elsewhere, almost none.",
      "So what: a Pakistan Army committed in the west raises the risk of diversion along the LoC. We should watch the west too."],
     "", None),
    (12, "Finding 2, Gulf, diaspora and sea lanes: the war reached the Gulf, Hormuz and Sri Lankan waters", H, "8:45", "9:45",
     ["In 2025 the US–Iran conflict killed people in 4 countries. In 2026 it was 14.",
      "Five Gulf states were struck: 25 events. A large Indian diaspora lives there. A second provider, the Middle East events file, confirms the spread: violent events in the six Gulf states rose from 9 to 322.",
      "299 deaths on Iran's Hormuz and Chabahar coast, where our port and the INSTC route sit. 104 killed off Sri Lanka.",
      "And closer home: deaths in Pakistani areas adjoining India and the LoC went from 2 in 2022 to 52 in 2025.",
      "The decision problem: our diaspora, energy routes, Chabahar and the IOR are now inside the strike envelope."],
     "", None),
    (13, "Finding 3, defence sustainment: Ukraine, the front is widening, not moving", H, "9:45", "10:45",
     ["In 2022, 55% of located events were in Donetsk. In 2026 it is 30%. The fighting has spread to Zaporizhzhia, Dnipropetrovsk, Sumy and into Russia: 10,358 deaths inside Russia in 2024.",
      "Recorded losses are lopsided, for example 1,274 Iranian against 11 Israel–US deaths in 2026. These are recorded deaths, an upper bound of reporting, not a verified exchange ratio.",
      "And it will last: in 37 years of UCDP data, all 15 country-years with over 10,000 deaths were followed by at least 1,000 more. For our Russian- and Israeli-origin platforms, plan spares on a multi-year horizon.",
      "So what, from the domain side: a wide static front rewards long-range fires, counter-drone and EW. Lessons for both our fronts."],
     "", f"Maj Mehta will now give our recommendations."),
    (14, "Recommendations 1: sense and warn", M, "10:45", "11:20",
     ["Sir, the commander's intent: see escalation coming a month out, protect Indians and our interests inside the strike envelope, and keep our platforms supplied.",
      "SENSE: task ISR and analysts on the monthly sub-national watch-list, and build Indian OSINT on the Gulf, Iran and the Red Sea. Lead: DIA and Service intelligence.",
      "WARN: adopt the Af–Pak interstate dyad and the KP and Balochistan hotspots as standing LoC indicators, and publish the RAG every month. Lead: HQ IDS, Northern and Western Commands."],
     "", None),
    (15, "Recommendations 2: shield and sustain", M, "11:20", "12:05",
     ["SHIELD: keep Gulf NEO plans current while US–Iran is AMBER, with a belligerent-movement picture in the IOR. Lead: HQ IDS, Navy, IAF and MEA.",
      "SUSTAIN: buffer and indigenise spares for Russian- and Israeli-origin equipment, and build HADR kits for women, children and under-fives. Lead: MoD, DPSUs and NDMA.",
      "SENSE and WARN need no new platform: the model and dashboard already exist."],
     "", None),
    (16, "Execution: who does what, by when", M, "12:05", "12:45",
     ["The table shows who does what, now, in 90 days and in 6 to 12 months.",
      "Column one is only tasking and a briefing format. It can start this month, with no new platform."],
     "", None),
    (17, "Threat scorecard: where to look next month", M, "12:45", "13:45",
     ["To close: the October 2026 scorecard.",
      "Russia–Ukraine RED at 6,780. Af–Pak AMBER, with Kandahar at 23%. US–Iran AMBER, Hormozgan at 16%. Israel–Hamas GREEN.",
      "The QR code opens the live system, which the jury is welcome to use.",
      "Open data and an honest model can tell India where to look next month. Thank you, sir. We welcome your questions."],
     "Leave this slide up during Q&A. 75 seconds of buffer remain to 15:00.", None),
]

QA_ROUTING = [
    ("Data, cleaning, models, metrics, the dashboard", S),
    ("Military meaning, India impact, the LoC and the Gulf", M),
    ("Recommendations, limits, anything else; chairs Q&A and routes questions", H),
]
BACKUPS = [
    ("18", "Conflict signatures", "If asked how the four wars differ: attrition, spikes, creep, decline."),
    ("19", "Attention Gap Index", "If asked about media bias or Indian sources: references follow events, not deaths."),
    ("20", "Humanitarian", "If asked about displacement or HADR: women and children, trigger on escalation flags."),
    ("21", "Synthesis of the twelve files", "If asked whether all datasets were used, or what the extra files add."),
    ("22–24", "GDELT", "If asked what is happening after September, the pre-war tone shift, or why news data is not in the model."),
    ("25–26", "Limits and validation", "If asked what the analysis cannot claim, or whether the 29% gain is significant."),
    ("27", "Model comparison", "If asked 'did the ensemble always win?' Show Track B: SARIMA won there."),
    ("28", "Data quality", "If asked about cleaning: 36 checks, FATA→KP, estimate repairs, month splitting."),
    ("29", "TreeSHAP", "If asked 'what drives the forecast?': last month's level and acceleration."),
    ("30", "Seasons and warning curves", "If asked about campaign seasons or how the warning threshold trades alarms for catches."),
    ("31", "Forward forecast", "If asked about Nov–Dec: RU–UA Nov 6,765 (3,071–30,447)."),
    ("32", "Verification and AI declaration", "If asked how AI was used, or how to check the demo against the submission (run ID)."),
    ("34", "Bootstrap and Diebold–Mariano", "If asked whether the 29% gain is significant, or about late-arriving data."),
    ("35", "Early-warning metrics and calibration", "If asked how reliable the probabilities are: use the list as a ranking."),
    ("36–47", "All 12 dashboard pages", "If the live demo fails, show the page in question from the annex."),
]

def shade(cell, hexcol):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd"); sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcol)
    tcPr.append(sh)


def run(p, t, bold=False, size=11, color=None, italic=False):
    r = p.add_run(t); r.bold = bold; r.italic = italic; r.font.size = Pt(size)
    if color is not None:
        r.font.color.rgb = color
    return r


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(2); sec.top_margin = sec.bottom_margin = Cm(1.6)
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")

# Formation logos in the page header: Corps of Signals 'Jimmy' left, MCTE formation sign right
from docx.enum.text import WD_TAB_ALIGNMENT
sec.header_distance = Cm(0.7)
hp = sec.header.paragraphs[0]
hp.paragraph_format.tab_stops.add_tab_stop(sec.page_width - sec.left_margin - sec.right_margin, WD_TAB_ALIGNMENT.RIGHT)
hp.add_run().add_picture(str(ROOT / "assets" / "logos" / "jimmy_sm.png"), height=Cm(1.6))
hp.add_run("\t")
hp.add_run().add_picture(str(ROOT / "assets" / "logos" / "mcte_sm.png"), height=Cm(1.6))
sec.top_margin = Cm(3.0)

p = doc.add_paragraph(); run(p, "DATA ANALYTICS COMPETITION 2026", True, 10, AMBER)
p = doc.add_paragraph(); run(p, "Conflict Watch: presenter script", True, 22, NAVY)
p = doc.add_paragraph(); run(p, f"{M} · {S} · {H}   |   15-minute slot, target 13:45   |   Deck: Conflict_Watch_Jury_Deck (47 slides: 17 main, 9 support, 5 backup, 16 annex)", False, 10, GREY)

doc.add_heading("Run of show", level=2)
t = doc.add_table(rows=1, cols=4); t.style = "Light Grid Accent 1"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
for c, h in zip(t.rows[0].cells, ["Time", "Slide", "Speaker", "Key line"]):
    c.text = h
blocks = [("0:00–1:30", "1 Cover, 2 BLUF", M, "Error cut by 29% on unseen data; RED, two AMBER, one GREEN; four tasks for India."),
          ("1:30–3:30", "3 Approach, 4 Pipeline, 5 Method", S, "Twelve issued files, 36 checks; the back-test chose the ensemble."),
          ("3:30–5:15", "6–8 Validation on withheld 2026", S, "It beats simple rules, and we show where it does not."),
          ("5:15–7:30", "9 LIVE DEMO (Ops site)", S, "Here is the RED card, and here is where it comes from."),
          ("7:30–10:45", "10–13 Findings 1–3: LoC, Gulf, sustainment", H, "Pakistan fights on two fronts; the war reached the Gulf; it will last."),
          ("10:45–12:45", "14–16 Recommendations", M, "Sense, warn, shield, sustain: SENSE and WARN need no new platform."),
          ("12:45–13:45", "17 Scorecard", M, "Open data and an honest model tell India where to look next month."),
          ("Q&A", "18–26 support, 27–31 backup, 32–47 annex", "All", "Pull the slide that answers the question.")]
for row in blocks:
    cells = t.add_row().cells
    for c, v in zip(cells, row):
        c.text = v
p = doc.add_paragraph(); run(p, "Speaking pace: about 140 words a minute. About 9.5 minutes of speech plus demo clicks and pauses. Each slide lists what to say, what to do on screen, and the handover line. Present from the PPTX in slideshow mode: transitions (Morph) and build-ins play by themselves in about 3 seconds, so never click to reveal. The PDF copy is fully built and static.", False, 9.5, GREY, True)

doc.add_heading("Before you start (T−15 minutes)", level=2)
for b in [f"Open {URL} and let it wake (it sleeps after a few idle days). Scroll the story once so every chart is drawn.",
          "Open the console in a second tab and press Ctrl+K once.",
          "Keep deck/conflictwatch.html (offline copy) and the demo video deck/Conflict_Watch_Demo.mp4 ready as fall-backs.",
          "Google Meet: share one Chrome window at about 1600×900, browser zoom 110–125%. Notifications off; wired network.",
          "Press P on the site for presenter mode: 15-minute timer turns amber at 12:00 and red at 14:00. N opens speaker notes."]:
    doc.add_paragraph(b, style="List Bullet")

doc.add_page_break()
for n, title, who, t0, t1, say, do, hand in SLIDES:
    tb = doc.add_table(rows=1, cols=1); c = tb.rows[0].cells[0]; shade(c, "07131F")
    cp = c.paragraphs[0]
    run(cp, f"SLIDE {n}   ", True, 10, RGBColor(0xF0, 0xB0, 0x3A)); run(cp, title, True, 12.5, RGBColor(0xFF, 0xFF, 0xFF))
    cp2 = c.add_paragraph(); run(cp2, f"{who}   ·   {t0}–{t1}", False, 9.5, RGBColor(0x9F, 0xB2, 0xC6))
    for line in say:
        q = doc.add_paragraph(style="List Bullet"); q.paragraph_format.space_after = Pt(2)
        if line.startswith("("):
            k = line.index(")") + 1
            run(q, line[:k] + " ", True, 11, AMBER); run(q, line[k:].strip(), False, 11)
        else:
            run(q, line, False, 11)
    if do:
        q = doc.add_paragraph(); run(q, "ON SCREEN: ", True, 9.5, RGBColor(0x1F, 0x7A, 0x8C)); run(q, do, False, 9.5, GREY, True)
    if hand:
        q = doc.add_paragraph(); run(q, "HANDOVER: ", True, 10, RED); run(q, f"“{hand}”", True, 10)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)

doc.add_heading("Q&A: who answers what", level=2)
for topic, who in QA_ROUTING:
    q = doc.add_paragraph(style="List Bullet"); run(q, who + ": ", True); run(q, topic)
doc.add_paragraph("Answer in one sentence first, then one number, then stop. If unsure: “We did not test that; the data would need X.”")
doc.add_heading("Backup slides to jump to", level=2)
bt = doc.add_table(rows=1, cols=3); bt.style = "Light Grid Accent 1"
for c, h in zip(bt.rows[0].cells, ["Slide", "Topic", "Use when"]):
    c.text = h
for row in BACKUPS:
    cells = bt.add_row().cells
    for c, v in zip(cells, row):
        c.text = v
doc.add_heading("Six likely questions", level=2)
for q, a in [("Did you tune on 2026?", "No. Every choice was made on the 2022–25 back-test; 2026 was scored once. (Sangwan)"),
             ("Is the 10:1 ratio real?", "It is what UCDP recorded: an upper bound of reporting, not a verified exchange ratio. (Mehta)"),
             ("Why could you not predict the US–Iran war?", "It began by decision with no build-up in deaths; no death-count model can see that. So we watch spread and hotspots. (Sangwan)"),
             ("Is the map correct?", "Every map uses the India point-of-view boundary: all of J&K and Ladakh, including PoK and Aksai Chin, shown as India. (Mehta)"),
             ("Why is GDELT not in the model?", "It tracks UCDP only in spike wars, adds nothing a week ahead (p 0.55) and lost to persistence out of sample. We use it to watch past UCDP's cut-off. (Sangwan)"),
             ("What would you do first with this?", "Start SENSE and WARN this month: tasking and a monthly RAG brief, no new platform. (Singh)")]:
    pq = doc.add_paragraph(); run(pq, q, True)
    doc.add_paragraph(a)
doc.save(OUT)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT.parent), str(OUT)], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
words = sum(len(" ".join(s[5]).split()) for s in SLIDES)
print(OUT, OUT.with_suffix(".pdf"), f"{words} spoken words ≈ {words / 140:.1f} min at 140 wpm")
