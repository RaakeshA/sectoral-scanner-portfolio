import pandas as pd
import yfinance as yf
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]     # .../Sectoral_Scanner
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"

TICKER_FILE = CONFIG_DIR / "tickers.txt"

# 1) Load tickers
if not TICKER_FILE.exists():
    print(f"❌ Ticker file not found: {TICKER_FILE}")
    raise SystemExit

with TICKER_FILE.open("r", encoding="utf-8") as f:
    tickers = [line.strip() for line in f if line.strip()]

if not tickers:
    print("❌ No tickers found in tickers.txt")
    raise SystemExit

print("✅ Tickers to download:", tickers)

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 2) Download each ticker
for ticker in tickers:
    print(f"\n📥 Downloading daily data for {ticker}...")

    try:
        data = yf.download(
            ticker,
            start="2021-01-01",       # only from 2021 onwards
            interval="1d",
            auto_adjust=False,
            progress=False
        )

        if data.empty:
            print(f"  ⚠ No data received for {ticker}. Skipping.")
            continue

        data = data.reset_index()
        safe_name = ticker.replace(".", "_")

        out_path = DATA_DIR / f"{safe_name}.csv"
        data.to_csv(out_path, index=False)

        print(f"  ✅ Saved {len(data)} rows to {out_path}")

    except Exception as e:
        print(f"  ❌ Error downloading {ticker}: {e}")
