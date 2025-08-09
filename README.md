
# Micro-cap Portfolio Tracker (Alpha Vantage)

Tracks daily prices for KLTR, LUNG, STTK, MX, TUSK using Alpha Vantage, computes portfolio value,
checks stop-losses, and appends results to `data/portfolio_history.csv`. Designed to run via GitHub Actions daily.

## What it does
- Calls Alpha Vantage `TIME_SERIES_DAILY` for each symbol.
- Uses **closing price** of the latest available trading day.
- Computes marked-to-market value for fixed share-counts.
- Applies stop-loss rules on a **closing basis**. If close <= stop, the position is sold at close and cash increases.
- Persists state (holdings and cash) in `state/portfolio_state.json`.
- Appends one row per run to `data/portfolio_history.csv`.
- Writes a human-readable report to `reports/latest_report.md`.
- Optional: publishes a minimal `docs/index.html` with the latest snapshot (for GitHub Pages).

## Initial portfolio (as of 2025-08-09)
- STTK 80 @ close
- LUNG 60 @ close
- KLTR 100 @ close
- MX   120 @ close
- TUSK 145 @ close
- Cash: 9.20 USD

Stops (closing basis):
- STTK: 0.60
- LUNG: 1.25
- KLTR: 1.40
- MX:   2.10
- TUSK: 1.80

## Setup (GitHub)
1. Create a new **private** GitHub repo. Upload the contents of this zip.
2. Go to **Settings → Secrets and variables → Actions → New repository secret** and add:
   - `ALPHAVANTAGE_API_KEY` = your key
3. Enable GitHub Pages (optional) if you want the HTML published from `/docs`.
4. The workflow in `.github/workflows/schedule.yml` will run **daily**.

## Local run (optional)
```bash
pip install -r requirements.txt
export ALPHAVANTAGE_API_KEY=Q3YFKEOTYSH3CN43
python main.py
```

## Outputs to check
- `data/portfolio_history.csv` → append-only daily history (date, prices, value, P/L).
- `reports/latest_report.md` → snapshot summary.
- `docs/index.html` → simple HTML summary (if GitHub Pages enabled).

## How I'll read it
Publish the CSV (either via GitHub Pages or as a raw file in a public repo).
I will fetch it daily and report to you without you doing anything.
