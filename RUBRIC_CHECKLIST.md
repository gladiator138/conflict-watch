# Rubric self-audit (100 marks)

Each line names where the judges will find the evidence.

| Criterion (marks) | What we deliver | Where |
|---|---|---|
| Problem framing (5) | Operational question for an Army audience; five sub-questions; DATA and DOMAIN tags on every claim | Report §2; deck slides 2–3 |
| Cleaning / imputation (10) | 36 logged checks; raw values kept beside fixes; day-weighted month allocation; FATA→KP harmonisation; publisher normalisation; World Bank interpolation; provisional 2026 flagged | `outputs/tables/data_quality_log.csv`; notebook 01; report §3 and App. A; dashboard page 12 |
| Feature engineering (5) | Two panels (4 conflicts, 222 area series); nine feature families with a military rationale; no leakage (features known at origin; context lagged 1 year); ablation | Notebook 02; report §4 and §7.2; `src/features.py` |
| EDA (10) | Intensity, tempo, seasonality, front geography, attrition, spread, Af–Pak interstate front, fog of war, displacement, demographics | Notebook 03; report §5; dashboard pages 2–7 |
| Actionable insights (15) | India impact table; Sense/Warn/Shield/Sustain with lead agencies and Now/90 days/6–12 months; RAG scorecard; watch-list | Report §6, §9; commander's brief; deck slides 13–14, 16 |
| Model choice / justification (8) | 7 models from naive to LightGBM-Δ and bottom-up; ablation explains the change target; ensemble chosen on back-test only | Report §7.1–7.2; deck backup "Why each method"; notebook 04 |
| Performance incl. withheld data (12) | 2026 holdout scored once; two tracks; MAE, RMSE, MAPE, sMAPE, MASE, RMSLE; −29% error vs naive; classifier AUC 0.79 vs 0.73 rule | Report §7.3, §8.1; `forecast_scores.csv`; dashboard pages 8–9 |
| Reliability for trend forecasting (5) | Conformal intervals (83% inside 80% band); direction accuracy 72%; stability by fold; SHAP; known failure mode stated | Report §7.4; deck slide 15 |
| Originality (5) | Attention Gap Index; fog-of-war finding; change-target LightGBM; sub-national escalation warning; India exposure tagging; what-if and live re-train | Report §5.3, §8; dashboard pages 3, 7, 9, 10, 11 |
| Dashboards / visualisation (5) | 12-page offline Streamlit dashboard in the deck's theme with drill-down, live thresholds, scenario and rule sliders, animation and CSV downloads; 31 figures (PNG + interactive HTML) | `app/app.py`; `outputs/figures/` |
| Report / reproducibility (5) | 17-page report; one-command pipeline (about 1–2.5 min); fixed seeds; README; requirements; executed notebooks; verified to run from the project folder | `report/`; `README.md`; `run_pipeline.py` |
| Presentation / storytelling (10) | 16-slide deck + 6 backups in the reference style, large fonts for Meet; BLUF → findings → prediction → recommendations → scorecard | `deck/Conflict_Watch_Jury_Deck.pptx` / `.pdf` |
| Q&A / teamwork (5) | 22 prepared answers; speaker split; run of show; backup demo video | `brief/QA_Prep_and_Speaker_Split.pdf`; `deck/Conflict_Watch_Demo.mp4` |
