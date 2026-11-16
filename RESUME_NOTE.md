# Resume note (final merge, paused 16 Nov 2026)

## Done
- Logos (Corps of Signals Jimmy top left, MCTE top right) on every slide, all four documents, the Streamlit app and the Ops site. Pushed to main (commit "Add Corps of Signals and MCTE logos...").
- Footer wording: COMPETITION DATA ONLY.
- Deck moved to the team's v4 order (`deck/build_deck.py`, RUNNING list at the end): 17 main + 9 support + 5 backup + 16 annex = 47 slides. The v4 synthesis and GDELT pre-war slides were added with v4 numbers still hard-coded.
- Extra files D9–D12 copied to `data/raw/extra/`. The GDELT pair and ActionGeo aggregates are in `data/gdelt/`.
- `src/extra_sources.py` (wired into run_pipeline.py) recomputes the v4 D7–D12 figures and writes `outputs/tables/extra_sources.json`.
- `report/build_report.py` merges the v4 content: the D1–D12 table and audits, the India mandates in the BLUF, §5.6 synthesis, the precursor-trial recommendation, and Appendix C self-verification.

## Recomputed vs v4 (to flag to Siddharth)
- Reproduced exactly: 27,646 Iran unrest deaths; Gulf 9 → 322; Indian Ocean 60 → 74; 100% of 15 ≥10k years persist; 4.9% of quiet years escalate; 8% Af–Pak case scope; 99.5% D1 events in D10; 936 → 930 reports/day; Goldstein +0.71 → −0.10; Ukraine 7 and Russia 1,593 events per death; Pakistan 310 → 2,361; 685 interstate deaths.
- Differ:
  - strategic developments ×5.1 (v4 ×5.6);
  - Goldstein p 0.007 (v4 0.005);
  - Kuwait 0.8 → 58/day (v4 0.4 → 50);
  - ρ Israel+Palestine 0.87 (v4 0.86);
  - Iran UCDP vs protests ρ −0.05 (v4 0.02);
  - weekly lead: Af–Pak p 0.02 alone, failing a 4-test correction (v4 "p ≥ 0.23 in all four");
  - October direction agrees 4/4 (v4 2/4);
  - TTP 2021 → 2025: 259 → 2,226 (v4 2,268);
  - bootstrap interval 2–41% (v4 5–47%, an older hand calculation);
  - D11 panel matches D10 start-month totals in 100% (v4 "86% of 2,199").
- v4 build scripts were not found on the laptop, so v4-only figures can't be reproduced.

## Next
1. Fix the pre-war volume p-value in extra_sources.py (use a t-test; it currently prints p = 1.00). Add Iran 2025 inflation 42% (D6, context.parquet) to §5.6.
2. Replace the hard-coded numbers on the deck synthesis and GDELT pre-war slides with values from extra_sources.json. Update the approach slide refs if the order changes.
3. Merge the v4 text into `brief/build_docs.py` (Q&A: twelve-file questions, 13:30 run of show, v4 speaker split with Sahil on the India findings and Mehta opening and closing) and into `brief/build_script.py` (new slide order 1–17, timings).
4. `python3 run_pipeline.py` (new run ID), then run the full rebuild chain (see the memory file submission-state.md). Check the numbers and run ID on every output, then commit, push and sync to /mnt/project-files/Data Analytics/submission/.
