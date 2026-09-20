import pandas as pd
from pathlib import Path

# -------- Base paths (portable) --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
TICKER_FILE = CONFIG_DIR / "tickers.txt"

# Trading-day approximations
DAYS_1M = 21
DAYS_3M = 63

# 1) Read tickers
if not TICKER_FILE.exists():
    print(f"❌ Ticker file not found: {TICKER_FILE}")
    raise SystemExit

with TICKER_FILE.open("r", encoding="utf-8") as f:
    tickers = [line.strip() for line in f if line.strip()]

if not tickers:
    print("❌ No tickers in tickers.txt")
    raise SystemExit

print("✅ Tickers loaded:", tickers)

rows = []

# 2) Process each ticker
for ticker in tickers:
    safe_name = ticker.replace(".", "_")
    csv_path = DATA_DIR / f"{safe_name}.csv"

    if not csv_path.exists():
        print(f"⚠ Data file missing for {ticker}: {csv_path}")
        continue

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"❌ Error reading {csv_path}: {e}")
        continue

    # Ensure Date column
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif "timestamp" in df.columns:
        df["Date"] = pd.to_datetime(df["timestamp"], errors="coerce")
    else:
        print(f"⚠ No 'Date' or 'timestamp' column in {csv_path}, skipping {ticker}")
        continue

    df = df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)

    # Keep only data from 2021 onwards
    df = df[df["Date"] >= "2021-01-01"]

    # Fix Close column for numeric errors
    if "Close" not in df.columns:
        print(f"⚠ No 'Close' column in {csv_path}, skipping {ticker}")
        continue

    # Clean & convert Close to numeric
    df["Close"] = (
        df["Close"]
        .astype(str)               # convert everything to string
        .str.replace(",", "", regex=False)  # remove commas if any
    )
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"])

    if len(df) < DAYS_3M + 1:
        print(f"⚠ Not enough data for 3M return: {ticker}")
        continue

    last_close = float(df.iloc[-1]["Close"])
    last_date = df.iloc[-1]["Date"]

    price_1m = float(df.iloc[max(0, len(df) - 1 - DAYS_1M)]["Close"])
    price_3m = float(df.iloc[max(0, len(df) - 1 - DAYS_3M)]["Close"])

    ret_1m = (last_close - price_1m) / price_1m * 100.0
    ret_3m = (last_close - price_3m) / price_3m * 100.0

    rows.append(
        {
            "ticker": ticker,
            "last_date": last_date,
            "last_close": last_close,
            "ret_1m_pct": ret_1m,
            "ret_3m_pct": ret_3m,
        }
    )

# 3) Save summary
if not rows:
    print("❌ No valid data to save.")
    raise SystemExit

summary_df = pd.DataFrame(rows).sort_values("ret_3m_pct", ascending=False)

out_path = DATA_DIR / "stock_strength.csv"
summary_df.to_csv(out_path, index=False)

print(f"\n✅ Saved stock strength summary to {out_path}")

# NEW: show what the latest date is across all stocks
try:
    max_date = pd.to_datetime(summary_df["last_date"]).max()
    print(f"📅 Max last_date across all stocks: {max_date}")
except Exception as e:
    print(f"⚠ Could not compute max_date: {e}")

print(summary_df.head())
