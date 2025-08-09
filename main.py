
import os, json, csv, sys, time
from datetime import datetime
from dateutil import tz
import requests

ALPHA_URL = "https://www.alphavantage.co/query"
API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def fetch_daily_close(symbol, use_adjusted=False):
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED" if use_adjusted else "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY
    }
    r = requests.get(ALPHA_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    key = "Time Series (Daily)"
    if key not in data:
        raise RuntimeError(f"Alpha Vantage error for {symbol}: {data}")
    ts = data[key]
    # Latest trading day (sorted desc)
    latest_date = sorted(ts.keys())[-1]
    close_key = "4. close" if not use_adjusted else "5. adjusted close"
    close = float(ts[latest_date][close_key])
    return latest_date, close

def to_tz(dt_utc, tzname):
    tz_to = tz.gettz(tzname)
    return dt_utc.astimezone(tz_to)

def main():
    if not API_KEY:
        print("Missing ALPHAVANTAGE_API_KEY")
        sys.exit(1)

    cfg = load_json("config.json")
    state = load_json("state/portfolio_state.json")
    symbols = cfg["symbols"]
    use_adj = cfg.get("use_adjusted_close", False)
    stops = cfg["stops"]
    holdings = state["holdings"]
    cash = float(state["cash"])

    latest_prices = {}
    latest_date = None

    # rate limiting: 5 req/min free plan; we'll sleep between calls
    for i, sym in enumerate(symbols):
        d, px = fetch_daily_close(sym, use_adjusted=use_adj)
        latest_prices[sym] = px
        latest_date = d if latest_date is None else max(latest_date, d)
        if i < len(symbols) - 1:
            time.sleep(15)  # polite gap to avoid hitting the per-minute cap

    # Apply stop-loss on a closing basis (if price <= stop -> sell all at close)
    actions = []
    for sym in symbols:
        stop = float(stops[sym])
        if holdings.get(sym, 0) > 0 and latest_prices[sym] <= stop:
            qty = int(holdings[sym])
            proceed = qty * latest_prices[sym]
            cash += proceed
            holdings[sym] = 0
            actions.append(f"STOP SELL {sym} {qty} @ {latest_prices[sym]:.4f}")

    # Compute portfolio value
    position_values = {sym: int(holdings.get(sym, 0)) * latest_prices[sym] for sym in symbols}
    total_value = float(cash) + sum(position_values.values())

    # CSV append
    os.makedirs("data", exist_ok=True)
    csv_path = "data/portfolio_history.csv"
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["date","cash"] + [f"{s}_close" for s in symbols] + [f"{s}_qty" for s in symbols] + [f"{s}_value" for s in symbols] + ["total_value","actions"])
        w.writerow([latest_date, f"{cash:.2f}"] +
                   [f"{latest_prices[s]:.4f}" for s in symbols] +
                   [int(holdings.get(s,0)) for s in symbols] +
                   [f"{position_values[s]:.2f}" for s in symbols] +
                   [f"{total_value:.2f}", "; ".join(actions)])

    # Persist state
    state["cash"] = round(cash, 2)
    state["holdings"] = holdings
    state["last_valuation_date"] = latest_date
    save_json("state/portfolio_state.json", state)

    # Report
    os.makedirs("reports", exist_ok=True)
    with open("reports/latest_report.md", "w", encoding="utf-8") as f:
        f.write(f"# Portfolio Report\\n")
        f.write(f"**As of (latest close)**: {latest_date}\\n\\n")
        for sym in symbols:
            f.write(f"- {sym}: close {latest_prices[sym]:.4f}, qty {holdings.get(sym,0)}, value ${position_values[sym]:.2f}\\n")
        f.write(f"\\nCash: ${cash:.2f}\\n")
        f.write(f"**Total value**: ${total_value:.2f}\\n")
        if actions:
            f.write(f"\\n**Actions**: {', '.join(actions)}\\n")

    # Update docs (simple injection)
    try:
        with open("docs/index.html", "r", encoding="utf-8") as f:
            html = f.read()
        summary = f"<p><strong>Date:</strong> {latest_date} &nbsp; <strong>Total:</strong> ${total_value:.2f}</p>"
        with open("docs/index.html", "w", encoding="utf-8") as f:
            f.write(html.replace('id=\"summary\">Latest report will appear here after first run.', f'id=\"summary\">{summary}'))
    except Exception as e:
        print("Docs update skipped:", e)

    print(f"OK {latest_date} total ${total_value:.2f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
