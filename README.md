# CONFLICT WATCH – Data Analytics Competition 2026

**When and where will conflict deaths rise next, and what does it mean for India?**
Russia–Ukraine · Israel–Hamas · Afghanistan–Pakistan · US–Iran

Team: Maj Shivam Mehta · Capt Siddharth Sangwan · Capt Sahil Singh · UNCLASSIFIED: open-source data only

**Live dashboard:** https://conflictmonitor2026.streamlit.app

---

## What is in this folder

| Path | What it is |
|---|---|
| `report/Conflict_Watch_Report.pdf` | Full analysis report: method, results, assumptions and limitations (10 pages + appendices); footer carries the run ID |
| `deck/` | Presentation deck (PPTX + PDF), commander's brief, Q&A prep sheet, demo-video script |
| `app/app.py` | Hosted app: opens on the Ops site; classic 12-page Streamlit dashboard in *Analyst dashboard* mode |
| `web/`, `scripts/export_web.py` | Ops site source (Vite + TypeScript + ECharts + d3-geo) and its data export with asserts |
| `notebooks/01–05` | Executed notebooks: cleaning, features, EDA (military + India), forecasting, early warning |
| `src/` | All pipeline code: `cleaning`, `features`, `insights`, `models`, `viz`, `config` |
| `run_pipeline.py` | One command that reproduces every table, model and figure |
| `score_holdout.py` | Scores the frozen Oct–Dec 2026 forecasts and watch-list against new UCDP events, with no refit (`--events FILE`, `--selftest`) |
| `src/robustness.py` | Evidence strength: month-block bootstrap, Diebold–Mariano, late-data test, warning calibration → `outputs/tables/robustness.json` |
| `src/gdelt.py`, `data/gdelt/` | GDELT media-coded events (Feb–12 Nov 2026) as compact aggregates plus the script that built them; compared with UCDP as **new, separately labelled** results |
| `outputs/tables/run_id.txt` | Run ID (hash of every result table) printed on the report, deck, dashboard and Ops site |
| `outputs/tables/` | Every number quoted anywhere, as CSV (incl. `data_quality_log.csv`) |
| `outputs/figures/` | 34 figures as PNG and interactive HTML |
| `models/models.joblib` | Fitted forecaster, ensemble members, conformal intervals and early-warning classifier |

## Data

Only the **official participant package** is used, and it is bundled in this repository under
`data/raw/for participants/` (`data/*.csv` and `documentation/`): UCDP GED 26.1 + Candidate 26.01.26.09,
source references, UNHCR bilateral and demographics, IDMC/UNRWA reference stocks and World Bank context.
Licences and attributions are in `data/raw/for participants/documentation/Sources_and_Licenses.md`
(UCDP data are CC BY 4.0). Source files are read-only and are never modified.

To use a copy stored elsewhere:

```bash
export CONFLICT_DATA_DIR="/path/to/for participants/data"
```

## Run it

```bash
pip install -r requirements-dev.txt   # or requirements.txt for the dashboard only

python run_pipeline.py            # about 2.5 min: clean → features → insights → models → scorecard → figures
streamlit run app/app.py          # dashboard at http://localhost:8501
jupyter lab notebooks/            # 01–05, each re-runs its stage with commentary

python report/build_report.py     # rebuild the report (Markdown + HTML) from the output tables
NODE_PATH=$(npm root -g) node report/to_pdf.js   # optional HTML → PDF (needs Node + Playwright)
python deck/build_deck.py         # rebuild the slide deck
```

The dashboard needs the outputs of `run_pipeline.py` (already included). It makes no internet calls.
Its maps use a bundled Natural Earth outline (`assets/world_lowres.geojson`).

## Ops site (story website + ops console)

The hosted app opens on the **Ops site**: a scroll-driven briefing (14 chapters) and a staff-officer console
(Brief, Map, Area, Forecast, Warning, What-if, Scorecard, Data quality), in a dark ops-room design.
The classic 12-page Streamlit dashboard is one click away in the sidebar (*Analyst dashboard*).

```bash
python scripts/export_web.py     # frozen outputs -> web/public/data; asserts every headline number (fails on any mismatch)
python scripts/build_site.py     # Vite build -> app/static/site/ (PWA, works offline) + app/static/conflictwatch.html (single file)
cd web && npm run dev            # live development server
```

* Every number comes from `web/public/data/facts.json`, generated from `outputs/tables`. The what-if simulator ships the
  exact Python ensemble output for every slider position (Af–Pak +30% × 3 months = 359, asserted).
* Maps draw India's boundary from Natural Earth's India point-of-view layer; PoK areas are shown as points inside it.
* Keys: **P** presenter mode (15-min timer, arrows jump chapters), **N** speaker notes, **Ctrl/⌘ K** command palette in the console.
* `deck/conflictwatch.html` is the single-file offline backup. `DEMO_SCRIPT.md` is the 3-minute live-demo walkthrough.

## Method in one paragraph

36 data-quality checks are logged and acted on. Examples: out-of-order estimates are repaired in new columns,
multi-month records are spread across months by day, FATA is harmonised into Khyber Pakhtunkhwa, and publishers are
normalised. The data become two monthly panels: 4 conflicts and 222 sub-national area series, from Jan 2014 to Sep 2026.
Seven forecasters are compared: naive, seasonal naive, 3-month mean, ETS, SARIMA, a global LightGBM on the *change* in
log deaths, and a bottom-up Tweedie LightGBM. They are scored with a walk-forward back-test (2022–2025) and **2026 is
the withheld test set**. The ensemble (3-month mean + ETS + LightGBM-Δ) is chosen on the back-test only. Split-conformal
intervals cover 83% of 2026 outcomes at 80%. A sub-national escalation classifier (ROC-AUC 0.79 on 2026, top-10
precision 3.5× the base rate) feeds a transparent Red/Amber/Green threat scorecard and a what-if simulator.

## Reproducibility notes

* Random seed fixed (`random_state = 42`); LightGBM runs deterministically on CPU.
* All design choices (features, ensemble members, interval bands, classifier features) were made on the
  2022–2025 back-test folds. 2026 was scored once.
* Every figure and number in the report and deck is read from `outputs/tables/`.
* The run ID (`outputs/tables/run_id.txt`) is a SHA-256 hash of those tables. If the ID on the deck, report, dashboard
  and Ops site match, they show the same run.
* GDELT does not change the submitted models: it tracks UCDP only in spike wars, adds nothing a week ahead and
  did not beat persistence out of sample. It is used to watch Oct–Nov 2026, past UCDP's Sep 2026 end.
