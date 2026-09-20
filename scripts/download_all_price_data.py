import os
import time
from datetime import date, timedelta
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import yfinance as yf

# ---------------- CONFIG ----------------
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

UNIVERSE_PATH = CONFIG_DIR / "stock_sector_map.csv"

START_YEAR = 2025
SLEEP_BETWEEN_REQUESTS = 0.3
MAX_RETRIES = 3
RETRY_DELAY = 2
MAX_WORKERS = 4   # Yahoo-safe

UPDATED_TICKERS_FILE = DATA_DIR / "updated_tickers_today.txt"

# ---------------- HELPERS ----------------
def get_today():
    return date.today()

def get_last_trading_day():
    today = get_today()
    if today.weekday() == 5:
        return today - timedelta(days=1)
    if today.weekday() == 6:
        return today - timedelta(days=2)
    return today

def clean_yf_df(df_raw: pd.DataFrame) -> pd.DataFrame:
    if df_raw is None or df_raw.empty:
        return pd.DataFrame()

    df = df_raw.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    df = df.reset_index()

    if "Date" not in df.columns:
        df = df.rename(columns={df.columns[0]: "Date"})

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()]
    df["Date"] = df["Date"].dt.tz_localize(None)

    return df.sort_values("Date").reset_index(drop=True)

def download_with_retry(ticker, start, end):
    for attempt in range(MAX_RETRIES):
        try:
            df = yf.download(
                ticker,
                start=start,
                end=end,
                interval="1d",
                auto_adjust=False,
                progress=False,
            )
            if not df.empty:
                return df
        except Exception:
            pass

        time.sleep(RETRY_DELAY * (attempt + 1))
    return None

# ---------------- LOAD UNIVERSE ----------------
if not UNIVERSE_PATH.exists():
    print("❌ stock_sector_map.csv missing")
    sys.exit(1)

tickers = (
    pd.read_csv(UNIVERSE_PATH)["ticker"]
    .dropna()
    .unique()
    .tolist()
)

DATA_DIR.mkdir(exist_ok=True)

last_trading_day = get_last_trading_day()
updated_tickers = []
any_new_data = False

# ---------------- PER-TICKER LOGIC ----------------
def process_ticker(ticker):
    global any_new_data

    safe = ticker.replace(".", "_")
    path = DATA_DIR / f"{safe}.csv"

    # Load existing
    if path.exists():
        df_old = pd.read_csv(path)
        df_old["Date"] = pd.to_datetime(df_old["Date"], errors="coerce")
        df_old = df_old.dropna(subset=["Date"])
        df_old = df_old[df_old["Date"] >= f"{START_YEAR}-01-01"]
        df_old = df_old.sort_values("Date")
    else:
        df_old = pd.DataFrame()

    # Case 1: Full download
    if df_old.empty:
        df_raw = download_with_retry(
            ticker,
            f"{START_YEAR}-01-01",
            (get_today() + timedelta(days=1)).strftime("%Y-%m-%d"),
        )
        if df_raw is None:
            return

        df_new = clean_yf_df(df_raw)
        if not df_new.empty:
            df_new.to_csv(path, index=False)
            updated_tickers.append(ticker)
            any_new_data = True
        return

    # Case 2: Incremental
    last_local_date = df_old["Date"].max().date()
    if last_local_date >= last_trading_day:
        return

    start_new = last_local_date + timedelta(days=1)
    end_new = get_today() + timedelta(days=1)

    df_raw = download_with_retry(
        ticker,
        start_new.strftime("%Y-%m-%d"),
        end_new.strftime("%Y-%m-%d"),
    )

    if df_raw is None:
        return

    df_new = clean_yf_df(df_raw)
    if df_new.empty:
        return

    combined = (
        pd.concat([df_old, df_new])
        .drop_duplicates(subset=["Date"], keep="last")
        .sort_values("Date")
        .reset_index(drop=True)
    )

    if len(combined) > len(df_old):
        combined.to_csv(path, index=False)
        updated_tickers.append(ticker)
        any_new_data = True

# ---------------- EXECUTION ----------------
print(f"🚀 Updating {len(tickers)} tickers (parallel={MAX_WORKERS})")

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = [executor.submit(process_ticker, t) for t in tickers]
    for _ in as_completed(futures):
        pass

# ---------------- SAVE UPDATED LIST ----------------
if updated_tickers:
    with open(UPDATED_TICKERS_FILE, "w") as f:
        for t in sorted(set(updated_tickers)):
            f.write(t + "\n")

print(f"✅ Updated tickers: {len(updated_tickers)}")

if not any_new_data:
    print("🚫 No new trading data found. Downstream pipeline can be skipped.")
else:
    print("📈 New data detected. Downstream pipeline should run.")

print("🎯 Download step completed.")
