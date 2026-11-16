# CONFLICT WATCH – Data Analytics Competition 2026

**When and where will conflict deaths rise next, and what does it mean for India?**
Russia–Ukraine · Israel–Hamas · Afghanistan–Pakistan · US–Iran

Team: Maj Shivam Mehta · Capt Siddharth Sangwan · Capt Sahil Singh · UNCLASSIFIED: open-source data only

---

## What is in this folder

| Path | What it is |
|---|---|
| `report/Conflict_Watch_Report.pdf` | Full analysis report: method, results, assumptions and limitations (17 pages) |
| `deck/` | Presentation deck (PPTX + PDF), commander's brief, Q&A prep sheet, demo-video script |
| `app/app.py` | Interactive Streamlit dashboard used for the live demo (12 pages, works offline) |
| `notebooks/01–05` | Executed notebooks: cleaning, features, EDA (military + India), forecasting, early warning |
| `src/` | All pipeline code: `cleaning`, `features`, `insights`, `models`, `viz`, `config` |
| `run_pipeline.py` | One command that reproduces every table, model and figure |
| `outputs/tables/` | Every number quoted anywhere, as CSV (incl. `data_quality_log.csv`) |
| `outputs/figures/` | 31 figures as PNG and interactive HTML |
| `models/models.joblib` | Fitted forecaster, ensemble members, conformal intervals and early-warning classifier |

## Data

Only the **official participant package** is used:
`final dataset/7. scraped data/for participants/data/*.csv`
(UCDP GED 26.1 + Candidate 26.01.26.09, source references, UNHCR bilateral and demographics,
IDMC/UNRWA reference stocks, World Bank context). Source files are read-only and are never modified.

The data folder is found automatically by searching up to six levels above this folder for
`for participants/data`. To point elsewhere:

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
