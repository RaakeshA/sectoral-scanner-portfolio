import os
from pathlib import Path

import pandas as pd
import yfinance as yf

# -------- Base paths (portable: works on Windows, Linux, GitHub Actions) --------
BASE_DIR = Path(__file__).resolve().parents[1]  # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"   # (kept in case you need later)

stock_strength_path = DATA_DIR / "stock_strength.csv"

# 1) Load stock_strength.csv
if not stock_strength_path.exists():
    print(f"❌ stock_strength.csv not found at: {stock_strength_path}")
    print("Run compute_stock_strength.py first.")
    raise SystemExit

df_stock = pd.read_csv(stock_strength_path)

required_cols = {"ticker", "last_close", "ret_1m_pct", "ret_3m_pct"}
if not required_cols.issubset(df_stock.columns):
    print("❌ stock_strength.csv is missing required columns.")
    print("Required:", required_cols)
    print("Present:", df_stock.columns.tolist())
    raise SystemExit

print(f"✅ Loaded stock_strength.csv with {len(df_stock)} rows")

# 2) Download NIFTY (^NSEI) data from Yahoo
print("\nDownloading NIFTY (^NSEI) data from Yahoo Finance...")

nifty = yf.download(
    "^NSEI",
    start="2021-01-01",
    interval="1d",
    auto_adjust=False,
    progress=False,
)

if nifty.empty:
    print("❌ No data returned for ^NSEI. Check internet or ticker.")
    raise SystemExit

nifty = nifty.reset_index()
nifty["Date"] = pd.to_datetime(nifty["Date"])
nifty = nifty.sort_values("Date").reset_index(drop=True)

print(f"✅ NIFTY data rows: {len(nifty)}")

if len(nifty) < 70:
    print("❌ Not enough NIFTY history to compute 1M/3M returns (need at least 70 days).")
    raise SystemExit

# 3) Compute NIFTY 1M & 3M returns
# Approx: 1M = 21 trading days, 3M = 63 trading days
last_close = float(nifty["Close"].iloc[-1])

idx_1m = max(0, len(nifty) - 1 - 21)
idx_3m = max(0, len(nifty) - 1 - 63)

price_1m = float(nifty["Close"].iloc[idx_1m])
price_3m = float(nifty["Close"].iloc[idx_3m])

nifty_ret_1m = (last_close - price_1m) / price_1m * 100.0
nifty_ret_3m = (last_close - price_3m) / price_3m * 100.0

print(f"\n📊 NIFTY 1M return: {nifty_ret_1m:.2f}%")
print(f"📊 NIFTY 3M return: {nifty_ret_3m:.2f}%")

# 4) Compute Relative Strength vs NIFTY for each stock
# RS_1m_pct = stock_1m_return - NIFTY_1m_return
# RS_3m_pct = stock_3m_return - NIFTY_3m_return

df_stock["RS_1m_pct"] = df_stock["ret_1m_pct"] - nifty_ret_1m
df_stock["RS_3m_pct"] = df_stock["ret_3m_pct"] - nifty_ret_3m

# 5) Save result
out_path = DATA_DIR / "stock_rs.csv"
df_stock.to_csv(out_path, index=False)

print(f"\n✅ Saved Relative Strength data to: {out_path}")
print("Sample:")
print(df_stock[["ticker", "ret_1m_pct", "ret_3m_pct", "RS_1m_pct", "RS_3m_pct"]].head())
