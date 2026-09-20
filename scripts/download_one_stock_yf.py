import pandas as pd
import yfinance as yf
from pathlib import Path

# -------- Base paths --------
BASE_DIR = Path(__file__).resolve().parents[1]   # .../Sectoral_Scanner
DATA_DIR = BASE_DIR / "data"

# Make sure data folder exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ----- Settings -----
symbol = "RELIANCE.NS"     # Yahoo Finance format
start_date = "2021-01-01"
end_date   = None          # None = fetch until today

print(f"Downloading {symbol} from Yahoo Finance from {start_date} to today...")

try:
    df = yf.download(
        symbol,
        start=start_date,
        end=end_date,
        interval="1d",
        auto_adjust=False,
        progress=False
    )
except Exception as e:
    print(f"❌ Yahoo Finance error: {e}")
    raise SystemExit

if df.empty:
    print("❌ No data returned from Yahoo Finance.")
    raise SystemExit

df = df.reset_index()
df.rename(columns={"Date": "timestamp"}, inplace=True)

# Save file
safe_name = symbol.replace(".", "_")
out_path = DATA_DIR / f"{safe_name}.csv"
df.to_csv(out_path, index=False)

print(f"✅ Saved {len(df)} rows to {out_path}")
print(df.head())
