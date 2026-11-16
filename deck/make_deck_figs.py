"""Re-export the deck's charts at slide proportions with large fonts (legible over a video call).

    python deck/make_deck_figs.py   ->  deck/figs/*.png   (needs the outputs of run_pipeline.py)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config as C, insights, viz  # noqa: E402
from src.cleaning import load  # noqa: E402

OUT = ROOT / "deck" / "figs"
OUT.mkdir(exist_ok=True)
if "BROWSER_PATH" not in os.environ:
    import glob
    c = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux64/chrome")
    if c:
        os.environ["BROWSER_PATH"] = c[0]


def big(fig, w_in, h_in, name, font=19, legend=True, keep_title=False, px_per_in=150, ml=70):
    fig.update_layout(font=dict(size=font), legend=dict(font=dict(size=font - 2)), showlegend=legend,
                      margin=dict(l=ml, r=30, t=60 if keep_title else 30, b=60))
    fig.update_annotations(font_size=font - 1)
    if not keep_title:
        fig.update_layout(title_text="")
    fig.update_xaxes(tickfont=dict(size=font - 2), title_font=dict(size=font - 1))
    fig.update_yaxes(tickfont=dict(size=font - 2), title_font=dict(size=font - 1))
    fig.write_image(OUT / f"{name}.png", width=int(w_in * px_per_in), height=int(h_in * px_per_in), scale=2)


ins = insights.run(save=False)
cm = pd.read_parquet(C.PROCESSED / "case_month.parquet")
preds = pd.read_parquet(C.PROCESSED / "forecast_preds.parquet")
future = pd.read_parquet(C.PROCESSED / "forecast_future.parquet")
e = load("events")

big(viz.fig_monthly_deaths(cm), 8.3, 4.8, "monthly_deaths")
big(viz.fig_front_geography(ins["front_geography"]), 8.3, 4.8, "front_geography", font=18)
big(viz.fig_afpak_interstate(e), 8.3, 2.45, "afpak_interstate", font=17)
big(viz.fig_afpak(ins["afpak_provinces"]), 8.3, 2.45, "afpak_provinces", font=16)
big(viz.fig_media_scatter(ins["media"]), 8.3, 4.8, "media_scatter")
big(viz.fig_displacement(ins["displacement"]), 8.3, 4.8, "displacement", font=16)
big(viz.fig_forecast_case(cm, preds, "Russia–Ukraine", track="A", future=future), 8.3, 2.45, "forecast_ru", font=16,
    keep_title=True)
big(viz.fig_forecast_case(cm, preds, "Afghanistan–Pakistan", track="A", future=future), 8.3, 2.45, "forecast_afpak",
    font=16, keep_title=True)
m = viz.fig_country_map(ins["country_deaths"])
m.update_layout(title_text="", margin=dict(l=0, r=0, t=0, b=0))
m.write_image(OUT / "map.png", width=1110, height=730, scale=2)
print("deck figures:", sorted(p.name for p in OUT.glob("*.png")))

# backup slides
rmsle = pd.read_csv(C.TAB_DIR / "forecast_rmsle.csv")
big(viz.fig_model_compare(rmsle), 7.4, 5.0, "model_compare", font=14, ml=330)
big(viz.fig_shap(pd.read_csv(C.TAB_DIR / "shap_lgb_case.csv"), title="Forecast (LightGBM-Δ)"), 6.0, 4.9,
    "shap_forecast", font=15, keep_title=True, ml=190, legend=False)
big(viz.fig_shap(pd.read_csv(C.TAB_DIR / "shap_early_warning.csv"), title="Escalation warning"), 6.0, 4.9,
    "shap_ew", font=15, keep_title=True, ml=190, legend=False)
big(viz.fig_seasonality(ins["seasonality"]), 12.2, 2.6, "seasonality", font=15, ml=190)
big(viz.fig_ew_curves(pd.read_parquet(C.PROCESSED / "early_warning_preds.parquet")), 12.2, 2.95, "ew_curves", font=15)
print("backup figures done")
