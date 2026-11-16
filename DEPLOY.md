# Hosting the dashboard

## GitHub
1. Create an empty repository on GitHub (no README, no licence), for example `conflict-watch`.
2. From this folder:
   ```bash
   git remote add origin https://github.com/<account>/conflict-watch.git
   git push -u origin main
   ```
The repository contains everything: the raw competition CSVs (`data/raw/for participants/`), processed data (`data/processed`), result tables (`outputs/tables`), fitted models (`models/`) and the map outline (`assets/`). A fresh clone can run the dashboard at once, or rebuild everything with `python run_pipeline.py`.

## Streamlit Community Cloud (free, public URL)
1. Go to share.streamlit.io and sign in with the GitHub account that owns the repository.
2. **Create app** → pick the repository, branch `main`, main file `app/app.py`.
3. **Advanced settings** → Python version **3.13**. No secrets are needed.
4. Deploy. The first build takes about 3–5 minutes; the app then has a URL such as
   `https://conflict-watch.streamlit.app`.
5. Put that URL (or the repository URL) into `QR_URL` at the top of `deck/build_deck.py` and run
   `python deck/build_deck.py` to print the QR code on the closing slide.

The app reads only files in the repository and makes no outbound calls, so it behaves the same hosted or on a laptop.
For the live presentation, keep the local copy (`streamlit run app/app.py`) running as the fallback.
